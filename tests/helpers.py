"""Shared test helpers: a fake Tk root and sample API result fixtures.

FakeRoot is deliberately NOT a tkinter widget - it only records after()
calls so tests can prove the worker schedules results instead of
touching widgets, then invoke the callback themselves to simulate the
GUI thread.
"""

from typing import Any, Callable


class FakeRoot:
    """Duck-typed stand-in for a Tk root that records after() calls."""

    def __init__(self) -> None:
        self.after_calls: list[tuple[int, Callable, tuple]] = []

    def after(self, delay: int, func: Callable, *args: Any) -> None:
        self.after_calls.append((delay, func, args))


def make_success_result() -> dict:
    """A realistic api.fetch_route success dict (GraphHopper-shaped)."""
    return {
        "ok": True,
        "url": "https://graphhopper.com/api/1/route?...",
        "data": {
            "paths": [{
                "distance": 15830.0,      # meters
                "time": 1661000.0,        # milliseconds
                "instructions": [
                    {"text": "Turn left onto Main Street",
                     "distance": 350.0},
                    {"text": "Continue straight",
                     "distance": 15480.0},
                ],
            }],
        },
        "from_name": "Quezon City, Metro Manila, PH",
        "to_name": "Makati, Metro Manila, PH",
    }


def make_failure_result() -> dict:
    """A realistic api.fetch_route failure dict."""
    return {
        "ok": False,
        "title": "Location not found: Nowhere",
        "detail": "GraphHopper could not match that place.",
    }
