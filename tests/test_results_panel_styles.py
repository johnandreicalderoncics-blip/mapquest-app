"""
Tests for Wave 2: Tasks 3.2 (Map Component Styling) and 3.3 (Results Panel Styling)

Task 3.2 (Requirements 1.5, 7.1, 7.7):
- Mobile touch targets >= 44x44px for map control buttons
- Dark-theme tile filter hook for theme-aware map styling

Task 3.3 (Requirements 2.3, 5.1, 5.2, 5.5, 5.6, 17.3, 17.4, 17.7):
- Results panel styles target the template's real class names
  (.trip-summary-card, .endpoint*, .metric-card*, .direction-step*, .empty-state*)
- Gradient trip summary card, color-coded metrics grid, timeline connector,
  staggered direction steps, empty-state styling, reduced-motion overrides
"""

import os

import pytest
from bs4 import BeautifulSoup

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "style.css")


def _css() -> str:
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _rule_block(css: str, selector: str) -> str:
    """Return the declaration block for the first rule matching `selector {`."""
    for variant in (f"{selector} {{", f"{selector}{{"):
        idx = css.find(variant)
        if idx != -1:
            start = idx + len(variant)
            depth = 1
            pos = start
            while pos < len(css) and depth > 0:
                if css[pos] == "{":
                    depth += 1
                elif css[pos] == "}":
                    depth -= 1
                pos += 1
            return css[start:pos - 1]
    return ""


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
# Task 3.2 — Map component styling gaps
# ---------------------------------------------------------------------------

def test_map_control_touch_targets_mobile():
    """Requirement 3.6: map control buttons must be >= 44x44px on mobile."""
    css = _css()
    mobile = _media_blocks(css, "(max-width: 767px)")
    assert mobile, "Expected a max-width: 767px media query"
    found = any(".map-control-btn" in b and "width: 44px" in b and "height: 44px" in b
                for b in mobile)
    assert found, "Mobile media query should size .map-control-btn to 44x44px"


def test_dark_theme_tile_filter_hooks():
    """Requirement 12.4 hook: dark tile filter for both dark-theme mechanisms."""
    css = _css()
    # data-theme attribute override (used by the Task 10.3 theme manager)
    assert "[data-theme=\"dark\"] .map-canvas .leaflet-tile-pane" in css, \
        "Dark theme tile filter must support [data-theme=dark]"
    # prefers-color-scheme media query (no-JS dark mode)
    dark_media = _media_blocks(css, "(prefers-color-scheme: dark)")
    assert any(".map-canvas .leaflet-tile-pane" in b for b in dark_media), \
        "Dark media query must include the tile-pane filter"


# ---------------------------------------------------------------------------
# Task 3.3 — Results panel styles target the template's real class names
# ---------------------------------------------------------------------------

def test_trip_summary_card_gradient():
    """Requirement 17.7: trip summary card has a gradient background and entry animation."""
    block = _rule_block(_css(), ".trip-summary-card")
    assert block, ".trip-summary-card must be styled"
    assert "linear-gradient" in block, "Trip summary card should have a gradient background"
    assert "summaryCardEntry" in block, "Trip summary card should animate in with the elastic entry (Task 14.1 superseded the original slideInUp)"


def test_legacy_orphan_selectors_removed():
    """Section 12 selectors must be re-pointed to template names, not duplicated."""
    css = _css()
    for orphan in (".trip-summary {", ".trip-metrics {", ".trip-metric {",
                   ".step-badge {", ".step-content {", ".step-instruction {",
                   ".results-empty {", ".directions {", ".direction-steps {"):
        assert orphan not in css, f"Orphaned selector {orphan} should be re-pointed"


def test_route_endpoints_styled():
    """Requirements 17.5: endpoint rows, labels, names and connector are styled."""
    css = _css()
    assert _rule_block(css, ".endpoint"), ".endpoint row must be styled"
    assert _rule_block(css, ".endpoint__connector"), "Connector line must be styled"
    assert _rule_block(css, ".endpoint__label"), "Endpoint label must be styled"
    assert _rule_block(css, ".endpoint__name"), "Endpoint name must be styled"
    assert ".endpoint--origin .endpoint__icon" in css, "Origin icon must be color-coded"
    assert ".endpoint--destination .endpoint__icon" in css, "Destination icon must be color-coded"


