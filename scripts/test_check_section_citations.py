#!/usr/bin/env python3
"""Tests for check_section_citations.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py.
"""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_section_citations  # noqa: E402
from check_section_citations import (  # noqa: E402
    citations,
    reference_entries,
    render_references,
    section_numbers,
    unnamed_citations,
    unnamed_texts,
    unresolved,
)

SPEC_TEXT = """\
# Spec

## 4. Tokens

### 4.1 Purpose

The grammar is that of AIP Section 4.1. Negotiation is in broker profile §8.1.

## 11. References

### Normative References
- [AIP], Agent Identity Protocol (`AIP-SPEC.md`).

### Informative References
- [AAP-BROKER-PROFILE], AAP Broker & Resolution Layer (`AAP-BROKER-PROFILE.md`, this repository).
"""

PROFILE_TEXT = """\
# Profile

## 6. Resolution Flow

### 6.8 Presentation binding

## 8. Future-Proofing

### 8.1 Versioning and negotiation

```
## 9. A heading inside a code block
```
"""

RENDER_XML = """<?xml version="1.0" encoding="utf-8"?>
<rfc docName="draft-fane-opena2a-aap-03" version="3">
  <middle>
    <section><name>Tokens</name>
      <t>The grammar is that of AIP Section 4.1 <xref target="AIP"/>. Negotiation
      is in broker profile
      Section 8.1.</t>
    </section>
  </middle>
  <back>
    <references>
      <name>Informative References</name>
      <reference anchor="AIP" target="https://example.org/agent-identity-protocol/AIP-SPEC.md">
        <front><title>Agent Identity Protocol</title></front>
      </reference>
      <reference anchor="AAP-BROKER-PROFILE" target="https://example.org/aap/broker-profile">
        <front><title>AAP Broker &amp; Resolution Layer</title></front>
        <annotation>Section numbers are those of AAP-BROKER-PROFILE.md.</annotation>
      </reference>
    </references>
  </back>
</rfc>
"""

SUBMITTED_03 = """\
## [0.6.0-draft] - 2026-01-02

Internet-Draft pairing: `draft-fane-opena2a-aap-03` (submitted 2026-01-02).
"""


def found(text, file="doc.md"):
    """Return (document name, numbers, names its text file) for each citation in text."""
    return [(c.doc.name, c.numbers, c.names_text) for c in citations(file, text)]


