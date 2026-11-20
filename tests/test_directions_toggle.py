"""Turn-by-turn directions live in a toggleable panel over the map."""

import os

import pytest
from bs4 import BeautifulSoup

from tests.test_results_panel_styles import FAKE_RESULT

APP_JS = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")


@pytest.fixture()
def route_soup(client, monkeypatch):
    monkeypatch.setattr("backend.services.resolve_key", lambda: "test-key")
    monkeypatch.setattr("backend.services.get_route", lambda *a, **k: dict(FAKE_RESULT))
    page = client.post("/route", data={"origin": "Manila", "destination": "Quezon City"})
    return BeautifulSoup(page.data.decode("utf-8"), "html.parser")


def test_toggle_button_is_in_map_controls(route_soup):
    controls = route_soup.find("div", class_="map-controls--actions")
    button = controls.find("button", id="directionsToggleBtn")
    assert button is not None
    assert button["aria-controls"] == "directionsPanel"
    assert button["aria-expanded"] == "false"


def test_badge_shows_step_count(route_soup):
    badge = route_soup.find("span", class_="map-control-btn__badge")
    assert badge.get_text(strip=True) == str(len(FAKE_RESULT["steps"]))


def test_panel_starts_hidden_inside_map(route_soup):
    panel = route_soup.find(id="directionsPanel")
    assert panel is not None
    assert panel.has_attr("hidden")
    assert panel.find_parent(id="mapContainer") is not None


def test_steps_are_no_longer_in_results_panel(route_soup):
    results = route_soup.find(id="resultsPanel")
    assert results.find("li", class_="direction-step") is None
    assert len(route_soup.find(id="directionsPanel").find_all("li", class_="direction-step")) == 3


def test_panel_has_close_button(route_soup):
    close = route_soup.find(id="directionsCloseBtn")
    assert close is not None and close.get("aria-label")


def test_no_toggle_without_a_route(client):
    soup = BeautifulSoup(client.get("/").data.decode("utf-8"), "html.parser")
    assert soup.find(id="directionsToggleBtn") is None
    assert soup.find(id="directionsPanel") is None


def test_js_wires_toggle_and_escape():
    js = open(APP_JS, encoding="utf-8").read()
    assert "directionsController.initialize();" in js
    assert 'getElementById("directionsToggleBtn")' in js
    assert '"aria-expanded"' in js and 'event.key === "Escape"' in js
