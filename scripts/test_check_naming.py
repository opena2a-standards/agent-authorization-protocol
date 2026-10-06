#!/usr/bin/env python3
"""Tests for check_naming.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_naming  # noqa: E402
from check_naming import first_use_error  # noqa: E402


class FirstUseTest(unittest.TestCase):
    def test_expanded_first_use_passes(self):
        text = "Intro.\nOpenA2A AIM (Agent Identity Management) supplies X.\nAIM does Y.\n"
        self.assertIsNone(first_use_error(text))

    def test_bare_first_use_fails(self):
        text = "Reuse the existing AIM signed-audit path.\n"
        self.assertIn("line 1", first_use_error(text))

    def test_expansion_without_organization_fails(self):
        text = "AIM (Agent Identity Management) supplies X.\n"
        self.assertIsNotNone(first_use_error(text))

    def test_bare_use_before_expansion_on_same_line_fails(self):
        text = "AIM and OpenA2A AIM (Agent Identity Management).\n"
        self.assertIsNotNone(first_use_error(text))

    def test_navigation_bar_is_not_a_use(self):
        text = (
            "> **OpenA2A specs** · [AIP](https://example.org) · [AIM](https://example.org)\n"
            "The OpenA2A AIM (Agent Identity Management) decorator.\n"
        )
        self.assertIsNone(first_use_error(text))

    def test_other_acronyms_are_not_a_use(self):
        text = "AIMS and AIMED are other words.\nThe AIM decorator.\n"
        self.assertIn("line 2", first_use_error(text))

    def test_document_without_the_name_passes(self):
        self.assertIsNone(first_use_error("No product name here.\n"))


class ListedDocumentsTest(unittest.TestCase):
    def test_every_listed_document_passes(self):
        for name in check_naming.DOCUMENTS:
            with self.subTest(document=name):
                text = (check_naming.ROOT / name).read_text(encoding="utf-8")
                self.assertIsNone(first_use_error(text))


if __name__ == "__main__":
    unittest.main()
