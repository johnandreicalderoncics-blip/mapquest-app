"""API key configuration for the Directions app.

The key is resolved in this order:
  1. GRAPHOPPER_KEY environment variable
  2. config.ini file next to this script ([graphhopper] key = ...)

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

CONFIG_FILE = Path(__file__).resolve().parent / "config.ini"


def get_api_key() -> str:
    """Return the GraphHopper API key, or exit with a friendly setup message."""
    # 1) Environment variable wins (handy for CI and quick testing).
    key = os.environ.get("GRAPHOPPER_KEY", "").strip()
    if key:
        return key

    # 2) Fall back to config.ini (git-ignored so the key stays private).
    parser = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        parser.read(CONFIG_FILE, encoding="utf-8")
        key = parser.get("graphhopper", "key", fallback="").strip()
        if key and key.upper() != "YOUR_KEY_HERE":
            return key

    # Nothing usable found — explain how to fix it instead of crashing.
    print("No GraphHopper API key found.\n")
    print("Set it up in one of two ways:")
    print('  1. Environment variable:  setx GRAPHOPPER_KEY "your-key-here"')
    print("     (open a NEW terminal afterwards so it takes effect)")
    print("  2. Copy config.sample.ini to config.ini in this folder")
    print("     and paste your key under [graphhopper].\n")
    print("A free key (no credit card) is available at:")
    print("  https://graphhopper.com/api/  ->  sign up -> Dashboard -> API key")
    sys.exit(1)
