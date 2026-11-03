"""Tests for Tasks 10.2 and 10.3: theme toggle UI and theme polish.

10.2: a toggle button with sun/moon icons and aria-pressed lives in the
      sidebar header before the collapse button; JS wires click +
      aria-pressed; CSS styles it and swaps the icons per theme.
10.3: theme switches run behind a 300ms cross-fade (.theme-transitioning),
      dark map tiles keep the filter hook from Task 3.2, and changes are
      announced through an sr-only live region.
"""

import os

BASE = os.path.dirname(__file__)
HTML_PATH = os.path.join(BASE, "..", "templates", "index.html")
CSS_PATH = os.path.join(BASE, "..", "static", "style.css")
JS_PATH = os.path.join(BASE, "..", "static", "app.js")


def _html() -> str:
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 10.2 toggle markup
# ---------------------------------------------------------------------------

def test_theme_toggle_button_exists_in_sidebar_header():
    html = _html()
    header_idx = html.find("form-sidebar__header")
    toggle_idx = html.find('id="themeToggle"')
    collapse_idx = html.find('id="collapseBtn"')
    assert header_idx != -1 and toggle_idx != -1, \
        "A #themeToggle button must exist in the sidebar header"
    assert header_idx < toggle_idx < collapse_idx, \
        "The toggle must sit before the collapse button in the header"


def test_theme_toggle_has_sun_moon_icons_and_aria_pressed():
    html = _html()
    toggle_idx = html.find('id="themeToggle"')
    end_idx = html.find("</button>", toggle_idx)
    toggle = html[toggle_idx:end_idx]
    assert "aria-pressed" in toggle, "Toggle must carry aria-pressed"
    assert "theme-toggle__icon--sun" in toggle and \
           "theme-toggle__icon--moon" in toggle, \
        "Toggle must contain sun and moon icon variants"


# ---------------------------------------------------------------------------
# 10.2 toggle CSS
# ---------------------------------------------------------------------------

def test_theme_toggle_styled():
    css = _css()
    assert ".theme-toggle" in css, "Theme toggle must be styled"
    assert ".theme-toggle__icon--sun" in css and \
           ".theme-toggle__icon--moon" in css, \
        "Sun/moon visibility must swap per theme in CSS"


# ---------------------------------------------------------------------------
# 10.2 toggle JS
# ---------------------------------------------------------------------------

def test_theme_toggle_wired_in_js():
    js = _js()
    assert "themeToggle" in js, "JS must wire the toggle button"
    assert "aria-pressed" in js, "Click must sync aria-pressed"


def test_theme_toggle_click_toggles_theme():
    js = _js()
    assert "toggleTheme" in js or "setTheme" in js, \
        "Click must call the theme manager to switch themes"


def test_theme_toggle_has_interaction_animation():
    js = _js()
    css = _css()
    assert "theme-toggle--changing" in js
    assert ".theme-toggle--changing .theme-toggle__icon" in css
    assert "@keyframes themeIconSwap" in css


def test_theme_and_animation_apis_have_compatibility_fallbacks():
    js = _js()
    assert "addListener" in js
    assert "requestFrame" in js
    assert "getMediaQuery" in js


# ---------------------------------------------------------------------------
# 10.3 cross-fade, tiles, announcements
# ---------------------------------------------------------------------------

def test_theme_switch_cross_fade():
    js = _js()
    assert "theme-transitioning" in js, \
        "Theme switch must add a .theme-transitioning class temporarily"


def test_dark_tile_filter_hook_present():
    css = _css()
    assert "leaflet-tile-pane" in css and "filter" in css, \
        "Dark-theme tile filter hook must exist"


def test_sr_only_utility_and_live_region():
    css = _css()
    html = _html()
    assert ".sr-only" in css, "An .sr-only utility class must exist"
    assert "sr-announcements" in html, \
        "A #sr-announcements live region must exist in the page"


def test_theme_change_announced_to_screen_readers():
    js = _js()
    assert "announce" in js.lower(), \
        "Theme changes must be announced via the live region"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
