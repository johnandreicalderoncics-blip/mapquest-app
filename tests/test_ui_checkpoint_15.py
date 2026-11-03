"""Task 15 checkpoint: end-to-end UI verification before polish.

Renders the real pages through the Flask test client and asserts the
overhauled UI structure, plus final app.js hygiene checks.
"""

import os

import pytest
from bs4 import BeautifulSoup

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")


def _js() -> str:
    with open(JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture()
def client(app):
    app.config["TESTING"] = True
    return app.test_client()


FAKE_RESULT = {
    "ok": True,
    "distance": "12.5 km",
    "duration": "25 mins",
    "fuel": "1.1 L",
    "route_points": [
        [14.5995, 120.9842],
        [14.6042, 120.9822],
        [14.6091, 120.9800],
    ],
    "from_name": "Manila",
    "to_name": "Quezon City",
    "profile_label": "Car",
    "steps": [
        {"number": 1, "text": "Head north", "distance": "0.5 km"},
        {"number": 2, "text": "Turn right", "distance": "12.0 km"},
    ],
}


def test_home_page_ui_structure(client):
    response = client.get("/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    # Core form IDs
    assert soup.find(id="routeForm"), "routeForm must exist"
    assert soup.find(id="submitBtn"), "submitBtn must exist"
    assert soup.find(id="origin"), "origin input must exist"
    assert soup.find(id="destination"), "destination input must exist"

    # Overhaul additions
    assert soup.find(id="themeToggle"), "theme toggle must exist"
    assert soup.find(id="main-content"), "#main-content must exist"
    assert soup.find(id="sr-announcements"), "live region must exist"
    assert soup.find(id="toast-container"), "toast container must exist"
    assert soup.select(".skip-link"), "skip link must exist"

    # Form carries the novalidate + post target
    form = soup.find(id="routeForm")
    assert form.get("method") == "post"
    assert form.get("action") == "/route"


def test_route_result_page_structure(client, monkeypatch):
    monkeypatch.setattr("backend.services.resolve_key", lambda *a, **k: "fake-key")
    monkeypatch.setattr("backend.services.get_route",
                        lambda *a, **k: dict(FAKE_RESULT))

    response = client.post("/route", data={
        "origin": "Manila",
        "destination": "Quezon City",
        "units": "metric",
        "profile": "car",
    })
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    assert soup.find(id="resultsPanel"), "results panel must render"
    assert soup.select(".trip-summary-card"), "trip summary card must render"
    assert soup.select(".metric-card"), "metric cards must render"
    assert soup.select(".direction-step"), "direction steps must render"
    assert soup.select(".endpoint"), "endpoints must render"
    assert soup.find(id="route-map"), "map container must render"

    # Route points are inlined for the map controller
    assert "window.routePoints" in response.get_data(as_text=True)


def test_app_js_hygiene():
    js = _js()
    assert "route-form" not in js, "dead #route-form ID must stay gone"
    assert "find-button" not in js, "dead #find-button ID must stay gone"
    assert "results-panel--visible" in js, "results reveal must be wired"
    assert "toastManager" in js, "toast manager must exist"
    assert "themeManager" in js, "theme manager must exist"
    assert "accessibilityController" in js, "a11y controller must exist"
    assert "errorHandler" in js, "error handler must exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
