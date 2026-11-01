"""Flask web entry point for the Directions app.

Run with:  py app.py

Architecture (ARCHITECTURE.md section 6): the browser is the
presentation layer; this module owns only HTTP concerns - routes,
form parsing and error pages. All logic lives in backend/services.py,
which calls backend/api.py. The server binds to 127.0.0.1 only, so
the app is never exposed to other devices on the network.

Security rules enforced here:
  * the API key never appears in any page, log line or URL;
  * unexpected exceptions are logged server-side and rendered as a
    friendly error page - never a traceback;
  * form values are validated and normalized before reaching the
    service layer.
"""

import os
import threading
import webbrowser

from flask import Flask, render_template, request

from backend import config, services

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}"

# Allowed form values; anything else falls back to these defaults so a
# tampered form can never reach formatting.UNIT_LABELS[units].
UNIT_DEFAULT = "imperial"
PROFILE_DEFAULT = "car"


def _page(**context) -> str:
    """Render index.html with the shared defaults every route needs."""
    context.setdefault("origin", "")
    context.setdefault("destination", "")
    context.setdefault("units", UNIT_DEFAULT)
    context.setdefault("profile", PROFILE_DEFAULT)
    context.setdefault("has_key", True)
    context.setdefault("setup_lines", [])
    context.setdefault("error", None)
    context.setdefault("error_detail", None)
    context.setdefault("result", None)
    return render_template("index.html", **context)


def create_app() -> Flask:
    """Application factory so tests can build fresh instances."""
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        has_key = services.resolve_key() is not None
        setup_lines = [] if has_key else config.SETUP_MESSAGE.splitlines()
        return _page(has_key=has_key, setup_lines=setup_lines)

    @app.post("/route")
    def route() -> str:
        origin = request.form.get("origin", "")
        destination = request.form.get("destination", "")
        units = request.form.get("units", UNIT_DEFAULT)
        profile = request.form.get("profile", PROFILE_DEFAULT)
        if units not in services.UNIT_CHOICES:
            units = UNIT_DEFAULT
        if profile not in services.PROFILE_CHOICES:
            profile = PROFILE_DEFAULT

        # Re-fill the form with what the user typed.
        context = {"origin": origin, "destination": destination,
                   "units": units, "profile": profile}

        error = services.validate_inputs(origin, destination)
        if error is not None:
            return _page(**context, error=error)

        key = services.resolve_key()
        if key is None:
            return _page(**context, has_key=False,
                         setup_lines=config.SETUP_MESSAGE.splitlines())

        result = services.get_route(key, origin.strip(),
                                    destination.strip(), units, profile)
        if not result.get("ok"):
            return _page(**context, error=result.get("title", "Error"),
                         error_detail=result.get("detail", ""))
        return _page(**context, result=result)

    @app.errorhandler(404)
    def not_found(_error) -> tuple[str, int]:
        return _page(error="Page not found.",
                     error_detail="Check the address and try again."), 404

    @app.errorhandler(Exception)
    def unhandled(error) -> tuple[str, int]:
        # Logged server-side only; the page never shows a traceback,
        # request URL or any configuration value.
        app.logger.exception("Unhandled error")
        return _page(error="Something went wrong on our side.",
                     error_detail="Please try again."), 500

    return app


if __name__ == "__main__":
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        # Open the browser shortly after the server starts listening.
        threading.Timer(1.0, webbrowser.open, args=(URL,)).start()
    app = create_app()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
