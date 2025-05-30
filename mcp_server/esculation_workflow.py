# math_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("math")

@mcp.tool()
def wrong_employee_name_provided():
    """ defined message to return to user"""
    return "This is the wrong employee name provided by user"


if __name__ == "__main__":
    mcp.run(transport= "stdio")
    