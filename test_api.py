#!/usr/bin/env python3
"""Manual live-server smoke test for the OTA agent HTTP API.

REQUIRES A RUNNING SERVER:

    python run.py        # in another terminal -> http://localhost:5001

Two groups of checks:

  * No-key checks   — /health, /report, /fleet, /dashboard. These only touch
                      JSON state and need no OpenAI credentials.
  * Agent checks    — /trigger-agent. These invoke GPT-4o-mini and so need
                      OPENAI_API_KEY set in the server's .env. They are slow
                      (the agent compiles firmware) and are skipped unless you
                      pass --agent.

For the fast, offline regression test of the /report -> /fleet -> agent
fleet-context chain, use test_fleet_flow.py instead (no server, no API key).
"""

import sys

import requests

BASE_URL = "http://localhost:5001"
TIMEOUT = 10
AGENT_TIMEOUT = 180

# Real fleet node roles (see CLAUDE.md): device_id -> (sensor_type, value, event)
FLEET = {
    "node-climate": ("temperature", 41.5, "temperature_critical"),
    "node-air": ("air_quality", 1450.0, "gas_critical"),
    "node-presence": ("motion", 0.0, "no_motion"),
    "node-structural": ("distance", 120.3, ""),
}


def test_health_endpoint() -> bool:
    """GET /health -> {"status": "healthy"}."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"  Health check failed: {e}")
        return False
    print(f"  status {response.status_code}: {response.text[:200]}")
    return response.status_code == 200


def test_report_endpoint() -> bool:
    """POST /report/{device_id} for all four nodes using QUERY PARAMS (not a JSON body).

    The query-param contract is load-bearing (docs/TRD.md §5) — the ESP32 firmware
    puts the reading in the URL and POSTs an empty body.
    """
    ok = True
    for device_id, (sensor_type, value, event) in FLEET.items():
        try:
            response = requests.post(
                f"{BASE_URL}/report/{device_id}",
                params={"sensor_type": sensor_type, "value": value, "event": event},
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            print(f"  {device_id}: request failed: {e}")
            ok = False
            continue
        print(f"  {device_id}: status {response.status_code} {response.text[:120]}")
        ok = ok and response.status_code == 200
    return ok


def test_report_rejects_json_body() -> bool:
    """POST /report with a JSON body and no query params must be rejected (422)."""
    try:
        response = requests.post(
            f"{BASE_URL}/report/node-climate",
            json={"sensor_type": "temperature", "value": 41.5, "event": "temperature_critical"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return False
    print(f"  status {response.status_code} (expected 422)")
    if response.status_code != 422:
        print("  REGRESSION: /report accepted a JSON body — TRD §5 contract broken.")
        return False
    return True


def test_fleet_endpoint() -> bool:
    """GET /fleet must contain every node just reported, with matching values."""
    try:
        response = requests.get(f"{BASE_URL}/fleet", timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"  Fleet read failed: {e}")
        return False
    if response.status_code != 200:
        print(f"  status {response.status_code}: {response.text[:200]}")
        return False

    fleet = response.json()
    ok = True
    for device_id, (sensor_type, value, event) in FLEET.items():
        entry = fleet.get(device_id)
        if entry is None:
            print(f"  {device_id}: MISSING from /fleet")
            ok = False
            continue
        match = (
            entry.get("sensor_type") == sensor_type
            and entry.get("value") == value
            and entry.get("event") == event
        )
        print(f"  {device_id}: {'ok' if match else 'MISMATCH'} -> {entry}")
        ok = ok and match
    return ok


def test_dashboard_endpoint() -> bool:
    """GET /dashboard renders HTML listing the nodes that have reported."""
    try:
        response = requests.get(f"{BASE_URL}/dashboard", timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"  Dashboard failed: {e}")
        return False
    body = response.text
    ok = response.status_code == 200 and "Auto-OTA Fleet" in body
    missing = [d for d in FLEET if d not in body]
    if missing:
        print(f"  Nodes missing from dashboard HTML: {missing}")
        ok = False
    print(f"  status {response.status_code}, {len(body)} bytes")
    return ok


def test_check_endpoint() -> bool:
    """GET /check/{device_id} answers whether a newer firmware version exists."""
    try:
        response = requests.get(
            f"{BASE_URL}/check/node-climate",
            params={"current_version": "v0"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        print(f"  Check failed: {e}")
        return False
    print(f"  status {response.status_code}: {response.text[:200]}")
    return response.status_code == 200 and "update_available" in response.json()


def test_trigger_agent_policy_mode() -> bool:
    """POST /trigger-agent WITH an explicit policy (legacy policy-driven mode). NEEDS API KEY."""
    payload = {
        "device_id": "node-climate",
        "event_details": "temperature_critical_41_celsius_sustained",
        "policy": "When node-climate reports a critical temperature, increase its sampling rate to every 5 seconds.",
    }
    return _post_trigger_agent(payload)


def test_trigger_agent_autonomous_mode() -> bool:
    """POST /trigger-agent with NO policy — agent reasons over fleet context. NEEDS API KEY."""
    payload = {
        "device_id": "node-air",
        "event_details": "air_quality_raw_1450_gas_critical_sustained",
    }
    return _post_trigger_agent(payload)


def _post_trigger_agent(payload: dict) -> bool:
    try:
        response = requests.post(
            f"{BASE_URL}/trigger-agent", json=payload, timeout=AGENT_TIMEOUT
        )
    except requests.RequestException as e:
        print(f"  Trigger-agent failed: {e}")
        return False
    print(f"  status {response.status_code}: {response.text[:500]}")
    return response.status_code == 200


NO_KEY_TESTS = [
    ("GET  /health", test_health_endpoint),
    ("POST /report (query params, 4 nodes)", test_report_endpoint),
    ("POST /report rejects JSON body", test_report_rejects_json_body),
    ("GET  /fleet", test_fleet_endpoint),
    ("GET  /dashboard", test_dashboard_endpoint),
    ("GET  /check", test_check_endpoint),
]

AGENT_TESTS = [
    ("POST /trigger-agent (policy mode)", test_trigger_agent_policy_mode),
    ("POST /trigger-agent (autonomous mode)", test_trigger_agent_autonomous_mode),
]


def main() -> int:
    run_agent = "--agent" in sys.argv
    print(f"Smoke-testing {BASE_URL} (server must be running: python run.py)\n")

    if not test_health_endpoint():
        print(
            f"\nServer is not responding at {BASE_URL}.\n"
            "Start it in another terminal with:  python run.py\n"
            "Then re-run:  python test_api.py [--agent]"
        )
        return 1
    print()

    results = [("GET  /health", True)]
    for name, test in NO_KEY_TESTS[1:]:
        print(name)
        results.append((name, test()))
        print()

    if run_agent:
        print("--- Agent tests (these NEED OPENAI_API_KEY in the server's .env, and are slow) ---\n")
        for name, test in AGENT_TESTS:
            print(name)
            results.append((name, test()))
            print()
    else:
        print("Skipping /trigger-agent tests (need OPENAI_API_KEY). Re-run with --agent to include them.\n")

    failed = [name for name, ok in results if not ok]
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print()
    if failed:
        print(f"{len(failed)} check(s) failed: {', '.join(failed)}")
        return 1
    print(f"All {len(results)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
