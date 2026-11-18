"""Type definitions and schemas for the travel planner."""

from __future__ import annotations

from typing import Any, List, Optional, TypedDict


class FlightOption(TypedDict):
    carrier: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    price: int


class HotelOption(TypedDict):
    name: str
    city: str
    stars: int
    price_per_night: int
    amenities: List[str]


class PlaceOption(TypedDict):
    name: str
    city: str
    type: str
    rating: Optional[float]
    source: Optional[str]


class DayPlan(TypedDict):
    date: str
    places: List[dict]
    activity: Optional[str]
    note: str


class BudgetEstimate(TypedDict):
    currency: str
    flight: Optional[int]
    hotel: Optional[int]
    food_and_local_transport: int
    known_total: int
    complete: bool
    note: str


class TripRequest(TypedDict, total=False):
    origin: str
    destination: str
    start: str
    end: str
    travelers: int
    rooms: int
    pace: str
    max_nightly_price: int
    effective_hotel_ceiling: int
    min_stars: int
    amenities: List[str]
    interests: List[str]
    daily_local_per_person: int
    budget: Optional[int]
    notes: str
