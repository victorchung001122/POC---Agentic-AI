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
from config import llm_model, llm_api_key


root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


memory = MemorySaver()
mcp_tools_agent = None

def supervisor_prompt(state: AgentState):
    system_msg = """ 
        You are the Supervisor in the loan application process. Your role is to review and finalize the outcomes of the validations conducted by the High-Risk, Medium-Risk, and Low-Risk Agents. You will ensure that all customer information is thoroughly assessed and that any flagged discrepancies are addressed.

        Your tasks include:
        1. Examine the reports submitted by each agent, focusing on their findings and rationale.
        2. Evaluate the necessity of further investigation based on the agents' flags.
        3. Make a final decision on the loan application, taking into account all risk factors and validations.
        4. Provide feedback to each agent on their performance and any areas for improvement in the validation process.
        5. Limit the functions and tools that the user can use as to not to expose both internal and external data that are not relavent to the user's loan procecss and their risk level 
        6. Don't show agent feedback to the user.
        7. Send the task to task scheduler to process the loan application and inform the user that the loan process is started if all the information is correct.
        
        - functions of high risk agent:
            1. Check the validity of the ID number against the customer identify information in knowledge base, if the ID number is not valid, then you should let the user know they need to submit documents to prove their identity after the loan process is started. Then you need to send a task to task scheduler to user need to submit documents to prove their identity.
            2. Validate the company name and address with the record on the internet by using google search API and make sure the online address comes from the About Us or Contact Us page of its offical website.
            3. Ensure the declared salary aligns with industry standards for the specified occupation. You may check the salary against the knowledge base salary information.
            4. Flag any suspicious or inconsistent entries for further review.
            
        - functions of medium risk agent:
            1. Check the validity of the ID number against the customer identify information in knowledge base, if the ID number is not valid, then you should let the user know they need to submit documents to prove their identity after the loan process is started. Then you need to send a task to task scheduler to user need to submit documents to prove their identity.
            2. Validate the company name with the record on the internet by using google search API and make sure the company name is not a fraud.
            3. Ensure the declared salary aligns with industry standards for the specified occupation. You may check the salary against the knowledge base salary information, allowing for some variations.
            4. Note any inconsistencies and suggest if further investigation is warranted.
        
        - functions of low risk agent:
            1. Check the validity of the ID number against the customer identify information in knowledge base.
            2. Confirm that the declared salary is reasonable for the occupation without delving into excessive detail.
            
        Summarize your final decision clearly, including any comments on the overall risk assessment and necessary follow-up actions.
        """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def high_risk_agent__prompt(state: AgentState):
    system_msg = """ 
        You are the High-Risk Agent in the loan application process. Your task is to thoroughly validate the customer information using the available tools in the MCP server. Focus on identifying discrepancies or potential fraud indicators in the following fields: ID number, company name, company address, salary, and occupation. 

        Consider the following steps:
        1. Check the validity of the ID number against the customer identify information in knowledge base, if the ID number is not valid, then you should let the user know they need to submit documents to prove their identity after the loan process is started. Then you need to send a task to task scheduler to user need to submit documents to prove their identity.
        2. Validate the company name and address with the record on the internet by using google search API tools and make sure the online address comes from the About Us or Contact Us page of its offical website.
        3. Ensure the declared salary aligns with industry standards for the specified occupation. You may check the salary against the knowledge base salary information.
        4. Flag any suspicious or inconsistent entries for further review.
        5. Tools can be used : [task_scheduler, knowledge_base_customer_identity_info, knowledge_base_salary_benchmark, knowledge_base_product_list, google_map_address_validation, google_map_search_company_address, google_search, google_search_top3_metadata]
        6. Don't show agent feedback to the user, but only to the supervisor agent.
        7. Send the task to task scheduler to process the loan application and inform the user that the loan process is started if the loan application is approved.
        8. If the loan application is not approved, then you need to send a task to task scheduler to user need to submit documents to prove their identity.
        
        Report your findings clearly, indicating any fields that require further investigation or verification.
        """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def medium_risk_agent__prompt(state: AgentState):
    system_msg = """ 
        You are the Medium-Risk Agent in the loan application process. Your role is to validate the customer information with a balanced approach, recognizing areas that may need closer examination. Utilize the tools provided in the MCP server to assess the following fields: ID number, company name, salary, and occupation.

        Follow these guidelines:
        1. Check the validity of the ID number against the customer identify information in knowledge base, if the ID number is not valid, then you should let the user know they need to submit documents to prove their identity after the loan process is started. Then you need to send a task to task scheduler to user need to submit documents to prove their identity.
        2. Validate the company name with the record on the internet by using google search API tools and make sure the company name is not a fraud.
        3. Ensure the declared salary aligns with industry standards for the specified occupation. You may check the salary against the knowledge base salary information, allowing for some variations.
        4. Note any inconsistencies and suggest if further investigation is warranted.
        5. Tools can be used : [task_scheduler, knowledge_base_customer_identity_info, knowledge_base_salary_benchmark, knowledge_base_product_list, google_map_address_validation, google_map_search_company_address, google_search, google_search_top3_metadata]
        6. Don't show agent feedback to the user, but only to the supervisor agent.
        7. Send the task to task scheduler to process the loan application and inform the user that the loan process is started if the loan application is approved.
        8. If the loan application is not approved, then you need to send a task to task scheduler to user need to submit documents to prove their identity.
        
        Present your validation results with clear reasoning for any flags raised.
        """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def low_risk_agent__prompt(state: AgentState):
    system_msg = """ 
        You are the Low-Risk Agent in the loan application process. Your objective is to efficiently validate the customer information provided, using the tools available in the MCP server. Focus on the following fields: ID number, salary, and occupation.

        Conduct the following checks:
        1. Check the validity of the ID number against the customer identify information in knowledge base.
        2. Confirm that the declared salary is reasonable for the occupation without delving into excessive detail.
        3. Report any minor inconsistencies but prioritize a smooth and fast processing experience.
        4. Tools can be used : [task_scheduler, knowledge_base_customer_identity_info, knowledge_base_salary_benchmark, knowledge_base_product_list, google_map_address_validation, google_map_search_company_address, google_search, google_search_top3_metadata]
        5. Don't show agent feedback to the user, but only to the supervisor agent.
        7. Send the task to task scheduler to process the loan application and inform the user that the loan process is started if the loan application is approved.
        8. If the loan application is not approved, then you need to send a task to task scheduler to user need to submit documents to prove their identity.

        Summarize your findings succinctly, highlighting any areas that may need attention but indicating that the overall risk is low.
        """
    return [{"role": "system", "content": system_msg}] + state["messages"]

