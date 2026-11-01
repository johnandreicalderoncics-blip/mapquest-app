"""Tests for gui.py's pure logic: validation and result rendering.

No tkinter windows are created here; these functions are plain data
transformations, which is exactly why gui.py factors them out.
"""

import unittest

from tests.helpers import make_failure_result, make_success_result

import gui


class ValidateInputsTests(unittest.TestCase):
    def test_rejects_empty_origin(self) -> None:
        self.assertEqual(gui.validate_inputs("", "Makati"),
                         "Please enter a starting location.")

    def test_rejects_whitespace_destination(self) -> None:
        self.assertEqual(gui.validate_inputs("Quezon City", "   "),
                         "Please enter a destination.")

    def test_rejects_both_empty(self) -> None:
        self.assertIsNotNone(gui.validate_inputs("", ""))

    def test_accepts_valid_inputs(self) -> None:
        self.assertIsNone(gui.validate_inputs("Quezon City", "Makati"))


class ResultToLinesSuccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = gui.result_to_lines(make_success_result(),
                                         "metric", "car")

    def test_renders_resolved_places(self) -> None:
        self.assertIn("From: Quezon City, Metro Manila, PH", self.lines)
        self.assertIn("To: Makati, Metro Manila, PH", self.lines)

    def test_renders_travel_mode(self) -> None:
        self.assertIn("Travel mode: Car (driving)", self.lines)

    def test_renders_duration_and_distance(self) -> None:
        self.assertIn("Trip duration: 00:27:41", self.lines)
        self.assertIn("Distance (Kilometers): 15.83 km", self.lines)

    def test_renders_fuel_estimate(self) -> None:
        self.assertIn("Fuel used (Liters (est.)): 1.27 L", self.lines)

    def test_renders_numbered_instructions(self) -> None:
        self.assertIn("Turn-by-turn directions:", self.lines)
        self.assertIn("1. Turn left onto Main Street (0.35 km)",
                      self.lines)
        self.assertIn("2. Continue straight (15.48 km)", self.lines)

    def test_imperial_fuel_uses_gallons(self) -> None:
        lines = gui.result_to_lines(make_success_result(),
                                    "imperial", "car")
        self.assertTrue(any("gal" in line for line in lines))


class ResultToLinesFailureTests(unittest.TestCase):
    def test_renders_title_and_detail(self) -> None:
        failure = make_failure_result()
        lines = gui.result_to_lines(failure, "metric", "car")
        self.assertIn("Location not found: Nowhere", lines)
        self.assertIn("GraphHopper could not match that place.", lines)

    def test_failure_has_no_route_summary(self) -> None:
        lines = gui.result_to_lines(make_failure_result(),
                                    "metric", "car")
        self.assertFalse(any(line.startswith("From:") for line in lines))

    def test_missing_keys_do_not_crash(self) -> None:
        lines = gui.result_to_lines({"ok": False}, "metric", "car")
        self.assertIn("Unknown error", lines)


class ResultToLinesEdgeCaseTests(unittest.TestCase):
    def test_empty_instructions_note(self) -> None:
        result = make_success_result()
        result["data"]["paths"][0]["instructions"] = []
        lines = gui.result_to_lines(result, "metric", "car")
        self.assertIn("No turn-by-turn instructions were returned for "
                      "this route.", lines)

    def test_bike_fuel_is_na(self) -> None:
        lines = gui.result_to_lines(make_success_result(),
                                    "metric", "bike")
        self.assertIn("Fuel used (Liters (est.)): N/A (not applicable "
                      "for this travel mode)", lines)


if __name__ == "__main__":
    unittest.main()
