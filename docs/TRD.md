# Technical Requirements Document (TRD)

System design and technical contracts for the LangChain-Powered Auto-OTA-Agent.
Read `PRD.md` for *why* this exists and `API_SPEC.md` for exact request/response
shapes. This doc covers *how* it is built and the design constraints that must
not silently regress. Accurate to the code as it currently stands.

---

## 1. System Overview & Architecture

The entire system is a **single FastAPI process** (`ota_agent/app.py`, run via
`run.py` → `ota_agent/main.py` → `uvicorn`). That one process is, at once:

- the **LangChain agent host** (`FirmwareAgent`, `agent.py`),
- the **OTA firmware server** (`/upload`, `/check`, `/download`),
- the **fleet state collector** (`/report`, `/fleet`),
- the **live dashboard** (`/dashboard`).

**Current build target is laptop-only** — one machine, one process, one port
(`5001`, `Config.SERVER_PORT`). There is no database server and no second
service. State is three JSON files on disk. A Raspberry Pi migration is planned
but out of scope until explicitly requested (see §7).

### Component diagram

```
                         ESP32 FLEET (real hardware)
   node-climate      node-air       node-presence     node-structural
   (DHT22)           (MQ-135)       (PIR+LDR)          (HC-SR04)
      |                 |                |                  |
      |  POST /report/{id}?sensor_type&value&event  (query params, §5)
      |  GET  /check/{id}?current_version
      |  GET  /download/{id}  -> HTTPUpdate
      +-----------------+----------------+------------------+
                                 |  (LAN, http, BASE_URL)
                                 v
   +===========================================================================+
   |            SINGLE FastAPI PROCESS  (ota_agent/app.py, port 5001)          |
   |                                                                           |
   |   /health  /trigger-agent  /upload  /check  /download  /report  /fleet   |
   |   /dashboard                                                              |
   |                                                                           |
   |   +---------------------+        +------------------------------------+   |
   |   |   FirmwareAgent      |  uses  |  LangChain tools (tools.py):       |   |
   |   |   (agent.py)         |------->|  get_fleet_context_tool            |   |
   |   |   GPT-4o-mini @0.2   |        |  read/write_new_firmware           |   |
   |   |   tool-calling loop  |        |  get_device_state_tool             |   |
   |   +---------------------+         |  compile_and_deploy_firmware       |   |
   |            |                      |  push_firmware_to_multiple_nodes   |   |
   |            |                      |  (trigger_ota_flash - legacy sim)  |   |
   |            |                      +------------------------------------+   |
   |            |                                    |                          |
   |            |                                    v                          |
   |            |                             arduino-cli (external, §4)        |
   +============|===============================================================+
                |                    JSON-file state (no DB server)
                v
   db.json            fleet_state.json           manifest.json
   (device schemas)   (latest sensor readings)   (device_id -> version + bin)
```

### State files

| File | Written by | Holds |
|---|---|---|
| `db.json` | `database.py` (`DeviceDatabase`) | Per-device sensor schema, hardware, `current_firmware_path`, `version_history`. Fleet roster is seeded here ahead of time. |
| `fleet_state.json` | `POST /report` via `_save_json` | Each node's latest `sensor_type`, `value`, `event`, `last_seen`. Read by `/fleet` and `get_fleet_context_tool`. |
| `manifest.json` | `POST /upload` via `_save_json` | `device_id -> {version, path}` for the latest compiled `.bin`. Read by `/check` and `/download`. |

`app.py` reads/writes `fleet_state.json` and `manifest.json` only through the
`_load_json` / `_save_json` helpers; `db.json` is owned by `DeviceDatabase`. Do
not open these files ad hoc elsewhere.

---

## 2. Agent Design & Fleet-Context Flow

`POST /trigger-agent` (see `API_SPEC.md`) is the single entry into the agent. It
builds a prompt with `FirmwareAgent.create_agent_prompt(device_id,
event_details, policy)` and calls `agent.invoke({"input": ...})`.

`FirmwareAgent` (`agent.py`) is a hand-rolled tool-calling loop, not a prebuilt
LangChain AgentExecutor:

1. LLM is `ChatOpenAI(model=gpt-4o-mini, temperature=0.2)` with tools bound via
   `bind_tools`.
