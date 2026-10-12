#!/usr/bin/env python3
"""Tests that the worked example marks the steps the v1 reference does not perform.

examples/orders-db-exchange.md walks the v1 resolution in numbered steps. A step
the v1 reference implementation does not perform carries a "v1:" note, in the
form the example's policy sample uses for `jurisdiction` ("v1: parsed, not
enforced"), so the flow does not present the step as performed. Version
negotiation is also marked as a conformance Level 2 requirement (broker profile
Section 13). The implementation status note of broker profile Section 14 names
the signature on audit records among what its list does not describe.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

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


if __name__ == "__main__":
    unittest.main()
