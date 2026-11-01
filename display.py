"""All screen output for the Directions app.

This is the "feature enhancement" layer over lab 4.9.2: the plain
print() statements of the lab are replaced with colored, table-formatted
output using the rich library, and every distance/time/fuel value is
rendered in the units the user chose (metric or imperial).

Unit facts (important for anyone continuing this project):
  * GraphHopper returns distances in METERS and times in MILLISECONDS,
    so this module converts to kilometers/miles and hh:mm:ss for
    display (the lab's MapQuest API did the unit conversion itself).
  * GraphHopper does not report fuel at all, so fuel for driving
    routes is an ESTIMATE in this layer: 8 L per 100 km (about 29 mpg).
    Walking/cycling routes show N/A instead of a made-up number.
"""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

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


def show_banner() -> None:
    """App title banner shown once at startup."""
    console.print(Panel.fit(
        "[bold cyan]Directions Finder[/]\n"
        "[dim]GraphHopper REST API - lab 4.9.2 feature-enhanced"
        " - DevNet Project Activity 3[/]",
        border_style="cyan",
    ))


def show_error(title: str, detail: str) -> None:
    """Render any failure as a red panel - never a raw traceback."""
    console.print(Panel(
        f"[bold red]{title}[/]\n{detail}",
        border_style="red",
        title="Route request failed",
    ))


def show_route(result: dict, units: str, profile: str) -> None:
    """Render a successful route: summary table + turn-by-turn table."""
    labels = UNIT_LABELS[units]
    path = result["data"]["paths"][0]
    instructions = path.get("instructions", [])

    # --- Trip summary -------------------------------------------------
    meters = path.get("distance", 0)
    if profile == "car":
        if units == "metric":
            fuel_text = f"{(meters / 1000) * LITERS_PER_KM:.2f} " \
                        f"{labels['fuel_short']}"
        else:
            fuel_text = f"{(meters / METERS_PER_MILE) * GALLONS_PER_MILE:.2f} " \
                        f"{labels['fuel_short']}"
    else:
        fuel_text = "N/A (not applicable for this travel mode)"

    summary = Table(show_header=False, box=box.ROUNDED, border_style="green",
                    title="[bold green]Trip Summary[/]", padding=(0, 2))
    summary.add_column(style="bold cyan", justify="right")
    summary.add_column()

    summary.add_row("From", result.get("from_name", "-"))
    summary.add_row("To", result.get("to_name", "-"))
    summary.add_row("Travel mode", PROFILE_LABELS.get(profile, profile))
    summary.add_row("Trip duration", format_time(path.get("time", 0)))
    summary.add_row(f"Distance ({labels['distance']})",
                    format_distance(meters, units))
    summary.add_row(f"Fuel used ({labels['fuel']})", fuel_text)
    console.print(summary)

    # --- Turn-by-turn directions ---------------------------------------
    steps = Table(title="[bold green]Turn-by-Turn Directions[/]",
                  box=box.SIMPLE_HEAVY, header_style="bold yellow",
                  padding=(0, 1))
    steps.add_column("#", justify="right", style="dim", width=4)
    steps.add_column("Instruction")
    steps.add_column(labels["short"], justify="right", width=10)

    for number, step in enumerate(instructions, start=1):
        text = step.get("text") or "(no description)"
        # step distances are meters - format_distance() converts them
        # to the user's chosen unit and drops the repeated unit text.
        steps.add_row(str(number), text,
                      format_distance(step.get("distance", 0),
                                      units).split()[0])
    if instructions:
        console.print(steps)
    else:
        console.print("[yellow]No turn-by-turn instructions were "
                      "returned for this route.[/]")
    console.print()


def show_result(result: dict, units: str, profile: str) -> None:
    """Single entry point used by main.py for every API reply."""
    if result.get("ok"):
        show_route(result, units, profile)
    else:
        show_error(result.get("title", "Unknown error"),
                   result.get("detail", ""))
