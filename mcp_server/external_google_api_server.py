
# math_server.py
from mcp.server.fastmcp import FastMCP
# import logging
import os
import googlemaps
from langchain_google_community import GoogleSearchAPIWrapper


os.environ["GPLACES_API_KEY"] = 'AIzaSyDfqOagFx6fbZBB5TlX_QZHvqV-Kj-jK6c'
os.environ["DEEPSEEK_API_KEY"] = 'sk-4b17e82aaa79439a92e9ae38e2d60a0a'
os.environ["OPENWEATHERMAP_API_KEY"] = 'b852730ad89a93d435107d9403b2f846'
os.environ["SERPAPI_API_KEY"] = '0c7ed14ff2aae79de26336fbb1d8a4b173a2ddeba99fc1e246442ab7941fa139'
os.environ["SERP_API_KEY"] = '0c7ed14ff2aae79de26336fbb1d8a4b173a2ddeba99fc1e246442ab7941fa139'
os.environ["GOOGLE_CSE_ID"] = "33c8df939e3984c0f"
os.environ["GOOGLE_API_KEY"] = "AIzaSyBsPJRspL0hgfmWPv5WxzExYladGU7dvZ0"

# Initialize Google Maps Client
gmaps = googlemaps.Client(key='AIzaSyDnSfbTdh4M9M9STqFxSUYGwRPl72JEl5A')

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
    