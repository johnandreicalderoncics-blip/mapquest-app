"""Directions Finder - interactive CLI application.

Entry point for the team's feature-enhanced version of the REST API
concepts from Cisco lab 4.9.2 "Integrate a REST API in a Python
Application" (DevNet Project Activity 3).

The lab used MapQuest; the team switched the API provider to
GraphHopper (free key, no billing information required) - see api.py.
The app concepts are identical: REST request -> JSON -> formatted
output.

Enhancements over the lab:
  * colored, table-formatted output (see display.py, rich library)
  * metric / imperial unit selection (converted in display.py)
  * travel mode selection (car / bike / walk - GraphHopper profiles)
  * place-name geocoding built in (type a city, not coordinates)
  * robust error handling - network, timeout, bad key, unknown place,
    Ctrl+C and end-of-input all produce friendly messages, no tracebacks

Run with:  py main.py
"""

import sys

from backend import api, config
import display

# Accepted answers for the startup prompts.
UNIT_CHOICES = {
    "m": "metric", "metric": "metric", "k": "metric", "km": "metric",
    "i": "imperial", "imperial": "imperial", "mi": "imperial",
    "miles": "imperial",
}
PROFILE_CHOICES = {
    "c": "car", "car": "car", "drive": "car", "driving": "car",
    "b": "bike", "bike": "bike", "bicycle": "bike", "cycle": "bike",
    "w": "walk", "walk": "walk", "foot": "walk", "f": "walk",
}
QUIT_WORDS = {"quit", "q"}


def choose(prompt: str, choices: dict, default: str) -> str:
    """Ask until the answer is valid; blank input picks the default."""
    while True:
        try:
            answer = display.console.input(prompt).strip().lower()
        except EOFError:
            return default
        if not answer:
            return default
        if answer in choices:
            return choices[answer]
        display.console.print("[red]Please choose one of the listed "
                              "options (or press Enter for the default).[/]")


def ask_location(prompt: str) -> str:
    """Read one location; 'quit' exits via the KeyboardInterrupt path."""
    answer = display.console.input(prompt).strip()
    if answer.lower() in QUIT_WORDS:
        raise KeyboardInterrupt  # reuse the same clean-exit path
    return answer


def main() -> None:
    display.show_banner()

    # Stop immediately with a friendly setup message if no key exists.
    key = config.get_api_key()

    units = choose(
        "[bold cyan]Units[/] - (m)etric or (i)mperial [dim](Enter = "
        "imperial)[/]: ",
        UNIT_CHOICES, "imperial")
    profile = choose(
        "[bold cyan]Travel mode[/] - (c)ar, (b)ike, (w)alk [dim](Enter "
        "= car)[/]: ",
        PROFILE_CHOICES, "car")

    display.console.print("[dim]Type 'quit' (or 'q') as the location to "
                          "exit.[/]\n")

    # Main input loop - one route per iteration, errors never stop it.
    while True:
        try:
            origin = ask_location(
                "[bold green]Starting location[/]: ")
            destination = ask_location(
                "[bold green]Destination[/]: ")
        except KeyboardInterrupt:
            # Covers both 'quit' and Ctrl+C: end the session politely.
            display.console.print("\n[bold cyan]Goodbye![/]")
            return

        result = api.fetch_route(key, origin, destination, units, profile)
        display.show_result(result, units, profile)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C during prompts (or while a request is in flight).
        print("\nGoodbye!")
        sys.exit(0)
