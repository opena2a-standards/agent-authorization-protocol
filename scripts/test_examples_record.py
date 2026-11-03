#!/usr/bin/env python3
"""Tests for docs/examples.json. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py. docs/examples.json lists, under the
path of a document, a command that document shows: the heading of the section
that holds it, the command, and, for a command that is not run, the reason
(`noexec`). The tests check, for each entry, that the document exists, that one
of its headings is the entry's section, and that a line of a fenced block in that
section is the command, so an entry fails here when its command moves to another
document or under another heading and the entry does not move with it. A section
runs from its heading to the next heading of the same or a higher level, and a
line inside a fenced block, such as a shell comment that starts with `#`, is not
read as a heading.
"""

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORD = ROOT / "docs" / "examples.json"

# An ATX heading: one to six `#`, the title, then an optional closing run of `#`.
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
# A fence line: three or more backticks or tildes, then the info string, if any.
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def lines_read(text):
    """Yield each line of `text` that is not a fence line, with True when it is inside a fenced block.

    A block closes at a fence line of the character that opened it, at least as
    long, with nothing after it but whitespace.
    """
    fence = None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
            else:
                yield line, False
        elif (match and match.group(1)[0] == fence[0]
              and len(match.group(1)) >= len(fence) and not match.group(2).strip()):
            fence = None
        else:
            yield line, True


def section(text, title):
    """The lines read under the first heading of `text` titled `title`, or None when no heading is.

    The section ends at the next heading of the same or a higher level.
    """
    found, level = None, 0
    for line, fenced in lines_read(text):
        heading = None if fenced else HEADING.match(line)
        if found is None:
            if heading and heading.group(2) == title:
                found, level = [], len(heading.group(1))
        elif heading and len(heading.group(1)) <= level:
            break
        else:
            found.append((line, fenced))
    return found


def problems(record, read):
    """One message per document or entry of `record` that does not show the command where it says.

    `read` returns the text of a document named by its path from the repository
    root, or None when there is no such file.
    """
    found = []
    for document, entries in record.items():
        text = read(document)
        if text is None:
            found.append(f"{document}: no such file")
            continue
        for entry in entries:
            lines = section(text, entry["section"])
            if lines is None:
                found.append(f'{document}: no heading "{entry["section"]}"')
            elif entry["command"] not in [line.strip() for line, fenced in lines if fenced]:
                found.append(
                    f'{document}: no fenced line "{entry["command"]}" under "{entry["section"]}"')
    return found


def read_document(name):
    """The text of the file at `name` from the repository root, or None when there is none."""
    path = ROOT / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


PAGE = (
    "# Page\n\n"
    "## Run it\n\n"
    "```bash\n"
    "# from the clone\n"
    "node run.mjs\n"
    "```\n\n"
    "### Reading the result\n\n"
    "```\n"
    "node read.mjs\n"
    "```\n\n"
    "## Later\n\n"
    "node prose.mjs\n\n"
    "~~~\n"
    "```\n"
    "node later.mjs\n"
    "~~~\n"
)


def record_entry(title, command):
    return {"section": title, "command": command, "noexec": "A reason."}


class ProblemsTest(unittest.TestCase):
    def check(self, record):
        return problems(record, {"page.md": PAGE, "other.md": "# Other\n\nText.\n"}.get)

    def test_a_command_on_a_fenced_line_of_its_section_passes(self):
        self.assertEqual(self.check({"page.md": [record_entry("Run it", "node run.mjs")]}), [])

    def test_a_comment_line_in_a_fenced_block_is_not_a_heading(self):
        self.assertIsNone(section(PAGE, "from the clone"))
        self.assertIn(("node run.mjs", True), section(PAGE, "Run it"))

    def test_a_subsection_is_part_of_its_section(self):
        self.assertEqual(self.check({"page.md": [record_entry("Run it", "node read.mjs")]}), [])

    def test_a_document_that_is_not_there_is_found(self):
        self.assertEqual(
            self.check({"README.md": [record_entry("Run it", "node run.mjs")]}),
            ["README.md: no such file"])

    def test_a_document_without_the_heading_is_found(self):
        self.assertEqual(
            self.check({"other.md": [record_entry("Run it", "node run.mjs")]}),
            ['other.md: no heading "Run it"'])

    def test_a_command_under_another_heading_is_found(self):
        self.assertEqual(
            self.check({"page.md": [record_entry("Later", "node run.mjs")]}),
            ['page.md: no fenced line "node run.mjs" under "Later"'])

    def test_a_section_ends_at_the_next_heading_of_its_level(self):
        self.assertEqual(
            self.check({"page.md": [record_entry("Run it", "node later.mjs")]}),
            ['page.md: no fenced line "node later.mjs" under "Run it"'])

    def test_a_command_outside_a_fenced_block_is_found(self):
        self.assertEqual(
            self.check({"page.md": [record_entry("Later", "node prose.mjs")]}),
            ['page.md: no fenced line "node prose.mjs" under "Later"'])

    def test_a_block_closes_only_at_a_fence_of_its_own_character(self):
        self.assertIn(("```", True), section(PAGE, "Later"))
        self.assertEqual(self.check({"page.md": [record_entry("Later", "node later.mjs")]}), [])

    def test_a_shorter_fence_or_one_with_an_info_string_does_not_close_a_block(self):
        text = "## Run it\n\n````\n```\n````bash\nnode run.mjs\n````\n\n# Run it\n"
        self.assertEqual(
            section(text, "Run it"),
            [("", False), ("```", True), ("````bash", True), ("node run.mjs", True), ("", False)])


class RecordTest(unittest.TestCase):
    def test_each_entry_names_the_document_and_section_that_show_its_command(self):
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(problems(record, read_document), [])


if __name__ == "__main__":
    unittest.main()
