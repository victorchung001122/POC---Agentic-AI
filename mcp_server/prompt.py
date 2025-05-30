from mcp.server.fastmcp.prompts import base
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Prompts")

@mcp.prompt()
def ask_for_employee_information():
    """ When user asks for the employee information. If the user provides correct employee name, the assistant will provide the employee information based on the employee name provided by user.
    """
    return [
        base.Message(
            role="assistant",
            type="text",
            content=[
                base.TextContent(
                    text=f"Hi! please provide correct employee name"
                )
            ]
        )
    ]
    
@mcp.prompt()
def provide_wrong_employee_name():
    """ When user asks for the employee information. If the user provides wrong employee name more than three times, the assistant will reject to provide the infomration.

    """
    return [
        base.Message(
            role="assistant",
            type="text",
            content=[
                base.TextContent(
                    text=f"When user asks for the employee information. If the user provides wrong employee name more than three times, the assistant will reject to provide the infomration."
                )
            ]
        )
    ]


@mcp.prompt()
def ask_product_information():
    """ When user asks for the product information, use this prompt.
    """
    return "What product do you want to know?"

@mcp.prompt()
def ask_product_information():
    """ When user provides the correct product name, use this prompt.
    """
    return "all the information about the product name provided by user."
    
if __name__ == "__main__":
    mcp.run(transport= "stdio")
    
    