def test_metrics_grid_and_cards():
    """Requirements 17.1, 17.2, 17.4: metrics grid with color-coded metric cards."""
    css = _css()
    grid = _rule_block(css, ".metrics-grid")
    assert grid and "display: grid" in grid, ".metrics-grid must be a grid"

    card = _rule_block(css, ".metric-card")
    assert card, ".metric-card must be styled"
    assert "transition" in card, "Metric card should transition on hover"
    hover = _rule_block(css, ".metric-card:hover")
    assert "transform" in hover, "Metric card should lift on hover"

    value = _rule_block(css, ".metric-card__value")
    assert "tabular-nums" in value, "Metric values should use tabular numerals"

    for variant in ("--distance", "--duration", "--fuel"):
        assert f".metric-card{variant} .metric-card__icon" in css, \
            f"Metric icon color variant {variant} must be styled"


def test_trip_summary_text_wraps_on_narrow_viewports():
    css = _css()
    endpoint = _rule_block(css, ".endpoint__name")
    assert "white-space: normal" in endpoint
    assert "overflow-wrap: anywhere" in endpoint
    assert "minmax(0, 1fr)" in css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in css


def test_trip_summary_metrics_remain_compact_and_readable():
    css = _css()
    value = _rule_block(css, ".metric-card__value")
    assert "font-size: var(--font-size-xl)" in value
    assert "white-space: normal" in value
    assert "overflow-wrap: anywhere" in value
    assert "font-size: clamp(0.9rem, 4vw, 1.1rem)" in css
    assert "overflow: visible" in css
    assert "container-type: inline-size" in css
    assert "@container (max-width: 92px)" in css
    mobile = _media_blocks(css, "(max-width: 767px)")
    assert any("grid-template-columns: repeat(3, minmax(0, 1fr))" in block
               and "flex-direction: column" in block for block in mobile)


def test_direction_steps_styled():
    """Requirements 5.1, 5.3, 5.5, 5.6: step badges, timeline, hover, stagger."""
    css = _css()

    number = _rule_block(css, ".direction-step__number")
    assert number and "36px" in number, "Step number badge must be 36px"
    assert ".direction-step:first-child .direction-step__number" in css, \
        "First step badge should use the origin marker color"
    assert ".direction-step:last-child .direction-step__number" in css, \
        "Last step badge should use the destination marker color"

    assert _rule_block(css, ".direction-step__timeline"), \
        "Per-step timeline connector must be styled (template provides __timeline elements)"

    hover = _rule_block(css, ".direction-step:hover")
    assert "translateX(4px)" in hover, "Step hover should translate right"

    distance = _rule_block(css, ".direction-step__distance")
    assert "tabular-nums" in distance, "Step distances should use tabular numerals"

    # 50ms stagger increments (Requirement 19.4)
    assert ".direction-step:nth-child(1)" in css, "Stagger delays must start at step 1"
    assert ".direction-step:nth-child(n+6)" in css, "Stagger must cap at step 6+"


def test_directions_section_styled():
    """Requirements 5.1, 17.1: directions section header and list container."""
    css = _css()
    assert _rule_block(css, ".directions-section"), ".directions-section must be styled"
    assert _rule_block(css, ".directions-section__title"), "Section title must be styled"
    assert _rule_block(css, ".directions-list"), ".directions-list must be styled"
    assert _rule_block(css, ".direction-step__instruction"), "Step instruction must be styled"
    assert _rule_block(css, ".direction-step__text"), "Step text must be styled"


def test_results_panel_scrollable():
    """The template has no __content wrapper, so the panel itself scrolls."""
    # The selector appears in several rules (base + responsive overrides,
    # including media queries earlier in the file); the scroll-container
    # requirement is met if any of them declares overflow-y: auto.
    css = _css()
    blocks = []
    needle = ".results-panel {"
    idx = css.find(needle)
    while idx != -1:
        start = idx + len(needle)
        depth = 1
        pos = start
        while pos < len(css) and depth > 0:
            if css[pos] == "{":
                depth += 1
            elif css[pos] == "}":
                depth -= 1
            pos += 1
        blocks.append(css[start:pos - 1])
        idx = css.find(needle, pos)
    assert any("overflow-y: auto" in b for b in blocks), \
        "Results panel must be its own scroll container"


