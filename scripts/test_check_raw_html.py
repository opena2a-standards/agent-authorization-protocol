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

    def test_processing_instruction_declaration_and_cdata_fail(self):
        # CommonMark reads each as raw HTML: an html_block on its own line,
        # html_inline in a paragraph.
        for text, raw in (("<?php echo 1; ?>\n", "<?php echo 1; ?>"),
                          ("<!DOCTYPE html>\n", "<!DOCTYPE html>"),
                          ("<![CDATA[x]]>\n", "<![CDATA[x]]>"),
                          ("A <?x?> here.\n", "<?x?>"),
                          ("A <!DOCTYPE html> here.\n", "<!DOCTYPE html>"),
                          ("A <![CDATA[x]]> here.\n", "<![CDATA[x]]>"),
                          ("A <?x\ny?> here.\n", "<?x y?>")):
            with self.subTest(text=text):
                self.assertEqual(findings(text),
                                 [f"line 1: HTML tag in Markdown prose, not rendered: {raw!r}"])

    def test_raw_html_does_not_cross_a_blank_line(self):
        # A blank line ends the paragraph, so CommonMark reads no raw HTML here.
        for text in ('A <span\n\nclass="x"> tag.\n', 'A <a title="x\n\ny"> tag.\n',
                     "A <a\n \n> tag.\n", "A <?x\n\ny?> here.\n", "A <!x\n\ny> here.\n",
                     "A <![CDATA[x\n\ny]]> here.\n"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_block_level_tag_that_begins_a_line_fails_across_a_blank_line(self):
        # CommonMark reads a line that begins with such a tag as the start of
        # an HTML block, which holds the line as raw HTML.
        self.assertEqual(findings('Intro.\n\n<div\n\nclass="x">\n'),
                         ["line 3: HTML tag in Markdown prose, not rendered: '<div class=\"x\">'"])
        for text in ("<details\n\nopen> text", "<p\n\nfoo>", "<table\n\n>", '<div class="x\n\n">',
                     '- <div\n\n  class="x">', "1. <div\n\n   class=x>",
                     "- a\n    - <div\n\n      class=x>", "> <div\n\nclass=x>",
                     "   <div\n\nclass=x>", "Intro.\n<DIV\n\nclass=x>", "</div\n\n>", "<pre\n\nx>"):
            with self.subTest(text=text):
                self.assertEqual(len(findings(text)), 1)

    def test_tag_that_opens_no_html_block_does_not_cross_a_blank_line(self):
        # No line here begins with a tag that opens an HTML block, so each tag
        # is inside a paragraph.
        for text in ("<span\n\nclass=x>", "`x` <div\n\nclass=x>", "</pre\n\n>"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_block_level_tag_on_one_line_fails_once(self):
        self.assertEqual(findings("<div>\n- <p>x</p>\n"),
                         ["line 1: HTML tag in Markdown prose, not rendered: '<div>'",
                          "line 2: HTML tag in Markdown prose, not rendered: '<p>'",
                          "line 2: HTML tag in Markdown prose, not rendered: '</p>'"])

    def test_raw_html_does_not_cross_a_line_that_begins_a_block_quote(self):
        # CommonMark ends the paragraph before a line that begins a block
        # quote, so the unclosed tag before that line is text.
        for text in ("<x\n> quoted\n", "<x\n> quoted>\n", "A </x\n> y\n",
                     "A <a title='x\n> y'> b\n", "A <?x\n> y?>\n", "> a <x\n> > b>\n",
                     "> <a\n>\n> b>\n", "> > a\n\n> <x\n> > y>\n", "> > \n> <x\n> > y>\n",
                     "> a > b <x\n> > y>\n", "- a <x\n  > y>\n"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_tag_across_a_line_that_continues_a_block_quote_fails(self):
        # The block quote markers of the second line are not text, and a ">"
        # after four spaces, or after "2.", which cannot interrupt a
        # paragraph, begins no block quote.
        self.assertEqual(findings('> <a\n> b="c"> d\n'),
                         ["line 1: HTML tag in Markdown prose, not rendered: '<a b=\"c\">'"])
        for text in ("> <a\nb>\n", "> > <a\n> b>\n", "- > <a\n  > b>\n", "> > a\n> <x\n> > y>\n",
                     "Intro.\n> <a\n> b>\n", "<x\n    > y\n", "> a <a title='x\n> 2. > y'>\n"):
            with self.subTest(text=text):
                self.assertEqual(len(findings(text)), 1)

    def test_quoted_attribute_value_split_across_lines_fails(self):
        self.assertEqual(len(findings("A <a b='x\ny'> tag.\n")), 1)

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

    def test_tag_in_a_fence_info_string_passes(self):
        # CommonMark reads text after the opening fence as the info string.
        for text in ("```<b>\nx\n```\n", "~~~ <b> x\n<n>\n~~~\n"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_text_after_a_fenced_code_block_is_checked(self):
        self.assertEqual(len(findings("```\n<a>\n```\nThen <b>.\n")), 1)

    def test_other_angle_brackets_pass(self):
        for text in ("An escaped \\<name> placeholder.", "An autolink <https://example.com>.",
                     "Mail <foo@example.com>.", "A comment <!-- marker --> here.",
                     "Empty comments <!--> and <!---> here.",
                     "An escaped \\<?x?> and \\<!DOCTYPE html> here.",
                     "A [link](<a b>) destination.", "a < b > c", "1 <2 and 3> 2"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_link_destination_after_spaces_or_a_line_break_passes(self):
        for text in ("[t]( <x>)\n", 'A [t](  <x> "title") link.\n', "[t](\n<x>)\n",
                     "> [t](\n> <x>)\n", "![i]( <a b>)\n", "[t]( <x> (t))\n", "[t]( <x>\n)\n",
                     "[a [b] c]( <x>)\n", "[a\nb]( <x>)\n"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_angle_brackets_that_are_no_link_destination_fail(self):
        # CommonMark reads raw HTML here: the brackets follow no link text, are
        # not followed by ")" or by spaces and a title, begin a paragraph, a
        # block quote or an HTML block, or are inside the link text.
        for text in ("a]( <x>)\n", "[t]( <x>\n", "[t]( <x> junk)\n", '[t]( <x>"t")\n',
                     "[t](\n\n<x>)\n", "[t](\n> <x>)\n", "[t](\n<div>)\n", "[<b>]( <x>)\n",
                     "[t]( <a<b>)\n"):
            with self.subTest(text=text):
                self.assertEqual(len(findings(text)), 1)


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
