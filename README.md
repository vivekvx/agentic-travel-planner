# Agentic AI Travel Consultant

A Streamlit travel planner for the supplied capstone assignment. It combines sample flight, hotel, and attraction datasets with a live Open-Meteo forecast. With a Groq API key, a LangChain tool calling agent independently chooses from the five required tools and writes a short consultant assessment. The interface also builds a data-backed itinerary and cost estimate without an API key.

## Run

```bash
cd /Users/vivek/agentic-travel-planner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Put your Groq API key in `.streamlit/secrets.toml` as `GROQ_API_KEY = "..."`, or set the `GROQ_API_KEY` environment variable. The default model is `openai/gpt-oss-120b`, verified with this Groq account. No key is needed to inspect a deterministic plan. Keep the secrets file private.

## How it works

1. The user starts with a route, 3–7 day dates, and traveler count. Optional preferences are available after the first plan. See [UX_PLAN.md](UX_PLAN.md) for the flow and rationale.
2. Dataset tools filter flights by exact route and date, rank eligible hotels, and rank attractions by interests and rating.
3. Open-Meteo supplies a daily forecast when the dates are inside its near-term forecast window.
4. The budget tool sums selected flight, hotel, and daily local costs. Missing components stay unknown, rather than being counted as zero.
5. The LangChain agent can call all five tools and gives concise consultant advice. The app shows the tool names used.
6. The output includes a readable plan and downloadable JSON.

## Dataset limits

The supplied 30 flights are all dated 2025, so they cannot provide a flight for a future trip. The app offers a way to check current flights elsewhere and does not invent a fare. The 40 hotels are sample records with unverified prices. The supplied place file has many conflicting names and types, so the discovery tool checks it and uses [a sourced attraction catalogue](data/curated_places.json) for itineraries. These attractions have no ratings, coordinates, opening hours, or visit durations; the app avoids claims about optimized travel time. The assignment's example uses rupees, so costs are labelled INR as an assumption. Weather forecasts are the only live data in the app.

For a production planner, connect a current flight and hotel supplier, use verified place details and coordinates, add a mapping or routing service, and confirm all prices before checkout.
