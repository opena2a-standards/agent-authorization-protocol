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

The worked example examples/transport-bindings.md presents the ATX over each binding
of the list, so its HTTP and A2A agent card sections are held to the same two facts.

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

EXAMPLE = "examples/transport-bindings.md"
# The example has no References section, so its citations name the text file.
EXAMPLE_HEADER_CITATION = "`atx-spec/core.md` §1.2 and §3.2"
EXAMPLE_FIELD_CITATION = "`atx-spec/core.md` §3.2"

# A phrase that places the ATX in the card's `atp` object.
ATX_IN_ATP = r"ATX (?:\w+ )?(?:under|in|inside|within) the `atp` object"


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


def example_sections():
    """Return {heading: text} for the level-2 sections of the example, in document order.

    The text runs to the next level-2 heading and is returned with each run of
    whitespace, line breaks included, as one space.
    """
    example = (ROOT / EXAMPLE).read_text(encoding="utf-8")
    parts = re.split(r"^## (.+)\n", example, flags=re.MULTILINE)
    return {
        heading: " ".join(text.split())
        for heading, text in zip(parts[1::2], parts[2::2])
    }


def summary_row(label):
    """Return the cells of the example's table row whose first cell is the label."""
    example = (ROOT / EXAMPLE).read_text(encoding="utf-8")
    for line in example.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0] == label:
            return cells
    return []


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
        self.assertNotRegex(text, ATX_IN_ATP)


class TransportBindingsExampleTest(unittest.TestCase):
    def setUp(self):
        self.sections = example_sections()

    def section(self, prefix):
        """Return (heading, text) of the one example section whose heading starts so."""
        found = [(h, t) for h, t in self.sections.items() if h.startswith(prefix)]
        self.assertEqual(len(found), 1, f"sections of {EXAMPLE} starting {prefix!r}")
        return found[0]

    def test_the_http_section_cites_the_atx_specification_for_the_header(self):
        _, text = self.section("HTTP binding")
        self.assertIn("`Agent-Trust-Credential` request header", text)
        self.assertIn(EXAMPLE_HEADER_CITATION, text)
        self.assertNotRegex(text, r"\bATP\b")

    def test_the_agent_card_section_reads_the_atx_from_the_atx_field(self):
        heading, text = self.section("A2A agent card binding")
        self.assertIn("the `atx` field", heading)
        self.assertNotIn("`atp`", heading)
        first_sentence = text.split(". ", 1)[0]
        self.assertIn("the `atx` field", first_sentence)
        self.assertNotIn("`atp`", first_sentence)
        self.assertIn(EXAMPLE_FIELD_CITATION, text)
        self.assertIn('"atx": ', text)
        self.assertNotRegex(text, r'"atp": \{[^}]*\bATX\b')
        self.assertIn("**The card's `atx` field**: the ATX", text)
        self.assertNotRegex(text, ATX_IN_ATP)

    def test_the_summary_row_of_the_agent_card_names_the_atx_field(self):
        cells = summary_row("A2A agent card")
        self.assertEqual(len(cells), 4, f"the A2A agent card row of {EXAMPLE}")
        where, _, reads = cells[1], cells[2], cells[3]
        for cell in (where, reads):
            self.assertIn("`atx` field", cell)
            self.assertNotIn("`atp`", cell)

    def test_no_sentence_of_the_example_places_the_atx_in_the_atp_object(self):
        text = " ".join(self.sections.values())
        self.assertNotRegex(text, ATX_IN_ATP)
        self.assertNotRegex(text, r"\bas in ATP\b")


if __name__ == "__main__":
    unittest.main()
