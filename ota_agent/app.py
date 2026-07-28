import json
import os
import time
import traceback
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from .agent import FirmwareAgent
from .config import Config


class EventRequest(BaseModel):
    device_id: str
    event_details: str
    policy: str = None  # Optional - for backward compatibility


class HealthResponse(BaseModel):
    status: str


class EventResponse(BaseModel):
    success: bool
    agent_output: str


def _load_json(path: str) -> Dict[str, Any]:
    """Load a JSON state file, returning {} if it doesn't exist yet."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_json(path: str, data: Dict[str, Any]) -> None:
    """Persist a JSON state file with stable formatting."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def create_app(agent: FirmwareAgent) -> FastAPI:
    """Factory function to create and configure FastAPI app."""
    app = FastAPI(title="OTA Agent", description="Autonomous IoT Firmware Management System")

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(status="healthy")

    @app.post("/trigger-agent", response_model=EventResponse)
    async def handle_event(request: EventRequest):
        """Handle incoming device events and trigger agent."""
        print(f"\n\n--- New Event for {request.device_id} ---")
        print(f"Event: {request.event_details}")
        if request.policy:
            print(f"Policy: {request.policy}")
        else:
            print("Mode: Autonomous Decision Making")
        print("--- Invoking Agent ---")

        input_string = FirmwareAgent.create_agent_prompt(
            request.device_id, request.event_details, request.policy
        )

        try:
            result = agent.invoke({"input": input_string})
            return EventResponse(success=True, agent_output=result.get("output", ""))
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/upload/{device_id}")
    async def upload_firmware(device_id: str, version: str, file: UploadFile = File(...)):
        """Store a compiled firmware binary and update the manifest.

        Called internally by compile_and_deploy_firmware(), not by ESP32 nodes.
        """
        store_dir = os.path.join(Config.FIRMWARE_STORE_DIR, device_id)
        os.makedirs(store_dir, exist_ok=True)
        bin_path = os.path.join(store_dir, f"{version}.bin")
        with open(bin_path, "wb") as f:
            f.write(await file.read())

        manifest = _load_json(Config.MANIFEST_FILE)
        manifest[device_id] = {"version": version, "path": bin_path}
        _save_json(Config.MANIFEST_FILE, manifest)

        return {"status": "uploaded", "device_id": device_id, "version": version}

    @app.get("/check/{device_id}")
    async def check_update(device_id: str, current_version: str):
        """Report whether a newer firmware version exists for this node."""
        manifest = _load_json(Config.MANIFEST_FILE)
        entry = manifest.get(device_id)
        if not entry:
            return {"update_available": False}
        latest = entry["version"]
        return {"update_available": latest != current_version, "latest_version": latest}

    @app.get("/download/{device_id}")
    async def download_firmware(device_id: str):
        """Return the current .bin for a device (called by httpUpdate on ESP32)."""
        manifest = _load_json(Config.MANIFEST_FILE)
        entry = manifest.get(device_id)
        if not entry or not os.path.exists(entry["path"]):
            # Known inconsistency (API_SPEC §/download): 200 with error body.
            return JSONResponse({"error": "no firmware found"})
        return FileResponse(entry["path"], media_type="application/octet-stream")

    @app.post("/report/{device_id}")
    async def report_state(device_id: str, sensor_type: str, value: float, event: str = ""):
        """Record a node's latest sensor reading into fleet_state.json.

        Uses query params, not a JSON body — load-bearing contract (TRD §5).
        """
        state = _load_json(Config.FLEET_STATE_FILE)
        state[device_id] = {
            "sensor_type": sensor_type,
            "value": value,
            "event": event,
            "last_seen": time.time(),
        }
        _save_json(Config.FLEET_STATE_FILE, state)
        return {"status": "recorded"}

    @app.get("/fleet")
    async def get_fleet():
        """Return the full current fleet state (source for get_fleet_context_tool)."""
        return _load_json(Config.FLEET_STATE_FILE)

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        """Human-readable HTML fleet view, auto-refreshes every 5s."""
        state = _load_json(Config.FLEET_STATE_FILE)
        manifest = _load_json(Config.MANIFEST_FILE)
        now = time.time()

        rows = []
        for device_id, s in sorted(state.items()):
            fw = manifest.get(device_id, {}).get("version", "—")
            age = f"{now - s.get('last_seen', now):.0f}s"
            event = s.get("event") or "—"
            rows.append(
                f"<tr><td>{device_id}</td><td>{s.get('sensor_type','')}</td>"
                f"<td>{s.get('value','')}</td><td>{event}</td>"
                f"<td>{fw}</td><td>{age}</td></tr>"
            )
        if not rows:
            rows.append("<tr><td colspan='6'>No nodes have reported yet.</td></tr>")

        return (
            "<!doctype html><html><head><meta http-equiv='refresh' content='5'>"
            "<title>Fleet Dashboard</title>"
            "<style>body{font-family:sans-serif;margin:2rem}"
            "table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #ccc;padding:.5rem;text-align:left}"
            "th{background:#222;color:#fff}</style></head><body>"
            "<h1>Auto-OTA Fleet</h1><table><tr>"
            "<th>Device</th><th>Sensor</th><th>Value</th><th>Event</th>"
            "<th>Firmware</th><th>Last report</th></tr>"
            + "".join(rows)
            + "</table></body></html>"
        )

    return app
