"""Tests for app.py's Flask routes (via test_client, mocked GraphHopper).

Every test runs without network access and without a real API key.
"""

import re
from pathlib import Path
from unittest import mock

import pytest

from backend import api as backend_api
from backend import config
from tests.helpers import make_failure_result, make_success_result


@pytest.fixture()
def no_config_file(monkeypatch):
    """Point config at a missing file so the app has no key."""
    monkeypatch.setattr(config, "CONFIG_FILE", Path("definitely-missing.ini"))
    return None


@pytest.fixture()
def env_key(monkeypatch):
    """Provide a key through the environment (highest precedence)."""
    monkeypatch.setenv("GRAPHOPPER_KEY", "SECRETKEY123")
    return "SECRETKEY123"


class TestIndexPage:
    def test_get_index_renders_the_form(self, client):
        response = client.get("/")
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'action="/route"' in body
        assert 'name="origin"' in body
        assert 'name="destination"' in body
        assert 'name="units"' in body
        assert 'name="profile"' in body

    def test_index_without_key_shows_setup_banner(self, client,
                                                  no_config_file):
        body = client.get("/").get_data(as_text=True)
        assert "No GraphHopper API key found" in body
        assert "GRAPHOPPER_KEY" in body  # setup instructions mention it

    def test_index_with_key_hides_setup_banner(self, client, env_key):
        body = client.get("/").get_data(as_text=True)
        assert "No GraphHopper API key found" not in body


class TestRoutePost:
    def test_empty_fields_show_error_without_calling_api(self, client):
        with mock.patch.object(backend_api, "fetch_route") as mocked:
            response = client.post("/route", data={
                "origin": "", "destination": "",
                "units": "metric", "profile": "car"})
        mocked.assert_not_called()
        body = response.get_data(as_text=True)
        assert "Please enter a starting location." in body

    def test_success_renders_trip_summary_and_refills_form(self, client,
                                                           env_key):
        with mock.patch.object(backend_api, "fetch_route",
                               return_value=make_success_result()):
            response = client.post("/route", data={
                "origin": "Quezon City",
                "destination": "Makati",
                "units": "metric", "profile": "car"})
        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Quezon City, Metro Manila, PH" in body
        assert "Makati, Metro Manila, PH" in body
        assert "00:27:41" in body
        assert "15.83 km" in body
        assert "Turn left onto Main Street" in body
        # The form keeps what the user typed.
        assert 'value="Quezon City"' in body

    def test_posted_units_stay_selected(self, client, env_key):
        with mock.patch.object(backend_api, "fetch_route",
                               return_value=make_success_result()):
            body = client.post("/route", data={
                "origin": "A", "destination": "B",
                "units": "metric", "profile": "bike"}
            ).get_data(as_text=True)
        # The metric/bike radios come back checked (the checked
        # attribute may render on the tag's following line).
        assert re.search(r'name="units" value="metric"\s+checked', body)
        assert re.search(r'name="profile" value="bike"\s+checked', body)
        assert not re.search(r'name="units" value="imperial"\s+checked',
                             body)

    def test_graphhopper_failure_shows_title_and_detail(self, client,
                                                        env_key):
        with mock.patch.object(backend_api, "fetch_route",
                               return_value=make_failure_result()):
            body = client.post("/route", data={
                "origin": "Nowhere", "destination": "Elsewhere",
                "units": "metric", "profile": "car"}
            ).get_data(as_text=True)
        assert "Location not found: Nowhere" in body
        assert "GraphHopper could not match that place." in body
        assert "Traceback" not in body

    def test_missing_key_shows_setup_banner_and_skips_api(self, client,
                                                          no_config_file):
        with mock.patch.object(backend_api, "fetch_route") as mocked:
            body = client.post("/route", data={
                "origin": "A", "destination": "B",
                "units": "metric", "profile": "car"}
            ).get_data(as_text=True)
        mocked.assert_not_called()
        assert "No GraphHopper API key found" in body

    def test_tampered_units_fall_back_to_default(self, client, env_key):
        # An invalid units value must not cause a 500 or reach the API
        # as-is; app.py normalizes it to the default.
        with mock.patch.object(backend_api, "fetch_route",
                               return_value=make_success_result()) as mocked:
            client.post("/route", data={
                "origin": "A", "destination": "B",
                "units": "leagues", "profile": "car"})
        assert mocked.call_args.args[3] == "imperial"


class TestKeyLeakGuard:
    def test_response_never_contains_key_or_key_param(self, client,
                                                      env_key):
        # Even when the mocked API result embeds the key in its url
        # field (as the real one does), no page may leak it.
        success = make_success_result()
        success["url"] = ("https://graphhopper.com/api/1/route?"
                          "key=SECRETKEY123&point=1,2")
        with mock.patch.object(backend_api, "fetch_route",
                               return_value=success):
            response = client.post("/route", data={
                "origin": "A", "destination": "B",
                "units": "metric", "profile": "car"})
        body = response.get_data(as_text=True)
        assert "SECRETKEY123" not in body
        assert "key=" not in body


class TestNotFound:
    def test_unknown_url_is_friendly(self, client):
        response = client.get("/definitely-not-a-page")
        body = response.get_data(as_text=True)
        assert response.status_code == 404
        assert "Page not found." in body
        assert "Traceback" not in body
