#!/usr/bin/env python3
"""Tests that the worked example marks the steps the v1 reference does not perform.

examples/orders-db-exchange.md walks the v1 resolution in numbered steps. A step
the v1 reference implementation does not perform carries a "v1:" note ("v1: audit
record written, not signed" on step 7), so the flow does not present the step as
performed, and the paragraph after the flow names the form of such a note by
quoting one that a step carries. The policy sample carries no "v1:" note, and its
`match` clause carries only predicates that broker profile Section 7.1, in the
sentence that names them, has a broker evaluate at every conformance level: the
flow grants the sample at step 3, the v1 reference targets Level 1, and under
Section 7.1 a broker that does not evaluate a predicate refuses at load a clause
carrying it. The note under the sample names each predicate of the Section 7.1
clause that the sample leaves out, and the example's reference spelling note
names `issuerChainIncludes` and `jurisdiction` and says what the reference
implementation does with them. Version negotiation is also marked as a
conformance Level 2 requirement (broker profile Section 13). The implementation
status note of broker profile Section 14 names the signature on audit records
among what its list does not describe.

The paragraph after the flow cites, for each of the three steps, the broker
profile section that defines it: the first broker profile section the paragraph
names after "(step N)" has a numbered heading, and its text, up to the next
heading, holds a phrase that defines the step (the heading "Versioning and
negotiation" for step 2, which Section 13, the conformance table, does not
hold). Each section number in the paragraph, written after "Section",
"Sections", "§" or "§§" or listed after such a number with or without its own
marker ("Sections 6.8 and 6.9", "Section 6.8 and 6.9"), is where
check_section_citations.py reads a number: in a citation next to the broker
profile's name and, in a list after "Section" or "§", with its own marker. So
that check reads every one; a number two of its citations read is counted once,
a number named at two places is counted at each, and a number of a citation of
another document is not read for the broker profile.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_section_citations  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "orders-db-exchange.md"
PROFILE = ROOT / "AAP-BROKER-PROFILE.md"

FLOW_HEADING = "## 3. Resolution flow (Section 6 of the broker profile)"
STEP = re.compile(r"│\s*(\d+)\.\s")

# A phrase that names a step the v1 reference does not perform, and the notes
# the step containing it carries.
UNPERFORMED = {
    "negotiate AAP version": ("Level 2", "v1:"),
    "rotating delegated key": ("v1:",),
    "signed audit": ("v1:",),
}

# Each step the paragraph after the flow cites, and the phrases of the text of
# the broker profile section that defines it.
DEFINED_BY = {
    2: ("Versioning and negotiation",),
    4: ("IdP signing key", "rotates"),
    7: ("signed audit log",),
}
STATUS_PARAGRAPH = "A `v1:` note marks"
# 'in the form step 7 uses ("v1: audit record written, not signed")': the step
# whose note the paragraph quotes as the form of a `v1:` note, and the note.
NOTE_FORM = re.compile(r'in the form step (\d+) uses \("(v1: [^"]+)"\)')
REFERENCE_NOTE = "**Reference spelling.**"
# The note under the policy sample on the predicates of the canonical federation
# clause of broker profile Section 7.1 that the sample leaves out.
LEVEL_1_NOTE = "**Level 1 binding.**"
# A predicate of the `match` clause of a policy binding: "    oasbLevel: ...".
MATCH_ENTRY = re.compile(r"    (?P<name>[A-Za-z]+): \S")
# The sentence of broker profile Section 7.1 that names what a broker evaluates
# at every conformance level: "`trustClass`, `oasbLevel`, `mode`, `scope` and
# `ttl` are evaluated at every conformance level".
EVERY_LEVEL = re.compile(
    r"((?:`\w+`(?:, |,? and ))*`\w+`) are evaluated at every conformance level"
)
# The policy sample with the `match` predicates it carried when it printed the
# canonical federation clause of broker profile Section 7.1, comments left out.
FEDERATION_SAMPLE = """\
- grant: grant://orders-db
  match:
    issuerChainIncludes: { partnersSet: trusted-partners }
    oasbLevel: ">=L2"
    trustClass: acme.com/orders:read
    jurisdiction: { in: [us, eu] }
  resolve:
    mode: exchange
