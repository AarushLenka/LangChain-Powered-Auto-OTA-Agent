import os
import sys
import uvicorn
from .config import Config
from .agent import FirmwareAgent
from .app import create_app


FLEET_NODES = ["node-climate", "node-air", "node-presence", "node-structural"]


def initialize_firmware_structure():
    """Backfill each fleet node's firmware dir + v1.0.cpp placeholder.

    db.json is the source of truth for the fleet roster (seeded ahead of time);
    this only ensures the on-disk v1.0.cpp exists so read_current_firmware works
    before the agent generates anything. Real WiFi/OTA plumbing lives in
    ota_agent/templates/ and is applied when a node is first flashed.
    """
    for device_id in FLEET_NODES:
        node_dir = os.path.join(Config.FIRMWARE_DIR, device_id)
        os.makedirs(node_dir, exist_ok=True)
        v1_path = os.path.join(node_dir, "v1.0.cpp")
        if not os.path.exists(v1_path):
            with open(v1_path, 'w') as f:
                f.write(
                    "// Firmware Version: 1.0 (placeholder)\n"
                    f"// Device: {device_id}\n"
                    "// Sensor-logic block is agent-generated; the WiFi/OTA\n"
                    "// skeleton comes from ota_agent/templates/.\n"
                )


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