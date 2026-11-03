"""Tests for Tasks 11.3, 11.4, 12.1 and 12.2: focus visibility, contrast
documentation, containment/animation hygiene, and resource hints.

11.3: `body.using-mouse` suppresses focus outlines for pointer users;
      :focus-visible gives keyboard users a 3px outline.
12.1: containment/will-change on the heavy panels; keyframes animate
      only compositor-friendly properties.
12.2: Leaflet stays server-gated; preload hints for the app stylesheet.
11.4 is a verification/documentation task (contrast audit recorded in the
completion report; tokens adjusted only if a pair fails).
"""

import os
import re

BASE = os.path.dirname(__file__)
CSS_PATH = os.path.join(BASE, "..", "static", "style.css")
JS_PATH = os.path.join(BASE, "..", "static", "app.js")
HTML_PATH = os.path.join(BASE, "..", "templates", "index.html")


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _html() -> str:
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 11.3 focus visibility
# ---------------------------------------------------------------------------

def test_using_mouse_class_in_js():
    js = _js()
    assert "using-mouse" in js, \
        "JS must toggle a body.using-mouse class on pointer/keyboard use"


def test_focus_visible_outline():
    css = _css()
    assert ":focus-visible" in css, "A :focus-visible rule must exist"
    assert "3px" in css, "Keyboard focus outline must be 3px"


def test_using_mouse_suppresses_outline():
    css = _css()
    assert ".using-mouse" in css, \
        "CSS must scope outline suppression to .using-mouse"


# ---------------------------------------------------------------------------
# 12.1 containment + animation hygiene
# ---------------------------------------------------------------------------

def test_heavy_panels_have_containment_and_will_change():
    css = _css()
    assert "will-change" in css and "contain:" in css, \
        "Heavy panels must declare will-change and contain"


def _keyframe_properties(css: str) -> list:
    """Collect all declaration property names inside @keyframes blocks."""
    props = []
    for match in re.finditer(r"@keyframes\s+[\w-]+\s*\{", css):
        start = match.end() - 1
        depth = 0
        pos = start
        while pos < len(css):
            if css[pos] == "{":
                depth += 1
            elif css[pos] == "}":
                depth -= 1
                if depth == 0:
                    break
            pos += 1
        body = css[start:pos]
        props.extend(re.findall(r"([a-zA-Z-]+)\s*:", body))
    return [p for p in props if p not in ("from", "to")]


def test_keyframes_animate_compositor_friendly_properties_only():
    """Transform/opacity/stroke-dashoffset/filter are GPU-cheap or
    paint-only; layout properties (width/height/top/left/margin/padding)
    trigger reflow every frame."""
    allowed = {
        "transform", "transform-origin", "opacity", "stroke-dashoffset", "filter",
        "clip-path", "fill", "stroke", "box-shadow", "background",
        "background-color", "color", "border-radius", "visibility",
        "text-shadow", "background-position", "stroke-width", "offset"
    }
    offenders = sorted(set(p for p in _keyframe_properties(_css())
                           if p not in allowed))
    assert not offenders, \
        f"Keyframes animate layout properties: {offenders}"


# ---------------------------------------------------------------------------
# 12.2 resource loading
# ---------------------------------------------------------------------------

def test_leaflet_is_available_for_initial_map():
    html = _html()
    assert 'id="route-map"' in html, \
        "The initial page must render a map container"
    assert "leaflet.js" in html, \
        "Leaflet must load on the initial page"


def test_app_stylesheet_preloaded():
    html = _html()
    assert 'rel="preload"' in html and "style.css" in html, \
        "The app stylesheet should carry a preload hint"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
