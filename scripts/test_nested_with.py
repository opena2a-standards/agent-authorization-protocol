#!/usr/bin/env python3
"""Tests that no script in scripts/ gains a `with` statement nested in another.

A `with` statement whose body is one other `with` statement and nothing else
spends two statements and two levels of indentation on what one statement that
names both context managers says. The tests parse every Python file of the
repository in scripts/ and the directories below it, and count the statements
written that way. Six test files held one each when these tests were added:
KNOWN lists them by path relative to scripts/ and the number each holds, and a
file passes only while it holds exactly that number, so it fails on a second
and fails when its statement is combined until its entry leaves KNOWN. A file
KNOWN does not list fails on its first, and a name KNOWN lists that is not the
path of one of those files fails. An `async with` and a `with` cannot share a
statement, so one that holds the other is not counted. CI runs these tests
through validate_examples.py.

In a git checkout the files of the repository are the ones git lists for
scripts/: those it tracks, and those it does not track and does not ignore. A
virtual environment in scripts/.venv/ or scripts/venv/, which .gitignore lists,
is not read. Where git is not installed or scripts/ is not in a git checkout,
they are the files in no directory whose name starts with ".", so a directory
that git would ignore and that is not hidden is read there.

CHANGELOG.md gives the rule the comment above KNOWN states and names that
comment as what says it. One test fails when the changelog gives the rule
after any other words or does not give it, and another when the comment no
longer states it. Both read a capital letter as its small one.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import pathlib
import shutil
import subprocess
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


def listed_by_git(root):
    """The Python files in `root` and below it that git tracks or does not ignore, or None.

    The paths are relative to `root`. An untracked file is given unless git
    ignores it. None is given when git is not installed or `root` is not in a
    git checkout.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others",
             "--exclude-standard", "--", "*.py"],
            capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [name for name in result.stdout.decode("utf-8").split("\0") if name]


def outside_hidden_directories(root):
    """The Python files in `root` and below it in no directory whose name starts with "."."""
    paths = [path.relative_to(root) for path in root.rglob("*.py")]
    return [path.as_posix() for path in paths
            if not any(part.startswith(".") for part in path.parts[:-1])]


