#!/usr/bin/env python3
"""Tests that no script in scripts/ imports a name it never reads.

An import a script does not use tells a reader that the script depends on a
module it does not touch. The tests parse every Python file in scripts/ and
fail on a name that an import binds and no expression reads. An import whose
line carries `# noqa` with no code, or with F401 among its codes, is kept: that
is how a script marks an import made for its effect, such as a probe for an
optional dependency. CI runs these tests through validate_examples.py.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import pathlib
import re
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent

NOQA = re.compile(r"#\s*noqa\b(?::\s*(?P<codes>[A-Z]+[0-9]+(?:[,\s]+[A-Z]+[0-9]+)*))?")


def kept(lines):
    """True if a line of an import carries `# noqa` with no code or with F401 among its codes."""
    for line in lines:
        marker = NOQA.search(line)
        if marker and (marker["codes"] is None or "F401" in re.split(r"[,\s]+", marker["codes"])):
            return True
    return False


def unused_imports(source):
    """The names the imports of `source` bind that no expression reads, in source order."""
    tree = ast.parse(source)
    lines = source.splitlines()
    read = {node.id for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    unused = []
    for node in sorted(imports, key=lambda node: (node.lineno, node.col_offset)):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if kept(lines[node.lineno - 1:node.end_lineno]):
            continue
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            if name != "*" and name not in read:
                unused.append(name)
    return unused


class UnusedImportsTest(unittest.TestCase):
    def test_no_script_imports_a_name_it_never_reads(self):
        scripts = sorted(SCRIPTS.glob("*.py"))
        self.assertIn(pathlib.Path(__file__).resolve(), scripts)
        for path in scripts:
            with self.subTest(script=path.name):
                self.assertEqual(unused_imports(path.read_text(encoding="utf-8")), [])

    def test_unused_import_is_detected(self):
        source = "import pathlib\nimport re\n\nPATTERN = re.compile('x')\n"
        self.assertEqual(unused_imports(source), ["pathlib"])

    def test_each_form_of_import_is_compared_by_the_name_it_binds(self):
        source = ("from __future__ import annotations\n"
                  "import os.path\n"
                  "import xml.etree.ElementTree as ET\n"
                  "from unittest import mock, TestCase\n"
                  "from re import *\n\n"
                  "print(os.path.sep, ET.Element, mock.patch)\n")
        self.assertEqual(unused_imports(source), ["TestCase"])

    def test_assigning_a_name_is_not_reading_it(self):
        self.assertEqual(unused_imports("import json\n\njson = None\n"), ["json"])

    def test_import_inside_a_block_is_examined(self):
        source = ("import pathlib\n\ntry:\n    import jsonschema\nexcept ImportError:\n    pass\n\n"
                  "import shutil\n")
        self.assertEqual(unused_imports(source), ["pathlib", "jsonschema", "shutil"])

    def test_import_marked_as_kept_is_skipped(self):
        for marker in ("# noqa", "# noqa: F401", "# noqa: E402, F401", "#noqa:F401 - probe"):
            with self.subTest(marker=marker):
                self.assertEqual(unused_imports(f"import jsonschema  {marker}\n"), [])

    def test_marker_for_another_rule_does_not_keep_an_import(self):
        self.assertEqual(unused_imports("import pathlib  # noqa: E402\n"), ["pathlib"])

    def test_marker_on_the_closing_line_of_an_import_keeps_it(self):
        source = "from unittest import (\n    mock,\n)  # noqa: F401\n"
        self.assertEqual(unused_imports(source), [])


if __name__ == "__main__":
    unittest.main()
