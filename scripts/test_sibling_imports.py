#!/usr/bin/env python3
"""Tests that each test file in scripts/ imports when it is named by path.

`python3 -m unittest scripts/test_x.py`, run from the repository root, imports the
file as the module `scripts.test_x` without putting scripts/ on sys.path, so a test
file that imports a sibling script (`import check_naming`) fails with
ModuleNotFoundError unless it first puts its own directory on sys.path, as in
`sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`. The documented
discover run hides the gap, because `-s scripts` puts scripts/ on sys.path. The
tests import every test file under that module name in a new interpreter started
in the repository root with PYTHONPATH ignored, and fail with the error the import
raised and the line to add. They import each file without running its tests, so a
sibling import inside a test method is not covered. CI runs these tests through
validate_examples.py.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
INSERT = "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))"
IMPORT = "import importlib, sys; importlib.import_module(sys.argv[1])"


def import_error_by_path(path, root):
    """The last line of the error raised importing `path` as `python3 -m unittest` does from `root`.

    None if the import succeeds. The module name is the path relative to `root`,
    without `.py` and with dots for slashes; the new interpreter has `root` as its
    working directory, ignores PYTHONPATH and writes no bytecode.
    """
    module = ".".join(path.relative_to(root).with_suffix("").parts)
    result = subprocess.run([sys.executable, "-B", "-E", "-c", IMPORT, module],
                            cwd=root, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        return None
    lines = result.stderr.strip().splitlines()
    return lines[-1] if lines else f"exit status {result.returncode}"


def failure_message(name, error):
    """What a test file named `name` that fails to import with `error` should contain."""
    return (f"python3 -m unittest {name} fails with {error}; a test file that imports a "
            f"sibling script runs {INSERT} before that import")


class SiblingImportsTest(unittest.TestCase):
    def test_each_test_file_imports_when_named_by_path(self):
        tests = sorted(SCRIPTS.glob("test_*.py"))
        self.assertIn(pathlib.Path(__file__).resolve(), tests)
        for path in tests:
            name = path.relative_to(ROOT).as_posix()
            with self.subTest(test=name):
                error = import_error_by_path(path, ROOT)
                self.assertIsNone(error, msg=failure_message(name, error))

    def fixture_error(self, source):
        """The import error of a test file holding `source` beside a sibling `check_naming.py`."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "check_naming.py").write_text("ROOT = None\n", encoding="utf-8")
            path = root / "scripts" / "test_fixture.py"
            path.write_text(source, encoding="utf-8")
            return import_error_by_path(path, root)

    def assert_sibling_not_found(self, source):
        self.assertEqual(self.fixture_error(source),
                         "ModuleNotFoundError: No module named 'check_naming'")

    def test_sibling_import_without_insert_fails(self):
        self.assert_sibling_not_found("import re\n\nimport check_naming\n")

    def test_from_import_of_a_sibling_without_insert_fails(self):
        self.assert_sibling_not_found("import unittest\nfrom check_naming import ROOT\n")

    def test_importlib_import_of_a_sibling_without_insert_fails(self):
        self.assert_sibling_not_found('import importlib\n\ncheck_naming = importlib.import_module("check_naming")\n')

    def test_insert_before_the_import_clears_it(self):
        source = f"import pathlib\nimport sys\n\n{INSERT}\n\nimport check_naming  # noqa: E402\n"
        self.assertIsNone(self.fixture_error(source))

    def test_insert_of_a_name_bound_to_the_directory_clears_it(self):
        source = ("import pathlib\nimport sys\n\nHERE = pathlib.Path(__file__).resolve().parent\n"
                  "sys.path.insert(0, str(HERE))\n\nimport check_naming  # noqa: E402\n")
        self.assertIsNone(self.fixture_error(source))

    def test_append_of_the_directory_clears_it(self):
        source = ("import pathlib\nimport sys\n\n"
                  "sys.path.append(str(pathlib.Path(__file__).resolve().parent))\n\n"
                  "import check_naming  # noqa: E402\n")
        self.assertIsNone(self.fixture_error(source))

    def test_insert_after_the_import_does_not_clear_it(self):
        self.assert_sibling_not_found(f"import pathlib\nimport sys\n\nimport check_naming\n\n{INSERT}\n")

    def test_import_before_the_insert_on_its_line_does_not_clear_it(self):
        self.assert_sibling_not_found(f"import pathlib\nimport sys\n\nimport check_naming; {INSERT}\n")

    def test_import_after_the_insert_on_its_line_clears_it(self):
        self.assertIsNone(self.fixture_error(f"import pathlib\nimport sys\n\n{INSERT}; import check_naming\n"))

    def test_insert_of_a_path_not_built_from_the_file_does_not_clear_it(self):
        self.assert_sibling_not_found("import sys\n\nsys.path.insert(0, 'elsewhere')\n\nimport check_naming\n")

    def test_insert_of_the_parent_of_the_directory_does_not_clear_it(self):
        self.assert_sibling_not_found("import pathlib\nimport sys\n\n"
                            "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))\n\n"
                            "import check_naming  # noqa: E402\n")

    def test_insert_inside_a_function_never_called_does_not_clear_it(self):
        self.assert_sibling_not_found(f"import pathlib\nimport sys\n\n\ndef unused():\n    {INSERT}\n\n\n"
                            "import check_naming  # noqa: E402\n")

    def test_failure_message_names_the_error_and_the_line_to_add(self):
        message = failure_message("scripts/test_x.py",
                                  "ModuleNotFoundError: No module named 'check_naming'")
        self.assertIn("python3 -m unittest scripts/test_x.py fails with "
                      "ModuleNotFoundError: No module named 'check_naming'", message)
        self.assertIn(INSERT, message)


if __name__ == "__main__":
    unittest.main()
