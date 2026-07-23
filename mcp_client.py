from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import json
import asyncio
load_dotenv()
import streamlit as st
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
SERPAPI_KEY = st.secrets["SERPAPI_API_KEY"]

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        "travelpayouts-custom": {
            "transport": "streamable_http",
            # Replace with your new self-hosted URL (Render/Railway/Fly.io), e.g.:
            # "url": "https://your-app-name.onrender.com/mcp"
            "url": "https://serpapi-mcp-server-8u7m.onrender.com/mcp"
        }
    }
)


search_tool = None
flight_tools = {}

async def initialize_mcp():
    global search_tool
    global flight_tools
    if search_tool is not None:
        return

    tools = await client.get_tools()

    search_tool = next((tool for tool in tools if tool.name == "tavily_search"), None)

    if search_tool is None:
        raise RuntimeError(
            "MCP tool tavily search is not found among available tools:"
        )

    required_flight_tools = ["search_flights_prices"]

    flight_tools = {
        tool.name: tool
        for tool in tools
        if tool.name in required_flight_tools
    }
    if len(flight_tools) < len(required_flight_tools):
        raise RuntimeError(
            f""""only {len(flight_tools)} flight_tools are loaded:\n"""
            f"Found: {list(flight_tools.keys())}"
        )

async def tavily_mcp_search(query: str):
    await initialize_mcp()
    response = await search_tool.ainvoke(
        {
            "query": query, "max_results": 10,
            "include_domains": [
            "booking.com",
            "agoda.com",
            "tripadvisor.com",
            "hotels.com",
            "expedia.com"
]
        }
    )
    if not response:
        return "No hotel results found."

    try:
        data = json.loads(response[0]["text"])
    except Exception as e:
        return f"Unable to parse Tavily response: {e}"

    results = data.get("results", [])

    if not results:
        return "No hotel results found."

    formatted = []

    for i, hotel in enumerate(results, start=1):
        title = hotel.get("title", "Unknown Hotel")
        url = hotel.get("url", "")
        snippet = hotel.get("content", "")

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        formatted.append(
            f"""### {i}. {title}

URL: {url}

{snippet}
"""
        )

    return "\n\n".join(formatted)


async def flight_mcp_search(destination, depart_date, ret_date=None, origin="DEL", passengers=1, currency="INR"):

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