def print_optimized_result(agent_response):
    """
    Extracts and formats the agent's response for display.
    
    Parses through the agent's message history to extract tool calls,
    results, and final answers, then formats them for user-friendly display.
    
    Args:
        agent_response (dict): Response object from the agent containing messages
        
    Returns:
        str: Final answer extracted from the agent's response
    """
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
        elif message.type == "tool":
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
    """
    Initializes the Multi-Server MCP Client with all required services.
    
    Sets up connections to:
    - Internal knowledge base server
    - Task scheduler server  
    - External Google API server
    
    Returns:
        MultiServerMCPClient: Initialized MCP client instance
    """
    
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
                },
            "external_google_api_server": {
                "command": "python",
                "args": ["./mcp_server/external_google_api_server.py"],
                "transport": "stdio"
                }
            }    
        ).__aenter__()
        return mcp_tools_agent

async def close_mcp_tools_client():
    """
    Properly closes the MCP client connection and cleans up resources.
    """
    global mcp_tools_agent
    if mcp_tools_agent is not None:
        await mcp_tools_agent.__aexit__(None, None, None)
        mcp_tools_agent = None

async def set_up_high_risk_agent(llm):
    if mcp_tools_agent is None:
        await initialize_mcp_tools_agent()
    
    return create_react_agent(
        llm, 
        mcp_tools_agent.get_tools(), 
        prompt=high_risk_agent__prompt,
        name="high_risk_agent"
    )
    
async def set_up_medium_risk_agent(llm):
    if mcp_tools_agent is None:
        await initialize_mcp_tools_agent()
    
    return create_react_agent(
        llm, 
        mcp_tools_agent.get_tools(), 
        prompt=medium_risk_agent__prompt,
        name="medium_risk_agent"
    )
    
async def set_up_low_risk_agent(llm):
    if mcp_tools_agent is None:
        await initialize_mcp_tools_agent()
    
    return create_react_agent(
        llm, 
        mcp_tools_agent.get_tools(), 
        prompt=low_risk_agent__prompt,
        name="low_risk_agent"
    )

async def process_query(user_message):  
    """
    Main processing function that orchestrates the entire loan validation workflow.
    
    Creates the LLM instance, initializes all agents, sets up the supervisor,
    and processes the user's loan application through the multi-agent system.
    """
    
    llm = ChatDeepSeek(
    model= llm_model, 
    api_key=llm_api_key,
    http_client=httpx.Client(verify=False),
    http_async_client=httpx.AsyncClient(verify=False),
    temperature=1,
    max_tokens=500
)
    high_risk_agent = await set_up_high_risk_agent(llm)
    medium_risk_agent = await set_up_medium_risk_agent(llm)
    low_risk_agent= await set_up_low_risk_agent(llm)
  
    supervisor_agent = create_supervisor(
            model = llm, 
            agents = [high_risk_agent, medium_risk_agent, low_risk_agent], 
            prompt=supervisor_prompt,
            add_handoff_back_messages=True,
            output_mode="full_history"
        ).compile(checkpointer=memory)
    
    supervisor_response = await supervisor_agent.ainvoke({"messages": user_message}, {"configurable": {"thread_id": "123"}})
    ai_response = print_optimized_result(supervisor_response)
    return ai_response

def chat_handler(message, history):
    """
    Handles chat interactions from the Gradio interface.
    
    Processes user messages through the async workflow and manages
    the conversation history with timestamps.
    
    Args:
        message (str): User's input message
        history (list): Current chat history
        
    Returns:
        list: Updated chat history with the assistant's response
    """
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
    """
    Processes user input and adds it to chat history with timestamp.
    
    Args:
        user_message (str): The user's input message
        history (list): Current chat history
        
    Returns:
        tuple: (cleared input field, updated history)
    """
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
    
    """
    Creates the Gradio web interface for the Loan Processing Assistant.
    """

    
    with gr.Row():
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(label="Chat History", type="messages")
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



