#!/usr/bin/env python3
"""Tests for validate_examples.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'"""

import contextlib
import io
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:
    import jsonschema  # noqa: F401
except ImportError:
    raise unittest.SkipTest("the 'jsonschema' package is required (pip install jsonschema)")

import check_naming  # noqa: E402
import check_raw_html  # noqa: E402
import check_references  # noqa: E402
import check_requirement_references  # noqa: E402
import check_status_claims  # noqa: E402
import check_section_citations  # noqa: E402
import check_spelling  # noqa: E402
import validate_examples  # noqa: E402

PASSING = "import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        pass\n"
FAILING = "import unittest\n\nclass T(unittest.TestCase):\n    def test_bad(self):\n        self.fail()\n"


def forget_path(path):
    if path in sys.path:
        sys.path.remove(path)


class RunUnitTestsTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def run_in(self, files):
        for name, text in files.items():
            (self.root / name).write_text(text, encoding="utf-8")
            self.addCleanup(sys.modules.pop, name.removesuffix(".py"), None)
        self.addCleanup(forget_path, str(self.root))
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            failed = validate_examples.run_unit_tests(self.root)
        return failed, out.getvalue()

    def test_passing_tests_count_no_failure(self):
        failed, out = self.run_in({"test_aap_runner_passes.py": PASSING})
        self.assertEqual(failed, 0)
        self.assertIn("unit tests OK    1 passed", out)

    def test_failing_test_is_counted(self):
        failed, out = self.run_in({
            "test_aap_runner_mixed_ok.py": PASSING,
            "test_aap_runner_mixed_bad.py": FAILING,
        })
        self.assertEqual(failed, 1)
        self.assertIn("unit tests FAIL  1 of 2 failed", out)

    def test_no_tests_found_is_a_failure(self):
        failed, out = self.run_in({"helper.py": PASSING})
        self.assertEqual(failed, 1)
        self.assertIn("no test_*.py tests found", out)

    def test_repository_unit_tests_are_discovered(self):
        names = {
            test.id().split(".")[0]
            for suite in unittest.TestLoader().discover(
                str(validate_examples.SCRIPTS), pattern="test_*.py",
                top_level_dir=str(validate_examples.SCRIPTS))
            for case in suite
            for test in case
        }
        self.assertIn("test_check_naming", names)
        self.assertIn("test_check_status_claims", names)
        self.assertIn("test_check_section_citations", names)
        self.assertIn("test_check_raw_html", names)
        self.assertIn("test_check_spelling", names)


class MainTest(unittest.TestCase):
    def run_main(self, unit_test_failures, status_claim_failures=0,
                 section_citation_failures=0, raw_html_failures=0, spelling_failures=0):
        out = io.StringIO()
        with mock.patch.object(validate_examples, "run_unit_tests",
                               return_value=unit_test_failures) as run, \
                mock.patch.object(check_naming, "check", return_value=0), \
                mock.patch.object(check_status_claims, "check",
                                  return_value=status_claim_failures) as status, \
                mock.patch.object(check_section_citations, "check",
                                  return_value=section_citation_failures) as cite, \
                mock.patch.object(check_raw_html, "check",
                                  return_value=raw_html_failures) as raw_html, \
                mock.patch.object(check_spelling, "check",
                                  return_value=spelling_failures) as spelling, \
                contextlib.redirect_stdout(out):
            code = validate_examples.main()
        run.assert_called_once_with()
        status.assert_called_once_with()
        cite.assert_called_once_with()
        raw_html.assert_called_once_with()
        spelling.assert_called_once_with()
        return code, out.getvalue()

    def test_unit_test_failure_fails_validation(self):
        code, out = self.run_main(1)
        self.assertEqual(code, 1)
        self.assertIn("1 failure(s)", out)

    def test_dated_implementation_status_fails_validation(self):
        code, out = self.run_main(0, status_claim_failures=1)
        self.assertEqual(code, 1)
        self.assertIn("1 failure(s)", out)

    def test_html_tag_in_markdown_prose_fails_validation(self):
        code, out = self.run_main(0, raw_html_failures=1)
        self.assertEqual(code, 1)
        self.assertIn("1 failure(s)", out)

    def test_british_spelling_fails_validation(self):
        code, out = self.run_main(0, spelling_failures=1)
        self.assertEqual(code, 1)
        self.assertIn("1 failure(s)", out)

    def test_passing_unit_tests_pass_validation(self):
        code, out = self.run_main(0)
        self.assertEqual(code, 0)
        self.assertIn("unit tests pass", out)

    def test_section_citation_failure_fails_validation(self):
        code, out = self.run_main(0, section_citation_failures=1)
        self.assertEqual(code, 1)
        self.assertIn("1 failure(s)", out)


