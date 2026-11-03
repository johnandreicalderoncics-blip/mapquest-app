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

import logging
import urllib.parse

import requests

# Configure logging for error tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    Wraps HTTP requests in try-catch blocks and handles:
    - DNS resolution failures
    - Connection refused errors
    - Network timeouts
    - Invalid JSON responses
    - HTTP error status codes (400-599)
    
    All errors are logged for debugging purposes.
    """
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        
    except requests.exceptions.ConnectionError as exc:
        # Handle DNS failures and connection refused separately for better UX
        error_str = str(exc).lower()
        
        if 'nodename nor servname provided' in error_str or 'name or service not known' in error_str or 'getaddrinfo failed' in error_str:
            # DNS resolution failure
            logger.error(f"DNS resolution failed for URL: {url}, Error: {exc}")
            return _fail(
                "DNS resolution failed",
                "Could not resolve graphhopper.com. Check your DNS settings "
                "and internet connection, then try again.")
        
        elif 'connection refused' in error_str or 'refused' in error_str:
            # Connection refused by server
            logger.error(f"Connection refused for URL: {url}, Error: {exc}")
            return _fail(
                "Connection refused",
                "The server refused the connection. The API service may be "
                "down or blocking requests. Please try again later.")
        
        else:
            # Generic connection error
            logger.error(f"Connection error for URL: {url}, Error: {exc}")
            return _fail(
                "No network connection",
                "Could not reach graphhopper.com. Check your internet "
                "connection and try again.")
    
    except requests.exceptions.Timeout as exc:
        logger.error(f"Request timeout for URL: {url}, Error: {exc}")
        return _fail(
            "The request timed out",
            f"The API did not answer within {TIMEOUT_SECONDS} seconds. "
            "Please try again.")
    
    except requests.exceptions.RequestException as exc:
        # Catch-all for other requests library errors
        logger.error(f"Request exception for URL: {url}, Error: {exc}")
        return _fail(
            "Network request failed",
            f"A network error occurred: {type(exc).__name__}. "
            "Please check your connection and try again.")

    # Handle HTTP error status codes
    if response.status_code in (401, 403):
        logger.warning(f"Authentication failed with status {response.status_code}")
        return _fail(
            "Invalid or unauthorized API key",
            "The API rejected the key. Check your key at "
            "graphhopper.com and update config.ini (or the "
            "GRAPHOPPER_KEY environment variable).")

    if response.status_code == 429:
        logger.warning("GraphHopper API rate limit reached")
        return _fail(
            "API rate limit reached",
            "Too many route requests were sent in a short time. "
            "Please wait a minute and try again.")
    
    # Handle other 4xx client errors
    if 400 <= response.status_code < 500:
        logger.error(f"Client error {response.status_code} for URL: {url}")
        return _fail(
            f"Client error ({response.status_code})",
            f"The request was invalid. HTTP {response.status_code}: "
            f"{response.reason}. Please check your inputs and try again.")
    
    # Handle 5xx server errors
    if 500 <= response.status_code < 600:
        logger.error(f"Server error {response.status_code} for URL: {url}")
        return _fail(
            f"Server error ({response.status_code})",
            f"The API server encountered an error. HTTP {response.status_code}: "
            f"{response.reason}. Please try again later.")

    # Parse JSON response
    try:
        data = response.json()
        logger.debug(f"Successfully parsed JSON response from {url}")
        return data
        
    except ValueError as exc:
        # Invalid JSON response
        logger.error(f"Invalid JSON in response from {url}, Error: {exc}, "
                    f"Status: {response.status_code}, Content: {response.text[:200]}")
        return _fail(
            "Unexpected response from the API",
            f"HTTP {response.status_code}: the response was not valid "
            "JSON. Please try again.")
    
    except Exception as exc:
        # Unexpected error during JSON parsing
        logger.error(f"Unexpected error parsing JSON from {url}, Error: {exc}")
        return _fail(
            "Failed to process API response",
            f"An unexpected error occurred while processing the response: "
            f"{type(exc).__name__}. Please try again.")

    # JSON error bodies (e.g. {"message": ...}) are interpreted by the
    # callers, which know what each request meant.


def geocode(key: str, query: str) -> dict:
    """Resolve a place name to coordinates.

    Returns {"ok": True, "name": str, "point": {"lat", "lng"}} on
    success, or a {"ok": False, ...} failure dictionary.
    
    All errors are logged for debugging.
    """
    logger.info(f"Geocoding query: '{query}'")
    
    scoped_query = query
    if "philippines" not in query.casefold() and " ph" not in query.casefold():
        scoped_query = f"{query}, Philippines"

    url = GEOCODE_URL + urllib.parse.urlencode(
        {
            "key": key,
            "q": scoped_query,
            "limit": 1,
            "locale": "en",
        })
    data = _get_json(url)
    
    # _get_json returns its own failure dictionary for network/HTTP
    # problems (e.g. a rejected key) - pass it through unchanged.
    if data.get("ok") is False:
        logger.warning(f"Geocoding failed for '{query}': {data.get('title')}")
        return data
    
    if not data.get("hits"):
        # Either an error body or no matching place.
        if "message" in data:
            logger.error(f"Geocoding API error for '{query}': {data['message']}")
            return _fail("Location lookup failed", data["message"])
        
        logger.warning(f"No geocoding results found for: '{query}'")
        return _fail(
            f"Location not found: {query}",
            "GraphHopper could not match that place. Try adding a city "
            "or country, e.g. 'Manila, PH'.")
    
    hit = data["hits"][0]
    name = ", ".join(str(part) for part in (
        hit.get("name"), hit.get("city"), hit.get("state"),
        hit.get("country")) if part)
    
    logger.info(f"Successfully geocoded '{query}' to: {name}")
    return {"ok": True, "name": name or query, "point": hit["point"]}


def fetch_route(key: str, origin: str, destination: str,
                units: str, profile: str) -> dict:
    """Geocode both places, then fetch the route between them.

    This function never raises for expected failures: network problems,
    bad keys and unknown places all come back as {"ok": False, ...}.
    
    All errors are logged for debugging.
    """
    logger.info(f"Fetching route from '{origin}' to '{destination}' "
                f"(profile: {profile}, units: {units})")
    
    # --- Step 1: resolve both place names to coordinates -------------
    for label, query in (("Starting location", origin),
                         ("Destination", destination)):
        place = geocode(key, query)
        if not place.get("ok"):
            logger.error(f"{label} geocoding failed: {place.get('title')}")
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
    
    logger.info(f"Requesting route from API")
    data = _get_json(url)
    
    if data.get("ok") is False:
        logger.error(f"Route request failed: {data.get('title')}")
        return data  # network/HTTP failure dictionary - pass it through
    
    if "message" in data and not data.get("paths"):
        logger.error(f"Route API returned error: {data['message']}")
        return _fail("Routing request failed", data["message"])
    
    if not data.get("paths"):
        logger.error(f"Route API returned unexpected structure (missing 'paths')")
        return _fail(
            "Routing request failed",
            "The API returned an unexpected reply. Please try again.")

    logger.info(f"Successfully fetched route from '{start['name']}' to '{end['name']}'")
    return {
        "ok": True,
        "url": url,
        "data": data,
        "from_name": start["name"],
        "to_name": end["name"],
    }
