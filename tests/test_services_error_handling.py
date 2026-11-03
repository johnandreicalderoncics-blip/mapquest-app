"""Tests for enhanced error handling in backend/services.py.

Validates input parameter validation, missing required fields,
invalid route data structures, and logging of validation failures.
"""

from unittest import mock

import pytest

from backend import services
from tests.helpers import make_success_result


class TestValidateInputsEnhanced:
    """Test enhanced validation with type checking and logging."""
    
    def test_non_string_origin(self):
        """Reject non-string origin parameter."""
        error = services.validate_inputs(123, "Destination")
        assert error == "Invalid origin parameter type."
    
    def test_non_string_destination(self):
        """Reject non-string destination parameter."""
        error = services.validate_inputs("Origin", 456)
        assert error == "Invalid destination parameter type."
    
    def test_none_origin(self):
        """Reject None as origin parameter."""
        error = services.validate_inputs(None, "Destination")
        assert error == "Invalid origin parameter type."
    
    def test_none_destination(self):
        """Reject None as destination parameter."""
        error = services.validate_inputs("Origin", None)
        assert error == "Invalid destination parameter type."
    
    def test_list_parameters(self):
        """Reject list parameters."""
        error = services.validate_inputs(["Origin"], ["Destination"])
        assert error == "Invalid origin parameter type."


class TestGetRouteInputValidation:
    """Test get_route input parameter validation."""
    
    def test_empty_api_key(self):
        """Reject empty API key."""
        result = services.get_route("", "Origin", "Dest", "metric", "car")
        assert result["ok"] is False
        assert result["title"] == "Configuration error"
        assert "API key" in result["detail"]
    
    def test_whitespace_only_api_key(self):
        """Reject whitespace-only API key."""
        result = services.get_route("   ", "Origin", "Dest", "metric", "car")
        assert result["ok"] is False
        assert result["title"] == "Configuration error"
    
    def test_non_string_api_key(self):
        """Reject non-string API key."""
        result = services.get_route(12345, "Origin", "Dest", "metric", "car")
        assert result["ok"] is False
        assert result["title"] == "Configuration error"
    
    def test_empty_origin_in_get_route(self):
        """Reject empty origin in get_route."""
        result = services.get_route("key", "", "Dest", "metric", "car")
        assert result["ok"] is False
        assert result["title"] == "Invalid input"
        assert "Starting location" in result["detail"]
    
    def test_empty_destination_in_get_route(self):
        """Reject empty destination in get_route."""
        result = services.get_route("key", "Origin", "", "metric", "car")
        assert result["ok"] is False
        assert result["title"] == "Invalid input"
        assert "Destination" in result["detail"]
    
    def test_invalid_units_defaults_to_metric(self):
        """Invalid units parameter defaults to metric."""
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("key", "A", "B", "invalid_units", "car")
            # Should succeed with metric units
            assert result["ok"] is True
            # Verify metric unit was used (km not mi)
            assert "km" in result["distance"]
    
    def test_invalid_profile_defaults_to_car(self):
        """Invalid profile parameter defaults to car."""
        with mock.patch.object(services.api, "fetch_route",
                               return_value=make_success_result()):
            result = services.get_route("key", "A", "B", "metric", "invalid_profile")
            # Should succeed with car profile
            assert result["ok"] is True
            assert "Car" in result["profile_label"]


class TestGetRouteDataStructureValidation:
    """Test validation of route data structures."""
    
    def test_non_dict_result_from_api(self):
        """Handle non-dict result from API."""
        with mock.patch.object(services.api, "fetch_route",
                               return_value="not a dict"):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Unexpected error"
            assert "Invalid response" in result["detail"]
    
    def test_missing_data_key(self):
        """Handle missing 'data' key in successful result."""
        bad_result = {"ok": True, "from_name": "A", "to_name": "B"}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=bad_result):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Invalid route data"
            assert "missing required data" in result["detail"]
    
    def test_non_dict_data(self):
        """Handle non-dict data field."""
        bad_result = {"ok": True, "data": "not a dict"}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=bad_result):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Invalid route data"
            assert "invalid structure" in result["detail"]
    
    def test_missing_paths_list(self):
        """Handle missing 'paths' list."""
        bad_result = {"ok": True, "data": {}}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=bad_result):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Invalid route data"
            assert "No valid route path" in result["detail"]
    
    def test_empty_paths_list(self):
        """Handle empty 'paths' list."""
        bad_result = {"ok": True, "data": {"paths": []}}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=bad_result):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Invalid route data"
    
    def test_non_list_paths(self):
        """Handle non-list 'paths' field."""
        bad_result = {"ok": True, "data": {"paths": "not a list"}}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=bad_result):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Invalid route data"
    
    def test_non_dict_path(self):
        """Handle non-dict path element."""
        bad_result = {"ok": True, "data": {"paths": ["not a dict"]}}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=bad_result):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Invalid route data"
            assert "invalid structure" in result["detail"]


