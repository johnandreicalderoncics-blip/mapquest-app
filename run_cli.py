"""Convenience entry point for the CLI application.

Allows running the CLI from the project root:
    py run_cli.py

This script simply imports and calls the CLI main function.
"""

import sys

if __name__ == "__main__":
    try:
        from src.frontend.cli.main import main
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
