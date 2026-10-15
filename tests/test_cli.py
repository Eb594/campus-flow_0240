import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import main


def run_cli(inputs):
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as d:
        cwd = os.getcwd()
        os.chdir(d)
        try:
            with mock.patch("builtins.input", side_effect=inputs), \
                 contextlib.redirect_stdout(out):
                main.main()
        finally:
            os.chdir(cwd)
    return out.getvalue()


class TestCLI(unittest.TestCase):
    def test_invalid_menu_choices_do_not_crash(self):
        text = run_cli(["", "abc", "99", "11"])
        self.assertEqual(text.count("Invalid choice"), 3)
        self.assertIn("Thank you", text)

    def test_non_numeric_affected_users_is_friendly(self):
        text = run_cli(["1", "Broken PC", "Hardware", "low", "five", "11"])
        self.assertIn("must be a whole number", text)
        self.assertNotIn("invalid literal", text)

    def test_note_flow_uses_business_layer(self):
        text = run_cli([
            "1", "Broken PC", "Hardware", "low", "1",
            "8", "T001", "first note",
            "8", "T001", "second note",
            "9", "T001",
            "11",
        ])
        self.assertLess(text.index("[1] first note"), text.index("[2] second note"))

    def test_note_errors_are_friendly(self):
        text = run_cli(["8", "T404", "hi", "9", "T404", "11"])
        self.assertEqual(text.count("Error: Ticket T404 was not found."), 2)

    def test_search_reprompts_on_invalid_filters(self):
        text = run_cli([
            "1", "WiFi down", "Network", "high", "12",
            "3", "wifi", "Furniture", "network", "bogus", "open", "", "y",
            "11",
        ])
        self.assertEqual(text.count("Error: Category must be"), 1)
        self.assertEqual(text.count("Error: Status must be"), 1)
        self.assertIn("T001 | WiFi down | Network | critical | open | Unassigned", text)
        self.assertIn("(BY PRIORITY)", text)

    def test_quiz_menu_shows_score(self):
        answers = ["C", "B", "D", "why", "A", "C", "B", "because"]
        text = run_cli(["10"] + answers + ["11"])
        self.assertIn("Final score: 6/6", text)


if __name__ == "__main__":
    unittest.main()