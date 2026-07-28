#!/usr/bin/env python3
"""Regression test: POST /report (query params) -> GET /fleet -> agent's fleet-context read.

Needs no running server and no OPENAI_API_KEY: it drives the app in-process with
fastapi.testclient.TestClient and a MagicMock agent.

    venv/bin/python test_fleet_flow.py     # or: pytest test_fleet_flow.py

The regression this exists to catch (docs/TRD.md §5): /report/{device_id} takes its
payload as QUERY PARAMS, never a JSON body. A prior draft had the ESP32 sending a
JSON body while the server read query params, which silently dropped every reading.
check_json_body_rejected() fails loudly if someone switches the contract back.

Assertions deliberately check only the fields they care about — extra fields on a
node entry (e.g. staleness annotations) must not break this test.
"""

import json
import os
import sys
from unittest.mock import MagicMock

# Config paths are relative, so state files land wherever cwd is. Pin it to the repo.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO_ROOT)
sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient  # noqa: E402

from ota_agent.app import create_app  # noqa: E402
from ota_agent.config import Config  # noqa: E402
from ota_agent import tools  # noqa: E402

# Gitignored runtime state this test must not clobber or leave behind.
STATE_FILES = [Config.FLEET_STATE_FILE, Config.MANIFEST_FILE]

# device_id -> (sensor_type, value, event)
FLEET = {
    "node-climate": ("temperature", 41.5, "temperature_critical"),
    "node-air": ("air_quality", 1450.0, "gas_critical"),
    "node-presence": ("motion", 0.0, "no_motion"),
    "node-structural": ("distance", 120.3, ""),
}


def agent_fleet_view() -> dict:
    """What the agent itself sees: get_fleet_context_tool reads fleet_state.json directly."""
    return json.loads(tools.get_fleet_context_tool.invoke({}))


def report_fleet(client: TestClient) -> None:
    """POST every node's reading using query params (the load-bearing contract)."""
    for device_id, (sensor_type, value, event) in FLEET.items():
        r = client.post(
            f"/report/{device_id}",
            params={"sensor_type": sensor_type, "value": value, "event": event},
        )
        assert r.status_code == 200, f"{device_id}: expected 200, got {r.status_code} {r.text}"
        assert r.json() == {"status": "recorded"}, r.json()


# --- checks (take a client; the test_* wrappers below supply a clean one) -----

def check_empty_fleet_is_empty_object(client: TestClient) -> None:
    """Before any node reports, both views are an empty object, not an error."""
    assert client.get("/fleet").json() == {}
    assert agent_fleet_view() == {}


def check_query_param_report_round_trips(client: TestClient) -> None:
    """All four nodes' query-param reports show up verbatim in /fleet AND the agent's view."""
    report_fleet(client)

    fleet = client.get("/fleet").json()
    assert set(FLEET) <= set(fleet), f"missing from /fleet: {set(FLEET) - set(fleet)}"

    agent_view = agent_fleet_view()
    assert set(FLEET) <= set(agent_view), (
        f"missing from agent fleet context: {set(FLEET) - set(agent_view)}"
    )

    for device_id, (sensor_type, value, event) in FLEET.items():
        for source, entry in (("/fleet", fleet[device_id]), ("agent", agent_view[device_id])):
            assert entry["sensor_type"] == sensor_type, (source, device_id, entry)
            assert entry["value"] == value, (source, device_id, entry)
            assert entry["event"] == event, (source, device_id, entry)
            assert isinstance(entry.get("last_seen"), (int, float)), (source, device_id, entry)


def check_agent_view_agrees_with_fleet_endpoint(client: TestClient) -> None:
    """The tool reads fleet_state.json directly, /fleet serves it over HTTP: they must agree."""
    report_fleet(client)

    fleet = client.get("/fleet").json()
    agent_view = agent_fleet_view()

    assert set(fleet) == set(agent_view), (
        f"agent sees {sorted(agent_view)}, /fleet serves {sorted(fleet)}"
    )
    for device_id, entry in fleet.items():
        for field in ("sensor_type", "value", "event", "last_seen"):
            assert agent_view[device_id][field] == entry[field], (device_id, field)


def check_json_body_rejected(client: TestClient) -> None:
    """REGRESSION GUARD (TRD §5): a JSON body with no query params must be rejected 422."""
    r = client.post(
        "/report/node-climate",
        json={"sensor_type": "temperature", "value": 41.5, "event": "temperature_critical"},
    )
    assert r.status_code == 422, (
        f"POST /report with a JSON body and no query params returned {r.status_code}, "
        "expected 422. The query-param contract (TRD §5) is broken — real ESP32 nodes "
        "would silently drop every reading."
    )
    # A rejected report must not have written anything into fleet state.
    assert "node-climate" not in client.get("/fleet").json()
    assert "node-climate" not in agent_fleet_view()


CHECKS = [
    check_empty_fleet_is_empty_object,
    check_query_param_report_round_trips,
    check_agent_view_agrees_with_fleet_endpoint,
    check_json_body_rejected,
]


def _clear_state() -> None:
    for path in STATE_FILES:
        if os.path.exists(path):
            os.remove(path)


def run_check(check) -> None:
    """Run one check against a clean slate, restoring any pre-existing runtime state."""
    backups = {p: open(p, "rb").read() for p in STATE_FILES if os.path.exists(p)}
    try:
        _clear_state()
        with TestClient(create_app(MagicMock())) as client:
            check(client)
    finally:
        _clear_state()
        for path, data in backups.items():
            with open(path, "wb") as f:
                f.write(data)


# --- pytest entry points ------------------------------------------------------

def test_empty_fleet_is_empty_object():
    run_check(check_empty_fleet_is_empty_object)


def test_query_param_report_round_trips():
    run_check(check_query_param_report_round_trips)


def test_agent_view_agrees_with_fleet_endpoint():
    run_check(check_agent_view_agrees_with_fleet_endpoint)


def test_json_body_rejected():
    run_check(check_json_body_rejected)


if __name__ == "__main__":
    failures = 0
    for _check in CHECKS:
        try:
            run_check(_check)
            print(f"PASS  {_check.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {_check.__name__}: {exc}")
    print(f"\n{len(CHECKS) - failures}/{len(CHECKS)} passed")
    sys.exit(1 if failures else 0)