class TestGetRouteCoordinateValidation:
    """Test coordinate extraction and validation."""
    
    def test_invalid_distance_defaults_to_zero(self):
        """Handle invalid distance value."""
        success = make_success_result()
        success["data"]["paths"][0]["distance"] = "invalid"
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert result["distance"] == "0.00 km"
    
    def test_negative_distance_defaults_to_zero(self):
        """Handle negative distance value."""
        success = make_success_result()
        success["data"]["paths"][0]["distance"] = -100
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert result["distance"] == "0.00 km"
    
    def test_invalid_time_defaults_to_zero(self):
        """Handle invalid time value."""
        success = make_success_result()
        success["data"]["paths"][0]["time"] = "invalid"
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert result["duration"] == "00:00:00"
    
    def test_non_dict_points(self):
        """Handle non-dict points field."""
        success = make_success_result()
        success["data"]["paths"][0]["points"] = "not a dict"
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert result["route_points"] == []
    
    def test_non_list_coordinates(self):
        """Handle non-list coordinates field."""
        success = make_success_result()
        success["data"]["paths"][0]["points"] = {"coordinates": "not a list"}
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert result["route_points"] == []
    
    def test_filters_invalid_coordinate_format(self):
        """Filter out coordinates with invalid format."""
        success = make_success_result()
        success["data"]["paths"][0]["points"]["coordinates"] = [
            [121.05, 14.65],  # Valid
            "invalid",        # Invalid - not a list
            [121.06],         # Invalid - too short
            [121.07, 14.67],  # Valid
        ]
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert len(result["route_points"]) == 2
            assert result["route_points"] == [[14.65, 121.05], [14.67, 121.07]]
    
    def test_filters_out_of_bounds_coordinates(self):
        """Filter out coordinates outside valid bounds."""
        success = make_success_result()
        success["data"]["paths"][0]["points"]["coordinates"] = [
            [121.05, 14.65],    # Valid
            [200.0, 14.66],     # Invalid - lon > 180
            [121.06, 100.0],    # Invalid - lat > 90
            [-200.0, 14.67],    # Invalid - lon < -180
            [121.07, -100.0],   # Invalid - lat < -90
            [121.08, 14.68],    # Valid
        ]
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert len(result["route_points"]) == 2
            assert result["route_points"] == [[14.65, 121.05], [14.68, 121.08]]
    
    def test_handles_non_numeric_coordinates(self):
        """Filter out coordinates with non-numeric values."""
        success = make_success_result()
        success["data"]["paths"][0]["points"]["coordinates"] = [
            [121.05, 14.65],      # Valid
            ["abc", "def"],       # Invalid - non-numeric
            [None, 14.66],        # Invalid - None value
            [121.06, 14.67],      # Valid
        ]
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert len(result["route_points"]) == 2


class TestGetRouteInstructionsValidation:
    """Test validation of route instructions."""
    
    def test_non_list_instructions(self):
        """Handle non-list instructions field."""
        success = make_success_result()
        success["data"]["paths"][0]["instructions"] = "not a list"
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert result["steps"] == []
    
    def test_filters_non_dict_instructions(self):
        """Filter out non-dict instruction elements."""
        success = make_success_result()
        success["data"]["paths"][0]["instructions"] = [
            {"text": "Turn left", "distance": 350.0},  # Valid
            "invalid instruction",                      # Invalid
            {"text": "Continue", "distance": 500.0},   # Valid
        ]
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert len(result["steps"]) == 2
            assert result["steps"][0]["text"] == "Turn left"
            assert result["steps"][1]["text"] == "Continue"
    
    def test_invalid_step_distance_defaults_to_zero(self):
        """Handle invalid step distance value."""
        success = make_success_result()
        success["data"]["paths"][0]["instructions"] = [
            {"text": "Turn left", "distance": "invalid"},
            {"text": "Continue", "distance": -100},
        ]
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert len(result["steps"]) == 2
            assert result["steps"][0]["distance"] == "0.00 km"
            assert result["steps"][1]["distance"] == "0.00 km"
    
    def test_missing_step_text_uses_default(self):
        """Handle missing step text."""
        success = make_success_result()
        success["data"]["paths"][0]["instructions"] = [
            {"distance": 350.0},  # Missing text
        ]
        with mock.patch.object(services.api, "fetch_route",
                               return_value=success):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is True
            assert len(result["steps"]) == 1
            assert result["steps"][0]["text"] == "(no description)"


class TestGetRouteExceptionHandling:
    """Test exception handling in get_route."""
    
    def test_exception_during_processing_returns_error(self):
        """Handle unexpected exceptions gracefully."""
        with mock.patch.object(services.api, "fetch_route",
                               side_effect=RuntimeError("Unexpected error")):
            result = services.get_route("key", "A", "B", "metric", "car")
            assert result["ok"] is False
            assert result["title"] == "Unexpected error"
            # Should not leak exception details to user
            assert "RuntimeError" not in result["detail"]
    
    def test_exception_in_formatting_returns_error(self):
        """Handle exceptions during data formatting."""
        with mock.patch.object(services.formatting, "format_distance",
                               side_effect=ValueError("Format error")):
            with mock.patch.object(services.api, "fetch_route",
                                   return_value=make_success_result()):
                result = services.get_route("key", "A", "B", "metric", "car")
                assert result["ok"] is False
                assert result["title"] == "Unexpected error"
