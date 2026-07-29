import glob
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime

import requests
from langchain_core.tools import tool

from .database import DeviceDatabase
from .config import Config

# ESP32 target + local upload endpoint. arduino-cli must be installed on PATH
# with core `esp32:esp32` and the DHT/Adafruit libraries (see CLAUDE.md).
FQBN = "esp32:esp32:esp32"
UPLOAD_URL = f"http://localhost:{Config.SERVER_PORT}/upload"


# Initialize database instance
db = DeviceDatabase(Config.DB_FILE)


@tool
def read_current_firmware(device_id: str) -> str:
    """Reads the current firmware code for a given device ID."""
    print(f"\nTOOL: Reading firmware for device '{device_id}'...")
    state = db.get_device_state(device_id)
    if not state or 'current_firmware_path' not in state:
        return f"Error: No firmware path found for device_id '{device_id}'."
    
    firmware_path = state['current_firmware_path']
    try:
        with open(firmware_path, 'r') as f:
            content = f.read()
        print(f"TOOL: Successfully read {firmware_path}")
        return content
    except FileNotFoundError:
        return f"Error: Firmware file not found at path: {firmware_path}"


@tool
def write_new_firmware(device_id: str, new_code: str) -> str:
    """Writes new firmware code to a file for a specific device."""
    print(f"\nTOOL: Writing new firmware for device '{device_id}'...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_version_str = f"v{timestamp}"
    device_firmware_dir = os.path.join(Config.FIRMWARE_DIR, device_id)
    os.makedirs(device_firmware_dir, exist_ok=True)
    new_firmware_path = os.path.join(device_firmware_dir, f"{new_version_str}.cpp")

    try:
        with open(new_firmware_path, 'w') as f:
            f.write(new_code)
        db.update_firmware_path(device_id, new_firmware_path)
        print(f"TOOL: New firmware saved to {new_firmware_path} and DB updated.")
        return f"Successfully wrote new firmware version {new_version_str} for device {device_id}."
    except Exception as e:
        return f"Error writing firmware: {e}"


@tool
def get_fleet_context_tool() -> str:
    """Returns the current sensor state of EVERY node in the fleet as JSON.

    Call this FIRST, before writing or deploying any firmware. It reports each
    node's latest sensor_type, value, event, and last_seen timestamp so you can
    decide whether the triggering event is isolated or correlated with other
    nodes' signals. Returns an empty object if no node has reported yet.

    Each node is additionally annotated with:
      - "age_seconds": how long ago that reading arrived (null if unknown)
      - "stale": true if the reading is older than the staleness threshold
        (Config.FLEET_STALENESS_SECONDS) or its timestamp is missing/unreadable.

    A node with "stale": true is NOT current evidence. You MUST NOT treat a stale
    reading as proof of a live correlated condition; base an ISOLATED vs CORRELATED
    judgment on the fresh ("stale": false) readings only. If a stale node's signal
    would have changed your decision, say so explicitly in the firmware comment
    block instead of assuming the stale value still holds.
    """
    print("\nTOOL: Reading fleet context from all nodes...")
    try:
        with open(Config.FLEET_STATE_FILE, "r") as f:
            fleet = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        fleet = {}

    now = time.time()
    annotated: dict[str, object] = {}
    for device_id, state in fleet.items():
        if not isinstance(state, dict):
            annotated[device_id] = state
            continue
        last_seen = state.get("last_seen")
        age = round(now - last_seen, 1) if isinstance(last_seen, (int, float)) else None
        annotated[device_id] = {
            **state,
            "age_seconds": age,
            "stale": age is None or age > Config.FLEET_STALENESS_SECONDS,
        }
    return json.dumps(annotated, indent=2)


@tool
def get_device_state_tool(device_id: str) -> str:
    """Retrieves the sensor schema and current configuration for a device."""
    print(f"\nTOOL: Getting state for device '{device_id}'...")
    state = db.get_device_state(device_id)
    if state:
        return json.dumps(state, indent=2)
    return f"Error: No state found for device_id '{device_id}'."


@tool
def trigger_ota_flash(device_id: str) -> str:
    """Simulates triggering an OTA flash process for the device."""
    print(f"\nTOOL: Triggering OTA flash for device '{device_id}'...")
    state = db.get_device_state(device_id)
    latest_firmware = state.get('current_firmware_path', 'N/A') if state else 'N/A'
    log_message = f"OTA flash triggered for device '{device_id}'. Device will now update to: '{latest_firmware}'."
    print(f"TOOL: {log_message}")
    return log_message


@tool
def compile_and_deploy_firmware(device_id: str) -> str:
    """Compiles a single node's current firmware with arduino-cli and OTA-deploys it.

    Use this for an ISOLATED event affecting ONE node — when get_fleet_context_tool
    shows the triggering signal is not correlated with anomalies on other nodes.

    Reads the device's current_firmware_path (.cpp) from the database, compiles it
    headlessly for the ESP32 target (esp32:esp32:esp32) via arduino-cli, then uploads
    the resulting .bin to the local OTA server (POST /upload/{device_id}) so manifest.json
    updates and the node picks it up on its next /check poll.

    Returns a success string naming the device and deployed version, or a clear error
    string beginning with 'arduino-cli not found', 'COMPILE FAILED:', or 'DEPLOY FAILED:'.
    This REPLACES the old simulated trigger_ota_flash for real deployment.
    """
    print(f"\nTOOL: Compiling and deploying firmware for '{device_id}'...")
    state = db.get_device_state(device_id)
    if not state or "current_firmware_path" not in state:
        return f"COMPILE FAILED: no firmware path in DB for device_id '{device_id}'."

    cpp_path = state["current_firmware_path"]
    if not os.path.exists(cpp_path):
        return f"COMPILE FAILED: firmware file not found at '{cpp_path}'."

    if shutil.which("arduino-cli") is None:
        return (
            "arduino-cli not found on PATH. Install arduino-cli and the esp32:esp32 "
            "core plus 'DHT sensor library' + 'Adafruit Unified Sensor' before deploying."
        )

    # arduino-cli requires the sketch file's basename to match its folder name.
    version = os.path.splitext(os.path.basename(cpp_path))[0]  # e.g. "v20260727153000"
    tmp_dir = tempfile.mkdtemp(prefix=f"otabuild-{device_id}-")
    try:
        sketch_dir = os.path.join(tmp_dir, version)
        build_dir = os.path.join(tmp_dir, "build")
        os.makedirs(sketch_dir, exist_ok=True)
        shutil.copy(cpp_path, os.path.join(sketch_dir, f"{version}.ino"))

        try:
            result = subprocess.run(
                ["arduino-cli", "compile", "--fqbn", FQBN,
                 "--output-dir", build_dir, sketch_dir],
                capture_output=True, text=True, timeout=120,
            )
        except FileNotFoundError:
            return "arduino-cli not found on PATH."
        except subprocess.TimeoutExpired:
            return "COMPILE FAILED: arduino-cli timed out after 120s."

        if result.returncode != 0:
            return f"COMPILE FAILED: {(result.stderr or result.stdout).strip()}"

        # arduino-cli emits several .bin files; httpUpdate wants the application
        # image only. Name it exactly rather than filtering by exclusion:
        #   <sketch>.ino.bin            app image      (what OTA needs)
        #   <sketch>.ino.merged.bin     4MB full-flash image, starts 0xFF
        #   <sketch>.ino.bootloader.bin bootloader
        #   <sketch>.ino.partitions.bin partition table
        # Uploading merged.bin would hand the node a full-flash image to apply
        # as an app update.
        bin_path = os.path.join(build_dir, f"{version}.ino.bin")
        if not os.path.exists(bin_path):
            produced = [os.path.basename(b) for b in glob.glob(os.path.join(build_dir, "*.bin"))]
            return (f"COMPILE FAILED: expected app image {version}.ino.bin in {build_dir}; "
                    f"got {produced}.")

        # An ESP32 app image starts with the 0xE9 magic byte. Refuse anything else
        # rather than serving a node an image it cannot boot.
        with open(bin_path, "rb") as fh:
            if fh.read(1) != b"\xe9":
                return (f"COMPILE FAILED: {os.path.basename(bin_path)} is not a valid ESP32 "
                        "app image (missing 0xE9 magic byte).")

        try:
            with open(bin_path, "rb") as fh:
                resp = requests.post(
                    f"{UPLOAD_URL}/{device_id}",
                    params={"version": version},
                    files={"file": (f"{version}.bin", fh, "application/octet-stream")},
                    timeout=30,
                )
        except requests.RequestException as e:
            return f"DEPLOY FAILED: could not reach OTA server at {UPLOAD_URL}: {e}"

        if resp.status_code != 200:
            return f"DEPLOY FAILED: upload returned {resp.status_code}: {resp.text}"

        print(f"TOOL: Deployed {version} to {device_id}.")
        return f"Successfully compiled and deployed firmware {version} to {device_id}."
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@tool
def push_firmware_to_multiple_nodes(device_ids: list[str]) -> str:
    """Compiles and OTA-deploys each listed node's current firmware, fleet-wide.

    Use this ONLY for a CORRELATED multi-node pattern — when get_fleet_context_tool
    shows several nodes reporting signals that together warrant an elevated firmware
    profile (e.g. heat on node-climate + gas on node-air + no_motion on node-presence
    indicating an unoccupied hazard). Do NOT use this for an isolated single-node event;
    use compile_and_deploy_firmware for that instead. Pass only the device_ids whose
    firmware you actually rewrote for the correlated response.

    Runs compile_and_deploy_firmware for each device_id (each compiles its OWN current
    firmware) and returns a per-node success/failure summary. A failure on one node does
    not abort the others. This REPLACES the old simulated trigger_ota_flash for real
    fleet-wide deployment.
    """
    print(f"\nTOOL: Fleet-wide deploy to {device_ids}...")
    lines = []
    ok = 0
    for device_id in device_ids:
        result = compile_and_deploy_firmware.invoke({"device_id": device_id})
        success = result.startswith("Successfully")
        ok += success
        lines.append(f"  [{'OK' if success else 'FAIL'}] {device_id}: {result}")
    header = f"Fleet-wide deploy: {ok}/{len(device_ids)} nodes succeeded."
    return header + "\n" + "\n".join(lines)


def get_all_tools():
    """Returns all available tools for the agent."""
    return [
        get_fleet_context_tool,
        read_current_firmware,
        write_new_firmware,
        get_device_state_tool,
        trigger_ota_flash,
        compile_and_deploy_firmware,
        push_firmware_to_multiple_nodes,
    ]