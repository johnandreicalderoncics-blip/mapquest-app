"""Unit tests for route coordinate extraction and validation.

This test suite covers:
1. CoordinateValidator class - bounds checking and filtering
2. extract_route_geometry function - nested path navigation, conversion, error handling
"""

import pytest
from src.frontend.desktop.map_widget import (
    CoordinateValidator,
    extract_route_geometry
)


class TestCoordinateValidator:
    """Test suite for CoordinateValidator class."""
    
    def test_is_valid_with_valid_coordinates(self):
        """Valid coordinates within bounds should return True."""
        assert CoordinateValidator.is_valid(0.0, 0.0) is True
        assert CoordinateValidator.is_valid(45.5, -122.7) is True
        assert CoordinateValidator.is_valid(-33.9, 151.2) is True
        assert CoordinateValidator.is_valid(90.0, 180.0) is True
        assert CoordinateValidator.is_valid(-90.0, -180.0) is True
    
    def test_is_valid_with_boundary_coordinates(self):
        """Boundary values should be considered valid."""
        # Maximum bounds
        assert CoordinateValidator.is_valid(90.0, 180.0) is True
        assert CoordinateValidator.is_valid(90.0, -180.0) is True
        
        # Minimum bounds
        assert CoordinateValidator.is_valid(-90.0, 180.0) is True
        assert CoordinateValidator.is_valid(-90.0, -180.0) is True
    
    def test_is_valid_with_invalid_latitude(self):
        """Latitude outside [-90, 90] should return False."""
        assert CoordinateValidator.is_valid(90.1, 0.0) is False
        assert CoordinateValidator.is_valid(-90.1, 0.0) is False
        assert CoordinateValidator.is_valid(91.0, 0.0) is False
        assert CoordinateValidator.is_valid(-91.0, 0.0) is False
        assert CoordinateValidator.is_valid(180.0, 0.0) is False
    
    def test_is_valid_with_invalid_longitude(self):
        """Longitude outside [-180, 180] should return False."""
        assert CoordinateValidator.is_valid(0.0, 180.1) is False
        assert CoordinateValidator.is_valid(0.0, -180.1) is False
        assert CoordinateValidator.is_valid(0.0, 181.0) is False
        assert CoordinateValidator.is_valid(0.0, -181.0) is False
        assert CoordinateValidator.is_valid(0.0, 360.0) is False
    
    def test_is_valid_with_numeric_strings(self):
        """Numeric strings that can be converted to float should be validated."""
        # These should work because float() conversion succeeds
        assert CoordinateValidator.is_valid("45.5", "-122.7") is True
        assert CoordinateValidator.is_valid("0", "0") is True
    
    def test_is_valid_with_non_numeric_input(self):
        """Truly non-numeric inputs should raise TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid("invalid", "data")
        
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid(None, None)
        
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid([], [])
        
        with pytest.raises((TypeError, ValueError)):
            CoordinateValidator.is_valid({}, {})
    
    def test_filter_valid_with_all_valid_coordinates(self):
        """All valid coordinates should be preserved."""
        coords = [
            (45.5, -122.7),
            (40.7, -74.0),
            (-33.9, 151.2)
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 3
        assert result == coords
    
    def test_filter_valid_with_mixed_coordinates(self):
        """Only valid coordinates should be preserved."""
        coords = [
            (45.5, -122.7),      # Valid
            (91.0, 0.0),         # Invalid lat
            (40.7, -74.0),       # Valid
            (0.0, 181.0),        # Invalid lon
            (-33.9, 151.2)       # Valid
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 3
        assert result == [(45.5, -122.7), (40.7, -74.0), (-33.9, 151.2)]
    
    def test_filter_valid_with_all_invalid_coordinates(self):
        """All invalid coordinates should be filtered out."""
        coords = [
            (91.0, 0.0),
            (0.0, 181.0),
            (-91.0, -181.0)
        ]
        result = CoordinateValidator.filter_valid(coords)
        assert len(result) == 0
        assert result == []
    
    def test_filter_valid_with_empty_list(self):
        """Empty list should return empty list."""
        result = CoordinateValidator.filter_valid([])
        assert result == []
    
    def test_filter_valid_with_malformed_coordinates(self):
        """Malformed coordinate entries should be filtered out."""
        coords = [
            (45.5, -122.7),           # Valid
            (40.7,),                  # Missing longitude
            ("invalid", "data"),      # Non-numeric strings
            None,                     # None entry
            [40.7, -74.0],           # List instead of tuple (should work)
            (0.0, 181.0),            # Invalid bounds
        ]
        result = CoordinateValidator.filter_valid(coords)
        # Should preserve only first and list entries (if valid)
        assert len(result) == 2
        assert (45.5, -122.7) in result
        assert (40.7, -74.0) in result


class TestExtractRouteGeometry:
    """Test suite for extract_route_geometry function."""
    
    def test_extract_valid_coordinates(self):
        """Valid result should extract and convert coordinates correctly."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [-122.7, 45.5],   # [lon, lat] format
                                [-74.0, 40.7],
                                [151.2, -33.9]
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        
        # Should convert to [lat, lon] format
        assert len(coords) == 3
        assert coords[0] == (45.5, -122.7)
        assert coords[1] == (40.7, -74.0)
        assert coords[2] == (-33.9, 151.2)
    
    def test_extract_with_ok_false(self):
        """Result with ok=False should return empty list."""
        result = {
            "ok": False,
            "title": "Error",
            "detail": "Route not found"
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_missing_data_key(self):
        """Missing 'data' key should return empty list."""
        result = {
            "ok": True
            # Missing "data" key
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_missing_paths_key(self):
        """Missing 'paths' key should return empty list."""
        result = {
            "ok": True,
            "data": {}  # Missing "paths" key
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_empty_paths_list(self):
        """Empty paths list should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": []  # Empty list
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_missing_points_key(self):
        """Missing 'points' key should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": [{}]  # Missing "points" key
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_missing_coordinates_key(self):
        """Missing 'coordinates' key should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {}  # Missing "coordinates" key
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_empty_coordinates_list(self):
        """Empty coordinates list should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": []  # Empty list
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_filters_invalid_latitudes(self):
        """Coordinates with invalid latitudes should be filtered out."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [-122.7, 45.5],    # Valid
                                [0.0, 91.0],       # Invalid lat (> 90)
                                [-74.0, 40.7],     # Valid
                                [0.0, -91.0],      # Invalid lat (< -90)
                                [151.2, -33.9]     # Valid
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        
        # Only 3 valid coordinates should be extracted
        assert len(coords) == 3
        assert coords[0] == (45.5, -122.7)
        assert coords[1] == (40.7, -74.0)
        assert coords[2] == (-33.9, 151.2)
    
    def test_extract_filters_invalid_longitudes(self):
        """Coordinates with invalid longitudes should be filtered out."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [-122.7, 45.5],    # Valid
                                [181.0, 0.0],      # Invalid lon (> 180)
                                [-74.0, 40.7],     # Valid
                                [-181.0, 0.0],     # Invalid lon (< -180)
                                [151.2, -33.9]     # Valid
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        
        # Only 3 valid coordinates should be extracted
        assert len(coords) == 3
        assert coords[0] == (45.5, -122.7)
        assert coords[1] == (40.7, -74.0)
        assert coords[2] == (-33.9, 151.2)
    
    def test_extract_handles_malformed_coordinates(self):
        """Malformed coordinate entries should be skipped."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [-122.7, 45.5],        # Valid
                                [40.7],                # Missing element
                                ["invalid", "data"],   # Non-numeric
                                None,                  # None entry
                                [-74.0, 40.7],         # Valid
                                {"lon": 151.2, "lat": -33.9}  # Dict instead of list
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        
        # Only 2 valid coordinates should be extracted
        assert len(coords) == 2
        assert coords[0] == (45.5, -122.7)
        assert coords[1] == (40.7, -74.0)
    
    def test_extract_with_all_invalid_coordinates(self):
        """All invalid coordinates should result in empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [181.0, 91.0],     # Both invalid
                                [-181.0, -91.0],   # Both invalid
                                [0.0, 100.0]       # Invalid lat
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_with_invalid_paths_type(self):
        """Non-list paths should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": "not a list"  # Invalid type
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_with_invalid_points_type(self):
        """Non-dict points should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": "not a dict"  # Invalid type
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_with_invalid_coordinates_type(self):
        """Non-list coordinates should return empty list."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": "not a list"  # Invalid type
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert coords == []
    
    def test_extract_with_single_coordinate(self):
        """Single coordinate should be extracted correctly."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [-122.7, 45.5]
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert len(coords) == 1
        assert coords[0] == (45.5, -122.7)
    
    def test_extract_with_large_coordinate_list(self):
        """Large coordinate list should be handled correctly."""
        # Create 1000 coordinates
        coordinates = [[i * 0.1, i * 0.05] for i in range(1000)]
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": coordinates
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        
        # Not all will be valid due to bounds, but should handle gracefully
        assert isinstance(coords, list)
        # First few should be valid
        assert (0.0, 0.0) in coords
        assert (0.05, 0.1) in coords
    
    def test_extract_preserves_precision(self):
        """Floating point precision should be preserved."""
        result = {
            "ok": True,
            "data": {
                "paths": [
                    {
                        "points": {
                            "coordinates": [
                                [-122.6789123, 45.5234567]
                            ]
                        }
                    }
                ]
            }
        }
        coords = extract_route_geometry(result)
        assert len(coords) == 1
        # Check precision (allow small floating point errors)
        lat, lon = coords[0]
        assert abs(lat - 45.5234567) < 1e-6
        assert abs(lon - (-122.6789123)) < 1e-6
    
    def test_extract_with_unexpected_exception(self):
        """Unexpected errors should be caught and return empty list."""
        # Pass invalid input type
        result = None
        coords = extract_route_geometry(result)
        assert coords == []
        
        # Pass non-dict
        result = "not a dict"
        coords = extract_route_geometry(result)
        assert coords == []
        
        # Pass list instead of dict
        result = []
        coords = extract_route_geometry(result)
        assert coords == []
