"""pytest fixtures for the Flask web tests.

One app instance with TESTING=True serves every route test; the autouse
fixture keeps GRAPHOPPER_KEY out of the environment so tests decide the
key state themselves.
"""

import pytest

from app import create_app


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
