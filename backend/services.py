"""Validation and route orchestration for the web frontend.

The service layer between Flask routes and backend/api.py: routes stay
thin (read form data, render templates) and all logic lives here as
pure, testable functions. GraphHopper failures arrive through the
shared {"ok": False, "title", "detail"} contract; this module turns a
successful route into exactly the dict the template needs - and
nothing more, because the raw API result embeds the API key in its
"url" field.
"""

import logging

from backend import api, config, formatting

# Configure module logger
logger = logging.getLogger(__name__)

UNIT_CHOICES = ("metric", "imperial")
PROFILE_CHOICES = ("car", "bike", "walk")


def validate_inputs(origin: str, destination: str) -> str | None:
    """Reject empty or whitespace-only locations before any request.

    Returns an error message, or None when both inputs are usable.
    
    Args:
        origin: The starting location string
        destination: The destination location string
        
    Returns:
        Error message if validation fails, None if inputs are valid
    """
    # Validate origin parameter
    if not isinstance(origin, str):
        logger.warning(f"Invalid origin type: {type(origin).__name__}")
        return "Invalid origin parameter type."
    
    if not isinstance(destination, str):
        logger.warning(f"Invalid destination type: {type(destination).__name__}")
        return "Invalid destination parameter type."
    
    # Check for empty or whitespace-only inputs
    if not origin.strip():
        logger.info("Validation failed: empty origin")
        return "Please enter a starting location."
    
    if not destination.strip():
        logger.info("Validation failed: empty destination")
        return "Please enter a destination."
    
    return None


def resolve_key() -> str | None:
    """Return the configured API key, or None when it is missing.

    Never prints or exits - the web layer shows config.SETUP_MESSAGE
    itself when this returns None.
    """
    return config.load_api_key()


