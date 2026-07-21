from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import asyncio
load_dotenv()

TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
SERPAPI_KEY=os.getenv("SERPAPI_KEY")

client=MultiServerMCPClient(
    {
        "tavily":{
            "transport":"streamable_http",
            "url":f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },   
         "travelpayouts-custom": {
            "command": "python",
            "args": ["mcp_server.py"],
            "transport": "stdio"
        }
                }
)


# async def main():
#     tools=await client.get_tools()
#     print("available mcp tools")
#     for tool in tools:
#         print(tool.name)

# if __name__=="__main__":
#     asyncio.run(main())


search_tool=None
flight_tools={}

async def initialize_mcp():
    global search_tool
    global flight_tools
    if search_tool is not None:
        return

    tools=await client.get_tools()
    
    search_tool=next((tool for tool in tools if tool.name=="tavily_search"),None)
    
    if search_tool is None:
        raise RuntimeError(
            "MCP tool tavily search is not found among available tools:"
        )
    
    required_flight_tools = ["search_flights_prices"]

    flight_tools={
            tool.name:tool
            for tool in tools
            if tool.name in required_flight_tools
        }
    if len(flight_tools)<len(required_flight_tools):
        raise RuntimeError(
            f""""only {len(flight_tools)} flight_tools are loaded:\n"""
             f"Found: {list(flight_tools.keys())}"
        )

async def tavily_mcp_search(query:str):
    await initialize_mcp()
    response=await search_tool.ainvoke(
        {
            "query":query,"max_results":5
        }       
    )
    result=[]
    for i, r in enumerate(response, start=1):
        title=r.get("title","unknown")
        url=r.get("url","")
        snippet=r.get("content","")
    
        if len(snippet)>300:
            snippet=snippet[:300].rsplit(" ",1)[0]+ "...."
    
        result.append( f"{i}. **{title}** \n {url} \n  {snippet}")
    
    return "\n\n".join(result)


async def flight_mcp_search(destination, depart_date, ret_date=None, origin="DEL", passengers=1,currency="INR"):

    await initialize_mcp()  # make sure flight_tools is populated first

    one_way = ret_date is None

    search_args = {
        "origin": origin,
        "destination": destination,
        "departure_at": depart_date,
        "one_way": one_way,
        "currency": currency,
        "limit": 5,
    }
    if not one_way:
        search_args["return_at"] = ret_date

    exact_result = await flight_tools["search_flights_prices"].ainvoke(search_args)

    return f"""
    requested_date:
    date:{depart_date},
    "flight":{exact_result}
"""
