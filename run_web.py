"""Convenience entry point for the Flask web application.

Allows running the web app from the project root:
    py run_web.py

This script creates and runs the Flask app using the application factory.
"""

import os
import threading
import webbrowser

if __name__ == "__main__":
    from src.frontend.web.app import create_app, HOST, PORT, URL
    
    # Open browser after server starts (only on main process, not reloader)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.0, webbrowser.open, args=(URL,)).start()
    
    app = create_app()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
