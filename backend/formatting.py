"""Presentation-neutral formatting shared by every frontend.

GraphHopper returns distances in METERS and times in MILLISECONDS.
This module converts those raw values into the user-facing strings
(kilometers/miles, hh:mm:ss, fuel estimates) without any terminal or
GUI rendering, so the CLI, the tkinter GUI and the web frontend show
identical numbers. See ARCHITECTURE.md sections 5 and 9.

Unit facts (important for anyone continuing this project):
  * GraphHopper does not report fuel at all, so fuel for driving
    routes is an ESTIMATE here: 8 L per 100 km (about 29 mpg).
    Walking/cycling routes show N/A instead of a made-up number.
"""

METERS_PER_MILE = 1609.344
LITERS_PER_KM = 0.08        # typical car: 8 L / 100 km
GALLONS_PER_MILE = 1 / 29.4  # typical car: 29 mpg

UNIT_LABELS = {
    "metric": {"distance": "Kilometers", "fuel": "Liters (est.)",
               "short": "km", "fuel_short": "L"},
    "imperial": {"distance": "Miles", "fuel": "Gallons (est.)",
                 "short": "mi", "fuel_short": "gal"},
}

PROFILE_LABELS = {
    "car": "Car (driving)",
    "bike": "Bicycle",
    "walk": "Walking",
}


def format_time(milliseconds: float) -> str:
    """Convert GraphHopper's milliseconds to hh:mm:ss."""
    seconds = int(milliseconds / 1000)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_distance(meters: float, units: str) -> str:
    """Convert meters to the user's chosen unit."""
    labels = UNIT_LABELS[units]
    if units == "metric":
        return f"{meters / 1000:.2f} {labels['short']}"
    return f"{meters / METERS_PER_MILE:.2f} {labels['short']}"


def format_fuel_estimate(meters: float, units: str, profile: str) -> str:
    """Estimate fuel for driving routes; N/A for every other mode.

    GraphHopper reports no fuel usage, so this is a fixed-consumption
    estimate (see the module docstring), never a measured value.
    """
    if profile != "car":
        return "N/A (not applicable for this travel mode)"
    labels = UNIT_LABELS[units]
    if units == "metric":
        return f"{(meters / 1000) * LITERS_PER_KM:.2f} {labels['fuel_short']}"
    return (f"{(meters / METERS_PER_MILE) * GALLONS_PER_MILE:.2f} "
            f"{labels['fuel_short']}")
