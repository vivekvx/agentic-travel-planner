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
