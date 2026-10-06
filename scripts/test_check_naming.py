#!/usr/bin/env python3
"""Tests for check_naming.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py.
"""

import contextlib
import io
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_naming  # noqa: E402
from check_naming import first_use_error  # noqa: E402


class FirstUseTest(unittest.TestCase):
    def test_expanded_first_use_passes(self):
        text = "Intro.\nOpenA2A AIM (Agent Identity Management) supplies X.\nAIM does Y.\n"
        self.assertIsNone(first_use_error(text))

    def test_bare_first_use_fails(self):
        text = "Reuse the existing AIM signed-audit path.\n"
        self.assertIn("line 1", first_use_error(text))

    def test_expansion_without_organization_fails(self):
        text = "AIM (Agent Identity Management) supplies X.\n"
        self.assertIsNotNone(first_use_error(text))

    def test_organization_without_expansion_fails(self):
        text = "OpenA2A AIM supplies X.\nOpenA2A AIM (Agent Identity Management) does Y.\n"
        self.assertIn("line 1", first_use_error(text))

    def test_bare_use_before_expansion_on_same_line_fails(self):
        text = "AIM and OpenA2A AIM (Agent Identity Management).\n"
        self.assertIsNotNone(first_use_error(text))

    def test_navigation_bar_is_not_a_use(self):
        text = (
            "> **OpenA2A specs** · [AIP](https://example.org) · [AIM](https://example.org)\n"
            "The OpenA2A AIM (Agent Identity Management) decorator.\n"
        )
        self.assertIsNone(first_use_error(text))

    def test_ordinary_blockquote_is_a_use(self):
        text = (
            "> Reuse the existing AIM signed-audit path.\n"
            "The OpenA2A AIM (Agent Identity Management) decorator.\n"
        )
        self.assertIn("line 1", first_use_error(text))

    def test_fenced_code_block_is_not_a_use(self):
        text = (
            "Intro.\n"
            "```text\n"
            "client --> broker (AIM path)\n"
            "```\n"
            "The OpenA2A AIM (Agent Identity Management) decorator.\n"
        )
        self.assertIsNone(first_use_error(text))

    def test_bare_use_after_fenced_code_block_fails(self):
        text = "```\n(AIM path)\n```\nThe AIM decorator.\n"
        self.assertIn("line 4", first_use_error(text))

    def test_fence_closes_only_on_same_character_and_length(self):
        text = "~~~~\n```\n~~~\n(AIM path)\n  ~~~~\nThe AIM decorator.\n"
        self.assertIn("line 6", first_use_error(text))

    def test_inline_triple_backticks_are_not_a_fence(self):
        text = "```AIM``` is inline code.\n"
        self.assertIn("line 1", first_use_error(text))

    def test_other_acronyms_are_not_a_use(self):
        text = "AIMS and AIMED are other words.\nThe AIM decorator.\n"
        self.assertIn("line 2", first_use_error(text))

    def test_document_without_the_name_passes(self):
        self.assertIsNone(first_use_error("No product name here.\n"))


class RepositoryDocumentsTest(unittest.TestCase):
    def test_every_document_passes(self):
        for name in check_naming.documents():
            with self.subTest(document=name):
                text = (check_naming.ROOT / name).read_text(encoding="utf-8")
                self.assertIsNone(first_use_error(text))

    def test_documents_outside_the_required_list_are_covered(self):
        names = check_naming.documents()
        for name in (
            *check_naming.REQUIRED,
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "decisions/2026-07-16-mldsa65-serialization-profile.md",
            "schemas/README.md",
            "draft-fane-opena2a-aap-02.xml",
        ):
            with self.subTest(document=name):
                self.assertIn(name, names)

    def test_repository_check_has_no_failures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_naming.check(), 0)


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_required(root):
    for name in check_naming.REQUIRED:
        write(root, name, "No product name here.\n")


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def test_without_git_every_markdown_file_and_draft_source_is_found(self):
        for name in ("a.md", "sub/b.md", ".hidden/c.md", "draft-x-00.xml",
                     "draft-x-00.txt", "other.xml", "sub/draft-y-00.xml"):
            write(self.root, name, "text\n")
        with mock.patch.object(check_naming, "tracked_documents", return_value=None):
            self.assertEqual(check_naming.documents(self.root),
                             ["a.md", "draft-x-00.xml", "sub/b.md"])

    @unittest.skipIf(shutil.which("git") is None, "git not installed")
    def test_in_a_git_checkout_only_tracked_files_are_found(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        write(self.root, "tracked.md", "text\n")
        write(self.root, "draft-x-00.xml", "text\n")
        write(self.root, "untracked.md", "The AIM decorator.\n")
        subprocess.run(["git", "-C", str(self.root), "add", "tracked.md", "draft-x-00.xml"],
                       check=True)
        self.assertEqual(check_naming.documents(self.root), ["draft-x-00.xml", "tracked.md"])

    def test_unlisted_document_with_bare_first_use_fails(self):
        write_required(self.root)
        write(self.root, "decisions/note.md", "Lesson from the AIM header gap.\n")
        with mock.patch.object(check_naming, "tracked_documents", return_value=None):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(check_naming.check(self.root), 1)
        self.assertIn("FAIL  decisions/note.md: line 1", out.getvalue())

    def test_missing_required_document_fails(self):
        write_required(self.root)
        (self.root / "AAP-SPEC.md").unlink()
        with mock.patch.object(check_naming, "tracked_documents", return_value=None):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(check_naming.check(self.root), 1)
        self.assertIn("FAIL  AAP-SPEC.md: required document not found", out.getvalue())

    def test_document_without_the_name_is_reported_as_no_use(self):
        write_required(self.root)
        with mock.patch.object(check_naming, "tracked_documents", return_value=None):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(check_naming.check(self.root), 0)
        self.assertIn("ok    README.md: does not use the name AIM", out.getvalue())
        self.assertNotIn("expanded", out.getvalue())

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (3, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_naming, "check", return_value=failures):
                    self.assertEqual(check_naming.main(), code)


if __name__ == "__main__":
    unittest.main()
