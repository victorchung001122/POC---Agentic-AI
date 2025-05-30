# math_server.py
from mcp.server.fastmcp import FastMCP
# import logging
import json

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
# logger = logging.getLogger(__name__)

mcp = FastMCP("knwoledge_base")


@mcp.tool()
def knowledge_base_employee_info():
    """get employee information from knwoledge base."""
    with open("knowledge_base/employee_info.txt", 'r', encoding='utf-8') as file:
        return file.read()

@mcp.tool()
def knowledge_base_product_list():
    """get product list and information from knwoledge base, such as product type, interestRate, minimumBalance, monthlyFees

    """
    with open("knowledge_base/product_list.json", 'r', encoding='utf-8') as file:
        return json.load(file)
    
    # The product list is provided in JSON format, including the following fields:
    # key - product name, e.g. savings account, loan
    # product_type - type of the product, e.g. savings, loan, credit card
    # interest_rate - interest rate of the product, e.g. 2.5%
    # minimum_balance - minimum balance required for the product, e.g. 1000 HKD
    # monthly_fees - monthly fees for the product, e.g. 50 HKD
    # rewards - rewards for the product, e.g. cashback, airline miles point
    # bonusPoints - bonus points for the product, e.g. 1000 points
        
    
    
@mcp.tool()
def knowledge_base_loan_record():
    """get loan record from knwoledge base, such as applicant_name, loan_amount, application_date, status, processing_details, approval_details"""
    with open("knowledge_base/loan_record.json", 'r', encoding='utf-8') as file:
        return json.load(file)

@mcp.tool() 
def knowledge_base_customer_info():
    """get customer information from knwoledge base, such as customer name, address, business nature and whether it is a live customer.
    
     The customer information is provided in JSON format, including the following fields:
        key - customer_name, e.g. Welab Bank
        address - address of the customer, e.g. 123 Main St, Hong Kong
        business_nature - nature of the business, e.g. banking, finance, insurance
        live_customer - whether the customer is a live customer, e.g. true or false
    """
    with open("knowledge_base/customer_info.json", 'r', encoding='utf-8') as file:
        return json.load(file)
    
@mcp.tool() 
def knowledge_base_customer_identity_info():
    """ Verify the identity of the user, such as identity number and name
    
    The identify information is provided in JSON format, including the following fields:
        key - just a increment number, e.g. 1, 2, 3
        identity_number - identity number, e.g. 123
        name - name of the user, e.g. John Doe
    
    Example:    
    {
        "1" : {"Identity Number" : "123", "Name" : "Elvis"},
        "2" : {"Identity Number" : "234", "Name" : "Tom"},
        "3" : {"Identity Number" : "345", "Name" : "Steven"}
    }
    """
    with open("knowledge_base/customer_identity_verification.json", 'r', encoding='utf-8') as file:
        return json.load(file)
    
@mcp.tool() 
def knowledge_base_salary_benchmark():
    """ The salary benchmark information is provided in JSON format, including the following fields:
        key - industry name, e.g. technology, finance, healthcare
        average_salary - average salary in HKD
        entry_level - entry level salary in HKD
        senior_level - senior level salary in HKD
        
        Since the salary benchmark is on industry level, the key is the industry name. And you need to identify which industry the user is in or analyze full set of data to find which one is the most suitable for the user.
    """
    with open("knowledge_base/salary_benchmark.json", 'r', encoding='utf-8') as file:
        return json.load(file)
    
if __name__ == "__main__":
    #mcp.run(transport="stdio")
    # logger.info("Start internal knowledge base server through MCP")
    mcp.run(transport= "stdio")