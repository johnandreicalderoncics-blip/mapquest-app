"""Basic tests for backend/formatting.py without display imports."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from backend import formatting


class FormatTimeTests(unittest.TestCase):
    def test_milliseconds_to_hh_mm_ss(self) -> None:
        self.assertEqual(formatting.format_time(1661000), "00:27:41")

    def test_zero(self) -> None:
        self.assertEqual(formatting.format_time(0), "00:00:00")

    def test_hours(self) -> None:
        self.assertEqual(formatting.format_time(3_600_000 * 2 + 61_000),
                         "02:01:01")


class FormatDistanceTests(unittest.TestCase):
    def test_metric(self) -> None:
        self.assertEqual(formatting.format_distance(15830, "metric"),
                         "15.83 km")

    def test_imperial(self) -> None:
        self.assertEqual(formatting.format_distance(15830, "imperial"),
                         "9.84 mi")


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


if __name__ == "__main__":
    unittest.main()
