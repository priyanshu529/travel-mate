import os
from typing import TypedDict,Annotated
import operator
import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AIMessage,AnyMessage,SystemMessage,HumanMessage
)
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from datetime import date
# from tools.flight_tool import search_flights
from mcp_client import tavily_mcp_search,flight_mcp_search
DATABASE_URL=os.getenv("DATABASE_URL")
import asyncio
import streamlit as st


DATABASE_URL = st.secrets["DATABASE_URL"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]


llm=ChatGroq(
    model="openai/gpt-oss-120b"
)

class TravelState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]
    user_query:str
    flight_result:str
    hotel_results:str
    itinerary:str
    llm_calls:int

class FlightQuery(BaseModel):
    departure_iata: str = Field(default="DEL",
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

def flight_agent(state:TravelState):
    structured_llm = llm.with_structured_output(FlightQuery)
    query=state["user_query"]
    prompt = f"""Extract flight search parameters from this user query: {query}

Rules:
- Todays date is {date.today().isoformat()}.
- If the departure airport is not mentioned, assume DEFAULT_ORIGIN (Delhi).
- If the destination city is mentioned but not a specific airport, pick the primary
  international airport for that city (e.g. Tokyo -> NRT).
- If "today" or a relative date is mentioned, resolve it to an actual YYYY-MM-DD date
  using today's date above.
- Never ask a clarifying question — always return your best-guess values for every field.
-If departure date and number of days of trip is given,calculate return date.
"""

    result = structured_llm.invoke(prompt)
    flight_data=asyncio.run(flight_mcp_search(result.arrival_iata,result.departure_date,result.return_date,result.departure_iata,result.passengers))

    return {
        "flight_result":flight_data,
        "messages":[
            AIMessage(content=f"Flight results fetched")
        ],
        "llm_calls":state.get("llm_calls",0)+1
    }

def hotel_agent(state:TravelState):
    query=f"best hotels for {state["user_query"]}"
    hotel_results=asyncio.run(tavily_mcp_search(query))
    return {
        "hotel_results":hotel_results,
        "messages":[
            AIMessage(content="Hotel information fetched")
        ],
        "llm_calls":state.get("llm_calls",0)+1
    }


def itinerary_agent(state:TravelState):
    prompt=f"""
    create a travel itinerary based on the following data.
    User Query:{state['user_query']},
    Flight Results(round trip):{state["flight_result"]},
    Hotel Results:{state["hotel_results"]}
"""
    response=llm.invoke([SystemMessage(
        content="You are an expert Travel planner create itinerary based on the given data and user's budget"
    ),
    HumanMessage(content=prompt)
    ])

    return{
        "itinerary":response.content,
        "messages":[response],
        "llm_calls":state.get("llm_calls",0)+1
    }



def final_agent(state: TravelState):

    final_prompt = final_prompt = f"""
You are a professional travel planner.

Your task is to combine the flight results, hotel recommendations, and itinerary into **one concise travel plan**.

## Requirements

* Use Markdown.
* Keep the response under 2000 words.
* Do NOT explain your reasoning.
* Do NOT repeat information.
* Use **only** the information provided below.
* If information is missing, write "Not Available" instead of making assumptions.

## Flight Rules (VERY IMPORTANT)

* The flight agent has **already searched round-trip flights**.
* Every flight object returned by the flight agent represents **one complete round-trip itinerary**, even if only the outbound leg is shown in the summary.
* **Do NOT** combine two different flight options.
* **Do NOT** add the prices of two different flights together.
* **Do NOT** display separate outbound and return flights.
* Display **only ONE flight option**.
* Always choose the **cheapest available itinerary** unless the user explicitly requested another preference.
* The **Price** must be exactly the price returned by the flight agent for that itinerary.
* Never estimate, calculate, double, or modify the flight price.
* If the flight agent returns multiple itineraries, ignore the others after selecting the cheapest.

Format the flight section exactly like this:

# ✈️ Flights

* Airline:
* Route:
* Departure:
* Arrival:
* Stops:
* **Round-trip Price:** ₹XXXX
* Note: Price shown is for the complete round-trip itinerary.

## Hotel Rules

* Hotel prices should be based on the number of travellers.
* If the number of travellers is not provided, assume 1 traveller.
* Display at most 3 hotel recommendations.

Format:

# 🏨 Hotels

| City | Hotel | Price | Rating |

## Itinerary Rules

* Create a practical itinerary using the selected hotel and destination.
* Do not invent flights or hotel names.

Format:

# 📅 Itinerary

## Day 1

* Morning:
* Afternoon:
* Evening:

## Day 2

...

## Budget Rules

The budget should contain:

| Category | Cost |

Categories:

* Flights
* Hotel
* Local Transport
* Food
* Activities

The **Flights** cost must be the exact round-trip price returned by the flight agent.

Show:

* Total Estimated Cost
* Remaining Budget (if the user specified one)

## Travel Tips

Provide 3–5 concise travel tips.

---

### Flight Data

{state["flight_result"]}

### Hotel Data

{state["hotel_results"]}

### Itinerary Context

{state["itinerary"]}

"""

    response = llm.invoke([
        HumanMessage(content=final_prompt)
    ],max_tokens=1500)

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def summary_llm(result):
    prompt=f"""
summarize the following result of the agent:{result} 
keeping all the necesary details (eg if its flight agent keep the flight name,id,price,timing etc) 
and remove all the unnecessary and boilerplate statements.
"""
    response=llm.invoke(prompt)
    return response.content
# build graph

graph=StateGraph(TravelState)

graph.add_node("flight_agent",flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("itinerary_agent",itinerary_agent)
graph.add_node("final_agent",final_agent)


# add edges
graph.add_edge(START,"flight_agent")
graph.add_edge("flight_agent","hotel_agent")
graph.add_edge("hotel_agent","itinerary_agent")
graph.add_edge("itinerary_agent","final_agent")
graph.add_edge("final_agent",END)

print("connecting")
_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

app=graph.compile(checkpointer=checkpointer)

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

if __name__=="__main__":
    user_id=str(uuid.uuid4())
    config={
        "configurable":{
            "thread_id":user_id,
        }
    }
    user_input=input("enter travel request:")

    result=app.invoke(
        {
            "messages":[
                HumanMessage(content=user_input)
            ],
            "user_query":user_input,
            "flight_result":"",
            "hotel_results":"",
            "itinerary":"",
            "llm_Calls":0
        },
        config=config
    )
    print(result["messages"][-1].content)
