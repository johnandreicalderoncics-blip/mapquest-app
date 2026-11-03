"""Tests for Tasks 6.4 and 7.1: button loading states and the map
controller refactor (static/app.js).

6.4: submit validates first (invalid blocks submission), valid disables
     the button + inputs, shows spinner + "Searching...", and buttons
     get the ripple effect on pointerdown.
7.1: map init lives in mapController.initializeMap with displayRoute and
     attachControlListeners as separate steps; polyline color comes from
     the CSS primary token with a fallback.
"""

import os

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 6.4 loading states
# ---------------------------------------------------------------------------

def test_submit_validates_and_blocks_invalid():
    js = _js()
    assert "preventDefault" in js, \
        "Invalid submissions must be blocked with preventDefault"
    assert "validateForm" in js, \
        "Submit must run validateForm before showing loading state"


def test_valid_submit_shows_loading_state():
    js = _js()
    assert "btn--loading" in js, "Submit must add the .btn--loading class"
    assert "Searching..." in js, "Submit must show the Searching... label"
    assert ".disabled = loading" in js, "Submit must disable the button"


def test_inputs_remain_submittable_during_submit():
    js = _js()
    assert "setLoading" in js, "formController.setLoading must centralize the loading state"
    assert ".readOnly = loading" in js, \
        "Location fields must remain successful controls during native POST"


def test_ripple_on_pointerdown():
    js = _js()
    assert "createRipple" in js, "animations.createRipple must be referenced"
    assert "pointerdown" in js, "Ripple must trigger on pointerdown"


# ---------------------------------------------------------------------------
# 7.1 map controller structure
# ---------------------------------------------------------------------------

def test_map_controller_has_separate_phases():
    js = _js()
    assert "initializeMap" in js, "mapController.initializeMap must exist"
    assert "displayRoute" in js, "mapController.displayRoute must exist"
    assert "attachControlListeners" in js, \
        "mapController.attachControlListeners must exist"


def test_polyline_color_from_css_token():
    js = _js()
    assert "getComputedStyle" in js and "--color-primary" in js, \
        "Polyline color must be read from the CSS --color-primary token"
    assert "#1a73e8" in js, "A fallback color must exist for token read failure"


def test_map_init_guards_against_missing_leaflet():
    js = _js()
    assert "window.L" in js, "Map init must guard on window.L presence"
    assert "routePoints" in js, "Map init must guard on window.routePoints"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
