"""Streamlit interface for the agentic travel planning assignment."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta

import streamlit as st

from travel_planner.agent import consult
from travel_planner.core import (cities, discover_places, estimate_budget, get_weather,
                                 make_days, search_flights, search_hotels)

st.set_page_config(page_title="Travel Consultant", page_icon="🧭", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("""
<style>
  .block-container {max-width: 1120px; padding-top: 2rem;}
  .hero {background: linear-gradient(125deg,#0d3340,#126b72); color:#fff;
         border-radius:18px; padding:28px 34px; margin-bottom:24px;}
  .hero h1 {color:#fff; margin:0 0 6px; font-size:2.4rem;}
  .hero p {margin:0; color:#d7f0ec;}
  .small-note {color:#5c6e72; font-size:.9rem;}
</style>
<div class="hero"><h1>Where will your next trip take you?</h1>
<p>Start with the essentials. Get a first plan, then shape it around your preferences.</p></div>
""", unsafe_allow_html=True)

def build_plan(request: dict, api_key: str, model: str) -> dict:
    """Create a verified plan and optional LangChain consultant advice."""
    start = date.fromisoformat(request["start"])
    end = date.fromisoformat(request["end"])
    flights = search_flights(request["origin"], request["destination"], start)
    selected_flight = flights["options"][0] if flights["options"] else None
    hotel_ceiling = request["max_nightly_price"]
    if request["budget"]:
        local_cost = request["daily_local_per_person"] * request["travelers"] * ((end - start).days + 1)
        flight_cost = selected_flight["price"] * request["travelers"] if selected_flight else 0
        remaining = request["budget"] - local_cost - flight_cost
        affordable_nightly = max(0, remaining // max(1, (end - start).days * request["rooms"]))
        hotel_ceiling = min(hotel_ceiling, affordable_nightly)
    hotels = search_hotels(request["destination"], hotel_ceiling,
                           request["min_stars"], request["amenities"])
    places = discover_places(request["destination"], request["interests"])
    weather = get_weather(request["destination"], start, end)
    selected_hotel = hotels["options"][0] if hotels["options"] else None
    estimate = estimate_budget(selected_flight["price"] if selected_flight else None,
                               selected_hotel["price_per_night"] if selected_hotel else None,
                               (end - start).days, request["travelers"],
                               request["daily_local_per_person"], request["rooms"])
    days = make_days(start, end, places["options"], request["pace"])
    advice = consult({**request, "effective_hotel_ceiling": hotel_ceiling}, api_key, model)
    if not api_key or advice.error:
        hotel_reason = (f"{selected_hotel['name']} fits your hotel preferences and ranks well for stars per rupee."
                        if selected_hotel else
                        ("No hotel fits the total budget after estimated daily costs; raise the budget or reduce daily spending."
                         if request["budget"] and hotel_ceiling < request["max_nightly_price"]
                         else "No hotel fits your preferences; try a higher nightly limit or fewer amenities."))
        place_names = ", ".join(item["name"] for item in places["options"][:3])
        activity_reason = (f"Start with {place_names}; these rank highest for your interests and ratings."
                           if place_names else "No attractions are listed for this destination.")
        flight_reason = ("The sample data includes an outbound flight for these dates, but availability is unverified."
                         if selected_flight else "No flight matches your dates in the sample data, so the cost is incomplete.")
        advice.advice = f"{hotel_reason} {activity_reason} {flight_reason} Check travel times and opening hours before booking."
    return {"request": request, "flight": selected_flight, "hotel": selected_hotel,
            "days": days, "weather": weather, "budget": estimate,
            "agent": advice.advice, "agent_tools": advice.tool_calls,
            "agent_error": advice.error, "agent_enabled": bool(api_key),
            "flight_search": flights, "hotel_search": hotels, "place_search": places,
            "hotel_ceiling_used": hotel_ceiling}