class CitationTest(unittest.TestCase):
    def test_name_then_number_forms(self):
        cases = {
            "per AIP Section 4.1, the": [("AIP", ("4.1",), False)],
            "see broker profile §7, §11 and": [("broker profile", ("7", "11"), False)],
            "the broker profile Sections 6.8, 6.9 and 7.3 define": [
                ("broker profile", ("6.8", "6.9", "7.3"), False)
            ],
            "[`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md) §13-§14": [
                ("broker profile", ("13", "14"), True)
            ],
            "[`AAP-BROKER-PROFILE.md` §14](./AAP-BROKER-PROFILE.md#14-x)": [
                ("broker profile", ("14",), True)
            ],
            "the AIP-SPEC §7.2 policy actions": [("AIP", ("7.2",), True)],
            "(JCS over a projected TBS, `atx-spec/core.md` §1.3a.2)": [("ATX", ("1.3a.2",), True)],
            "(pipe-delimited string, ATP §4.3)": [("ATP", ("4.3",), False)],
            "the AAP-SPEC.md §9.6 conventions": [("AAP-SPEC", ("9.6",), True)],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(found(text), expected)

    def test_number_then_name_forms(self):
        self.assertEqual(found("the flow of §6 of the broker profile"), [("broker profile", ("6",), False)])
        self.assertEqual(found("(Section 4.4.1 of AAP-SPEC), narrowed"), [("AAP-SPEC", ("4.4.1",), True)])

    def test_a_singular_marker_does_not_take_a_bare_number(self):
        self.assertEqual(found("broker profile §6, step 3"), [("broker profile", ("6",), False)])

    def test_parenthesized_number_counts_only_after_a_document_name(self):
        self.assertEqual(found("of the broker profile (§6, step 3)"), [("broker profile", ("6",), False)])
        self.assertEqual(found("together with the agent's ATX (Section 6)."), [])
        self.assertEqual(found("an AIP (Section 4) agent"), [])

    def test_other_documents_and_bare_numbers_are_not_family_citations(self):
        for text in ("RFC 7519 §2", "RFC 9396 §10", "the §4 invariant", "(Section 8.1)", "ATP/ATX/AIP leave it"):
            with self.subTest(text=text):
                self.assertEqual(found(text), [])

    def test_names_inside_a_word_or_a_path_are_not_names(self):
        self.assertEqual(found("https://example.org/AIP-SPEC.md Section 4"), [])
        self.assertEqual(found("XAIP Section 4"), [])

    def test_a_citation_split_across_lines_carries_its_first_line(self):
        cites = citations("doc.md", "one\ntwo broker profile\n§8.1 three\n")
        self.assertEqual([(c.line, c.numbers) for c in cites], [(2, ("8.1",))])

    def test_unnamed_citation_of_the_spec_fails(self):
        failures = unnamed_citations("ex.md", "# Ex\n\n## 3. Flow (Section 6 of the spec)\n")
        self.assertEqual(len(failures), 1)
        self.assertIn('ex.md:3: "Section 6 of the spec" does not name its document', failures[0])
        self.assertEqual(unnamed_citations("ex.md", "## 3. Flow (Section 6 of the broker profile)\n"), [])


class ParseTest(unittest.TestCase):
    def test_section_numbers_skip_code_fences(self):
        self.assertEqual(section_numbers(PROFILE_TEXT), {"6", "6.8", "8", "8.1"})

    def test_reference_entries_read_both_label_forms_and_continuations(self):
        text = (
            "## 16. References\n\n### Normative\n\n"
            "- **ATP**, Agent Trust Protocol (`ATP-SPEC.md`).\n"
            "- **AIP**, Agent Identity Protocol,\n  `AIP-SPEC.md` on a continuation line.\n"
            "- **RFC 8693**, OAuth 2.0 Token Exchange.\n"
            "- [AAP-BROKER-PROFILE], AAP Broker & Resolution Layer.\n\n"
            "## 17. Related work\n\n- **ATX**, not a reference entry.\n"
        )
        entries = reference_entries(text)
        self.assertEqual(sorted(entries), ["AIP", "ATP", "broker profile"])
        self.assertIn("AIP-SPEC.md", entries["AIP"])

    def test_render_references_carry_target_and_annotation(self):
        references = render_references(ET.fromstring(RENDER_XML.encode()))
        self.assertEqual(references["AIP"], ("https://example.org/agent-identity-protocol/AIP-SPEC.md", ""))
        self.assertEqual(
            references["AAP-BROKER-PROFILE"],
            ("https://example.org/aap/broker-profile", "Section numbers are those of AAP-BROKER-PROFILE.md."),
        )


class RuleTest(unittest.TestCase):
    HEADINGS = {"AAP-SPEC.md": {"4", "4.1"}, "AAP-BROKER-PROFILE.md": {"6", "6.8", "8.1"}}

    def test_number_missing_from_a_local_document_fails(self):
        cites = citations("doc.md", "broker profile §6.8 and broker profile §6.2 and AAP-SPEC §4.4")
        failures = unresolved(cites, self.HEADINGS)
        self.assertEqual(len(failures), 2)
        self.assertIn("AAP-BROKER-PROFILE.md has no numbered heading 6.2", failures[0])
        self.assertIn("AAP-SPEC.md has no numbered heading 4.4", failures[1])

    def test_every_number_of_a_range_is_resolved(self):
        failures = unresolved(citations("doc.md", "broker profile §6-§7"), self.HEADINGS)
        self.assertEqual(len(failures), 1)
        self.assertIn("no numbered heading 7", failures[0])

    def test_numbers_of_an_outside_document_are_not_resolved_here(self):
        self.assertEqual(unresolved(citations("doc.md", "AIP Section 99.9"), self.HEADINGS), [])

    def test_listed_document_whose_entry_does_not_name_its_text_fails_once(self):
        cites = citations("doc.md", "ATP §4.3 and ATP Section 10.2")
        failures = unnamed_texts(cites, {"ATP": "- [ATP], Agent Trust Protocol."})
        self.assertEqual(len(failures), 1)
        self.assertIn("the ATP entry of the References section does not name ATP-SPEC.md", failures[0])

    def test_entry_that_names_its_text_passes(self):
        cites = citations("doc.md", "ATP §4.3 and broker profile §6")
        entries = {
            "ATP": "- [ATP], Agent Trust Protocol (`ATP-SPEC.md`).",
            "broker profile": "- [AAP-BROKER-PROFILE], AAP Broker (`AAP-BROKER-PROFILE.md`).",
        }
        self.assertEqual(unnamed_texts(cites, entries), [])

    def test_a_listed_document_needs_its_text_in_the_entry_even_when_the_citation_names_it(self):
        failures = unnamed_texts(citations("doc.md", "AIP-SPEC §7.2"), {"AIP": "- **AIP**, Agent Identity Protocol."})
        self.assertEqual(len(failures), 1)

    def test_outside_document_without_an_entry_must_be_named_in_the_citation(self):
        failures = unnamed_texts(citations("doc.md", "ATP Section 10.2"), {})
        self.assertEqual(len(failures), 1)
        self.assertIn("ATP is outside this repository; name ATP-SPEC.md", failures[0])
        self.assertEqual(unnamed_texts(citations("doc.md", "ATP-SPEC.md Section 10.2"), {}), [])

    def test_local_document_without_an_entry_passes(self):
        self.assertEqual(unnamed_texts(citations("doc.md", "broker profile §8.1, AAP-SPEC §4"), {}), [])


class CheckTest(unittest.TestCase):
    def run_check(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name, text in files.items():
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                if isinstance(text, bytes):
                    (root / name).write_bytes(text)
                else:
                    (root / name).write_text(text, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                failures = check_section_citations.check(root)
            return failures, out.getvalue()

    def base(self):
        return {
            "AAP-SPEC.md": SPEC_TEXT,
            "AAP-BROKER-PROFILE.md": PROFILE_TEXT,
            "draft-fane-opena2a-aap-03.xml": RENDER_XML,
        }

    def test_census_line_lists_citations_and_printed_addresses(self):
        failures, out = self.run_check(self.base())
        self.assertEqual(failures, 0, out)
        self.assertIn("ok    section citations of family documents:", out)
        self.assertIn("AAP-SPEC.md 2 (AIP 1, broker profile 1)", out)
        self.assertIn("draft-fane-opena2a-aap-03.xml 2 (AIP 1, broker profile 1)", out)
        self.assertIn(
            "printed address in draft-fane-opena2a-aap-03.xml:"
            " AIP https://example.org/agent-identity-protocol/AIP-SPEC.md (names AIP-SPEC.md),"
            " broker profile https://example.org/aap/broker-profile (names AAP-BROKER-PROFILE.md)",
            out,
        )

    def test_the_render_is_parsed_once(self):
        with mock.patch.object(ET, "fromstring", wraps=ET.fromstring) as fromstring:
            failures, out = self.run_check(self.base())
        self.assertEqual(failures, 0, out)
        self.assertEqual(fromstring.call_count, 1)

    def test_printed_address_that_does_not_name_the_text_is_reported_not_failed_in_a_submitted_render(self):
        files = self.base()
        files["draft-fane-opena2a-aap-03.xml"] = RENDER_XML.replace(
            "<annotation>Section numbers are those of AAP-BROKER-PROFILE.md.</annotation>", ""
        )
        files["CHANGELOG.md"] = SUBMITTED_03
        failures, out = self.run_check(files)
        self.assertEqual(failures, 0, out)
        self.assertIn(
            "broker profile https://example.org/aap/broker-profile (does not name AAP-BROKER-PROFILE.md);"
            " draft-fane-opena2a-aap-03.xml is submitted (CHANGELOG.md)",
            out,
        )

    def test_printed_address_that_does_not_name_the_text_fails_in_the_next_render(self):
        files = self.base()
        files["draft-fane-opena2a-aap-03.xml"] = RENDER_XML.replace(
            "<annotation>Section numbers are those of AAP-BROKER-PROFILE.md.</annotation>", ""
        )
        unreleased = "## [Unreleased]\n\n" + SUBMITTED_03.split("\n\n", 1)[1]
        for changelog in (None, SUBMITTED_03.replace("aap-03", "aap-02"), unreleased):
            with self.subTest(changelog=changelog):
                if changelog is None:
                    files.pop("CHANGELOG.md", None)
                else:
                    files["CHANGELOG.md"] = changelog
                failures, out = self.run_check(files)
                self.assertEqual(failures, 1, out)
                self.assertIn(
                    "FAIL  draft-fane-opena2a-aap-03.xml: broker profile is cited by section number and its"
                    " reference entry (https://example.org/aap/broker-profile) does not name"
                    " AAP-BROKER-PROFILE.md; the next render must print an address of AAP-BROKER-PROFILE.md"
                    " or name it in the entry's annotation",
                    out,
                )
                self.assertIn(
                    "draft-fane-opena2a-aap-03.xml is the next render (no released section of"
                    " CHANGELOG.md records it as submitted)",
                    out,
                )

    def test_next_render_passes_when_the_address_or_the_annotation_names_the_text(self):
        # RENDER_XML names AIP-SPEC.md in the AIP address and AAP-BROKER-PROFILE.md in the
        # broker profile annotation.
        failures, out = self.run_check(self.base())
        self.assertEqual(failures, 0, out)
        self.assertIn("draft-fane-opena2a-aap-03.xml is the next render", out)

    def test_render_number_missing_from_the_profile_fails(self):
        files = self.base()
        files["draft-fane-opena2a-aap-03.xml"] = RENDER_XML.replace("Section 8.1.", "Section 8.9.")
        failures, out = self.run_check(files)
        self.assertEqual(failures, 1, out)
        self.assertIn('draft-fane-opena2a-aap-03.xml:6: "broker profile Section 8.9"', out)
        self.assertIn("AAP-BROKER-PROFILE.md has no numbered heading 8.9", out)

    def test_render_citation_without_a_reference_entry_fails(self):
        files = self.base()
        files["draft-fane-opena2a-aap-03.xml"] = RENDER_XML.replace(
            "The grammar", "ATP Section 4.3 and the grammar"
        )
        failures, out = self.run_check(files)
        self.assertEqual(failures, 1, out)
        self.assertIn("ATP is cited by section number and has no reference entry", out)

    def test_only_the_newest_render_is_read(self):
        files = self.base()
        files["draft-fane-opena2a-aap-02.xml"] = RENDER_XML.replace("Section 8.1.", "Section 8.9.")
        failures, out = self.run_check(files)
        self.assertEqual(failures, 0, out)

    def test_changelog_and_decision_notes_are_not_checked(self):
        files = self.base()
        files["CHANGELOG.md"] = "- broker profile §6.2 was renumbered.\n"
        files["decisions/2026-01-01-note.md"] = "AAP-SPEC v0.3 broker profile §6.2, ATP §4.3.\n"
        failures, out = self.run_check(files)
        self.assertEqual(failures, 0, out)

    def test_other_markdown_is_checked(self):
        files = self.base()
        files["examples/flow.md"] = "## 3. Resolution flow (Section 6 of the spec)\n\nbroker profile §6.2\n"
        failures, out = self.run_check(files)
        self.assertEqual(failures, 2, out)
        self.assertIn("examples/flow.md:1:", out)
        self.assertIn("examples/flow.md:3:", out)

    def test_missing_local_document_fails(self):
        files = self.base()
        del files["AAP-BROKER-PROFILE.md"]
        failures, out = self.run_check(files)
        self.assertEqual(failures, 1, out)
        self.assertIn("AAP-BROKER-PROFILE.md not found", out)

    def test_render_that_is_not_utf8_or_not_well_formed_fails_without_a_traceback(self):
        # RENDER_XML ends with a line break, so its last line, "</rfc>", is line `lines`.
        lines = RENDER_XML.count("\n")
        data = RENDER_XML.encode("utf-8")
        for render, reason in (
            (
                data + b"<!-- caf\xe9 -->\n",
                f"line {lines + 1}: not valid UTF-8 (invalid continuation byte at byte"
                f" {len(data) + 8}); save the document as UTF-8",
            ),
            (
                RENDER_XML.replace("</rfc>", "<t></rfc>"),
                f"line {lines}: not well-formed XML (mismatched tag); correct the XML",
            ),
        ):
            with self.subTest(reason=reason):
                files = self.base()
                files["draft-fane-opena2a-aap-03.xml"] = render
                failures, out = self.run_check(files)
                self.assertEqual(failures, 1, out)
                self.assertIn(f"FAIL  draft-fane-opena2a-aap-03.xml: {reason}\n", out)
                # The Markdown documents are still checked.
                self.assertIn(
                    "FAIL  section citations of family documents: AAP-SPEC.md 2 (AIP 1,"
                    " broker profile 1); 1 failure(s); printed address in"
                    " draft-fane-opena2a-aap-03.xml: none",
                    out,
                )


class RepositoryTest(unittest.TestCase):
    def test_every_family_citation_resolves_and_names_its_text(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            failures = check_section_citations.check()
        self.assertEqual(failures, 0, out.getvalue())
        self.assertIn("printed address in draft-fane-opena2a-aap-", out.getvalue())

    def test_a_next_render_copied_from_the_02_render_must_print_an_address_of_the_broker_profile_text(self):
        # The -02 render cites broker profile Section 8.1 and prints
        # https://specs.opena2a.org/aap/broker-profile, which carries no section numbers.
        root = check_section_citations.ROOT
        render = (root / "draft-fane-opena2a-aap-02.xml").read_text(encoding="utf-8")
        failure = "draft-fane-opena2a-aap-03.xml: broker profile is cited by section number"
        blob = "https://github.com/opena2a-standards/agent-authorization-protocol/blob/main/AAP-BROKER-PROFILE.md"
        for text, fails in (
            (render, True),
            (render.replace('target="https://specs.opena2a.org/aap/broker-profile"', f'target="{blob}"'), False),
        ):
            with self.subTest(fails=fails), tempfile.TemporaryDirectory() as tmp:
                copy = pathlib.Path(tmp)
                for name in ("AAP-SPEC.md", "AAP-BROKER-PROFILE.md"):
                    (copy / name).write_bytes((root / name).read_bytes())
                (copy / "draft-fane-opena2a-aap-03.xml").write_text(text, encoding="utf-8")
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    check_section_citations.check(copy)
                if fails:
                    self.assertIn(failure, out.getvalue())
                else:
                    self.assertNotIn(failure, out.getvalue())
                    self.assertIn(f"broker profile {blob} (names AAP-BROKER-PROFILE.md)", out.getvalue())

    def test_reference_entries_name_the_text_of_each_family_document_cited_by_number(self):
        root = check_section_citations.ROOT
        spec = reference_entries((root / "AAP-SPEC.md").read_text(encoding="utf-8"))
        profile = reference_entries((root / "AAP-BROKER-PROFILE.md").read_text(encoding="utf-8"))
        for entries, name, text in (
            (spec, "AIP", "AIP-SPEC.md"),
            (spec, "ATP", "ATP-SPEC.md"),
            (spec, "ATX", "atx-spec/core.md"),
            (spec, "broker profile", "AAP-BROKER-PROFILE.md"),
            (profile, "AIP", "AIP-SPEC.md"),
            (profile, "ATP", "ATP-SPEC.md"),
        ):
            with self.subTest(name=name, text=text):
                self.assertIn(text, entries[name])


if __name__ == "__main__":
    unittest.main()
