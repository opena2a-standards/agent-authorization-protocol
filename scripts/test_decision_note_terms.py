#!/usr/bin/env python3
"""Tests that the decision notes in decisions/ say who recommended what in plain terms.

A reader outside the project cannot resolve a group the notes do not define or
an abbreviation for a role, so a note states what was recommended rather than
crediting a recommendation by a possessive ("the authors' recommendation"),
and does not qualify a threat model with an abbreviation ("XYZ threat model").
A note records what was decided and when, not who approved it or was asked to.

The tests find these forms:

- a possessive, singular or plural ("the group's", "the editors'"), before
  recommendation, go-ahead, approval or sign-off, either directly or with one
  word between ("Xyz's explicit go-ahead");
- the same before gate, only when the word in the possessive starts with a
  capital letter, A to Z ("Xyz's gate"): a note also uses "gate" for a
  verification gate ("the verifier's gate"), which credits no one;
- "requested from", "requested of" and "approved by";
- two or more capital letters directly before "threat model".

The capital letter is the only sign of a name the tests read, so a common noun
written with one before gate is found as a name is: at the start of a sentence
or a list item ("Verifier's gate rejects a missing family") and in a heading
in title case ("The Verifier's Gate"). A note writes such a noun in lower
case, with a word before it where it would start a sentence ("The verifier's
gate rejects a missing family"); the failure of the test on a possessive
before gate prints that rewrite.

The five nouns are matched in the singular and the plural, and they and the
three phrases in any letter case. The apostrophe is straight or curly. The
contractions it's, that's, there's, here's, what's, who's and let's are not
read as possessives. Line breaks are read as spaces, so a phrase split across
two lines is found.

The patterns read characters, not grammar, so the tests also find two forms
that credit no one, each where a possessive would be found: a word ending in
s and closed by a quotation mark, straight or curly, which is read as a plural
possessive ("the 'editors' approval"), and a contraction other than the seven
above, which is read as a singular possessive ("she's the approval"). A note
that carries one rewords it.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DECISIONS = ROOT / "decisions"

# A note that must be present, so a move or rename cannot drop it from the tests.
REQUIRED = "2026-07-16-mldsa65-serialization-profile.md"

# "there's" and the like are contractions, not possessives.
NOT_A_CONTRACTION = r"(?!(?i:it|that|there|here|what|who|let)['’]s\b)"
# The end of a possessive, singular or plural, with a straight or a curly
# apostrophe ("Xyz's", "the editors’"), then at most one word before the noun.
POSSESSIVE_END = r"(?:['’]s|s['’])(?: [\w-]+)? "

CREDITED_RECOMMENDATION = re.compile(
    rf"\b{NOT_A_CONTRACTION}\w+{POSSESSIVE_END}(?i:recommendations?)\b"
)
QUALIFIED_THREAT_MODEL = re.compile(r"\b[A-Z]{2,} threat model\b")
CREDITED_APPROVAL = re.compile(
    rf"\b{NOT_A_CONTRACTION}\w+{POSSESSIVE_END}(?i:go-aheads?|approvals?|sign-offs?)\b"
    rf"|\b{NOT_A_CONTRACTION}[A-Z]\w*{POSSESSIVE_END}(?i:gates?)\b"
    r"|\b(?i:requested from|requested of|approved by)\b"
)
# A form CREDITED_APPROVAL found that is a possessive before gate.
GATE_FORM = re.compile(r"(?i:gates?)\Z")
# What a failure on that form adds: a capital letter at the start of a sentence
# reads as a name, so the writer of a note is told how to write the sentence.
GATE_REWRITE = (
    'a possessive before "gate" is read as a credit when its word starts with a'
    " capital letter, wherever the word stands; write the noun of a verification"
    " gate in lower case, with a word before it at the start of a sentence"
    ' ("The verifier\'s gate")'
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

    def test_no_credited_recommendation_form_is_present(self):
        for name, text in notes().items():
            with self.subTest(note=name):
                self.assertEqual(CREDITED_RECOMMENDATION.findall(text), [])

    def test_no_threat_model_is_qualified_by_an_abbreviation(self):
        for name, text in notes().items():
            with self.subTest(note=name):
                self.assertEqual(QUALIFIED_THREAT_MODEL.findall(text), [])

    def assert_no_credited_approval(self, text):
        """Fail on the credited approvals in `text`; a gate among them adds its rewrite."""
        found = CREDITED_APPROVAL.findall(text)
        gate = any(GATE_FORM.search(form) for form in found)
        self.assertEqual(found, [], GATE_REWRITE if gate else None)

    def test_no_credited_approval_form_is_present(self):
        for name, text in notes().items():
            with self.subTest(note=name):
                self.assert_no_credited_approval(text)

    def test_a_gate_that_starts_a_sentence_fails_with_its_rewrite(self):
        for text in (
            "Verifier's gate rejects a missing family",
            "A missing family fails. Verifier’s gates reject it.",
        ):
            with self.subTest(text=text):
                with self.assertRaises(AssertionError) as raised:
                    self.assert_no_credited_approval(text)
                self.assertIn(GATE_REWRITE, str(raised.exception))

    def test_the_rewrite_of_a_gate_passes(self):
        self.assert_no_credited_approval("The verifier's gate rejects a missing family")

    def test_a_form_other_than_a_gate_fails_without_the_rewrite(self):
        with self.assertRaises(AssertionError) as raised:
            self.assert_no_credited_approval("option (B) was approved by Xyz")
        self.assertNotIn(GATE_REWRITE, str(raised.exception))


class PatternFormsTest(unittest.TestCase):
    """Each form a pattern matches has a phrase here, so a pattern that drops one fails."""

    def assert_forms(self, pattern, matched, not_matched):
        for phrase in matched:
            with self.subTest(matched=phrase):
                self.assertIsNotNone(pattern.search(phrase))
        for phrase in not_matched:
            with self.subTest(not_matched=phrase):
                self.assertIsNone(pattern.search(phrase))

    def test_credited_recommendation_forms(self):
        self.assert_forms(
            CREDITED_RECOMMENDATION,
            matched=(
                "proceeded on the authors' recommendation",
                "proceeded on the authors’ recommendation",
                "proceeded on the group's recommendation",
                "proceeded on the group’s recommendation",
                "proceeded on the authors' final recommendation",
                "proceeded on the group's long-standing recommendation",
                "proceeded on the group's Recommendation",
                "proceeded on the authors' recommendations",
            ),
            not_matched=(
                "proceeded on the recommendation",
                "the knob's blast radius is one recommendation",
                "there's no recommendation to flip the default",
            ),
        )

    def test_qualified_threat_model_forms(self):
        self.assert_forms(
            QUALIFIED_THREAT_MODEL,
            matched=(
                "- XYZ threat model: tokens are short",
                "- XY threat model: tokens are short",
            ),
            not_matched=(
                "- Threat model: tokens are short",
                "- A threat model: tokens are short",
            ),
        )

    def test_credited_approval_forms_with_a_possessive(self):
        for noun in ("go-ahead", "approval", "sign-off"):
            self.assert_forms(
                CREDITED_APPROVAL,
                matched=(
                    f"adoption window — with Xyz's {noun} to continue",
                    f"adoption window — with Xyz’s {noun} to continue",
                    f"adoption window — with the editors' {noun} to continue",
                    f"adoption window — with the editors’ {noun} to continue",
                    f"adoption window — with Xyz's explicit {noun} to continue",
                    f"adoption window — with Xyz's {noun.capitalize()} to continue",
                    f"adoption window — with Xyz's {noun}s to continue",
                ),
                not_matched=(
                    f"the knob's blast radius needs no {noun}",
                    f"there's no {noun} step in the exchange",
                ),
            )

    def test_credited_approval_forms_with_a_gate(self):
        self.assert_forms(
            CREDITED_APPROVAL,
            matched=(
                "resubmits only after this lands (Xyz's gate)",
                "resubmits only after this lands (Xyz’s gate)",
                "resubmits only after this lands (the Editors' gate)",
                "resubmits only after this lands (the Editors’ gate)",
                "resubmits only after this lands (Xyz's final gate)",
                "resubmits only after this lands (Xyz's Gate)",
                "resubmits only after this lands (Xyz's gates)",
                # A common noun written with a capital letter is found as a name is.
                "Verifier's gate rejects a missing family",
                "A missing family fails. Verifier's gate rejects it.",
                "- Verifier's gate: rejects a missing family",
                "## The Verifier's Gate",
            ),
            not_matched=(
                "The verifier's gate rejects a missing family",
                "the verifier's gate rejects a missing family",
                "the verifier’s family gate rejects a missing family",
                "both verifiers' gates reject a missing family",
                "It's the gate condition that is satisfied",
            ),
        )

    def test_credited_approval_forms_without_a_possessive(self):
        self.assert_forms(
            CREDITED_APPROVAL,
            matched=(
                "the contested knob — ratification requested from Xyz",
                "Requested from Xyz.",
                "ratification was requested of Xyz",
                "Requested of Xyz.",
                "option (B) was approved by Xyz",
                "Approved by Xyz.",
            ),
            not_matched=(
                "adoption window — on 2026-07-16.",
                "(a condition set on 2026-07-16).",
                "plus the broker's foreign-lane default",
            ),
        )

    def test_a_contraction_is_not_read_as_a_possessive(self):
        for word in ("it", "that", "there", "here", "what", "who", "let"):
            self.assert_forms(
                CREDITED_RECOMMENDATION,
                matched=(),
                not_matched=(
                    f"{word}'s the recommendation",
                    f"{word.capitalize()}’s the recommendation",
                ),
            )
            self.assert_forms(
                CREDITED_APPROVAL,
                matched=(),
                not_matched=(
                    f"{word}'s the approval",
                    f"{word.capitalize()}’s the approval",
                    f"{word.capitalize()}'s the gate",
                    f"{word.capitalize()}’s the gate",
                ),
            )

    def test_a_capital_letter_before_gate_is_read_as_a_name_and_described(self):
        description = " ".join(__doc__.split())
        self.assertIn(
            "The capital letter is the only sign of a name the tests read", description
        )
        # A name in lower case is not found; a common noun with a capital letter is.
        self.assertIsNone(CREDITED_APPROVAL.search("after this lands (xyz's gate)"))
        for phrase in ("Verifier's gate rejects a missing family", "The Verifier's Gate"):
            with self.subTest(phrase=phrase):
                self.assertIsNotNone(CREDITED_APPROVAL.search(phrase))
                self.assertIn(phrase, description)
        rewrite = "The verifier's gate rejects a missing family"
        self.assertIsNone(CREDITED_APPROVAL.search(rewrite))
        self.assertIn(rewrite, description)
        # The description says the failure prints that rewrite.
        self.assertIn("(\"The verifier's gate\")", GATE_REWRITE)

    def test_forms_that_credit_no_one_are_found_and_described(self):
        description = " ".join(__doc__.split())
        for phrase in ("the 'editors' approval", "she's the approval"):
            with self.subTest(phrase=phrase):
                self.assertIsNotNone(CREDITED_APPROVAL.search(phrase))
                self.assertIn(phrase, description)
        self.assert_forms(
            CREDITED_APPROVAL,
            matched=(
                "he quoted the ‘editors’ approval",
                "he quoted the 'editors' final approval",
                "He's the gate",
            ),
            not_matched=(),
        )
        self.assert_forms(
            CREDITED_RECOMMENDATION,
            matched=(
                "he quoted the 'authors' recommendation",
                "she's the recommendation",
            ),
            not_matched=(),
        )


if __name__ == "__main__":
    unittest.main()
