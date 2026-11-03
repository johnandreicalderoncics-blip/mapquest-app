"""Tests for error handling in backend/formatting.py."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from backend import formatting


class FormatTimeErrorTests(unittest.TestCase):
    """Test error handling for format_time function."""
    
    def test_valid_time(self) -> None:
        """Valid input should work correctly."""
        self.assertEqual(formatting.format_time(1661000), "00:27:41")
        self.assertEqual(formatting.format_time(0), "00:00:00")
    
    def test_none_value(self) -> None:
        """None values should return 'N/A'."""
        self.assertEqual(formatting.format_time(None), "N/A")
    
    def test_negative_value(self) -> None:
        """Negative values should return 'N/A'."""
        self.assertEqual(formatting.format_time(-1000), "N/A")
        self.assertEqual(formatting.format_time(-999999), "N/A")
    
    def test_non_numeric_value(self) -> None:
        """Non-numeric values should return 'N/A'."""
        self.assertEqual(formatting.format_time("invalid"), "N/A")
        self.assertEqual(formatting.format_time([1, 2, 3]), "N/A")
        self.assertEqual(formatting.format_time({}), "N/A")


class FormatDistanceErrorTests(unittest.TestCase):
    """Test error handling for format_distance function."""
    
    def test_valid_distance(self) -> None:
        """Valid input should work correctly."""
        self.assertEqual(formatting.format_distance(15830, "metric"), "15.83 km")
        self.assertEqual(formatting.format_distance(15830, "imperial"), "9.84 mi")
    
    def test_none_meters(self) -> None:
        """None meters should return 'N/A'."""
        self.assertEqual(formatting.format_distance(None, "metric"), "N/A")
        self.assertEqual(formatting.format_distance(None, "imperial"), "N/A")
    
    def test_negative_meters(self) -> None:
        """Negative meters should return 'N/A'."""
        self.assertEqual(formatting.format_distance(-100, "metric"), "N/A")
        self.assertEqual(formatting.format_distance(-9999, "imperial"), "N/A")
    
    def test_non_numeric_meters(self) -> None:
        """Non-numeric meters should return 'N/A'."""
        self.assertEqual(formatting.format_distance("invalid", "metric"), "N/A")
        self.assertEqual(formatting.format_distance([1, 2], "metric"), "N/A")
        self.assertEqual(formatting.format_distance({}, "imperial"), "N/A")
    
    def test_invalid_units(self) -> None:
        """Invalid units should default to metric."""
        result = formatting.format_distance(15830, "invalid_unit")
        self.assertEqual(result, "15.83 km")  # Defaults to metric
        
        result = formatting.format_distance(15830, "")
        self.assertEqual(result, "15.83 km")  # Empty string defaults to metric
        
        result = formatting.format_distance(15830, None)
        self.assertEqual(result, "15.83 km")  # None defaults to metric


class FormatFuelEstimateErrorTests(unittest.TestCase):
    """Test error handling for format_fuel_estimate function."""
    
    def test_valid_fuel_estimate(self) -> None:
        """Valid input should work correctly."""
        self.assertEqual(formatting.format_fuel_estimate(25000, "metric", "car"), "2.00 L")
        self.assertEqual(formatting.format_fuel_estimate(25000, "imperial", "car"), "0.53 gal")
        self.assertEqual(formatting.format_fuel_estimate(25000, "metric", "bike"), 
                        "N/A (not applicable for this travel mode)")
    
    def test_none_meters(self) -> None:
        """None meters should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate(None, "metric", "car"), "N/A")
        self.assertEqual(formatting.format_fuel_estimate(None, "imperial", "car"), "N/A")
    
    def test_negative_meters(self) -> None:
        """Negative meters should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate(-100, "metric", "car"), "N/A")
        self.assertEqual(formatting.format_fuel_estimate(-9999, "imperial", "car"), "N/A")
    
    def test_non_numeric_meters(self) -> None:
        """Non-numeric meters should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate("invalid", "metric", "car"), "N/A")
        self.assertEqual(formatting.format_fuel_estimate([1, 2], "metric", "car"), "N/A")
    
    def test_invalid_units(self) -> None:
        """Invalid units should default to metric."""
        result = formatting.format_fuel_estimate(25000, "invalid_unit", "car")
        self.assertEqual(result, "2.00 L")  # Defaults to metric
    
    def test_invalid_profile(self) -> None:
        """Invalid profile should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate(25000, "metric", "invalid_profile"), "N/A")
        self.assertEqual(formatting.format_fuel_estimate(25000, "metric", ""), "N/A")
        self.assertEqual(formatting.format_fuel_estimate(25000, "metric", None), "N/A")


if __name__ == "__main__":
    unittest.main()