def get_route(key: str, origin: str, destination: str,
              units: str, profile: str,
              gas_price: float = formatting.DEFAULT_GAS_PRICE_PHP) -> dict:
    """Fetch a route and shape it for the index.html template.

    Failure dictionaries from api.fetch_route pass through unchanged.
    On success only template-ready fields are returned - never the raw
    API result, whose "url" field contains the API key. Unexpected
    exceptions become a friendly failure dictionary; the route layer
    logs the real error server-side.
    
    Args:
        key: GraphHopper API key
        origin: Starting location
        destination: Ending location
        units: Unit system ("metric" or "imperial")
        profile: Travel mode ("car", "bike", or "walk")
        
    Returns:
        Dictionary with route data or error information
    """
    # Validate all input parameters
    if not isinstance(key, str) or not key.strip():
        logger.error("Invalid or missing API key")
        return {
            "ok": False,
            "title": "Configuration error",
            "detail": "API key is missing or invalid."
        }
    
    if not isinstance(origin, str) or not origin.strip():
        logger.error("Invalid origin parameter in get_route")
        return {
            "ok": False,
            "title": "Invalid input",
            "detail": "Starting location is required."
        }
    
    if not isinstance(destination, str) or not destination.strip():
        logger.error("Invalid destination parameter in get_route")
        return {
            "ok": False,
            "title": "Invalid input",
            "detail": "Destination is required."
        }
    
    if units not in UNIT_CHOICES:
        logger.warning(f"Invalid units parameter: {units}, defaulting to metric")
        units = "metric"
    
    if profile not in PROFILE_CHOICES:
        logger.warning(f"Invalid profile parameter: {profile}, defaulting to car")
        profile = "car"
    
    try:
        result = api.fetch_route(key, origin, destination, units, profile)
        
        # Validate result structure
        if not isinstance(result, dict):
            logger.error(f"API returned non-dict result: {type(result).__name__}")
            return {
                "ok": False,
                "title": "Unexpected error",
                "detail": "Invalid response from routing service."
            }
        
        if not result.get("ok"):
            logger.info(f"Route request failed: {result.get('title', 'Unknown error')}")
            return result

        # Validate route data structure
        if "data" not in result:
            logger.error("Missing 'data' key in successful route result")
            return {
                "ok": False,
                "title": "Invalid route data",
                "detail": "Route response missing required data."
            }
        
        data = result["data"]
        if not isinstance(data, dict):
            logger.error(f"Route data is not a dict: {type(data).__name__}")
            return {
                "ok": False,
                "title": "Invalid route data",
                "detail": "Route response has invalid structure."
            }
        
        paths = data.get("paths", [])
        if not paths or not isinstance(paths, list):
            logger.error("Missing or invalid 'paths' in route data")
            return {
                "ok": False,
                "title": "Invalid route data",
                "detail": "No valid route path found."
            }
        
        path = paths[0]
        if not isinstance(path, dict):
            logger.error(f"Path is not a dict: {type(path).__name__}")
            return {
                "ok": False,
                "title": "Invalid route data",
                "detail": "Route path has invalid structure."
            }
        
        # Extract and validate route components with defaults
        meters = path.get("distance", 0)
        if not isinstance(meters, (int, float)) or meters < 0:
            logger.warning(f"Invalid distance value: {meters}, using 0")
            meters = 0
        
        time_ms = path.get("time", 0)
        if not isinstance(time_ms, (int, float)) or time_ms < 0:
            logger.warning(f"Invalid time value: {time_ms}, using 0")
            time_ms = 0
        
        # Extract route points with validation
        points = path.get("points", {})
        if not isinstance(points, dict):
            logger.warning(f"Points is not a dict: {type(points).__name__}")
            points = {}
        
        coordinates = points.get("coordinates", [])
        if not isinstance(coordinates, list):
            logger.warning(f"Coordinates is not a list: {type(coordinates).__name__}")
            coordinates = []
        
        route_points = []
        for point in coordinates:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                try:
                    # Convert [lon, lat] to [lat, lon] and validate
                    lon, lat = float(point[0]), float(point[1])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        route_points.append([lat, lon])
                    else:
                        logger.warning(f"Coordinate out of bounds: lat={lat}, lon={lon}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid coordinate values: {point}, error: {e}")
            else:
                logger.warning(f"Invalid coordinate format: {point}")
        
        # Extract and format steps with validation
        instructions = path.get("instructions", [])
        if not isinstance(instructions, list):
            logger.warning(f"Instructions is not a list: {type(instructions).__name__}")
            instructions = []
        
        steps = []
        for number, step in enumerate(instructions, start=1):
            if not isinstance(step, dict):
                logger.warning(f"Step {number} is not a dict: {type(step).__name__}")
                continue
            
            step_distance = step.get("distance", 0)
            if not isinstance(step_distance, (int, float)) or step_distance < 0:
                logger.warning(f"Invalid step distance for step {number}: {step_distance}")
                step_distance = 0
            
            steps.append({
                "number": number,
                "text": step.get("text") or "(no description)",
                "distance": formatting.format_distance(step_distance, units),
            })
        
        return {
            "ok": True,
            "origin": origin,
            "destination": destination,
            "from_name": result.get("from_name", "-"),
            "to_name": result.get("to_name", "-"),
            "profile_label": formatting.PROFILE_LABELS.get(profile, profile),
            "duration": formatting.format_time(time_ms),
            "distance": formatting.format_distance(meters, units),
            "fuel": formatting.format_fuel_estimate(meters, units, profile),
            "fuel_cost": formatting.format_fuel_cost(meters, profile, gas_price),
            "gas_price": f"{gas_price:,.2f}",
            "eta": formatting.format_eta(time_ms),
            "steps": steps,
            "route_points": route_points,
        }
    except Exception as e:
        # Log the actual exception for debugging
        logger.exception(f"Unexpected error processing route: {e}")
        # Deliberately no exception text here: details could echo
        # request internals. app.py logs the real error server-side.
        return {"ok": False, "title": "Unexpected error",
                "detail": "Something went wrong on our side. "
                          "Please try again."}
