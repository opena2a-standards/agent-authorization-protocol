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


def count(body: str) -> int:
    return len(findings(document(body)))


class SentenceTest(unittest.TestCase):
    def test_sentence_ends_at_a_question_or_exclamation_mark(self):
        for mark in "?!":
            with self.subTest(mark=mark):
                self.assertEqual(
                    count(f"Which worker MUST end{mark} Token revocation is RFC 7009."), 0)

    def test_sentence_ends_before_an_opening_quote_bracket_or_emphasis(self):
        for opening in ('"', "(", "[", "*", "**", "_", "`"):
            with self.subTest(opening=opening):
                self.assertEqual(
                    count(f"A broker MUST end the worker. {opening}Token revocation is RFC 7009."),
                    0)

    def test_sentence_ends_after_a_closing_quote_bracket_or_emphasis(self):
        for closing in ('"', "'", ")", "]", "*", "**", "_", "`"):
            with self.subTest(closing=closing):
                self.assertEqual(
                    count(f"A broker MUST end the worker.{closing} Token revocation is RFC 7009."),
                    0)

    def test_full_stop_before_a_lowercase_letter_or_digit_does_not_end_a_sentence(self):
        self.assertEqual(count("A broker MUST make approx. one RFC 7009 call."), 1)
        self.assertEqual(count("A broker MUST follow ver. 2 of RFC 7009."), 1)

    def test_full_stop_of_an_abbreviation_does_not_end_a_sentence(self):
        for abbreviation in ("e.g.", "i.e.", "cf.", "vs.", "viz.", "E.g.", "I.e."):
            with self.subTest(abbreviation=abbreviation):
                self.assertEqual(
                    count(f"A broker SHOULD revoke it at the issuer, {abbreviation} RFC 7009 "
                          "revocation."), 1)

    def test_word_that_ends_like_an_abbreviation_ends_a_sentence(self):
        self.assertEqual(count("A broker MUST parse the TLVs. Token revocation is RFC 7009."), 0)
        self.assertEqual(count("A broker MUST support DCF. Token revocation is RFC 7009."), 0)

    def test_full_stop_inside_a_code_span_does_not_end_a_sentence(self):
        self.assertEqual(count("A broker MUST call `revoke. Token` as RFC 7009 defines it."), 1)


class CitationTest(unittest.TestCase):
    def test_each_number_of_a_list_is_a_citation(self):
        for body, numbers in (
            ("A broker MUST NOT send RFCs 6749 and 6750 tokens.", ["6749", "6750"]),
            ("A broker MUST NOT send RFC 6749 and 6750 tokens.", ["6749", "6750"]),
            ("A broker MUST NOT send RFC 6749 or 6750 tokens.", ["6749", "6750"]),
            ("A broker MUST NOT send RFC 6749 / 6750 tokens.", ["6749", "6750"]),
            ("A broker MUST NOT send RFC 6749/6750 tokens.", ["6749", "6750"]),
            ("A broker MUST NOT use RFCs 6749, 6750 and 7009.", ["6749", "6750", "7009"]),
            ("A broker MUST NOT use RFCs 6749, 6750, or 7009.", ["6749", "6750", "7009"]),
            ("A broker MUST NOT use RFC6749.", ["6749"]),
        ):
            with self.subTest(body=body):
                self.assertEqual(
                    [reason.split()[3] for reason in findings(document(body))], numbers)

    def test_a_number_that_is_not_an_rfc_number_ends_the_list(self):
        cited = check_requirement_references.cited
        self.assertEqual(cited("RFC 6749 and 60 seconds"), [(4, "6749")])
        self.assertEqual(cited("RFC 6749 and 1780315500"), [(4, "6749")])
        self.assertEqual(cited("RFC 6749, Section 6750"), [(4, "6749")])
        self.assertEqual(cited("RFC 67490 and RFC 123456"), [(4, "67490")])
        self.assertEqual(cited("the RFCS 6749 and PRFC 6750"), [])

    def test_each_number_reports_its_own_line(self):
        text = document("A broker MUST NOT send RFC 6749 and\n6750 tokens.")
        self.assertEqual([reason.split(":")[0] for reason in findings(text)], ["line 3", "line 4"])

    def test_number_wrapped_onto_an_indented_line_is_read(self):
        text = document("- A broker SHOULD revoke the credential through RFC\n  7009 revocation.")
        self.assertEqual([reason.split(":")[0] for reason in findings(text)], ["line 4"])

    def test_label_with_a_list_of_numbers_is_read(self):
        for label, numbers in (
            ("RFCs 6749 and 6750", ["6749", "6750"]),
            ("RFCs 6749, 6750 and 7009", ["6749", "6750", "7009"]),
            ("RFC 6749 / 6750", ["6749", "6750"]),
            ("RFC 6749** / **RFC 6750", ["6749", "6750"]),
        ):
            with self.subTest(label=label):
                text = (f"# Profile\n\n## 9. References\n\n### Informative\n\n"
                        f"- **{label}**, OAuth 2.0 (see also RFC 9999).\n")
                _, informative, _ = check_requirement_references.references(text.split("\n"))
                self.assertEqual(sorted(informative), numbers)


