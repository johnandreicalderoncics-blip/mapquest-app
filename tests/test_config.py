"""Tests for backend/config.py: key resolution and the CLI exit contract."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from backend import config


class LoadApiKeyTests(unittest.TestCase):
    """load_api_key() must never print or exit - it returns None."""

    def run_load(self, env_value: str, ini_key: str | None) -> str | None:
        """Call load_api_key with controlled env and config.ini."""
        env = {"GRAPHOPPER_KEY": env_value}
        with mock.patch.dict(config.os.environ, env), \
                tempfile.TemporaryDirectory() as tmp:
            if ini_key is None:
                config_file = Path(tmp) / "missing.ini"
            else:
                config_file = Path(tmp) / "config.ini"
                config_file.write_text(
                    f"[graphhopper]\nkey = {ini_key}\n",
                    encoding="utf-8")
            with mock.patch.object(config, "CONFIG_FILE", config_file):
                return config.load_api_key()

    def test_env_var_wins_and_is_stripped(self) -> None:
        self.assertEqual(self.run_load("  test-key  ", None), "test-key")

    def test_ini_key_used_when_env_empty(self) -> None:
        self.assertEqual(self.run_load("", "ini-key"), "ini-key")

    def test_missing_everything_returns_none(self) -> None:
        self.assertIsNone(self.run_load("", None))

    def test_placeholder_key_returns_none(self) -> None:
        self.assertIsNone(self.run_load("", "YOUR_KEY_HERE"))


class GetApiKeyCliContractTests(unittest.TestCase):
    """The CLI path must keep its original setup-message behavior."""

    def test_get_api_key_returns_key_when_configured(self) -> None:
        with mock.patch.dict(config.os.environ,
                             {"GRAPHOPPER_KEY": "test-key"}):
            self.assertEqual(config.get_api_key(), "test-key")

    def test_get_api_key_prints_setup_message_and_exits(self) -> None:
        buffer = io.StringIO()
        with mock.patch.dict(config.os.environ, {"GRAPHOPPER_KEY": ""}), \
                mock.patch.object(config, "CONFIG_FILE",
                                  Path("definitely-missing.ini")), \
                  redirect_stdout(buffer):
            with self.assertRaises(SystemExit) as ctx:
                config.get_api_key()
        self.assertEqual(ctx.exception.code, 1)
        self.assertTrue(buffer.getvalue().startswith(
            "No GraphHopper API key found."))


if __name__ == "__main__":
    unittest.main()
