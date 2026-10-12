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

import ast
import pathlib
import re
import string
import subprocess
import sys
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
    " capital letter, A to Z, wherever the word stands; write the noun of a"
    " verification gate in lower case, with a word before it at the start of a"
    ' sentence ("The verifier\'s gate")'
)

# What marks a changelog entry as one the tests read: the path of this file
# with a backtick directly before it and directly after it.
PATH_IN_BACKTICKS = "`scripts/test_decision_note_terms.py`"
# A noun or a phrase CREDITED_RECOMMENDATION and CREDITED_APPROVAL find in any
# letter case: the five nouns, singular or plural, and the three phrases.
ANY_CASE_TERM = re.compile(
    r"\b(?i:recommendations?|go-aheads?|approvals?|sign-offs?|gates?"
    r"|requested from|requested of|approved by)\b"
)
# What a changelog sentence on QUALIFIED_THREAT_MODEL names. That check is
# case-sensitive: its abbreviation is two or more capital letters.
THREAT_MODEL = re.compile(r"(?i)\bthreat model\b")
CASE_SENSITIVE = re.compile(r"(?i)\b(?:is|are) case[- ]sensitive\b")
# What a failure on a sentence that says case-sensitive adds: where the one
# statement the tests pass goes.
CASE_SENSITIVE_REWRITE = (
    "the checks find their five nouns and three phrases in any letter case; a"
    " statement that the check on an abbreviation before threat model is"
    " case-sensitive goes in a sentence that names threat model and none of them"
)
# The statement of the rule on a possessive before gate. The pattern reads A to
# Z, so the statement goes on "A to Z", with or without a comma before it.
CAPITAL_LETTER = "starts with a capital letter"
CAPITAL_LETTER_NOT_A_TO_Z = re.compile(rf"{CAPITAL_LETTER}(?!,? A to Z\b)")
# A changelog sentence that has both, in any letter case, says a common noun
# with a capital letter is found before gate. An entry is read on its own, so
# such a sentence names the letters the pattern reads as well.
COMMON_NOUN_WITH_A_CAPITAL = ("common noun", "capital letter")
A_TO_Z = re.compile(r"\bA to Z\b")
# What the failure says when no sentence of an entry read has both of
# COMMON_NOUN_WITH_A_CAPITAL.
NO_SENTENCE_ON_A_COMMON_NOUN = (
    'no sentence of an entry read has "common noun" and "capital letter"; the sentence'
    " that says a common noun with a capital letter is found before gate has both and"
    ' "A to Z"'
)
# What a changelog sentence on the entries the tests read names, and how it
# names PATH_IN_BACKTICKS.
UNRELEASED = "[Unreleased]"
BETWEEN_BACKTICKS = "directly between two backticks"
# What the failure says when no sentence of the entries read names UNRELEASED.
NO_SENTENCE_ON_THE_ENTRIES_READ = (
    f"no sentence of an entry read names {UNRELEASED}; the sentence that says"
    f' which entries the tests read names it and has "{BETWEEN_BACKTICKS}"'
)


def notes():
    """Each decision note and its text with every run of whitespace read as one space."""
    return {
        path.name: " ".join(path.read_text(encoding="utf-8").split())
        for path in sorted(DECISIONS.glob("*.md"))
    }


def read_description():
    """The description of these tests, read from this file as __doc__ holds it.

    The file is parsed with optimize=0: on Python 3.14, ast.parse also drops
    the docstrings when they are stripped (python3 -OO, PYTHONOPTIMIZE=2).
    """
    path = pathlib.Path(__file__)
    source = path.read_text(encoding="utf-8")
    tree = compile(source, path, "exec", ast.PyCF_ONLY_AST, dont_inherit=True, optimize=0)
    return ast.get_docstring(tree, clean=False)


