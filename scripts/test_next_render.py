#!/usr/bin/env python3
"""Tests that the next Internet-Draft revision is a render of the specification as it stands.

draft-fane-opena2a-aap-03 is the revision after the filed -00 to -02. A copy of the -02
source with its name changed keeps the -02 claim values and wording, so it does not
render AAP-SPEC.md as it stands. The tests check that the -03 source and its text
render are in the repository, that the source names its revision, and that the text
render names the revision and the date of the source. They check that each JSON
example of the next render (the newest render that no released section of
CHANGELOG.md records as submitted, as check_references.py reads it) equals, once its
RFC 8792 line folds are undone, one of the JSON files scripts/generate_examples.py
writes to examples/tokens/ (the claim sets and the general-form tokens). The filed -02
render fails that check: its CGT and DA examples carry the trust class "orders:read",
and the generated claim sets carry "acme.com/orders:read". The example test is
skipped when the newest render is recorded as submitted.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_references  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
REVISION = "draft-fane-opena2a-aap-03"
FILED_RENDER = "draft-fane-opena2a-aap-02.xml"
TOKENS = ROOT / "examples" / "tokens"

# RFC 8792 single backslash folding: the header line and the blank line after it, then
# a backslash that ends a line together with the leading spaces of the next line.
FOLD_HEADER = re.compile(r"\ANOTE: '\\' line wrapping per RFC 8792\n\n")
FOLD = re.compile(r"\\\n *")
# The date on the first page of a text render: "Intended status: ...  21 October 2026".
FIRST_PAGE_DATE = re.compile(r"^Intended status: .*?\s(\d{1,2} [A-Z][a-z]+ \d{4})$", re.MULTILINE)


def unfold(text):
    """Return the content of a block, with RFC 8792 single backslash folds undone."""
    if not FOLD_HEADER.match(text):
        return text
    return FOLD.sub("", FOLD_HEADER.sub("", text, count=1))


def parse(name):
    """Return the parsed root element of a render in the repository."""
    path = ROOT / name
    if not path.is_file():
        raise AssertionError(f"{name} not found")
    _, tree, error = check_references.read_render(path)
    if error:
        raise AssertionError(f"{name}: {error}")
    return tree


def examples(tree):
    """Return the JSON examples of a parsed render, parsed, in document order."""
    return [
        json.loads(unfold(code.text.strip("\n")))
        for code in tree.iter("sourcecode")
        if code.get("type") == "json"
    ]


def generated():
    """Return the parsed JSON files generate_examples.py writes to examples/tokens/."""
    paths = sorted([*TOKENS.glob("*.claims.json"), *TOKENS.glob("*.general.json")])
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def not_generated(tree):
    """Return the JSON examples of a parsed render that no generated file equals."""
    files = generated()
    return [example for example in examples(tree) if example not in files]


class UnfoldTest(unittest.TestCase):
    def test_a_folded_digest_is_joined(self):
        folded = (
            "NOTE: '\\' line wrapping per RFC 8792\n\n"
            '{"d":\n  "sha256:ab\\\n    cd"}'
        )
        self.assertEqual(json.loads(unfold(folded)), {"d": "sha256:abcd"})

    def test_a_block_without_the_header_is_read_as_written(self):
        self.assertEqual(unfold('{"d": "a\\\\"}'), '{"d": "a\\\\"}')


class RevisionTest(unittest.TestCase):
    def test_the_source_and_the_text_render_are_present(self):
        for suffix in (".xml", ".txt"):
            with self.subTest(suffix=suffix):
                self.assertTrue((ROOT / f"{REVISION}{suffix}").is_file(), f"{REVISION}{suffix} not found")

    def test_the_source_names_its_revision(self):
        tree = parse(f"{REVISION}.xml")
        self.assertEqual(tree.get("docName"), REVISION)
        series = [info.get("value") for info in tree.iter("seriesInfo") if info.get("name") == "Internet-Draft"]
        self.assertEqual(series, [REVISION])

    def test_the_text_render_names_the_revision_and_the_date_of_its_source(self):
        date = parse(f"{REVISION}.xml").find("front/date")
        source_date = f"{int(date.get('day'))} {date.get('month')} {date.get('year')}"
        path = ROOT / f"{REVISION}.txt"
        self.assertTrue(path.is_file(), f"{path.name} not found")
        text = path.read_text(encoding="utf-8")
        self.assertIn(REVISION, text.split("\nAbstract\n", 1)[0])
        first_page_date = FIRST_PAGE_DATE.search(text)
        self.assertIsNotNone(first_page_date, f"{path.name}: no date on the first page")
        self.assertEqual(first_page_date.group(1), source_date)


class ExampleTest(unittest.TestCase):
    def test_each_example_of_the_next_render_is_a_generated_file(self):
        name = check_references.newest_render(ROOT)
        if name is None or check_references.render_submitted(ROOT, name):
            self.skipTest(f"no next render: {name} is recorded as submitted")
        tree = parse(name)
        self.assertTrue(examples(tree), f"{name} has no JSON example")
        self.assertEqual(not_generated(tree), [], f"{name} carries an example no generated file equals")

    def test_the_filed_02_render_carries_examples_no_generated_file_equals(self):
        # A next render copied from the -02 source fails the test above on these.
        stale = not_generated(parse(FILED_RENDER))
        self.assertIn("orders:read", [example.get("trust_class") for example in stale])


if __name__ == "__main__":
    unittest.main()
