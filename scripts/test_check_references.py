#!/usr/bin/env python3
"""Tests for check_references.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py.
"""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_references  # noqa: E402
from check_references import (  # noqa: E402
    compare,
    markdown_references,
    newest_render,
    recorded_classes,
    render_references,
    submitted_renders,
)

SPEC_TEXT = """\
# Spec

See [ATP] and [AIP].

## 11. References

### Normative References
- [RFC 2119] / [RFC 8174], Key words for requirement levels.
- [ATP], Agent Trust Protocol.

### Informative References
- [AI Agent Threat Matrix], https://threats.opena2a.org
- [AAP-CONFORMANCE], AAP Conformance Suite.

## Authors' Addresses

- [NOT-A-REFERENCE], an address line.
"""

RENDER_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<rfc docName="draft-fane-opena2a-aap-09" version="3">
  <back>
    <references>
      <name>References</name>
    <references>
      <name>Normative References</name>
      <reference anchor="RFC2119" target="https://www.rfc-editor.org/info/rfc2119">
        <front><title>Key words for use in RFCs</title></front>
      </reference>
      <reference anchor="RFC8174" target="https://www.rfc-editor.org/info/rfc8174">
        <front><title>Ambiguity of Uppercase vs Lowercase</title></front>
      </reference>
      <reference anchor="ATP" target="https://specs.opena2a.org/atp">
        <front><title>Agent Trust Protocol (ATP)</title></front>
      </reference>
    </references>
    <references>
      <name>Informative References</name>
      <reference anchor="THREATMATRIX" target="https://threats.opena2a.org">
        <front><title>AI Agent
          Threat Matrix</title></front>
      </reference>
      <reference anchor="AAP-CONFORMANCE" target="https://github.com/opena2a-standards/aap-conformance">
        <front><title>AAP Conformance Suite</title></front>
      </reference>
      <reference anchor="RFC8792" target="https://www.rfc-editor.org/info/rfc8792">
        <front><title>Handling Long Lines</title></front>
      </reference>
    </references>
    </references>
  </back>
</rfc>
"""

CHANGELOG_TEXT = """\
# Changelog

## [Unreleased]

### Changed

- The grammar is AIP's. AIP is a normative
  reference. [AI Agent Threat Matrix] is an informative reference.

## [0.1.0] - 2026-01-01

