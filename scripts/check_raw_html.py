#!/usr/bin/env python3
"""Check that no Markdown document carries an HTML tag in its prose.

CommonMark and GitHub Markdown read an angle-bracket placeholder such as
<YYYY-MM-DD> or <name> as a raw HTML tag, and a rendered page does not show
it: "fails on as of <YYYY-MM-DD>" renders as "fails on as of ". The
repository's Markdown writes such a placeholder as a code span (`<name>`) or
with an escaped bracket (\\<name>), and carries no raw HTML other than HTML
comments.

The check fails on raw HTML other than a comment in the prose of a Markdown
document: an open or closing tag, a processing instruction (<?x?>), a
declaration (<!DOCTYPE html>) or a CDATA section (<![CDATA[x]]>), outside
fenced code blocks and code spans, not escaped, and not the destination of an
inline link ([text](<...>), also after spaces or a line break). Raw HTML
inside a paragraph crosses neither a blank line nor a line that begins a block
quote, as CommonMark ends the paragraph at both. The check takes a line to
begin a block quote where it begins with more block quote markers (>) than any
earlier line after the last blank line holds, and does not read the block
quote markers of any other line as text. An open or closing tag with a name in
BLOCK_NAMES, or an open tag with a name in RAW_NAMES (<div, </div, <p, <pre,
<table, ...), that begins a line, after indentation and any list or block
quote markers, fails even when a blank line splits it: CommonMark reads a line
that begins with such a tag as the start of an HTML block, which holds the
line as raw HTML. A processing instruction, a declaration or a CDATA section
that a blank line or a line that begins a block quote splits passes, even
where it begins a line and CommonMark reads it as an HTML block that continues
past that line. An HTML comment passes, and so does an autolink
(<https://...>), which renders as a link.

The documents are every Markdown file in the repository (check_naming.py
lists them), so a new document is covered without being listed.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import bisect
import re
import sys
from collections.abc import Callable

import check_naming

ROOT = check_naming.ROOT

# The markers that begin a line inside a list item or a block quote: a list
# marker after any indentation, and a block quote marker (">") after at most
# three spaces. QUOTES reads the block quote markers before any list marker.
LIST_MARKER = r"[ \t]*(?:[-+*]|[0-9]{1,9}[.)])[ \t]"
QUOTE_MARKER = r"[ ]{0,3}>"
CONTAINER = re.compile(rf"(?:{LIST_MARKER}|{QUOTE_MARKER})*")
QUOTES = re.compile(rf"(?:{QUOTE_MARKER})*")

# A blank line ends a paragraph, and so does a line that begins a block quote:
# raw HTML inside a paragraph crosses neither. In the text that TAG reads, a
# line begins with a block quote marker only where it begins a block quote
# (see tag_text()). CHAR is one character of a paragraph (a line break only if
# neither kind of line follows it), and WS one whitespace character of a
# paragraph.
PARAGRAPH_BREAK = rf"\n(?![ \t]*\n)(?!{QUOTE_MARKER})"
CHAR = rf"(?:[^\n]|{PARAGRAPH_BREAK})"
WS = rf"(?:[^\S\n]|{PARAGRAPH_BREAK})"


def chars_except(quote: str) -> str:
    """Return a pattern for one paragraph character other than quote."""
    return rf"(?:[^{quote}\n]|{PARAGRAPH_BREAK})"


# Raw HTML other than a comment, as CommonMark defines it: an open tag, a
# closing tag, a processing instruction, a declaration or a CDATA section,
# none of which crosses the end of a paragraph (BLOCK_TAG reads a tag that
# opens an HTML block across a blank line). A backslash before the bracket
# escapes it, and "](<...>)" is a link destination (tag_text() blanks one out
# after spaces or a line break too).
TAG = re.compile(
    rf"""
    (?<!\\)(?<!\]\()
    <(?:
        [A-Za-z][A-Za-z0-9-]*
        (?:{WS}+[A-Za-z_:][A-Za-z0-9_.:-]*
           (?:{WS}*={WS}*(?:[^\s"'=<>`]+|'{chars_except("'")}*'|"{chars_except('"')}*"))?)*
        {WS}*/?
      | /[A-Za-z][A-Za-z0-9-]*{WS}*
      | \?{CHAR}*?\?
      | ![A-Za-z]{chars_except(">")}*
      | !\[CDATA\[{CHAR}*?\]\]
    )>
    """,
    re.VERBOSE,
)

# The names with which a line that begins with "<" opens an HTML block in
# CommonMark: an open or closing tag with a name of BLOCK_NAMES, or an open
# tag with a name of RAW_NAMES. CommonMark lists "search" and GitHub's
# renderer lists "source".
BLOCK_NAMES = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|"
    "details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|"
    "h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|"
    "optgroup|option|p|param|search|section|source|summary|table|tbody|td|tfoot|th|thead|"
    "title|tr|track|ul"
)
RAW_NAMES = "pre|script|style|textarea"

# A tag that begins a line, after indentation and list or block quote markers,
# with a name that opens an HTML block. The HTML block holds the line as raw
# HTML even when a blank line splits the tag, so the tag is read across a
# blank line.
BLOCK_TAG = re.compile(
    rf"""
    ^(?=(?:[ \t]*(?:>|(?:[-+*]|[0-9]{{1,9}}[.)])[ \t]))*[ \t]*
    (?P<tag><(?:
        (?:{BLOCK_NAMES}|{RAW_NAMES})
        (?:\s+[A-Za-z_:][A-Za-z0-9_.:-]*(?:\s*=\s*(?:[^\s"'=<>`]+|'[^']*'|"[^"]*"))?)*
        \s*/?
      | /(?:{BLOCK_NAMES})\s*
    )>))
    """,
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)

# A backtick string: a run of backticks, read whole. code_spans() pairs the
# backtick strings that begin and end each code span.
BACKTICKS = re.compile(r"`+")
# The line break that begins a blank line, which ends a paragraph.
PARAGRAPH_END = re.compile(r"\n[ \t]*\n")

# A link destination in angle brackets (the group) after a link text, "(",
# spaces and at most one line break, followed by the ")" that ends the link or
# by spaces and a link title.
DESTINATION = re.compile(
    rf"\[(?:[^\[\]\n]|{PARAGRAPH_BREAK}|\[[^\[\]\n]*\])*\]\([ \t]*(?:\n[ \t]*)?(<[^<>\n]*>)"
    r"(?=[ \t]*(?:\n[ \t]*)?\)|(?=[ \t\n])[ \t]*(?:\n[ \t]*)?[\"'(])"
)

FIX = "write the placeholder as a code span (`<name>`) or escape the bracket (\\<name>)"


def blank(match: re.Match) -> str:
    """Return the matched text with every character but a line break replaced by a space."""
    return re.sub(r"[^\n]", " ", match.group(0))


def blank_group(match: re.Match, group: int) -> str:
    """Return the matched text with the text of group blanked out as blank() does."""
    start, end = match.start(group) - match.start(), match.end(group) - match.start()
    text = match.group(0)
    return text[:start] + re.sub(r"[^\n]", " ", text[start:end]) + text[end:]


def code_spans(text: str) -> Callable[[int], tuple[int, int] | None]:
    """Return a function that gives the start and end offsets of the first code
    span of text that begins at or after an offset, or None when none does.

    A code span is a backtick string that neither a backtick nor a backslash
    precedes, then text that does not end the paragraph, then the next
    backtick string of the same length. Each backtick string is paired once
    with the next string of its length, so a paragraph with many backtick
    strings that no later string of the same length closes is not read again
    to its end from each of them.
    """
    runs = [match.span() for match in BACKTICKS.finditer(text)]
    # The next backtick string of the same length as each, read from the last.
    closing: list[int | None] = [None] * len(runs)
    latest: dict[int, int] = {}
    for index in reversed(range(len(runs))):
        start, end = runs[index]
        closing[index] = latest.get(end - start)
        latest[end - start] = index
    # The code span each backtick string opens, in order. The first blank line
    # found so far is kept while the scan moves forward.
    spans = []
    brk = -1
    for index, (start, end) in enumerate(runs):
        close = closing[index]
        if close is None or text[start - 1:start] == "\\":
            continue
        if brk < end:
            found = PARAGRAPH_END.search(text, end)
            brk = found.start() if found else len(text)
        if runs[close][0] < brk:
            spans.append((start, runs[close][1]))
    starts = [start for start, _ in spans]

    def search(pos: int) -> tuple[int, int] | None:
        index = bisect.bisect_left(starts, pos)
        return spans[index] if index < len(spans) else None

    return search


def prose(text: str) -> str:
    """Return text with fenced code blocks and code spans blanked out.

    Offsets and line breaks are kept, so a position in the result is the same
    position in text.
    """
    lines = []
    fence = None
    for line in text.split("\n"):
        if fence is not None:
            if check_naming.closes(line, fence):
                fence = None
            lines.append(" " * len(line))
            continue
        fence = check_naming.opening_fence(line)
        lines.append(" " * len(line) if fence is not None else line)
    text = "\n".join(lines)
    search = code_spans(text)
    parts = []
    last = 0
    while (span := search(last)) is not None:
        parts += [text[last:span[0]], re.sub(r"[^\n]", " ", text[span[0]:span[1]])]
        last = span[1]
    parts.append(text[last:])
    return "".join(parts)


def tag_text(body: str) -> str:
    """Return body as TAG reads it.

    A line begins a block quote where the block quote markers before its
    first list marker outnumber the block quote markers of each earlier line
    after the last blank line. Such a line keeps its markers, so
    PARAGRAPH_BREAK ends the paragraph before it. The block quote markers of
    any other line are not text and are blanked out, and so are link
    destinations in angle brackets. Offsets and line breaks are kept.
    """
    lines = []
    depth = 0  # the most block quote markers on a line after the last blank line
    for line in body.split("\n"):
        end = CONTAINER.match(line).end()
        quotes = line.count(">", 0, end)
        if line.count(">", 0, QUOTES.match(line).end()) <= depth:
            line = line[:end].replace(">", " ") + line[end:]
        depth = max(depth, quotes) if line[end:].strip() else 0
        lines.append(line)
    text = "\n".join(lines)
    return DESTINATION.sub(lambda match: blank_group(match, 1), text)


def findings(text: str) -> list[str]:
    """Return one reason per HTML tag in the prose of text, in document order."""
    line_starts = [0, *(match.end() for match in re.finditer("\n", text))]
    body = prose(text)
    tags = {match.start(): match.group(0) for match in TAG.finditer(tag_text(body))}
    for match in BLOCK_TAG.finditer(body):
        start = match.start("tag")
        # A code span before the tag means that the tag does not begin the line.
        if text[match.start():start] == body[match.start():start]:
            tags.setdefault(start, match.group("tag"))
    found = []
    for start, raw in sorted(tags.items()):
        lineno = bisect.bisect_right(line_starts, start)
        tag = " ".join(raw.split())
        found.append(f"line {lineno}: HTML tag in Markdown prose, not rendered: {tag!r}")
    return found


def documents(root=ROOT) -> list[str]:
    """Return the Markdown documents the check covers, as sorted paths relative to root."""
    return [name for name in check_naming.documents(root) if name.endswith(".md")]


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
            print(f"ok    {name}: no HTML tag in prose")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
