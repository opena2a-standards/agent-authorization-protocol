#!/usr/bin/env python3
"""Check that the documents use American spelling for two word families.

The repository spells "authorization" and "behavior" the American way, so a
British form of the same family reads as an inconsistency. The check fails on
two families, in any letter case, with any prefix:

  - a word that ends in -our where American spelling has -or, on the stems in
    OUR_STEMS, with any ending ("honour", "behavioural", "favourite"; write
    "honor", "behavioral", "favorite");
  - a word with -is- where American spelling has -iz-, on the stems in
    ISE_STEMS followed by an ending in ISE_ENDINGS ("authorise",
    "organisational", "unrecognised"; write "authorize", "organizational",
    "unrecognized"). A word with an ending ISE_ENDINGS does not list passes.

Only listed stems are read, so words whose American spelling ends in -our or
-ise ("hour", "detour", "glamour", "advertise", "exercise", "compromise",
"improvisation") pass, and so does "emphases", the plural of "emphasis".

The documents are every Markdown file in the repository and the XML source of
each Internet-Draft (check_naming.py lists them), so a new document is covered
without being listed. Code is not read, as sample output or an identifier there
can carry a spelling the repository does not choose: in Markdown, a fenced code
block or a code span (`normalise()`); in the XML source of an Internet-Draft, a
<sourcecode> or <artwork> element or inline code (<tt>), which are its forms of
a fenced code block and a code span.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import re
import sys

import check_naming
import check_raw_html

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
ISE_ENDINGS = (
    "able", "ably", "ation", "ational", "ations", "e", "ed", "er", "ers", "es",
    "ing", "ingly",
)


def alternation(words) -> str:
    """Return a regex alternation of words, longest first."""
    return "|".join(sorted(words, key=len, reverse=True))


OUR = re.compile(rf"\b(\w*?(?:{alternation(OUR_STEMS)}))(ou)(r\w*)", re.IGNORECASE)
ISE = re.compile(
    rf"\b(\w*?(?:{alternation(ISE_STEMS)})i)(s)((?:{alternation(ISE_ENDINGS)})\b)",
    re.IGNORECASE,
)

# An Internet-Draft element that holds code or a diagram, with its tags. A
# self-closing element (<artwork src="a.svg"/>) holds no text and is not matched.
XML_CODE = re.compile(r"<(sourcecode|artwork|tt)(?:\s[^>]*)?(?<!/)>.*?</\1\s*>", re.DOTALL)


def american(match: re.Match) -> str:
    """Return the American spelling of the British word match holds."""
    head, british, tail = match.groups()
    if british.lower() == "ou":
        return head + british[0] + tail
    return head + ("Z" if british.isupper() else "z") + tail


def prose(text: str, xml: bool = False) -> str:
    """Return text with its code blanked out, keeping offsets and line breaks.

    Markdown code is a fenced code block, with its fences, or a code span; with
    xml, text is the XML source of an Internet-Draft and its code is each
    element XML_CODE matches.
    """
    if xml:
        return XML_CODE.sub(check_raw_html.blank, text)
    return check_raw_html.prose(text)


def matches(text: str, xml: bool = False) -> list[tuple[int, str, str]]:
    """Return (line number, British word, American word) per match, in document order.

    Code, as prose() reads it, is skipped.
    """
    found = []
    for lineno, line in enumerate(prose(text, xml).splitlines(), start=1):
        words = [*OUR.finditer(line), *ISE.finditer(line)]
        for match in sorted(words, key=lambda m: m.start()):
            found.append((lineno, match.group(0), american(match)))
    return found


def findings(text: str, xml: bool = False) -> list[str]:
    """Return one reason per British spelling in text, in document order.

    With xml, text is read as the XML source of an Internet-Draft, else as Markdown.
    """
    return [f"line {lineno}: {british!r}; write {fix!r}"
            for lineno, british, fix in matches(text, xml)]


def check(root=ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    for name in check_naming.documents(root):
        text = (root / name).read_text(encoding="utf-8")
        reasons = findings(text, xml=name.endswith(".xml"))
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