"""
# The match predicates the reference policy loader loads without evaluating,
# read from `src/broker/grant-policy.ts` at commit 660af0d, the commit the
# reference spelling note cites. Broker profile Section 7.1 requires a broker
# that does not evaluate a predicate to refuse at load a clause carrying it, so
# the note names each of them and says what the reference does.
UNEVALUATED_PREDICATES = ("issuerChainIncludes", "jurisdiction")
# "(step 4) is described in broker profile Section 11": a step and the first
# broker profile section named after it, before the next step.
STEP_SECTION = re.compile(
    r"\(step (\d+)\)(?:(?!\(step ).)*?\b[Bb]roker profile Section (\d+(?:\.\d+)*)"
)
# A section number written after "Section", "Sections", "§" or "§§", the markers
# check_section_citations.py reads ("§99" is a section number too), and each
# later number of its list, with or without its own marker ("Sections 6.8 and
# 6.9", "§7, §11", "Section 6.8 and 6.9"). After "Section" or "§" that check reads
# a later number only when it has its own marker, so the 6.9 of "broker profile
# Section 6.8 and 6.9" is written and not read.
SECTION_NUMBERS = re.compile(
    rf"{check_section_citations.MARKER}\s*(?P<list>{check_section_citations.NUM}"
    rf"(?:{check_section_citations.SEPARATOR}(?:{check_section_citations.MARKER}\s*)?"
    rf"{check_section_citations.NUM})*)"
)


def flow_steps():
    """Return the resolution flow's steps as {number: text}, continuation lines joined."""
    lines = EXAMPLE.read_text(encoding="utf-8").splitlines()
    start = lines.index(FLOW_HEADING)
    fence = next(i for i in range(start, len(lines)) if lines[i].startswith("```"))
    end = next(i for i in range(fence + 1, len(lines)) if lines[i].startswith("```"))
    steps, current = {}, None
    for line in lines[fence + 1:end]:
        match = STEP.search(line)
        if match:
            current = int(match.group(1))
            steps[current] = line[match.end():]
        elif current is not None and line.lstrip().startswith("│"):
            steps[current] += " " + line.lstrip()[1:].strip()
        else:
            current = None
    return steps


def implementation_status_note():
    text = PROFILE.read_text(encoding="utf-8")
    section = text[text.index("## 14. Reference Implementation"):]
    section = section[:section.index("\n## 15.")]
    note = section[section.index("**Implementation status.**"):]
    return " ".join(note[:note.index("\n\n")].split())


def example_paragraph(opening):
    """The paragraph of the example that starts with `opening`, line breaks read as spaces."""
    text = EXAMPLE.read_text(encoding="utf-8")
    start = text.index(opening)
    return " ".join(text[start:text.index("\n\n", start)].split())


def status_paragraph():
    """The paragraph after the flow that cites the sections, line breaks read as spaces."""
    return example_paragraph(STATUS_PARAGRAPH)


def reference_spelling_note():
    """The note under the policy sample on the reference spelling, line breaks read as spaces."""
    return example_paragraph(REFERENCE_NOTE)


def level_1_note():
    """The note under the policy sample on the predicates it leaves to Section 7.1."""
    return example_paragraph(LEVEL_1_NOTE)


def policy_sample(document=EXAMPLE):
    """The lines of the one fenced yaml block of `document`: the example's policy sample,
    or the canonical federation clause of Section 7.1 when `document` is the broker profile."""
    text = document.read_text(encoding="utf-8")
    blocks = re.findall(r"^```yaml\n(.*?)^```$", text, flags=re.M | re.S)
    if len(blocks) != 1:
        raise AssertionError(f"{document.name}: {len(blocks)} fenced yaml blocks, want 1")
    return blocks[0].splitlines()


def match_predicates(lines):
    """The names of the predicates of the `match` clause of a policy binding, in order."""
    start = lines.index("  match:")
    names = []
    for line in lines[start + 1:]:
        if not line.startswith("    "):
            break
        entry = MATCH_ENTRY.match(line)
        if entry is None:
            raise AssertionError(f"not a predicate of a match clause: {line!r}")
        names.append(entry["name"])
    if not names:
        raise AssertionError("the match clause has no predicates")
    return names


