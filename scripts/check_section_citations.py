#!/usr/bin/env python3
"""Check that the section numbers cited next to a family document's name resolve.

A citation such as "broker profile §8.1", "AIP Section 4.1" or "Section 4.4.1 of
AAP-SPEC" sends the reader to a numbered section of an OpenA2A document. The check
reads a citation in which a name in NAMES below sits next to a section number, with
the numbers listed directly after that number ("§7, §11", "Sections 6.8, 6.9 and
7.3"). These forms are not read:

- a number further along the sentence, such as §6.8 in "the broker profile (§6,
  step 3, and §6.8)" or §4–§6 in "AAP-SPEC §9 and the claim-semantics rules of
  §4–§6";
- a number listed without its own marker after "Section" or "§": "AIP §4.1, 4.2"
  reads 4.1 only;
- a number in parentheses after the bare name AIP, ATP or ATX, which also names a
  protocol or a credential: nothing is read in "AIP (Section 4.1)";
- a name that NAMES does not list, such as the ATX text written `core.md` rather
  than atx-spec/core.md;
- a number after a link whose target is longer than 256 characters, as in
  "[AIP-SPEC.md](target) §7.2".

In the specification and the broker profile a number in one of these forms is not
checked; in any other Markdown document it fails (rule 6).

The citations checked are those in the Markdown documents of this repository and in
the newest Internet-Draft render (draft-fane-opena2a-aap-NN.xml), except the render's
citations of AAP-SPEC, the specification it renders. CHANGELOG.md, the dated notes in
decisions/ and the earlier renders cite the numbering of the version they describe and
are not checked.

1. A cited document of this repository (the specification, AAP-SPEC.md, and the
   broker profile, AAP-BROKER-PROFILE.md) has a numbered heading with each cited
   number.
2. The text whose numbering is meant is named. A family document can have more than
   one numbered text: the AIP Markdown and its Internet-Draft number their sections
   differently, as AAP-SPEC.md and its render do. So where the citing document's
   References section lists the cited document, that entry names its text file
   (AIP-SPEC.md, ATP-SPEC.md, atx-spec/core.md, did-method-opena2a.md,
   AAP-BROKER-PROFILE.md). A document outside this repository, whose headings this
   check cannot read, is named by its text file in the citation (file name or stem,
   "AIP-SPEC §7.2", "did-method-opena2a Sections 3.1 and 3.1.1") or in that entry.
3. A citation names its document: "Section 6 of the spec" in a document other than
   the specification fails.
4. In the render, each document cited by number has a reference entry. The census
   line lists the printed address (the entry's target) of each, and whether the
   address or the entry's annotation names the text file: "address names",
   "annotation names" or "does not name".
5. The next render prints, for each document it cites by number, an address that
   names the text file, or names it in the entry's annotation. A render a released
   section of CHANGELOG.md records as submitted ("`draft-fane-opena2a-aap-02`
   (submitted 2026-10-02") cannot change, so there an address that does not name its
   text is reported, not failed; in any other render it fails.
6. In each Markdown document other than the specification and the broker profile, a
   section number names its document. The specification and the broker profile use
   the same numbers for different sections (Section 5 is the DA in AAP-SPEC and the
   CPI in the broker profile), so a bare number in another document does not say
   which of them it means. Each number written after "Section", "Sections", "§" or
   "§§", or listed after such a number with or without its own marker, is one the
   check reads in a citation above, or a section of an RFC or a FIPS standard ("RFC
   7519 §2", "[RFC 9421] Section 4", "FIPS 204 §5.3", "Section 4 of RFC 9449"); any
   other fails, including one that means a numbered heading of the citing document
   itself. "CPI modes (`Exchange`, §5)" fails and "CPI modes (`Exchange`, broker
   profile §5)" passes. A number in a citation of "the spec" is reported once, by
   rule 3.

Prints one census line. Exit code 0 = no failure. A document that is not valid UTF-8,
or a render that is not well-formed XML, fails with a line naming where it stops
reading. Also run by validate_examples.py so the check runs in CI.
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import check_naming
import check_references

ROOT = pathlib.Path(__file__).resolve().parent.parent

SPEC = "AAP-SPEC.md"
# Documents whose section numbers are those of the version they describe.
NOT_CHECKED = re.compile(r"CHANGELOG\.md|decisions/.*")


@dataclass(frozen=True)
class Document:
    name: str  # the name the census line uses
    text: str  # the text file whose numbering a citation means
    local: bool  # the text file is in this repository
    label: str  # the reference label (Markdown) and anchor (render)


DOCUMENTS = (
    Document("AAP-SPEC", "AAP-SPEC.md", True, "AAP-SPEC"),
    Document("broker profile", "AAP-BROKER-PROFILE.md", True, "AAP-BROKER-PROFILE"),
    Document("AIP", "AIP-SPEC.md", False, "AIP"),
    Document("ATP", "ATP-SPEC.md", False, "ATP"),
    Document("ATX", "atx-spec/core.md", False, "ATX"),
    Document("DID method", "did-method-opena2a.md", False, "DID-OPENA2A"),
)
BY_NAME = {doc.name: doc for doc in DOCUMENTS}
BY_LABEL = {check_references.key(doc.label): doc for doc in DOCUMENTS}
# The specification and the broker profile; rule 6 reads every other Markdown document.
NUMBERED = {doc.text for doc in DOCUMENTS if doc.local}

# (pattern, document, names its text file). A name that is only a document name may
# be followed by a parenthesized number, "the broker profile (§6, step 3)"; AIP, ATP
# and ATX also name a protocol or a credential, so "the agent's ATX (Section 6)" is
# not a citation of ATX.
NAMES = (
    (r"AAP-SPEC(?:\.md)?", "AAP-SPEC", True),
    (r"AAP-BROKER-PROFILE(?:\.md)?", "broker profile", True),
    (r"[Bb]roker[ -][Pp]rofile", "broker profile", False),
    (r"AIP-SPEC(?:\.md)?", "AIP", True),
    (r"ATP-SPEC(?:\.md)?", "ATP", True),
    (r"atx-spec/core\.md", "ATX", True),
    (r"did-method-opena2a(?:\.md)?", "DID method", True),
    (r"AIP", "AIP", False),
    (r"ATP", "ATP", False),
    (r"ATX", "ATX", False),
)
NAME = "(?P<name>" + "|".join(pattern for pattern, _, _ in NAMES) + ")"
NAME_START = r"(?<![\w/.-])"
NAME_END = r"(?![\w-])"

NUM = r"\d+[a-z]?(?:\.\d+[a-z]?)*"
SEPARATOR = r"\s*(?:,|/|-|–|\band\b|\bor\b|\bto\b)\s*"
MARKER = r"(?:Sections?|§§?)"
# After a plural marker a later number may stand alone ("Sections 6.8, 6.9 and 7.3");
# after a singular one it carries its own marker ("§7, §11", "§13-§14").
NUMBERS = (
    rf"(?:(?:Sections|§§)\s*(?P<plural>{NUM}(?:{SEPARATOR}(?:{MARKER}\s*)?{NUM})*)"
    rf"|(?:Section(?!s)|§(?!§))\s*(?P<single>{NUM}(?:{SEPARATOR}{MARKER}\s*{NUM})*))"
)
NUMBER = re.compile(NUM)

# "AIP Section 4.1", "broker profile §7, §11", "[`AAP-BROKER-PROFILE.md` §14](...)",
# "[`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md) §13-§14", "broker profile (§6".
# A link target is read up to 256 characters, so a run of "AIP](" without a closing
# parenthesis is not read to its end again from each name in it.
NAME_FIRST = re.compile(
    NAME_START + NAME + NAME_END
    + r"`?(?:\]\([^)\s]{0,256}\))?`?\*{0,2}(?:'s)?\s*(?P<paren>\(\s*)?" + NUMBERS
)
# "§6 of the broker profile", "Section 4.4.1 of AAP-SPEC".
NUMBER_FIRST = re.compile(
    NUMBERS + r"\s+of\s+(?:the\s+)?`?" + NAME_START + NAME + NAME_END
)
# "Section 6 of the spec": a citation that does not say which document.
UNNAMED = re.compile(NUMBERS + r"\s+of\s+the\s+spec(?:ification)?\b")
# The words after the numbers of such a citation, which rule 3 reports.
OF_THE_SPEC = re.compile(r"\s+of\s+the\s+spec(?:ification)?\b")

# A section number written after "Section", "Sections", "§" or "§§", with each later
# number of its list, with or without its own marker: "§5", "§3.2/§4.2", "§4–§6",
# "Sections 6.8, 6.9 and 7.3", and the "§4.1, 4.2" of "AIP §4.1, 4.2" (rule 6).
WRITTEN = re.compile(rf"{MARKER}\s*{NUM}(?:{SEPARATOR}(?:{MARKER}\s*)?{NUM})*")
# A section of an RFC or a FIPS standard, named before the number ("RFC 7519 §2",
# "[RFC 9421] Section 4", "RFC 7515, Section 7.2.1", "FIPS 204 §5.3") or after it
# ("Section 4 of RFC 9449").
STANDARD = r"\[?(?:RFC|FIPS)\s*\d+\]?"
STANDARD_BEFORE = re.compile(STANDARD + r",?\s*$")
STANDARD_AFTER = re.compile(r"\s+of\s+" + STANDARD)
# How many characters before a written number STANDARD_BEFORE reads.
STANDARD_WINDOW = 24

HEADING = re.compile(rf"#{{1,6}}\s+({NUM})\.?\s")
# A References entry: "- [AIP], ..." or "- **ATP**, ...".
ENTRY = re.compile(r"\s*[-*]\s+(?:\[([^\]]+)\]|\*\*([^*]+)\*\*)")
CONTINUATION = re.compile(r"\s+\S")


@dataclass(frozen=True)
class Citation:
    file: str
    line: int
    doc: Document
    numbers: tuple[str, ...]
    names_text: bool  # the citation itself names the text file
    quote: str
    offsets: tuple[int, ...] = ()  # where each of numbers starts in the text


def classify(name: str) -> tuple[Document, bool]:
    """Return the document a matched name means and whether it names its text file."""
    for pattern, doc_name, names_text in NAMES:
        if re.fullmatch(pattern, name):
            return BY_NAME[doc_name], names_text
    raise ValueError(name)


def citations(file: str, text: str) -> list[Citation]:
    """Return the citations in text in which a name in NAMES sits next to a section number.

    A citation holds that number and the numbers listed directly after it; the module
    docstring lists the forms that are not read.
    """
    flat = text.replace("\n", " ")
    found = {}
    for pattern in (NAME_FIRST, NUMBER_FIRST):
        for match in pattern.finditer(flat):
            doc, names_text = classify(match.group("name"))
            if pattern is NAME_FIRST and match.group("paren") and not (
                names_text or doc.name == "broker profile"
            ):
                continue
            group = "plural" if match.group("plural") else "single"
            numbers = match.group(group)
            found.setdefault(
                match.start(),
                Citation(
                    file,
                    text.count("\n", 0, match.start()) + 1,
                    doc,
                    tuple(NUMBER.findall(numbers)),
                    names_text,
                    " ".join(match.group(0).split()),
                    tuple(match.start(group) + n.start() for n in NUMBER.finditer(numbers)),
                ),
            )
    return [found[start] for start in sorted(found)]


def unnamed_citations(file: str, text: str) -> list[str]:
    """Return a failure line for each citation of "the spec" in text."""
    failures = []
    for match in UNNAMED.finditer(text.replace("\n", " ")):
        line = text.count("\n", 0, match.start()) + 1
        failures.append(
            f"{file}:{line}: \"{' '.join(match.group(0).split())}\" does not name its"
            f" document; write AAP-SPEC or the broker profile"
        )
    return failures


def unnamed_numbers(file: str, text: str, cites: list[Citation]) -> list[str]:
    """Return a failure line for each written list of section numbers that names no document.

    Rule 6, for a Markdown document other than the specification and the broker
    profile: a number passes when one of cites, the citations of text, reads it, or
    when it is a section of an RFC or a FIPS standard. A list in a citation of "the
    spec" is left to unnamed_citations(). A failing list ("§3.2/§4.2") gives one line,
    with each of its numbers that no citation reads.
    """
    flat = text.replace("\n", " ")
    read = {offset for cite in cites for offset in cite.offsets}
    failures = []
    for match in WRITTEN.finditer(flat):
        before = flat[max(0, match.start() - STANDARD_WINDOW):match.start()]
        if (
            STANDARD_BEFORE.search(before)
            or STANDARD_AFTER.match(flat, match.end())
            or OF_THE_SPEC.match(flat, match.end())
        ):
            continue
        numbers = [
            number.group(0)
            for number in NUMBER.finditer(match.group(0))
            if match.start() + number.start() not in read
        ]
        if numbers:
            line = text.count("\n", 0, match.start()) + 1
            failures.append(
                f"{file}:{line}: \"{' '.join(match.group(0).split())}\": no document is named"
                f" for {', '.join(numbers)}; write the document's name next to the number,"
                f" as in \"broker profile §5\" or \"AAP-SPEC §4.3\""
            )
    return failures


def section_numbers(text: str) -> set[str]:
    """Return the numbers of the numbered headings of a Markdown text, outside code fences."""
    numbers = set()
    fence = None
    for line in text.splitlines():
        if fence is not None:
            if check_naming.closes(line, fence):
                fence = None
            continue
        fence = check_naming.opening_fence(line)
        if fence is not None:
            continue
        heading = HEADING.match(line)
        if heading:
            numbers.add(heading.group(1))
    return numbers


def reference_entries(text: str) -> dict[str, str]:
    """Return {document name: entry text} for each family document the References section lists."""
    entries = {}
    in_section = False
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = check_references.REFERENCES_HEADING.fullmatch(line) is not None
            current = None
            continue
        if not in_section:
            continue
        entry = ENTRY.match(line)
        if entry:
            doc = BY_LABEL.get(check_references.key(entry.group(1) or entry.group(2)))
            current = doc.name if doc else None
            if current:
                entries[current] = line
            continue
        if current and CONTINUATION.match(line):
            entries[current] += " " + line.strip()
        else:
            current = None
    return entries


def render_references(tree: ET.Element) -> dict[str, tuple[str, str]]:
    """Return {anchor: (target, annotation)} for each reference of a parsed RFCXML v3 document."""
    references = {}
    for ref in tree.iter("reference"):
        annotation = ref.find("annotation")
        references[ref.get("anchor", "")] = (
            ref.get("target", ""),
            " ".join("".join(annotation.itertext()).split()) if annotation is not None else "",
        )
    return references


def unresolved(cites: list[Citation], headings: dict[str, set[str]]) -> list[str]:
    """Return a failure line for each cited number a local document does not have."""
    failures = []
    for cite in cites:
        if not cite.doc.local:
            continue
        missing = [n for n in cite.numbers if n not in headings[cite.doc.text]]
        if missing:
            failures.append(
                f"{cite.file}:{cite.line}: \"{cite.quote}\": {cite.doc.text} has no numbered"
                f" heading {', '.join(missing)}"
            )
    return failures


def unnamed_texts(cites: list[Citation], entries: dict[str, str]) -> list[str]:
    """Return a failure line for each citation that does not say which text it means."""
    failures = []
    reported = set()
    for cite in cites:
        entry = entries.get(cite.doc.name)
        if entry is not None:
            if cite.doc.text not in entry and cite.doc.name not in reported:
                reported.add(cite.doc.name)
                failures.append(
                    f"{cite.file}:{cite.line}: \"{cite.quote}\": the {cite.doc.label} entry of"
                    f" the References section does not name {cite.doc.text}"
                )
        elif not cite.doc.local and not cite.names_text:
            failures.append(
                f"{cite.file}:{cite.line}: \"{cite.quote}\": {cite.doc.name} is outside this"
                f" repository; name {cite.doc.text} in the citation or in a References entry"
            )
    return failures


def census(cites: list[Citation]) -> str:
    """Return "N (doc n, doc n)" for a list of citations."""
    counts = {}
    for cite in cites:
        counts[cite.doc.name] = counts.get(cite.doc.name, 0) + 1
    detail = ", ".join(f"{name} {n}" for name, n in sorted(counts.items(), key=lambda i: (-i[1], i[0])))
    return f"{len(cites)}" + (f" ({detail})" if detail else "")


def check(root: pathlib.Path = ROOT) -> int:
    """Print the failures and the census line; return the number of failures."""
    failures = []
    headings = {}
    for doc in DOCUMENTS:
        if doc.local:
            path = root / doc.text
            if not path.is_file():
                print(f"FAIL  section citations: {doc.text} not found")
                return 1
            text, error = check_naming.read_text(path)
            if error:
                print(f"FAIL  section citations: {doc.text}: {error}")
                return 1
            headings[doc.text] = section_numbers(text)

    parts = []
    for name in check_naming.documents(root):
        if not name.endswith(".md") or NOT_CHECKED.fullmatch(name):
            continue
        text, error = check_naming.read_text(root / name)
        if error:
            failures.append(f"{name}: {error}")
            continue
        cites = citations(name, text)
        failures += unresolved(cites, headings)
        failures += unnamed_texts(cites, reference_entries(text))
        if name != SPEC:
            failures += unnamed_citations(name, text)
        if name not in NUMBERED:
            failures += unnamed_numbers(name, text, cites)
        if cites:
            parts.append(f"{name} {census(cites)}")

    render_name = check_references.newest_render(root)
    addresses = []
    status = ""
    if render_name is None:
        failures.append("no draft-fane-opena2a-aap-NN.xml found")
    else:
        submitted = check_references.render_submitted(root, render_name)
        text, tree, error = check_references.read_render(root / render_name)
        if error:
            failures.append(f"{render_name}: {error}")
        else:
            references = render_references(tree)
            # The XML source, so a failure names the line of the source; the citations
            # are in element text, where a line break is a space.
            cites = [c for c in citations(render_name, text) if c.doc.name != "AAP-SPEC"]
            failures += unresolved(cites, headings)
            for doc in sorted({c.doc for c in cites}, key=lambda d: d.name):
                if doc.label not in references:
                    failures.append(
                        f"{render_name}: {doc.name} is cited by section number and has no reference entry"
                    )
                    continue
                target, annotation = references[doc.label]
                if doc.text in target:
                    named = f"address names {doc.text}"
                elif doc.text in annotation:
                    named = f"annotation names {doc.text}"
                else:
                    named = f"does not name {doc.text}"
                    if not submitted:
                        failures.append(
                            f"{render_name}: {doc.name} is cited by section number and its reference"
                            f" entry ({target or 'no target'}) does not name {doc.text}; the next render"
                            f" must print an address of {doc.text} or name it in the entry's annotation"
                        )
                addresses.append(f"{doc.name} {target or '(no target)'} ({named})")
            parts.append(f"{render_name} {census(cites)}")
        status = "; " + check_references.render_status(render_name, submitted)

    for failure in failures:
        print(f"FAIL  {failure}")
    print(
        f"{'FAIL' if failures else 'ok  '}  section citations of family documents:"
        f" {'; '.join(parts) or 'none'}; {len(failures)} failure(s);"
        f" printed address in {render_name or 'no render'}: {', '.join(addresses) or 'none'}"
        f"{status}"
    )
    return len(failures)


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
