"""Tests for Task 4.2: Animation Controller Module (static/app.js).

The animation controller provides reduced-motion detection, the ripple
effect generator, a smooth-scroll utility and the post-render route
display orchestration (map -> polyline -> results), per Requirements
2.2, 2.3, 2.4, 8.2, 19.1, 19.2, 19.4.

Also guards the app.js reorganization: the dead submit-feedback IDs
(#route-form / #find-button) must never return.
"""

import os

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_dead_submit_ids_removed():
    """Bug fix: submit feedback targeted #route-form/#find-button; the real
    IDs are routeForm/submitBtn. The dead selectors must be gone."""
    js = _js()
    assert "route-form" not in js, "app.js still references the dead #route-form ID"
    assert "find-button" not in js, "app.js still references the dead #find-button ID"
    assert "routeForm" in js and "submitBtn" in js, \
        "app.js must reference the real form and submit button IDs"


def test_should_animate_respects_reduced_motion():
    """Requirement 9.5 / 2.2: shouldAnimate detects prefers-reduced-motion."""
    js = _js()
    assert "shouldAnimate" in js, "animations.shouldAnimate must exist"
    assert "prefers-reduced-motion" in js, \
        "shouldAnimate must check the prefers-reduced-motion media query"
    assert "matchMedia" in js, "Reduced-motion detection must use matchMedia"


def test_reduced_motion_change_listener():
    """shouldAnimate must stay correct if the user toggles the OS setting."""
    js = _js()
    assert "addEventListener" in js and "change" in js, \
        "The reduced-motion media query must be observed for changes"


def test_create_ripple_targets_btn_ripple():
    """Requirement 8.1: ripple generator drives the .btn__ripple element."""
    js = _js()
    assert "createRipple" in js, "animations.createRipple must exist"
    assert "btn__ripple" in js, "Ripple generator must target the .btn__ripple element"
    assert "btn__ripple--active" in js, \
        "Ripple generator must toggle the --active modifier that triggers the CSS animation"


def test_smooth_scroll_uses_request_animation_frame():
    """Requirement 19.2: smooth scroll utility with rAF easing."""
    js = _js()
    assert "smoothScroll" in js, "animations.smoothScroll must exist"
    assert "requestAnimationFrame" in js, "Smooth scroll must animate via requestAnimationFrame"
    assert "easeInOutCubic" in js, "Smooth scroll must use an easing function"


def test_orchestrate_route_display_exists():
    """Requirement 19.1: post-render orchestration (results follow the map)."""
    js = _js()
    assert "orchestrateRouteDisplay" in js, \
        "animations.orchestrateRouteDisplay must exist"


def test_utils_debounce_and_throttle_exist():
    """Utilities required by 6.1 (validation debounce) and 12.3."""
    js = _js()
    assert "debounce" in js, "utils.debounce must exist"
    assert "throttle" in js, "utils.throttle must exist"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
