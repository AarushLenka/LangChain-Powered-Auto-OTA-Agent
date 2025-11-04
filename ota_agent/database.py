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
        except FileNotFoundError:
            print(f"Database file {self.db_file} not found")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {self.db_file}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error reading device state: {e}")
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
            else:
                print(f"Device {device_id} not found in database")
                return False
        except FileNotFoundError:
            print(f"Database file {self.db_file} not found")
            return False
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {self.db_file}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error updating firmware path: {e}")
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
                    "current_firmware_path": initial_firmware_path,
                    "sensor_schema": {
                        "A": {"type": "temperature", "pin": 1, "unit": "celsius"},
                        "B": {"type": "humidity", "pin": 2, "unit": "percentage"},
                        "C": {"type": "pressure", "pin": 3, "unit": "pascal"},
                        "D": {"type": "light_intensity", "pin": 4, "unit": "lux"},
                        "E": {"type": "motion", "pin": 5, "unit": "boolean"},
                        "F": {"type": "gps_latitude", "pin": 6, "unit": "degrees"}
                    },
                    "version_history": [initial_firmware_path]
                }
                
                with open(self.db_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error initializing device: {e}")