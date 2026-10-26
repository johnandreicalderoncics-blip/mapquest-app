"""GraphHopper API access layer (geocoding + routing).

Everything that talks to the network lives here: turning place names
into coordinates (Geocoding API), fetching the route (Routing API),
and translating every failure (network down, timeout, bad key, unknown
place, API error) into a plain result dictionary so the rest of the
app never has to handle raw exceptions.

Result shape:
    {"ok": True,  "url": str, "data": <parsed JSON>}
    {"ok": False, "title": str, "detail": str}

Why GraphHopper? The original lab (4.9.2) used MapQuest, but MapQuest
now requires billing information even for its free tier. The team chose
GraphHopper instead: it is a free REST/JSON directions API with a
standard key signup (no credit card), so the same lab concepts -
REST request, JSON parsing, status handling - still apply.

API docs: https://docs.graphhopper.com/
"""

import urllib.parse

import requests

GEOCODE_URL = "https://graphhopper.com/api/1/geocode?"
ROUTE_URL = "https://graphhopper.com/api/1/route?"
TIMEOUT_SECONDS = 10

# GraphHopper travel profiles selectable in the app.
PROFILES = {"car": "car", "bike": "bike", "walk": "foot"}

# Coordinates must be sent as "latitude,longitude" for GraphHopper.
def _coord(point: dict) -> str:
    return f"{point['lat']},{point['lng']}"


def _fail(title: str, detail: str) -> dict:
    return {"ok": False, "title": title, "detail": detail}


def _get_json(url: str) -> dict:
    """GET a URL and return parsed JSON, or a failure dictionary.

    Handles the network/HTTP/JSON layers once for both API calls.
    """
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError:
        return _fail(
            "No network connection",
            "Could not reach graphhopper.com. Check your internet "
            "connection and try again.")
    except requests.exceptions.Timeout:
        return _fail(
            "The request timed out",
            f"The API did not answer within {TIMEOUT_SECONDS} seconds. "
            "Please try again.")

    if response.status_code in (401, 403):
        return _fail(
            "Invalid or unauthorized API key",
            "The API rejected the key. Check your key at "
            "graphhopper.com and update config.ini (or the "
            "GRAPHOPPER_KEY environment variable).")

    try:
        return response.json()
    except ValueError:
        return _fail(
            "Unexpected response from the API",
            f"HTTP {response.status_code}: the response was not valid "
            "JSON. Please try again.")

    # JSON error bodies (e.g. {"message": ...}) are interpreted by the
    # callers, which know what each request meant.


def geocode(key: str, query: str) -> dict:
    """Resolve a place name to coordinates.

    Returns {"ok": True, "name": str, "point": {"lat", "lng"}} on
    success, or a {"ok": False, ...} failure dictionary.
    """
    url = GEOCODE_URL + urllib.parse.urlencode(
        {"key": key, "q": query, "limit": 1, "locale": "en"})
    data = _get_json(url)
    # _get_json returns its own failure dictionary for network/HTTP
    # problems (e.g. a rejected key) - pass it through unchanged.
    if data.get("ok") is False:
        return data
    if not data.get("hits"):
        # Either an error body or no matching place.
        if "message" in data:
            return _fail("Location lookup failed", data["message"])
        return _fail(
            f"Location not found: {query}",
            "GraphHopper could not match that place. Try adding a city "
            "or country, e.g. 'Manila, PH'.")
    hit = data["hits"][0]
    name = ", ".join(str(part) for part in (
        hit.get("name"), hit.get("city"), hit.get("state"),
        hit.get("country")) if part)
    return {"ok": True, "name": name or query, "point": hit["point"]}


def fetch_route(key: str, origin: str, destination: str,
                units: str, profile: str) -> dict:
    """Geocode both places, then fetch the route between them.

    This function never raises for expected failures: network problems,
    bad keys and unknown places all come back as {"ok": False, ...}.
    """
    # --- Step 1: resolve both place names to coordinates -------------
    for label, query in (("Starting location", origin),
                         ("Destination", destination)):
        place = geocode(key, query)
        if not place.get("ok"):
            return place  # already a friendly failure dictionary
        if label == "Starting location":
            start = place
        else:
            end = place

    # --- Step 2: request the route between the two coordinates -------
    # GraphHopper accepts multiple "point" parameters in the query
    # string, so they are appended manually instead of put in the dict
    # (a Python dict cannot hold duplicate keys).
    params = urllib.parse.urlencode({
        "key": key,
        "profile": PROFILES[profile],
        "points_encoded": "false",
        "instructions": "true",
        "locale": "en",
    })
    url = (ROUTE_URL + params
           + "&point=" + urllib.parse.quote(_coord(start["point"]))
           + "&point=" + urllib.parse.quote(_coord(end["point"])))
    data = _get_json(url)
    if data.get("ok") is False:
        return data  # network/HTTP failure dictionary - pass it through
    if "message" in data and "paths" not in data:
        return _fail("Routing request failed", data["message"])
    if "paths" not in data:
        return _fail(
            "Routing request failed",
            "The API returned an unexpected reply. Please try again.")

    return {
        "ok": True,
        "url": url,
        "data": data,
        "from_name": start["name"],
        "to_name": end["name"],
    }
