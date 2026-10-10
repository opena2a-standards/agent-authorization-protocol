#!/usr/bin/env python3
"""Check that the first use of the name AIM in each document is expanded.

"AIM" alone sits beside other agent identity acronyms, so in every document a
specification reader is likely to open, the first line that contains the whole
word AIM must name it as "OpenA2A AIM (Agent Identity Management)", and that
phrase must be where the word first appears on the line. Later uses may be bare.

The documents are every Markdown file in the repository and the XML source of
each Internet-Draft (the text renders are generated from it), so a new document
is covered without being listed. The family navigation bar at the top of
README.md is a list of link labels, not prose, and is not counted as a use.
Neither is a line inside a fenced code block: a diagram label or sample output
cannot carry the expansion, so the first use must be in prose.

Exit code 0 = every document passes. A document that is not valid UTF-8 fails
with the line of the first byte that does not decode; read_text() reports it,
and the other checks read their documents through it. Also run by
validate_examples.py so the check runs in CI.
"""

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

FIRST_USE = "OpenA2A AIM (Agent Identity Management)"

# Git pathspecs: "*.md" matches at any depth, "draft-*.xml" at the top level.
PATTERNS = ("*.md", "draft-*.xml")

# Documents that must be present, so a move or rename cannot drop them from the check.
REQUIRED = (
    "README.md",
    "AAP-SPEC.md",
    "AAP-BROKER-PROFILE.md",
    "examples/orders-db-exchange.md",
)

NAV_BAR_PREFIX = "> **OpenA2A specs**"
WORD = re.compile(r"\bAIM\b")
PREFIX_LEN = FIRST_USE.index("AIM")

# A Markdown code fence: three or more backticks or tildes, indented or not (as
# inside a list item), then the info string.
FENCE = re.compile(r"\s*(`{3,}|~{3,})(.*)")


def opening_fence(line: str) -> str | None:
    """Return the fence that opens a fenced code block on line, or None."""
    match = FENCE.fullmatch(line)
    if match is None:
        return None
    fence, info = match.groups()
    # A backtick fence's info string cannot contain a backtick: "```AIM```" is inline code.
    if fence[0] == "`" and "`" in info:
        return None
    return fence


def closes(line: str, fence: str) -> bool:
    """Return True if line closes the fenced code block opened by fence."""
    match = FENCE.fullmatch(line)
    if match is None:
        return False
    closing, rest = match.groups()
    return closing[0] == fence[0] and len(closing) >= len(fence) and not rest.strip()


def first_use(text: str) -> tuple[int, str] | None:
    """Return the line number and line of the first use of AIM in text, or None.

    Lines inside a fenced code block, and the fences themselves, are skipped.
    """
    fence = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        if fence is not None:
            if closes(line, fence):
                fence = None
            continue
        fence = opening_fence(line)
        if fence is not None:
            continue
        if not line.startswith(NAV_BAR_PREFIX) and WORD.search(line):
            return lineno, line
    return None


def first_use_error(text: str) -> str | None:
    """Return None if the first use of AIM in text is expanded, else a reason."""
    found = first_use(text)
    if found is None:
        return None
    lineno, line = found
    start = WORD.search(line).start() - PREFIX_LEN
    if start >= 0 and line.startswith(FIRST_USE, start):
        return None
    return f"line {lineno}: first use of AIM is not {FIRST_USE!r}: {line.strip()}"


def tracked_documents(root: pathlib.Path) -> list[str] | None:
    """Return the tracked files matching PATTERNS, or None outside a git checkout."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", *PATTERNS],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [name for name in result.stdout.decode("utf-8").split("\0") if name]


def documents(root: pathlib.Path = ROOT) -> list[str]:
    """Return every document the check covers, as sorted paths relative to root.

    In a git checkout these are the tracked files, so local files that are never
    committed are not read. Otherwise every matching file outside a hidden
    directory is used.
    """
    names = tracked_documents(root)
    if names is None:
        paths = [*root.rglob("*.md"), *root.glob("draft-*.xml")]
        names = [
            path.relative_to(root).as_posix()
            for path in paths
            if not any(part.startswith(".") for part in path.relative_to(root).parts)
        ]
    return sorted(name for name in set(names) if (root / name).is_file())


def read_text(path: pathlib.Path) -> tuple[str | None, str | None]:
    """Return the text of path and None, or None and a reason when path is not valid UTF-8.

    The reason names the line of the first byte that does not decode. Every check
    reads its documents through this function, so such a document is reported as
    a FAIL line instead of a traceback.
    """
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError as error:
        lineno = path.read_bytes().count(b"\n", 0, error.start) + 1
        return None, (f"line {lineno}: not valid UTF-8 ({error.reason} at byte {error.start}); "
                      "save the document as UTF-8")


def check(root: pathlib.Path = ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    names = documents(root)
    for name in REQUIRED:
        if name not in names:
            print(f"FAIL  {name}: required document not found")
            failures += 1
    for name in names:
        text, error = read_text(root / name)
        if error:
            print(f"FAIL  {name}: {error}")
            failures += 1
            continue
        error = first_use_error(text)
        if error:
            print(f"FAIL  {name}: {error}")
            failures += 1
        elif first_use(text):
            print(f"ok    {name}: first use of AIM is expanded")
        else:
            print(f"ok    {name}: does not use the name AIM")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
