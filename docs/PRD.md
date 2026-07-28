# Product Requirements Document (PRD)

## 1. Product Name
LangChain-Powered Auto-OTA-Agent — Multi-Sensor Fleet Edition

## 2. Problem Statement
Most hobbyist IoT-OTA demos are single-device, single-sensor, single-rule: "if temperature > X, push new firmware." This doesn't reflect how real deployments work — a factory floor, greenhouse, or smart building has *heterogeneous* sensors whose signals only mean something in combination. A temperature spike alone is a warm day; a temperature spike plus a gas spike plus no detected occupants is a hazard.

This project builds a small, real (not simulated) hardware fleet where an LLM agent autonomously writes and deploys firmware, and — critically — makes that decision by reasoning across the *entire fleet's* current sensor state, not just the event that triggered it.

## 3. Goals
- Demonstrate autonomous, LLM-driven firmware generation and OTA deployment on real ESP32 hardware (not a simulation).
- Demonstrate cross-sensor, cross-device reasoning: the same raw event should produce different agent behavior depending on fleet-wide context.
- Keep the system runnable entirely on a laptop for development and demos, with a clear, low-risk migration path to an always-on Raspberry Pi later.
- Produce a live, human-readable fleet dashboard suitable for a demo recording.

## 4. Non-Goals (for this phase)
- Production-grade security (auth, encrypted OTA, signed firmware) — explicitly deferred, tracked in `ROADMAP.md`.
- Automatic rollback on failed updates — deferred.
- Multi-tenant / multi-user support — single operator, single fleet.
- Cloud deployment (AWS/Azure IoT) — deferred, mentioned in original roadmap only as a future extension.
- Raspberry Pi hosting — deferred to a later, explicitly-scoped migration (see `TRD.md` §7). Do not build this now.

## 5. Target User
A single technically-capable operator (e.g. a student/engineer building a portfolio or research demo) who wants to:
- Run the whole system locally without extra infrastructure.
- See the agent's reasoning reflected in generated firmware comments.
- Demo believable, differentiated fleet behavior on camera.

## 6. Core User Stories

1. **As the operator**, I can power on 1-4 ESP32 nodes, each with a different sensor, and see them all appear on a live dashboard within seconds.
2. **As the operator**, when one node reports an anomalous reading in isolation, I want the agent to generate a low-urgency, single-node firmware update — not a fleet-wide disruption.
3. **As the operator**, when multiple nodes report a correlated pattern (e.g. heat + gas + no motion), I want the agent to recognize the correlation and push an appropriately elevated firmware profile to multiple relevant nodes at once.
4. **As the operator**, I want the generated firmware's code comments to explain *why* the agent made its decision, referencing which other nodes' signals it considered — so the reasoning is auditable, not a black box.
5. **As the operator**, I want to run everything with `python run.py` and no additional infrastructure, so I can iterate quickly during development.
6. **As the operator**, when I'm ready to leave the system running unattended, I want a documented, low-friction path to move the always-on parts to a Raspberry Pi without re-architecting the agent or ESP32 firmware logic.

## 7. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | System exposes a single FastAPI process serving: agent trigger endpoint, OTA firmware upload/check/download, fleet sensor-state reporting, and a live dashboard. |
| FR-2 | Each ESP32 node periodically polls for firmware updates and reports its current sensor reading. |
| FR-3 | The agent, before generating firmware, retrieves current state of every node in the fleet. |
| FR-4 | The agent can deploy firmware to a single node or to multiple nodes atomically as part of one decision. |
| FR-5 | Generated firmware for any node preserves the OTA-check/WiFi plumbing unchanged; only sensor-logic is agent-generated. |
| FR-6 | Dashboard auto-refreshes and shows, per node: sensor type, latest value, latest event, current firmware version, time since last report. |
| FR-7 | System supports at least 4 distinct sensor node roles: climate, air quality, presence/light, structural. |
| FR-8 | Training/eval data (`training_data.json`) includes scenarios that specifically test cross-sensor correlation, not only single-sensor thresholds. |

## 8. Non-Functional Requirements

- **Simplicity over infra:** prefer JSON-file state and a single process over adding a database or second server, for this phase.
- **Auditability:** every firmware generation must leave a human-readable trace of the agent's reasoning in code comments.
- **Portability:** nothing in the agent, tools, or ESP32 sensor logic should assume a specific host (laptop vs Pi) — only network config (`BASE_URL`, static IP) should differ between environments.
- **Latency:** end-to-end (sensor event → new firmware live on device) should complete within a few minutes for a demo; compilation time (20-60s via `arduino-cli`) is an accepted current bottleneck, not a defect.

## 9. Success Metrics (Qualitative, Demo-Oriented)

- A single-signal event and a multi-signal correlated event, triggered back to back, visibly produce different agent behavior (different firmware scope, different comments) in a live demo.
- The dashboard alone, with no narration, communicates "this is a fleet of different sensors being managed by one AI agent" to an outside viewer.
- The system runs start-to-finish on a laptop with no Pi, no cloud account beyond OpenAI, and no manual firmware pushes after initial USB flashing.

## 10. Open Questions / Risks

- **IP fragility on laptop:** DHCP-assigned IP can change between sessions, breaking `BASE_URL` in already-flashed firmware. Mitigated short-term by documentation (see `TRD.md`); resolved properly only after Pi migration with a static IP reservation.
- **Compile time scaling:** if more node types are added, `arduino-cli` compile time per firmware push may become the dominant latency factor. Not a blocker at 4 nodes.
- **Agent reasoning consistency:** LLM-driven decisions on ambiguous fleet states may vary run to run even at low temperature. Mitigate via explicit training scenarios and prompt constraints in `agent.py`, not by trying to make the LLM fully deterministic.
