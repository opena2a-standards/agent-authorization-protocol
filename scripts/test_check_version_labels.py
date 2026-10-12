#!/usr/bin/env python3
"""Tests for check_version_labels.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

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

import check_version_labels  # noqa: E402
from check_version_labels import SUFFIX, changelog_state, findings  # noqa: E402

HEAD = "# Changelog\n\nIntro.\n\n"
RELEASED = "## [0.5.1-draft] - 2026-10-02\n\nPairing.\n\n### Changed\n\n- Earlier change.\n"
EMPTY = HEAD + "## [Unreleased]\n\n" + RELEASED
WITH_ENTRY = HEAD + "## [Unreleased]\n\n### Changed\n\n- A requirement moved.\n\n" + RELEASED


def document(version, suffix=""):
    return f"# Title\n\n## Subtitle\n\n**Version:** {version}{suffix}\n**Date:** October 2026\n"


class ChangelogStateTest(unittest.TestCase):
    def test_empty_unreleased_section_records_no_change(self):
        self.assertEqual(changelog_state(EMPTY), (False, "0.5.1-draft"))

    def test_subheading_alone_records_no_change(self):
        text = HEAD + "## [Unreleased]\n\n### Changed\n\n### Added\n\n" + RELEASED
        self.assertEqual(changelog_state(text), (False, "0.5.1-draft"))

    def test_entry_records_a_change(self):
        self.assertEqual(changelog_state(WITH_ENTRY), (True, "0.5.1-draft"))

    def test_entries_of_released_sections_are_not_unreleased(self):
        text = HEAD + "## [Unreleased]\n\n" + RELEASED + "\n## [0.5.0-draft] - 2026-09-08\n\n- X.\n"
        self.assertEqual(changelog_state(text), (False, "0.5.1-draft"))

    def test_newest_released_section_is_the_first(self):
        text = WITH_ENTRY + "\n## [0.2.0-draft] - 2026-06-01 (+ errata through 2026-07-02)\n"
        self.assertEqual(changelog_state(text)[1], "0.5.1-draft")

    def test_changelog_without_released_section(self):
        self.assertEqual(changelog_state(HEAD + "## [Unreleased]\n\n- First.\n"), (True, None))


class FindingsTest(unittest.TestCase):
    def test_unreleased_changes_require_the_suffix(self):
        reasons = findings("AAP-SPEC.md", document("0.5.1-draft"), True, "0.5.1-draft")
        self.assertEqual(len(reasons), 1)
        self.assertIn("line 5: CHANGELOG.md [Unreleased] records changes, but the label names"
                      " 0.5.1-draft alone; append 'plus unreleased changes", reasons[0])

    def test_suffix_passes_with_unreleased_changes(self):
        for name, version in (("AAP-SPEC.md", "0.5.1-draft"),
                              ("AAP-BROKER-PROFILE.md", "0.4.1-draft")):
            with self.subTest(document=name):
                self.assertEqual(
                    findings(name, document(version, SUFFIX), True, "0.5.1-draft"), [])

    def test_bare_label_passes_without_unreleased_changes(self):
        for name, version in (("AAP-SPEC.md", "0.5.1-draft"),
                              ("AAP-BROKER-PROFILE.md", "0.4.1-draft")):
            with self.subTest(document=name):
                self.assertEqual(findings(name, document(version), False, "0.5.1-draft"), [])

    def test_suffix_fails_without_unreleased_changes(self):
        reasons = findings("AAP-BROKER-PROFILE.md", document("0.4.1-draft", SUFFIX), False,
                           "0.5.1-draft")
        self.assertEqual(len(reasons), 1)
        self.assertIn("records no change; remove 'plus unreleased changes", reasons[0])

    def test_specification_names_the_newest_release(self):
        for version in ("0.5.2-draft", "0.5.0-draft"):
            with self.subTest(version=version):
                reasons = findings("AAP-SPEC.md", document(version, SUFFIX), True, "0.5.1-draft")
                self.assertEqual(reasons, [
                    f"line 5: names {version}, but the newest released section of CHANGELOG.md"
                    " is 0.5.1-draft; the label names the last release"])

    def test_specification_fails_when_nothing_is_released(self):
        reasons = findings("AAP-SPEC.md", document("0.1.0-draft", SUFFIX), True, None)
        self.assertEqual(reasons,
                         ["line 5: names 0.1.0-draft, but CHANGELOG.md has no released section"])

    def test_broker_profile_version_is_not_compared(self):
        self.assertEqual(
            findings("AAP-BROKER-PROFILE.md", document("0.4.1-draft"), False, "0.5.1-draft"), [])

    def test_label_in_another_form_fails(self):
        for line in ("0.5.1-draft (plus unreleased changes)", "0.5.1", "v0.5.1-draft",
                     "0.5.1-draft plus unreleased changes"):
            with self.subTest(line=line):
                reasons = findings("AAP-SPEC.md", document(line), True, "0.5.1-draft")
                self.assertEqual(len(reasons), 1)
                self.assertIn("is not '**Version:** MAJOR.MINOR.PATCH-draft'", reasons[0])

    def test_rc_and_final_labels_are_versions(self):
        for version in ("0.6.0-rc1", "1.0.0-final"):
            with self.subTest(version=version):
                self.assertEqual(
                    findings("AAP-SPEC.md", document(version, SUFFIX), True, version), [])

    def test_missing_version_line_fails(self):
        self.assertEqual(findings("AAP-SPEC.md", "# Title\n\n**Date:** October 2026\n", False,
                                  "0.5.1-draft"), ["no **Version:** line"])


class RepositoryDocumentsTest(unittest.TestCase):
    def test_repository_check_has_no_failures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_version_labels.check(), 0)


def write(root, name, text):
    (root / name).write_text(text, encoding="utf-8")


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        write(self.root, "CHANGELOG.md", WITH_ENTRY)
        write(self.root, "AAP-SPEC.md", document("0.5.1-draft", SUFFIX))
        write(self.root, "AAP-BROKER-PROFILE.md", document("0.4.1-draft", SUFFIX))

    def run_check(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            failures = check_version_labels.check(self.root)
        return failures, out.getvalue().splitlines()

    def test_labels_with_suffix_pass(self):
        failures, lines = self.run_check()
        self.assertEqual(failures, 0)
        self.assertEqual(lines, [
            "ok    AAP-SPEC.md: version line names the release and the unreleased changes",
            "ok    AAP-BROKER-PROFILE.md: version line names the release and the unreleased"
            " changes"])

    def test_labels_unchanged_after_a_requirement_change_fail(self):
        write(self.root, "AAP-SPEC.md", document("0.5.1-draft"))
        write(self.root, "AAP-BROKER-PROFILE.md", document("0.4.1-draft"))
        failures, lines = self.run_check()
        self.assertEqual(failures, 2)
        self.assertTrue(lines[0].startswith("FAIL  AAP-SPEC.md: line 5: CHANGELOG.md"))
        self.assertTrue(lines[1].startswith("FAIL  AAP-BROKER-PROFILE.md: line 5: CHANGELOG.md"))

    def test_release_state_passes_with_bare_labels(self):
        write(self.root, "CHANGELOG.md", EMPTY)
        write(self.root, "AAP-SPEC.md", document("0.5.1-draft"))
        write(self.root, "AAP-BROKER-PROFILE.md", document("0.4.1-draft"))
        failures, lines = self.run_check()
        self.assertEqual(failures, 0)
        self.assertEqual(lines, ["ok    AAP-SPEC.md: version line names the release",
                                 "ok    AAP-BROKER-PROFILE.md: version line names the release"])

    def test_missing_changelog_fails(self):
        (self.root / "CHANGELOG.md").unlink()
        failures, lines = self.run_check()
        self.assertEqual((failures, lines), (1, ["FAIL  CHANGELOG.md: required document not found"]))

    def test_missing_document_fails(self):
        (self.root / "AAP-BROKER-PROFILE.md").unlink()
        failures, lines = self.run_check()
        self.assertEqual(failures, 1)
        self.assertIn("FAIL  AAP-BROKER-PROFILE.md: required document not found", lines)

    def test_document_that_is_not_utf8_fails_without_a_traceback(self):
        (self.root / "AAP-SPEC.md").write_bytes(b"Text.\ncaf\xe9\n")
        failures, lines = self.run_check()
        self.assertEqual(failures, 1)
        self.assertIn("FAIL  AAP-SPEC.md: line 2: not valid UTF-8 (invalid continuation byte "
                      "at byte 9); save the document as UTF-8", lines)

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (2, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_version_labels, "check", return_value=failures):
                    self.assertEqual(check_version_labels.main(), code)


if __name__ == "__main__":
    unittest.main()
