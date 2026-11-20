"""Tests for the peso fuel-cost estimate, the ETA and the gas price input."""

from datetime import datetime

import pytest

from backend import formatting, services

LEAVE_AT = datetime(2026, 11, 20, 22, 30)


# ---- format_fuel_cost --------------------------------------------------------

def test_fuel_cost_for_car_uses_8_liters_per_100_km():
    # 125 km -> 10 L -> 10 x 65.50 = 655.00
    assert formatting.format_fuel_cost(125_000, "car", 65.50) == "₱655.00"


def test_fuel_cost_uses_thousands_separator():
    # 2,000 km -> 160 L -> 160 x 62 = 9,920.00
    assert formatting.format_fuel_cost(2_000_000, "car", 62) == "₱9,920.00"


def test_fuel_cost_defaults_to_default_price():
    expected = f"₱{10 * formatting.DEFAULT_GAS_PRICE_PHP:,.2f}"
    assert formatting.format_fuel_cost(125_000, "car") == expected


@pytest.mark.parametrize("profile", ["bike", "walk"])
def test_fuel_cost_not_applicable_without_car(profile):
    assert formatting.format_fuel_cost(125_000, profile, 65) == "N/A"


@pytest.mark.parametrize("meters, price", [(-1, 60), (1000, -5), ("x", 60), (None, 60)])
def test_fuel_cost_bad_input_is_na(meters, price):
    assert formatting.format_fuel_cost(meters, "car", price) == "N/A"


def test_fuel_cost_matches_liters_estimate():
    liters = float(formatting.format_fuel_estimate(80_000, "metric", "car").split()[0])
    assert formatting.format_fuel_cost(80_000, "car", 100) == f"₱{liters * 100:,.2f}"


# ---- parse_gas_price ---------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("65.5", 65.5),
    ("₱70.25", 70.25),
    (" 58 ", 58.0),
    ("1,0.5", 10.5),
])
def test_parse_gas_price_accepts_numbers(raw, expected):
    assert formatting.parse_gas_price(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "abc", "0", "-3", "501", "1e9"])
def test_parse_gas_price_falls_back_to_default(raw):
    assert formatting.parse_gas_price(raw) == formatting.DEFAULT_GAS_PRICE_PHP


# ---- format_eta ----------------------------------------------------------------

def test_eta_same_day():
    assert formatting.format_eta(10 * 60_000, now=LEAVE_AT) == "10:40 PM"


def test_eta_next_day():
    assert formatting.format_eta(3 * 3_600_000, now=LEAVE_AT) == "1:30 AM (+1 day)"


def test_eta_several_days():
    assert formatting.format_eta(50 * 3_600_000, now=LEAVE_AT) == "12:30 AM (+3 days)"


def test_eta_morning_has_no_leading_zero():
    assert formatting.format_eta(0, now=datetime(2026, 1, 1, 9, 5)) == "9:05 AM"


@pytest.mark.parametrize("bad", [None, -1, "soon"])
def test_eta_bad_input_is_na(bad):
    assert formatting.format_eta(bad, now=LEAVE_AT) == "N/A"


# ---- service + web wiring ----------------------------------------------------

def _fake_api(monkeypatch, meters=125_000, time_ms=3_600_000):
    monkeypatch.setattr(services.api, "fetch_route", lambda *a, **k: {
        "ok": True, "from_name": "Manila", "to_name": "Baguio",
        "data": {"paths": [{"distance": meters, "time": time_ms,
                            "points": {"coordinates": []}, "instructions": []}]},
    })


def test_get_route_returns_cost_eta_and_price(monkeypatch):
    _fake_api(monkeypatch)
    result = services.get_route("k", "Manila", "Baguio", "metric", "car", 65.50)
    assert result["ok"]
    assert result["fuel_cost"] == "₱655.00"
    assert result["gas_price"] == "65.50"
    assert result["eta"].endswith(("AM", "PM", "day)", "days)"))


def test_get_route_cost_is_na_for_walking(monkeypatch):
    _fake_api(monkeypatch)
    result = services.get_route("k", "Manila", "Baguio", "metric", "walk", 65.50)
    assert result["fuel_cost"] == "N/A"


def test_web_form_passes_gas_price_to_service(client, monkeypatch):
    seen = {}

    def fake_get_route(key, origin, destination, units, profile, gas_price, weight_kg):
        seen["gas_price"] = gas_price
        return {"ok": False, "title": "Stop", "detail": "test"}

    monkeypatch.setattr(services, "resolve_key", lambda: "k")
    monkeypatch.setattr(services, "get_route", fake_get_route)
    response = client.post("/route", data={"origin": "Manila", "destination": "Baguio",
                                           "gas_price": "70.10"})
    assert seen["gas_price"] == 70.10
    assert b'value="70.10"' in response.data


def test_web_form_bad_gas_price_uses_default(client, monkeypatch):
    seen = {}

    def fake_get_route(*args):
        seen["gas_price"] = args[5]
        return {"ok": False, "title": "Stop", "detail": "test"}

    monkeypatch.setattr(services, "resolve_key", lambda: "k")
    monkeypatch.setattr(services, "get_route", fake_get_route)
    client.post("/route", data={"origin": "Manila", "destination": "Baguio",
                                "gas_price": "free"})
    assert seen["gas_price"] == formatting.DEFAULT_GAS_PRICE_PHP


def test_home_page_shows_gas_price_field(client):
    html = client.get("/").data.decode("utf-8")
    assert 'name="gas_price"' in html
    assert f'value="{formatting.DEFAULT_GAS_PRICE_PHP:.2f}"' in html