2. The loop runs up to `max_iterations` (default 10). Each iteration: render the
   system prompt + human input + scratchpad, call the LLM, append the response.
3. If the response has no `tool_calls`, the loop returns `response.content` as
   `output`. Otherwise it executes each requested tool, appends a `ToolMessage`
   with the result, and iterates. Unknown tool names return an error
   `ToolMessage` rather than crashing.
4. If the iteration cap is hit, it returns `"Max iterations reached"`.

### Mandatory fleet-context step (core differentiator)

Both the system prompt and the per-event prompt make this a **hard, ordered
requirement**: before writing or deploying ANY firmware, the agent MUST call
`get_fleet_context_tool()` to read every node's latest state. This is the
project's central design property, not an optional optimization — do not remove
or bypass it.

The agent then reasons about the triggering event:

- **ISOLATED** — only this node signals anything unusual; other nodes' current
  readings are normal.
- **CORRELATED** — the event lines up with anomalies on other nodes (the
  canonical example: heat on `node-climate` + gas on `node-air` + `no_motion`
  on `node-presence` = unoccupied hazard).

The same raw event is required to produce *different* firmware depending on this
fleet-wide judgment.

### Auditability requirement

Every generated firmware MUST include a comment block naming which other nodes'
signals (if any) influenced the decision. The reasoning has to be readable in
the `.cpp`/`.ino` itself — a black-box decision is a contract violation.

### Deployment-scope decision

| Reasoning outcome | Tool | Effect |
|---|---|---|
| ISOLATED, one node | `compile_and_deploy_firmware(device_id)` | Compile + OTA-deploy that single node. |
| CORRELATED, multiple nodes | rewrite each relevant node's firmware, then `push_firmware_to_multiple_nodes([device_ids])` | Compile + deploy each named node; a failure on one does not abort the others. |

`trigger_ota_flash` still exists but is a **legacy simulation** — the real
compile/deploy tools replace it. It is only a fallback if a real deploy tool is
unavailable. If any deploy tool returns an error string (`arduino-cli not found`
/ `COMPILE FAILED:` / `DEPLOY FAILED:`), the agent must report it plainly and not
claim success.

A legacy explicit-`policy` mode (`create_agent_prompt(..., policy=...)`) exists
for backward compatibility; autonomous mode (no policy) is the default. Both
paths still enforce the fleet-context-first step.

---

## 3. Firmware Generation & Templates

Firmware lives in `ota_agent/templates/`:

- `skeleton.ino.template` — the shared, **non-regenerable** plumbing for every
  node (a placeholder sensor block).
- `node-climate.ino`, `node-air.ino`, `node-presence.ino`,
  `node-structural.ino` — the skeleton with its constants filled in and a
  default per-hardware sensor block.

### Regenerable vs. non-regenerable

Everything in a sketch is fixed plumbing — `connectWiFi()`, `reportReading()`,
`checkForOTA()` (the OTA loop via `HTTPUpdate`), `setup()`, `loop()`, includes,
constants — **except** the single region between:

```
// ==== AGENT SENSOR BLOCK START ====
void readAndActOnSensor() { ... }
// ==== AGENT SENSOR BLOCK END ====
```

The agent regenerates **only** the body of `readAndActOnSensor()` (plus any
sensor-library includes/defines it needs, kept inside the markers). It must
never rewrite the plumbing.

**Why this is a hard constraint:** `checkForOTA()` is what keeps a node
field-updatable, and `loop()` runs it *before* the sensor work so a bad sensor
block can never starve the update path. If generated firmware drops the OTA
loop, the device can only be recovered with a physical USB reflash. Losing the
OTA loop is therefore treated as a critical regression, not a style issue.

Per the auditability rule (§2), when the agent regenerates the block it prepends
a comment naming which other fleet nodes' signals influenced the logic.

### The four per-node constants

At the top of every sketch, exactly these four differ between nodes — and no
server IP is hardcoded anywhere except `BASE_URL`:

| Constant | Example | Purpose |
|---|---|---|
| `BASE_URL` | `http://192.168.1.100:5001` | OTA + report server address (the ONLY thing that changes on Pi migration, §7). |
| `DEVICE_ID` | `node-climate` | Identifies the node in every endpoint path. |
| `SENSOR_TYPE` | `temperature` | Sent on `/report`. |
| `FIRMWARE_VERSION` | `v1.0` | Sent on `/check`; bumped each OTA build. |

