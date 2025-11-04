import os
import sys
import uvicorn
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
// Description: Initial firmware that monitors sensors A, C, D based on device schema
#include <Arduino.h>

// --- Pin Definitions (based on sensor_schema)
#define SENSOR_A_PIN 1  // temperature
#define SENSOR_C_PIN 3  // pressure  
#define SENSOR_D_PIN 4  // light_intensity

// --- Configuration ---
const int SENSOR_A_THRESHOLD = 100;

void setup() {
    Serial.begin(115200);
    while (!Serial);
    Serial.println("============================");
    Serial.println("Device starting... Firmware v1.0");
    Serial.println("Mode: Monitoring Sensors A, C, D");
    Serial.println("============================");
    
    pinMode(SENSOR_A_PIN, INPUT);
    pinMode(SENSOR_C_PIN, INPUT);
    pinMode(SENSOR_D_PIN, INPUT);
}

void loop() {
    int sensor_a_value = analogRead(SENSOR_A_PIN);
    int sensor_c_value = analogRead(SENSOR_C_PIN);
    int sensor_d_value = analogRead(SENSOR_D_PIN);

    Serial.print("DATA: Sensor A (temperature): ");
    Serial.println(sensor_a_value);
    Serial.print("DATA: Sensor C (pressure): ");
    Serial.println(sensor_c_value);
    Serial.print("DATA: Sensor D (light_intensity): ");
    Serial.println(sensor_d_value);

    if (sensor_a_value > SENSOR_A_THRESHOLD) {
        Serial.println("EVENT: sensor_A_threshold_exceeded");
    }

    Serial.println("---");
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
        
        # Run server with uvicorn
        print(f"Starting OTA Agent Server on port {Config.SERVER_PORT}...")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=Config.SERVER_PORT,
            log_level="info" if not Config.DEBUG else "debug"
        )
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()