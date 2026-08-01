from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage
from .config import Config
from .tools import get_all_tools


class FirmwareAgent:
    """Autonomous IoT firmware engineer agent."""
    
    SYSTEM_PROMPT = (
        "You are an expert autonomous IoT firmware engineer managing a FLEET of ESP32 "
        "sensor nodes (climate, air quality, presence/light, structural). You have deep "
        "knowledge of Arduino/C++, sensor management, power optimization, and IoT best practices. "
        "You can read, write, and deploy firmware using the provided tools.\n\n"
        "MANDATORY FIRST STEP: Before writing or deploying ANY firmware, you MUST call "
        "'get_fleet_context_tool' to read every node's latest sensor state. Reason about "
        "whether the triggering event is ISOLATED (only this node signals anything unusual) "
        "or CORRELATED with other nodes' current signals (e.g. heat + gas + no motion = hazard). "
        "The same raw event should produce different firmware depending on fleet-wide context.\n\n"
        "Every firmware you generate MUST include a comment block naming which other nodes' "
        "signals (if any) influenced your decision — the reasoning must be auditable, not a black box.\n\n"
        "DEPLOYMENT (real, not simulated): after writing firmware with 'write_new_firmware', deploy it "
        "with the real compile/deploy tools, choosing scope from the fleet reasoning above:\n"
        "  - ISOLATED event on one node -> call 'compile_and_deploy_firmware' for that single node.\n"
        "  - CORRELATED multi-node pattern (e.g. heat + gas + no motion) -> rewrite firmware for each "
        "relevant node, then call 'push_firmware_to_multiple_nodes' with just those device_ids.\n"
        "These real tools run arduino-cli and update the OTA manifest; they REPLACE the old simulated "
        "'trigger_ota_flash'. Only fall back to 'trigger_ota_flash' if a real deploy tool is unavailable. "
        "If a deploy tool returns an error string (arduino-cli not found / COMPILE FAILED / DEPLOY FAILED), "
        "report it plainly — do not claim success.\n\n"
        "Always generate complete, compilable Arduino C++ code with detailed comments explaining your decisions."
    )
    
    def __init__(self, max_iterations: int = 10):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE
        )
        self.tools = get_all_tools()
        self.tool_dict = {tool.name: tool for tool in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.max_iterations = max_iterations
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def invoke(self, input_dict: dict) -> dict:
        """Execute the agent with the given input."""
        input_text = input_dict["input"]
        messages = [HumanMessage(content=input_text)]
        
        for i in range(self.max_iterations):
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
    
    @staticmethod
    def create_agent_prompt(device_id: str, event_details: str, policy: str = None) -> str:
        """Creates a formatted prompt for the agent."""
        if policy:
            # Policy-driven mode (backward compatibility)
            return f"""
You have received a runtime event from device '{device_id}'.
Event: '{event_details}'
Policy: '{policy}'

Follow these steps:
1. Use 'get_fleet_context_tool' FIRST to read the state of every node in the fleet.
2. Use 'get_device_state_tool' to understand the device configuration.
3. Use 'read_current_firmware' to inspect the existing code.
4. Rewrite the *entire firmware* in C++/Arduino format to implement the policy, including
   a comment block naming any other nodes' signals that influenced the decision.
5. Use 'write_new_firmware' to save the code.
6. Deploy for real: 'compile_and_deploy_firmware' for a single isolated-event node, or
   'push_firmware_to_multiple_nodes' with the relevant device_ids for a correlated
   multi-node pattern. These run arduino-cli + update the OTA manifest and REPLACE the
   simulated 'trigger_ota_flash'. If a deploy tool returns an error string, report it — don't claim success.
"""
        else:
            # Autonomous decision-making mode
            return f"""
You have received a runtime event from device '{device_id}'.
Event: '{event_details}'

As an autonomous IoT firmware engineer, analyze this event and determine the optimal response.

Consider these factors in your decision-making:
1. **Device Safety**: Prevent damage, overheating, or malfunction
2. **Power Efficiency**: Optimize battery life and energy consumption
3. **Sensor Optimization**: Improve data quality and reliability
4. **Network Management**: Handle connectivity issues intelligently
5. **Security**: Protect against tampering and unauthorized access
6. **Performance**: Balance responsiveness with resource constraints

Follow these steps:
1. Use 'get_fleet_context_tool' FIRST to read the current state of EVERY node in the fleet.
   Decide whether this event is isolated or correlated with other nodes' signals.
2. Use 'get_device_state_tool' to understand the device configuration and available sensors
3. Use 'read_current_firmware' to inspect the existing code and understand current behavior
4. Analyze the event IN THE CONTEXT OF THE WHOLE FLEET and determine the best firmware
   modifications based on:
   - Whether other nodes' signals elevate or de-escalate the urgency of this event
   - IoT industry best practices
   - Arduino/embedded systems optimization techniques
   - Sensor management strategies
   - Power management principles
   - Safety and reliability requirements
5. Rewrite the *entire firmware* with your intelligent modifications, including a comment
   block naming which other nodes' signals (if any) influenced the decision
6. Use 'write_new_firmware' to save the optimized code with detailed comments explaining your decisions
7. Deploy for real, choosing scope from your fleet reasoning:
   - ISOLATED event on this node only -> 'compile_and_deploy_firmware' for the single device.
   - CORRELATED multi-node pattern (e.g. heat + gas + no motion) -> rewrite firmware for each
     relevant node with 'write_new_firmware', then 'push_firmware_to_multiple_nodes' with just those device_ids.
   These run arduino-cli and update the OTA manifest, REPLACING the simulated 'trigger_ota_flash'.
   If a deploy tool returns an error string (arduino-cli not found / COMPILE FAILED / DEPLOY FAILED), report it honestly.

Make autonomous decisions that demonstrate your expertise in IoT firmware engineering.
Include detailed comments in your code explaining why you made each decision.
"""