#!/usr/bin/env python3
"""Tests that no script in scripts/ gains a `with` statement nested in another.

A `with` statement whose body is one other `with` statement and nothing else
spends two statements and two levels of indentation on what one statement that
names both context managers says. The tests parse every Python file in scripts/
and count the statements written that way. Six test files held one each when
these tests were added: KNOWN lists them, so each passes with the one it holds
and fails on a second. A file KNOWN does not list fails on its first. An
`async with` and a `with` cannot share a statement, so one that holds the other
is not counted. CI runs these tests through validate_examples.py.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import pathlib
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parent

# The files that held a nested `with` statement when these tests were added,
# and how many each held. A file leaves the table when its statements are
# combined.
KNOWN = {
    "test_check_naming.py": 1,
    "test_check_raw_html.py": 1,
    "test_check_requirement_references.py": 1,
    "test_check_spelling.py": 1,
    "test_check_status_claims.py": 1,
    "test_check_version_labels.py": 1,
}


def holds_one_with(node):
    """True if `node` is a `with` statement whose body is one `with` statement of its kind."""
    return (isinstance(node, (ast.With, ast.AsyncWith)) and len(node.body) == 1
            and type(node.body[0]) is type(node))


def nested_withs(source):
    """The line of each `with` statement of `source` that holds one it could take in, in order.

    Statements nested three deep or more combine into one, so only the
    outermost of them is given.
    """
    nodes = list(ast.walk(ast.parse(source)))
    held = {node.body[0] for node in nodes if holds_one_with(node)}
    return sorted(node.lineno for node in nodes if holds_one_with(node) and node not in held)


def unlisted(name, source):
    """The lines `nested_withs` gives for `source` after the number KNOWN records for `name`."""
    return nested_withs(source)[KNOWN.get(name, 0):]


class NestedWithTest(unittest.TestCase):
    def test_no_script_gains_a_nested_with_statement(self):
        scripts = sorted(SCRIPTS.glob("*.py"))
        self.assertIn(pathlib.Path(__file__).resolve(), scripts)
        for path in scripts:
            with self.subTest(script=path.name):
                self.assertEqual(unlisted(path.name, path.read_text(encoding="utf-8")), [])

    def test_listed_file_passes_with_what_it_held_and_fails_on_one_more(self):
        nested = "with a:\n    with b:\n        pass\n"
        with mock.patch.dict(KNOWN, {"listed.py": 1}):
            self.assertEqual(unlisted("listed.py", nested), [])
            self.assertEqual(unlisted("listed.py", nested * 2), [4])
            self.assertEqual(unlisted("other.py", nested), [1])

    def test_nested_with_is_detected(self):
        self.assertEqual(nested_withs("with a:\n    with b:\n        pass\n"), [1])

    def test_each_nested_with_of_a_file_is_given(self):
        source = ("with a:\n    with b:\n        pass\n\n\n"
                  "def run():\n    with c:\n        with d as e:\n            pass\n")
        self.assertEqual(nested_withs(source), [1, 7])

    def test_combined_with_is_not_reported(self):
        for source in ("with a, b:\n    pass\n", "with a, \\\n        b:\n    pass\n"):
            with self.subTest(source=source):
                self.assertEqual(nested_withs(source), [])

    def test_with_that_holds_another_statement_is_not_reported(self):
        for source in ("with a:\n    with b:\n        pass\n    done()\n",
                       "with a:\n    ready()\n    with b:\n        pass\n",
                       "with a:\n    for item in items:\n        with b:\n            pass\n"):
            with self.subTest(source=source):
                self.assertEqual(nested_withs(source), [])

    def test_statements_nested_three_deep_are_given_once(self):
        source = "with a:\n    with b:\n        with c:\n            pass\n"
        self.assertEqual(nested_withs(source), [1])

    def test_nested_async_with_is_detected(self):
        source = "async def run():\n    async with a:\n        async with b:\n            pass\n"
        self.assertEqual(nested_withs(source), [2])

    def test_async_with_and_with_are_not_counted_together(self):
        for inside, outside in (("with", "async with"), ("async with", "with")):
            with self.subTest(inside=inside, outside=outside):
                source = (f"async def run():\n    {outside} a:\n        {inside} b:\n"
                          "            pass\n")
                self.assertEqual(nested_withs(source), [])

    def test_with_statements_of_one_kind_inside_the_other_kind_are_given(self):
        source = ("async def run():\n    async with a:\n        with b:\n            with c:\n"
                  "                pass\n")
        self.assertEqual(nested_withs(source), [3])


if __name__ == "__main__":
    unittest.main()
