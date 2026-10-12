#!/usr/bin/env python3
"""Tests for the specifications Section 9.4 names as citing its signature gate.

AAP-SPEC section 9.4 is the one home of the family signature gate and names the
specifications that cite it for their own signature arrays rather than restate it.
The names must be those of specifications that do cite it, so the sentence and the
0.5.1-draft changelog entry that describes it are checked against CITING below.
AIP is not in CITING: AIP-SPEC.md does not mention AAP section 9.4. When a
specification adds the citation, add it to CITING and to both sentences.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Each specification that cites AAP section 9.4, with the text file that cites it.
CITING = {
    "ATX": "atx-spec/core.md",
    "ATP": "ATP-SPEC.md",
}

MARKER = "<!-- opena2a-definition: signature-family-gate -->"
SPEC_SENTENCE = re.compile(r"([A-Z][A-Za-z, ]*?) cite this rule for their own signature arrays")
CHANGELOG_CLAUSE = re.compile(r"`HYBRID_INCOMPLETE`\), which ([A-Z][A-Za-z, ]*?) (?:now )?cite\b")


def names(phrase):
    """Return the names in a list such as "ATX, ATP and AIP"."""
    return [name.strip() for name in re.split(r",|\band\b", phrase) if name.strip()]


def gate_paragraph():
    text = (ROOT / "AAP-SPEC.md").read_text(encoding="utf-8")
    start = text.index(MARKER) + len(MARKER)
    return " ".join(text[start:].strip().split("\n\n", 1)[0].split())


def changelog_section(version):
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    start = text.index(f"## [{version}]")
    end = text.find("\n## [", start + 1)
    return " ".join(text[start:end if end != -1 else len(text)].split())


class SignatureGateCitersTest(unittest.TestCase):
    def test_names_reads_each_list_form(self):
        self.assertEqual(names("ATX, ATP and AIP"), ["ATX", "ATP", "AIP"])
        self.assertEqual(names("ATX and ATP"), ["ATX", "ATP"])
        self.assertEqual(names("ATP"), ["ATP"])

    def test_spec_names_the_citing_specifications(self):
        match = SPEC_SENTENCE.search(gate_paragraph())
        self.assertIsNotNone(match, "section 9.4 no longer names the specifications citing it")
        self.assertEqual(sorted(names(match.group(1))), sorted(CITING))

    def test_changelog_entry_names_the_citing_specifications(self):
        match = CHANGELOG_CLAUSE.search(changelog_section("0.5.1-draft"))
        self.assertIsNotNone(match, "the 0.5.1-draft entry no longer names the citing specifications")
        self.assertEqual(sorted(names(match.group(1))), sorted(CITING))


if __name__ == "__main__":
    unittest.main()
