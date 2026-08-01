"""Fake the ESP32 fleet so the dashboard looks live without hardware.

Each simulated node does exactly what the real firmware templates do:
report its reading to POST /report/{device_id} (query params), then poll
GET /check/{device_id} and pull GET /download when a new build exists.

    python run.py            # terminal 1
    python simulate_fleet.py # terminal 2  -> http://localhost:5001/dashboard

Values are a random walk around a plausible baseline, so the dashboard drifts
like real sensors instead of flipping between canned numbers. Occasionally a
node goes anomalous (--anomaly) so the agent has something to react to.
"""

import argparse
import random
import sys
import time
from typing import Dict, Optional, Tuple

import requests

BASE_URL = "http://localhost:5001"

# device_id -> (sensor_type, baseline, drift step, anomaly value)
# Baselines/steps are the calibration knobs: tune here, not in the loop.
NODES: Dict[str, Tuple[str, float, float, float]] = {
    "node-climate": ("temperature", 22.0, 0.4, 41.5),
    "node-air": ("air_quality", 320.0, 25.0, 1450.0),
    "node-presence": ("motion", 0.0, 1.0, 1.0),
    "node-structural": ("distance", 120.0, 6.0, 12.0),
}


def classify(sensor_type: str, value: float) -> str:
    """Map a reading to the event string the real firmware would send."""
    if sensor_type == "temperature":
        return "temperature_critical" if value > 35 else "temperature_high" if value > 28 else ""
    if sensor_type == "air_quality":
        return "gas_critical" if value > 1000 else "gas_warning" if value > 600 else ""
    if sensor_type == "motion":
        return "motion_detected" if value >= 1 else "no_motion"
    if sensor_type == "distance":
        return "proximity_alert" if value < 30 else ""
    return ""


def next_value(sensor_type: str, value: float, step: float, anomaly: float, chance: float) -> float:
    """Random-walk the reading, occasionally jumping to the anomaly value."""
    if random.random() < chance:
        return anomaly
    if sensor_type == "motion":
        return float(random.random() < 0.25)
    return round(value + random.uniform(-step, step), 1)


def check_for_update(device_id: str, current: Optional[str]) -> Optional[str]:
    """Poll /check and, if a new build exists, download it. Returns new version."""
    r = requests.get(f"{BASE_URL}/check/{device_id}", params={"current_version": current or "v0"})
    r.raise_for_status()
    body = r.json()
    if not body.get("update_available"):
        return current
    latest = body["latest_version"]
    requests.get(f"{BASE_URL}/download/{device_id}").raise_for_status()
    time.sleep(1)  # a real httpUpdate flash + reboot takes a few seconds
    print(f"  {device_id}: OTA flashed {current or '(none)'} -> {latest}")
    return latest


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--interval", type=float, default=5.0, help="seconds between reports")
    p.add_argument("--anomaly", type=float, default=0.05, help="per-node chance of an anomalous reading")
    p.add_argument("--once", action="store_true", help="single round, then exit")
    args = p.parse_args()

    values = {d: cfg[1] for d, cfg in NODES.items()}
    versions: Dict[str, Optional[str]] = {d: None for d in NODES}

    print(f"Simulating {len(NODES)} nodes against {BASE_URL} (Ctrl-C to stop)")
    while True:
        for device_id, (sensor_type, _, step, anomaly) in NODES.items():
            values[device_id] = next_value(sensor_type, values[device_id], step, anomaly, args.anomaly)
            value = values[device_id]
            event = classify(sensor_type, value)
            try:
                requests.post(
                    f"{BASE_URL}/report/{device_id}",
                    params={"sensor_type": sensor_type, "value": value, "event": event},
                ).raise_for_status()
                versions[device_id] = check_for_update(device_id, versions[device_id])
            except requests.RequestException as e:
                print(f"  {device_id}: server unreachable ({e.__class__.__name__}) - is run.py up?")
                continue
            print(f"  {device_id}: {sensor_type}={value} {event or '-'}")
        if args.once:
            return 0
        time.sleep(args.interval)


def _selftest() -> None:
    assert classify("temperature", 41.5) == "temperature_critical"
    assert classify("temperature", 30) == "temperature_high"
    assert classify("temperature", 22) == ""
    assert classify("air_quality", 1450) == "gas_critical"
    assert classify("distance", 12) == "proximity_alert"
    assert classify("motion", 0) == "no_motion"
    random.seed(0)
    v = 22.0
    for _ in range(200):
        v = next_value("temperature", v, 0.4, 41.5, 0.0)
    assert 10 < v < 35, f"walk ran away: {v}"
    assert next_value("temperature", 22.0, 0.4, 41.5, 1.0) == 41.5
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        sys.exit(main())
