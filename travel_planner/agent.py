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
