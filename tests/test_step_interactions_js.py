"""Tests for Task 8.2: Direction-step interactions (static/app.js).

Steps become keyboard-activatable (tabindex + role=button, Enter/Space)
and clicking one centers the map on an interpolated position along the
route polyline (window.routePoints holds vertices, not per-step points),
with an info toast for feedback. Task 8.3's stagger is CSS-only (locked
by test_results_panel_styles.py); no JS delay logic is required.
"""

import os

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_steps_get_keyboard_activatable_attributes():
    js = _js()
    assert "direction-step" in js, "Direction steps must be selected"
    assert "tabindex" in js, "Steps must receive tabindex=0"
    assert "role" in js and "button" in js, "Steps must get role=button"


def test_steps_handle_enter_and_space():
    js = _js()
    assert "keydown" in js, "Steps must listen for keydown"
    assert "Enter" in js and "\" \"" in js or "Space" in js or "' '" in js, \
        "Enter and Space must activate a step"


def test_step_click_centers_map_on_route():
    js = _js()
    assert "setView" in js, "Step activation must move the map view"
    assert "routePoints" in js, "Step position must interpolate along routePoints"


def test_step_click_shows_info_toast():
    js = _js()
    assert "toastManager.show" in js or "showStepToast" in js, \
        "Step activation must surface an info toast"


def test_step_activation_skipped_without_route():
    """Steps must not move the map when no route is on screen."""
    js = _js()
    assert "state.route" in js or "routePoints" in js, \
        "Step activation must guard on a live route"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
