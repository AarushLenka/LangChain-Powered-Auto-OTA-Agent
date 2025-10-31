import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CHECK ENVIRONMENT ---
if "OPENAI_API_KEY" not in os.environ:
    print("Error: OPENAI_API_KEY environment variable not set.")
    sys.exit(1)

# --- LANGCHAIN IMPORTS ---
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# --- CONFIGURATION ---
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
@tool
def read_current_firmware(device_id: str) -> str:
    """Reads the current firmware code for a given device ID."""
    print(f"\nTOOL: Reading firmware for device '{device_id}'...")
    state = get_device_state(device_id)
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
    device_firmware_dir = os.path.join(FIRMWARE_DIR, device_id)
    os.makedirs(device_firmware_dir, exist_ok=True)
    new_firmware_path = os.path.join(device_firmware_dir, f"{new_version_str}.cpp")

    try:
        with open(new_firmware_path, 'w') as f:
            f.write(new_code)
        update_device_firmware_path(device_id, new_firmware_path)
        print(f"TOOL: New firmware saved to {new_firmware_path} and DB updated.")
        return f"Successfully wrote new firmware version {new_version_str} for device {device_id}."
    except Exception as e:
        return f"Error writing firmware: {e}"


@tool
def get_device_state_tool(device_id: str) -> str:
    """Retrieves the sensor schema and current configuration for a device."""
    print(f"\nTOOL: Getting state for device '{device_id}'...")
    state = get_device_state(device_id)
    if state:
        return json.dumps(state, indent=2)
    return f"Error: No state found for device_id '{device_id}'."


@tool
def trigger_ota_flash(device_id: str) -> str:
    """Simulates triggering an OTA flash process for the device."""
    print(f"\nTOOL: Triggering OTA flash for device '{device_id}'...")
    state = get_device_state(device_id)
    latest_firmware = state.get('current_firmware_path', 'N/A') if state else 'N/A'
    log_message = f"OTA flash triggered for device '{device_id}'. Device will now update to: '{latest_firmware}'."
    print(f"TOOL: {log_message}")
    return log_message


# --- SIMPLE AGENT CLASS ---
class SimpleAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.tool_dict = {tool.name: tool for tool in tools}
        
        # Bind tools to LLM
        self.llm_with_tools = llm.bind_tools(tools)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert autonomous IoT firmware engineer. "
                        "You can read, write, and deploy firmware using the provided tools. "
                        "Always generate complete, compilable Arduino C++ code when modifying logic."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def invoke(self, input_dict):
        """Execute the agent with the given input."""
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        
        input_text = input_dict["input"]
        messages = [HumanMessage(content=input_text)]
        
        max_iterations = 10
        for i in range(max_iterations):
            print(f"\n--- Agent Iteration {i+1} ---")
            
            # Format messages for prompt
            prompt_value = self.prompt.invoke({
                "input": input_text,
                "agent_scratchpad": messages[1:] if len(messages) > 1 else []
            })
            
            # Get LLM response
            response = self.llm_with_tools.invoke(prompt_value.to_messages())
            messages.append(response)
            
            # Check if we're done
            if not response.tool_calls:
                print("\n--- Agent Complete ---")
                return {"output": response.content}
            
            # Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                print(f"Calling tool: {tool_name} with args: {tool_args}")
                
                if tool_name in self.tool_dict:
                    tool_result = self.tool_dict[tool_name].invoke(tool_args)
                    messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    ))
                else:
                    messages.append(ToolMessage(
                        content=f"Error: Tool {tool_name} not found",
                        tool_call_id=tool_call["id"]
                    ))
        
        return {"output": "Max iterations reached"}


# --- AGENT CREATION ---
def create_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    tools = [
        read_current_firmware,
        write_new_firmware,
        get_device_state_tool,
        trigger_ota_flash
    ]
    return SimpleAgent(llm, tools)


# --- FLASK SERVER SETUP ---
app = Flask(__name__)
agent_executor = create_agent()

@app.route('/trigger-agent', methods=['POST'])
def handle_event():
    data = request.json
    device_id = data.get("device_id")
    event_details = data.get("event_details")
    policy = data.get("policy")

    if not all([device_id, event_details, policy]):
        return jsonify({"error": "Missing device_id, event_details, or policy"}), 400

    print(f"\n\n--- New Event for {device_id} ---")
    print(f"Event: {event_details}")
    print(f"Policy: {policy}")
    print("--- Invoking Agent ---")

    input_string = f"""
You have received a runtime event from device '{device_id}'.
Event: '{event_details}'
Policy: '{policy}'

Follow these steps:
1. Use 'get_device_state_tool' to understand the device configuration.
2. Use 'read_current_firmware' to inspect the existing code.
3. Rewrite the *entire firmware* in C++/Arduino format to implement the policy.
4. Use 'write_new_firmware' to save the code.
5. Use 'trigger_ota_flash' to simulate deployment.
"""

    try:
        result = agent_executor.invoke({"input": input_string})
        return jsonify({"success": True, "agent_output": result.get('output')})
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# --- MAIN ENTRYPOINT ---
if __name__ == '__main__':
    os.makedirs(os.path.join(FIRMWARE_DIR, "device-001"), exist_ok=True)
    initial_firmware_path = os.path.join(FIRMWARE_DIR, "device-001", "v1.0.cpp")
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

    app.run(port=6969, debug=True)