import httpx
from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph_supervisor import create_supervisor
from config import llm_model, llm_api_key

memory = MemorySaver()

def prompt(state: AgentState):
    system_msg = """ You are a supervisor managing a math agent:\n"
        "- math agent. Assign math-related tasks to this agent\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    """
    return [{"role": "system", "content": system_msg}] + state["messages"]


def print_optimized_result(agent_response):
    messages = agent_response.get("messages", [])
    steps = []
    final_answer = None
    print(messages)
    for message in messages:
        if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
            tool_calls = message.additional_kwargs["tool_calls"]
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']
                steps.append(f"tools calling : {tool_name}({tool_args})")
        elif message.type == "top0ool":
            tool_name = message.name
            tool_result = message.content
            steps.append(f"{tool_name} result : {tool_result}")
        elif message.type == "ai":
            final_answer = message.content

    print("\nCalculation Steps:")
    for step in steps:
        print(f"- {step}")
    if final_answer:
        print(f"\nFinal Answer: {final_answer}")
        
    return final_answer


async def run_agent():
    llm = ChatDeepSeek(
        model=llm_model,
        api_key=llm_api_key,
        http_client=httpx.Client(verify=False),
        http_async_client=httpx.AsyncClient(verify=False),
        temperature=1,
        max_tokens=500
    )
    async with MultiServerMCPClient(
            {
            "internal_knowledge_base": {
                "command": "python",
                "args": ["./mcp_server/internal_knowledge_base_server.py"],
                "transport": "stdio",
            }
            }                    
        ) as kb_client:
        async with MultiServerMCPClient(
            {
            "math": {
                "command": "python",
                "args": ["./mcp_server/math_server.py"],
                "transport": "stdio"
            }
            }                    
        ) as math_client:
        
            math_agent = create_react_agent(
                llm, 
                math_client.get_tools(), 
                prompt =(
                    """"You are a math agent.\n\n"
                    "INSTRUCTIONS:\n"
                    - Assist ONLY with math-related tasks\n"
                    "- After you're done with your tasks, respond to the supervisor directly\n"
                    "- Respond ONLY with the results of your work, do NOT include ANY other text."""),
                name="math_agent"
            )
            
            kb_agent = create_react_agent(
                llm, 
                kb_client.get_tools(), 
                prompt =(
                    """"You are a knwoledge base agent.\n\n"
                    "INSTRUCTIONS:\n"
                    - Assist ONLY with knowledge base searching tasks\n"
                    "- After you're done with your tasks, respond to the supervisor directly\n"
                    "- Respond ONLY with the results of your work, do NOT include ANY other text."""),
                name="kb_client"
            )
        
            supervisor  = create_supervisor(
                model = llm, 
                agents = [kb_agent, math_agent], 
                prompt=prompt,
                add_handoff_back_messages=True,
                output_mode="full_history"
            ).compile(checkpointer=memory)
                
            while True:
                try:
                    user_input = input("User: ")
                    if user_input.lower() in ["exit", "quit"]:
                        print("Bye!")
                        break
                    
                    # Run the agent with the user input
                    supervisor_response = await supervisor.ainvoke({"messages": user_input}, {"configurable": {"thread_id": "1234"}})
                    
                    print_optimized_result(supervisor_response)

                except Exception as e:
                    print(f"Error: {e}")
                    continue



# Run the async function
if __name__ == "__main__":
    asyncio.run(run_agent())