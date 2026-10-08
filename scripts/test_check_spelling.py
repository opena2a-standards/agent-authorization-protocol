#!/usr/bin/env python3
"""Tests for check_spelling.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

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

import check_naming  # noqa: E402
import check_spelling  # noqa: E402
from check_spelling import findings  # noqa: E402


class FindingsTest(unittest.TestCase):
    def test_our_form_fails_with_the_american_spelling(self):
        text = "Intro.\nthe trust class and scope a broker will honour; the broker denies\n"
        self.assertEqual(findings(text), ["line 2: 'honour'; write 'honor'"])

    def test_our_forms_with_prefixes_and_endings_fail(self):
        for british, american in (("honour", "honor"), ("Honourable", "Honorable"),
                                  ("dishonoured", "dishonored"),
                                  ("behaviour", "behavior"), ("behavioural", "behavioral"),
                                  ("favourite", "favorite"), ("colourful", "colorful"),
                                  ("neighbourhood", "neighborhood"), ("saviour", "savior"),
                                  ("savoury", "savory"), ("HONOUR", "HONOR")):
            with self.subTest(word=british):
                self.assertEqual(findings(f"a {british}.\n"),
                                 [f"line 1: {british!r}; write {american!r}"])

    def test_ise_forms_fail_with_the_american_spelling(self):
        for british, american in (("authorise", "authorize"),
                                  ("Authorisation", "Authorization"),
                                  ("unauthorised", "unauthorized"),
                                  ("organisations", "organizations"),
                                  ("recognisable", "recognizable"),
                                  ("deserialising", "deserializing"),
                                  ("normaliser", "normalizer"),
                                  ("AUTHORISED", "AUTHORIZED")):
            with self.subTest(word=british):
                self.assertEqual(findings(f"a {british}.\n"),
                                 [f"line 1: {british!r}; write {american!r}"])

    def test_american_words_ending_in_our_or_ise_pass(self):
        for word in ("our", "hour", "your", "four", "detour", "contour", "devour", "flour",
                     "glamour", "paramour", "advertise", "exercise", "compromised",
                     "supervised", "improvisation", "emphasis", "emphases", "analyses",
                     "criticism", "specialist", "optimism", "realism", "characteristic"):
            with self.subTest(word=word):
                self.assertEqual(findings(f"a {word}.\n"), [])

    def test_american_spelling_passes(self):
        text = "The broker will honor the authorization; behavior is unauthorized.\n"
        self.assertEqual(findings(text), [])

    def test_every_british_word_on_a_line_is_reported_in_order(self):
        text = "Organisations honour the authorisation.\n"
        self.assertEqual(findings(text), [
            "line 1: 'Organisations'; write 'Organizations'",
            "line 1: 'honour'; write 'honor'",
            "line 1: 'authorisation'; write 'authorization'",
        ])

    def test_fenced_code_block_is_not_read(self):
        text = "Before.\n```\nnormalise(behaviour)\n```\nAfter the colour.\n"
        self.assertEqual(findings(text), ["line 5: 'colour'; write 'color'"])

    def test_xml_source_is_read(self):
        text = "<t>A broker will <em>honour</em> the grant.</t>\n"
        self.assertEqual(findings(text), ["line 1: 'honour'; write 'honor'"])


class RepositoryDocumentsTest(unittest.TestCase):
    def test_every_document_passes(self):
        for name in check_naming.documents():
            with self.subTest(document=name):
                text = (check_spelling.ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(findings(text), [])

    def test_repository_check_has_no_failures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_spelling.check(), 0)


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def run_check(self):
        out = io.StringIO()
        with mock.patch.object(check_naming, "tracked_documents", return_value=None), \
                contextlib.redirect_stdout(out):
            failures = check_spelling.check(self.root)
        return failures, out.getvalue()

    def test_unlisted_document_with_a_british_spelling_fails(self):
        write(self.root, "README.md", "A broker will honor the grant.\n")
        write(self.root, "decisions/note.md", "A broker will honour the grant.\n")
        write(self.root, "draft-x-00.xml", "<t>The organisation.</t>\n")
        failures, out = self.run_check()
        self.assertEqual(failures, 2)
        self.assertIn("FAIL  decisions/note.md: line 1: 'honour'; write 'honor'", out)
        self.assertIn("FAIL  draft-x-00.xml: line 1: 'organisation'; write 'organization'", out)
        self.assertIn("ok    README.md: American spelling", out)

    def test_document_with_several_british_words_counts_once(self):
        write(self.root, "README.md", "The colour.\nThe flavour.\n")
        failures, out = self.run_check()
        self.assertEqual(failures, 1)
        self.assertEqual(out.count("FAIL  README.md"), 2)

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (3, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_spelling, "check", return_value=failures):
                    self.assertEqual(check_spelling.main(), code)


if __name__ == "__main__":
    unittest.main()