def python_files(root):
    """The Python files of the repository in `root` and below it, by path relative to `root`.

    In a git checkout they are the files `listed_by_git` gives, so a file git
    ignores is not one of them. Otherwise they are the files
    `outside_hidden_directories` gives. A path is given once, and a path that
    is not a file below `root`, such as a tracked file deleted there, is left
    out.
    """
    names = listed_by_git(root)
    if names is None:
        names = outside_hidden_directories(root)
    return sorted(name for name in set(names) if (root / name).is_file())


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

    A line break or a run of spaces in `changelog` reads as one space, and a
    capital letter as its small one.
    """
    text = " ".join(changelog.split()).lower()
    rule = LEAVES_THE_TABLE.lower()
    return text.count(rule), text.count(f"{COMMENT_SAYS.lower()} {rule}")


def write(root, name):
    """Write a Python file `name` below `root`, in the directories its path names."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("pass\n", encoding="utf-8")


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
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch(f"{__name__}.listed_by_git", return_value=None):
            root = pathlib.Path(tmp)
            (root / "sub" / "deeper").mkdir(parents=True)
            for name in ("top.py", "sub/x.py", "sub/deeper/y.py", "sub/notes.txt"):
                (root / name).write_text("pass\n", encoding="utf-8")
            self.assertEqual(python_files(root), ["sub/deeper/y.py", "sub/x.py", "top.py"])

    @unittest.skipIf(shutil.which("git") is None, "git not installed")
    def test_in_a_git_checkout_files_git_ignores_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            shutil.copyfile(SCRIPTS.parent / ".gitignore", repo / ".gitignore")
            for name in ("other.py", "scripts/top.py", "scripts/gone.py", "scripts/new.py",
                         "scripts/sub/x.py", "scripts/.tools/run.py", "scripts/venv/kept.py",
                         "scripts/.venv/lib/site.py", "scripts/venv/lib/site.py"):
                write(repo, name)
            subprocess.run(["git", "-C", str(repo), "add", "--force", "scripts/top.py",
                            "scripts/gone.py", "scripts/venv/kept.py"], check=True)
            (repo / "scripts" / "gone.py").unlink()
            self.assertEqual(python_files(repo / "scripts"),
                             [".tools/run.py", "new.py", "sub/x.py", "top.py", "venv/kept.py"])

    def test_outside_a_git_checkout_files_in_hidden_directories_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch(f"{__name__}.listed_by_git", return_value=None):
            root = pathlib.Path(tmp)
            for name in ("top.py", ".x.py", ".venv/lib/site.py", "sub/.cache/y.py",
                         "venv/lib/site.py"):
                write(root, name)
            self.assertEqual(python_files(root), [".x.py", "top.py", "venv/lib/site.py"])

    def test_path_the_list_names_more_than_once_is_given_once(self):
        listed = ["top.py", "sub/x.py", "top.py", "top.py"]
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch(f"{__name__}.listed_by_git", return_value=listed):
            root = pathlib.Path(tmp)
            for name in ("top.py", "sub/x.py"):
                write(root, name)
            self.assertEqual(python_files(root), ["sub/x.py", "top.py"])

    @unittest.skipIf(shutil.which("git") is None, "git not installed")
    def test_path_git_lists_for_each_unmerged_stage_is_given_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            for name in ("scripts/top.py", "scripts/new.py"):
                write(repo, name)
            blob = subprocess.run(
                ["git", "-C", str(repo), "hash-object", "-w", "scripts/top.py"],
                capture_output=True, check=True, text=True).stdout.strip()
            # Stages 1, 2 and 3 of one path, which a merge leaves for a file with a
            # content conflict.
            stages = "".join(f"100644 {blob} {stage}\tscripts/top.py\n" for stage in (1, 2, 3))
            subprocess.run(["git", "-C", str(repo), "update-index", "--index-info"],
                           input=stages, check=True, text=True)
            self.assertEqual(sorted(listed_by_git(repo / "scripts")),
                             ["new.py", "top.py", "top.py", "top.py"])
            self.assertEqual(python_files(repo / "scripts"), ["new.py", "top.py"])

    def test_git_gives_no_list_when_it_fails_or_is_not_installed(self):
        for error in (subprocess.CalledProcessError(128, "git"), FileNotFoundError("git")):
            with self.subTest(error=error), mock.patch("subprocess.run", side_effect=error):
                self.assertIsNone(listed_by_git(SCRIPTS))

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

    def test_nested_with_in_a_subdirectory_fails_the_check_of_the_scripts(self):
        test = NestedWithTest("test_each_script_holds_the_number_known_records")
        nested, combined = "with a:\n    with b:\n        pass\n", "with a, b:\n    pass\n"
        for name, source, failures in (("sub/held.py", nested, 1),
                                       ("sub/deeper/held.py", nested, 1),
                                       ("sub/held.py", combined, 0)):
            result = unittest.TestResult()
            with self.subTest(name=name, failures=failures), \
                    tempfile.TemporaryDirectory() as tmp, \
                    mock.patch.dict(KNOWN, clear=True), \
                    mock.patch(f"{__name__}.listed_by_git", return_value=None), \
                    mock.patch(f"{__name__}.SCRIPTS", pathlib.Path(tmp)) as root:
                (root / name).parent.mkdir(parents=True)
                for path, text in ((pathlib.Path(__file__).name, "pass\n"), (name, source)):
                    (root / path).write_text(text, encoding="utf-8")
                test.run(result)
                self.assertEqual((len(result.failures), result.errors), (failures, []))

    @unittest.skipIf(shutil.which("git") is None, "git not installed")
    def test_subdirectory_test_passes_where_git_ignores_the_temporary_directory(self):
        test = NestedWithTest("test_nested_with_in_a_subdirectory_fails_the_check_of_the_scripts")
        result = unittest.TestResult()
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / ".gitignore").write_text("tmp/\n", encoding="utf-8")
            write(repo, "tmp/held.py")
            self.assertEqual(listed_by_git(repo / "tmp"), [])
            with mock.patch("tempfile.tempdir", str(repo / "tmp")):
                test.run(result)
        self.assertEqual((result.testsRun, result.failures, result.errors), (1, [], []))

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

    def test_rule_is_counted_whatever_its_capital_letters(self):
        sentence = LEAVES_THE_TABLE.capitalize()
        comment_says = COMMENT_SAYS[0].upper() + COMMENT_SAYS[1:]
        self.assertEqual(credits(f"- As the test's docstring says: {sentence}.\n"), (1, 0))
        self.assertEqual(credits(f"- The docstring says {LEAVES_THE_TABLE.upper()}.\n"), (1, 0))
        self.assertEqual(credits(f"- {comment_says}\n  {sentence}.\n"), (1, 1))

    def test_capitalized_rule_after_other_words_fails_the_check_of_the_changelog(self):
        changelog = (SCRIPTS.parent / "CHANGELOG.md").read_text(encoding="utf-8")
        added = f"- As the test's docstring says: {LEAVES_THE_TABLE.capitalize()}.\n"
        test = CommentAboveKnownTest(
            "test_changelog_gives_the_rule_only_as_what_the_comment_above_known_says")
        for text, failures in ((changelog, 0), (changelog + added, 1)):
            result = unittest.TestResult()
            reads = mock.patch.object(pathlib.Path, "read_text", return_value=text)
            with self.subTest(failures=failures), reads:
                test.run(result)
                self.assertEqual((len(result.failures), len(result.errors)), (failures, 0))

    def test_comment_above_is_the_run_of_comment_lines_before_the_assignment(self):
        source = "# Not this one.\n\n# First line\n# and second.\nKNOWN = {}\n"
        self.assertEqual(comment_above(source, "KNOWN"), "First line and second.")
        self.assertEqual(comment_above("x = 1\nKNOWN = {}\n", "KNOWN"), "")
        self.assertEqual(comment_above("# A comment.\nOTHER = {}\n", "KNOWN"), "")


if __name__ == "__main__":
    unittest.main()
