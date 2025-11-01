import json
import os
from datetime import datetime
from langchain_core.tools import tool
from .database import DeviceDatabase
from .config import Config


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


def get_all_tools():
    """Returns all available tools for the agent."""
    return [
        read_current_firmware,
        write_new_firmware,
        get_device_state_tool,
        trigger_ota_flash
    ]