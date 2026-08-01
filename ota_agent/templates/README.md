# ESP32 Firmware Templates

Per-node ESP32 sketches for the fleet. Each is the **shared skeleton**
(`skeleton.ino.template`) with its four constants filled in and a default
sensor block for its hardware.

## Non-regenerable vs. agent-owned

Everything in a sketch is **non-regenerable plumbing** — WiFi connect/reconnect,
the OTA check/download loop (`checkForOTA()` via `HTTPUpdate`), `reportReading()`,
`setup()`, `loop()` — **except** the region between:

```
// ==== AGENT SENSOR BLOCK START ====
void readAndActOnSensor() { ... }
// ==== AGENT SENSOR BLOCK END ====
```

The agent regenerates **only** the body of `readAndActOnSensor()` (plus any
sensor-library includes/defines it needs, kept inside the markers). It must
never rewrite the plumbing.

**Why it matters:** if generated firmware drops the OTA loop, the device can
only be recovered by a physical USB reflash. The OTA loop is what keeps a node
field-updatable. Treat everything outside the markers as immutable.

When the agent regenerates the block it must prepend a comment naming which
other fleet nodes' signals (if any) influenced the logic — see the Agent
Behavior Contract in `CLAUDE.md`.

## The four per-node constants (the ONLY things that differ)

At the top of every sketch, exactly these four — nothing else, and no
hardcoded server IP anywhere except `BASE_URL`:

| constant | example |
|---|---|
| `BASE_URL` | `http://192.168.1.100:5001` |
| `DEVICE_ID` | `node-climate` |
| `SENSOR_TYPE` | `temperature` |
| `FIRMWARE_VERSION` | `v1.0` (bumped each OTA build; sent in `/check`) |

## `/report` contract — QUERY PARAMS, not JSON

`reportReading()` POSTs to `/report/{DEVICE_ID}` with **query parameters**:

```
POST /report/node-climate?sensor_type=temperature&value=41.50&event=temperature_critical
```

Body is empty; all data is in the URL. Sending a JSON body here is a known
regression — the server (`app.py`) reads query params. If this ever changes,
`docs/API_SPEC.md` and every sketch must change together.

`value` is a float; `event` is empty unless the reading crosses that node's
threshold.

## OTA flow

1. `GET /check/{DEVICE_ID}?current_version=FIRMWARE_VERSION`
2. If response contains `update_available: true`, apply
   `GET /download/{DEVICE_ID}` via `httpUpdate.update()` (reboots on success).

`checkForOTA()` runs first in `loop()`, before sensor work, so a bad sensor
block can never starve the update path.

## Files

| file | node | hardware / pins |
|---|---|---|
| `skeleton.ino.template` | — | shared skeleton, placeholder sensor block |
| `node-climate.ino` | node-climate | DHT22, data pin 4 (temperature) |
| `node-air.ino` | node-air | MQ-135, analog pin 34 (air_quality) |
| `node-presence.ino` | node-presence | PIR pin 27 + LDR analog 35 (motion) |
| `node-structural.ino` | node-structural | HC-SR04, trig/echo pin 5 (distance) |
