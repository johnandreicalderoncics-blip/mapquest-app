"""Unit tests for CoordinateValidator class.

Tests validate that geographic coordinates are properly validated against
bounds and that invalid coordinates are filtered out correctly.
"""

import pytest
from src.frontend.desktop.map_widget import CoordinateValidator


class TestCoordinateValidator:
    """Test suite for CoordinateValidator static methods."""
    
    def test_is_valid_with_valid_coordinates(self):
        """Test that valid coordinates pass validation."""
        # Test coordinates well within bounds
        assert CoordinateValidator.is_valid(0.0, 0.0) is True
        assert CoordinateValidator.is_valid(45.5, -122.6) is True
        assert CoordinateValidator.is_valid(-33.8, 151.2) is True
        
        # Test boundary values
        assert CoordinateValidator.is_valid(90.0, 180.0) is True
        assert CoordinateValidator.is_valid(-90.0, -180.0) is True
        assert CoordinateValidator.is_valid(90.0, -180.0) is True
        assert CoordinateValidator.is_valid(-90.0, 180.0) is True
    
    def test_is_valid_with_invalid_latitudes(self):
        """Test that latitudes outside [-90, 90] are rejected."""
        assert CoordinateValidator.is_valid(90.1, 0.0) is False
        assert CoordinateValidator.is_valid(-90.1, 0.0) is False
        assert CoordinateValidator.is_valid(100.0, 0.0) is False
        assert CoordinateValidator.is_valid(-100.0, 0.0) is False
        assert CoordinateValidator.is_valid(200.0, 0.0) is False
    
    def test_is_valid_with_invalid_longitudes(self):
        """Test that longitudes outside [-180, 180] are rejected."""
        assert CoordinateValidator.is_valid(0.0, 180.1) is False
        assert CoordinateValidator.is_valid(0.0, -180.1) is False
        assert CoordinateValidator.is_valid(0.0, 200.0) is False
        assert CoordinateValidator.is_valid(0.0, -200.0) is False
        assert CoordinateValidator.is_valid(0.0, 360.0) is False
    
    def test_is_valid_with_both_invalid(self):
        """Test that coordinates with both invalid lat and lon are rejected."""
        assert CoordinateValidator.is_valid(100.0, 200.0) is False
        assert CoordinateValidator.is_valid(-100.0, -200.0) is False
    
    def test_is_valid_with_integer_inputs(self):
        """Test that integer inputs are handled correctly."""
        assert CoordinateValidator.is_valid(45, -122) is True
        assert CoordinateValidator.is_valid(100, 0) is False
        assert CoordinateValidator.is_valid(0, 200) is False
    
    def test_is_valid_with_string_numbers(self):
        """Test that string representations of numbers are handled."""
        assert CoordinateValidator.is_valid("45.5", "-122.6") is True
        assert CoordinateValidator.is_valid("100.0", "0.0") is False
    
    def test_is_valid_raises_on_non_numeric(self):
        """Test that non-numeric inputs raise appropriate exceptions."""
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid("abc", 0.0)
        
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid(0.0, "xyz")
        
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid(None, 0.0)
        
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid(0.0, None)
    
    def test_filter_valid_with_all_valid_coordinates(self):
        """Test that filter_valid returns all coordinates when all are valid."""
        coords = [
            (45.5, -122.6),
            (-33.8, 151.2),
            (0.0, 0.0),
            (90.0, 180.0),
            (-90.0, -180.0)
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 5
        assert result == [
            (45.5, -122.6),
            (-33.8, 151.2),
            (0.0, 0.0),
            (90.0, 180.0),
            (-90.0, -180.0)
        ]
    
    def test_filter_valid_removes_invalid_latitudes(self):
        """Test that coordinates with invalid latitudes are filtered out."""
        coords = [
            (45.5, -122.6),    # Valid
            (100.0, 0.0),      # Invalid lat
            (-33.8, 151.2),    # Valid
            (-95.0, 0.0)       # Invalid lat
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_removes_invalid_longitudes(self):
        """Test that coordinates with invalid longitudes are filtered out."""
        coords = [
            (45.5, -122.6),    # Valid
            (0.0, 200.0),      # Invalid lon
            (-33.8, 151.2),    # Valid
            (0.0, -190.0)      # Invalid lon
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_removes_coordinates_with_both_invalid(self):
        """Test that coordinates with both invalid lat and lon are filtered."""
        coords = [
            (45.5, -122.6),    # Valid
            (100.0, 200.0),    # Both invalid
            (-33.8, 151.2)     # Valid
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_with_empty_list(self):
        """Test that filter_valid handles empty list correctly."""
        coords = []
        result = CoordinateValidator.filter_valid(coords)
        assert result == []
    
    def test_filter_valid_with_all_invalid(self):
        """Test that filter_valid returns empty list when all coords invalid."""
        coords = [
            (100.0, 0.0),
            (0.0, 200.0),
            (-100.0, -200.0)
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert result == []
    
    def test_filter_valid_handles_lists(self):
        """Test that filter_valid works with lists instead of tuples."""
        coords = [
            [45.5, -122.6],
            [100.0, 0.0],      # Invalid
            [-33.8, 151.2]
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_handles_mixed_types(self):
        """Test that filter_valid works with mixed tuples and lists."""
        coords = [
            (45.5, -122.6),
            [100.0, 0.0],      # Invalid
            (-33.8, 151.2),
            [0.0, 200.0]       # Invalid
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_skips_malformed_coordinates(self):
        """Test that filter_valid skips coordinates that are not tuples/lists."""
        coords = [
            (45.5, -122.6),
            "not a coordinate",
            (-33.8, 151.2),
            None,
            42  # Single number, not a pair
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_skips_coordinates_with_too_few_elements(self):
        """Test that filter_valid skips coordinates with less than 2 elements."""
        coords = [
            (45.5, -122.6),
            (45.5,),           # Only one element
            [],                # Empty
            (-33.8, 151.2)
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_handles_coordinates_with_extra_elements(self):
        """Test that filter_valid uses first two elements if more exist."""
        coords = [
            (45.5, -122.6, 100.0),  # Has elevation, should use first two
            (-33.8, 151.2)
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_handles_non_numeric_elements(self):
        """Test that filter_valid skips coordinates with non-numeric values."""
        coords = [
            (45.5, -122.6),
            ("abc", "xyz"),    # Non-numeric
            (-33.8, 151.2),
            (45.5, None)       # None value
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        assert result == [(45.5, -122.6), (-33.8, 151.2)]
    
    def test_filter_valid_converts_to_float(self):
        """Test that filter_valid converts numeric types to float."""
        coords = [
            (45, -122),        # Integers
            ("45.5", "-122.6") # String numbers
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 2
        # Check that results are floats
        assert isinstance(result[0][0], float)
        assert isinstance(result[0][1], float)
        assert isinstance(result[1][0], float)
        assert isinstance(result[1][1], float)
    
    def test_filter_valid_raises_on_non_iterable(self):
        """Test that filter_valid raises TypeError for non-iterable input."""
        with pytest.raises(TypeError):
            CoordinateValidator.filter_valid(42)
        
        with pytest.raises(TypeError):
            CoordinateValidator.filter_valid(None)
