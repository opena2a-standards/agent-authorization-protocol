#!/usr/bin/env python3
"""Tests that the decision notes in decisions/ say who recommended what in plain terms.

A reader outside the project cannot resolve a group the notes do not define or
an abbreviation for a role, so a note states what was recommended rather than
crediting a recommendation to a group by name ("the authors' recommendation"),
and does not qualify a threat model with an abbreviation ("XYZ threat model").
A note records what was decided and when, not who approved it or was asked to:
it does not credit a go-ahead, gate, approval or sign-off to someone by a
possessive ("Xyz's go-ahead") or say from whom something was requested.
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
CREDITED_APPROVAL = re.compile(
    r"\b\w+['’]s (?:go-ahead|gate|approval|sign-off)\b|\brequested from\b"
)


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

    def test_no_approval_is_credited_to_someone(self):
        for name, text in notes().items():
            with self.subTest(note=name):
                self.assertEqual(CREDITED_APPROVAL.findall(text), [])

    def test_patterns_match_the_forms_they_reject(self):
        self.assertTrue(CREDITED_RECOMMENDATION.search("proceeded on the authors' recommendation"))
        self.assertFalse(CREDITED_RECOMMENDATION.search("proceeded on the recommendation"))
        self.assertTrue(QUALIFIED_THREAT_MODEL.search("- XYZ threat model: tokens are short"))
        self.assertFalse(QUALIFIED_THREAT_MODEL.search("- Threat model: tokens are short"))
        self.assertTrue(CREDITED_APPROVAL.search("adoption window — with Xyz's go-ahead to continue"))
        self.assertTrue(CREDITED_APPROVAL.search("resubmits only after this lands (Xyz’s gate)"))
        self.assertTrue(CREDITED_APPROVAL.search("the contested knob — ratification requested from Xyz"))
        self.assertFalse(CREDITED_APPROVAL.search("adoption window — on 2026-07-16."))
        self.assertFalse(CREDITED_APPROVAL.search("(a condition set on 2026-07-16)."))
        self.assertFalse(CREDITED_APPROVAL.search("plus the broker's foreign-lane default"))


if __name__ == "__main__":
    unittest.main()
