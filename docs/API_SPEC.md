# API Specification

All endpoints are served by the single FastAPI process (`ota_agent/app.py`), default port `5001` (configurable in `config.py`). Base URL in examples: `http://<HOST>:5001`.

---

### `GET /health`
Liveness check.

**Response `200`**
```json
{ "status": "healthy" }
```

---

### `POST /trigger-agent`
Fires the LangChain `FirmwareAgent` for a given device event. The agent internally calls `get_fleet_context_tool()` before deciding on firmware changes (see `TRD.md` §2).

**Request body**
```json
{
  "device_id": "node-climate",
  "event_details": "sensor_temperature_critical_41_celsius",
  "policy": null
}
```
- `device_id` (string, required) — must match a known node id.
- `event_details` (string, required) — free-text event description; the agent parses this along with fleet context.
- `policy` (string, optional, nullable) — legacy explicit-policy mode; omit for autonomous mode.

**Response `200`**
```json
{
  "success": true,
  "agent_output": "Reviewed fleet context: node-air reported no gas anomaly, node-presence reported no motion. Treated as isolated climate event. Deployed low-urgency firmware to node-climate only."
}
```

**Response `500`** (agent or compile failure)
```json
{
  "success": false,
  "agent_output": "COMPILE FAILED: ..."
}
```

---

### `POST /upload/{device_id}`
Stores a compiled firmware binary and updates the manifest. Called internally by `compile_and_deploy_firmware()`, not directly by ESP32 nodes.

**Path params:** `device_id` (string)
**Query params:** `version` (string, required) — e.g. a timestamp like `v20260727153000`
**Body:** `multipart/form-data`, field `file` — the `.bin` payload

**Response `200`**
```json
{ "status": "uploaded", "device_id": "node-climate", "version": "v20260727153000" }
```

---

### `GET /check/{device_id}`
Called by each ESP32 node on its polling interval to check for a newer firmware version.

**Path params:** `device_id` (string)
**Query params:** `current_version` (string, required) — the version currently running on the device

**Response `200`**
```json
{ "update_available": true, "latest_version": "v20260727153000" }
```
If no firmware has ever been uploaded for this `device_id`:
```json
{ "update_available": false }
```
This stays a `200`, not a 404 — a USB-flashed node with nothing uploaded yet is a normal steady state, and 404ing it would make every node error-loop until its first deploy.

Note the response is compact JSON (`"update_available":true`, no space). ESP32 clients must not depend on a specific spacing when matching this field; the shipped templates accept either form.

---

### `GET /download/{device_id}`
Returns the current `.bin` for a device. Called by `httpUpdate.update()` on the ESP32 after `/check` reports an update is available.

**Response `200`:** binary, `Content-Type: application/octet-stream`
**Response `404` (no firmware on record):**
```json
{ "detail": "no firmware found" }
```
A 200 here would hand the ESP32 a JSON error body to flash as if it were a firmware binary, so this case is a hard 404. `httpUpdate.update()` treats the non-200 as a failed update and leaves the running firmware in place.

---

### `POST /report/{device_id}`
Called by every ESP32 node on every sensor read to report its current state into `fleet_state.json`. **Uses query parameters, not a JSON body** — this is a deliberate, load-bearing contract; see `TRD.md` §5.

**Path params:** `device_id` (string)
**Query params:**
- `sensor_type` (string, required) — e.g. `"temperature"`, `"air_quality"`, `"motion"`, `"distance"`
- `value` (float, required) — the raw reading
- `event` (string, optional, default `""`) — non-empty only when the reading crosses that node's threshold, e.g. `"temperature_critical"`

**Response `200`**
```json
{ "status": "recorded" }
```

---

### `GET /fleet`
Returns the full current fleet state. This is what `get_fleet_context_tool()` calls before the agent writes any firmware.

**Response `200`**
```json
{
  "node-climate":   { "sensor_type": "temperature", "value": 41.5, "event": "temperature_critical", "last_seen": 1785000000.0 },
  "node-air":       { "sensor_type": "air_quality",  "value": 1450, "event": "",                     "last_seen": 1785000002.0 },
  "node-presence":  { "sensor_type": "motion",       "value": 0,    "event": "no_motion",             "last_seen": 1785000001.0 },
  "node-structural":{ "sensor_type": "distance",     "value": 120.3,"event": "",                     "last_seen": 1785000003.0 }
}
```
Keys present only for nodes that have reported at least once. Consumers should not assume all four node roles are present.

---

### `GET /dashboard`
Human-readable HTML view, auto-refreshes every 5 seconds. Not intended for programmatic consumption; renders a table of device / sensor_type / value / event / firmware version / seconds-since-last-report, sourced from `/fleet` + `manifest.json` internally.

---

## Error Handling Conventions (Current State)

- Error cases use real status codes. `/download` 404s when no firmware is on record; `/trigger-agent` 500s on agent or compile failure; missing/invalid query params yield FastAPI's `422`.
- One deliberate exception: `/check` returns `200` with `update_available: false` for a device that has no firmware uploaded yet. That is a normal state for a freshly USB-flashed node, not an error.
- No authentication headers are checked anywhere. Do not add auth to a subset of endpoints without a corresponding update here and in `TRD.md` §8 — partial auth coverage is worse than none because it creates a false sense of security.
