#!/usr/bin/env python3
"""Tests for check_raw_html.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py.
"""

import contextlib
import io
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_raw_html  # noqa: E402
from check_raw_html import findings  # noqa: E402


class FindingsTest(unittest.TestCase):
    def test_placeholder_in_prose_fails(self):
        text = "Intro.\n\nThe check fails on \"as of <YYYY-MM-DD>\".\n"
        self.assertEqual(findings(text),
                         ["line 3: HTML tag in Markdown prose, not rendered: '<YYYY-MM-DD>'"])

    def test_tags_fail(self):
        for text in ("Set <name> to the agent.", "A break<br/>here.", "Ends </em> here.",
                     'A <a href="x">link</a>.', "A <x-y> tag."):
            with self.subTest(text=text):
                self.assertTrue(findings(text))

    def test_tag_split_across_lines_fails_at_its_first_line(self):
        text = 'Text.\nA <span\nclass="x"> tag.\n'
        self.assertEqual(len(findings(text)), 1)
        self.assertIn("line 2:", findings(text)[0])

    def test_placeholder_in_a_table_row_fails(self):
        self.assertEqual(len(findings("| `x` | MUST | <type> | Shown. |\n")), 1)

    def test_code_span_passes(self):
        for text in ("Fails on `as of <YYYY-MM-DD>`.", "A ``x ` <n> `` span.",
                     "A span `split\nover <two> lines`."):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_code_span_does_not_cross_a_paragraph(self):
        self.assertEqual(len(findings("A `x\n\n<n>` y.\n")), 1)

    def test_text_after_a_code_span_is_checked(self):
        self.assertEqual(findings("A ``x ` <n> `` span and <m>.\n"),
                         ["line 1: HTML tag in Markdown prose, not rendered: '<m>'"])

    def test_fenced_code_block_passes(self):
        for text in ("```\n<name>\n```\n", "~~~json\n<b>\n~~~\n", "- item\n  ```\n  <n>\n  ```\n"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_text_after_a_fenced_code_block_is_checked(self):
        self.assertEqual(len(findings("```\n<a>\n```\nThen <b>.\n")), 1)

    def test_other_angle_brackets_pass(self):
        for text in ("An escaped \\<name> placeholder.", "An autolink <https://example.com>.",
                     "Mail <foo@example.com>.", "A comment <!-- marker --> here.",
                     "A [link](<a b>) destination.", "a < b > c", "1 <2 and 3> 2"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])


class RepositoryDocumentsTest(unittest.TestCase):
    def test_every_markdown_document_is_covered(self):
        names = check_raw_html.documents()
        for name in ("README.md", "AAP-SPEC.md", "AAP-BROKER-PROFILE.md", "CHANGELOG.md"):
            with self.subTest(document=name):
                self.assertIn(name, names)
        self.assertTrue(all(name.endswith(".md") for name in names))

    def test_repository_check_has_no_failures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_raw_html.check(), 0)


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def test_placeholder_in_a_changelog_fails(self):
        (self.root / "CHANGELOG.md").write_text(
            "# Changelog\n\nThe check fails on \"as of <YYYY-MM-DD>\".\n", encoding="utf-8")
        (self.root / "README.md").write_text("Fails on `<name>`.\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_raw_html.check(self.root), 1)
        self.assertIn(
            "FAIL  CHANGELOG.md: line 3: HTML tag in Markdown prose, not rendered: "
            "'<YYYY-MM-DD>'; write the placeholder as a code span (`<name>`) or escape "
            "the bracket (\\<name>)", out.getvalue())
        self.assertIn("ok    README.md: no HTML tag in prose", out.getvalue())

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (3, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_raw_html, "check", return_value=failures):
                    self.assertEqual(check_raw_html.main(), code)


if __name__ == "__main__":
    unittest.main()
