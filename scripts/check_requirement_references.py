#!/usr/bin/env python3
"""Check that no requirement depends on an RFC listed only as an informative reference.

A reference that must be read to implement a requirement is a normative reference.
A sentence that carries a requirement keyword (MUST, MUST NOT, REQUIRED, SHALL,
SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY or OPTIONAL, in
capitals) and cites an RFC therefore needs that RFC among the normative references
of its document.

The check reads every Markdown document with a References section that sorts its
entries under Normative and Informative headings (check_naming.py lists the
documents, so a new document is covered without being listed). It takes the RFC
numbers in the label of each list entry, the text before the first comma
("[RFC 2119] / [RFC 8174], ..." or "**RFC 6749 / RFC 6750**, ..."), and fails on
an RFC that only the Informative list carries and that a sentence outside the
References section cites next to a requirement keyword. A sentence ends at a full
stop, question mark or exclamation mark followed by a space and a capital letter,
at a blank line, and before a heading, a list item or a table row; fenced code
blocks are not read. A reference not named by RFC number is not checked.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import bisect
import re
import sys

import check_naming

ROOT = check_naming.ROOT

REFERENCES_HEADING = re.compile(r"(#{1,6})\s+(?:\d+\.\s+)?References\s*$")
HEADING = re.compile(r"(#{1,6})\s")
CLASS_HEADING = re.compile(r"#{1,6}\s+(Normative|Informative)\b")
ENTRY = re.compile(r"\s*[-*+]\s+(.*)")
FENCE = re.compile(r"\s*(```|~~~)")
# A line that starts a new unit of prose: a heading, a list item or a table row.
UNIT_START = re.compile(r"\s*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|\|)")
RFC = re.compile(r"\bRFC\s?(\d{3,5})\b")
KEYWORD = re.compile(
    r"\b(?:MUST NOT|SHALL NOT|SHOULD NOT|NOT RECOMMENDED|MUST|REQUIRED|SHALL|SHOULD|"
    r"RECOMMENDED|MAY|OPTIONAL)\b"
)
# The end of a sentence: ".", "?" or "!", any closing quote, bracket or emphasis, then
# whitespace before a capital letter (after any opening quote, bracket or emphasis).
SENTENCE_END = re.compile(r"[.!?][\"')\]*_`]*\s+(?=[\"(\[*_`]*[A-Z])")

FIX = "list it as a normative reference, or state the sentence without the requirement keyword"


def references(lines: list[str]) -> tuple[set[str], set[str], set[int]]:
    """Return the normative RFCs, the informative RFCs and the line indexes of the
    References sections of a document."""
    normative: set[str] = set()
    informative: set[str] = set()
    section: set[int] = set()
    level = 0
    kind = None
    fenced = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
        heading = None if fenced else HEADING.match(line)
        if heading and level and len(heading.group(1)) <= level:
            level, kind = 0, None
        start = None if fenced else REFERENCES_HEADING.match(line)
        if start:
            level, kind = len(start.group(1)), None
        if not level:
            continue
        section.add(index)
        if heading:
            match = CLASS_HEADING.match(line)
            kind = match.group(1) if match else None
            continue
        entry = ENTRY.match(line)
        if kind and entry:
            label = entry.group(1).split(",", 1)[0]
            (normative if kind == "Normative" else informative).update(RFC.findall(label))
    return normative, informative, section


def units(lines: list[str], skip: set[int]) -> list[list[int]]:
    """Return the units of prose as lists of line indexes: lines between blank lines,
    split before a heading, a list item or a table row, outside fenced code blocks
    and the lines in skip."""
    found: list[list[int]] = []
    current: list[int] = []
    fenced = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
            blank = True
        else:
            blank = fenced or index in skip or not line.strip()
        if blank or UNIT_START.match(line):
            if current:
                found.append(current)
            current = []
        if not blank:
            current.append(index)
    if current:
        found.append(current)
    return found


def sentences(text: str) -> list[tuple[int, int]]:
    """Return the start and end offsets of the sentences of a unit of prose."""
    spans = []
    start = 0
    for match in SENTENCE_END.finditer(text):
        spans.append((start, match.end()))
        start = match.end()
    spans.append((start, len(text)))
    return spans


def findings(text: str) -> list[str]:
    """Return one reason per citation of an informative-only RFC in a sentence with a
    requirement keyword, in document order."""
    lines = text.split("\n")
    normative, informative, section = references(lines)
    only_informative = informative - normative
    if not only_informative:
        return []
    found = []
    for unit in units(lines, section):
        body = "\n".join(lines[index] for index in unit)
        line_starts = [0, *(match.end() for match in re.finditer("\n", body))]
        for start, end in sentences(body):
            sentence = body[start:end]
            keywords = list(dict.fromkeys(KEYWORD.findall(sentence)))
            if not keywords:
                continue
            for match in RFC.finditer(sentence):
                number = match.group(1)
                if number not in only_informative:
                    continue
                lineno = unit[bisect.bisect_right(line_starts, start + match.start()) - 1] + 1
                found.append(
                    f"line {lineno}: RFC {number} is listed only as an informative reference "
                    f"and is cited in a sentence with {', '.join(keywords)}"
                )
    return found


def documents(root=ROOT) -> list[str]:
    """Return the Markdown documents with a classed References section, as sorted paths
    relative to root."""
    names = []
    for name in check_naming.documents(root):
        if not name.endswith(".md"):
            continue
        normative, informative, _ = references(
            (root / name).read_text(encoding="utf-8").split("\n"))
        if normative or informative:
            names.append(name)
    return names


def check(root=ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    for name in documents(root):
        reasons = findings((root / name).read_text(encoding="utf-8"))
        for reason in reasons:
            print(f"FAIL  {name}: {reason}; {FIX}")
        if reasons:
            failures += 1
        else:
            print(f"ok    {name}: no requirement cites an informative-only RFC")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
