"""Deterministic travel data tools and itinerary validation."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CITY_COORDINATES = {
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Delhi": (28.6139, 77.2090),
    "Goa": (15.2993, 74.1240),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Kolkata": (22.5726, 88.3639),
    "Mumbai": (19.0760, 72.8777),
}
WEATHER_CODES = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Cloudy",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers",
    81: "Rain showers", 82: "Heavy showers", 95: "Thunderstorm",
}


def load_data(name: str) -> list[dict]:
    """Load one of the bundled assignment datasets."""
    if name not in {"flights", "hotels", "places", "curated_places"}:
        raise ValueError("Unknown dataset")
    with (DATA_DIR / f"{name}.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def cities() -> list[str]:
    return sorted(CITY_COORDINATES)


def search_flights(origin: str, destination: str, departure_date: date,
                   sort_by: str = "cheapest") -> dict:
    """Only offer flights whose route and date actually match the request."""
    route = [row for row in load_data("flights")
             if row["from"] == origin and row["to"] == destination]
    matches = [row for row in route
               if datetime.fromisoformat(row["departure_time"]).date() == departure_date]
    if sort_by == "fastest":
        matches.sort(key=lambda row: (datetime.fromisoformat(row["arrival_time"])
                                      - datetime.fromisoformat(row["departure_time"]), row["price"]))
    else:
        matches.sort(key=lambda row: (row["price"], row["arrival_time"]))
    return {
        "options": matches[:5],
        "status": "available_in_dataset" if matches else "no_matching_flight",
        "note": ("Prices and availability come from the sample dataset, not a live airline."
                 if matches else "No flight matches this route and date in the sample dataset. Do not present a historical flight as bookable."),
        "route_sample_count": len(route),
    }


def search_hotels(city: str, max_nightly_price: int | None = None,
                  min_stars: int = 1, amenities: list[str] | None = None) -> dict:
    """Rank matching hotels by value while keeping the full price visible."""
    required = {item.lower() for item in amenities or []}
    matches = [row for row in load_data("hotels") if row["city"] == city
               and row["stars"] >= min_stars
               and (max_nightly_price is None or row["price_per_night"] <= max_nightly_price)
               and required.issubset({item.lower() for item in row["amenities"]})]
    matches.sort(key=lambda row: (-row["stars"] / row["price_per_night"],
                                  row["price_per_night"]))
    return {"options": matches[:5], "count": len(matches),
            "note": "Hotel names, amenities, and prices are sample data; availability is unverified."}


def discover_places(city: str, interests: list[str] | None = None) -> dict:
    """Use sourced attractions when the supplied sample has inconsistent labels."""
    preferred = {interest.lower() for interest in interests or []}
    supplied = [row for row in load_data("places") if row["city"] == city]
    invalid = [row for row in supplied if row["type"].lower() not in row["name"].lower()]
    if invalid:
        matches = [row for row in load_data("curated_places") if row["city"] == city]
        note = (f"{len(invalid)} of {len(supplied)} supplied place records have conflicting names and types. "
                "The itinerary uses separately sourced attractions; verify hours and travel times.")
    else:
        matches = supplied
        note = "Attraction records have no opening hours, coordinates, or visit durations."
    matches.sort(key=lambda row: (row["type"].lower() not in preferred,
                                  -(row["rating"] or 0), row["name"]))
    return {"options": matches, "count": len(matches),
            "note": note, "invalid_sample_count": len(invalid)}


def get_weather(city: str, start: date, end: date) -> dict:
    """Fetch daily forecast, or explain when dates fall outside its horizon."""
    if city not in CITY_COORDINATES:
        return {"days": [], "status": "unsupported_city", "note": "No coordinates for this city."}
    today = date.today()
    if start < today or end > today + timedelta(days=15):
        return {"days": [], "status": "outside_forecast_window",
                "note": "Open-Meteo forecast is available only for near-term dates. Weather has not been predicted for this trip."}
    latitude, longitude = CITY_COORDINATES[city]
    query = urlencode({"latitude": latitude, "longitude": longitude,
                       "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                       "timezone": "auto", "start_date": start.isoformat(),
                       "end_date": end.isoformat()})
    try:
        with urlopen(f"https://api.open-meteo.com/v1/forecast?{query}", timeout=10) as response:
            payload = json.load(response)
        daily = payload["daily"]
        days = [{"date": day, "condition": WEATHER_CODES.get(daily["weather_code"][i], "Unknown"),
                 "high_c": daily["temperature_2m_max"][i],
                 "low_c": daily["temperature_2m_min"][i],
                 "rain_probability_percent": daily["precipitation_probability_max"][i]}
                for i, day in enumerate(daily["time"])]
        return {"days": days, "status": "forecast", "note": "Live forecast from Open-Meteo; conditions may change."}
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
        return {"days": [], "status": "weather_unavailable",
                "note": f"Weather service unavailable: {type(exc).__name__}."}


def estimate_budget(flight_price_per_person: int | None, hotel_price_per_night: int | None,
                    nights: int, travelers: int, daily_local_per_person: int,
                    rooms: int = 1) -> dict:
    """Calculate known costs; never imply a missing flight costs zero."""
    flight = flight_price_per_person * travelers if flight_price_per_person is not None else None
    hotel = hotel_price_per_night * nights * rooms if hotel_price_per_night is not None else None
    local = daily_local_per_person * travelers * (nights + 1)
    known_total = sum(value for value in (flight, hotel, local) if value is not None)
    return {"currency": "INR (assumed from assignment example)", "flight": flight,
            "hotel": hotel, "food_and_local_transport": local, "known_total": known_total,
            "complete": flight is not None and hotel is not None,
            "note": "Flight estimate is outbound only. Estimate excludes return flights, attraction tickets, taxes, and unlisted fees. Missing components are not included in known_total."}
