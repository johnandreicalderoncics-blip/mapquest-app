"""Walking and biking routes show calories burned instead of fuel cost."""

import pytest
from bs4 import BeautifulSoup

from backend import formatting, services

HOUR = 3_600_000


# ---- format_calories ---------------------------------------------------------

def test_walk_one_hour_70kg():
    # MET 3.5 x 70 kg x 1 h = 245 kcal
    assert formatting.format_calories(HOUR, "walk", 70) == "245 kcal"


def test_bike_two_hours_80kg_uses_thousands_separator():
    # MET 7.5 x 80 kg x 2 h = 1,200 kcal
    assert formatting.format_calories(2 * HOUR, "bike", 80) == "1,200 kcal"


def test_heavier_person_burns_more():
    light = formatting.format_calories(HOUR, "walk", 50)
    heavy = formatting.format_calories(HOUR, "walk", 90)
    assert int(heavy.split()[0].replace(",", "")) > int(light.split()[0].replace(",", ""))


def test_car_has_no_calories():
    assert formatting.format_calories(HOUR, "car", 70) == "N/A"


@pytest.mark.parametrize("ms, kg", [(-1, 70), (HOUR, 0), ("x", 70), (None, 70)])
def test_bad_input_is_na(ms, kg):
    assert formatting.format_calories(ms, "walk", kg) == "N/A"


# ---- parse_weight ------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [("70", 70.0), (" 65.5 ", 65.5), ("80kg", 80.0)])
def test_parse_weight_accepts_numbers(raw, expected):
    assert formatting.parse_weight(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "heavy", "0", "-5", "1000"])
def test_parse_weight_falls_back_to_default(raw):
    assert formatting.parse_weight(raw) == formatting.DEFAULT_WEIGHT_KG


# ---- service and page --------------------------------------------------------

def _fake_api(monkeypatch):
    monkeypatch.setattr(services.api, "fetch_route", lambda *a, **k: {
        "ok": True, "from_name": "A", "to_name": "B",
        "data": {"paths": [{"distance": 5000, "time": HOUR,
                            "points": {"coordinates": []}, "instructions": []}]},
    })


def test_get_route_returns_calories_for_walk(monkeypatch):
    _fake_api(monkeypatch)
    result = services.get_route("k", "A", "B", "metric", "walk", 62.0, 70.0)
    assert result["calories"] == "245 kcal"
    assert result["is_car"] is False


def _post(client, monkeypatch, profile, **extra):
    monkeypatch.setattr(services, "resolve_key", lambda: "k")
    _fake_api(monkeypatch)
    data = {"origin": "A", "destination": "B", "profile": profile, **extra}
    return BeautifulSoup(client.post("/route", data=data).data.decode("utf-8"), "html.parser")


def test_walk_result_shows_calories_card(client, monkeypatch):
    soup = _post(client, monkeypatch, "walk", weight="70")
    card = soup.find("div", class_="metric-card--cost").get_text(" ", strip=True)
    assert "Calories burned (70 kg)" in card and "245 kcal" in card
    assert "Fuel cost" not in card


def test_car_result_still_shows_fuel_cost(client, monkeypatch):
    soup = _post(client, monkeypatch, "car")
    card = soup.find("div", class_="metric-card--cost").get_text(" ", strip=True)
    assert "Fuel cost" in card


def test_form_shows_weight_field_only_for_walk_and_bike(client, monkeypatch):
    soup = _post(client, monkeypatch, "bike", weight="70")
    assert not soup.find(attrs={"data-field": "weight"}).has_attr("hidden")
    assert soup.find(attrs={"data-field": "gas_price"}).has_attr("hidden")
    assert soup.find("input", id="weight")["value"] == "70"

    home = BeautifulSoup(client.get("/").data.decode("utf-8"), "html.parser")
    assert home.find(attrs={"data-field": "weight"}).has_attr("hidden")
