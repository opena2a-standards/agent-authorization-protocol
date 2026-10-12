#!/usr/bin/env python3
"""Tests that the decision notes in decisions/ say who recommended what in plain terms.

A reader outside the project cannot resolve a group the notes do not define or
an abbreviation for a role, so a note states what was recommended rather than
crediting a recommendation to a group by name ("the authors' recommendation"),
and does not qualify a threat model with an abbreviation ("XYZ threat model").
Line breaks are read as spaces, so a phrase split across two lines is found.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DECISIONS = ROOT / "decisions"

# A note that must be present, so a move or rename cannot drop it from the tests.
REQUIRED = "2026-07-16-mldsa65-serialization-profile.md"

CREDITED_RECOMMENDATION = re.compile(r"\b\w+s' recommendation\b")
QUALIFIED_THREAT_MODEL = re.compile(r"\b[A-Z]{2,} threat model\b")


def notes():
    """Each decision note and its text with every run of whitespace read as one space."""
    return {
        path.name: " ".join(path.read_text(encoding="utf-8").split())
        for path in sorted(DECISIONS.glob("*.md"))
    }


class DecisionNoteTermsTest(unittest.TestCase):
    def test_required_note_is_read(self):
        self.assertIn(REQUIRED, notes())

    def test_no_recommendation_is_credited_to_a_group(self):
        for name, text in notes().items():
            with self.subTest(note=name):
                self.assertEqual(CREDITED_RECOMMENDATION.findall(text), [])

    def test_no_threat_model_is_qualified_by_an_abbreviation(self):
        for name, text in notes().items():
            with self.subTest(note=name):
                self.assertEqual(QUALIFIED_THREAT_MODEL.findall(text), [])

    def test_patterns_match_the_forms_they_reject(self):
        self.assertTrue(CREDITED_RECOMMENDATION.search("proceeded on the authors' recommendation"))
        self.assertFalse(CREDITED_RECOMMENDATION.search("proceeded on the recommendation"))
        self.assertTrue(QUALIFIED_THREAT_MODEL.search("- XYZ threat model: tokens are short"))
        self.assertFalse(QUALIFIED_THREAT_MODEL.search("- Threat model: tokens are short"))


if __name__ == "__main__":
    unittest.main()