On disk, `main.py` backfills a `firmware/<device_id>/v1.0.cpp` placeholder per
node so `read_current_firmware` works before the agent generates anything; the
real plumbing comes from the templates at first flash. `write_new_firmware`
writes new versions as `firmware/<device_id>/v<timestamp>.cpp` and updates
`db.json`.

---

## 4. OTA Update Flow

`arduino-cli` is a **required external dependency**: it must be on `PATH` with
the `esp32:esp32` core and the `DHT sensor library` + `Adafruit Unified Sensor`
libraries installed. The compile target FQBN is `esp32:esp32:esp32`.

End-to-end path (server side, `compile_and_deploy_firmware` in `tools.py`):

1. Look up the device's `current_firmware_path` (`.cpp`) in `db.json`; error out
   with a `COMPILE FAILED:` string if missing.
2. Guard: if `arduino-cli` is not on `PATH`, return the `arduino-cli not found`
   string (no crash).
3. Copy the `.cpp` into a temp sketch dir as `<version>.ino` (arduino-cli
   requires the sketch basename to match its folder name), then
   `arduino-cli compile --fqbn esp32:esp32:esp32 --output-dir <build> <sketch>`
   with a 120s timeout.
4. On success, pick the application `.bin` (skipping bootloader/partition bins)
   and `POST /upload/{device_id}?version=<version>` (multipart `file`) to the
   local server. `/upload` writes the bin under `firmware_store/<device_id>/`
   and updates `manifest.json`.
5. Temp build dir is always cleaned up.

Node side (in the template plumbing):

6. On each loop, the node calls `GET /check/{id}?current_version=FIRMWARE_VERSION`.
   The server compares against `manifest.json` and answers
   `{update_available, latest_version}`.
7. If an update is available, the node applies `GET /download/{id}` via
   `httpUpdate.update()`, which flashes and reboots into the new firmware.

`push_firmware_to_multiple_nodes` simply runs step 1–5 for each device_id and
returns a per-node OK/FAIL summary; one node failing does not abort the rest.

---

## 5. Reporting Contract (load-bearing: query params, not JSON)

`POST /report/{device_id}` accepts its payload as **query parameters**, never a
JSON body:

```
POST /report/node-climate?sensor_type=temperature&value=41.50&event=temperature_critical
```

The FastAPI handler signature is
`report_state(device_id, sensor_type: str, value: float, event: str = "")`, so
FastAPI binds those from the query string. The request body is empty.

**Why this is load-bearing.** The ESP32 firmware's `reportReading()` builds the
data into the URL and POSTs an empty body (`http.POST("")`). The server and the
firmware must agree on where the data lives. A prior draft had exactly this
mismatch — ESP32 sending a JSON body while the server read query params — which
silently dropped every reading. **Reintroducing that mismatch is a regression**,
not a refactor. If this contract ever changes, the ESP32 templates
(`ota_agent/templates/`) and `docs/API_SPEC.md` MUST change in the same commit.

`event` is empty unless the reading crosses that node's threshold (e.g.
`temperature_critical`). Each report overwrites the node's entry in
`fleet_state.json` and stamps `last_seen = time.time()`.

---

## 6. Data / State Model

Three JSON files, no schema engine. The fleet is four nodes:

| device_id | sensor_type | hardware |
|---|---|---|
| `node-climate` | temperature (+ humidity) | DHT22 |
| `node-air` | air_quality (raw analog) | MQ-135 |
| `node-presence` | motion (+ light) | PIR + LDR |
| `node-structural` | distance | HC-SR04 |

### `db.json` — device schemas (seeded, source of truth for roster)

```json
{
  "node-climate": {
    "hardware": "DHT22",
    "current_firmware_path": "firmware/node-climate/v1.0.cpp",
    "sensor_schema": {
      "temperature": {"type": "temperature", "pin": 4, "unit": "celsius"},
      "humidity":    {"type": "humidity",    "pin": 4, "unit": "percentage"}
    },
    "version_history": ["firmware/node-climate/v1.0.cpp"]
  }
}
```

