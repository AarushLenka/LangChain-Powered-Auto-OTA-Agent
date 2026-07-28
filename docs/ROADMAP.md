# Roadmap

Sequenced backlog. Items are grouped by phase; within a phase, do them roughly top to bottom, since later items in a phase often assume earlier ones are done. Do not start a later phase's items while an earlier phase has open blocking items, unless explicitly told to jump ahead.

## Phase 1 — Single-Laptop Fleet (current phase, in progress)

- [ ] Fold OTA/fleet/dashboard routes into `ota_agent/app.py` (single process, single port)
- [ ] Implement `get_fleet_context_tool()` and wire it into the agent's system prompt as a mandatory pre-firmware-write step
- [ ] Implement `push_firmware_to_multiple_nodes()` and give the agent explicit criteria (in its system prompt) for when to use it vs single-node deployment
- [ ] Split each node's ESP32 sketch into a shared, non-regenerable skeleton + a per-node sensor block template (`ota_agent/templates/`)
- [ ] Flash and validate all four node roles (`node-climate`, `node-air`, `node-presence`, `node-structural`) against the laptop-hosted server
- [ ] Add at least 5 new scenarios to `training_data.json` that specifically test cross-sensor correlation (not just single-sensor thresholds) — e.g. "temp critical + gas critical + no motion" vs "temp critical alone"
- [ ] Confirm dashboard (`/dashboard`) correctly reflects live multi-node state during a correlated-event test

## Phase 2 — Robustness on Laptop (before Pi migration)

- [ ] Add a staleness cutoff to `get_fleet_context_tool()` — discount or flag readings older than a configurable threshold (e.g. 60s) so the agent doesn't reason over stale data during timing races
- [ ] Normalize error responses across `/check` and `/download` to proper HTTP status codes instead of `200` with an error body (coordinate with `docs/API_SPEC.md` — update the spec in the same change)
- [ ] Add a basic automated test that exercises `/report` → `/fleet` → agent's fleet-context read, to catch the query-param/JSON-body class of bug going forward
- [ ] Add a "last known good" firmware retention policy so a failed OTA push can be manually recovered without hunting through `firmware_store/`

## Phase 3 — Raspberry Pi Migration (do not start until explicitly requested)

See `docs/TRD.md` §7 for the full technical plan. High-level sequence:
- [ ] Copy project to Pi, install deps in venv
- [ ] Reserve a static LAN IP for the Pi in the router
- [ ] Perform one final laptop-hosted OTA push to every node that only changes `BASE_URL` to the Pi's static IP
- [ ] Wrap the app in a systemd service on the Pi with `Restart=always`
- [ ] Verify all nodes report into the Pi-hosted dashboard before decommissioning the laptop process

## Phase 4 — Deferred / Explicitly Out of Scope Until Requested

These are real, known gaps. They are deliberately not being worked on yet — do not pick these up opportunistically as part of unrelated tasks.

- [ ] API authentication (all endpoints currently unauthenticated)
- [ ] Automatic rollback on failed/bad firmware
- [ ] Firmware signing / integrity verification before flashing
- [ ] A/B testing for firmware updates across a subset of the fleet
- [ ] Web dashboard beyond the current auto-refresh HTML view (e.g. a proper frontend framework, historical charts)
- [ ] Cloud IoT integration (AWS IoT / Azure IoT)
- [ ] Multi-tenant / multi-operator support

## Notes for Claude Code

- Before starting any item, re-read `CLAUDE.md`'s "What NOT to Do" section — several of the Phase 4 items are explicitly excluded from current work for good reasons, not oversights.
- If a Phase 1 or 2 item requires touching an API contract, update `docs/API_SPEC.md` in the same change, not as a follow-up.
- If you find a bug or gap not listed here, add it to the appropriate phase rather than fixing it silently if it's out of the current phase's scope — flag it to the operator instead.
