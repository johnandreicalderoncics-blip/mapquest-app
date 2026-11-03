"""Tests for Tasks 7.2, 7.4 and 8.1: route display animation, loading
overlay message cycling, and the results controller (static/app.js).

7.2: polyline drawn with a stroke-dasharray animation honoring
     prefers-reduced-motion.
7.4: #mapLoadingText cycles messages every 2s until the map is ready
     (300ms minimum display retained).
8.1: resultsController.show() reveals the panel (--visible) and resets
     its scroll position.
"""

import os

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "templates", "index.html")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_loading_overlay_hidden_attribute_hides_overlay():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()
    assert ".map-loading-overlay[hidden]" in css
    assert "display: none !important" in css


def test_initial_page_renders_map_without_route():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    assert 'id="route-map"' in template
    assert 'window.routePoints = ' in template
    assert 'else %}[]{% endif %}' in template


def test_map_initializes_default_view_without_route():
    js = _js()
    assert "CONFIG.defaultView.center" in js
    assert "state.map.setView" in js
    assert "var hasRoute" in js


# ---------------------------------------------------------------------------
# 7.2 polyline animation
# ---------------------------------------------------------------------------

def test_animate_polyline_exists():
    js = _js()
    assert "animatePolyline" in js, "mapController.animatePolyline must exist"


def test_animate_polyline_uses_dash_technique():
    js = _js()
    assert "stroke-dasharray" in js or "strokeDasharray" in js, \
        "Polyline animation must set stroke-dasharray"
    assert "stroke-dashoffset" in js or "strokeDashoffset" in js, \
        "Polyline animation must animate stroke-dashoffset"


def test_animate_polyline_honors_reduced_motion():
    js = _js()
    assert "shouldAnimate" in js, \
        "Polyline animation must be skipped under prefers-reduced-motion"


def test_polyline_animation_uses_draw_polyline_keyframe():
    """The CSS drawPolyline keyframe exists (Task 4.1); JS must reference
    the animation class or apply the keyframe."""
    js = _js()
    assert "drawPolyline" in js or "polyline-animating" in js, \
        "JS must apply the drawPolyline animation to the path"


# ---------------------------------------------------------------------------
# 7.4 loading overlay messages
# ---------------------------------------------------------------------------

def test_loading_text_cycles_messages():
    js = _js()
    assert "mapLoadingText" in js, "Overlay text element must be targeted"
    assert "setInterval" in js, "Messages must cycle on an interval"
    assert "clearInterval" in js, "Cycling must stop when the map is ready"


def test_loading_interval_is_two_seconds():
    js = _js()
    assert "2000" in js, "Message cycle interval must be 2000ms"


# ---------------------------------------------------------------------------
# 8.1 results controller
# ---------------------------------------------------------------------------

def test_results_controller_exists():
    js = _js()
    assert "resultsController" in js, "resultsController must be defined"
    assert "results-panel--visible" in js, \
        "Reveal must add the .results-panel--visible class"


def test_results_controller_resets_scroll():
    js = _js()
    assert "scrollTop" in js, "Panel scroll position must reset on show"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
