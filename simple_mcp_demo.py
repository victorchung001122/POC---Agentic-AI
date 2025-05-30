import os
import json
import httpx
import googlemaps
import gradio as gr
from typing import List, Tuple
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import AgentType, initialize_agent
from langchain_community.utilities import GoogleTrendsAPIWrapper, GoogleFinanceAPIWrapper
from langchain_community.tools.google_trends import GoogleTrendsQueryRun
from langchain_community.tools.google_finance import GoogleFinanceQueryRun
from langchain_google_community import GoogleSearchAPIWrapper
from config import PLACES_API_KEY, llm_api_key, OPENWEATHERMAP_API_KEY, SERPAPI_API_KEY, SERP_API_KEY, GOOGLE_CSE_ID, GOOGLE_API_KEY, GOOGLE_MAPS_API_KEY


# Environment Variables for API Keys and User Agent
os.environ["USER_AGENT"] = "testing"
os.environ["GPLACES_API_KEY"] = PLACES_API_KEY
os.environ["DEEPSEEK_API_KEY"] = llm_api_key
os.environ["OPENWEATHERMAP_API_KEY"] = OPENWEATHERMAP_API_KEY
os.environ["SERPAPI_API_KEY"] = SERPAPI_API_KEY
os.environ["SERP_API_KEY"] = SERP_API_KEY
os.environ["GOOGLE_CSE_ID"] = GOOGLE_CSE_ID
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize Google Maps Client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Define tools
@tool
def knowledge_base_employee_info(input: str) -> str:
    """get employee information from knwoledge base."""
    with open("knowledge_base/employee_info.txt", 'r', encoding='utf-8') as file:
        return file.read()

@tool
def knowledge_base_product_list(input: str) -> str:
    """get product list and information from knwoledge base, such as product type, interestRate, minimumBalance, monthlyFees"""
    with open("knowledge_base/product_list.json", 'r', encoding='utf-8') as file:
        return json.load(file)
    
@tool
def knowledge_base_loan_record(input: str) -> str:
    """get loan record from knwoledge base, such as applicant_name, loan_amount, application_date, status, processing_details, approval_details"""
    with open("knowledge_base/loan_record.json", 'r', encoding='utf-8') as file:
        return json.load(file)

@tool 
def knowledge_base_customer_info(input: str) -> str:
    """get customer information from knwoledge base, such as customer name, address, business nature and whether it is a live customer."""
    with open("knowledge_base/customer_info.json", 'r', encoding='utf-8') as file:
        return json.load(file)

@tool 
def google_map_address_validation(input: str) -> str:
    """input address to validate the address with google map api"""
    return gmaps.geocode(input)

@tool 
def google_map_search_company_address(input: str) -> str:
    """input address to search the company address with google map api."""
    return gmaps.places(query=input)

@tool 
def google_search(input: str) -> str:
    """do google search based on the input and return the details of top 3 result"""
    search_result = GoogleSearchAPIWrapper(k=3).run(input)
    return search_result

@tool 
def google_search_top3_metadata(input: str) -> str:
    """do google search based on the input and return the metadata of top 3 result, including title, link, snippet"""
    search_result = GoogleSearchAPIWrapper().results(input, 3)
    return search_result


# Initialize LangChain Chat Model
llm = init_chat_model(
    "deepseek-chat", 
    model_provider="deepseek", 
    http_client=httpx.Client(verify=False),
    temperature=1,
    max_tokens=500,
    timeout=None,
    max_retries=2,
)

# Load tools into agent
tools = [
    GoogleTrendsQueryRun(api_wrapper=GoogleTrendsAPIWrapper()),
    GoogleFinanceQueryRun(api_wrapper=GoogleFinanceAPIWrapper()),
    knowledge_base_employee_info, 
    knowledge_base_product_list,
    knowledge_base_loan_record,
    knowledge_base_customer_info, 
    google_map_address_validation,
    google_map_search_company_address,
    google_search,
    google_search_top3_metadata
]

agent_chain = initialize_agent(
    tools=tools, 
    llm=llm, 
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors="Check your output and ensure it conforms!"
)

# Define interaction functions
def get_ai_response(user_message):
    if not user_message.strip():
        return "Please provide a specific question."
    return agent_chain.invoke([HumanMessage(content=user_message)])['output']

def user(user_message, history: list):
    return user_message, history + [{"role": "user", "content": user_message}]

def bot(user_message, history: list):
    bot_message = get_ai_response(user_message)
    history.append({"role": "assistant", "content": ""})
    for character in bot_message:
        history[-1]['content'] += character
        yield history

def clear_history():
    return []

# Setup Gradio interface
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox()
    clear = gr.Button("Clear")
    msg.submit(user, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False).then(
        bot, inputs=[msg, chatbot], outputs=chatbot)
    clear.click(clear_history, [], chatbot)

demo.launch(debug=True)