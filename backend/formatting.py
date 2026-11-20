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

import logging

logger = logging.getLogger(__name__)

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
    """Convert GraphHopper's milliseconds to hh:mm:ss.
    
    Args:
        milliseconds: Time duration in milliseconds (must be non-negative).
        
    Returns:
        Formatted time string as hh:mm:ss, or error string for invalid input.
        
    Error Handling:
        - None values return "N/A"
        - Negative values return "N/A" with logged warning
        - Non-numeric values return "N/A" with logged warning
    """
    if milliseconds is None:
        logger.warning("format_time received None value")
        return "N/A"
    
    try:
        milliseconds = float(milliseconds)
    except (TypeError, ValueError) as exc:
        logger.warning(f"format_time received non-numeric value: {milliseconds!r} ({exc})")
        return "N/A"
    
    if milliseconds < 0:
        logger.warning(f"format_time received negative value: {milliseconds}")
        return "N/A"
    
    seconds = int(milliseconds / 1000)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_distance(meters: float, units: str) -> str:
    """Convert meters to the user's chosen unit.
    
    Args:
        meters: Distance in meters (must be non-negative).
        units: Unit system, either "metric" or "imperial".
        
    Returns:
        Formatted distance string with unit label, or error string for invalid input.
        
    Error Handling:
        - None meters value returns "N/A"
        - Negative meters value returns "N/A" with logged warning
        - Non-numeric meters value returns "N/A" with logged warning
        - Invalid units string defaults to "metric" with logged warning
    """
    if meters is None:
        logger.warning("format_distance received None value for meters")
        return "N/A"
    
    try:
        meters = float(meters)
    except (TypeError, ValueError) as exc:
        logger.warning(f"format_distance received non-numeric meters value: {meters!r} ({exc})")
        return "N/A"
    
    if meters < 0:
        logger.warning(f"format_distance received negative meters value: {meters}")
        return "N/A"
    
    # Validate units string
    if units not in UNIT_LABELS:
        logger.warning(f"format_distance received invalid units: {units!r}, defaulting to 'metric'")
        units = "metric"
    
    labels = UNIT_LABELS[units]
    if units == "metric":
        return f"{meters / 1000:.2f} {labels['short']}"
    return f"{meters / METERS_PER_MILE:.2f} {labels['short']}"


def format_fuel_estimate(meters: float, units: str, profile: str) -> str:
    """Estimate fuel for driving routes; N/A for every other mode.

    GraphHopper reports no fuel usage, so this is a fixed-consumption
    estimate (see the module docstring), never a measured value.
    
    Args:
        meters: Distance in meters (must be non-negative).
        units: Unit system, either "metric" or "imperial".
        profile: Travel profile, one of "car", "bike", "walk".
        
    Returns:
        Formatted fuel estimate string with unit label, or N/A for non-car profiles.
        
    Error Handling:
        - None meters value returns "N/A"
        - Negative meters value returns "N/A" with logged warning
        - Non-numeric meters value returns "N/A" with logged warning
        - Invalid units string defaults to "metric" with logged warning
        - Invalid profile returns "N/A" with logged warning
    """
    if meters is None:
        logger.warning("format_fuel_estimate received None value for meters")
        return "N/A"
    
    try:
        meters = float(meters)
    except (TypeError, ValueError) as exc:
        logger.warning(f"format_fuel_estimate received non-numeric meters value: {meters!r} ({exc})")
        return "N/A"
    
    if meters < 0:
        logger.warning(f"format_fuel_estimate received negative meters value: {meters}")
        return "N/A"
    
    # Validate units string
    if units not in UNIT_LABELS:
        logger.warning(f"format_fuel_estimate received invalid units: {units!r}, defaulting to 'metric'")
        units = "metric"
    
    # Validate profile
    if profile not in PROFILE_LABELS:
        logger.warning(f"format_fuel_estimate received invalid profile: {profile!r}")
        return "N/A"
    
    if profile != "car":
        return "N/A (not applicable for this travel mode)"
    
    labels = UNIT_LABELS[units]
    if units == "metric":
        return f"{(meters / 1000) * LITERS_PER_KM:.2f} {labels['fuel_short']}"
    return (f"{(meters / METERS_PER_MILE) * GALLONS_PER_MILE:.2f} "
            f"{labels['fuel_short']}")


# --- Fuel cost (Philippine peso) and ETA ----------------------------------
#
# Cost is always worked out from LITERS, whatever display unit the user
# picked, because PH pump prices are quoted per liter. The default price
# is only a starting value; the web form lets the user type today's price.
DEFAULT_GAS_PRICE_PHP = 62.00   # PHP per liter, editable in the web form
MIN_GAS_PRICE_PHP = 1.0
MAX_GAS_PRICE_PHP = 500.0


def parse_gas_price(raw) -> float:
    """Turn a form value into a usable PHP/L price, or the default.

    Accepts "65.5", "₱65.50" or "1,065"; anything blank, non-numeric or
    outside MIN..MAX falls back to DEFAULT_GAS_PRICE_PHP.
    """
    if raw is None:
        return DEFAULT_GAS_PRICE_PHP
    text = str(raw).strip().replace("₱", "").replace(",", "")
    try:
        price = float(text)
    except ValueError:
        return DEFAULT_GAS_PRICE_PHP
    if not (MIN_GAS_PRICE_PHP <= price <= MAX_GAS_PRICE_PHP):
        return DEFAULT_GAS_PRICE_PHP
    return price


def format_fuel_cost(meters: float, profile: str,
                     price_per_liter: float = DEFAULT_GAS_PRICE_PHP) -> str:
    """Estimated fuel cost in pesos for driving routes, e.g. "₱1,234.56".

    Uses the same 8 L/100 km assumption as format_fuel_estimate, so the
    liters and the peso figure on screen always agree.
    """
    if profile != "car":
        return "N/A"
    try:
        meters = float(meters)
        price = float(price_per_liter)
    except (TypeError, ValueError):
        logger.warning("format_fuel_cost received non-numeric input")
        return "N/A"
    if meters < 0 or price < 0:
        logger.warning("format_fuel_cost received a negative value")
        return "N/A"
    liters = (meters / 1000) * LITERS_PER_KM
    return f"₱{liters * price:,.2f}"


def format_eta(milliseconds: float, now=None) -> str:
    """Clock time of arrival if the user leaves now, e.g. "3:45 PM".

    Adds "(+1 day)" / "(+2 days)" when the trip ends on a later date.
    `now` is injectable so tests don't depend on the real clock.
    """
    from datetime import datetime, timedelta

    try:
        milliseconds = float(milliseconds)
    except (TypeError, ValueError):
        logger.warning(f"format_eta received non-numeric value: {milliseconds!r}")
        return "N/A"
    if milliseconds < 0:
        logger.warning(f"format_eta received negative value: {milliseconds}")
        return "N/A"

    now = now or datetime.now()
    arrival = now + timedelta(milliseconds=milliseconds)
    clock = arrival.strftime("%I:%M %p").lstrip("0")
    days = (arrival.date() - now.date()).days
    if days == 1:
        return f"{clock} (+1 day)"
    if days > 1:
        return f"{clock} (+{days} days)"
    return clock