- ATP is an informative reference.
"""


def render(*entries):
    """Build render entries from (anchor, class, target) triples with empty titles."""
    return [(anchor, "", ref_class, target) for anchor, ref_class, target in entries]


class ParseTest(unittest.TestCase):
    def test_markdown_entries_carry_their_class(self):
        self.assertEqual(
            markdown_references(SPEC_TEXT),
            [
                ("RFC 2119", "normative"),
                ("RFC 8174", "normative"),
                ("ATP", "normative"),
                ("AI Agent Threat Matrix", "informative"),
                ("AAP-CONFORMANCE", "informative"),
            ],
        )

    def test_markdown_without_references_section_has_no_entries(self):
        self.assertEqual(markdown_references("# Spec\n\n- [ATP], a list item.\n"), [])

    def test_render_entries_carry_class_title_and_target(self):
        entries = render_references(RENDER_XML)
        self.assertEqual(len(entries), 6)
        self.assertIn(
            ("THREATMATRIX", "AI Agent Threat Matrix", "informative", "https://threats.opena2a.org"),
            entries,
        )
        self.assertIn(("ATP", "Agent Trust Protocol (ATP)", "normative", "https://specs.opena2a.org/atp"), entries)

    def test_recorded_classes_read_only_the_unreleased_section(self):
        self.assertEqual(
            recorded_classes(CHANGELOG_TEXT),
            {
                "AIP": ("AIP", "normative"),
                "AIAGENTTHREATMATRIX": ("AI Agent Threat Matrix", "informative"),
            },
        )

    def test_lowercase_subject_is_not_a_recorded_class(self):
        self.assertEqual(recorded_classes("## [Unreleased]\n\nIt is a normative reference.\n"), {})

    def test_submitted_renders_read_the_pairing_records_of_released_sections(self):
        changelog = (
            "## [Unreleased]\n\n`draft-fane-opena2a-aap-04` (submitted 2026-12-01).\n\n"
            "## [0.5.1-draft] - 2026-10-02\n\n"
            "Internet-Draft pairing: `draft-fane-opena2a-aap-02` (submitted\n2026-10-02; document date\n"
            "2026-09-30) and `draft-fane-opena2a-aap-01` (submitted 2026-07-23) before it.\n\n"
            "## [0.5.0-draft] - 2026-09-08\n\n"
            "`draft-fane-opena2a-aap-03` was not submitted to the datatracker by this release;\n"
            "draft-fane-opena2a-aap-05 (submitted later) has no date.\n"
        )
        self.assertEqual(
            submitted_renders(changelog), {"draft-fane-opena2a-aap-01", "draft-fane-opena2a-aap-02"}
        )

    def test_newest_render_compares_draft_numbers_as_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            for name in ("draft-fane-opena2a-aap-02.xml", "draft-fane-opena2a-aap-10.xml", "draft-other-11.xml"):
                (root / name).write_bytes(RENDER_XML)
            self.assertEqual(newest_render(root), "draft-fane-opena2a-aap-10.xml")


class CompareTest(unittest.TestCase):
    def test_shared_references_in_the_same_class_pass(self):
        failures, summary = compare(
            markdown_references(SPEC_TEXT), render_references(RENDER_XML), {}, "draft.xml"
        )
        self.assertEqual(failures, [])
        self.assertIn("5 shared, 5 same class, 0 changed", summary)
        self.assertIn("only in the render: RFC8792", summary)

    def test_label_matches_render_title(self):
        failures, summary = compare(
            [("AI Agent Threat Matrix", "informative")],
            render_references(RENDER_XML),
            {},
            "draft.xml",
        )
        self.assertIn("1 shared, 1 same class", summary)
        self.assertNotIn("THREATMATRIX", summary.split("only in the render:")[1])

    def test_class_mismatch_fails(self):
        failures, _ = compare(
            [("AIP", "normative")],
            render(("AIP", "informative", "https://example.com/aip")),
            {},
            "draft.xml",
        )
        self.assertEqual(len(failures), 1)
        self.assertIn("[AIP] is normative in AAP-SPEC.md and informative in draft.xml", failures[0])
        self.assertIn('"AIP is a normative reference"', failures[0])

    def test_class_change_recorded_in_unreleased_passes(self):
        failures, summary = compare(
            [("AIP", "normative")],
            render(("AIP", "informative", "https://example.com/aip")),
            {"AIP": ("AIP", "normative")},
            "draft.xml",
        )
        self.assertEqual(failures, [])
        self.assertIn("1 changed since the render and recorded in CHANGELOG.md [Unreleased] (AIP normative)", summary)

    def test_class_change_recorded_in_unreleased_fails_in_the_next_render(self):
        failures, summary = compare(
            [("AIP", "normative")],
            render(("AIP", "informative", "https://example.com/aip")),
            {"AIP": ("AIP", "normative")},
            "draft.xml",
            submitted=False,
        )
        self.assertEqual(len(failures), 1)
        self.assertIn(
            "[AIP] is normative in AAP-SPEC.md and informative in draft.xml, the next render;"
            " CHANGELOG.md [Unreleased] records the change, so the next render must carry it",
            failures[0],
        )
        self.assertIn("0 changed since the render", summary)
        self.assertIn("draft.xml is the next render (no released section of CHANGELOG.md records it", summary)

    def test_summary_says_the_render_is_submitted(self):
        _, summary = compare([], [], {}, "draft.xml")
        self.assertTrue(summary.endswith("; draft.xml is submitted (CHANGELOG.md)"), summary)

    def test_recorded_class_the_markdown_does_not_carry_fails(self):
        failures, _ = compare(
            [("AIP", "informative")],
            render(("AIP", "normative", "https://example.com/aip")),
            {"AIP": ("AIP", "normative")},
            "draft.xml",
        )
        self.assertEqual(len(failures), 2)
        self.assertIn("lists it as informative", failures[1])

    def test_recorded_class_for_an_unlisted_reference_fails(self):
        failures, _ = compare([], [], {"AIP": ("AIP", "normative")}, "draft.xml")
        self.assertEqual(failures, ["CHANGELOG.md [Unreleased] records AIP as a normative reference; AAP-SPEC.md does not list it"])

    def test_family_reference_missing_from_markdown_fails(self):
        for target in (
            "https://github.com/opena2a-standards/aap-conformance",
            "https://specs.opena2a.org/atp",
            "https://opena2a.org/",
        ):
            with self.subTest(target=target):
                failures, _ = compare([], render(("FAMILY", "informative", target)), {}, "draft.xml")
                self.assertEqual(len(failures), 1)
                self.assertIn("is a family reference", failures[0])

    def test_other_render_only_reference_is_reported_not_failed(self):
        for target in (
            "https://www.rfc-editor.org/info/rfc8792",
            "https://opena2a.org.example.com/",
            "https://github.com/opena2a-standards-fork/x",
        ):
            with self.subTest(target=target):
                failures, summary = compare([], render(("OTHER", "informative", target)), {}, "draft.xml")
                self.assertEqual(failures, [])
                self.assertIn("only in the render: OTHER", summary)

    def test_duplicate_markdown_label_fails(self):
        failures, _ = compare([("ATP", "normative"), ("ATP", "informative")], [], {}, "draft.xml")
        self.assertEqual(failures, ["[ATP] is listed twice in AAP-SPEC.md"])


class CheckTest(unittest.TestCase):
    SPEC = SPEC_TEXT.replace(
        "- [ATP], Agent Trust Protocol.\n", "- [ATP], Agent Trust Protocol.\n- [AIP], Agent Identity Protocol.\n"
    )
    RENDER = RENDER_XML.replace(
        b'      <reference anchor="RFC8792"',
        b'      <reference anchor="AIP" target="https://example.org/AIP-SPEC.md">\n'
        b"        <front><title>Agent Identity Protocol</title></front>\n"
        b"      </reference>\n"
        b'      <reference anchor="RFC8792"',
    )
    SUBMITTED = "\nInternet-Draft pairing: `draft-fane-opena2a-aap-09` (submitted 2026-01-02).\n"

    def run_check(self, changelog):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "AAP-SPEC.md").write_text(self.SPEC, encoding="utf-8")
            (root / "draft-fane-opena2a-aap-09.xml").write_bytes(self.RENDER)
            (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                failures = check_references.check(root)
            return failures, out.getvalue()

    def test_recorded_change_passes_against_a_submitted_render(self):
        failures, out = self.run_check(CHANGELOG_TEXT + self.SUBMITTED)
        self.assertEqual(failures, 0, out)
        self.assertIn("1 changed since the render and recorded in CHANGELOG.md [Unreleased] (AIP normative)", out)
        self.assertIn("draft-fane-opena2a-aap-09.xml is submitted (CHANGELOG.md)", out)

    def test_recorded_change_fails_against_the_next_render(self):
        failures, out = self.run_check(CHANGELOG_TEXT)
        self.assertEqual(failures, 1, out)
        self.assertIn("[AIP] is normative in AAP-SPEC.md and informative in draft-fane-opena2a-aap-09.xml, the next render", out)

    def test_a_submission_recorded_in_unreleased_does_not_count(self):
        changelog = CHANGELOG_TEXT.replace("### Changed\n", "### Changed\n" + self.SUBMITTED)
        failures, out = self.run_check(changelog)
        self.assertEqual(failures, 1, out)


class RepositoryTest(unittest.TestCase):
    def test_spec_and_newest_render_agree(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            failures = check_references.check()
        self.assertEqual(failures, 0, out.getvalue())
        self.assertIn("reference classes AAP-SPEC.md vs draft-fane-opena2a-aap-", out.getvalue())

    def test_changelog_records_the_submitted_renders(self):
        changelog = (check_references.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertLessEqual(
            {"draft-fane-opena2a-aap-01", "draft-fane-opena2a-aap-02"}, submitted_renders(changelog)
        )

    def test_a_next_render_copied_from_the_02_render_must_list_aip_as_normative(self):
        # The -02 render lists AIP as informative; AAP-SPEC.md lists it as normative.
        root = check_references.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp)
            for name in ("AAP-SPEC.md", "CHANGELOG.md"):
                (copy / name).write_bytes((root / name).read_bytes())
            (copy / "draft-fane-opena2a-aap-03.xml").write_bytes(
                (root / "draft-fane-opena2a-aap-02.xml").read_bytes()
            )
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                failures = check_references.check(copy)
        self.assertGreaterEqual(failures, 1, out.getvalue())
        self.assertIn(
            "[AIP] is normative in AAP-SPEC.md and informative in draft-fane-opena2a-aap-03.xml", out.getvalue()
        )

    def test_spec_lists_the_conformance_suite_as_informative(self):
        spec = (check_references.ROOT / "AAP-SPEC.md").read_text(encoding="utf-8")
        self.assertIn(("AAP-CONFORMANCE", "informative"), markdown_references(spec))


if __name__ == "__main__":
    unittest.main()
