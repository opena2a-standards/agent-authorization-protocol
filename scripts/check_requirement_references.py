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
numbers in the label of each list entry, the text before the first comma that is
not inside a list of RFC numbers ("[RFC 2119] / [RFC 8174], ...",
"**RFC 6749 / RFC 6750**, ..." or "RFCs 6749, 6750 and 7009, ..."), and fails on
an RFC that only the Informative list carries and that a sentence outside the
References section cites next to a requirement keyword. A citation is "RFC" or
"RFCs" and a number, with each further number joined to it by a comma, a slash,
"and" or "or" ("RFC 6749 and 6750"). A reference not named by RFC number is not
checked.

Prose is what is left of a document without its code and comments. A fenced code
block is not read; its fence closes only on a fence of the same character and at
least the same length, as in CommonMark, so a longer fence can hold a shorter one.
An indented code block is not read: a line indented four or more spaces past the
margin, or past the text of the list item that holds it, where it does not
continue a paragraph. An HTML comment and a code span are not read. A unit of
prose ends at a blank line and at a thematic break or setext underline; a heading
is a unit by itself, and a list item and a table row each begin one. Inside a
unit a sentence ends at a full stop, question mark or exclamation mark followed
by a space and a capital letter (after any opening quote, bracket or emphasis);
the full stop of "e.g.", "i.e.", "cf.", "vs." or "viz." does not end a sentence.