def test_results_panel_empty_variant():
    """Requirements 20.1, 20.4: empty-state panel variant styled with fade/pulse."""
    css = _css()
    assert _rule_block(css, ".results-panel--empty"), \
        "Empty results panel variant must be styled"
    illustration = _rule_block(css, ".empty-state__illustration")
    assert "animation" in illustration and "pulse" in illustration, \
        "Empty-state illustration should pulse"
    assert _rule_block(css, ".empty-state__title"), "Empty-state title must be styled"
    assert _rule_block(css, ".empty-state__message"), "Empty-state message must be styled"


def test_directions_empty_state_styled():
    """The 'no instructions' fallback inside a rendered route is styled."""
    css = _css()
    assert _rule_block(css, ".directions-empty-state"), \
        "Directions empty state must be styled"


def test_results_panel_mobile_spacing():
    """Requirements 17.3, 5.7: compact metric grid and 44px step targets."""
    css = _css()
    mobile = _media_blocks(css, "(max-width: 767px)")
    assert any(".metrics-grid" in b and
               "repeat(3, minmax(0, 1fr))" in b for b in mobile), \
        "Mobile metrics grid should use three compact columns"
    assert any(".direction-step" in b and "min-height: 44px" in b for b in mobile), \
        "Mobile direction steps should meet the 44px touch target"


def test_map_controls_reserve_space_for_results_panel():
    css = _css()
    controls = _rule_block(css, ".map-controls")
    assert "--map-controls-right" in controls
    js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()
    assert "mapLayoutController" in js
    assert "getBoundingClientRect" in js
    assert "--map-controls-right" in js


def test_results_panel_reduced_motion():
    """Requirement 9.5: new component names must be covered by reduced-motion overrides."""
    css = _css()
    blocks = _media_blocks(css, "(prefers-reduced-motion: reduce)")
    assert any(".trip-summary-card" in b and "animation: none" in b for b in blocks), \
        "Reduced motion must disable the trip summary card animation"
    assert any(".metric-card" in b and "animation: none" in b for b in blocks), \
        "Reduced motion must disable metric card animations"


# ---------------------------------------------------------------------------
# Template contract (Task 2.3 markup) — regression guards
# ---------------------------------------------------------------------------

FAKE_RESULT = {
    "ok": True,
    "from_name": "Manila, PH",
    "to_name": "Quezon City, PH",
    "profile_label": "Car",
    "duration": "30 mins",
    "distance": "12.3 km",
    "fuel": "1.2 L",
    "steps": [
        {"number": 1, "text": "Head north on Rizal St", "distance": "1.2 km"},
        {"number": 2, "text": "Turn left onto Main Ave", "distance": "0.8 km"},
        {"number": 3, "text": "Arrive at destination", "distance": "0 m"},
    ],
    "route_points": [[14.5995, 120.9842], [14.6338, 121.0194], [14.6760, 121.0437]],
}


@pytest.fixture()
def result_page(client, monkeypatch):
    monkeypatch.setattr("backend.services.resolve_key", lambda: "test-key")
    monkeypatch.setattr("backend.services.get_route", lambda *a, **k: dict(FAKE_RESULT))
    return client.post("/route", data={"origin": "Manila", "destination": "Quezon City"})


def test_rendered_result_metrics_structure(result_page):
    """Rendered route page contains the metrics grid with 3 color-coded cards."""
    soup = BeautifulSoup(result_page.data.decode("utf-8"), "html.parser")
    grid = soup.find("div", class_="metrics-grid")
    assert grid is not None, "Rendered result must include a metrics grid"
    cards = grid.find_all("div", class_="metric-card")
    assert len(cards) == 3, "Metrics grid must render 3 metric cards"
    classes = {c for card in cards for c in card.get("class", [])}
    assert {"metric-card--distance", "metric-card--duration", "metric-card--fuel"} <= classes


def test_rendered_result_steps_structure(result_page):
    """Rendered route page contains direction steps with numbers and distances."""
    soup = BeautifulSoup(result_page.data.decode("utf-8"), "html.parser")
    steps = soup.find_all("li", class_="direction-step")
    assert len(steps) == 3, "Rendered result must include one li per step"
    assert steps[0].find("span", class_="direction-step__number") is not None
    assert steps[0].find("span", class_="direction-step__distance") is not None


def test_empty_panel_structure(client):
    """No-route page renders the empty results panel variant."""
    response = client.get("/")
    soup = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    panel = soup.find("aside", class_="results-panel--empty")
    assert panel is not None, "No-route page must render the empty panel variant"
    assert panel.find("h2", class_="empty-state__title") is not None
    assert panel.find("p", class_="empty-state__message") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
