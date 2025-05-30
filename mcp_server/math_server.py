# math_server.py
from mcp.server.fastmcp import FastMCP
# import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
# logger = logging.getLogger(__name__)

mcp = FastMCP("math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    # logger.info(f"Adding {a} and {b}")
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    # logger.info(f"Multiplying {a} and {b}")
    return a * b

if __name__ == "__main__":
    #mcp.run(transport="stdio")
    # logger.info("Start math server through MCP")
    mcp.run(transport= "stdio")
    