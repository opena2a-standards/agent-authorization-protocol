#!/usr/bin/env python3
"""Check that the documents use American spelling for two word families.

The repository spells "authorization" and "behavior" the American way, so a
British form of the same family reads as an inconsistency. The check fails on
two families, in any letter case, with any prefix or ending:

  - a word that ends in -our where American spelling has -or, on the stems in
    OUR_STEMS ("honour", "behavioural", "favourite"; write "honor",
    "behavioral", "favorite");
  - a word with -is- where American spelling has -iz-, on the stems in
    ISE_STEMS followed by an ending in ISE_ENDINGS ("authorise",
    "organisation", "unrecognised"; write "authorize", "organization",
    "unrecognized").

Only listed stems are read, so words whose American spelling ends in -our or
-ise ("hour", "detour", "glamour", "advertise", "exercise", "compromise",
"improvisation") pass, and so does "emphases", the plural of "emphasis".

The documents are every Markdown file in the repository and the XML source of
each Internet-Draft (check_naming.py lists them), so a new document is covered
without being listed. A line inside a fenced code block is not read: sample
output or an identifier there can carry a spelling the repository does not
choose.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import re
import sys

import check_naming

ROOT = check_naming.ROOT

# The part of each word before "our", whose American spelling ends in "or".
OUR_STEMS = (
    "arm", "behavi", "cand", "clam", "col", "endeav", "fav", "flav", "harb",
    "hon", "hum", "lab", "neighb", "od", "parl", "rig", "rum", "sav", "savi",
    "splend", "tum", "val", "vap", "vig",
)

# The part of each word before "is", whose American spelling has "iz".
ISE_STEMS = (
    "author", "canonical", "categor", "central", "character", "critic", "custom",
    "final", "general", "initial", "local", "maxim", "memor", "minim", "normal",
    "optim", "organ", "personal", "priorit", "random", "real", "recogn", "sanit",
    "serial", "special", "stabil", "standard", "summar", "synchron", "token",
    "util", "visual",
)

# Endings after "is"; "-ism" and "-ist" ("criticism", "specialist") are not listed.
ISE_ENDINGS = ("able", "ation", "ations", "e", "ed", "er", "ers", "es", "ing")


def alternation(words) -> str:
    """Return a regex alternation of words, longest first."""
    return "|".join(sorted(words, key=len, reverse=True))


OUR = re.compile(rf"\b(\w*?(?:{alternation(OUR_STEMS)}))(ou)(r\w*)", re.IGNORECASE)
ISE = re.compile(
    rf"\b(\w*?(?:{alternation(ISE_STEMS)})i)(s)((?:{alternation(ISE_ENDINGS)})\b)",
    re.IGNORECASE,
)


def american(match: re.Match) -> str:
    """Return the American spelling of the British word match holds."""
    head, british, tail = match.groups()
    if british.lower() == "ou":
        return head + british[0] + tail
    return head + ("Z" if british.isupper() else "z") + tail


def matches(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, British word, American word) per match, in document order.

    Lines inside a fenced code block, and the fences themselves, are skipped.
    """
    found = []
    fence = None
    for lineno, line in enumerate(text.splitlines(), start=1):
        if fence is not None:
            if check_naming.closes(line, fence):
                fence = None
            continue
        fence = check_naming.opening_fence(line)
        if fence is not None:
            continue
        words = [*OUR.finditer(line), *ISE.finditer(line)]
        for match in sorted(words, key=lambda m: m.start()):
            found.append((lineno, match.group(0), american(match)))
    return found


def findings(text: str) -> list[str]:
    """Return one reason per British spelling in text, in document order."""
    return [f"line {lineno}: {british!r}; write {fix!r}"
            for lineno, british, fix in matches(text)]


def check(root=ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    for name in check_naming.documents(root):
        reasons = findings((root / name).read_text(encoding="utf-8"))
        for reason in reasons:
            print(f"FAIL  {name}: {reason}")
        if reasons:
            failures += 1
        else:
            print(f"ok    {name}: American spelling")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
