"""Verify that user refinements change the displayed trip state."""

from unittest.mock import patch
from pathlib import Path

from streamlit.testing.v1 import AppTest

from travel_planner.agent import AgentResult


def test_hotel_choice_and_pace_feedback():
    weather = {"days": [], "status": "forecast", "note": "test forecast"}
    with patch("travel_planner.agent.consult", return_value=AgentResult("test advice", [])), \
         patch("travel_planner.core.get_weather", return_value=weather):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"),
                                default_timeout=20).run()
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state["plan"]["hotel"]["hotel_id"] == "HOT0014"

        hotel_widget = next(item for item in app.selectbox
                            if item.label == "Preferred hotel · optional")
        hotel_widget.set_value("HOT0011")
        app.select_slider[0].set_value("Packed")
        app.button[1].click().run()

        assert not app.exception
        assert app.session_state["plan"]["hotel"]["hotel_id"] == "HOT0011"
        assert app.session_state["request"]["pace"] == "Packed"
        assert "preferred hotel is now selected" in app.session_state["refinement_feedback"]
        assert "only five sourced attractions" in app.session_state["refinement_feedback"]

        app.selectbox[1].set_value("Mumbai")
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state["plan"]["request"]["hotel_id"] is None
        assert "refinement_feedback" not in app.session_state
