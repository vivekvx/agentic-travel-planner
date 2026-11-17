"""LangChain tool calling consultant for evidence gathering and advice."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from .core import (discover_places, estimate_budget, get_weather,
                   search_flights, search_hotels)


@dataclass
class AgentResult:
    advice: str
    tool_calls: list[str]
    error: str | None = None


def consult(request: dict, api_key: str, model: str = "openai/gpt-oss-120b") -> AgentResult:
    """Let an LLM select and call the assignment's five travel tools."""
    if not api_key:
        return AgentResult("Add a Groq API key to get the agent's consultant assessment. The data-backed plan below works without a key.", [])

    try:
        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
        from langchain_core.tools import tool
        from langchain_groq import ChatGroq
    except ImportError:
        return AgentResult("Install the project requirements to enable the LangChain agent.", [], "Missing LangChain packages")

    start = date.fromisoformat(request["start"])
    end = date.fromisoformat(request["end"])
    observations: list[str] = []

    @tool
    def flight_search(sort_by: str = "cheapest") -> str:
        """Find date-matched flights for the requested route. Sort by cheapest or fastest."""
        return json.dumps(search_flights(request["origin"], request["destination"], start,
                                         sort_by=sort_by))

    @tool
    def hotel_recommendations() -> str:
        """Find hotels matching city, star level, nightly budget, and amenities."""
        return json.dumps(search_hotels(request["destination"], request["effective_hotel_ceiling"],
                                        request["min_stars"], request["amenities"]))

    @tool
    def places_discovery() -> str:
        """Find destination attractions ranked by interests and rating."""
        return json.dumps(discover_places(request["destination"], request["interests"]))

    @tool
    def weather_lookup() -> str:
        """Check whether a live Open-Meteo forecast exists for the trip dates."""
        return json.dumps(get_weather(request["destination"], start, end))

    @tool
    def budget_estimation(flight_price_per_person: int | None = None,
                          hotel_price_per_night: int | None = None) -> str:
        """Estimate the trip in INR. Pass null for an unavailable flight or hotel."""
        return json.dumps(estimate_budget(flight_price_per_person, hotel_price_per_night,
                                          (end - start).days, request["travelers"],
                                          request["daily_local_per_person"], request["rooms"]))

    tools = [flight_search, hotel_recommendations, places_discovery,
             weather_lookup, budget_estimation]
    by_name = {item.name: item for item in tools}
    system = SystemMessage(content=(
        "You are a careful travel consultant. Choose and call the available tools to examine flights, "
        "hotels, attractions, weather, and budget before advising. Use the user's preferences. "
        "Do not invent availability, places, prices, routes, weather, distances, or opening hours. "
        "Sample records are unverified; never say booked. If no dated flight exists, state that the "
        "flight cost is unknown. Give a concise day-wise itinerary using only places returned by the "
        "tool, then explain your hotel and activity choices, budget tradeoffs, and one practical next "
        "step. If the sample data runs out of places, label remaining time flexible. Do not reveal "
        "private chain of thought."
    ))
    messages = [system, HumanMessage(content=json.dumps(request))]
    try:
        model_client = ChatGroq(model=model, groq_api_key=api_key, temperature=0).bind_tools(tools)
        for _ in range(6):
            reply = model_client.invoke(messages)
            messages.append(reply)
            if not reply.tool_calls:
                content = reply.content if isinstance(reply.content, str) else str(reply.content)
                return AgentResult(content, observations)
            for call in reply.tool_calls:
                selected = by_name.get(call["name"])
                if selected is None:
                    result = json.dumps({"error": "Unknown tool"})
                else:
                    try:
                        result = selected.invoke(call.get("args") or {})
                    except Exception as exc:
                        result = json.dumps({"error": f"{type(exc).__name__}: {exc}"})
                    observations.append(call["name"])
                messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
        return AgentResult("The consultant reached its tool-call limit. Review the data-backed plan below.", observations,
                           "Tool-call limit")
    except Exception as exc:
        return AgentResult("The agent could not complete its assessment. Review the data-backed plan below.",
                           observations, f"{type(exc).__name__}: {exc}")
