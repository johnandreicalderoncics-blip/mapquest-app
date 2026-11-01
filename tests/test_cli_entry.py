"""Tests that the CLI entry point still imports and runs."""

import unittest
from unittest import mock

from backend import api
import main


class StubConsole:
    """Stand-in for display.console: scripted input, recorded output."""

    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.printed: list[str] = []

    def input(self, prompt: str = "") -> str:
        if not self.answers:
            raise EOFError  # matches Rich's console.input on closed stdin
        return self.answers.pop(0)

    def print(self, *args, **kwargs) -> None:
        self.printed.append(" ".join(str(arg) for arg in args))


class CliEntryTests(unittest.TestCase):
    def test_main_module_imports(self) -> None:
        self.assertTrue(callable(main.main))

    def test_main_runs_and_exits_on_quit_without_requests(self) -> None:
        console = StubConsole(["i", "c", "quit"])
        with mock.patch.object(main.config, "get_api_key",
                               return_value="test-key"), \
                mock.patch.object(main.display, "console", console), \
                mock.patch.object(api, "fetch_route") as mocked:
            main.main()  # 'quit' as the location ends the session
        mocked.assert_not_called()
        self.assertTrue(console.printed)  # banner and/or goodbye printed


if __name__ == "__main__":
    unittest.main()