`DeviceDatabase.update_firmware_path` appends each new `.cpp` to
`version_history` and repoints `current_firmware_path`.

### `fleet_state.json` — latest sensor readings (runtime)

```json
{
  "node-climate":   { "sensor_type": "temperature",  "value": 41.5,  "event": "temperature_critical", "last_seen": 1785000000.0 },
  "node-air":       { "sensor_type": "air_quality",  "value": 1450,  "event": "",                     "last_seen": 1785000002.0 },
  "node-presence":  { "sensor_type": "motion",       "value": 0,     "event": "no_motion",            "last_seen": 1785000001.0 },
  "node-structural":{ "sensor_type": "distance",     "value": 120.3, "event": "",                     "last_seen": 1785000003.0 }
}
```

Keys exist only for nodes that have reported at least once — consumers must not
assume all four are present.

### `manifest.json` — OTA pointer (runtime)

```json
{
  "node-climate": {
    "version": "v20260727153000",
    "path": "firmware_store/node-climate/v20260727153000.bin",
    "previous": { "version": "v20260727120000", "path": "firmware_store/node-climate/v20260727120000.bin" }
  }
}
```

`previous` is the last known good firmware: `/upload` carries the entry it
replaces forward, and `POST /rollback/{device_id}` swaps the two so a bad push
can be recovered without hunting through `firmware_store/` for the right `.bin`.
Rollback is operator-driven and reversible; nothing is deleted. Automatic
rollback on a failed flash remains a Phase 4 item.

---

## 7. Raspberry Pi Migration Plan (future — DO NOT implement now)

Out of current scope. Do **not** add Pi-specific code, paths, or systemd units
until explicitly requested (matches `ROADMAP.md` Phase 3 and the `PRD.md`
non-goal). This section documents the intended low-risk path only.

The migration is deliberately cheap because nothing in the agent, tools, or
ESP32 *sensor logic* assumes a host — only network config (`BASE_URL`, IP)
differs between laptop and Pi. Sequence:

1. Copy the project to the Pi; create a venv and `pip install -r requirements.txt`.
2. Reserve a **static LAN IP** for the Pi in the router (fixes the DHCP IP
   fragility risk noted in `PRD.md` §10).
3. While still laptop-hosted, perform **one final OTA push** to every node that
   changes **only `BASE_URL`** to the Pi's static IP (all other plumbing and the
   agent sensor block stay byte-for-byte identical).
4. Run the app on the Pi wrapped in a **systemd service with `Restart=always`**.
5. Verify all nodes report into the Pi-hosted `/dashboard` before decommissioning
   the laptop process.

The one-hop `BASE_URL`-only push in step 3 is what makes this reversible: if the
Pi is unreachable, the laptop is still live until step 5 confirms the cutover.

---

## 8. Security Posture (Current State)

Everything below is a **deliberate deferral**, tracked in `ROADMAP.md` Phase 4 —
not an oversight. Do not opportunistically "harden" these as a side effect of an
unrelated task; each changes the ESP32 client code and belongs to its own scoped
item.

- **No authentication anywhere.** No endpoint checks any auth header. Any host on
  the LAN can `/report`, `/trigger-agent`, `/upload`, or `/download`.
- **No firmware signing / integrity check.** `/download` serves whatever `.bin`
  the manifest points at; the node flashes it unverified. No rollback on a bad
  flash.
- **Error status codes: normalized.** `/download` now returns `404` when no
  firmware is on record, rather than `200` with an error body — a `200` there
  would hand the ESP32 a JSON error to flash as a binary. `/check` deliberately
  keeps `200 {"update_available": false}` for a device with nothing uploaded
  yet, since that is a normal state for a freshly USB-flashed node rather than
  an error. See `API_SPEC.md` "Error Handling Conventions".

**Partial auth is worse than none.** Adding authentication to only a subset of
endpoints creates a false sense of security. If/when auth lands, it must cover
all endpoints at once, and `API_SPEC.md` §Error Handling and this section must be
updated together.

---

## Cross-references

- `docs/PRD.md` — product rationale, goals/non-goals, success metrics, risks.
- `docs/API_SPEC.md` — exact request/response shapes for every endpoint.
- `docs/ROADMAP.md` — phased backlog (Phase 3 = Pi migration §7; Phase 4 =
  security deferrals §8).
