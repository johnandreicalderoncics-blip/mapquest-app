"""Tests for Tasks 5.1-5.3: Responsive Layout System (static/style.css).

5.1 Mobile (<=767px): form sidebar becomes a collapsible bottom sheet,
    full-viewport map, full-screen results overlay, 44px touch targets,
    16px inputs (iOS zoom prevention), landscape override.
5.2 Tablet (768-1023px): sidebar 40% width (min 320px).
5.3 Desktop (>=1024px): sidebar fixed 380px width.
"""

import os

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _media_blocks(css: str, query: str) -> list:
    """Return all @media <query> blocks (brace-balanced)."""
    blocks = []
    needle = f"@media {query}"
    idx = css.find(needle)
    while idx != -1:
        open_brace = css.find("{", idx)
        depth = 1
        pos = open_brace + 1
        while pos < len(css) and depth > 0:
            if css[pos] == "{":
                depth += 1
            elif css[pos] == "}":
                depth -= 1
            pos += 1
        blocks.append(css[open_brace + 1:pos - 1])
        idx = css.find(needle, pos)
    return blocks


# ---------------------------------------------------------------------------
# 5.1 Mobile (<=767px)
# ---------------------------------------------------------------------------

def test_mobile_form_sidebar_bottom_sheet():
    """Requirement 3.2: sidebar becomes a bottom sheet on mobile."""
    css = _css()
    mobile = _media_blocks(css, "(max-width: 767px)")
    sheet = [b for b in mobile if ".form-sidebar" in b and "bottom: 0" in b and "top: auto" in b]
    assert sheet, "Mobile media query must turn the form sidebar into a bottom sheet"
    block = sheet[0]
    assert "width: 100%" in block, "Bottom sheet must span the full width"
    assert "max-height: 70vh" in block, "Bottom sheet must cap at 70vh (Requirement 3.2)"
    assert "border-top-left-radius" in block or "border-radius" in block, \
        "Bottom sheet needs rounded top corners"


def test_mobile_sidebar_collapsed_state():
    """Requirement 3.2: collapsible bottom sheet has a collapsed state."""
    css = _css()
    assert ".form-sidebar--collapsed" in css, \
        "A collapsed-state class must exist for the bottom sheet"


def test_mobile_results_full_screen_overlay():
    """Requirement 3.8: results panel becomes a full-screen overlay on mobile."""
    css = _css()
    mobile = _media_blocks(css, "(max-width: 767px)")
    overlay = [b for b in mobile if ".results-panel" in b and "top: 0" in b]
    assert overlay, "Mobile media query must make the results panel a full-screen overlay"
    assert any("100vh" in b for b in overlay), \
        "Full-screen overlay must cover the viewport height"


def test_mobile_touch_targets_44px():
    """Requirement 3.6: interactive elements are at least 44x44px on mobile."""
    css = _css()
    mobile = _media_blocks(css, "(max-width: 767px)")
    joined = "\n".join(mobile)
    assert ".btn" in joined and "min-height: 44px" in joined, \
        "Buttons must meet the 44px touch target on mobile"
    assert ".form-field__input" in joined and "min-height: 44px" in joined, \
        "Form inputs must meet the 44px touch target on mobile"
    assert ".segmented-control__label" in joined, \
        "Segmented control labels must be sized for touch on mobile"


def test_mobile_input_font_16px():
    """Requirement 3.9: inputs stay at 16px on mobile to prevent iOS zoom."""
    css = _css()
    mobile = _media_blocks(css, "(max-width: 767px)")
    assert any(".form-field__input" in b and "font-size: 16px" in b for b in mobile), \
        "Mobile inputs must use 16px font size"


def test_mobile_landscape_override():
    """Requirement 3.10: landscape phones get a shorter bottom sheet."""
    css = _css()
    landscape = _media_blocks(css, "(max-width: 767px) and (orientation: landscape)")
    assert landscape, "A landscape media query must exist for mobile"
    assert any(".form-sidebar" in b for b in landscape), \
        "Landscape override must adjust the form sidebar"


# ---------------------------------------------------------------------------
# 5.2 Tablet (768-1023px)
# ---------------------------------------------------------------------------

def test_tablet_sidebar_40_percent():
    """Requirement 3.3: tablet sidebar is 40% width, minimum 320px."""
    css = _css()
    tablet = _media_blocks(css, "(min-width: 768px) and (max-width: 1023px)")
    block = [b for b in tablet if ".form-sidebar" in b and "max-width: 40%" in b]
    assert block, "Tablet media query must size the sidebar at 40% width"
    assert "min-width: 320px" in block[0], "Tablet sidebar must keep a 320px minimum"


# ---------------------------------------------------------------------------
# 5.3 Desktop (>=1024px)
# ---------------------------------------------------------------------------

def test_desktop_sidebar_380px():
    """Requirement 3.4: desktop sidebar is fixed at 380px."""
    css = _css()
    desktop = _media_blocks(css, "(min-width: 1024px)")
    block = [b for b in desktop if ".form-sidebar" in b]
    assert block, "Desktop media query must size the form sidebar"
    assert "380px" in block[0], "Desktop sidebar must be 380px wide"


def test_map_controls_tablet_desktop_sizing_kept():
    """The existing tablet/desktop control-button sizing must survive the
    responsive rewrite."""
    css = _css()
    tablet = _media_blocks(css, "(min-width: 768px) and (max-width: 1023px)")
    desktop = _media_blocks(css, "(min-width: 1024px)")
    assert any(".map-control-btn" in b for b in tablet), \
        "Tablet media query must keep map control sizing"
    assert any(".map-control-btn" in b for b in desktop), \
        "Desktop media query must keep map control sizing"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
