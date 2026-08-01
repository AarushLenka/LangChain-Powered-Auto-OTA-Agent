"""Self-check for the staleness cutoff in get_fleet_context_tool().

Run directly: `venv/bin/python test_fleet_staleness.py` (also works under pytest).
Uses a temp fleet_state.json via Config.FLEET_STATE_FILE, so the real runtime
fleet_state.json is never created, read, or overwritten.
"""

import json
import os
import tempfile
import time

from ota_agent.config import Config
from ota_agent.tools import get_fleet_context_tool


def test_fleet_staleness() -> None:
    now = time.time()
    state = {
        "node-climate": {"sensor_type": "temperature", "value": 41.5,
                         "event": "temperature_critical", "last_seen": now},
        "node-air": {"sensor_type": "air_quality", "value": 900,
                     "event": "gas_critical", "last_seen": now - 600},
        "node-presence": {"sensor_type": "motion", "value": 0, "event": "no_motion"},
    }

    tmp_dir = tempfile.mkdtemp(prefix="fleet-staleness-")
    tmp_path = os.path.join(tmp_dir, "fleet_state.json")
    original = Config.FLEET_STATE_FILE
    try:
        with open(tmp_path, "w") as f:
            json.dump(state, f)
        Config.FLEET_STATE_FILE = tmp_path
        fleet = json.loads(get_fleet_context_tool.invoke({}))
    finally:
        Config.FLEET_STATE_FILE = original
        os.remove(tmp_path)
        os.rmdir(tmp_dir)

    assert fleet["node-climate"]["stale"] is False, fleet["node-climate"]
    assert fleet["node-climate"]["age_seconds"] < 5, fleet["node-climate"]
    assert fleet["node-air"]["stale"] is True, fleet["node-air"]
    assert fleet["node-air"]["age_seconds"] >= 600, fleet["node-air"]
    # Missing last_seen -> unknown age, treated as stale.
    assert fleet["node-presence"]["stale"] is True, fleet["node-presence"]
    assert fleet["node-presence"]["age_seconds"] is None, fleet["node-presence"]
    # Original fields survive the annotation.
    assert fleet["node-climate"]["event"] == "temperature_critical"
    assert not os.path.exists("fleet_state.json"), "test leaked runtime fleet_state.json"


if __name__ == "__main__":
    test_fleet_staleness()
    print("OK: fresh node stale=False, 600s-old node stale=True, missing last_seen stale=True")
