#!/usr/bin/env python3
"""Tests that each test file in scripts/ imports when it is named by path.

`python3 -m unittest scripts/test_x.py`, run from the repository root, imports the
file as the module `scripts.test_x` without putting scripts/ on sys.path, so a test
file that imports a sibling script (`import check_naming`) fails with
ModuleNotFoundError unless it first puts its own directory on sys.path, as in
`sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`. The documented
discover run hides the gap, because `-s scripts` puts scripts/ on sys.path. The
tests import every test file under that module name in a new interpreter started
in the repository root, and fail with the error the import raised and, when the
module it did not find is a sibling script, the line to add. The new interpreter
is given each PYTHONPATH entry of the run except one that is scripts/, so a package
installed through PYTHONPATH is found and a sibling script is not. The tests import
each file without running its tests; a sibling script that a file imports inside a
function is imported after the file, as that function imports it when a test calls
it, so the file has to put its directory on sys.path when it is imported: an
insertion inside the function does not count. Each file is imported a second time
with the `jsonschema` package made unavailable, so a test file that needs the
package skips its tests where it would fail to load. CI runs these tests through
validate_examples.py.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
INSERT = "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))"
# Puts the entries of the first argument where the interpreter puts PYTHONPATH,
# after the working directory, then imports each module the other arguments name.
IMPORT = """\
import importlib, os, sys
sys.path[1:1] = [entry for entry in sys.argv[1].split(os.pathsep) if entry]
for name in sys.argv[2:]:
    importlib.import_module(name)
