#!/usr/bin/env python3
"""Tests for check_requirement_references.py. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py.
"""

import contextlib
import io
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_requirement_references  # noqa: E402
from check_requirement_references import findings  # noqa: E402

REFERENCES = (
    "## 9. References\n\n"
    "### Normative\n\n"
    "- **RFC 2119 / RFC 8174**, Key words for requirement levels.\n"
    "- **RFC 8693**, OAuth 2.0 Token Exchange.\n\n"
    "### Informative\n\n"
    "- **RFC 6749 / RFC 6750**, OAuth 2.0 and Bearer Token Usage.\n"
    "- **RFC 7009**, OAuth 2.0 Token Revocation (a broker SHOULD read RFC 9999).\n\n"
    "---\n\n"
    "## 10. Related work\n\n"
    "RFC 7009 is related work.\n"
)


def document(body: str) -> str:
    return f"# Profile\n\n{body}\n\n{REFERENCES}"


class FindingsTest(unittest.TestCase):
    def test_informative_rfc_in_a_requirement_sentence_fails(self):
        text = document("Where the issuer supports it (RFC 7009), a broker SHOULD revoke it.")
        self.assertEqual(findings(text), [
            "line 3: RFC 7009 is listed only as an informative reference and is cited "
            "in a sentence with SHOULD"])

    def test_every_requirement_keyword_counts(self):
        for keyword in ("MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
                        "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", "OPTIONAL"):
            with self.subTest(keyword=keyword):
                text = document(f"A broker {keyword} use RFC 6750 bearer tokens.")
                self.assertIn(f"sentence with {keyword}", findings(text)[0])

    def test_lowercase_keyword_passes(self):
        self.assertEqual(findings(document("A broker should revoke it (RFC 7009).")), [])

    def test_both_rfcs_of_a_shared_label_are_read(self):
        text = document("A broker MUST NOT send RFC 6749 or RFC 6750 tokens.")
        self.assertEqual(len(findings(text)), 2)

    def test_normative_rfc_passes(self):
        self.assertEqual(findings(document("A broker MUST perform RFC 8693 exchange.")), [])

    def test_rfc_listed_in_both_classes_passes(self):
        text = document("A broker MUST revoke it (RFC 7009).").replace(
            "- **RFC 8693**", "- **RFC 7009**, OAuth 2.0 Token Revocation.\n- **RFC 8693**")
        self.assertEqual(findings(text), [])

    def test_informative_rfc_without_a_keyword_passes(self):
        self.assertEqual(findings(document("Token revocation is defined in RFC 7009.")), [])

    def test_keyword_in_another_sentence_passes(self):
        text = document("A broker MUST end the worker. Token revocation is RFC 7009.")
        self.assertEqual(findings(text), [])

    def test_keyword_in_another_list_item_passes(self):
        text = document("- A broker MUST end the worker\n- token revocation, RFC 7009")
        self.assertEqual(findings(text), [])

    def test_keyword_across_a_blank_line_passes(self):
        text = document("A broker MUST end the worker\n\nper RFC 7009 where supported.")
        self.assertEqual(findings(text), [])

    def test_wrapped_sentence_reports_the_line_of_the_citation(self):
        text = document("A broker SHOULD revoke an outstanding\ncredential through RFC 7009.")
        self.assertEqual(len(findings(text)), 1)
        self.assertIn("line 4:", findings(text)[0])

    def test_sentence_after_a_closing_bracket_is_split(self):
        text = document("Revocation uses (RFC 7009.) A broker MUST end the worker.")
        self.assertEqual(findings(text), [])

    def test_fenced_code_block_is_not_read(self):
        text = document("```\nA broker MUST revoke it (RFC 7009).\n```")
        self.assertEqual(findings(text), [])

    def test_references_section_is_not_read_but_a_later_section_is(self):
        self.assertEqual(findings(document("Intro.")), [])
        text = document("Intro.") + "\nA broker MUST NOT skip RFC 7009.\n"
        self.assertEqual(len(findings(text)), 1)

    def test_rfc_named_only_in_an_entry_description_is_not_listed(self):
        self.assertEqual(findings(document("A broker MUST read RFC 9999.")), [])

    def test_document_without_references_passes(self):
        self.assertEqual(findings("# Notes\n\nA broker SHOULD revoke it (RFC 7009).\n"), [])

    def test_markdown_bracket_labels_are_read(self):
        text = (
            "# Spec\n\nA verifier MUST check it [RFC 9162].\n\n## 11. References\n\n"
            "### Normative References\n- [RFC 2119] / [RFC 8174], Key words.\n\n"
            "### Informative References\n- [RFC 9162], Certificate Transparency.\n"
        )
        self.assertEqual(findings(text), [
            "line 3: RFC 9162 is listed only as an informative reference and is cited "
            "in a sentence with MUST"])


class RepositoryDocumentsTest(unittest.TestCase):
    def test_both_specification_documents_are_covered(self):
        names = check_requirement_references.documents()
        for name in ("AAP-SPEC.md", "AAP-BROKER-PROFILE.md"):
            with self.subTest(document=name):
                self.assertIn(name, names)
        self.assertNotIn("CHANGELOG.md", names)

    def test_repository_check_has_no_failures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_requirement_references.check(), 0)


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def test_failing_and_passing_documents_are_reported(self):
        (self.root / "PROFILE.md").write_text(
            document("A broker SHOULD revoke it (RFC 7009)."), encoding="utf-8")
        (self.root / "SPEC.md").write_text(document("Intro."), encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(
            "# Changelog\n\nA broker SHOULD revoke it (RFC 7009).\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_requirement_references.check(self.root), 1)
        self.assertIn(
            "FAIL  PROFILE.md: line 3: RFC 7009 is listed only as an informative reference "
            "and is cited in a sentence with SHOULD; list it as a normative reference, or "
            "state the sentence without the requirement keyword", out.getvalue())
        self.assertIn("ok    SPEC.md: no requirement cites an informative-only RFC",
                      out.getvalue())
        self.assertNotIn("CHANGELOG.md", out.getvalue())

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (3, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_requirement_references, "check",
                                       return_value=failures):
                    self.assertEqual(check_requirement_references.main(), code)


if __name__ == "__main__":
    unittest.main()
