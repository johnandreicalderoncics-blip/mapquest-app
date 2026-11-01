"""Validation and route orchestration for the web frontend.

The service layer between Flask routes and backend/api.py: routes stay
thin (read form data, render templates) and all logic lives here as
pure, testable functions. GraphHopper failures arrive through the
shared {"ok": False, "title", "detail"} contract; this module turns a
successful route into exactly the dict the template needs - and
nothing more, because the raw API result embeds the API key in its
"url" field.
"""

from backend import api, config, formatting

UNIT_CHOICES = ("metric", "imperial")
PROFILE_CHOICES = ("car", "bike", "walk")


def validate_inputs(origin: str, destination: str) -> str | None:
    """Reject empty or whitespace-only locations before any request.

    Returns an error message, or None when both inputs are usable.
    """
    if not origin.strip():
        return "Please enter a starting location."
    if not destination.strip():
        return "Please enter a destination."
    return None


def resolve_key() -> str | None:
    """Return the configured API key, or None when it is missing.

    Never prints or exits - the web layer shows config.SETUP_MESSAGE
    itself when this returns None.
    """
    return config.load_api_key()


def get_route(key: str, origin: str, destination: str,
              units: str, profile: str) -> dict:
    """Fetch a route and shape it for the index.html template.

    Failure dictionaries from api.fetch_route pass through unchanged.
    On success only template-ready fields are returned - never the raw
    API result, whose "url" field contains the API key. Unexpected
    exceptions become a friendly failure dictionary; the route layer
    logs the real error server-side.
    """
    try:
        result = api.fetch_route(key, origin, destination, units, profile)
        if not result.get("ok"):
            return result

        path = result["data"]["paths"][0]
        meters = path.get("distance", 0)
        # Step distances are meters; format_distance() converts them to
        # the user's chosen unit.
        steps = [
            {
                "number": number,
                "text": step.get("text") or "(no description)",
                "distance": formatting.format_distance(
                    step.get("distance", 0), units),
            }
            for number, step in enumerate(path.get("instructions", []),
                                          start=1)
        ]
        return {
            "ok": True,
            "origin": origin,
            "destination": destination,
            "from_name": result.get("from_name", "-"),
            "to_name": result.get("to_name", "-"),
            "profile_label": formatting.PROFILE_LABELS.get(profile, profile),
            "duration": formatting.format_time(path.get("time", 0)),
            "distance": formatting.format_distance(meters, units),
            "fuel": formatting.format_fuel_estimate(meters, units, profile),
            "steps": steps,
        }
    except Exception:
        # Deliberately no exception text here: details could echo
        # request internals. app.py logs the real error server-side.
        return {"ok": False, "title": "Unexpected error",
                "detail": "Something went wrong on our side. "
                          "Please try again."}
