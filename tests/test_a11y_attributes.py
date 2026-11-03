"""Tests for Tasks 11.1 and 11.2: ARIA attributes and keyboard access.

11.1: fullscreen button carries aria-pressed; a polite #sr-announcements
      region exists; described-by wiring stays intact.
11.2: Alt+O / Alt+D move focus to the origin/destination inputs, Escape
      hides the results panel and dismisses toasts, a skip link targets
      #main-content, and the mobile full-screen results panel traps focus.
"""

import os

BASE = os.path.dirname(__file__)
HTML_PATH = os.path.join(BASE, "..", "templates", "index.html")
JS_PATH = os.path.join(BASE, "..", "static", "app.js")


def _html() -> str:
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 11.1 ARIA
# ---------------------------------------------------------------------------

def test_fullscreen_button_has_aria_pressed():
    html = _html()
    btn_idx = html.find('id="fullscreenBtn"')
    end_idx = html.find("</button>", btn_idx)
    btn = html[btn_idx:end_idx]
    assert "aria-pressed" in btn, "Fullscreen toggle must carry aria-pressed"


def test_sr_announcements_region_has_role_status():
    html = _html()
    region_idx = html.find('id="sr-announcements"')
    assert region_idx != -1, "Live region must exist"
    region_idx2 = html.find('id="sr-announcements"')
    tag_start = html.rfind("<div", 0, region_idx2)
    tag_end = html.find(">", region_idx2)
    tag = html[tag_start:tag_end]
    assert 'role="status"' in tag, "Live region must be role=status"
    assert "aria-live" in tag, "Live region must declare aria-live"
    assert "sr-only" in tag, "Live region must be visually hidden"


def test_inputs_keep_aria_describedby():
    html = _html()
    assert 'aria-describedby="originHelp"' in html
    assert 'aria-describedby="destinationHelp"' in html


# ---------------------------------------------------------------------------
# 11.2 keyboard access
# ---------------------------------------------------------------------------

def test_alt_shortcuts_focus_fields():
    js = _js()
    assert "keydown" in js and "altKey" in js, \
        "Global keydown handler must check Alt for field shortcuts"
    assert "origin" in js and "destination" in js, \
        "Alt+O/Alt+D must target the origin/destination inputs"


def test_escape_hides_results_and_dismisses_toasts():
    js = _js()
    assert "Escape" in js, "Escape must be handled"
    assert "dismissAll" in js, "Escape must dismiss all toasts"
    assert "results-panel--visible" in js, \
        "Escape must hide the results panel via its visibility class"


def test_skip_link_and_main_content():
    html = _html()
    assert "skip-link" in html, "A skip link must exist"
    assert 'id="main-content"' in html, "Skip target #main-content must exist"
    assert 'href="#main-content"' in html, "Skip link must point at #main-content"


def test_results_panel_focus_trap():
    js = _js()
    assert "trapFocus" in js or "focusTrap" in js, \
        "The full-screen results overlay must trap focus"


def test_fullscreen_aria_pressed_synced_in_js():
    js = _js()
    assert "fullscreenBtn" in js and "aria-pressed" in js, \
        "Fullscreen changes must sync aria-pressed from JS"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
