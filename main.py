import os
import asyncio
import uuid
from typing import TypedDict, Annotated
import operator
from datetime import date

import nest_asyncio
nest_asyncio.apply()  # ← fixes "event loop already running" in Streamlit

import psycopg
from psycopg.rows import dict_row
import streamlit as st

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

from mcp_client import tavily_mcp_search, flight_mcp_search

# ── Secrets ──────────────────────────────────────────────────────────────────
DATABASE_URL = st.secrets["DATABASE_URL"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatGroq(model="openai/gpt-oss-120b")


# ── State ─────────────────────────────────────────────────────────────────────
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_result: str
    hotel_results: str
    itinerary: str
    llm_calls: int


# ── Flight query schema ───────────────────────────────────────────────────────
class FlightQuery(BaseModel):
    departure_iata: str = Field(
        default="DEL",
        description="3-letter IATA airport code of the origin airport (e.g. DEL)"
    )
    arrival_iata: str = Field(
        description="3-letter IATA airport code of the destination airport (e.g. BOM)"
    )
    departure_date: str = Field(
        description="Departure date in YYYY-MM-DD format"
    )
    return_date: str | None = Field(
        default=None,
        description="Return date in YYYY-MM-DD format if mentioned"
    )
    passengers: int = Field(
        default=1,
        description="Number of passengers"
    )


# ── Agents ────────────────────────────────────────────────────────────────────
def flight_agent(state: TravelState):
    structured_llm = llm.with_structured_output(FlightQuery)
    query = state["user_query"]

    prompt = f"""Extract flight search parameters from this user query: {query}

Rules:
- Today's date is {date.today().isoformat()}.
- If the departure airport is not mentioned, assume Delhi (DEL).
- If the destination city is mentioned but not a specific airport, pick the primary
  international airport for that city (e.g. Tokyo -> NRT).
- If "today" or a relative date is mentioned, resolve it to an actual YYYY-MM-DD date
  using today's date above.
- Never ask a clarifying question — always return your best-guess values for every field.
"""

    result = structured_llm.invoke(prompt)

    flight_data = asyncio.run(
        flight_mcp_search(
            result.arrival_iata,
            result.departure_date,
            result.return_date,
            result.departure_iata,
            result.passengers,
        )
    )

    return {
        "flight_result": flight_data,
        "messages": [AIMessage(content="Flight results fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def hotel_agent(state: TravelState):
    query = f"best hotels for {state['user_query']}"
    hotel_results = asyncio.run(tavily_mcp_search(query))

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information fetched")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def itinerary_agent(state: TravelState):
    prompt = f"""
Create a travel itinerary based on the following data.
User Query: {state['user_query']}
Flight Results: {state['flight_result']}
Hotel Results: {state['hotel_results']}
"""
    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner. Create an itinerary based on the given data and user's budget."),
        HumanMessage(content=prompt),
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def final_agent(state: TravelState):
    final_prompt = f"""
You are a professional travel planner.

Your task is to combine the flight results, hotel recommendations, and itinerary into ONE concise travel plan.

Requirements:
- Use Markdown.
- Keep the response under 2000 words.
- Do NOT explain your reasoning.
- Do NOT repeat information.
- Be concise and practical.

Format exactly like this:

# 🌏 Trip Summary
- Destination:
- Duration:
- Travelers:
- Budget:

# ✈️ Flights
note: flight prices should be based on number of people from the query; if not provided assume 1 passenger.
- Airline
- Route
- Departure
- Arrival
- Price

# 🏨 Hotels
note: prices should be based on number of people from the query; if not provided assume 1 passenger.
| City | Hotel | Price | Rating (if available) |

# 📅 Itinerary
## Day 1
- Morning:
- Afternoon:
- Evening:

## Day 2
...

# 💰 Estimated Budget
| Category | Cost |

Total Estimated Cost:
Remaining Budget:

# 💡 Travel Tips
- 3-5 short tips only.

Use only the information provided below.

Flights:
{state['flight_result']}

Hotels:
{state['hotel_results']}

Itinerary:
{state['itinerary']}
"""

    response = llm.invoke(
        [HumanMessage(content=final_prompt)],
        max_tokens=1500,
    )

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ── Graph ─────────────────────────────────────────────────────────────────────
graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)

# ── Checkpointer ──────────────────────────────────────────────────────────────
print("Connecting to database...")
_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row,
)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()

app = graph.compile(checkpointer=checkpointer)

# ── CLI entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    user_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": user_id}}
    user_input = input("Enter travel request: ")

    result = app.invoke(
        {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input,
            "flight_result": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        },
        config=config,
    )
    print(result["messages"][-1].content)
