# math_server.py
from mcp.server.fastmcp import FastMCP
# import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
# logger = logging.getLogger(__name__)

mcp = FastMCP("Weather")


# mcp_configured = FastMCP(
#     name="ConfiguredServer",
#     port=8080,  # Sets the default SSE port
#     host="127.0.0.1", # Sets the default SSE host
#     log_level="DEBUG", # Sets the logging level
#     on_duplicate_tools="warn" # Warn if tools with the same name are registered (options: 'error', 'warn', 'ignore')
# )


@mcp.tool()
async def get_weather(location: str) -> str:
    """Get the weather for a location"""
    # logger.info(f"The get_weather method is called: location=%s", location)
    # Simulate fetching weather data
    return "The weather is sunny with a high of 25°C."

if __name__ == "__main__":
    #mcp.run(transport="stdio")
    # logger.info("Starting Weather MCP server...")
    mcp.run(transport= "sse")
    