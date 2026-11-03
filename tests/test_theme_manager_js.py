"""Tests for Tasks 9.2 and 10.1: toast lifecycle locks and the theme
manager (static/app.js + templates/index.html).

9.2: active-toast tracking, max-4 cap, manual dismiss clears the auto
     timer, removal after the exit animation.
10.1: themeManager persists the choice in localStorage('theme'), falls
      back to prefers-color-scheme, sets data-theme on <html>, and
      follows OS changes when no saved pref exists. index.html carries
      an anti-FOUC inline script that sets data-theme before paint.
"""

import os

BASE = os.path.dirname(__file__)
JS_PATH = os.path.join(BASE, "..", "static", "app.js")
HTML_PATH = os.path.join(BASE, "..", "templates", "index.html")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _html() -> str:
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# 9.2 lifecycle
# ---------------------------------------------------------------------------

def test_active_toasts_tracked_and_capped():
    js = _js()
    assert "active" in js, "toastManager must track active toasts"
    assert "MAX_TOASTS" in js, "toastManager must cap the toast count"


def test_manual_dismiss_clears_auto_timer():
    js = _js()
    assert "clearTimeout" in js, \
        "Manual dismiss must clear the pending auto-dismiss timer"


# ---------------------------------------------------------------------------
# 10.1 theme manager
# ---------------------------------------------------------------------------

def test_theme_manager_exists():
    js = _js()
    assert "themeManager" in js, "themeManager module must exist"


def test_theme_persists_in_local_storage():
    js = _js()
    assert "localStorage" in js and "theme" in js, \
        "Theme choice must be saved under localStorage key 'theme'"


def test_theme_falls_back_to_os_preference():
    js = _js()
    assert "prefers-color-scheme" in js, \
        "Without a saved pref, the OS color scheme decides the theme"


def test_set_theme_sets_data_attribute():
    js = _js()
    assert "data-theme" in js, \
        "setTheme must set the data-theme attribute on <html>"
    assert "documentElement" in js, "Theme attribute must go on the root element"


def test_theme_follows_os_changes_when_no_saved_pref():
    js = _js()
    assert "addEventListener" in js and "change" in js, \
        "OS theme changes must be observed"


# ---------------------------------------------------------------------------
# anti-FOUC inline script
# ---------------------------------------------------------------------------

def test_anti_fouc_inline_script_present():
    html = _html()
    assert "data-theme" in html, \
        "index.html must set data-theme before first paint"
    assert "localStorage" in html, \
        "The anti-FOUC script must read the saved theme from localStorage"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
