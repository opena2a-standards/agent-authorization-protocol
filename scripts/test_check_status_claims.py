#!/usr/bin/env python3
"""Tests for check_status_claims.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

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

import check_status_claims  # noqa: E402
from check_status_claims import findings  # noqa: E402


class FindingsTest(unittest.TestCase):
    def test_iso_date_anchor_fails(self):
        text = "Intro.\nAs of 2026-09-08 the broker mints nothing else.\n"
        self.assertEqual(findings(text),
                         ["line 2: dated implementation status: 'As of 2026-09-08'"])

    def test_revision_date_anchor_fails(self):
        text = "As of the date of this revision, both verifiers match the pattern.\n"
        self.assertIn("line 1: dated implementation status", findings(text)[0])

    def test_anchor_split_across_lines_fails(self):
        text = "the token otherwise. As\nof 2026-09-08 the reference broker binds nothing.\n"
        self.assertEqual(findings(text),
                         ["line 1: dated implementation status: 'As of 2026-09-08'"])

    def test_anchor_split_inside_a_blockquote_fails(self):
        text = "> Recorded as of the date\n> of this revision.\n"
        self.assertEqual(len(findings(text)), 1)

    def test_universal_negative_fails(self):
        self.assertIn("unscoped universal negative",
                      findings("A target: no implementation mints BACs.\n")[0])

    def test_reference_universal_negative_fails(self):
        text = "Intro.\n\nNo reference implementation mints AITs; the schema pins the form.\n"
        self.assertIn("line 3: unscoped universal negative", findings(text)[0])

    def test_table_row_universal_negative_fails(self):
        text = "| `x` | MAY | string | Deprecated. No implementation minted it. |\n"
        self.assertEqual(len(findings(text)), 1)

    def test_findings_are_in_document_order(self):
        text = "No implementation does X.\nAs of 2026-09-08 none does Y.\n"
        self.assertEqual([reason.split(":")[0] for reason in findings(text)],
                         ["line 1", "line 2"])

    def test_scoped_negative_passes(self):
        self.assertEqual(findings("No known implementation minted it.\n"), [])

    def test_named_record_passes(self):
        text = ("> **Implementation status (non-normative).** This specification does not\n"
                "> record which implementations mint AITs.\n")
        self.assertEqual(findings(text), [])

    def test_other_dates_and_words_pass(self):
        text = ("Submitted 2026-10-02 as of record.\n"
                "Each implementation carries no implementation-defined claim names.\n")
        self.assertEqual(findings(text), [])


class RepositoryDocumentsTest(unittest.TestCase):
    def test_every_document_passes(self):
        for name in check_status_claims.documents():
            with self.subTest(document=name):
                text = (check_status_claims.ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(findings(text), [])

    def test_specification_documents_are_covered(self):
        names = check_status_claims.documents()
        for name in ("AAP-SPEC.md", "AAP-BROKER-PROFILE.md"):
            with self.subTest(document=name):
                self.assertIn(name, names)

    def test_repository_check_has_no_failures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_status_claims.check(), 0)


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for name in check_status_claims.DOCUMENTS:
            write(self.root, name, "Text.\n")

    def test_filed_revisions_are_skipped_and_later_revisions_are_covered(self):
        for name in ("draft-fane-opena2a-aap-00.xml", "draft-fane-opena2a-aap-02.xml",
                     "draft-fane-opena2a-aap-02.txt", "draft-fane-opena2a-aap-03.xml",
                     "draft-other-03.xml"):
            write(self.root, name, "As of the date of this revision no implementation.\n")
        self.assertEqual(check_status_claims.documents(self.root),
                         ["AAP-SPEC.md", "AAP-BROKER-PROFILE.md",
                          "draft-fane-opena2a-aap-03.xml"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_status_claims.check(self.root), 1)
        self.assertIn("FAIL  draft-fane-opena2a-aap-03.xml: line 1", out.getvalue())
        self.assertNotIn("aap-02", out.getvalue())

    def test_dated_claim_in_the_specification_fails(self):
        write(self.root, "AAP-SPEC.md", "Intro.\nAs of 2026-09-08 no implementation mints it.\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_status_claims.check(self.root), 1)
        self.assertIn("FAIL  AAP-SPEC.md: line 2: dated implementation status", out.getvalue())
        self.assertIn("FAIL  AAP-SPEC.md: line 2: unscoped universal negative", out.getvalue())
        self.assertIn("ok    AAP-BROKER-PROFILE.md", out.getvalue())

    def test_missing_document_fails(self):
        (self.root / "AAP-BROKER-PROFILE.md").unlink()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_status_claims.check(self.root), 1)
        self.assertIn("FAIL  AAP-BROKER-PROFILE.md: required document not found",
                      out.getvalue())

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (3, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_status_claims, "check", return_value=failures):
                    self.assertEqual(check_status_claims.main(), code)


if __name__ == "__main__":
    unittest.main()
