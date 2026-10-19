#!/usr/bin/env python3
"""Tests that AAP-SPEC.md cites the did:opena2a string form rather than restating it.

Section 3.1 of the did:opena2a DID method specification (did-method-opena2a.md) says
that it and Section 3.1.1 are the one home of the `did:opena2a` string form for the
OpenA2A specification family, and that ATX, ATP and AAP cite them rather than restate
the grammar. The tests read AAP-SPEC.md and check that a citation
check_section_citations.py reads names did-method-opena2a with Sections 3.1 and 3.1.1,
that the References section lists the method as [DID-OPENA2A], normative, naming its
text file and its repository, and that no rule of the method's ABNF is restated: no
line of AAP-SPEC.md defines `opena2a-did`, `resource-type` or `resource-id`.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_references  # noqa: E402
import check_section_citations  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = "AAP-SPEC.md"
TEXT = "did-method-opena2a.md"
REPOSITORY = "https://github.com/opena2a-standards/did-method-opena2a"
LABEL = "DID-OPENA2A"
SECTIONS = ("3.1", "3.1.1")

# A line that defines a rule of the method's ABNF (Section 3.1 of did-method-opena2a.md).
GRAMMAR_RULE = re.compile(r"^\s*(opena2a-did|resource-type|resource-id)\s*=", re.MULTILINE)


def spec_text():
    return (ROOT / SPEC).read_text(encoding="utf-8")


def did_method_citations(text):
    """The citations of the DID method that check_section_citations.py reads in text."""
    return [c for c in check_section_citations.citations(SPEC, text) if c.doc.text == TEXT]


class DidSyntaxCitationTest(unittest.TestCase):
    def setUp(self):
        self.text = spec_text()

    def test_spec_cites_sections_3_1_and_3_1_1_of_the_did_method(self):
        cited = [c for c in did_method_citations(self.text) if c.numbers == SECTIONS]
        self.assertTrue(cited, f"{SPEC} has no citation of did-method-opena2a Sections 3.1 and 3.1.1")
        self.assertTrue(all(c.names_text for c in cited))

    def test_references_section_lists_the_did_method_as_normative(self):
        classes = dict(check_references.markdown_references(self.text))
        self.assertEqual(classes.get(LABEL), "normative")

    def test_references_entry_names_the_text_file_and_the_repository(self):
        entry = check_section_citations.reference_entries(self.text).get("DID method", "")
        self.assertIn(TEXT, entry)
        self.assertIn(REPOSITORY, entry)

    def test_the_references_entry_alone_is_not_the_citation(self):
        entry = check_section_citations.reference_entries(self.text).get("DID method", "")
        self.assertEqual(did_method_citations(entry), [])

    def test_grammar_is_not_restated(self):
        match = GRAMMAR_RULE.search(self.text)
        self.assertIsNone(match, f"{SPEC} restates the did:opena2a ABNF rule {match and match.group(1)}")

    def test_grammar_rule_is_detected(self):
        for line in (
            'opena2a-did       = "did:opena2a:" resource-type ":" resource-id [ "#" fragment ]',
            'resource-type     = ALPHA-LOWER *( ALPHA-LOWER / "_" )',
            "resource-id = 1*( unreserved / \":\" / pct-encoded )",
        ):
            with self.subTest(line=line):
                self.assertIsNotNone(GRAMMAR_RULE.search("```\n" + line + "\n```"))
        self.assertIsNone(GRAMMAR_RULE.search("the `resource-type` of a DID (Section 3.1)"))


if __name__ == "__main__":
    unittest.main()
