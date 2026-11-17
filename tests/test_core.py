"""Checks for the dataset limitations that could otherwise mislead travelers."""

import unittest
from datetime import date, timedelta

from travel_planner.core import (discover_places, estimate_budget, get_weather,
                                 make_days, search_flights, search_hotels)


class PlanningDataTests(unittest.TestCase):
    def test_historical_flight_is_not_offered_for_future_date(self):
        result = search_flights("Delhi", "Goa", date.today() + timedelta(days=7))
        self.assertEqual(result["options"], [])
        self.assertEqual(result["status"], "no_matching_flight")

    def test_missing_flight_does_not_become_zero_cost(self):
        estimate = estimate_budget(None, 3000, 2, 2, 1000)
        self.assertIsNone(estimate["flight"])
        self.assertEqual(estimate["known_total"], 12000)
        self.assertFalse(estimate["complete"])

    def test_hotel_filters_are_applied(self):
        result = search_hotels("Goa", max_nightly_price=4000, min_stars=3)
        self.assertTrue(all(row["city"] == "Goa" and row["stars"] >= 3
                            and row["price_per_night"] <= 4000 for row in result["options"]))

    def test_distant_weather_is_not_guessed(self):
        start = date.today() + timedelta(days=30)
        result = get_weather("Goa", start, start + timedelta(days=2))
        self.assertEqual(result["status"], "outside_forecast_window")
        self.assertEqual(result["days"], [])

    def test_mislabeled_places_use_sourced_catalogue(self):
        result = discover_places("Goa", ["beach"])
        self.assertEqual(result["invalid_sample_count"], 5)
        self.assertEqual(result["options"][0]["type"], "beach")
        self.assertTrue(all(row["source"].startswith("https://") for row in result["options"]))

    def test_long_and_packed_trips_have_no_unexplained_empty_days(self):
        start = date.today() + timedelta(days=7)
        places = discover_places("Goa")["options"]
        for end, pace in [(start + timedelta(days=6), "Balanced"),
                          (start + timedelta(days=2), "Packed")]:
            days = make_days(start, end, places, pace)
            self.assertTrue(all(day["places"] or day["activity"] for day in days))
            self.assertTrue(days[0]["places"])


if __name__ == "__main__":
    unittest.main()
