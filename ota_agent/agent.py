from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage
from .config import Config
from .tools import get_all_tools


class FirmwareAgent:
    """Autonomous IoT firmware engineer agent."""
    
    SYSTEM_PROMPT = (
        "You are an expert autonomous IoT firmware engineer. "
        "You can read, write, and deploy firmware using the provided tools. "
        "Always generate complete, compilable Arduino C++ code when modifying logic."
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
    def create_agent_prompt(device_id: str, event_details: str, policy: str) -> str:
        """Creates a formatted prompt for the agent."""
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