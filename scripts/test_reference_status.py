#!/usr/bin/env python3
"""Tests that AAP-SPEC.md credits the reference implementation with what the broker profile does.

The Reference implementation paragraph of AAP-SPEC.md lists what the reference
implementation provides. The implementation status note of broker profile
Section 14 names the sections of the broker profile that sit outside the
implemented surface. The tests read the sections that note names and check that
the AAP-SPEC paragraph cites each of them and the note itself, and that it does
not credit the whole resolution flow of Section 6, so a section added to the
note fails until the paragraph is changed with it.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

SECTION = r"\d+(?:\.\d+)*"


def paragraph(name, opening):
    """The paragraph of `name` that starts with `opening`, with its whitespace collapsed."""
    text = (ROOT / name).read_text(encoding="utf-8")
    found = [p for p in text.split("\n\n") if p.startswith(opening)]
    if len(found) != 1:
        raise AssertionError(f"{name}: {len(found)} paragraphs start with {opening!r}, want 1")
    return " ".join(found[0].split())


def outside_sections(note):
    """The broker profile sections the implementation status note places outside the surface."""
    return set(re.findall(rf"\bSection ({SECTION})\b", note))


def cited_sections(spec_paragraph):
    """The section numbers the AAP-SPEC paragraph cites with a section sign."""
    return set(re.findall(rf"§({SECTION})\b", spec_paragraph))


def credits_whole_flow(spec_paragraph):
    """True if the paragraph lists the resolution flow of Section 6 without naming its steps."""
    return re.search(r"(?<!steps of )\bthe resolution flow of §6\b", spec_paragraph) is not None


class ReferenceStatusTest(unittest.TestCase):
    def setUp(self):
        self.note = paragraph("AAP-BROKER-PROFILE.md", "**Implementation status.** The list above")
        self.spec = paragraph("AAP-SPEC.md", "**Reference implementation.**")

    def test_note_names_sections_outside_the_surface(self):
        self.assertTrue({"6.8", "6.9", "6.10", "6.13"} <= outside_sections(self.note))

    def test_spec_cites_each_section_outside_the_surface(self):
        missing = sorted(outside_sections(self.note) - cited_sections(self.spec))
        self.assertEqual(missing, [], "AAP-SPEC.md Reference implementation paragraph")

    def test_spec_cites_the_status_note(self):
        self.assertIn("broker profile §14", self.spec)

    def test_spec_does_not_credit_the_whole_resolution_flow(self):
        self.assertFalse(credits_whole_flow(self.spec))

    def test_whole_flow_wording_is_detected(self):
        self.assertTrue(credits_whole_flow(
            "the `grant://` scheme, the resolution flow of §6 of the broker profile, the CPI"))
        self.assertFalse(credits_whole_flow(
            "the worker steps of the resolution flow of §6 of the broker profile"))


if __name__ == "__main__":
    unittest.main()
