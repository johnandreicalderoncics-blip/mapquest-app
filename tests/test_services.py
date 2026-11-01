"""Tests for backend/services.py: validation, key resolution, route shaping.

GraphHopper calls are mocked with tests.helpers fixtures; no network
request is ever made.
"""

import re
from pathlib import Path
from unittest import mock

import pytest

from backend import services
from tests.helpers import make_failure_result, make_success_result


class TestValidateInputs:
    def test_blank_origin(self):
        assert services.validate_inputs("", "Makati") == \
            "Please enter a starting location."

    def test_blank_destination(self):
        assert services.validate_inputs("Quezon City", "") == \
            "Please enter a destination."

    def test_whitespace_only_inputs(self):
        assert services.validate_inputs("   ", "  ") is not None

    def test_valid_inputs_return_none(self):
        assert services.validate_inputs("Quezon City", "Makati") is None


class TestResolveKey:
    def test_env_var_key_is_returned(self, monkeypatch):
        monkeypatch.setenv("GRAPHOPPER_KEY", "env-key")
        assert services.resolve_key() == "env-key"

    def test_missing_everything_returns_none(self, monkeypatch):
        monkeypatch.delenv("GRAPHOPPER_KEY", raising=False)
        with mock.patch.object(services.config, "CONFIG_FILE",
                               Path("definitely-missing.ini")):
            assert services.resolve_key() is None


class TestGetRouteSuccess:
    def test_success_shape_is_template_ready(self):
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("k", "A", "B", "metric", "car")

        assert result["ok"] is True
        assert result["from_name"] == "Quezon City, Metro Manila, PH"
        assert result["to_name"] == "Makati, Metro Manila, PH"
        assert result["profile_label"] == "Car (driving)"
        assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result["duration"])
        assert result["distance"] == "15.83 km"
        assert result["fuel"] == "1.27 L"

    def test_success_result_never_contains_the_api_url(self):
        # The raw fetch_route dict embeds the API key in "url"; the
        # service layer must strip it.
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("k", "A", "B", "metric", "car")
        assert "url" not in result

    def test_steps_are_numbered_with_formatted_distances(self):
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("k", "A", "B", "metric", "car")
        assert result["steps"] == [
            {"number": 1, "text": "Turn left onto Main Street",
             "distance": "0.35 km"},
            {"number": 2, "text": "Continue straight",
             "distance": "15.48 km"},
        ]

    def test_imperial_distance(self):
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("k", "A", "B", "imperial", "car")
        assert result["distance"] == "9.84 mi"

    def test_bike_fuel_is_na(self):
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("k", "A", "B", "metric", "bike")
        assert result["fuel"].startswith("N/A")

    def test_empty_instructions_give_empty_steps(self):
        success = make_success_result()
        success["data"]["paths"][0]["instructions"] = []
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("k", "A", "B", "metric", "car")
        assert result["steps"] == []


class TestGetRouteFailure:
    def test_failure_dict_passes_through_unchanged(self):
        failure = make_failure_result()
        with mock.patch.object(services.api, "fetch_route",
                               return_value=failure):
            assert services.get_route("k", "A", "B", "metric",
                                      "car") is failure

    def test_unexpected_exception_becomes_friendly_failure(self):
        with mock.patch.object(services.api, "fetch_route",
                               side_effect=RuntimeError("boom")):
            result = services.get_route("k", "A", "B", "metric", "car")
        assert result["ok"] is False
        assert result["title"] == "Unexpected error"
        # No exception internals leak to the user.
        assert "RuntimeError" not in result["detail"]
        assert "boom" not in result["detail"]
