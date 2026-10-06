#!/usr/bin/env python3
"""Check that the first use of the name AIM in each listed document is expanded.

"AIM" alone sits beside other agent identity acronyms, so in every document a
specification reader is likely to open, the first line that contains the whole
word AIM must name it as "OpenA2A AIM (Agent Identity Management)", and that
phrase must be where the word first appears on the line. Later uses may be bare.

The family navigation bar at the top of README.md is a list of link labels, not
prose, and is not counted as a use.

Exit code 0 = every listed document passes. Also run by validate_examples.py so
the check runs in CI.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

FIRST_USE = "OpenA2A AIM (Agent Identity Management)"

DOCUMENTS = [
    "README.md",
    "AAP-SPEC.md",
    "AAP-BROKER-PROFILE.md",
    "examples/orders-db-exchange.md",
]

NAV_BAR_PREFIX = "> **OpenA2A specs**"
WORD = re.compile(r"\bAIM\b")
PREFIX_LEN = FIRST_USE.index("AIM")


def first_use_error(text: str) -> str | None:
    """Return None if the first use of AIM in text is expanded, else a reason."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.startswith(NAV_BAR_PREFIX):
            continue
        match = WORD.search(line)
        if match is None:
            continue
        start = match.start() - PREFIX_LEN
        if start >= 0 and line.startswith(FIRST_USE, start):
            return None
        return f"line {lineno}: first use of AIM is not {FIRST_USE!r}: {line.strip()}"
    return None


def check() -> int:
    """Print one line per listed document and return the number of failures."""
    failures = 0
    for name in DOCUMENTS:
        path = ROOT / name
        if not path.is_file():
            print(f"FAIL  {name}: listed document not found")
            failures += 1
            continue
        error = first_use_error(path.read_text(encoding="utf-8"))
        if error:
            print(f"FAIL  {name}: {error}")
            failures += 1
        else:
            print(f"ok    {name}: first use of AIM is expanded")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
