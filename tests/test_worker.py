"""Tests for the worker-thread handoff in gui.py.

The key guarantee: the worker never touches widgets - it schedules the
result exactly once via root.after(0, ...) and the FakeRoot (which
never executes callbacks) proves it.
"""

import unittest
from unittest import mock

from backend import api
from tests.helpers import FakeRoot, make_success_result

import gui


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


if __name__ == "__main__":
    unittest.main()
