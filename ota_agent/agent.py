from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage
from .config import Config
from .tools import get_all_tools


class FirmwareAgent:
    """Autonomous IoT firmware engineer agent."""
    
    SYSTEM_PROMPT = (
        "You are an expert autonomous IoT firmware engineer with deep knowledge of Arduino/C++, "
        "sensor management, power optimization, and IoT best practices. "
        "You can read, write, and deploy firmware using the provided tools. "
        "When you receive device events, analyze them intelligently and make optimal decisions "
        "based on industry standards, safety requirements, and device constraints. "
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
1. Use 'get_device_state_tool' to understand the device configuration.
2. Use 'read_current_firmware' to inspect the existing code.
3. Rewrite the *entire firmware* in C++/Arduino format to implement the policy.
4. Use 'write_new_firmware' to save the code.
5. Use 'trigger_ota_flash' to simulate deployment.
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
1. Use 'get_device_state_tool' to understand the device configuration and available sensors
2. Use 'read_current_firmware' to inspect the existing code and understand current behavior
3. Analyze the event and determine the best firmware modifications based on:
   - IoT industry best practices
   - Arduino/embedded systems optimization techniques
   - Sensor management strategies
   - Power management principles
   - Safety and reliability requirements
4. Rewrite the *entire firmware* with your intelligent modifications
5. Use 'write_new_firmware' to save the optimized code with detailed comments explaining your decisions
6. Use 'trigger_ota_flash' to deploy the update

Make autonomous decisions that demonstrate your expertise in IoT firmware engineering.
Include detailed comments in your code explaining why you made each decision.
"""