#!/usr/bin/env python3
"""Tests that each test file in scripts/ runs on its own when named by path.

`python3 -m unittest scripts/test_x.py` imports the file without putting
scripts/ on sys.path, so a test file that imports a sibling script (`import
check_naming`) fails with ModuleNotFoundError unless it first inserts its own
directory, as in `sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`.
The documented discover run hides the gap, because `-s scripts` puts scripts/ on
sys.path. The tests parse every test file and fail on an import of a sibling
script that comes before a module-level `sys.path.insert` of a path built from
`__file__`. CI runs these tests through validate_examples.py.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import pathlib
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent


def inserts_own_directory(node):
    """True if `node` is a statement `sys.path.insert(...)` whose path is built from `__file__`."""
    if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
        return False
    call = node.value
    if ast.unparse(call.func) != "sys.path.insert" or len(call.args) != 2:
        return False
    return any(isinstance(name, ast.Name) and name.id == "__file__" for name in ast.walk(call.args[1]))


def sibling_imports_before_insert(source, siblings):
    """The sibling modules `source` imports before it inserts its own directory, in source order."""
    tree = ast.parse(source)
    inserted_at = next((node.lineno for node in tree.body if inserts_own_directory(node)), None)
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    early = []
    for node in sorted(imports, key=lambda node: (node.lineno, node.col_offset)):
        if inserted_at is not None and node.lineno > inserted_at:
            continue
        if isinstance(node, ast.ImportFrom):
            names = [node.module] if node.level == 0 and node.module else []
        else:
            names = [alias.name for alias in node.names]
        early.extend(name.split(".")[0] for name in names if name.split(".")[0] in siblings)
    return early


class SiblingImportsTest(unittest.TestCase):
    def test_each_test_file_inserts_its_directory_before_importing_a_sibling(self):
        siblings = {path.stem for path in SCRIPTS.glob("*.py")}
        tests = sorted(SCRIPTS.glob("test_*.py"))
        self.assertIn(pathlib.Path(__file__).resolve(), tests)
        for path in tests:
            with self.subTest(test=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertEqual(sibling_imports_before_insert(source, siblings), [])

    def test_sibling_import_without_insert_is_detected(self):
        source = "import re\n\nimport check_naming\n"
        self.assertEqual(sibling_imports_before_insert(source, {"check_naming"}), ["check_naming"])

    def test_insert_before_the_import_clears_it(self):
        source = ("import pathlib\nimport sys\n\n"
                  "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))\n\n"
                  "import check_naming  # noqa: E402\n")
        self.assertEqual(sibling_imports_before_insert(source, {"check_naming"}), [])

    def test_insert_after_the_import_does_not_clear_it(self):
        source = ("import pathlib\nimport sys\n\nimport check_naming\n\n"
                  "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))\n")
        self.assertEqual(sibling_imports_before_insert(source, {"check_naming"}), ["check_naming"])

    def test_insert_of_a_path_not_built_from_the_file_does_not_clear_it(self):
        source = "import sys\n\nsys.path.insert(0, 'elsewhere')\n\nimport check_naming\n"
        self.assertEqual(sibling_imports_before_insert(source, {"check_naming"}), ["check_naming"])

    def test_from_import_of_a_sibling_is_detected(self):
        source = "import unittest\nfrom check_references import newest_render\n"
        self.assertEqual(sibling_imports_before_insert(source, {"check_references"}),
                         ["check_references"])


if __name__ == "__main__":
    unittest.main()
