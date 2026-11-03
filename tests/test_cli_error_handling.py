"""Tests for CLI error handling.

Verifies that the CLI properly handles:
- Keyboard interrupts (Ctrl+C)
- End-of-file conditions (Ctrl+D/Ctrl+Z)
- Unexpected exceptions during execution
- Logging of errors
- Clean exits with appropriate exit codes
"""

import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.frontend.cli import main as cli_main


class TestCLIErrorHandling:
    """Test error handling in CLI main module."""

    def test_keyboard_interrupt_during_input(self):
        """Verify Ctrl+C during location input exits gracefully."""
        with patch('src.frontend.cli.display.console.input', side_effect=KeyboardInterrupt):
            with patch('src.frontend.cli.display.console.print') as mock_print:
                with patch('src.frontend.cli.display.show_banner'):
                    with patch('backend.config.get_api_key', return_value='test-key'):
                        exit_code = cli_main.main()
                        
        assert exit_code == 0
        # Should print goodbye message
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('Goodbye' in str(call) for call in calls)

    def test_eof_error_during_choose(self):
        """Verify EOF (Ctrl+D/Ctrl+Z) returns default choice in choose()."""
        # EOFError during choose() should return the default value
        with patch('src.frontend.cli.display.console.input', side_effect=EOFError):
            result = cli_main.choose("test prompt", {"a": "apple"}, "default")
        
        assert result == "default"

    def test_api_key_configuration_error(self):
        """Verify error when API key configuration fails."""
        with patch('backend.config.get_api_key', side_effect=Exception('Config error')):
            with patch('src.frontend.cli.display.console.print') as mock_print:
                with patch('src.frontend.cli.display.show_banner'):
                    with patch('logging.error'):
                        exit_code = cli_main.main()
                        
        assert exit_code == 1
        # Should print error message
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('Error loading API key' in str(call) for call in calls)

    def test_api_key_not_found_exits_with_code_1(self):
        """Verify missing API key returns exit code 1."""
        with patch('backend.config.get_api_key', side_effect=SystemExit(1)):
            with patch('src.frontend.cli.display.show_banner'):
                exit_code = cli_main.main()
                
        assert exit_code == 1

    def test_unexpected_error_during_startup(self):
        """Verify unexpected errors during startup are caught."""
        with patch('src.frontend.cli.display.show_banner', side_effect=RuntimeError('Startup error')):
            with patch('src.frontend.cli.display.console.print') as mock_print:
                with patch('logging.error'):
                    exit_code = cli_main.main()
                    
        assert exit_code == 1
        # Should print unexpected error message
        calls = [str(call) for call in mock_print.call_args_list]
        assert any('unexpected error' in str(call).lower() for call in calls)

    def test_logging_setup_with_valid_dir(self):
        """Verify logging setup succeeds with valid directory."""
        # Just verify it doesn't raise
        cli_main.setup_logging()
        # If we reach here, it worked
        assert True

    def test_logging_setup_failure_does_not_crash(self):
        """Verify logging setup failure doesn't prevent app from running."""
        # Save original
        original_log_dir = cli_main.LOG_DIR
        
        try:
            # Set LOG_DIR to a path that will fail
            cli_main.LOG_DIR = Path("/nonexistent/path/that/will/fail")
            
            # This should not raise - just print a warning
            cli_main.setup_logging()
            
        finally:
            # Restore original
            cli_main.LOG_DIR = original_log_dir
        
        # If we reach here without exception, test passes
        assert True

    def test_ask_location_with_quit_raises_keyboard_interrupt(self):
        """Verify typing 'quit' raises KeyboardInterrupt."""
        with patch('src.frontend.cli.display.console.input', return_value='quit'):
            with pytest.raises(KeyboardInterrupt):
                cli_main.ask_location("test prompt")

    def test_ask_location_with_q_raises_keyboard_interrupt(self):
        """Verify typing 'q' raises KeyboardInterrupt."""
        with patch('src.frontend.cli.display.console.input', return_value='q'):
            with pytest.raises(KeyboardInterrupt):
                cli_main.ask_location("test prompt")

    def test_ask_location_returns_normal_input(self):
        """Verify normal location input is returned."""
        with patch('src.frontend.cli.display.console.input', return_value='Miami'):
            result = cli_main.ask_location("test prompt")
        assert result == 'Miami'

    def test_main_returns_correct_exit_code_on_success(self):
        """Verify main returns 0 on successful execution with immediate exit."""
        with patch('backend.config.get_api_key', return_value='test-key'):
            with patch('src.frontend.cli.display.show_banner'):
                with patch('src.frontend.cli.display.console.print'):
                    # Immediately exit with KeyboardInterrupt during first input
                    with patch('src.frontend.cli.display.console.input', side_effect=KeyboardInterrupt):
                        exit_code = cli_main.main()
                        
        assert exit_code == 0

    def test_choose_handles_eof_gracefully(self):
        """Verify choose() handles EOFError by returning default."""
        with patch('src.frontend.cli.display.console.input', side_effect=EOFError):
            result = cli_main.choose("Test prompt", {"a": "apple", "b": "banana"}, "default_value")
        
        assert result == "default_value"

    def test_choose_handles_empty_input_as_default(self):
        """Verify choose() treats empty input as default selection."""
        with patch('src.frontend.cli.display.console.input', return_value=''):
            result = cli_main.choose("Test prompt", {"a": "apple"}, "default_value")
        
        assert result == "default_value"

    def test_choose_validates_input(self):
        """Verify choose() rejects invalid input and prompts again."""
        # First invalid, then valid
        with patch('src.frontend.cli.display.console.input', side_effect=['invalid', 'a']):
            with patch('src.frontend.cli.display.console.print'):
                result = cli_main.choose("Test prompt", {"a": "apple"}, "default")
        
        assert result == "apple"
