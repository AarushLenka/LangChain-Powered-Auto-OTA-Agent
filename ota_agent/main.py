import os
import sys
from .config import Config
from .database import DeviceDatabase
from .agent import FirmwareAgent
from .app import create_app


def initialize_firmware_structure():
    """Initialize firmware directory and default firmware."""
    device_id = "device-001"
    os.makedirs(os.path.join(Config.FIRMWARE_DIR, device_id), exist_ok=True)
    initial_firmware_path = os.path.join(Config.FIRMWARE_DIR, device_id, "v1.0.cpp")
    
    if not os.path.exists(initial_firmware_path):
        initial_code = """// Firmware Version: 1.0
// Active Sensors: A, C, D
#include <Arduino.h>
void setup() {
    Serial.begin(115200);
    Serial.println("Device starting... Firmware v1.0");
}
void loop() {
    int sensor_a_value = analogRead(1);
    Serial.print("Sensor A: "); Serial.println(sensor_a_value);
    if (sensor_a_value > 100) { Serial.println("EVENT: sensor_A_threshold_exceeded"); }
    delay(5000);
}
"""
        with open(initial_firmware_path, 'w') as f:
            f.write(initial_code)
    
    # Initialize device in database
    db = DeviceDatabase(Config.DB_FILE)
    db.initialize_device(device_id, initial_firmware_path)


def main():
    """Main entry point."""
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize structures
        initialize_firmware_structure()
        
        # Create agent and app
        agent = FirmwareAgent()
        app = create_app(agent)
        
        # Run server
        print(f"Starting OTA Agent Server on port {Config.FLASK_PORT}...")
        app.run(port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()