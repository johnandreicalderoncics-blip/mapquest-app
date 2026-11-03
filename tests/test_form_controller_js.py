"""Tests for Tasks 5.4, 6.1-6.3: layout transitions/containment and the
form controller (static/app.js + static/style.css).

6.1 Real-time validation with debounced feedback, aria-invalid, shake.
6.2 Segmented control aria-checked sync on change.
6.3 Clear buttons shown/hidden on input and on load; click clears + focuses.
5.4 Containment on .map-container/.toast and 300ms sidebar transitions.
"""

import os

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _rule_block(css: str, selector: str) -> str:
    """Return the declaration block for the first top-level rule matching
    `selector {` (skips matches inside @media blocks)."""
    depth = 0
    idx = 0
    needle = f"{selector} {{"
    while True:
        idx = css.find(needle, idx)
        if idx == -1:
            return ""
        # Only accept when we are not inside another block.
        if css.rfind("}", 0, idx) == -1 or \
           css[:idx].count("{") == css[:idx].count("}"):
            start = idx + len(needle)
            d = 1
            pos = start
            while pos < len(css) and d > 0:
                if css[pos] == "{":
                    d += 1
                elif css[pos] == "}":
                    d -= 1
                pos += 1
            return css[start:pos - 1]
        idx += len(needle)


# ---------------------------------------------------------------------------
# 6.1 validation
# ---------------------------------------------------------------------------

def test_validate_form_and_field_exist():
    js = _js()
    assert "validateForm" in js, "formController.validateForm must exist"
    assert "validateField" in js, "formController.validateField must exist"


def test_field_error_helpers_exist():
    js = _js()
    assert "showFieldError" in js, "formController.showFieldError must exist"
    assert "clearFieldError" in js, "formController.clearFieldError must exist"


def test_validation_sets_aria_invalid():
    js = _js()
    assert "aria-invalid" in js.lower() or "setAttribute(\"aria-invalid\"" in js, \
        "Validation must toggle aria-invalid on the input"


def test_validation_uses_error_state_class():
    js = _js()
    assert "form-field--error" in js, \
        "Validation must toggle the .form-field--error class (CSS shake/border)"


def test_validation_is_debounced_realtime():
    """Requirement 6.1: validate on input after a 300ms debounce."""
    js = _js()
    assert "debounce" in js and "input" in js, \
        "Validation must run on input events"
    assert "300" in js, "Validation debounce must be 300ms"


def test_validation_trims_whitespace():
    js = _js()
    assert ".trim()" in js, "Validation must trim whitespace before checking"


# ---------------------------------------------------------------------------
# 6.2 segmented control aria sync
# ---------------------------------------------------------------------------

def test_segmented_control_aria_sync():
    js = _js()
    assert "segmented-control__input" in js, \
        "Segmented radios must be selected by class"
    assert "aria-checked" in js, \
        "Radio change must sync aria-checked"
    assert "data-selected-index" in js, \
        "Radio change must expose the selected index for slider alignment"


# ---------------------------------------------------------------------------
# 6.3 clear buttons
# ---------------------------------------------------------------------------

def test_clear_buttons_wired():
    js = _js()
    assert "form-field__clear" in js, \
        "Clear buttons must be selected by class"


def test_clear_buttons_shown_on_input_and_load():
    """The hidden attribute must be managed in JS on input events and at
    init (server pre-fills values but buttons start hidden)."""
    js = _js()
    assert "removeAttribute(\"hidden\")" in js or \
           "hidden = false" in js or \
           ".hidden = false" in js, \
        "Clear button must be revealed by removing the hidden attribute"
    # both an input listener path and an initial sync path exist
    assert js.count("syncClearButton") >= 2 or \
           ("syncClearButtons" in js), \
        "Clear-button visibility must be synced on input and on load"


def test_clear_click_clears_and_focuses():
    js = _js()
    assert "input.focus()" in js, \
        "Clear click must return focus to the input"


# ---------------------------------------------------------------------------
# 5.4 containment + transitions
# ---------------------------------------------------------------------------

def test_map_container_has_containment():
    block = _rule_block(_css(), ".map-container")
    assert "contain:" in block, ".map-container must declare contain"


def test_toast_has_containment():
    block = _rule_block(_css(), ".toast")
    assert "contain:" in block, ".toast must declare contain"


def test_form_sidebar_has_layout_transitions():
    block = _rule_block(_css(), ".form-sidebar")
    assert "transition" in block and "300ms" in block, \
        "Sidebar layout properties must transition over 300ms"


def test_field_adornments_have_separate_reserved_space():
    css = _css()
    assert "right: 44px" in css, \
        "The validation checkmark must sit beside, not under, the clear button"
    assert "padding-right: 72px" in css, \
        "Inputs must reserve space for both validation and clear controls"


def test_mobile_sidebar_collapse_is_wired():
    js = _js()
    assert "sidebarController" in js
    assert "form-sidebar--collapsed" in js
    assert 'aria-expanded' in js


def test_mobile_idle_sidebar_and_summary_toggle_are_wired():
    js = _js()
    assert "form-sidebar--idle" in js
    assert "tripSummaryController" in js
    assert "tripSummaryToggle" in js


def test_information_holders_collapse_on_desktop():
    css = _css()
    assert "@media (min-width: 768px)" in css
    assert ".form-sidebar--collapsed" in css
    assert "max-width: 56px" in css
    assert ".trip-summary-card--collapsed .trip-summary-card__content" in css
    assert "display: inline-flex" in css


def test_collapsed_desktop_sidebar_keeps_reveal_button_inside_rail():
    css = _css()
    assert ".form-sidebar--collapsed .form-sidebar__title" in css
    assert "display: none" in css
    assert ".form-sidebar--collapsed .form-sidebar__header" in css
    assert "width: 40px" in css


def test_mobile_header_keeps_theme_toggle_visible():
    css = _css()
    assert ".form-sidebar__header .theme-toggle" in css
    assert 'display: flex' in css
    assert "--font-family-display" in css


def test_input_adornments_share_vertical_centering():
    css = _css()
    assert ".form-field__clear" in css
    assert ".form-field--valid .form-field__input-wrapper::after" in css
    assert "top: 50%;" in css
    assert "transform: translateY(-50%)" in css


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
