#!/usr/bin/env python3
"""Tests for the list of initial bindings in the broker profile's transport section.

The section "Pluggable transport and discovery" of AAP-BROKER-PROFILE.md lists where
a broker receives an ATX. The ATX specification names both members the list uses: its
`core.md` presents the ATX in an `Agent-Trust-Credential` HTTP header (sections 1.2
and 3.2) and reads it from the `atx` field of an A2A agent card (section 3.2).
ATP-SPEC.md does not name the header, and the `atp` object of its agent card (section
3.4) has the members `did`, `trustProof` and `trustAuthorityDid`. The tests read the
list in this repository only: the section numbers and member names of `core.md` and
ATP-SPEC.md are stated here from those texts, and neither text is fetched.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

PROFILE = "AAP-BROKER-PROFILE.md"
SECTION_TITLE = "Pluggable transport and discovery"

# How the profile cites a section of `core.md` (its References entry names the file).
ATX_HEADER_CITATION = "the ATX specification, `core.md` §1.2 and §3.2"
ATX_FIELD_CITATION = "the ATX specification, `core.md` §3.2"


def bindings():
    """Return {label: text} for the list items of the section, in document order.

    An item is "- **label**, text"; the text runs to the next item or blank line and
    is returned with each run of whitespace, line breaks included, as one space.
    """
    profile = (ROOT / PROFILE).read_text(encoding="utf-8")
    section = re.search(
        rf"^#+ [\d.]+ {re.escape(SECTION_TITLE)}\n(.*?)(?=^#+ |^---$)",
        profile,
        re.MULTILINE | re.DOTALL,
    )
    if section is None:
        return {}
    items = re.findall(
        r"^- \*\*(.+?)\*\*, (.*?)(?=^- |^\s*$)",
        section.group(1),
        re.MULTILINE | re.DOTALL,
    )
    return {label: " ".join(text.split()) for label, text in items}


class TransportBindingsTest(unittest.TestCase):
    def setUp(self):
        self.bindings = bindings()

    def test_the_section_lists_the_three_initial_bindings(self):
        self.assertEqual(list(self.bindings), ["HTTP", "A2A agent card", "MCP manifest"])

    def test_the_http_binding_cites_the_atx_specification_for_the_header(self):
        text = self.bindings["HTTP"]
        self.assertIn("`Agent-Trust-Credential` header", text)
        self.assertIn(ATX_HEADER_CITATION, text)
        self.assertNotRegex(text, r"\bATP\b")

    def test_the_agent_card_binding_names_the_atx_field(self):
        text = self.bindings["A2A agent card"]
        self.assertIn("ATX carried in the `atx` field of the agent card", text)
        self.assertIn(ATX_FIELD_CITATION, text)

    def test_the_agent_card_binding_does_not_place_the_atx_in_the_atp_object(self):
        text = self.bindings["A2A agent card"]
        self.assertNotRegex(text, r"ATX (?:\w+ )?(?:under|in|inside|within) the `atp` object")


if __name__ == "__main__":
    unittest.main()