class ContrastTest(unittest.TestCase):
    def test_rfc_named_for_contrast_passes(self):
        for phrase in ("Unlike", "In contrast to", "In contrast with", "As opposed to",
                       "Rather than", "Instead of"):
            with self.subTest(phrase=phrase):
                self.assertEqual(
                    count(f"{phrase} an RFC 6750 bearer token, a CGT MUST be bound to a key."), 0)
        self.assertEqual(count("A CGT MUST be bound to a key, unlike an RFC 6750 bearer token."), 0)
        self.assertEqual(
            count("A CGT MUST be bound to a key rather\nthan sent as an RFC 6750 bearer token."), 0)

    def test_citation_after_the_end_of_the_phrase_fails(self):
        for end in ",;:":
            with self.subTest(end=end):
                self.assertEqual(
                    count(f"Unlike a bearer token{end} RFC 7009 revocation MUST be supported."), 1)

    def test_citation_after_the_requirement_keyword_fails(self):
        self.assertEqual(count("Rather than polling a broker MUST use RFC 7009 revocation."), 1)

    def test_parenthesis_inside_the_phrase_does_not_end_it(self):
        self.assertEqual(
            count("Unlike a bearer token (RFC 6749, RFC 6750), a CGT MUST be bound to a key."), 0)

    def test_parenthesis_that_closes_around_the_phrase_ends_it(self):
        self.assertEqual(
            count("A CGT MUST be bound (unlike a bearer token) and revoked per RFC 7009."), 1)

    def test_phrase_followed_by_a_relative_clause_fails(self):
        for word in ("which", "that", "who", "whom", "whose", "where"):
            with self.subTest(word=word):
                self.assertEqual(
                    count(f"Unlike RFC 7009 revocation, {word} a broker MUST support, the list "
                          "is local."), 1)

    def test_word_that_begins_like_a_contrast_word_fails(self):
        self.assertEqual(count("A broker MUST treat as unlikely any RFC 7009 response."), 1)

    def test_only_the_citation_inside_the_phrase_passes(self):
        text = document("Unlike an RFC 6750 bearer token, an RFC 7009 request MUST be signed.")
        self.assertEqual([reason.split()[3] for reason in findings(text)], ["7009"])


class UnitTest(unittest.TestCase):
    def test_heading_is_a_unit_by_itself(self):
        self.assertEqual(count("## Revocation (RFC 7009)\nA broker MUST end the worker."), 0)
        self.assertEqual(count("A broker MUST end the worker\n## Revocation (RFC 7009)"), 0)
        self.assertEqual(count("### Revocation (RFC 7009)\n### A broker MUST end the worker"), 0)
        # The lines on either side of a heading are not one unit.
        self.assertEqual(
            count("A broker MUST end the worker\n## Revocation\ntoken revocation is RFC 7009"), 0)

    def test_heading_is_read(self):
        self.assertEqual(count("## A broker MUST use RFC 7009"), 1)

    def test_setext_underline_and_thematic_break_end_a_unit(self):
        for line in ("---", "===", "-", "***", "* * *", "___", "  ---  "):
            with self.subTest(line=line):
                self.assertEqual(
                    count(f"Revocation (RFC 7009)\n{line}\nA broker MUST end the worker."), 0)

    def test_line_of_text_that_begins_like_a_rule_does_not_end_a_unit(self):
        self.assertEqual(count("A broker MUST end the worker\n--- as in RFC 7009."), 1)

    def test_each_list_marker_begins_a_unit(self):
        for first, second in (("-", "-"), ("*", "*"), ("+", "+"), ("1.", "2."), ("1)", "2)"),
                              ("10.", "11.")):
            with self.subTest(marker=first):
                self.assertEqual(
                    count(f"{first} A broker MUST end the worker\n"
                          f"{second} token revocation, RFC 7009"), 0)

    def test_table_row_is_a_unit(self):
        self.assertEqual(
            count("| A broker MUST end the worker |\n| token revocation, RFC 7009 |"), 0)
        self.assertEqual(count("| Exchange | A broker MUST use RFC 7009 |"), 1)


