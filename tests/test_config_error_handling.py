"""Comprehensive error handling tests for backend/config.py"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend import config


class ConfigErrorHandlingTests(unittest.TestCase):
    """Test comprehensive error handling in config module."""

    def test_malformed_ini_logs_error_and_returns_none(self) -> None:
        """Test that malformed INI file prints error message."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.ini"
            # Write malformed INI (missing closing bracket)
            config_file.write_text("[graphhopper\nkey = test", encoding="utf-8")
            
            with mock.patch.dict(config.os.environ, {"GRAPHOPPER_KEY": ""}), \
                    mock.patch.object(config, "CONFIG_FILE", config_file):
                result = config.load_api_key()
                self.assertIsNone(result)

    def test_unreadable_config_file_returns_none(self) -> None:
        """Test that unreadable config file is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.ini"
            config_file.write_text("[graphhopper]\nkey = test", encoding="utf-8")
            
            # Mock file to raise exception on read
            with mock.patch.dict(config.os.environ, {"GRAPHOPPER_KEY": ""}), \
                    mock.patch.object(config, "CONFIG_FILE", config_file):
                with mock.patch('configparser.ConfigParser.read', 
                               side_effect=Exception("File read error")):
                    result = config.load_api_key()
                    self.assertIsNone(result)

    def test_missing_config_file_returns_none_no_error(self) -> None:
        """Test that missing config file is handled silently."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "nonexistent.ini"
            
            with mock.patch.dict(config.os.environ, {"GRAPHOPPER_KEY": ""}), \
                    mock.patch.object(config, "CONFIG_FILE", config_file):
                result = config.load_api_key()
                self.assertIsNone(result)

    def test_env_var_read_error_continues_to_config(self) -> None:
        """Test that env var read error doesn't stop config file reading."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.ini"
            config_file.write_text("[graphhopper]\nkey = valid-key", encoding="utf-8")
            
            # Mock environ.get to raise exception
            with mock.patch.object(config.os.environ, 'get',
                                  side_effect=Exception("Env error")), \
                    mock.patch.object(config, "CONFIG_FILE", config_file):
                result = config.load_api_key()
                # Should still read from config file
                self.assertEqual(result, "valid-key")

    def test_config_parser_get_error_returns_none(self) -> None:
        """Test that error extracting key from parser is handled."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.ini"
            config_file.write_text("[graphhopper]\nkey = test", encoding="utf-8")
            
            with mock.patch.dict(config.os.environ, {"GRAPHOPPER_KEY": ""}), \
                    mock.patch.object(config, "CONFIG_FILE", config_file):
                # Mock parser.get to raise exception
                with mock.patch('configparser.ConfigParser.get',
                               side_effect=Exception("Parser error")):
                    result = config.load_api_key()
                    self.assertIsNone(result)

    def test_whitespace_only_env_var_returns_none(self) -> None:
        """Test that whitespace-only env var is treated as missing."""
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "missing.ini"
            
            with mock.patch.dict(config.os.environ, {"GRAPHOPPER_KEY": "   "}), \
                    mock.patch.object(config, "CONFIG_FILE", config_file):
                result = config.load_api_key()
                self.assertIsNone(result)

    def test_get_api_key_handles_load_exception(self) -> None:
        """Test that get_api_key handles exceptions from load_api_key."""
        with mock.patch('backend.config.load_api_key',
                       side_effect=Exception("Unexpected error")):
            with self.assertRaises(SystemExit) as ctx:
                config.get_api_key()
            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
