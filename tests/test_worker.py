"""Tests for the worker-thread handoff in gui.py.

The key guarantee: the worker never touches widgets - it schedules the
result exactly once via root.after(0, ...) and the FakeRoot (which
never executes callbacks) proves it.
"""

import unittest
from unittest import mock

from backend import api
from tests.helpers import FakeRoot, make_success_result

from src.frontend.desktop import gui


class RunRouteRequestTests(unittest.TestCase):
    def test_passes_arguments_to_fetch_route(self) -> None:
        with mock.patch.object(api, "fetch_route",
                               return_value=make_success_result()) as mocked:
            gui.run_route_request("k", "A", "B", "metric", "car")
        mocked.assert_called_once_with("k", "A", "B", "metric", "car")

    def test_unexpected_exception_becomes_failure_dict(self) -> None:
        with mock.patch.object(api, "fetch_route",
                               side_effect=RuntimeError("boom")):
            result = gui.run_route_request("k", "A", "B", "metric", "car")
        self.assertFalse(result["ok"])
        self.assertEqual(result["title"], "Unexpected error")
        self.assertIn("RuntimeError", result["detail"])

    def test_expected_failure_passes_through_unchanged(self) -> None:
        failure = {"ok": False, "title": "t", "detail": "d"}
        with mock.patch.object(api, "fetch_route", return_value=failure):
            self.assertIs(gui.run_route_request("k", "A", "B",
                                                "metric", "car"), failure)


class StartRouteRequestTests(unittest.TestCase):
    def test_success_schedules_result_via_after_only(self) -> None:
        root = FakeRoot()
        delivered: list[dict] = []
        recorder = delivered.append

        with mock.patch.object(api, "fetch_route",
                               return_value=make_success_result()):
            thread = gui.start_route_request(root, recorder,
                                             "k", "A", "B", "metric",
                                             "car")
            thread.join(timeout=5)

        # Exactly one after() handoff with delay 0 and the result dict.
        self.assertEqual(len(root.after_calls), 1)
        delay, callback, args = root.after_calls[0]
        self.assertEqual(delay, 0)
        self.assertIs(callback, recorder)
        self.assertEqual(args, (make_success_result(),))
        # The worker never executed the callback itself (FakeRoot does
        # not run it, so the list is still empty here).
        self.assertEqual(delivered, [])

    def test_unexpected_error_is_scheduled_as_failure(self) -> None:
        root = FakeRoot()
        delivered: list[dict] = []

        with mock.patch.object(api, "fetch_route",
                               side_effect=RuntimeError("boom")):
            thread = gui.start_route_request(root, delivered.append,
                                             "k", "A", "B", "metric",
                                             "car")
            thread.join(timeout=5)

        delay, callback, args = root.after_calls[0]
        result = args[0]
        self.assertFalse(result["ok"])
        self.assertEqual(result["title"], "Unexpected error")
        # Simulating the GUI thread invoking the callback delivers it.
        callback(*args)
        self.assertEqual(delivered, [result])

    def test_timeout_delivers_timeout_result(self) -> None:
        """Verify timeout handling when request exceeds timeout_seconds."""
        import time
        root = FakeRoot()
        delivered: list[dict] = []

        # Mock fetch_route to take longer than the timeout
        def slow_fetch(*args, **kwargs):
            time.sleep(2)  # Sleep longer than timeout
            return make_success_result()

        with mock.patch.object(api, "fetch_route", side_effect=slow_fetch):
            thread = gui.start_route_request(root, delivered.append,
                                             "k", "A", "B", "metric",
                                             "car", timeout_seconds=0.5)
            # Wait for timeout to trigger
            time.sleep(1)

        # Should have one after() call with timeout result
        self.assertGreaterEqual(len(root.after_calls), 1)
        delay, callback, args = root.after_calls[0]
        result = args[0]
        self.assertFalse(result["ok"])
        self.assertEqual(result["title"], "The request timed out")
        self.assertIn("did not complete within", result["detail"])

    def test_successful_result_prevents_timeout(self) -> None:
        """Verify successful result arrives before timeout."""
        root = FakeRoot()
        delivered: list[dict] = []

        # Mock fetch_route to complete quickly
        with mock.patch.object(api, "fetch_route",
                               return_value=make_success_result()):
            thread = gui.start_route_request(root, delivered.append,
                                             "k", "A", "B", "metric",
                                             "car", timeout_seconds=5)
            thread.join(timeout=2)

        # Should have exactly one after() call with success result
        self.assertEqual(len(root.after_calls), 1)
        delay, callback, args = root.after_calls[0]
        result = args[0]
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
