#!/usr/bin/env python3
"""Tests that no script in scripts/ gains a `with` statement nested in another.

A `with` statement whose body is one other `with` statement and nothing else
spends two statements and two levels of indentation on what one statement that
names both context managers says. The tests parse every Python file in scripts/
and the directories below it, and count the statements written that way. Six
test files held one each when these tests were added: KNOWN lists them by path
relative to scripts/ and the number each holds, and a file passes only while it
holds exactly that number, so it fails on a second and fails when its statement
is combined until its entry leaves KNOWN. A file KNOWN does not list fails on
its first, and a name KNOWN lists that is not the path of one of those files
fails. An `async with` and a `with` cannot share a statement, so one that holds
the other is not counted. CI runs these tests through validate_examples.py.

CHANGELOG.md gives the rule the comment above KNOWN states and names that
comment as what says it. One test fails when the changelog gives the rule
after any other words or does not give it, and another when the comment no
longer states it.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import pathlib
import tempfile
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parent

# The files that held a nested `with` statement when these tests were added,
# by path relative to scripts/, and how many each held. A file leaves the table
# when its statements are combined, and the tests fail until it does.
KNOWN = {
    "test_check_naming.py": 1,
    "test_check_raw_html.py": 1,
    "test_check_requirement_references.py": 1,
    "test_check_spelling.py": 1,
    "test_check_status_claims.py": 1,
    "test_check_version_labels.py": 1,
}

# The rule the comment above KNOWN states, in the words CHANGELOG.md gives it
# in, and the words the changelog gives it after.
LEAVES_THE_TABLE = "a file leaves the table when its statements are combined"
COMMENT_SAYS = "the comment above `KNOWN` says"


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


def miscount(name, source):
    """The lines `nested_withs` gives for `source`, or None if KNOWN records that many for `name`.

    KNOWN records none for a file it does not list.
    """
    lines = nested_withs(source)
    return None if len(lines) == KNOWN.get(name, 0) else lines


def absent(names):
    """The names KNOWN lists that are not among `names`, sorted."""
    return sorted(set(KNOWN) - set(names))


def python_files(root):
    """Every Python file in `root` and the directories below it, by path relative to `root`."""
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*.py"))


def comment_above(source, name):
    """The comment that ends on the line before the one that assigns `name` in `source`.

    The comment is the run of lines that start with "#" and end there, joined
    into one line without the "#". It is "" when the line before the
    assignment is not such a line, or no line starts with the assignment.
    """
    lines = source.splitlines()
    end = next((at for at, line in enumerate(lines) if line.startswith(f"{name} = ")), 0)
    start = end
    while start and lines[start - 1].startswith("#"):
        start -= 1
    return " ".join(line.lstrip("#").strip() for line in lines[start:end])


def credits(changelog):
    """How often `changelog` has LEAVES_THE_TABLE, and how often directly after COMMENT_SAYS.

    A line break or a run of spaces in `changelog` reads as one space.
    """
    text = " ".join(changelog.split())
    return text.count(LEAVES_THE_TABLE), text.count(f"{COMMENT_SAYS} {LEAVES_THE_TABLE}")


class NestedWithTest(unittest.TestCase):
    def test_each_script_holds_the_number_known_records(self):
        scripts = python_files(SCRIPTS)
        self.assertIn(pathlib.Path(__file__).name, scripts)
        self.assertEqual(absent(scripts), [])
        for name in scripts:
            with self.subTest(script=name):
                self.assertIsNone(miscount(name, (SCRIPTS / name).read_text(encoding="utf-8")),
                                  f"KNOWN records {KNOWN.get(name, 0)}")

    def test_files_in_subdirectories_are_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "sub" / "deeper").mkdir(parents=True)
            for name in ("top.py", "sub/x.py", "sub/deeper/y.py", "sub/notes.txt"):
                (root / name).write_text("pass\n", encoding="utf-8")
            self.assertEqual(python_files(root), ["sub/deeper/y.py", "sub/x.py", "top.py"])

    def test_listed_name_does_not_cover_a_file_of_that_name_in_a_subdirectory(self):
        nested = "with a:\n    with b:\n        pass\n"
        with mock.patch.dict(KNOWN, {"listed.py": 1}, clear=True):
            self.assertEqual(miscount("sub/listed.py", nested), [1])
            self.assertEqual(absent(["sub/listed.py"]), ["listed.py"])

    def test_listed_file_passes_with_what_it_held_and_fails_on_one_more(self):
        nested = "with a:\n    with b:\n        pass\n"
        with mock.patch.dict(KNOWN, {"listed.py": 1}):
            self.assertIsNone(miscount("listed.py", nested))
            self.assertEqual(miscount("listed.py", nested * 2), [1, 4])
            self.assertEqual(miscount("other.py", nested), [1])
            self.assertIsNone(miscount("other.py", "x = 1\n"))

    def test_listed_file_fails_when_it_holds_fewer_than_known_records(self):
        nested = "with a:\n    with b:\n        pass\n"
        with mock.patch.dict(KNOWN, {"listed.py": 2}):
            self.assertEqual(miscount("listed.py", nested), [1])
            self.assertEqual(miscount("listed.py", "x = 1\n"), [])

    def test_name_known_lists_that_is_not_a_script_is_given(self):
        with mock.patch.dict(KNOWN, {"kept.py": 1, "gone.py": 1}, clear=True):
            self.assertEqual(absent(["kept.py", "other.py"]), ["gone.py"])
            self.assertEqual(absent(["gone.py", "kept.py"]), [])

    def test_stale_entry_fails_the_check_of_the_scripts(self):
        test = NestedWithTest("test_each_script_holds_the_number_known_records")
        for entry in ({pathlib.Path(__file__).name: 1}, {"gone.py": 1}):
            result = unittest.TestResult()
            with self.subTest(entry=entry), mock.patch.dict(KNOWN, entry):
                test.run(result)
                self.assertEqual(len(result.failures), 1)

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


class CommentAboveKnownTest(unittest.TestCase):
    def test_comment_above_known_states_the_rule_the_changelog_gives(self):
        source = pathlib.Path(__file__).resolve().read_text(encoding="utf-8")
        self.assertIn(LEAVES_THE_TABLE, comment_above(source, "KNOWN").lower())

    def test_changelog_gives_the_rule_only_as_what_the_comment_above_known_says(self):
        changelog = (SCRIPTS.parent / "CHANGELOG.md").read_text(encoding="utf-8")
        given, after_comment_says = credits(changelog)
        self.assertGreater(given, 0)
        self.assertEqual(after_comment_says, given)

    def test_rule_given_after_other_words_is_not_counted_with_the_comment(self):
        entry = f"- A stale entry stayed although {COMMENT_SAYS}\n  {LEAVES_THE_TABLE}.\n"
        docstring = entry.replace(COMMENT_SAYS, "the test's docstring says")
        self.assertEqual(credits(entry), (1, 1))
        self.assertEqual(credits(docstring), (1, 0))
        self.assertEqual(credits(entry + docstring), (2, 1))
        self.assertEqual(credits("- No entry gives the rule.\n"), (0, 0))

    def test_comment_above_is_the_run_of_comment_lines_before_the_assignment(self):
        source = "# Not this one.\n\n# First line\n# and second.\nKNOWN = {}\n"
        self.assertEqual(comment_above(source, "KNOWN"), "First line and second.")
        self.assertEqual(comment_above("x = 1\nKNOWN = {}\n", "KNOWN"), "")
        self.assertEqual(comment_above("# A comment.\nOTHER = {}\n", "KNOWN"), "")


if __name__ == "__main__":
    unittest.main()