# __doc__ is None when docstrings are stripped (python3 -OO, PYTHONOPTIMIZE=2).
# The tests that check the description read __doc__, so it is read from this
# file instead.
if __doc__ is None:
    __doc__ = read_description()


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
        # The whole paragraph of the description on a possessive before gate, so
        # no clause of it can be reworded, and no sentence added to it, with every
        # test passing. Each clause is checked against the patterns below.
        paragraph = (
            "The capital letter is the only sign of a name the tests read, so a common"
            " noun written with one before gate is found as a name is: at the start of"
            " a sentence or a list item (\"Verifier's gate rejects a missing family\")"
            " and in a heading in title case (\"The Verifier's Gate\"). A note writes"
            " such a noun in lower case, with a word before it where it would start a"
            " sentence (\"The verifier's gate rejects a missing family\"); the failure"
            " of the test on a possessive before gate prints that rewrite."
        )
        paragraphs = [" ".join(block.split()) for block in __doc__.split("\n\n")]
        self.assertIn(paragraph, paragraphs)
        # A name in lower case is not found; a common noun with a capital letter is,
        # as a name is: at the start of a sentence or a list item and in a heading.
        self.assertIsNone(CREDITED_APPROVAL.search("after this lands (xyz's gate)"))
        for phrase in (
            "Verifier's gate rejects a missing family",
            "A missing family fails. Verifier's gate rejects it.",
            "- Verifier's gate: rejects a missing family",
            "The Verifier's Gate",
        ):
            with self.subTest(phrase=phrase):
                self.assertIsNotNone(CREDITED_APPROVAL.search(phrase))
        # The noun in lower case with a word before it is not found.
        self.assertIsNone(
            CREDITED_APPROVAL.search("The verifier's gate rejects a missing family")
        )
        # The failure prints that rewrite: the failure message is GATE_REWRITE
        # (test_a_gate_that_starts_a_sentence_fails_with_its_rewrite), which
        # carries it.
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


def entries_read(changelog):
    """Each entry under [Unreleased] in `changelog` that carries PATH_IN_BACKTICKS, as one line.

    An entry that names this file only in another way is not returned: without
    backticks, or with a space or other text between a backtick and the path.
    """
    start = changelog.index("## [Unreleased]")
    end = changelog.find("\n## [", start + 1)
    return [
        " ".join(entry.split())
        for entry in re.split(r"\n(?=- )", changelog[start:end])
        if PATH_IN_BACKTICKS in entry
    ]


def changelog_entries():
    """The entries of CHANGELOG.md that entries_read() returns."""
    return entries_read((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))


def sentences(entry):
    """The parts of `entry` the tests read as its sentences.

    An entry is split only where a period and then whitespace come directly
    before a capital letter A to Z, a backtick, a straight double quotation
    mark or an opening parenthesis.
    """
    return re.split(r"(?<=\.)\s+(?=[A-Z`\"(])", entry)


def case_sensitive_claims(entry):
    """The sentences of `entry` that match CASE_SENSITIVE, but for one on threat model.

    A sentence on threat model names THREAT_MODEL and no ANY_CASE_TERM. A
    sentence that names neither is returned as one that names an ANY_CASE_TERM
    is: it can speak of the check the sentence before it names ("Its match is
    case-sensitive").
    """
    return [
        sentence
        for sentence in sentences(entry)
        if CASE_SENSITIVE.search(sentence)
        and (ANY_CASE_TERM.search(sentence) or not THREAT_MODEL.search(sentence))
    ]


def capital_letter_claims(entry):
    """The sentences of `entry` that state CAPITAL_LETTER and do not go on "A to Z"."""
    return [
        sentence for sentence in sentences(entry) if CAPITAL_LETTER_NOT_A_TO_Z.search(sentence)
    ]


def common_noun_statements(entry):
    """The sentences of `entry` that have each of COMMON_NOUN_WITH_A_CAPITAL, in any letter case.

    A sentence can start with either ("Common nouns with a capital letter").
    """
    return [
        sentence
        for sentence in sentences(entry)
        if all(words in sentence.lower() for words in COMMON_NOUN_WITH_A_CAPITAL)
    ]


def common_noun_claims(entry):
    """The common_noun_statements() of `entry` that do not have A_TO_Z."""
    return [
        sentence for sentence in common_noun_statements(entry) if not A_TO_Z.search(sentence)
    ]


def changelog_with(entry):
    """A changelog whose one entry under [Unreleased] is `entry`."""
    return (
        "# Changelog\n\n## [Unreleased]\n\n### Changed\n\n"
        f"{entry}\n\n"
        "## [0.1.0-draft] - 2026-06-01\n\n### Added\n\n"
        f"- {PATH_IN_BACKTICKS} is named in a released section.\n"
    )


