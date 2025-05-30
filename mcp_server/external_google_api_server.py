
# math_server.py
from mcp.server.fastmcp import FastMCP
# import logging
import os
import googlemaps
from langchain_google_community import GoogleSearchAPIWrapper
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
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


# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
# logger = logging.getLogger(__name__)

mcp = FastMCP("Google Search")


@mcp.tool()
async def google_map_address_validation(input: str) -> str:
    """A wrapper around Google Map. Useful for when you need to answer questions about current location or address validation. Input should be a geocode of location or company name. Output is a JSON array of the query results"""
    # logger.info(f"Validate the addree {input} with google map api")
    return gmaps.geocode(input)

@mcp.tool()
async def google_map_search_company_address(input: str) -> str:
    """A wrapper around Google Map. Useful for when you need to answer questions about current location or address validation. Input should be a search query of location or company name. Output is a JSON array of the query results"""
    # logger.info(f"Search the company {input} with google map api")
    return gmaps.places(query=input)

@mcp.tool()
async def google_search(input: str) -> str:
    """A wrapper around Google Search. Useful for when you need to answer questions about current events with top 3 relevance. 
    
    Input parameters.
        - query: str,
        - num_results: int,
        - search_params: Dict[str, str] | None = None
        
    Returns:
    snippet - The description of the result
    title - The title of the result
    link - The link to the result

    Return type:A list of dictionaries.
    """
    print("Trigger google search tools {input}")
    # logger.info(f"Search {input} with google api and return top 3 results")
    search_result = GoogleSearchAPIWrapper(k=3).run(input)
    print(search_result)
    return search_result

@mcp.tool() 
async def google_search_top3_metadata(input: str) -> str:
    """A wrapper around Google Search. Useful for when you need to answer questions about search query and its metadata of top 3 query result, including title, link, snippet. 
    
    Returns:
    snippet - The description of the result
    title - The title of the result
    link - The link to the result

    Return type:A list of dictionaries.
    """
    # logger.info(f"Search {input} with google search api and return the metadata of top 3 results")
    print("Trigger google search tools top 3 metadata : {input}")
    search_result = GoogleSearchAPIWrapper().results(input, 3)
    print(search_result)
    return search_result

if __name__ == "__main__":
    #mcp.run(transport="stdio")
    # logger.info("Starting external google search MCP server...")
    mcp.run(transport= "stdio")
    