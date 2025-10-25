import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# --- CONFIGURATION ---
# IMPORTANT: Set your OpenAI API key in your environment variables
# export OPENAI_API_KEY="your_key_here"
# If not set, the script will exit.
if "OPENAI_API_KEY" not in os.environ:
    print("Error: OPENAI_API_KEY environment variable not set.")
    exit()

DB_FILE = "db.json"
FIRMWARE_DIR = "firmware"

# --- DATABASE HELPERS ---
def get_device_state(device_id):
    """Reads the state of a device from the DB.""" [cite: 158-159]
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        return data.get(device_id)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def update_device_firmware_path(device_id, new_path):
    """Updates the firmware path for a device in the DB.""" [cite: 164-165]
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        if device_id in data:
            data[device_id]['current_firmware_path'] = new_path
            if 'version_history' not in data[device_id]:
                data[device_id]['version_history'] = []
            data[device_id]['version_history'].append(new_path)
            with open(DB_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return False

# --- LANGCHAIN CUSTOM TOOLS ---
class ReadFirmwareTool(BaseTool):
    name = "read_current_firmware"
    description = "Reads the current firmware code for a given device ID. Input must be the device_id as a string." [cite: 177-180]

    def _run(self, device_id: str) -> str:
        """Reads and returns the content of the current firmware file.""" [cite: 181-182]
        print(f"\nTOOL: Reading firmware for device '{device_id}'...")
        state = get_device_state(device_id)
        if not state or 'current_firmware_path' not in state:
            return f"Error: No state or firmware path found for device_id '{device_id}'." [cite: 185-186]
        firmware_path = state['current_firmware_path']
        try:
            with open(firmware_path, 'r') as f:
                content = f.read()
            print(f"TOOL: Successfully read {firmware_path}")
            return content
        except FileNotFoundError:
            return f"Error: Firmware file not found at path: {firmware_path}" [cite: 192-193]

class WriteFirmwareTool(BaseTool):
    name = "write_new_firmware"
    description = "Writes new firmware code to a file for a specific device. Input must be a dictionary with 'device_id' and 'new_code'." [cite: 194-197]

    def _run(self, device_id: str, new_code: str) -> str:
        """Saves the new firmware and updates the database.""" [cite: 198-199]
        print(f"\nTOOL: Writing new firmware for device '{device_id}'...")
        # Create a new versioned file path
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_version_str = f"v{timestamp}"
        device_firmware_dir = os.path.join(FIRMWARE_DIR, device_id)
        os.makedirs(device_firmware_dir, exist_ok=True)
        new_firmware_path = os.path.join(device_firmware_dir, f"{new_version_str}.cpp")
        try:
            with open(new_firmware_path, 'w') as f:
                f.write(new_code)
            # Update the database to point to the new firmware
            update_device_firmware_path(device_id, new_firmware_path)
            print(f"TOOL: New firmware saved to {new_firmware_path} and DB updated.")
            return f"Successfully wrote new firmware version {new_version_str} for device {device_id}." [cite: 210-211]
        except Exception as e:
            return f"Error writing firmware: {e}" [cite: 212-213]

class DeviceStateTool(BaseTool):
    name = "get_device_state"
    description = "Retrieves the sensor schema and current configuration for a device. Input must be the device_id as a string." [cite: 214-217]

    def _run(self, device_id: str) -> str:
        """Returns the device state as a JSON string.""" [cite: 218-219]
        print(f"\nTOOL: Getting state for device '{device_id}'...")
        state = get_device_state(device_id)
        if state:
            return json.dumps(state)
        return f"Error: No state found for device_id '{device_id}'." [cite: 224]

class TriggerOtaFlashTool(BaseTool):
    name = "trigger_ota_flash"
    description = "Simulates triggering an Over-The-Air flash process for the device. The device will then pull the latest firmware. Input must be the device_id as a string." [cite: 225-227]

    def _run(self, device_id: str) -> str:
        """Simulates the OTA flash command.""" [cite: 228-229]
        print(f"\nTOOL: Triggering OTA flash for device '{device_id}'...")
        state = get_device_state(device_id)
        latest_firmware = state.get('current_firmware_path', 'N/A')
        # In a real system, this would call a real OTA service API
        log_message = f"OTA flash command sent to device '{device_id}'. Device will now update to firmware: '{latest_firmware}'." [cite: 234-235]
        print(f"TOOL: {log_message}")
        return log_message

# --- AGENT SETUP ---
# Define the prompt template
prompt_template = """
You are an expert autonomous IoT firmware engineer. Your task is to modify device firmware based on real-time events and predefined policies.
You have received a runtime event from device: '{device_id}'
The event is: '{event_details}'
The user-defined policy for this event is: '{policy}'

Your goal is to rewrite the device's firmware to implement the logic defined in the policy.
Follow these steps precisely:
1. **Analyze Context**: Use the 'get_device_state' tool to understand the device's capabilities (like its sensor schema).
2. **Read Current Code**: Use the 'read_current_firmware' tool to get the current source code.
3. **Synthesize New Code**: Based on the event, policy, and current code, rewrite the *entire* firmware. The new code must be a complete, compilable C++/Arduino program. Do not write partial code or snippets. The new logic should be robust.
4. **Save New Firmware**: Use the 'write_new_firmware' tool, passing the 'device_id' and the 'new_code' you just generated.
5. **Deploy**: Use the 'trigger_ota_flash' tool to simulate deploying the update to the device.

Begin the process now.
"""

def create_agent():
    """Initializes and returns the LangChain agent.""" [cite: 256, 258]
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.2)
    # Initialize tools
    tools = [
        ReadFirmwareTool(),
        WriteFirmwareTool(),
        DeviceStateTool(),
        TriggerOtaFlashTool()
    ]
    # Create the prompt from the template
    prompt = PromptTemplate.from_template(prompt_template)
    # Create the ReAct agent
    agent = create_react_agent(llm, tools, prompt)
    # Create the Agent Executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

