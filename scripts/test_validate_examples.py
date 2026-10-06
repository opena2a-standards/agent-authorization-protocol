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


class MainTest(unittest.TestCase):
    def run_main(self, unit_test_failures):
        out = io.StringIO()
        with mock.patch.object(validate_examples, "run_unit_tests",
                               return_value=unit_test_failures) as run, \
                mock.patch.object(check_naming, "check", return_value=0), \
                contextlib.redirect_stdout(out):
            code = validate_examples.main()
        run.assert_called_once_with()
        return code, out.getvalue()

    def test_unit_test_failure_fails_validation(self):
        code, out = self.run_main(1)
        self.assertEqual(code, 1)
        self.assertIn("1 failure(s)", out)

    def test_passing_unit_tests_pass_validation(self):
        code, out = self.run_main(0)
        self.assertEqual(code, 0)
        self.assertIn("unit tests pass", out)


if __name__ == "__main__":
    unittest.main()