An RFC named only for contrast is not a dependency of the requirement. A
citation passes inside a phrase that begins with "unlike", "in contrast to", "in
contrast with", "as opposed to", "rather than" or "instead of" and ends at the
next comma, semicolon, colon or requirement keyword, or at the parenthesis that
closes around it: "Unlike an RFC 6750 bearer token, a CGT MUST be bound to a
key." A phrase followed by a relative clause is not read as a contrast, since
that clause can state a requirement on what the phrase names ("unlike RFC 7009
revocation, which a broker MUST support").

Exit code 0 = every document passes. A document that is not valid UTF-8 fails
with a line naming the first byte that does not decode. Also run by
validate_examples.py so the check runs in CI.
"""

import bisect
import re
import sys

import check_naming
import check_raw_html

ROOT = check_naming.ROOT

REFERENCES_HEADING = re.compile(r"(#{1,6})\s+(?:\d+\.\s+)?References\s*$")
HEADING = re.compile(r"(#{1,6})\s")
CLASS_HEADING = re.compile(r"#{1,6}\s+(Normative|Informative)\b")
ENTRY = re.compile(r"\s*[-*+]\s+(.*)")
# A list item: its marker and the spaces before its text.
LIST_ITEM = re.compile(r"\s*([-*+]|\d{1,9}[.)])(\s+)")
# An HTML comment that begins a line: an HTML block, which runs to the line that
# holds "-->" whatever lies between, a blank line or a fence included.
COMMENT_START = re.compile(r"\s*<!--")
# An HTML comment or a code span inside a paragraph: neither crosses a blank line.
# The code span is the one check_raw_html.CODE_SPAN reads.
INLINE = re.compile(
    r"<!--(?:[^\n]|\n(?![ \t]*\n))*?-->"
    r"|(?<![`\\])(?P<ticks>`+)(?!`)(?:[^\n]|\n(?![ \t]*\n))+?(?<!`)(?P=ticks)(?!`)"
)
# A thematic break, or the underline of a setext heading.
RULE = re.compile(r"=+|-+|(?:[-*_]\s*){3,}")
# An ATX heading, which is a unit of prose by itself.
UNIT_HEADING = re.compile(r"\s*#{1,6}\s")
# A line that starts a new unit of prose: a list item or a table row.
UNIT_START = re.compile(r"\s*(?:[-*+]\s|\d+[.)]\s|\|)")
# A citation: "RFC" or "RFCs" and a number, then each number joined to it by a comma,
# a slash, "and" or "or".
RFC = re.compile(
    r"\bRFCs?\s*\d{3,5}\b"
    r"(?:(?:\s*,\s*(?:(?:and|or)\s+)?|\s*/\s*|\s+(?:and|or)\s+)\d{3,5}\b)*"
)
NUMBER = re.compile(r"\d+")
KEYWORD = re.compile(
    r"\b(?:MUST NOT|SHALL NOT|SHOULD NOT|NOT RECOMMENDED|MUST|REQUIRED|SHALL|SHOULD|"
    r"RECOMMENDED|MAY|OPTIONAL)\b"
)
# Abbreviations whose full stop does not end a sentence.
ABBREVIATIONS = ("e.g", "i.e", "cf", "vs", "viz")
# The end of a sentence: ".", "?" or "!" that is not the full stop of an abbreviation,
# any closing quote, bracket or emphasis, then whitespace before a capital letter
# (after any opening quote, bracket or emphasis).
SENTENCE_END = re.compile(
    "".join(rf"(?<!\b(?i:{re.escape(word)}))" for word in ABBREVIATIONS)
    + r"[.!?][\"')\]*_`]*\s+(?=[\"(\[*_`]*[A-Z])"
)
# The words that begin a contrast, and the accepted wording a failure line names.
CONTRAST = re.compile(
    r"\b(?:unlike|in\s+contrast\s+(?:to|with)|as\s+opposed\s+to|rather\s+than|instead\s+of)\b",
    re.IGNORECASE,
)
CONTRAST_WORDS = '"unlike", "in contrast to", "as opposed to", "rather than" or "instead of"'
# A relative clause after a contrast can state a requirement on what the contrast names.
RELATIVE = re.compile(r"[,;:]?\s*(?:which|that|who|whom|whose|where)\b", re.IGNORECASE)

FIX = (
    "list it as a normative reference, or state the sentence without the requirement keyword "
    f"(an RFC named only for contrast passes after {CONTRAST_WORDS})"
)


def blocks(lines: list[str]) -> list[str]:
    """Return lines with each line that is not prose emptied: a line of a fenced or an
    indented code block, and a line of an HTML comment that begins a line. On the line
    that closes such a comment the text up to the "-->" is blanked out."""
    read = []
    fence = None  # the fence that opened the fenced code block being read
    comment = False  # inside an HTML comment that began a line
    paragraph = False  # the line before is paragraph text, which an indented line continues
    # The column where the text of each list item begins, innermost last. An item is
    # dropped at the first line after a blank line that is indented less than its text.
    offsets: list[int] = []
    for line in lines:
        if fence is not None:
            if check_naming.closes(line, fence):
                fence = None
            read.append("")
            continue
        if comment:
            end = line.find("-->")
            comment = end < 0
            read.append("" if comment else " " * (end + 3) + line[end + 3:])
            continue
        fence = check_naming.opening_fence(line)
        if fence is not None or not line.strip():
            paragraph = False
            read.append("")
            continue
        expanded = line.expandtabs(4)
        indent = len(expanded) - len(expanded.lstrip())
        if not paragraph:
            while offsets and indent < offsets[-1]:
                offsets.pop()
            if indent >= (offsets[-1] if offsets else 0) + 4:
                read.append("")
                continue
        start = COMMENT_START.match(line)
        if start and "-->" not in line[start.end():]:
            comment, paragraph = True, False
            read.append("")
            continue
        item = LIST_ITEM.match(expanded)
        if item:
            # More than four spaces after the marker begin an indented code block
            # inside the item, whose text then begins one space after the marker.
            spaces = len(item.group(2))
            offsets.append(indent + len(item.group(1)) + (spaces if spaces <= 4 else 1))
        paragraph = UNIT_HEADING.match(line) is None
        read.append(line)
    return read


def label_numbers(entry: str) -> list[str]:
    """Return the RFC numbers in the label of a reference entry: the text before the
    first comma that is not inside a list of RFC numbers."""
    numbers: list[str] = []
    end = 0
    for match in RFC.finditer(entry):
        if "," in entry[end:match.start()]:
            break
        numbers += NUMBER.findall(match.group(0))
        end = match.end()
    return numbers


def references(block: list[str]) -> tuple[set[str], set[str], set[int]]:
    """Return the normative RFCs, the informative RFCs and the line indexes of the
    References sections of a document, given its lines as blocks() returns them."""
    normative: set[str] = set()
    informative: set[str] = set()
    section: set[int] = set()
    level = 0
    kind = None
    for index, line in enumerate(block):
        heading = HEADING.match(line)
        if heading and level and len(heading.group(1)) <= level:
            level, kind = 0, None
        start = REFERENCES_HEADING.match(line)
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
            (normative if kind == "Normative" else informative).update(
                label_numbers(entry.group(1)))
    return normative, informative, section


def units(block: list[str], skip: set[int]) -> list[list[int]]:
    """Return the units of prose as lists of line indexes: lines between blank lines,
    thematic breaks and setext underlines, split before a list item or a table row,
    with each heading a unit by itself, outside the lines in skip."""
    found: list[list[int]] = []
    current: list[int] = []
    for index, line in enumerate(block):
        text = line.strip()
        blank = index in skip or not text or RULE.fullmatch(text) is not None
        heading = not blank and UNIT_HEADING.match(line) is not None
        if blank or heading or UNIT_START.match(line):
            if current:
                found.append(current)
            current = []
        if heading:
            found.append([index])
        elif not blank:
            current.append(index)
    if current:
        found.append(current)
    return found


def sentences(text: str, read: str) -> list[tuple[int, int]]:
    """Return the start and end offsets of the sentences of a unit of prose. read is
    text with its comments and code spans blanked out: a full stop inside one does
    not end a sentence."""
    spans = []
    start = 0
    for match in SENTENCE_END.finditer(text):
        if read[match.start()] != text[match.start()]:
            continue
        spans.append((start, match.end()))
        start = match.end()
    spans.append((start, len(text)))
    return spans


def cited(text: str) -> list[tuple[int, str]]:
    """Return the offset and the number of each RFC cited in text, with each number of
    a list ("RFCs 6749 and 6750") as a citation of its own."""
    return [
        (number.start(), number.group(0))
        for match in RFC.finditer(text)
        for number in NUMBER.finditer(text, match.start(), match.end())
    ]


def contrasts(sentence: str) -> list[tuple[int, int]]:
    """Return the start and end offsets of the phrases of a sentence that state a
    contrast: from a word of CONTRAST to the next comma, semicolon or colon outside
    parentheses, the parenthesis that closes around the phrase, or a requirement
    keyword. A phrase that a relative clause follows is left out."""
    spans = []
    for match in CONTRAST.finditer(sentence):
        end = match.end()
        depth = 0
        while end < len(sentence):
            char = sentence[end]
            if char == ")" and not depth:
                break
            if (char in ",;:" and not depth) or KEYWORD.match(sentence, end):
                break
            depth += (char == "(") - (char == ")")
            end += 1
        if not RELATIVE.match(sentence, end):
            spans.append((match.start(), end))
    return spans


def findings(text: str) -> list[str]:
    """Return one reason per citation of an informative-only RFC in a sentence with a
    requirement keyword, in document order."""
    block = blocks(text.split("\n"))
    normative, informative, section = references(block)
    only_informative = informative - normative
    if not only_informative:
        return []
    read = INLINE.sub(check_raw_html.blank, "\n".join(block)).split("\n")
    found = []
    for unit in units(block, section):
        body = "\n".join(block[index] for index in unit)
        prose = "\n".join(read[index] for index in unit)
        line_starts = [0, *(match.end() for match in re.finditer("\n", body))]
        for start, end in sentences(body, prose):
            sentence = prose[start:end]
            keywords = list(dict.fromkeys(KEYWORD.findall(sentence)))
            if not keywords:
                continue
            contrast = contrasts(sentence)
            for offset, number in cited(sentence):
                if number not in only_informative:
                    continue
                if any(first <= offset < last for first, last in contrast):
                    continue
                lineno = unit[bisect.bisect_right(line_starts, start + offset) - 1] + 1
                found.append(
                    f"line {lineno}: RFC {number} is listed only as an informative reference "
                    f"and is cited in a sentence with {', '.join(keywords)}"
                )
    return found


def documents(root=ROOT) -> list[str]:
    """Return the Markdown documents with a classed References section, as sorted paths
    relative to root. A byte that is not valid UTF-8 is replaced, so a document that
    holds one is listed and check() reports it."""
    names = []
    for name in check_naming.documents(root):
        if not name.endswith(".md"):
            continue
        text = (root / name).read_text(encoding="utf-8", errors="replace")
        normative, informative, _ = references(blocks(text.split("\n")))
        if normative or informative:
            names.append(name)
    return names


def check(root=ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    for name in documents(root):
        text, error = check_naming.read_text(root / name)
        if error:
            print(f"FAIL  {name}: {error}")
            failures += 1
            continue
        reasons = findings(text)
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