"""
NOT_FOUND = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")
SIBLING_NOT_FOUND = "ModuleNotFoundError: No module named 'check_naming'"
# A module of the package's name that fails as the import of a missing package does.
NO_JSONSCHEMA = 'raise ModuleNotFoundError("No module named \'jsonschema\'", name="jsonschema")\n'
WITHOUT_JSONSCHEMA = ("; this import ran with the 'jsonschema' package made unavailable, and a test "
                      "file that needs the package skips its tests with unittest.skipUnless")


def sibling_scripts(path):
    """The module names of the scripts in the directory of `path`."""
    return {script.stem for script in path.parent.glob("*.py")}


def imports_inside_functions(path):
    """The sibling scripts the file at `path` imports inside a function, sorted.

    An `import` or `from ... import` statement inside a function runs when the
    function is called, not when the file is imported. A file that does not parse
    has none: importing it raises the error.
    """
    try:
        tree = ast.parse(path.read_bytes())
    except (SyntaxError, ValueError):
        return []
    names = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(function):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return sorted(names & sibling_scripts(path))


def python_path_without(directory):
    """The PYTHONPATH entries of this run, as absolute paths, except each that is `directory`.

    An entry is read as the interpreter reads it: a relative entry is relative to
    the working directory, an empty entry is the working directory, and an empty
    PYTHONPATH has no entry.
    """
    value = os.environ.get("PYTHONPATH")
    if not value:
        return []
    entries = [os.path.abspath(entry) for entry in value.split(os.pathsep)]
    return [entry for entry in entries
            if not (os.path.exists(entry) and os.path.samefile(entry, directory))]


def import_error_by_path(path, root):
    """The last line of the error raised importing `path` as `python3 -m unittest` does from `root`.

    None if the import succeeds, and so does the import of each sibling script the
    file imports inside a function. The module name is the path relative to `root`,
    without `.py` and with dots for slashes. The new interpreter has `root` as its
    working directory, reads no PYTHON* environment variable, has on sys.path each
    PYTHONPATH entry of this run that is not the directory of `path`, prints the
    error without color and writes no bytecode.
    """
    module = ".".join(path.relative_to(root).with_suffix("").parts)
    kept = os.pathsep.join(python_path_without(path.parent))
    result = subprocess.run(
        [sys.executable, "-B", "-E", "-c", IMPORT, kept, module, *imports_inside_functions(path)],
        cwd=root, env={**os.environ, "NO_COLOR": "1"}, capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        return None
    lines = result.stderr.strip().splitlines()
    return lines[-1] if lines else f"exit status {result.returncode}"


def failure_message(name, error, siblings):
    """What a test file named `name` that fails to import with `error` is told.

    The line to add is named when the module the import did not find is one of `siblings`.
    """
    message = f"python3 -m unittest {name} fails with {error}"
    missing = NOT_FOUND.fullmatch(error)
    if missing and missing[1] in siblings:
        message += f"; a test file that imports a sibling script runs {INSERT} before that import"
    return message


class SiblingImportsTest(unittest.TestCase):
    def assert_each_test_file_imports(self, condition=""):
        tests = sorted(SCRIPTS.glob("test_*.py"))
        self.assertIn(pathlib.Path(__file__).resolve(), tests)
        for path in tests:
            name = path.relative_to(ROOT).as_posix()
            with self.subTest(test=name):
                error = import_error_by_path(path, ROOT)
                if error is not None:
                    self.fail(failure_message(name, error, sibling_scripts(path)) + condition)

    def test_each_test_file_imports_when_named_by_path(self):
        self.assert_each_test_file_imports()

    def test_each_test_file_imports_where_jsonschema_is_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (pathlib.Path(tmp) / "jsonschema.py").write_text(NO_JSONSCHEMA, encoding="utf-8")
            entries = filter(None, [tmp, os.environ.get("PYTHONPATH")])
            with mock.patch.dict(os.environ, {"PYTHONPATH": os.pathsep.join(entries)}):
                self.assert_each_test_file_imports(WITHOUT_JSONSCHEMA)

    def fixture(self, source):
        """A test file holding `source` beside a sibling `check_naming.py`, and its repository root.

        The root also holds `deps/aap_fixture_package.py`, a package no test file can
        import unless PYTHONPATH names `deps`.
        """
        root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        for name, text in (("scripts/check_naming.py", "ROOT = None\n"),
                           ("scripts/test_fixture.py", source),
                           ("deps/aap_fixture_package.py", "")):
            (root / name).parent.mkdir(exist_ok=True)
            (root / name).write_text(text, encoding="utf-8")
        return root / "scripts" / "test_fixture.py", root

    def fixture_error(self, source, *entries):
        """The import error of the fixture for `source`, run with PYTHONPATH naming `entries` of its root."""
        path, root = self.fixture(source)
        named = os.pathsep.join(str(root / entry) for entry in entries)
        with mock.patch.dict(os.environ, {"PYTHONPATH": named}):
            return import_error_by_path(path, root)

    def fixture_error_from(self, directory, python_path):
        """The import error of a fixture that imports the package, then the sibling.

        The run has `directory` of the fixture's root as its working directory and
        `python_path` as PYTHONPATH.
        """
        path, root = self.fixture("import aap_fixture_package\nimport check_naming\n")
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(root / directory)
        with mock.patch.dict(os.environ, {"PYTHONPATH": python_path}):
            return import_error_by_path(path, root)

    def assert_sibling_not_found(self, source, *entries):
        self.assertEqual(self.fixture_error(source, *entries), SIBLING_NOT_FOUND)

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

    def test_sibling_import_inside_a_test_method_without_insert_fails(self):
        self.assert_sibling_not_found("import unittest\n\n\nclass T(unittest.TestCase):\n"
                                      "    def test_x(self):\n        import check_naming\n"
                                      "        self.assertIsNone(check_naming.ROOT)\n")

    def test_from_import_of_a_sibling_inside_a_function_without_insert_fails(self):
        self.assert_sibling_not_found("def root():\n    from check_naming import ROOT\n    return ROOT\n")

    def test_insert_clears_a_sibling_import_inside_a_function(self):
        source = (f"import pathlib\nimport sys\n\n{INSERT}\n\n\n"
                  "def root():\n    import check_naming\n    return check_naming.ROOT\n")
        self.assertIsNone(self.fixture_error(source))

    def test_insert_inside_the_function_that_imports_does_not_clear_it(self):
        self.assert_sibling_not_found(f"import pathlib\nimport sys\n\n\ndef root():\n    {INSERT}\n"
                                      "    import check_naming\n    return check_naming.ROOT\n")

    def test_import_inside_a_function_of_a_module_that_is_not_a_sibling_is_not_made(self):
        source = "def package():\n    import aap_fixture_package\n    return aap_fixture_package\n"
        self.assertIsNone(self.fixture_error(source))

    def test_file_that_does_not_parse_fails_with_its_error(self):
        self.assertRegex(self.fixture_error("def root(:\n    import check_naming\n"), "^SyntaxError: ")

    def test_python_path_entry_that_is_the_directory_does_not_clear_it(self):
        self.assert_sibling_not_found("import check_naming\n", "scripts")

    def test_package_on_python_path_is_found(self):
        self.assertIsNone(self.fixture_error("import aap_fixture_package\n", "deps"))

    def test_package_is_not_found_without_its_python_path_entry(self):
        self.assertEqual(self.fixture_error("import aap_fixture_package\n"),
                         "ModuleNotFoundError: No module named 'aap_fixture_package'")

    def test_python_path_keeps_the_package_and_drops_the_directory(self):
        source = "import aap_fixture_package\nimport check_naming\n"
        self.assert_sibling_not_found(source, "scripts", "deps")
        self.assert_sibling_not_found(source, "deps", "scripts")

    def test_relative_python_path_entry_is_read_from_the_working_directory_of_the_run(self):
        entries = os.pathsep.join([".", os.path.join(os.pardir, "scripts")])
        self.assertEqual(self.fixture_error_from("deps", entries), SIBLING_NOT_FOUND)

    def test_empty_python_path_entry_is_the_working_directory_of_the_run(self):
        entries = os.pathsep.join(["", os.path.join(os.pardir, "deps")])
        self.assertEqual(self.fixture_error_from("scripts", entries), SIBLING_NOT_FOUND)

    def test_unset_or_empty_python_path_has_no_entry(self):
        with mock.patch.dict(os.environ, {"PYTHONPATH": ""}):
            self.assertEqual(python_path_without(SCRIPTS), [])
            del os.environ["PYTHONPATH"]
            self.assertEqual(python_path_without(SCRIPTS), [])

    def test_error_is_plain_text_when_the_run_forces_color(self):
        with mock.patch.dict(os.environ, {"FORCE_COLOR": "1", "PYTHON_COLORS": "1"}):
            os.environ.pop("NO_COLOR", None)
            self.assert_sibling_not_found("import check_naming\n")

    def test_import_writes_no_bytecode(self):
        source = f"import pathlib\nimport sys\n\n{INSERT}\n\nimport check_naming  # noqa: E402\n"
        path, root = self.fixture(source)
        self.assertIsNone(import_error_by_path(path, root))
        self.assertEqual(sorted(found.relative_to(root).as_posix() for found in root.rglob("*")),
                         ["deps", "deps/aap_fixture_package.py", "scripts",
                          "scripts/check_naming.py", "scripts/test_fixture.py"])

    def test_import_that_exits_with_nothing_on_standard_error_fails_with_the_exit_status(self):
        self.assertEqual(self.fixture_error("import sys\n\nsys.exit(3)\n"), "exit status 3")

    def test_failure_message_names_the_error_and_the_line_to_add(self):
        message = failure_message("scripts/test_x.py", SIBLING_NOT_FOUND, {"check_naming"})
        self.assertIn(f"python3 -m unittest scripts/test_x.py fails with {SIBLING_NOT_FOUND}", message)
        self.assertIn(INSERT, message)

    def test_failure_message_names_no_line_to_add_for_another_error(self):
        for error in ("ModuleNotFoundError: No module named 'jsonschema'",
                      "unittest.case.SkipTest: the 'jsonschema' package is required (pip install jsonschema)",
                      "exit status 3"):
            with self.subTest(error=error):
                self.assertEqual(failure_message("scripts/test_x.py", error, {"check_naming"}),
                                 f"python3 -m unittest scripts/test_x.py fails with {error}")


if __name__ == "__main__":
    unittest.main()
