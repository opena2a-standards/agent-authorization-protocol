#!/usr/bin/env python3
"""Tests that the worked example marks the steps the v1 reference does not perform.

examples/orders-db-exchange.md walks the v1 resolution in numbered steps. A step
the v1 reference implementation does not perform carries a "v1:" note, in the
form the example's policy sample uses for `jurisdiction` ("v1: parsed, not
enforced"), so the flow does not present the step as performed. Version
negotiation is also marked as a conformance Level 2 requirement (broker profile
Section 13). The implementation status note of broker profile Section 14 names
the signature on audit records among what its list does not describe.

The paragraph after the flow cites, for each of the three steps, the broker
profile section that defines it: the first broker profile section the paragraph
names after "(step N)" has a numbered heading, and its text, up to the next
heading, holds a phrase that defines the step (the heading "Versioning and
negotiation" for step 2, which Section 13, the conformance table, does not
hold). Each section number in the paragraph, written after "Section" or "§",
is written next to the broker profile's name, so check_section_citations.py,
which reads a number only there, reads every one.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_section_citations  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "orders-db-exchange.md"
PROFILE = ROOT / "AAP-BROKER-PROFILE.md"

FLOW_HEADING = "## 3. Resolution flow (Section 6 of the broker profile)"
STEP = re.compile(r"│\s*(\d+)\.\s")

# A phrase that names a step the v1 reference does not perform, and the notes
# the step containing it carries.
UNPERFORMED = {
    "negotiate AAP version": ("Level 2", "v1:"),
    "rotating delegated key": ("v1:",),
    "signed audit": ("v1:",),
}

# Each step the paragraph after the flow cites, and the phrases of the text of
# the broker profile section that defines it.
DEFINED_BY = {
    2: ("Versioning and negotiation",),
    4: ("IdP signing key", "rotates"),
    7: ("signed audit log",),
}
STATUS_PARAGRAPH = "A `v1:` note marks"
# "(step 4) is described in broker profile Section 11": a step and the first
# broker profile section named after it, before the next step.
STEP_SECTION = re.compile(
    r"\(step (\d+)\)(?:(?!\(step ).)*?\b[Bb]roker profile Section (\d+(?:\.\d+)*)"
)
# A section number written after "Section", "Sections", "§" or "§§", the markers
# check_section_citations.py reads ("§99" is a section number too).
SECTION_NUMBER = re.compile(r"(?:\bSections?\s+|§§?\s*)(\d+(?:\.\d+)*)")


def flow_steps():
    """Return the resolution flow's steps as {number: text}, continuation lines joined."""
    lines = EXAMPLE.read_text(encoding="utf-8").splitlines()
    start = lines.index(FLOW_HEADING)
    fence = next(i for i in range(start, len(lines)) if lines[i].startswith("```"))
    end = next(i for i in range(fence + 1, len(lines)) if lines[i].startswith("```"))
    steps, current = {}, None
    for line in lines[fence + 1:end]:
        match = STEP.search(line)
        if match:
            current = int(match.group(1))
            steps[current] = line[match.end():]
        elif current is not None and line.lstrip().startswith("│"):
            steps[current] += " " + line.lstrip()[1:].strip()
        else:
            current = None
    return steps


def implementation_status_note():
    text = PROFILE.read_text(encoding="utf-8")
    section = text[text.index("## 14. Reference Implementation"):]
    section = section[:section.index("\n## 15.")]
    note = section[section.index("**Implementation status.**"):]
    return " ".join(note[:note.index("\n\n")].split())


def status_paragraph():
    """The paragraph after the flow that cites the sections, line breaks read as spaces."""
    text = EXAMPLE.read_text(encoding="utf-8")
    start = text.index(STATUS_PARAGRAPH)
    return " ".join(text[start:text.index("\n\n", start)].split())


def profile_section(number):
    """The heading and text of broker profile Section `number` up to the next heading, or None."""
    lines = PROFILE.read_text(encoding="utf-8").splitlines()
    heading = re.compile(rf"#+ {re.escape(number)}\.? ")
    start = next((i for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    return " ".join(" ".join(lines[start:end]).split())


def written_section_numbers(paragraph):
    """Every section number written in `paragraph`, named or not."""
    return sorted(SECTION_NUMBER.findall(paragraph))


def read_section_numbers(paragraph):
    """The broker profile section numbers check_section_citations.py reads in `paragraph`."""
    return sorted(
        number
        for cite in check_section_citations.citations(EXAMPLE.name, paragraph)
        if cite.doc.text == PROFILE.name
        for number in cite.numbers
    )


class WorkedExampleStatusTest(unittest.TestCase):
    def test_flow_has_seven_numbered_steps(self):
        self.assertEqual(sorted(flow_steps()), list(range(1, 8)))

    def test_each_unperformed_step_carries_its_note(self):
        steps = flow_steps()
        for phrase, notes in UNPERFORMED.items():
            holding = [n for n, text in steps.items() if phrase in text]
            with self.subTest(phrase=phrase):
                self.assertEqual(len(holding), 1, f"{phrase!r} is in steps {holding}")
                for note in notes:
                    self.assertIn(note, steps[holding[0]])

    def test_implementation_status_names_the_audit_signature(self):
        note = implementation_status_note()
        self.assertIn("Outside that list are:", note)
        self.assertRegex(note, r"signature on audit records of Section 6\.7")

    def test_each_unperformed_step_cites_the_section_that_defines_it(self):
        cited = {int(step): number for step, number in STEP_SECTION.findall(status_paragraph())}
        for step, phrases in DEFINED_BY.items():
            with self.subTest(step=step):
                self.assertIn(step, cited, f"no broker profile section is cited for step {step}")
                section = profile_section(cited[step])
                self.assertIsNotNone(section, f"the broker profile has no Section {cited[step]}")
                for phrase in phrases:
                    self.assertTrue(
                        phrase in section,
                        f"Section {cited[step]} does not hold {phrase!r}, which defines step {step}",
                    )

    def test_the_citation_check_reads_each_section_number_of_the_paragraph(self):
        paragraph = status_paragraph()
        self.assertEqual(read_section_numbers(paragraph), written_section_numbers(paragraph))

    def test_a_section_number_written_with_the_section_sign_is_counted(self):
        # "§99" without the broker profile's name is not read by the citation
        # check, so the comparison above must see it and fail.
        paragraph = status_paragraph()
        self.assertIn("targets Level 1.", paragraph)
        for sign in ("§99", "§ 99", "§§99"):
            with self.subTest(sign=sign):
                unnamed = paragraph.replace("targets Level 1.", f"targets Level 1 ({sign}).")
                self.assertIn("99", written_section_numbers(unnamed))
                self.assertNotIn("99", read_section_numbers(unnamed))
                self.assertNotEqual(
                    read_section_numbers(unnamed), written_section_numbers(unnamed)
                )


if __name__ == "__main__":
    unittest.main()
