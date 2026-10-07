#!/usr/bin/env python3
"""Check that no Markdown document carries an HTML tag in its prose.

CommonMark and GitHub Markdown read an angle-bracket placeholder such as
<YYYY-MM-DD> or <name> as a raw HTML tag, and a rendered page does not show
it: "fails on as of <YYYY-MM-DD>" renders as "fails on as of ". The
repository's Markdown writes such a placeholder as a code span (`<name>`) or
with an escaped bracket (\\<name>), and carries no raw HTML.

The check fails on an HTML open or closing tag in the prose of a Markdown
document: outside fenced code blocks and code spans, not escaped, and not the
destination of a link. An HTML comment is not a tag and passes, and so is an
autolink (<https://...>), which renders as a link.

The documents are every Markdown file in the repository (check_naming.py
lists them), so a new document is covered without being listed.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import bisect
import re
import sys

import check_naming

ROOT = check_naming.ROOT

# An open tag or a closing tag, as CommonMark defines raw HTML. A backslash
# before the bracket escapes it, and "](<...>)" is a link destination.
TAG = re.compile(
    r"""
    (?<!\\)(?<!\]\()
    <(?:
        [A-Za-z][A-Za-z0-9-]*
        (?:\s+[A-Za-z_:][A-Za-z0-9_.:-]*(?:\s*=\s*(?:[^\s"'=<>`]+|'[^']*'|"[^"]*"))?)*
        \s*/?
      | /[A-Za-z][A-Za-z0-9-]*\s*
    )>
    """,
    re.VERBOSE,
)

# A code span: a backtick string, then text that does not end the paragraph,
# then a backtick string of the same length.
CODE_SPAN = re.compile(r"(?<![`\\])(`+)(?!`)((?:[^\n]|\n(?![ \t]*\n))+?)(?<!`)\1(?!`)")

FIX = "write the placeholder as a code span (`<name>`) or escape the bracket (\\<name>)"


def blank(match: re.Match) -> str:
    """Return the matched text with every character but a line break replaced by a space."""
    return re.sub(r"[^\n]", " ", match.group(0))


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
    return CODE_SPAN.sub(blank, "\n".join(lines))


def findings(text: str) -> list[str]:
    """Return one reason per HTML tag in the prose of text, in document order."""
    line_starts = [0, *(match.end() for match in re.finditer("\n", text))]
    found = []
    for match in TAG.finditer(prose(text)):
        lineno = bisect.bisect_right(line_starts, match.start())
        tag = " ".join(match.group(0).split())
        found.append(f"line {lineno}: HTML tag in Markdown prose, not rendered: {tag!r}")
    return found


def documents(root=ROOT) -> list[str]:
    """Return the Markdown documents the check covers, as sorted paths relative to root."""
    return [name for name in check_naming.documents(root) if name.endswith(".md")]


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
            print(f"ok    {name}: no HTML tag in prose")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
