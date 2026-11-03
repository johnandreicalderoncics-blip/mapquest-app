"""Tests for Tasks 12.3, 13.2 and 13.3: debounce wiring, the error
handler, and empty-state fade-in (static/app.js + static/style.css).

12.3: throttled window resize calls map.invalidateSize().
13.1: validation coverage verified by tests/test_form_controller_js.py
      (no new code; noted in the completion report).
13.2: errorHandler mirrors server-rendered .alert text into an error
      toast on load, shows a network banner with Retry on offline,
      clears it on online, and logs to console.error.
13.3: empty-state content fades in.
"""

import os

BASE = os.path.dirname(__file__)
JS_PATH = os.path.join(BASE, "..", "static", "app.js")
CSS_PATH = os.path.join(BASE, "..", "static", "style.css")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 12.3 resize throttle
# ---------------------------------------------------------------------------

def test_throttled_resize_invalidates_map():
    js = _js()
    assert "throttle" in js and "resize" in js, \
        "Window resize must be throttled"
    assert "invalidateSize" in js, "Resize must invalidate the map size"


# ---------------------------------------------------------------------------
# 13.2 error handler
# ---------------------------------------------------------------------------

def test_error_handler_exists():
    js = _js()
    assert "errorHandler" in js, "errorHandler module must exist"


def test_server_alert_mirrored_to_toast():
    js = _js()
    assert '.alert' in js or 'querySelectorAll(".alert")' in js, \
        "Server-rendered .alert blocks must be found on load"
    assert "toastManager.show" in js, \
        "Alert text must be mirrored into an error toast"


def test_offline_banner_with_retry():
    js = _js()
    assert "offline" in js and "online" in js, \
        "Connectivity changes must be observed"
    assert "location.reload" in js, "Retry must reload the page"


def test_errors_logged_to_console():
    js = _js()
    assert "console.error" in js, "Errors must be logged"


# ---------------------------------------------------------------------------
# 13.3 empty-state fade-in
# ---------------------------------------------------------------------------

def test_empty_state_fades_in():
    css = _css()
    assert ".empty-state" in css and "animation" in css, \
        "Empty-state content must fade in"
    assert ".directions-empty-state" in css and "animation" in css, \
        "Directions empty state must fade in"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
