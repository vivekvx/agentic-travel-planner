"""Exercise the LangChain tool-calling loop without a paid model request."""

import json
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage

from travel_planner.agent import consult


class AgentHarnessTests(unittest.TestCase):
    def test_all_five_tools_return_observations_to_the_model(self):
        start = date.today() + timedelta(days=2)
        request = {
            "origin": "Delhi", "destination": "Goa",
            "start": start.isoformat(),
            "end": (start + timedelta(days=2)).isoformat(),
            "travelers": 2, "rooms": 1, "pace": "Balanced",
            "max_nightly_price": 5000, "effective_hotel_ceiling": 5000,
            "min_stars": 3, "amenities": [], "interests": ["beach"],
            "daily_local_per_person": 1500, "budget": None, "notes": "",
        }
        names = ["flight_search", "hotel_recommendations", "places_discovery",
                 "weather_lookup", "budget_estimation"]
        calls = [{"name": name, "args": {}, "id": f"call-{index}"}
                 for index, name in enumerate(names)]
        calls[-1]["args"] = {"flight_price_per_person": None,
                              "hotel_price_per_night": 1232}
        responses = [AIMessage(content="", tool_calls=calls),
                     AIMessage(content="Here is your grounded plan.")]
        observations = []

        def invoke(messages):
            if len(messages) > 2:
                observations.extend(message for message in messages if isinstance(message, ToolMessage))
            return responses.pop(0)

        with patch("langchain_groq.ChatGroq") as model, \
             patch("travel_planner.agent.get_weather", return_value={
                 "status": "forecast", "days": [], "note": "test forecast"}):
            model.return_value.bind_tools.return_value.invoke.side_effect = invoke
            result = consult(request, api_key="test-key")

        self.assertIsNone(result.error)
        self.assertEqual(result.tool_calls, names)
        self.assertEqual(len(observations), 5)
        payloads = [json.loads(message.content) for message in observations]
        self.assertTrue(all("error" not in payload for payload in payloads))
        self.assertEqual(payloads[0]["status"], "no_matching_flight")
        self.assertEqual(payloads[3]["status"], "forecast")
        self.assertEqual(payloads[4]["hotel"], 2464)


if __name__ == "__main__":
    unittest.main()
