#!/usr/bin/env python3
"""Tests that examples/ holds a worked example of each binding the broker profile lists.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'

README.md describes examples/ as covering transport bindings. Broker profile
Section 8.5 lists the initial bindings as list items whose bold label names the
binding (**HTTP**, **A2A agent card**, **MCP manifest**). Each label must be named
by a heading of a Markdown file in examples/, outside fenced code blocks, so a
binding added to Section 8.5 without a worked example fails here. CI runs these
tests through validate_examples.py.
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_naming  # noqa: E402

ROOT = check_naming.ROOT
PROFILE = ROOT / "AAP-BROKER-PROFILE.md"
EXAMPLES = ROOT / "examples"

SECTION = re.compile(r"#{1,6}\s+8\.5\s")
SECTION_END = re.compile(r"#{1,6}\s|---\s*$")
BINDING = re.compile(r"\s*[-*]\s+\*\*([^*]+)\*\*")
HEADING = re.compile(r"#{1,6}\s+(.*)")


def initial_bindings(text: str) -> list[str]:
    """Return the bold labels of the list items in broker profile Section 8.5."""
    labels = []
    inside = False
    for line in text.splitlines():
        if not inside:
            inside = SECTION.match(line) is not None
            continue
        if SECTION_END.match(line):
            break
        match = BINDING.match(line)
        if match:
            labels.append(match.group(1))
    return labels


def headings(text: str) -> list[str]:
    """Return the text of each Markdown heading outside fenced code blocks."""
    found = []
    fence = None
    for line in text.splitlines():
        if fence is not None:
            if check_naming.closes(line, fence):
                fence = None
            continue
        fence = check_naming.opening_fence(line)
        if fence is not None:
            continue
        match = HEADING.match(line)
        if match:
            found.append(match.group(1))
    return found


class ExampleBindingsTest(unittest.TestCase):
    def test_profile_lists_the_initial_bindings(self):
        self.assertEqual(
            initial_bindings(PROFILE.read_text(encoding="utf-8")),
            ["HTTP", "A2A agent card", "MCP manifest"],
        )

    def test_each_initial_binding_has_a_worked_example(self):
        example_headings = [
            heading.casefold()
            for path in sorted(EXAMPLES.glob("*.md"))
            for heading in headings(path.read_text(encoding="utf-8"))
        ]
        for label in initial_bindings(PROFILE.read_text(encoding="utf-8")):
            with self.subTest(binding=label):
                self.assertTrue(
                    any(label.casefold() in heading for heading in example_headings),
                    f"no heading in examples/*.md names the {label} binding of "
                    "broker profile Section 8.5",
                )

    def test_headings_skip_fenced_code_blocks(self):
        text = "# Title\n\n```yaml\n# a comment, not a heading\n```\n\n## HTTP binding\n"
        self.assertEqual(headings(text), ["Title", "HTTP binding"])

    def test_bindings_stop_at_the_next_section(self):
        text = ("### 8.5 Bindings\n\n- **HTTP**, a header.\n\n"
                "## 9. Next\n\n- **Not a binding**, later text.\n")
        self.assertEqual(initial_bindings(text), ["HTTP"])


if __name__ == "__main__":
    unittest.main()
