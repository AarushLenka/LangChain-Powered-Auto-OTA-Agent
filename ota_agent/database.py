import json
import os
from typing import Optional, Dict, Any


class DeviceDatabase:
    """Handles device state persistence."""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Reads the state of a device from the DB."""
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
            return data.get(device_id)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def update_firmware_path(self, device_id: str, new_path: str) -> bool:
        """Updates the firmware path for a device in the DB."""
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
            
            if device_id in data:
                data[device_id]['current_firmware_path'] = new_path
                if 'version_history' not in data[device_id]:
                    data[device_id]['version_history'] = []
                data[device_id]['version_history'].append(new_path)
                
                with open(self.db_file, 'w') as f:
                    json.dump(data, f, indent=2)
                return True
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return False
    
    def initialize_device(self, device_id: str, initial_firmware_path: str):
        """Initialize a device in the database if it doesn't exist."""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {}
            
            if device_id not in data:
                data[device_id] = {
                    "device_id": device_id,
                    "current_firmware_path": initial_firmware_path,
                    "sensors": {
                        "A": {"pin": 1, "type": "analog"},
                        "C": {"pin": 3, "type": "analog"},
                        "D": {"pin": 4, "type": "digital"}
                    },
                    "version_history": [initial_firmware_path]
                }
                
                with open(self.db_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error initializing device: {e}")