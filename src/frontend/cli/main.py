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

import logging
import sys
import traceback
from pathlib import Path

from backend import api, config
from src.frontend.cli import display

# Configure logging for error tracking
LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "cli_errors.log"

def setup_logging() -> None:
    """Configure logging to file for error tracking."""
    try:
        LOG_DIR.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
    except Exception as e:
        # If logging setup fails, continue without it
        print(f"Warning: Could not set up error logging: {e}", file=sys.stderr)

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


def main() -> int:
    """Run the interactive CLI application.
    
    Returns:
        Exit code: 0 for success, non-zero for errors
    """
    try:
        display.show_banner()

        # Stop immediately with a friendly setup message if no key exists.
        try:
            key = config.get_api_key()
        except SystemExit:
            # config.get_api_key() calls sys.exit(1) when no key found
            # Re-raise to let outer handler catch it
            return 1
        except Exception as e:
            display.console.print("[red]Error loading API key configuration.[/]")
            logging.error(f"API key configuration error: {e}\n{traceback.format_exc()}")
            return 1

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
                return 0
            except EOFError:
                # End of input (e.g., Ctrl+D on Unix, Ctrl+Z on Windows)
                display.console.print("\n[bold cyan]Goodbye![/]")
                return 0
            except Exception as e:
                # Unexpected error during input - log but continue
                display.console.print(f"[red]Error reading input: {e}[/]")
                logging.error(f"Input error: {e}\n{traceback.format_exc()}")
                continue

            try:
                result = api.fetch_route(key, origin, destination, units, profile)
                display.show_result(result, units, profile)
            except Exception as e:
                # Unexpected error during route fetch or display
                display.console.print(f"[red]Unexpected error: {e}[/]")
                display.console.print("[yellow]Please try again or type 'quit' to exit.[/]")
                logging.error(f"Route fetch/display error: {e}\n{traceback.format_exc()}")
                # Continue the loop - don't crash the entire app
                continue

    except KeyboardInterrupt:
        # Ctrl+C during startup or prompts
        display.console.print("\n[bold cyan]Goodbye![/]")
        return 0
    except Exception as e:
        # Catch-all for any unexpected errors during startup
        display.console.print(f"\n[red bold]An unexpected error occurred:[/] {e}")
        display.console.print("[yellow]The error has been logged for debugging.[/]")
        logging.error(f"Unhandled exception in main: {e}\n{traceback.format_exc()}")
        return 1

    return 0


if __name__ == "__main__":
    # Set up error logging
    setup_logging()
    
    # Run the application and exit with appropriate code
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        # Final catch for Ctrl+C - ensure clean exit
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        # Absolute last resort - something went very wrong
        print(f"\nFatal error: {e}", file=sys.stderr)
        logging.critical(f"Fatal unhandled exception: {e}\n{traceback.format_exc()}")
        sys.exit(1)