class ChangelogEntriesTest(unittest.TestCase):
    """The changelog entries entries_read() returns describe the checks as the patterns do."""

    def test_entries_are_read(self):
        entries = changelog_entries()
        self.assertTrue(any('"requested from"' in entry for entry in entries))

    def test_an_entry_is_read_only_with_the_path_directly_between_two_backticks(self):
        path = "scripts/test_decision_note_terms.py"
        self.assertEqual(PATH_IN_BACKTICKS, f"`{path}`")
        for entry in (
            f"- The match of `{path}` changed.",
            f"- The match of ``{path}`` changed.",
            f"- The match of {path} changed:\n  `{path}` finds one more form.",
        ):
            with self.subTest(read=entry):
                self.assertEqual(entries_read(changelog_with(entry)), [" ".join(entry.split())])
        for entry in (
            f"- The match of {path} changed.",
            f"- The match of `` {path} `` changed.",
            f"- The match of `` {path} `` is case-sensitive before gate.",
            f"- The tests run with `python3 {path}`.",
            f"- The tests in `{path} ` changed.",
        ):
            with self.subTest(not_read=entry):
                self.assertEqual(entries_read(changelog_with(entry)), [])

    def assert_the_entries_read_are_stated_with_the_backticks(self, entries):
        """Fail on a sentence of `entries` that names UNRELEASED and not the backticks.

        Fail as well when no sentence of `entries` names UNRELEASED.
        """
        stated = [
            sentence for entry in entries for sentence in sentences(entry) if UNRELEASED in sentence
        ]
        self.assertNotEqual(stated, [], NO_SENTENCE_ON_THE_ENTRIES_READ)
        self.assertEqual(
            [sentence for sentence in stated if BETWEEN_BACKTICKS not in sentence],
            [],
            f'write "{BETWEEN_BACKTICKS}"',
        )

    def test_a_sentence_on_each_entry_read_names_the_backticks(self):
        self.assert_the_entries_read_are_stated_with_the_backticks(changelog_entries())

    def test_a_reworded_or_missing_sentence_on_the_entries_read_fails(self):
        stated = (
            f"- Tests of {PATH_IN_BACKTICKS} read each entry under {UNRELEASED} that has the"
            f" path {BETWEEN_BACKTICKS}."
        )
        self.assert_the_entries_read_are_stated_with_the_backticks([stated])
        # A sentence that names the section in other words names the backticks too.
        for reworded in (
            f"- Tests of {PATH_IN_BACKTICKS} read every entry under {UNRELEASED} that"
            " contains the code span.",
            f"- Tests of {PATH_IN_BACKTICKS} read the entries of {UNRELEASED} that name it.",
        ):
            with self.subTest(fails=reworded):
                with self.assertRaises(AssertionError) as raised:
                    self.assert_the_entries_read_are_stated_with_the_backticks([stated, reworded])
                self.assertIn(f'write "{BETWEEN_BACKTICKS}"', str(raised.exception))
        # No sentence names the section: the test fails, where it passed.
        for entries in ([], [f"- {PATH_IN_BACKTICKS} finds one more form. No note changes."]):
            with self.subTest(fails=entries):
                with self.assertRaises(AssertionError) as raised:
                    self.assert_the_entries_read_are_stated_with_the_backticks(entries)
                self.assertIn(NO_SENTENCE_ON_THE_ENTRIES_READ, str(raised.exception))

    def test_a_sentence_ends_where_the_split_is_described(self):
        first = f"- {PATH_IN_BACKTICKS} finds go-ahead in any letter case."
        # A period and then whitespace end a sentence before a capital letter A to
        # Z, a backtick, a straight double quotation mark and an opening
        # parenthesis.
        for second in (
            "The patterns are unchanged.",
            "`XY threat model` is found.",
            '"XY threat model" is found.',
            "(The patterns are unchanged.)",
        ):
            with self.subTest(split_before=second[0]):
                self.assertEqual(sentences(f"{first} {second}"), [first, second])
                self.assertEqual(sentences(f"{first}\n  {second}"), [first, second])
        # They end none before a lower-case letter, a digit, a capital letter
        # outside A to Z, a curly or a single quotation mark or an opening
        # bracket.
        for second in (
            "the patterns are unchanged.",
            "24 tests pass.",
            "Émile's gate is not found.",
            "“XY threat model” is found.",
            "'XY threat model' is found.",
            "[XY] threat model is not found.",
        ):
            with self.subTest(no_split_before=second[0]):
                self.assertEqual(sentences(f"{first} {second}"), [f"{first} {second}"])
        # Nor is a sentence ended by a period with no whitespace after it, or by
        # whitespace with another character than a period before it.
        for entry in (
            "- The suffix of scripts/x.Py is not read.",
            "- Is go-ahead found? The patterns are unchanged.",
            "- The check finds go-ahead; The patterns are unchanged.",
            '- The check finds "go-ahead." The patterns are unchanged.',
            "- The check finds go-ahead (in any letter case.) The patterns are unchanged.",
        ):
            with self.subTest(one_sentence=entry):
                self.assertEqual(sentences(entry), [entry])
        # Each printable ASCII character other than whitespace is read in both
        # places. Directly after the whitespace, a sentence ends before each
        # capital letter A to Z and the other three, and before no other
        # character: no hyphen, asterisk or "<". Directly before it, a sentence
        # ends after a period and after no other character: no "!" or ":".
        printable = [character for character in string.printable if not character.isspace()]
        split_before = string.ascii_uppercase + '`"('
        for character in printable:
            second = f"{character}XY is found."
            for space in (" ", "\n  "):
                entry = f"{first}{space}{second}"
                with self.subTest(after_whitespace=character, space=space):
                    expected = [first, second] if character in split_before else [entry]
                    self.assertEqual(sentences(entry), expected)
        for character in printable:
            entry = f"- The check finds go-ahead{character} The patterns are unchanged."
            with self.subTest(before_whitespace=character):
                expected = (
                    ["- The check finds go-ahead.", "The patterns are unchanged."]
                    if character == "."
                    else [entry]
                )
                self.assertEqual(sentences(entry), expected)
        # The tests read the sentences apart: a statement on threat model after a
        # sentence that names go-ahead passes with each of the four at its start,
        # and fails where the two are one sentence.
        for second in (
            "The check on an abbreviation before threat model is case-sensitive.",
            "`XY threat model` is found and `xy threat model` is not: the check is"
            " case-sensitive.",
            '"XY threat model" is found and "xy threat model" is not: the check is'
            " case-sensitive.",
            "(The check on an abbreviation before threat model is case-sensitive.)",
        ):
            with self.subTest(read_apart=second):
                self.assertEqual(case_sensitive_claims(f"{first} {second}"), [])
        unsplit = f"{first} the check on an abbreviation before threat model is case-sensitive."
        self.assertEqual(case_sensitive_claims(unsplit), [unsplit])

    def test_a_sentence_of_an_entry_read_says_case_sensitive_only_on_threat_model(self):
        self.assertIsNotNone(CREDITED_RECOMMENDATION.search("on the group's RECOMMENDATION"))
        for phrase in ("with Xyz's Go-Ahead", "REQUESTED FROM Xyz", "with Xyz's GATE"):
            with self.subTest(phrase=phrase):
                self.assertIsNotNone(CREDITED_APPROVAL.search(phrase))
        for entry in changelog_entries():
            with self.subTest(entry=entry[:80]):
                self.assertEqual(case_sensitive_claims(entry), [], CASE_SENSITIVE_REWRITE)

    def test_a_sentence_says_case_sensitive_only_with_threat_model_and_no_term(self):
        # The check on an abbreviation before threat model is case-sensitive, so
        # an entry can say so in a sentence that names threat model, in any letter
        # case, and no noun or phrase the checks find in any letter case.
        self.assertIsNotNone(QUALIFIED_THREAT_MODEL.search("- XYZ threat model: tokens"))
        self.assertIsNone(QUALIFIED_THREAT_MODEL.search("- xyz threat model: tokens"))
        on_threat_model = "The check on an abbreviation before threat model is case-sensitive."
        for entry in (
            f"- {PATH_IN_BACKTICKS}: the check on an abbreviation before threat model"
            " is case-sensitive.",
            f"- {PATH_IN_BACKTICKS} finds go-ahead in any letter case. {on_threat_model}",
            f"- {PATH_IN_BACKTICKS} changed. The matches before Threat Model ARE Case Sensitive.",
        ):
            with self.subTest(passes=entry):
                self.assertEqual(case_sensitive_claims(entry), [])
        # Each of the five nouns and the three phrases is found in any letter
        # case, so a sentence that names one fails: in any letter case, for a noun
        # in the plural as well, and with threat model named beside it.
        nouns = ("recommendation", "go-ahead", "approval", "sign-off", "gate")
        phrases = ("requested from", "requested of", "approved by")
        self.assertIsNotNone(CREDITED_RECOMMENDATION.search(f"on the group's {nouns[0]}"))
        for found in (*(f"with Xyz's {noun}" for noun in nouns[1:]), *phrases):
            with self.subTest(found=found):
                self.assertIsNotNone(CREDITED_APPROVAL.search(found))
        for term in (*nouns, *(f"{noun}s" for noun in nouns), *phrases):
            for sentence in (
                f"The match of {term} is case-sensitive.",
                f"The match of {term.upper()} IS Case Sensitive.",
                f'The matches of "{term}" and the like are case-sensitive.',
                f"The match of {term}, as the one before threat model, is case-sensitive.",
            ):
                with self.subTest(fails=sentence):
                    self.assertEqual(
                        case_sensitive_claims(f"- {PATH_IN_BACKTICKS} changed. {sentence}"),
                        [sentence],
                    )
        # A sentence that names neither fails as well: it can speak of the check
        # the sentence before it names.
        for sentence in ("Its match is case-sensitive.", "It is case-sensitive."):
            with self.subTest(fails=sentence):
                self.assertEqual(
                    case_sensitive_claims(
                        f"- {PATH_IN_BACKTICKS} finds go-ahead in any letter case. {sentence}"
                    ),
                    [sentence],
                )
        # The patterns read characters, not grammar: a sentence that names a term
        # fails whatever it calls case-sensitive, and one that names threat model
        # and no term passes whatever it calls case-sensitive.
        both = "- The approval check is unchanged, and the check on threat model is case-sensitive."
        self.assertEqual(case_sensitive_claims(both), [both])
        other = "- The check on threat model is unchanged, and the other check is case-sensitive."
        self.assertEqual(case_sensitive_claims(other), [])

    def test_an_entry_read_that_lists_gate_names_the_capital_letter(self):
        self.assertIsNone(CREDITED_APPROVAL.search("the verifier's gate rejects it"))
        self.assertIsNotNone(CREDITED_APPROVAL.search("Xyz's gate"))
        for entry in changelog_entries():
            for sentence in sentences(entry):
                if re.search(r"\bgate\b", sentence) and re.search(
                    r"\b(?:go-ahead|approval|sign-off)\b", sentence
                ):
                    with self.subTest(sentence=sentence):
                        self.assertIn("capital letter", sentence)

    def test_the_capital_letter_rule_is_stated_with_a_to_z(self):
        # The pattern reads A to Z: a capital letter outside that range is not
        # found ("É" is E with an acute accent).
        self.assertIsNotNone(CREDITED_APPROVAL.search("with Xyz's gate"))
        self.assertIsNone(CREDITED_APPROVAL.search("with Émile's gate"))
        self.assertTrue("É".isupper())
        # The description and the printed rewrite say so where they state the rule.
        description = " ".join(__doc__.split())
        self.assertIn(f"{CAPITAL_LETTER}, A to Z", description)
        self.assertEqual(capital_letter_claims(description), [])
        self.assertIn(f"{CAPITAL_LETTER}, A to Z", GATE_REWRITE)
        self.assertEqual(capital_letter_claims(GATE_REWRITE), [])
        # So does each sentence of an entry read that states it.
        for entry in changelog_entries():
            with self.subTest(entry=entry[:80]):
                self.assertEqual(
                    capital_letter_claims(entry), [], f'write "{CAPITAL_LETTER}, A to Z"'
                )
        stated = f"A possessive before gate is found when its word {CAPITAL_LETTER}"
        for sentence in (f"{stated}, A to Z.", f"{stated} A to Z, before gate."):
            with self.subTest(passes=sentence):
                self.assertEqual(capital_letter_claims(f"- {sentence}"), [])
        for sentence in (f"{stated}.", f"{stated}, before gate.", f"{stated}, A to Zeta."):
            with self.subTest(fails=sentence):
                self.assertEqual(capital_letter_claims(f"- {sentence}"), [f"- {sentence}"])

    def assert_a_common_noun_is_stated_with_a_to_z(self, entries):
        """Fail on a common_noun_claims() sentence of `entries`.

        Fail as well when no sentence of `entries` has both of COMMON_NOUN_WITH_A_CAPITAL.
        """
        stated = [sentence for entry in entries for sentence in common_noun_statements(entry)]
        self.assertNotEqual(stated, [], NO_SENTENCE_ON_A_COMMON_NOUN)
        self.assertEqual(
            [sentence for entry in entries for sentence in common_noun_claims(entry)],
            [],
            'write "capital letter, A to Z"',
        )

    def test_a_common_noun_with_a_capital_letter_is_stated_with_a_to_z(self):
        # A common noun before gate is found as a name is only when its first
        # letter is one of A to Z ("É" is E with an acute accent).
        self.assertIsNotNone(CREDITED_APPROVAL.search("Verifier's gate rejects a missing family"))
        self.assertIsNone(CREDITED_APPROVAL.search("Église's gate rejects a missing family"))
        self.assertTrue("É".isupper())
        # Each sentence of an entry read that says such a noun is found names
        # those letters, and at least one sentence says it.
        self.assert_a_common_noun_is_stated_with_a_to_z(changelog_entries())
        found = "a common noun with a capital letter"
        for sentence in (
            f"The check finds {found}, A to Z, before gate.",
            "The capital letter, A to Z, is the only sign of a name, so a common noun"
            " written with one is found.",
            # The two are read in any letter case, so a sentence can start with either.
            "Common nouns with a capital letter, A to Z, before gate are found as names are.",
            "Capital letters, A to Z, start the common nouns found before gate.",
            # A sentence with one of the two is not read as such a statement.
            "A common noun in lower case before gate is not found.",
            "A sentence ends before a capital letter.",
        ):
            with self.subTest(passes=sentence):
                self.assertEqual(
                    common_noun_claims(f"- {PATH_IN_BACKTICKS} changed. {sentence}"), []
                )
        for sentence in (
            f"The check finds {found} before gate.",
            "The capital letter is the only sign of a name, so a common noun written"
            " with one is found.",
            f"The check finds {found}, A to Zeta, before gate.",
            "Common nouns with a capital letter before gate are found as names are.",
            "Capital letters start the common nouns found before gate.",
            "A COMMON NOUN with a CAPITAL LETTER before gate is found.",
        ):
            with self.subTest(fails=sentence):
                self.assertEqual(
                    common_noun_claims(f"- {PATH_IN_BACKTICKS} changed. {sentence}"),
                    [sentence],
                )

    def test_a_missing_sentence_on_a_common_noun_fails_with_what_to_write(self):
        stated = (
            f"- {PATH_IN_BACKTICKS} finds a common noun with a capital letter, A to Z,"
            " before gate."
        )
        self.assert_a_common_noun_is_stated_with_a_to_z([stated])
        # No sentence has both words: the failure names the missing sentence.
        for entries in (
            [],
            [f"- {PATH_IN_BACKTICKS} finds one more form. No note changes."],
            [stated.replace("common noun", "common word")],
            [
                f"- {PATH_IN_BACKTICKS} finds a common noun before gate.",
                f"- {PATH_IN_BACKTICKS} finds a word with a capital letter, A to Z.",
            ],
        ):
            with self.subTest(fails=entries):
                with self.assertRaises(AssertionError) as raised:
                    self.assert_a_common_noun_is_stated_with_a_to_z(entries)
                self.assertIn(NO_SENTENCE_ON_A_COMMON_NOUN, str(raised.exception))
        # A sentence with both and not A to Z: the failure says what to write.
        without_a_to_z = f"- {PATH_IN_BACKTICKS} finds a common noun with a capital letter."
        with self.assertRaises(AssertionError) as raised:
            self.assert_a_common_noun_is_stated_with_a_to_z([stated, without_a_to_z])
        self.assertIn('write "capital letter, A to Z"', str(raised.exception))
        self.assertNotIn(NO_SENTENCE_ON_A_COMMON_NOUN, str(raised.exception))


class StrippedDocstringsTest(unittest.TestCase):
    def test_the_description_read_from_this_file_is_the_docstring(self):
        self.assertEqual(read_description(), __doc__)

    def test_the_description_is_read_when_docstrings_are_stripped(self):
        # python3 -OO and PYTHONOPTIMIZE=2 set __doc__ to None; the tests that read
        # the description still run and pass.
        here = pathlib.Path(__file__).resolve()
        tests = [
            f"{here.stem}.PatternFormsTest.{name}"
            for name in (
                "test_a_capital_letter_before_gate_is_read_as_a_name_and_described",
                "test_forms_that_credit_no_one_are_found_and_described",
            )
        ]
        tests.append(
            f"{here.stem}.ChangelogEntriesTest.test_the_capital_letter_rule_is_stated_with_a_to_z"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-E", "-OO", "-m", "unittest", *tests],
            cwd=here.parent, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Ran 3 tests", result.stderr)


if __name__ == "__main__":
    unittest.main()
