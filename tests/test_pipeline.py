"""End-to-end integration tests for the full planning pipeline."""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from travel_planner.core import (
    cities,
    discover_places,
    estimate_budget,
    make_days,
    search_flights,
    search_hotels,
)


class TestFullPlanningPipeline(unittest.TestCase):
    def test_end_to_end_itinerary_creation(self):
        city_names = cities()
        self.assertIn("Delhi", city_names)
        self.assertIn("Goa", city_names)

        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=3)

        flight_res = search_flights("Delhi", "Goa", start)
        self.assertIn("options", flight_res)

        hotel_res = search_hotels("Goa", max_nightly_price=8000, min_stars=2)
        self.assertTrue(len(hotel_res["options"]) > 0)
        selected_hotel = hotel_res["options"][0]

        places_res = discover_places("Goa", interests=["beach", "fort"])
        self.assertTrue(len(places_res["options"]) > 0)

        days = make_days(start, end, places_res["options"], pace="Balanced")
        self.assertEqual(len(days), 4)
        for day in days:
            self.assertIn("date", day)
            self.assertTrue(day["places"] or day["activity"])

        budget = estimate_budget(
            flight_price_per_person=None,
            hotel_price_per_night=selected_hotel["price_per_night"],
            nights=3,
            travelers=2,
            daily_local_per_person=1500,
            rooms=1,
        )
        self.assertFalse(budget["complete"])
        self.assertGreater(budget["known_total"], 0)


if __name__ == "__main__":
    unittest.main()