class CodeAndCommentTest(unittest.TestCase):
    def test_keyword_inside_a_code_span_is_not_a_requirement(self):
        self.assertEqual(count("The `MUST` column of the table follows RFC 7009."), 0)
        self.assertEqual(count("The ``MUST`` column of the table follows RFC 7009."), 0)

    def test_rfc_inside_a_code_span_is_not_a_citation(self):
        self.assertEqual(count("A broker MUST send `RFC 7009` as the label."), 0)

    def test_fence_closes_only_on_the_same_character_and_at_least_the_same_length(self):
        for body in (
            "````\n```\nA broker MUST revoke it (RFC 7009).\n```\n````",
            "~~~\n```\nA broker MUST revoke it (RFC 7009).\n~~~",
            "```\n~~~\nA broker MUST revoke it (RFC 7009).\n```",
            "```\n``` text\nA broker MUST revoke it (RFC 7009).\n```",
        ):
            with self.subTest(body=body):
                self.assertEqual(count(body), 0)
                # The fence is closed: the text after it is read.
                self.assertEqual(count(f"{body}\n\nA broker MUST revoke it (RFC 7009)."), 1)

    def test_fence_that_holds_an_unclosed_shorter_fence_does_not_hide_the_document(self):
        text = document("````\n```\ncode\n````\n\nA broker MUST revoke it (RFC 7009).")
        normative, informative, _ = check_requirement_references.references(
            check_requirement_references.blocks(text.split("\n")))
        self.assertEqual(sorted(normative), ["2119", "8174", "8693"])
        self.assertEqual(sorted(informative), ["6749", "6750", "7009"])
        self.assertEqual([reason.split(":")[0] for reason in findings(text)], ["line 8"])

    def test_fence_inside_the_references_section_is_not_read(self):
        text = document("A broker MUST revoke it (RFC 7009).").replace(
            "- **RFC 8693**",
            "```\n### Informative\n```\n\n"
            "- **RFC 7009**, OAuth 2.0 Token Revocation.\n- **RFC 8693**")
        self.assertEqual(findings(text), [])

    def test_indented_code_block_is_not_read(self):
        self.assertEqual(count("Example:\n\n    A broker MUST revoke it (RFC 7009)."), 0)
        self.assertEqual(count("Example:\n\n\tA broker MUST revoke it (RFC 7009)."), 0)
        self.assertEqual(
            count("Example:\n\n    A broker MUST revoke it\n\n    through RFC 7009."), 0)

    def test_line_indented_three_spaces_is_prose(self):
        self.assertEqual(count("Example:\n\n   A broker MUST revoke it (RFC 7009)."), 1)

    def test_indented_line_that_continues_a_paragraph_is_prose(self):
        for body in ("A broker SHOULD revoke an outstanding\n    credential (RFC 7009).",
                     "- A broker SHOULD revoke an outstanding\n      credential (RFC 7009)."):
            with self.subTest(body=body):
                self.assertEqual(count(body), 1)

    def test_indented_line_after_a_heading_fence_or_comment_is_code(self):
        for before in ("## Example", "Text\n```\ncode\n```", "Text\n<!--\nnote\n-->"):
            with self.subTest(before=before):
                self.assertEqual(count(f"{before}\n    A broker MUST revoke it (RFC 7009)."), 0)

    def test_paragraph_of_a_list_item_is_prose_and_its_indented_block_is_code(self):
        for item, prose, code in (("- Step.", 5, 6), ("1. Step.", 6, 7), ("10. Step.", 7, 8),
                                  ("-   Step.", 7, 8), ("-     Step.", 5, 6)):
            with self.subTest(item=item):
                body = "{}\n\n{}A broker MUST revoke it (RFC 7009)."
                self.assertEqual(count(body.format(item, " " * prose)), 1)
                self.assertEqual(count(body.format(item, " " * code)), 0)

    def test_nested_list_item_moves_the_code_indentation(self):
        body = "- Outer.\n  - Inner.\n{}\n{}A broker MUST revoke it (RFC 7009)."
        self.assertEqual(count(body.format("", " " * 7)), 1)
        self.assertEqual(count(body.format("", " " * 8)), 0)
        # A later item of the outer list closes the inner one.
        self.assertEqual(count(body.format("- Next.\n", " " * 5)), 1)
        self.assertEqual(count(body.format("- Next.\n", " " * 6)), 0)

    def test_text_after_a_list_closes_it(self):
        self.assertEqual(
            count("- Step.\n\nExample:\n\n    A broker MUST revoke it (RFC 7009)."), 0)

    def test_html_comment_is_not_read(self):
        for body in (
            "<!-- MUST --> See RFC 7009.",
            "A broker MUST revoke it. <!-- RFC 7009 -->",
            "A broker MUST revoke it <!-- as in\nRFC 7009 --> at the issuer.",
            "<!--\nA broker MUST revoke it (RFC 7009).\n\nIt SHOULD use RFC 7009.\n-->",
            "<!--\nnote\nA broker MUST --> use RFC 7009.",
        ):
            with self.subTest(body=body):
                self.assertEqual(count(body), 0)

    def test_text_around_an_html_comment_is_read(self):
        for body in (
            "<!-- note --> A broker MUST revoke it (RFC 7009).",
            "A broker MUST <!-- note --> revoke it (RFC 7009).",
            "<!--\nnote\n--> A broker MUST revoke it (RFC 7009).",
            "<!--\nnote\n-->\n\nA broker MUST revoke it (RFC 7009).",
        ):
            with self.subTest(body=body):
                self.assertEqual(count(body), 1)

    def test_fence_inside_a_comment_and_comment_inside_a_fence_do_not_hide_the_text_after(self):
        self.assertEqual(count("<!--\n```\n-->\n\nA broker MUST revoke it (RFC 7009)."), 1)
        self.assertEqual(count("```\n<!--\n```\n\nA broker MUST revoke it (RFC 7009)."), 1)

    def test_comment_inside_a_code_span_is_not_a_comment(self):
        self.assertEqual(count("Write `<!--` first. A broker MUST send RFC 7009 before `-->`."), 1)


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

    def test_failure_line_names_the_wording_that_passes_for_a_contrast(self):
        (self.root / "PROFILE.md").write_text(
            document("A broker SHOULD revoke it (RFC 7009)."), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            check_requirement_references.check(self.root)
        self.assertIn(
            'requirement keyword (an RFC named only for contrast passes after "unlike", '
            '"in contrast to", "as opposed to", "rather than" or "instead of")\n', out.getvalue())

    def test_document_that_is_not_utf8_fails_without_a_traceback(self):
        (self.root / "PROFILE.md").write_bytes(
            b"caf\xe9\n\n" + document("Intro.").encode("utf-8"))
        (self.root / "SPEC.md").write_text(document("Intro."), encoding="utf-8")
        # Not a document of this check: it has no References section.
        (self.root / "NOTES.md").write_bytes(b"A broker SHOULD revoke it (RFC 7009). caf\xe9\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_requirement_references.check(self.root), 1)
        self.assertEqual(out.getvalue().splitlines(), [
            "FAIL  PROFILE.md: line 1: not valid UTF-8 (invalid continuation byte at byte 3); "
            "save the document as UTF-8",
            "ok    SPEC.md: no requirement cites an informative-only RFC",
        ])

    def test_main_exit_code_follows_the_failure_count(self):
        for failures, code in ((0, 0), (1, 1), (3, 1)):
            with self.subTest(failures=failures):
                with mock.patch.object(check_requirement_references, "check",
                                       return_value=failures):
                    self.assertEqual(check_requirement_references.main(), code)


if __name__ == "__main__":
    unittest.main()
