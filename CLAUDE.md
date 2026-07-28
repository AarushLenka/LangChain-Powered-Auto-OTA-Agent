# CLAUDE.md

Guidance for Claude Code when working in this repository. Read this file first,understand the existing codebase from graphify, then `PRD.md`, `TRD.md`, and `API_SPEC.md` in `/docs` before making changes.
Maintain proper git commits but do not add yourself to as an co author.
Not allowed to access .env
## Project Summary

**LangChain-Powered Auto-OTA-Agent** is an AI agent (LangChain + GPT-4o-mini + FastAPI) that autonomously writes, compiles, and OTA-deploys firmware for a small fleet of ESP32 IoT sensor nodes. The agent reasons across the *whole fleet's* sensor state (not just a single triggering event) before deciding what firmware to generate and which nodes to push it to.

Current build target: **laptop-only** (one FastAPI process hosts the agent, OTA firmware server, and fleet dashboard). A Raspberry Pi migration is planned later (see `docs/TRD.md` §7) but is **out of scope until explicitly requested** — do not add Pi-specific code (systemd units, Pi-only paths) unless asked.

Read `docs/PRD.md` for why this exists and what "done" looks like. Read `docs/TRD.md` for the system design and endpoint contracts. Read `docs/API_SPEC.md` for exact request/response shapes before touching any endpoint.

## Repository Structure

```
ota_agent/
  __init__.py
  main.py              # uvicorn entrypoint
  app.py               # FastAPI routes: /health, /trigger-agent, /upload, /check, /download, /report, /fleet, /dashboard
  agent.py             # FirmwareAgent (LangChain agent, tool-calling loop, system prompt)
  config.py            # port, model name, temperature, other settings
  database.py          # DeviceDatabase (JSON-based device/sensor schema state)
  tools.py             # LangChain tools: read/write firmware, compile_and_deploy_firmware,
                        # get_fleet_context_tool, push_firmware_to_multiple_nodes
  templates/            # per-node ESP32 sketch skeletons (WiFi/OTA plumbing) — AI fills in
                        # only the sensor-reading block, never regenerates this plumbing
firmware/
  <device_id>/          # generated .cpp source, versioned by timestamp
firmware_store/
  <device_id>/           # compiled .bin files served for OTA (created at runtime)
manifest.json           # device_id -> latest firmware version + path
fleet_state.json         # device_id -> latest sensor reading, event, last_seen timestamp
db.json                  # device sensor schemas
training_data.json        # 100 scenarios across 10 categories, used for agent eval
run.py                    # entry point
requirements.txt
docs/
  PRD.md
  TRD.md
  API_SPEC.md
  ROADMAP.md
test_api.py
autonomous_demo.py
run_training_scenarios.py
```

## Tech Stack

- Python 3.11+, FastAPI, LangChain (`langchain-openai`, `langchain-core`), Pydantic v2, Uvicorn
- OpenAI GPT-4o-mini, temperature 0.2
- `arduino-cli` for headless ESP32 compilation (must be installed and on `PATH`; core `esp32:esp32` and libraries `DHT sensor library` + `Adafruit Unified Sensor` must be installed via `arduino-cli`)
- C++ (Arduino core) for ESP32 firmware
- No database server — state is JSON files (`db.json`, `manifest.json`, `fleet_state.json`). Do not introduce a database engine unless asked; this is a deliberate simplicity choice for the current phase.

## Setup & Commands

```bash
# install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# configure
echo 'OPENAI_API_KEY="..."' > .env

# run (single process: agent + OTA server + fleet dashboard + firmware storage)
python run.py
# -> http://localhost:5001  (health: /health, dashboard: /dashboard)

# test
python test_api.py
python autonomous_demo.py
python run_training_scenarios.py all
```

There is currently no automated test suite beyond `test_api.py` and the demo/training scripts. If you add new tools or endpoints, add a corresponding scenario to `training_data.json` and/or a check in `test_api.py` rather than only manual curl testing.

## Fleet & Sensor Node Model

Four sensor node roles exist conceptually (see `docs/PRD.md` for rationale):

| device_id | sensor_type | hardware |
|---|---|---|
| `node-climate` | temperature (+ humidity) | DHT22 |
| `node-air` | air quality (raw analog) | MQ-135 |
| `node-presence` | motion / light | PIR + LDR |
| `node-structural` | proximity/distance | HC-SR04 |

Nodes POST to `/report/{device_id}` using **query parameters** (`sensor_type`, `value`, `event`) — not a JSON body. This is intentional and must not be changed without updating both the ESP32 firmware templates and `docs/API_SPEC.md` together. A prior draft had a mismatch here (ESP32 sent JSON, server expected query params) — treat any reintroduction of that mismatch as a regression.

## Agent Behavior Contract

The `FirmwareAgent` in `agent.py` MUST, before writing new firmware:
1. Call `get_fleet_context_tool()` to read every node's latest state via `/fleet`.
2. Reason about whether the triggering event is isolated or correlated with other nodes' current signals.
3. Include a code comment block in the generated `.cpp` explaining which other nodes' signals (if any) influenced the decision.
4. Decide single-node (`compile_and_deploy_firmware`) vs fleet-wide (`push_firmware_to_multiple_nodes`) deployment based on that reasoning.

Do not let the agent regenerate the WiFi-connect / OTA-check plumbing from the node templates — only the `readAndActOnSensor()` / sensor-logic block should be model-generated. This is a hard constraint: firmware that loses its OTA-check loop cannot be updated again without a physical USB reflash.

## Coding Conventions

- Python: type hints on all new function signatures, docstrings on LangChain tools (the docstring is what the LLM sees as the tool description — keep it precise and behavior-defining, not just descriptive).
- FastAPI routes: keep request/response shapes exactly matching `docs/API_SPEC.md`. If you need to change a contract, update the spec doc in the same change.
- Firmware `.cpp`/`.ino` templates: keep `BASE_URL`, `DEVICE_ID`, `SENSOR_TYPE`, `FIRMWARE_VERSION` as the only per-node constants at the top of the file; don't hardcode IPs anywhere else in a template.
- Prefer editing `fleet_state.json`/`manifest.json` via the existing `_load_json`/`_save_json` helpers in `app.py` rather than opening files ad hoc elsewhere.
- No secrets in committed files — `OPENAI_API_KEY` comes from `.env`, never hardcode it.

## What NOT to Do

- Don't add Raspberry Pi-specific code, paths, or systemd units yet — that's a future migration (`docs/TRD.md` §7), not current scope.
- Don't add a real database (Postgres/SQLite/etc.) unless explicitly requested — JSON-file state is a deliberate current-phase choice per `docs/PRD.md`.
- Don't change `/report/{device_id}` to accept a JSON body without updating the ESP32 templates and `docs/API_SPEC.md` in the same change.
- Don't remove or bypass the "agent must check fleet context before writing firmware" behavior — it's the project's core differentiator, not an optional feature.
- Don't add firmware authentication/security hardening as a side effect of an unrelated task — it's tracked deliberately in `docs/ROADMAP.md` as its own item, since it changes the ESP32 client code too.

## When Starting a Task

1. Check `docs/ROADMAP.md` for whether this task is already scoped and sequenced.
2. Check `docs/API_SPEC.md` if the task touches any endpoint.
3. Run `python test_api.py` before and after your change to confirm you haven't broken existing behavior.
4. If you add or change a LangChain tool, update its docstring and add/update a scenario in `training_data.json`.
