"""API key configuration for the Directions app.

The key is resolved in this order:
  1. GRAPHOPPER_KEY environment variable
  2. config.ini in the project root (one level above backend/),
     section [graphhopper], key = ...

The real key must never be committed to GitHub: config.ini is listed
in .gitignore. Copy config.sample.ini to config.ini and paste your key.

Free key (no credit card required): https://graphhopper.com/
See README.md for the full setup guide so another team can continue
this project.
"""

import configparser
import os
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.ini"

# Shown (CLI: printed, GUI: displayed in the window) when no usable key
# is found. A single print() of this string reproduces the original
# CLI setup output exactly.
SETUP_MESSAGE = "\n".join((
    "No GraphHopper API key found.",
    "",
    "Set it up in one of two ways:",
    '  1. Environment variable:  setx GRAPHOPPER_KEY "your-key-here"',
    "     (open a NEW terminal afterwards so it takes effect)",
    "  2. Copy config.sample.ini to config.ini in this folder",
    "     and paste your key under [graphhopper].",
    "",
    "A free key (no credit card) is available at:",
    "  https://graphhopper.com/api/  ->  sign up -> Dashboard -> API key",
))


def load_api_key() -> str | None:
    """Return the GraphHopper API key, or None if none is configured.

    Unlike get_api_key() this never prints or exits, so the GUI can
    show SETUP_MESSAGE itself instead of dying on startup.
    
    Error Handling:
    - Missing config file: Returns None (file existence checked before reading)
    - Malformed INI file: Catches parsing errors and logs them, returns None
    - Missing section/key: Uses fallback="" to handle gracefully
    - Invalid/placeholder key: Filters out "YOUR_KEY_HERE" placeholder
    """
    # 1) Environment variable wins (handy for CI and quick testing).
    try:
        key = os.environ.get("GRAPHOPPER_KEY", "").strip()
        if key:
            return key
    except Exception as exc:
        # Unexpected error reading environment variable - log and continue
        print(f"Warning: Error reading GRAPHOPPER_KEY environment variable: {exc}")

    # 2) Fall back to config.ini (git-ignored so the key stays private).
    parser = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        try:
            parser.read(CONFIG_FILE, encoding="utf-8")
        except configparser.Error as exc:
            # Malformed INI file - log error and return None
            print(f"Error: Failed to parse config file {CONFIG_FILE}: {exc}")
            return None
        except Exception as exc:
            # Unexpected error reading config file - log and return None
            print(f"Error: Unexpected error reading config file {CONFIG_FILE}: {exc}")
            return None
        
        try:
            key = parser.get("graphhopper", "key", fallback="").strip()
            if key and key.upper() != "YOUR_KEY_HERE":
                return key
        except Exception as exc:
            # Error extracting key from config - log and return None
            print(f"Warning: Error extracting API key from config file: {exc}")
            return None
    else:
        # Config file doesn't exist - not an error, just means no key configured
        pass

    # Nothing usable found - let the caller decide how to explain it.
    return None


def get_api_key() -> str:
    """Return the GraphHopper API key, or exit with a friendly setup message.
    
    Error Handling:
    - Missing key: Prints SETUP_MESSAGE and exits cleanly with status 1
    - All errors from load_api_key() are handled there and result in None
    """
    try:
        key = load_api_key()
        if key is None:
            print(SETUP_MESSAGE)
            sys.exit(1)
        return key
    except Exception as exc:
        # Unexpected error during key loading - show error and exit
        print(f"Error: Unexpected error loading API key: {exc}")
        print("\n" + SETUP_MESSAGE)
        sys.exit(1)
