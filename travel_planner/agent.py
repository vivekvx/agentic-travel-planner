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
