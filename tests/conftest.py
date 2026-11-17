"""pytest fixtures for the Flask web tests.

One app instance with TESTING=True serves every route test; the autouse
fixture keeps GRAPHOPPER_KEY out of the environment so tests decide the
key state themselves.
"""

import pytest

from src.frontend.web.app import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_key_env(monkeypatch):
    """Remove any real key so tests start from a no-key state."""
    monkeypatch.delenv("GRAPHOPPER_KEY", raising=False)


@pytest.fixture(autouse=True)
def no_map_tile_threads(monkeypatch):
    """Stop tkintermapview's background tile threads in tests.

    The real map widget starts threads that download OpenStreetMap tiles
    and create Tk images off the main thread. Tk is not thread-safe, so
    under CI this intermittently aborts the interpreter, and tests should
    not hit the network anyway. Making the thread targets return at once
    keeps the widget usable (tiles just stay blank).
    """
    try:
        import tkintermapview
    except ImportError:
        return
    cls = tkintermapview.TkinterMapView
    monkeypatch.setattr(cls, "pre_cache", lambda self: None)
    monkeypatch.setattr(cls, "load_images_background", lambda self: None)