def evaluated_at_every_level():
    """The names broker profile Section 7.1 has a broker evaluate at every conformance level."""
    found = EVERY_LEVEL.findall(profile_section("7.1") or "")
    if len(found) != 1:
        raise AssertionError(
            f"broker profile Section 7.1: {len(found)} sentences name what a broker evaluates"
            " at every conformance level, want 1"
        )
    return re.findall(r"`(\w+)`", found[0])


def not_evaluated_at_every_level(predicates):
    """The predicates that broker profile Section 7.1 does not name among those a broker
    evaluates at every conformance level, in order."""
    every_level = evaluated_at_every_level()
    return [name for name in predicates if name not in every_level]


def profile_section(number):
    """The heading and text of broker profile Section `number` up to the next heading, or None."""
    lines = PROFILE.read_text(encoding="utf-8").splitlines()
    heading = re.compile(rf"#+ {re.escape(number)}\.? ")
    start = next((i for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    return " ".join(" ".join(lines[start:end]).split())


def written_sections(paragraph):
    """(offset, number) for every section number written in `paragraph`, named or not."""
    return sorted(
        (match.start("list") + number.start(), number.group())
        for match in SECTION_NUMBERS.finditer(paragraph)
        for number in check_section_citations.NUMBER.finditer(match.group("list"))
    )


def read_sections(paragraph):
    """(offset, number) for each broker profile section number check_section_citations.py
    reads in `paragraph`, once where two of its citations read the same number."""
    return sorted({
        (offset, number)
        for cite in check_section_citations.citations(EXAMPLE.name, paragraph)
        if cite.doc.text == PROFILE.name
        for offset, number in zip(cite.offsets, cite.numbers, strict=True)
    })


def written_section_numbers(paragraph):
    """Every section number written in `paragraph`, named or not."""
    return sorted(number for _, number in written_sections(paragraph))


def read_section_numbers(paragraph):
    """The broker profile section numbers check_section_citations.py reads in `paragraph`."""
    return sorted(number for _, number in read_sections(paragraph))


class WorkedExampleStatusTest(unittest.TestCase):
    def test_flow_has_seven_numbered_steps(self):
        self.assertEqual(sorted(flow_steps()), list(range(1, 8)))

    def test_each_unperformed_step_carries_its_note(self):
        steps = flow_steps()
        for phrase, notes in UNPERFORMED.items():
            holding = [n for n, text in steps.items() if phrase in text]
            with self.subTest(phrase=phrase):
                self.assertEqual(len(holding), 1, f"{phrase!r} is in steps {holding}")
                for note in notes:
                    self.assertIn(note, steps[holding[0]])

    def test_implementation_status_names_the_audit_signature(self):
        note = implementation_status_note()
        self.assertIn("Outside that list are:", note)
        self.assertRegex(note, r"signature on audit records of Section 6\.7")

    def test_the_form_of_a_note_is_a_note_a_step_carries(self):
        # The paragraph after the flow names the form of a `v1:` note by quoting
        # one; the step it names carries that note.
        form = NOTE_FORM.search(status_paragraph())
        self.assertIsNotNone(form, "the paragraph quotes no note of a step as the form")
        self.assertIn(form.group(2), flow_steps()[int(form.group(1))])

    def test_the_policy_sample_carries_no_v1_note(self):
        # A `v1:` note marks a step of the flow. What the reference does with the
        # predicates of the policy sample is said in the reference spelling note.
        for line in policy_sample():
            with self.subTest(line=line.strip()):
                self.assertNotIn("v1:", line)

    def test_the_reference_spelling_note_names_each_unevaluated_predicate(self):
        note = reference_spelling_note()
        for predicate in UNEVALUATED_PREDICATES:
            with self.subTest(predicate=predicate):
                self.assertIn(f"`{predicate}`", note)
        self.assertIn("does not evaluate them to refuse at load", note)
        self.assertIn("broker profile §7.1", note)

    def test_the_policy_sample_matches_only_on_what_every_level_evaluates(self):
        # The flow grants the sample at step 3, and the v1 reference targets
        # Level 1. Under broker profile Section 7.1 a broker that does not
        # evaluate a predicate refuses at load a clause carrying it, so the
        # sample matches only on what Section 7.1 has a broker evaluate at
        # every conformance level.
        self.assertIn("evaluate policy", flow_steps()[3])
        self.assertEqual(not_evaluated_at_every_level(match_predicates(policy_sample())), [])

    def test_a_federation_predicate_in_the_policy_sample_is_detected(self):
        self.assertEqual(
            not_evaluated_at_every_level(match_predicates(FEDERATION_SAMPLE.splitlines())),
            ["issuerChainIncludes", "jurisdiction"],
        )

    def test_the_note_names_each_predicate_the_sample_leaves_to_section_7_1(self):
        # The canonical federation clause of Section 7.1 grants the same resource
        # with predicates the sample leaves out; the note under the sample names
        # each, cites the refusal at load of Section 7.1 and the missing ATX claim
        # of Section 9, and names the step at which a broker denies.
        sample = match_predicates(policy_sample())
        left = [name for name in match_predicates(policy_sample(PROFILE)) if name not in sample]
        self.assertTrue(left, "the policy sample carries each predicate of the Section 7.1 clause")
        note = level_1_note()
        for name in left:
            with self.subTest(predicate=name):
                self.assertIn(f"`{name}`", note)
        for phrase in ("broker profile §7.1", "broker profile §9", "at load", "at step 3"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, note)

    def test_each_unperformed_step_cites_the_section_that_defines_it(self):
        cited = {int(step): number for step, number in STEP_SECTION.findall(status_paragraph())}
        for step, phrases in DEFINED_BY.items():
            with self.subTest(step=step):
                self.assertIn(step, cited, f"no broker profile section is cited for step {step}")
                section = profile_section(cited[step])
                self.assertIsNotNone(section, f"the broker profile has no Section {cited[step]}")
                for phrase in phrases:
                    self.assertTrue(
                        phrase in section,
                        f"Section {cited[step]} does not hold {phrase!r}, which defines step {step}",
                    )

    def test_the_citation_check_reads_each_section_number_of_the_paragraph(self):
        paragraph = status_paragraph()
        self.assertEqual(read_sections(paragraph), written_sections(paragraph))

    def test_a_section_number_written_with_the_section_sign_is_counted(self):
        # "§99" without the broker profile's name is not read by the citation
        # check, so the comparison above must see it and fail.
        paragraph = status_paragraph()
        self.assertIn("targets Level 1.", paragraph)
        for sign in ("§99", "§ 99", "§§99"):
            with self.subTest(sign=sign):
                unnamed = paragraph.replace("targets Level 1.", f"targets Level 1 ({sign}).")
                self.assertIn("99", written_section_numbers(unnamed))
                self.assertNotIn("99", read_section_numbers(unnamed))
                self.assertNotEqual(read_sections(unnamed), written_sections(unnamed))

    def test_each_number_of_a_section_list_is_counted(self):
        # A named list is read in full, so the comparison passes on it; an
        # unnamed number after it is not read, so the comparison must fail.
        for listed in ("Sections 6.8 and 6.9", "§§6.8 and 6.9", "§§ 6.8, 6.9"):
            with self.subTest(listed=listed):
                named = f"The flow follows broker profile {listed}."
                self.assertEqual(written_section_numbers(named), ["6.8", "6.9"])
                self.assertEqual(read_sections(named), written_sections(named))
                hidden = f"{named} Step 4 is Section 6.9."
                self.assertEqual(written_section_numbers(hidden), ["6.8", "6.9", "6.9"])
                self.assertNotEqual(read_sections(hidden), written_sections(hidden))

    def test_a_bare_number_listed_after_a_singular_marker_is_counted(self):
        # After "Section" or "§" the citation check reads a later number only
        # when it has its own marker, so the bare 6.9 is written and not read.
        for listed in ("Section 6.8 and 6.9", "§6.8, 6.9", "§ 6.8-6.9"):
            with self.subTest(listed=listed):
                named = f"The flow follows broker profile {listed}."
                self.assertEqual(written_section_numbers(named), ["6.8", "6.9"])
                self.assertEqual(read_section_numbers(named), ["6.8"])
                self.assertNotEqual(read_sections(named), written_sections(named))
        for listed in ("Section 6.8 and Section 6.9", "§6.8, §6.9", "§ 6.8-§6.9"):
            with self.subTest(listed=listed):
                named = f"The flow follows broker profile {listed}."
                self.assertEqual(read_section_numbers(named), ["6.8", "6.9"])
                self.assertEqual(read_sections(named), written_sections(named))

    def test_a_number_two_citations_read_is_counted_once(self):
        # Naming the broker profile before and after its numbers makes two
        # citations of them; the numbers are read once, so unnamed copies of
        # them later in the paragraph are not hidden.
        for cited, unnamed in (
            ("Sections 6.8 and 6.9", "Step 4 is Section 6.8 and step 5 is Section 6.9."),
            ("Section 6.8", "Step 4 is Section 6.8."),
        ):
            with self.subTest(cited=cited):
                named = f"The broker profile {cited} of the broker profile applies."
                self.assertEqual(len(check_section_citations.citations(EXAMPLE.name, named)), 2)
                self.assertEqual(read_sections(named), written_sections(named))
                hidden = f"{named} {unnamed}"
                self.assertNotEqual(read_sections(hidden), written_sections(hidden))

    def test_a_number_named_at_two_places_is_counted_at_each(self):
        # Two citations that read the same number at two places count it at
        # each place, so the comparison passes.
        named = ("Step 4 follows broker profile Section 6.8, and step 5 also follows "
                 "broker profile Section 6.8.")
        self.assertEqual(written_section_numbers(named), ["6.8", "6.8"])
        self.assertEqual(read_section_numbers(named), ["6.8", "6.8"])
        self.assertEqual(read_sections(named), written_sections(named))

    def test_a_number_cited_for_another_document_is_counted(self):
        # The citation check reads these numbers for AAP-SPEC or AIP, not for
        # the broker profile, so the comparison must see them and fail.
        paragraph = status_paragraph()
        self.assertIn("targets Level 1.", paragraph)
        for cited, number in (("AAP-SPEC §4.4", "4.4"), ("AIP Section 4.1", "4.1")):
            with self.subTest(cited=cited):
                other = paragraph.replace("targets Level 1.", f"targets Level 1 ({cited}).")
                self.assertIn(number, written_section_numbers(other))
                self.assertNotIn(number, read_section_numbers(other))
                self.assertNotEqual(read_sections(other), written_sections(other))

    def test_a_citation_without_offsets_is_an_error(self):
        # A citation that does not record where its numbers start cannot be
        # compared by position, so reading it raises instead of dropping them.
        cite = check_section_citations.Citation(
            EXAMPLE.name, 1, check_section_citations.BY_NAME["broker profile"], ("6.8",),
            False, "broker profile Section 6.8",
        )
        with mock.patch.object(check_section_citations, "citations", return_value=[cite]), \
                self.assertRaises(ValueError):
            read_sections("broker profile Section 6.8")

    def test_numbers_the_citation_check_reads_in_other_forms_are_counted(self):
        # No space after the marker, a marker joined to the word before it, and
        # a letter suffix, which the citation check reads as part of the number.
        for written, number in (("x Section8", "8"), ("appliesSections 77", "77"),
                                ("x Section 6.8a", "6.8a")):
            with self.subTest(written=written):
                self.assertEqual(written_section_numbers(written), [number])

    def test_a_section_number_written_after_the_word_section_is_counted(self):
        # "Sections 99" without the broker profile's name is not read by the
        # citation check either; the paragraph itself writes only "Section N".
        paragraph = status_paragraph()
        self.assertIn("targets Level 1.", paragraph)
        for word in ("Section 99", "Sections 99"):
            with self.subTest(word=word):
                unnamed = paragraph.replace("targets Level 1.", f"targets Level 1 ({word}).")
                self.assertIn("99", written_section_numbers(unnamed))
                self.assertNotIn("99", read_section_numbers(unnamed))
                self.assertNotEqual(read_sections(unnamed), written_sections(unnamed))


if __name__ == "__main__":
    unittest.main()