# --- FLASK WEB SERVER ---
app = Flask(__name__)
agent_executor = create_agent()

@app.route('/trigger-agent', methods=['POST'])
def handle_event():
    """Endpoint to receive events and trigger the agent.""" [cite: 278, 280]
    data = request.json
    device_id = data.get("device_id")
    event_details = data.get("event_details")
    policy = data.get("policy")

    if not all([device_id, event_details, policy]):
        return jsonify({"error": "Missing device_id, event_details, or policy"}), 400

    print(f"\n\n--- New Event Received for {device_id} ---")
    print(f"Event: {event_details}")
    print(f"Policy: {policy}")
    print("--- Invoking Agent ---")

    try:
        # Run the agent with the provided context
        result = agent_executor.invoke({
            "device_id": device_id,
            "event_details": event_details,
            "policy": policy
        })
        return jsonify({"success": True, "agent_output": result.get('output')})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure initial firmware directory exists
    if not os.path.exists(os.path.join(FIRMWARE_DIR, "device-001")):
        os.makedirs(os.path.join(FIRMWARE_DIR, "device-001"))

    # Create dummy initial firmware if it doesn't exist
    initial_firmware_path = os.path.join(FIRMWARE_DIR, "device-001", "v1.0.cpp")
    if not os.path.exists(initial_firmware_path):
        initial_code = """// Firmware Version: 1.0
// Active Sensors: A, C, D
#include <Arduino.h>
void setup() { Serial.begin(115200); Serial.println("Device starting... Firmware v1.0"); }
void loop() {
    int sensor_a_value = analogRead(1);
    Serial.print("Sensor A: "); Serial.println(sensor_a_value);
    if (sensor_a_value > 100) { Serial.println("EVENT: sensor_A_threshold_exceeded"); }
    delay(5000);
}"""
        with open(initial_firmware_path, 'w') as f:
            f.write(initial_code)

    # Run the Flask app
    app.run(port=5001, debug=True)