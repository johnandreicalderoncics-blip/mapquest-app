"""Tests for Task 9.1: Toast Manager (static/app.js).

The manager renders toasts into the server-rendered #toast-container,
escapes dynamic content, shows an inline-SVG icon per type, supports
auto-dismiss and manual dismissal via the .toast--dismissing CSS class
(matched to style.css; design.md's toast--exiting name is stale).
"""

import os

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_toast_manager_exists():
    js = _js()
    assert "toastManager" in js, "toastManager module must exist"
    assert "toast-container" in js, "Toasts must render into #toast-container"


def test_toast_manager_show_api():
    js = _js()
    assert "show" in js and "success" in js and "error" in js and "info" in js, \
        "toastManager.show must support success/error/warning/info types"


def test_toast_manager_escapes_dynamic_content():
    js = _js()
    assert "escapeHTML" in js, "Dynamic toast content must be escaped"


def test_toast_manager_builds_close_button():
    js = _js()
    assert "toast__close" in js, "Each toast must include a close button"


def test_toast_manager_dismiss_uses_css_class():
    js = _js()
    assert "toast--dismissing" in js, \
        "Dismissal must add .toast--dismissing (matches style.css)"


def test_toast_manager_removes_after_exit_animation():
    js = _js()
    assert "removeChild" in js or "remove()" in js, \
        "Toast element must be removed from the DOM after the exit animation"


def test_toast_manager_role_status():
    js = _js()
    assert "role" in js and "status" in js, \
        "Toast elements must carry role=status for screen readers"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
