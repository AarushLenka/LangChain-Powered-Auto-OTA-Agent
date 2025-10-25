import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangChain imports
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# --- CONFIGURATION ---
# IMPORTANT: Set your OpenAI API key in your environment variables
# If not set, the script will exit.
if "OPENAI_API_KEY" not in os.environ:
    print("Error: OPENAI_API_KEY environment variable not set.")
    sys.exit(1)

DB_FILE = "db.json"
FIRMWARE_DIR = "firmware"

# --- DATABASE HELPERS ---
def get_device_state(device_id):
    """Reads the state of a device from the DB."""
    try:
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        return data.get(device_id)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def update_device_firmware_path(device_id, new_path):
    """Updates the firmware path for a device in the DB."""
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
    # --- FIX: Added : str type annotations ---
    name: str = "read_current_firmware"
    description: str = "Reads the current firmware code for a given device ID. Input must be the device_id as a string."

    def _run(self, device_id: str) -> str:
        """Reads and returns the content of the current firmware file."""
        print(f"\nTOOL: Reading firmware for device '{device_id}'...")
        state = get_device_state(device_id)
        if not state or 'current_firmware_path' not in state:
            return f"Error: No state or firmware path found for device_id '{device_id}'."
        firmware_path = state['current_firmware_path']
        try:
            with open(firmware_path, 'r') as f:
                content = f.read()
            print(f"TOOL: Successfully read {firmware_path}")
            return content
        except FileNotFoundError:
            return f"Error: Firmware file not found at path: {firmware_path}"

class WriteFirmwareTool(BaseTool):
    # --- FIX: Added : str type annotations ---
    name: str = "write_new_firmware"
    description: str = "Writes new firmware code to a file for a specific device. Input must be a dictionary with 'device_id' and 'new_code'."

    def _run(self, device_id: str, new_code: str) -> str:
        """Saves the new firmware and updates the database."""
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
            return f"Successfully wrote new firmware version {new_version_str} for device {device_id}."
        except Exception as e:
            return f"Error writing firmware: {e}"

class DeviceStateTool(BaseTool):
    # --- FIX: Added : str type annotations ---
    name: str = "get_device_state"
    description: str = "Retrieves the sensor schema and current configuration for a device. Input must be the device_id as a string."

    def _run(self, device_id: str) -> str:
        """Returns the device state as a JSON string."""
        print(f"\nTOOL: Getting state for device '{device_id}'...")
        state = get_device_state(device_id)
        if state:
            return json.dumps(state)
        return f"Error: No state found for device_id '{device_id}'."

class TriggerOtaFlashTool(BaseTool):
    # --- FIX: Added : str type annotations ---
    name: str = "trigger_ota_flash"
    description: str = "Simulates triggering an Over-The-Air flash process for the device. The device will then pull the latest firmware. Input must be the device_id as a string."

    def _run(self, device_id: str) -> str:
        """Simulates the OTA flash command."""
        print(f"\nTOOL: Triggering OTA flash for device '{device_id}'...")
        state = get_device_state(device_id)
        latest_firmware = state.get('current_firmware_path', 'N/A')
        # In a real system, this would call a real OTA service API
        log_message = f"OTA flash command sent to device '{device_id}'. Device will now update to firmware: '{latest_firmware}'."
        print(f"TOOL: {log_message}")
        return log_message

# --- AGENT SETUP ---
# Define the prompt template
prompt_template = """
You are an expert autonomous IoT firmware engineer.
You have access to the following tools:
{tools}

Use the following format:

Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: a summary of the actions taken and the final result.

Begin!

Your task is to process the following event:
{input}

Follow the steps outlined in the task *exactly*.
Thought:{agent_scratchpad}
"""

def create_agent():
    """Initializes and returns the LangChain agent."""
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
    """Endpoint to receive events and trigger the agent."""
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
    initial_firmware_path = os.path.join(FIRMWARE_DIR, "device-001", "v1.0..cpp") # Note: potential typo in original doc, should be v1.0.cpp
    if not os.path.exists(initial_firmware_path):
        # Correcting path if the typo-version wasn't found
        initial_firmware_path_corrected = os.path.join(FIRMWARE_DIR, "device-001", "v1.0.cpp")
        if not os.path.exists(initial_firmware_path_corrected):
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
            with open(initial_firmware_path_corrected, 'w') as f:
                f.write(initial_code)

    # Run the Flask app
    app.run(port=5001, debug=True)