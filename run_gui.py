"""Convenience entry point for the desktop GUI application.

Allows running the GUI from the project root:
    py run_gui.py

This script simply imports and calls the GUI main function.
"""

if __name__ == "__main__":
    from src.frontend.desktop.gui import main
    main()
