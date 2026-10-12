#!/usr/bin/env python3
"""Tests that the documents name AI Agent Threat Matrix techniques as the matrix does.

examples/orders-db-exchange.md and AAP-BROKER-PROFILE.md Section 12.1 cite
techniques by ID and name. MATRIX_NAMES holds the name each technique's page
at https://threats.opena2a.org/techniques/ carries in its title, so a citation
whose name differs from the page's fails here without a network call.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The title of each technique's page, without " | AI Agent Threat Matrix".
MATRIX_NAMES = {
    "T-3002": "Environment Variable Leakage",
    "T-3003": "Tool Response Credential Capture",
    "T-3006": "Context Window Credential Leak",
    "T-8002": "HTTP Callback",
}

DOCUMENTS = ("examples/orders-db-exchange.md", "AAP-BROKER-PROFILE.md")

# [T-3002](https://threats.opena2a.org/techniques/T-3002) (Name)
LINKED = re.compile(r"\[(T-\d{4})\]\([^)]*\) \(([^)]*)\)")
# **T-3002, Name.**
LISTED = re.compile(r"\*\*(T-\d{4}), ([^*]*)\*\*")


def citations(text):
    """Return (technique ID, cited name) for each technique text cites with a name."""
    return [m.groups() for m in LINKED.finditer(text)] + [
        m.groups() for m in LISTED.finditer(text)]


def names_technique(cited, technique):
    """Whether the cited name starts with the matrix's name for technique, as a whole word."""
    return re.match(re.escape(MATRIX_NAMES[technique]) + r"\b", cited) is not None


class ThreatMatrixNamesTest(unittest.TestCase):
    def test_a_name_other_than_the_matrix_name_is_rejected(self):
        self.assertFalse(names_technique("Environment Variable Exposure", "T-3002"))
        self.assertFalse(names_technique("HTTP Callbacks", "T-8002"))
        self.assertTrue(names_technique("Environment Variable Leakage.", "T-3002"))
        self.assertTrue(names_technique("HTTP Callback exfiltration", "T-8002"))

    def test_each_document_names_each_technique_as_the_matrix_does(self):
        for document in DOCUMENTS:
            found = citations((ROOT / document).read_text(encoding="utf-8"))
            with self.subTest(document=document):
                self.assertEqual({technique for technique, _ in found}, set(MATRIX_NAMES))
            for technique, cited in found:
                with self.subTest(document=document, technique=technique):
                    self.assertTrue(
                        names_technique(cited, technique),
                        f"{document} names {technique} {cited!r}; the matrix names it "
                        f"{MATRIX_NAMES[technique]!r}")


if __name__ == "__main__":
    unittest.main()
