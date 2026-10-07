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
import time
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

    def test_blockquote_marker_is_not_reported_as_a_word(self):
        text = "> Recorded as\n> of 2026-09-08 by the broker.\n"
        self.assertEqual(findings(text),
                         ["line 1: dated implementation status: 'as of 2026-09-08'"])

    def test_month_name_date_anchors_fail(self):
        for anchor in ("As of October 2026", "As of 6 October 2026", "As of October 6, 2026",
                       "As of Oct. 2026", "As of 2026", "As of 2026-09-08T10:00Z"):
            with self.subTest(anchor=anchor):
                reasons = findings(f"{anchor}, both verifiers match the pattern.\n")
                self.assertEqual(len(reasons), 1)
                self.assertIn("line 1: dated implementation status", reasons[0])

    def test_every_month_name_fails(self):
        months = ("January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December")
        for month in (*months, *(name[:3] for name in months), "Sept"):
            anchor = f"As of {month} 2026"
            with self.subTest(anchor=anchor):
                self.assertEqual(findings(f"{anchor}, both verifiers match.\n"),
                                 [f"line 1: dated implementation status: {anchor!r}"])

    def test_month_name_date_anchor_is_reported_in_full(self):
        self.assertEqual(findings("As of 6 October 2026, both verifiers match.\n"),
                         ["line 1: dated implementation status: 'As of 6 October 2026'"])

    def test_relative_date_anchors_fail(self):
        for anchor in ("As of this writing", "As of the time of writing", "As of this revision",
                       "As of today", "As of now"):
            with self.subTest(anchor=anchor):
                self.assertEqual(len(findings(f"{anchor}, no broker binds cnf.\n")), 1)

    def test_anchor_ends_at_a_word_boundary(self):
        for text in ("Measured as of 20260 requests.\n", "Read as of Mayhem.\n",
                     "Treated as of this revisionist reading.\n", "Seen as of nowhere.\n"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_universal_negative_fails(self):
        self.assertIn("unscoped universal negative",
                      findings("A target: no implementation mints BACs.\n")[0])

    def test_plural_universal_negative_fails(self):
        self.assertEqual(findings("No implementations mint BACs.\n"),
                         ["line 1: unscoped universal negative: 'No implementations'"])

    def test_universal_negative_with_another_qualifier_fails(self):
        for text, words in (("No current implementation mints BACs.", "No current implementation"),
                            ("None of the implementations mint BACs.",
                             "None of the implementations"),
                            ("None of the deployed implementations mint BACs.",
                             "None of the deployed implementations")):
            with self.subTest(text=text):
                self.assertEqual(findings(text),
                                 [f"line 1: unscoped universal negative: {words!r}"])

    def test_universal_negative_split_by_inline_markup_fails(self):
        for text in ("No *reference* implementation mints AITs.",
                     "No _reference_ implementation mints AITs.",
                     "No `reference` implementation mints AITs.",
                     "<t>No <em>reference</em> implementation mints it</t>"):
            with self.subTest(text=text):
                self.assertEqual(
                    findings(text),
                    ["line 1: unscoped universal negative: 'No reference implementation'"])

    def test_negative_needs_a_word_boundary_before_no(self):
        self.assertEqual(findings("The Juno implementation mints BACs.\n"), [])

    def test_implementation_as_a_modifier_passes(self):
        for text in ("This section places no implementation requirement on verifiers.",
                     "It adds no reference implementation guidance.",
                     "No implementation-defined claim names."):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

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
        for text in ("No known implementation minted it.", "No *known* implementation minted it.",
                     "None of the known implementations mint it."):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_normative_statement_passes(self):
        # A conforming, compliant or conformant implementation is the subject of
        # a requirement, not of a status claim.
        for text in ("No conforming implementation accepts an AIT without cnf.",
                     "No compliant implementation accepts it.",
                     "No conformant implementation accepts it.",
                     "No *conforming* implementation accepts it.",
                     "None of the conforming implementations accept it.",
                     "<t>No <em>conforming</em> implementation accepts it</t>"):
            with self.subTest(text=text):
                self.assertEqual(findings(text), [])

    def test_nonconforming_qualifier_fails(self):
        self.assertEqual(findings("No nonconforming implementation mints BACs.\n"),
                         ["line 1: unscoped universal negative: "
                          "'No nonconforming implementation'"])

    def test_named_record_passes(self):
        text = ("> **Implementation status (non-normative).** This specification does not\n"
                "> record which implementations mint AITs.\n")
        self.assertEqual(findings(text), [])

    def test_line_numbers_follow_the_line_of_each_match(self):
        text = "".join(f"line {n}: no implementation mints it.\n" for n in range(1, 2001))
        self.assertEqual([reason.split(":")[0] for reason in findings(text)],
                         [f"line {n}" for n in range(1, 2001)])

    def test_run_time_is_linear_in_the_number_of_matches(self):
        # Counting newlines from the start of the text for every match took
        # 4.6 s on 44,444 matches; precomputed line starts take well under 1 s.
        text = "no implementation\n" * 44444
        start = time.perf_counter()
        self.assertEqual(len(findings(text)), 44444)
        self.assertLess(time.perf_counter() - start, 2.0)

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
                     "other-03.xml"):
            write(self.root, name, "As of the date of this revision no implementation.\n")
        self.assertEqual(check_status_claims.documents(self.root),
                         ["AAP-SPEC.md", "AAP-BROKER-PROFILE.md",
                          "draft-fane-opena2a-aap-03.xml"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_status_claims.check(self.root), 1)
        self.assertIn("FAIL  draft-fane-opena2a-aap-03.xml: line 1", out.getvalue())
        self.assertNotIn("aap-02", out.getvalue())

    def test_every_other_internet_draft_source_is_covered(self):
        for name in ("draft-ietf-opena2a-aap-00.xml", "draft-other-03.xml"):
            write(self.root, name, "<rfc><t>no implementation mints it</t></rfc>\n")
        self.assertEqual(check_status_claims.documents(self.root),
                         ["AAP-SPEC.md", "AAP-BROKER-PROFILE.md",
                          "draft-ietf-opena2a-aap-00.xml", "draft-other-03.xml"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_status_claims.check(self.root), 2)
        self.assertIn("FAIL  draft-ietf-opena2a-aap-00.xml: line 1: unscoped universal negative",
                      out.getvalue())

    def test_failure_line_names_the_accepted_wording(self):
        write(self.root, "AAP-SPEC.md", "Intro.\nNo implementation mints BACs.\n")
        write(self.root, "AAP-BROKER-PROFILE.md", "As of October 2026 the broker binds cnf.\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_status_claims.check(self.root), 2)
        lines = out.getvalue().splitlines()
        self.assertEqual(
            lines[0],
            "FAIL  AAP-SPEC.md: line 2: unscoped universal negative: 'No implementation'; "
            'write "no known implementation", or name the record that holds the status '
            "(broker profile Section 14, the reference implementation's repository, "
            "or the aap-conformance repository's conformance.json)")
        self.assertEqual(
            lines[1],
            "FAIL  AAP-BROKER-PROFILE.md: line 1: dated implementation status: "
            "'As of October 2026'; state the status without a date and name the record "
            "that holds it (broker profile Section 14, the reference implementation's "
            "repository, or the aap-conformance repository's conformance.json)")

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
