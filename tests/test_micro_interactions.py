"""Tests for Tasks 14.1 and 14.2: success feedback and micro-animations.

14.1: a success toast ("Route found: X to Y") fires on load when a route
      exists; blur-validate marks fields .form-field--valid with a
      checkmark; the summary card enters with an elastic bounce.
14.2: submit-button ripple (done in 6.4, locked by test_loading_states_js)
      and step-number parallax on hover.
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


def _rule_block(css: str, selector: str) -> str:
    idx = css.find(f"{selector} {{")
    if idx == -1:
        return ""
    start = idx + len(selector) + 2
    depth = 1
    pos = start
    while pos < len(css) and depth > 0:
        if css[pos] == "{":
            depth += 1
        elif css[pos] == "}":
            depth -= 1
        pos += 1
    return css[start:pos - 1]


# ---------------------------------------------------------------------------
# 14.1 success feedback
# ---------------------------------------------------------------------------

def test_success_toast_on_route_load():
    js = _js()
    assert "showSuccessToast" in js or ("Route found" in js), \
        "A success toast must fire on load when a route exists"
    assert "endpoint__name" in js, \
        "Toast copy must come from the rendered endpoint names"


def test_valid_field_checkmark():
    js = _js()
    assert "form-field--valid" in js, \
        "Blur-validate must mark valid fields"
    css = _css()
    valid = _rule_block(css, ".form-field--valid .form-field__input-wrapper::after")
    assert valid, "A checkmark ::after must be styled for valid fields"


def test_summary_card_elastic_entry():
    css = _css()
    block = _rule_block(css, ".trip-summary-card")
    assert "summaryCardEntry" in block or "elasticBounce" in block, \
        "Summary card must enter with an elastic bounce"
    assert "@keyframes summaryCardEntry" in css, \
        "The combined entry keyframe must exist"


# ---------------------------------------------------------------------------
# 14.2 micro-animations
# ---------------------------------------------------------------------------

def test_step_number_parallax_on_hover():
    css = _css()
    idx = css.find(".direction-step:hover .direction-step__number {")
    assert idx != -1, "Step number must respond to step hover"
    block = css[idx:css.find("}", idx)]
    assert "translate" in block, "Hover must include a parallax translate"


def test_submit_ripple_still_wired():
    js = _js()
    assert "pointerdown" in js and "createRipple" in js, \
        "Submit ripple (6.4) must remain wired"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
