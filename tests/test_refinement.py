"""Verify that user refinements change the displayed trip state."""

from unittest.mock import patch
from pathlib import Path
import pytest

from streamlit.testing.v1 import AppTest

from travel_planner.agent import AgentResult


@pytest.mark.parametrize("kind,label,value,field", [
    ("select_slider", "Pace", "Relaxed", "pace"),
    ("multiselect", "Things you enjoy", ["fort"], "interests"),
    ("number_input", "Total budget · optional (₹)", 5000, "budget"),
    ("number_input", "Hotel per room/night (₹)", 1000, "max_nightly_price"),
    ("selectbox", "Minimum hotel stars", 5, "min_stars"),
    ("selectbox", "Preferred hotel · optional", "HOT0011", "hotel_id"),
    ("number_input", "Rooms", 2, "rooms"),
    ("number_input", "Food + local travel per person/day (₹)", 2000, "daily_local_per_person"),
    ("multiselect", "Hotel amenities", ["gym"], "amenities"),
    ("text_area", "Tell the consultant anything else", "Prefer quiet evenings", "notes"),
])
def test_each_refinement_applies_and_can_be_reversed(monkeypatch, kind, label, value, field):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    with patch("travel_planner.agent.consult", return_value=AgentResult("test advice", [])) as agent, \
         patch("travel_planner.core.get_weather", return_value={"days": [], "note": "test", "status": "forecast"}):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
        app.button[0].click().run()
        baseline = app.session_state["plan"]
        widget = next(item for item in getattr(app, kind) if item.label == label)
        original = widget.value
        widget.set_value(value)
        app.button[1].click().run()
        assert not app.exception
        revised = app.session_state["plan"]
        assert revised["request"][field] == value
        assert agent.call_args.args[0][field] == value
        if field in {"rooms", "daily_local_per_person", "budget", "max_nightly_price"}:
            assert revised["budget"] != baseline["budget"]
        if field in {"hotel_id", "amenities"}:
            assert revised["hotel"]["hotel_id"] != baseline["hotel"]["hotel_id"]
        if field in {"interests", "pace"}:
            assert revised["days"] != baseline["days"]
        if field == "min_stars":
            assert all(row["stars"] >= 5 for row in revised["hotel_search"]["options"])
        next(item for item in getattr(app, kind) if item.label == label).set_value(original)
        app.button[1].click().run()
        assert not app.exception
        restored = app.session_state["plan"]
        assert restored["hotel"] == baseline["hotel"]
        assert restored["budget"] == baseline["budget"]
        assert restored["days"] == baseline["days"]


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


def test_repeated_empty_results_explain_missing_matches():
    with patch("travel_planner.agent.consult", return_value=AgentResult("test", [])), \
         patch("travel_planner.core.get_weather", return_value={"days": [], "note": "test", "status": "forecast"}):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
        app.button[0].click().run()
        next(w for w in app.number_input if w.label == "Hotel per room/night (₹)").set_value(500)
        next(w for w in app.multiselect if w.label == "Things you enjoy").set_value(["museum"])
        app.button[1].click().run()
        app.button[1].click().run()
        assert not app.exception
        feedback = app.session_state["refinement_feedback"]
        assert "No hotel meets" in feedback
        assert "No sourced attractions match" in feedback
        assert "ranks highest" not in feedback
