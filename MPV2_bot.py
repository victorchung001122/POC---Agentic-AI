import httpx
import gradio as gr
from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import asyncio
from datetime import datetime
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph_supervisor import create_supervisor

import logging
import sys
# logging.basicConfig(level=logging.DEBUG)
root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


memory = MemorySaver()
mcp_tools_agent = None

def negotiator_agent_prompt(state: AgentState):
    system_msg = """ 
    You are the Negotiator Agent, the central point of contact for the client in the loan package negotiation process. Your primary responsibilities are:

    1. Negotiate with the client, maintaining a polite and helpful attitude.
    2. Stream the conversation to the Rejection Agent and receive the sentiment analysis, rejection category, rejection priority, and sales recovery strategies.
    3. Summarize the conversation, including the loan package offered, reasons for escalation, and urgency, and send it to the Loan Officer Escalation Route Agent if the client rejects the loan offer or has a strong pushback.
    4. Provide the sales recovery strategy and loan parameters to the Loan Recommendation Agent if the client requests another loan package.
    5. Receive the recommended loan package from the Loan Recommendation Agent and negotiate with the client.
    6. Once the client accepts the loan package, schedule the next steps, such as the loan application, by sending a task to the Task Scheduler.
    7. Don't show agent feedback to the user, but only to the supervisor agent.
    
    Your goal is to guide the client through the negotiation process, utilizing the insights and strategies provided by the other agents, to reach a successful loan agreement. Maintain professionalism, empathy, and a problem-solving mindset throughout the interaction.
    """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def rejection_agent_prompt(state: AgentState):
    system_msg = """ 
    You are the Rejection Agent, working under the supervision of the Negotiator Agent. Your primary responsibilities are:

    1. Analyze the sentiment of the conversation received from the Negotiator Agent.
    2. Extract the rejection reasons from the conversation, such as loan amount not meeting financing needs, high-interest rate, or long processing time, by referencing the rejection taxonomy bank.
    3. Generate one or more sales recovery strategies based on the actual scenario, customer needs, or requests, using the sales recovery strategy bank.
    4. Provide the sentiment analysis result, rejection category, rejection priority, and sales recovery strategies to the Negotiator Agent.

    Your goal is to identify the customer's willingness to accept the loan, continue with the loan application, and prevent the client from dropping out of the loan process. Utilize your knowledge of rejection reasons and sales recovery strategies to support the Negotiator Agent in the negotiation process.
    """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def loan_recommendation_agent_prompt(state: AgentState):
    system_msg = """ 
    You are the Loan Recommendation Agent, working under the supervision of the Negotiator Agent. Your primary responsibilities are:

    1. Receive the loan parameters and sales recovery strategy from the Negotiator Agent.
    2. Fine-tune the loan parameters using the loan calculator system and pricing engine.
    3. Cross-check the loan package with the pre-defined business rules and guardrails to ensure it complies with the bank's standards and interests.
    4. If the new loan package is feasible, reach out to the Approval in Principle Engine to determine the required documents and the process timeline.
    5. Provide the recommended loan package details, including the required documents and process timeline, to the Negotiator Agent for further negotiation.

    Your goal is to offer a loan package that meets the client's needs while aligning with the bank's policies and guidelines. Leverage your expertise in loan calculations, pricing, and business rules to deliver a compliant and attractive loan recommendation to the Negotiator Agent.
        """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def loan_officer_escalation_route_agent_prompt(state: AgentState):
    system_msg = """ 
    You are the Loan Officer Escalation Route Agent, working under the supervision of the Negotiator Agent. Your primary responsibilities are:

    1. Receive the escalation from the Negotiator Agent, including the conversation summary, task, and urgency.
    2. Create a case in the Case Management System to proceed with human support.
    3. Provide the necessary information and context to the loan officer or the appropriate human support team to ensure a smooth escalation process.

    Your goal is to facilitate the transition from the automated negotiation process to the human-assisted loan application when the situation requires more specialized attention or when the client explicitly requests human involvement. Ensure a seamless handoff and provide the relevant details to the loan officer or human support team.
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

async def initialize_mcp_tools_agent():
    global mcp_tools_agent
    if mcp_tools_agent is None:
        mcp_tools_agent = await MultiServerMCPClient(
            {
            "internal_knowledge_base": {
                "command": "python",
                "args": ["./mcp_server/internal_knowledge_base_server.py"],
                "transport": "stdio",
                },
            "task_scheduler": {
                        "command": "python",
                        "args" : ["./mcp_server/task_scheduler.py"],
                        "transport": "stdio",
                }
            }    
        ).__aenter__()
        return mcp_tools_agent

async def close_mcp_tools_client():
    global mcp_tools_agent
    if mcp_tools_agent is not None:
        await mcp_tools_agent.__aexit__(None, None, None)
        mcp_tools_agent = None

async def set_up_rejection_agent(llm):
    if mcp_tools_agent is None:
        await initialize_mcp_tools_agent()
    
    return create_react_agent(
        llm, 
        mcp_tools_agent.get_tools(), 
        prompt=rejection_agent_prompt,
        name="rejection_agent"
    )
    
async def set_up_loan_recommendation_agent(llm):
    if mcp_tools_agent is None:
        await initialize_mcp_tools_agent()
    
    return create_react_agent(
        llm, 
        mcp_tools_agent.get_tools(), 
        prompt=loan_recommendation_agent_prompt,
        name="loan_recommendation_agent"
    )
    
async def set_up_loan_officer_escalation_route_agent(llm):
    if mcp_tools_agent is None:
        await initialize_mcp_tools_agent()
    
    return create_react_agent(
        llm, 
        mcp_tools_agent.get_tools(), 
        prompt=loan_officer_escalation_route_agent_prompt,
        name="loan_officer_escalation_route_agent"
    )

async def process_query(user_message):  
    llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key="sk-4b17e82aaa79439a92e9ae38e2d60a0a",
    http_client=httpx.Client(verify=False),
    http_async_client=httpx.AsyncClient(verify=False),
    temperature=1,
    max_tokens=500
)
    rejection_agent = await set_up_rejection_agent(llm)
    loan_recommendation_agen = await set_up_loan_recommendation_agent(llm)
    loan_officer_escalation_route_agent= await set_up_loan_officer_escalation_route_agent(llm)
  
    supervisor_agent = create_supervisor(
            model = llm, 
            agents = [rejection_agent, loan_recommendation_agen, loan_officer_escalation_route_agent], 
            prompt= negotiator_agent_prompt,
            add_handoff_back_messages=True,
            output_mode="full_history"
        ).compile(checkpointer=memory)
    
    supervisor_response = await supervisor_agent.ainvoke({"messages": user_message}, {"configurable": {"thread_id": "123"}})
    ai_response = print_optimized_result(supervisor_response)
    return ai_response

def chat_handler(message, history):
    timestamp = datetime.now().strftime("%H:%M:%S")    
    # Process query
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ai_response = loop.run_until_complete(process_query(message))
        assistant_timestamp = datetime.now().strftime("%H:%M:%S")
        response_text = f"**Assistant** ({assistant_timestamp}): {ai_response}"
        history.append({
            "role": "assistant",
            "content": response_text
        })
    except Exception as e:
        history.append({
            "role": "assistant",
            "content": f"**Error** ({timestamp}): {str(e)}"
        })
    finally:
        loop.close()
    return history

def user_message_box(user_message, history: list):
    timestamp = datetime.now().strftime("%H:%M:%S")
    history.append({
        "role": "user",
        "content": f"**User** ({timestamp}): {user_message}"
    })
    return user_message, history

def clear_history():
    return []

with gr.Blocks(title="Loan Process Assistant", css=".gradio-container {background-color: #E3E4FA !important;} .clear-btn {background-color: #FF6347 !important; color: white !important;}") as demo:
    gr.Markdown("# EY Loan Process Assistant")
    
    
    with gr.Row():
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(label="Chat History", type="messages")  # Added type="messages"
            msg = gr.Textbox(label="Your message", placeholder="Ask something...")
            clear = gr.Button("Clear Chat History", elem_classes="clear-btn")
        
    msg.submit(user_message_box, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False).then(
        chat_handler, inputs=[msg, chatbot], outputs=chatbot)
    
    # Handle clear button
    clear.click(
        clear_history,
        inputs=None,
        outputs=chatbot
    )
# Launch with specific port
demo.launch(server_name="127.0.0.1", 
        server_port=int("7860"),
        share=False)