class NotUtf8Test(unittest.TestCase):
    """Every document check on a copy of the repository's documents that holds a
    Markdown file that is not valid UTF-8: a FAIL line, never a traceback."""

    CHECKS = (check_naming, check_status_claims, check_references,
              check_requirement_references, check_section_citations, check_raw_html,
              check_spelling)
    REASON = "not valid UTF-8 (invalid continuation byte at byte"

    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for name in check_naming.documents():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(validate_examples.ROOT / name, self.root / name)
        patcher = mock.patch.object(check_naming, "tracked_documents", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_checks(self):
        results = {}
        for module in self.CHECKS:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                failures = module.check(self.root)
            results[module] = (failures, out.getvalue())
        return results

    def test_the_copy_passes_every_check(self):
        for module, (failures, out) in self.run_checks().items():
            with self.subTest(check=module.__name__):
                self.assertEqual(failures, 0, out)

    def test_a_new_markdown_file_fails_each_check_that_reads_every_document(self):
        (self.root / "NOTES.md").write_bytes(b"# Notes\n\nCaf\xe9.\n")
        results = self.run_checks()
        line = f"FAIL  NOTES.md: line 3: {self.REASON} 12); save the document as UTF-8"
        every_document = (check_naming, check_section_citations, check_raw_html, check_spelling)
        for module in self.CHECKS:
            failures, out = results[module]
            with self.subTest(check=module.__name__):
                if module in every_document:
                    self.assertEqual(failures, 1, out)
                    self.assertIn(line, out.splitlines())
                else:
                    # NOTES.md is not one of the documents these checks read.
                    self.assertEqual(failures, 0, out)
                    self.assertNotIn("NOTES.md", out)

    def test_a_specification_document_fails_every_check(self):
        for name in ("AAP-SPEC.md", "AAP-BROKER-PROFILE.md"):
            with self.subTest(document=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b"caf\xe9\n")
                self.addCleanup(path.write_bytes, original)
                results = self.run_checks()
                path.write_bytes(original)
                for module in self.CHECKS:
                    failures, out = results[module]
                    if name != "AAP-SPEC.md" and module is check_references:
                        continue  # check_references reads the specification only
                    with self.subTest(check=module.__name__):
                        self.assertGreaterEqual(failures, 1, out)
                        self.assertIn(f"{name}: line ", out)
                        self.assertIn(self.REASON, out)

    def test_a_changelog_fails_the_checks_that_read_it(self):
        path = self.root / "CHANGELOG.md"
        path.write_bytes(path.read_bytes() + b"caf\xe9\n")
        results = self.run_checks()
        for module in (check_naming, check_references, check_raw_html, check_spelling):
            failures, out = results[module]
            with self.subTest(check=module.__name__):
                self.assertGreaterEqual(failures, 1, out)
                self.assertIn("CHANGELOG.md: line ", out)
                self.assertIn(self.REASON, out)
        self.assertFalse(check_references.render_submitted(
            self.root, "draft-fane-opena2a-aap-02.xml"))

    def test_extract_block_exits_with_the_reason(self):
        path = self.root / "AAP-SPEC.md"
        path.write_bytes(b"### 1 Example\n\ncaf\xe9\n")
        with self.assertRaises(SystemExit) as raised:
            validate_examples.extract_block(path, "### 1 Example")
        self.assertIn(f"AAP-SPEC.md: line 3: {self.REASON} 18); save the document as UTF-8",
                      str(raised.exception))


if __name__ == "__main__":
    unittest.main()
