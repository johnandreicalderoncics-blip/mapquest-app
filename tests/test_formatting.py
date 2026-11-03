"""Tests for backend/formatting.py and display.py's re-exports."""

import logging
import unittest

from backend import formatting
from src.frontend.cli import display


class FormatTimeTests(unittest.TestCase):
    def test_milliseconds_to_hh_mm_ss(self) -> None:
        self.assertEqual(formatting.format_time(1661000), "00:27:41")

    def test_zero(self) -> None:
        self.assertEqual(formatting.format_time(0), "00:00:00")

    def test_hours(self) -> None:
        self.assertEqual(formatting.format_time(3_600_000 * 2 + 61_000),
                         "02:01:01")
    
    def test_none_value(self) -> None:
        """None values should return 'N/A'."""
        self.assertEqual(formatting.format_time(None), "N/A")
    
    def test_negative_value(self) -> None:
        """Negative values should return 'N/A'."""
        self.assertEqual(formatting.format_time(-1000), "N/A")
    
    def test_non_numeric_value(self) -> None:
        """Non-numeric values should return 'N/A'."""
        self.assertEqual(formatting.format_time("invalid"), "N/A")
        self.assertEqual(formatting.format_time([1, 2, 3]), "N/A")


class FormatDistanceTests(unittest.TestCase):
    def test_metric(self) -> None:
        self.assertEqual(formatting.format_distance(15830, "metric"),
                         "15.83 km")

    def test_imperial(self) -> None:
        self.assertEqual(formatting.format_distance(15830, "imperial"),
                         "9.84 mi")
    
    def test_none_meters(self) -> None:
        """None meters should return 'N/A'."""
        self.assertEqual(formatting.format_distance(None, "metric"), "N/A")
    
    def test_negative_meters(self) -> None:
        """Negative meters should return 'N/A'."""
        self.assertEqual(formatting.format_distance(-100, "metric"), "N/A")
    
    def test_non_numeric_meters(self) -> None:
        """Non-numeric meters should return 'N/A'."""
        self.assertEqual(formatting.format_distance("invalid", "metric"), "N/A")
        self.assertEqual(formatting.format_distance([1, 2], "metric"), "N/A")
    
    def test_invalid_units(self) -> None:
        """Invalid units should default to metric."""
        result = formatting.format_distance(15830, "invalid_unit")
        self.assertEqual(result, "15.83 km")  # Defaults to metric


class FormatFuelEstimateTests(unittest.TestCase):
    """Must match the fuel logic display.show_route used before."""

    def test_car_metric_liters(self) -> None:
        self.assertEqual(
            formatting.format_fuel_estimate(25000, "metric", "car"),
            "2.00 L")

    def test_car_imperial_gallons(self) -> None:
        self.assertEqual(
            formatting.format_fuel_estimate(25000, "imperial", "car"),
            "0.53 gal")

    def test_non_car_na(self) -> None:
        for profile in ("bike", "walk"):
            self.assertEqual(
                formatting.format_fuel_estimate(25000, "metric", profile),
                "N/A (not applicable for this travel mode)")
    
    def test_none_meters(self) -> None:
        """None meters should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate(None, "metric", "car"), "N/A")
    
    def test_negative_meters(self) -> None:
        """Negative meters should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate(-100, "metric", "car"), "N/A")
    
    def test_non_numeric_meters(self) -> None:
        """Non-numeric meters should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate("invalid", "metric", "car"), "N/A")
    
    def test_invalid_units(self) -> None:
        """Invalid units should default to metric."""
        result = formatting.format_fuel_estimate(25000, "invalid_unit", "car")
        self.assertEqual(result, "2.00 L")  # Defaults to metric
    
    def test_invalid_profile(self) -> None:
        """Invalid profile should return 'N/A'."""
        self.assertEqual(formatting.format_fuel_estimate(25000, "metric", "invalid_profile"), "N/A")


class DisplayReExportTests(unittest.TestCase):
    """display.py must keep exposing the moved names (CLI compatibility)."""

    def test_display_reexports_formatting(self) -> None:
        self.assertIs(display.format_time, formatting.format_time)
        self.assertIs(display.format_distance, formatting.format_distance)
        self.assertIs(display.format_fuel_estimate,
                      formatting.format_fuel_estimate)
        self.assertIs(display.UNIT_LABELS, formatting.UNIT_LABELS)
        self.assertIs(display.PROFILE_LABELS, formatting.PROFILE_LABELS)
        self.assertEqual(display.METERS_PER_MILE, formatting.METERS_PER_MILE)


if __name__ == "__main__":
    unittest.main()
