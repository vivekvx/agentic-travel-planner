"""Checks for the dataset limitations that could otherwise mislead travelers."""

import unittest
from datetime import date, timedelta

from travel_planner.core import estimate_budget, search_flights


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


if __name__ == "__main__":
    unittest.main()
