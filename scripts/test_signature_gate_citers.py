#!/usr/bin/env python3
"""Tests for the specifications Section 9.4 names as citing its signature gate.

AAP-SPEC section 9.4 is the one home of the family signature gate and names the
specifications that cite it for their own signature arrays rather than restate it.
The names must be those of specifications that do cite it, so the sentence, the
0.5.1-draft changelog entry that describes it, and the same sentence in the XML source
of every Internet-Draft after the filed revisions -00 to -02 are checked against CITING
below. The text render of a revision is generated from its XML source, so the source is
the one read, except that the text render of the newest revision is also read.
draft-fane-opena2a-aap-02 is left as filed: its sentence names ATX, ATP and AIP, which
the 0.5.1-draft entry records. The newest revision must be a later one, so the newest
render names only the specifications that cite the gate. AIP is not in CITING:
AIP-SPEC.md does not mention AAP section 9.4. When a specification adds the citation,
add it to CITING and to each of these sentences.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_references  # noqa: E402
import check_status_claims  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILED_RENDER = "draft-fane-opena2a-aap-02.xml"

# Each specification that cites AAP section 9.4, with the text file that cites it.
CITING = {
    "ATX": "atx-spec/core.md",
    "ATP": "ATP-SPEC.md",
}

MARKER = "<!-- opena2a-definition: signature-family-gate -->"
SPEC_SENTENCE = re.compile(r"([A-Z][A-Za-z, ]*?) cite this rule for their own signature arrays")
CHANGELOG_CLAUSE = re.compile(r"`HYBRID_INCOMPLETE`\), which ([A-Z][A-Za-z, ]*?) (?:now )?cite\b")
# A line of a text render's page break: the footer, the form feed, the running header.
PAGE_BREAK_LINE = re.compile(r"\[Page \d+\]\s*$|\f|^Internet-Draft {2,}")


def names(phrase):
    """Return the names in a list such as "ATX, ATP and AIP"."""
    return [name.strip() for name in re.split(r",|\band\b", phrase) if name.strip()]


def gate_paragraph():
    text = (ROOT / "AAP-SPEC.md").read_text(encoding="utf-8")
    start = text.index(MARKER) + len(MARKER)
    return " ".join(text[start:].strip().split("\n\n", 1)[0].split())


def changelog_section(version):
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    start = text.index(f"## [{version}]")
    end = text.find("\n## [", start + 1)
    return " ".join(text[start:end if end != -1 else len(text)].split())


def render_citers(tree):
    """Return the names each paragraph of a parsed render gives as citing the gate."""
    found = []
    for paragraph in tree.iter("t"):
        match = SPEC_SENTENCE.search(" ".join("".join(paragraph.itertext()).split()))
        if match:
            found.append(names(match.group(1)))
    return found


def text_render_citers(path):
    """Return the names each sentence of a text render gives as citing the gate.

    The lines of each page break are dropped first, so a sentence that a page break
    splits reads as one.
    """
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if not PAGE_BREAK_LINE.search(line)]
    return [names(match.group(1)) for match in SPEC_SENTENCE.finditer(" ".join(" ".join(lines).split()))]


def later_renders(root):
    """Return the Internet-Draft XML sources after the filed revisions, in revision order."""
    drafts = []
    for path in root.glob("draft-fane-opena2a-aap-*.xml"):
        match = check_status_claims.DRAFT.fullmatch(path.name)
        if match and int(match.group(1)) > check_status_claims.LAST_FILED_REVISION:
            drafts.append((int(match.group(1)), path.name))
    return [name for _, name in sorted(drafts)]


def render_failures(root):
    """Return one reason per later render whose section 9.4 sentence is not CITING."""
    failures = []
    for name in later_renders(root):
        _, tree, error = check_references.read_render(root / name)
        if error:
            failures.append(f"{name}: {error}")
            continue
        citers = render_citers(tree)
        if not citers:
            failures.append(f"{name}: section 9.4 no longer names the specifications citing it")
        for found in citers:
            if sorted(found) != sorted(CITING):
                failures.append(f"{name}: section 9.4 names {', '.join(found)} as citing it;"
                                f" the specifications citing it are {', '.join(sorted(CITING))}")
    return failures


class SignatureGateCitersTest(unittest.TestCase):
    def test_names_reads_each_list_form(self):
        self.assertEqual(names("ATX, ATP and AIP"), ["ATX", "ATP", "AIP"])
        self.assertEqual(names("ATX and ATP"), ["ATX", "ATP"])
        self.assertEqual(names("ATP"), ["ATP"])

    def test_spec_names_the_citing_specifications(self):
        match = SPEC_SENTENCE.search(gate_paragraph())
        self.assertIsNotNone(match, "section 9.4 no longer names the specifications citing it")
        self.assertEqual(sorted(names(match.group(1))), sorted(CITING))

    def test_changelog_entry_names_the_citing_specifications(self):
        match = CHANGELOG_CLAUSE.search(changelog_section("0.5.1-draft"))
        self.assertIsNotNone(match, "the 0.5.1-draft entry no longer names the citing specifications")
        self.assertEqual(sorted(names(match.group(1))), sorted(CITING))

    def test_filed_render_is_left_as_filed(self):
        _, tree, error = check_references.read_render(ROOT / FILED_RENDER)
        self.assertIsNone(error)
        self.assertEqual(render_citers(tree), [["ATX", "ATP", "AIP"]])
        self.assertNotIn(FILED_RENDER, later_renders(ROOT))

    def test_later_renders_name_the_citing_specifications(self):
        self.assertEqual(render_failures(ROOT), [])

    def test_newest_render_names_the_citing_specifications(self):
        newest = check_references.newest_render(ROOT)
        self.assertIn(newest, later_renders(ROOT))
        _, tree, error = check_references.read_render(ROOT / newest)
        self.assertIsNone(error)
        self.assertEqual([sorted(found) for found in render_citers(tree)], [sorted(CITING)])
        text = (ROOT / newest).with_suffix(".txt")
        self.assertEqual([sorted(found) for found in text_render_citers(text)], [sorted(CITING)])

    def test_text_render_citers_reads_a_sentence_across_a_page_break(self):
        page_break = ("   otherwise it is rejected as \"HYBRID_INCOMPLETE\".  ATX and\n\n\n\n"
                      "Fane                     Expires 24 April 2027                  [Page 21]\n"
                      "\f\n"
                      "Internet-Draft                     AAP                      October 2026\n\n\n"
                      "   ATP cite this rule for their own signature arrays rather than\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "draft.txt"
            path.write_text(page_break, encoding="utf-8")
            self.assertEqual(text_render_citers(path), [["ATX", "ATP"]])
        filed = ROOT / FILED_RENDER.replace(".xml", ".txt")
        self.assertEqual(text_render_citers(filed), [["ATX", "ATP", "AIP"]])

    def test_a_later_render_naming_aip_fails(self):
        filed = (ROOT / FILED_RENDER).read_text(encoding="utf-8")
        corrected, count = re.subn(r"ATX, ATP and AIP cite\b", "ATX and ATP cite", filed)
        self.assertEqual(count, 1)
        dropped, count = re.subn(r"ATX, ATP and AIP cite\s+this rule for their own signature"
                                 r" arrays rather than restate it\.", "", filed)
        self.assertEqual(count, 1)
        cases = {
            filed: ["draft-fane-opena2a-aap-03.xml: section 9.4 names ATX, ATP, AIP as citing"
                    " it; the specifications citing it are ATP, ATX"],
            corrected: [],
            dropped: ["draft-fane-opena2a-aap-03.xml: section 9.4 no longer names the"
                      " specifications citing it"],
        }
        for text, expected in cases.items():
            with tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                (root / FILED_RENDER).write_text(filed, encoding="utf-8")
                (root / "draft-fane-opena2a-aap-03.xml").write_text(text, encoding="utf-8")
                self.assertEqual(render_failures(root), expected)

    def test_later_renders_are_ordered_by_revision_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for revision in ("01", "02", "03", "10"):
                (root / f"draft-fane-opena2a-aap-{revision}.xml").write_text("<rfc/>", encoding="utf-8")
            self.assertEqual(later_renders(root),
                             ["draft-fane-opena2a-aap-03.xml", "draft-fane-opena2a-aap-10.xml"])


if __name__ == "__main__":
    unittest.main()
