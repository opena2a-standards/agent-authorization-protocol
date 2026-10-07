#!/usr/bin/env python3
"""Check the specification for two wordings of implementation status that go stale.

A sentence such as "as of 2026-09-08 no implementation mints cnf" is true on
the day it is written and goes stale without the text changing; "as of the
date of this revision" moves the claim's date silently every time a revision
is cut. Neither can be checked by a reader. The specification instead names
the record that answers the question (broker profile Section 14, the
reference implementation's repository, the aap-conformance repository's
conformance.json), or scopes a negative to what is known.

The check fails on two wordings, in prose and in table rows, also when the
words are split across lines or by inline markup (emphasis, a code span, an
HTML or xml2rfc element such as <em>):

  - a date anchor: "as of" followed by a date ("2026-09-08", "October 2026",
    "6 October 2026", "October 6, 2026", "2026") or by a moving anchor ("the
    date of this revision", "this revision", "this writing", "today", "now");
  - an unscoped universal negative: "no implementation", "no implementations",
    "no" with one word before "implementation" ("no reference implementation",
    "no current implementation") and "none of the implementations". A negative
    scoped to what is known passes ("no known implementation"), and so does
    "no implementation" used as a modifier ("no implementation requirement",
    "no implementation-defined claim").

The documents are AAP-SPEC.md, AAP-BROKER-PROFILE.md and the XML source of
every Internet-Draft (draft-*.xml at the top level) except the filed revisions
-00 to -02 of draft-fane-opena2a-aap, which are left as filed.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import bisect
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

DOCUMENTS = ("AAP-SPEC.md", "AAP-BROKER-PROFILE.md")

# Internet-Draft revisions filed before this check existed; their text is not changed.
LAST_FILED_REVISION = 2
DRAFT = re.compile(r"draft-fane-opena2a-aap-(\d{2})\.xml")

# Words may be split across lines, by a Markdown blockquote marker ("> "), by
# emphasis or code-span markup, or by an inline element ("<em>", "</em>").
SEP = r"(?:[\s>*_~`]|</?[A-Za-z][A-Za-z0-9]*\s*>)+"

MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
    r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b\.?"
)
DAY = r"\d{1,2}(?:st|nd|rd|th)?(?!\d)"
YEAR = r"(?:19|20)\d{2}(?!\d)"

DATE = "|".join((
    r"\d{4}-\d{2}-\d{2}(?!\d)",
    rf"{DAY}{SEP}{MONTH}(?:{SEP}{YEAR})?",
    rf"{MONTH}(?:{SEP}{DAY},?)?(?:{SEP}{YEAR})?",
    YEAR,
    rf"(?:the{SEP}date{SEP}of{SEP})?this{SEP}(?:revision|draft|version|document)\b",
    rf"(?:the{SEP}time{SEP}of{SEP})?(?:this{SEP})?writing\b",
    r"today\b",
    r"now\b",
))

# One word between "no" and "implementation" ("no current implementation"),
# unless the word scopes the negative to what is known.
QUALIFIER = rf"(?:(?!known\b)[A-Za-z][A-Za-z-]*{SEP})?"

# "implementation" as a modifier of the next noun is not a claim about implementations.
MODIFIED = (
    r"requirements?|guidance|details?|choices?|changes?|constraints?|considerations?"
    r"|burdens?|costs?|efforts?|work|notes?|advice|experience|status|reports?"
    r"|obligations?|decisions?|dependency|dependencies|latitude|freedom|flexibility"
)

NEGATIVE = "|".join((
    rf"\bno{SEP}{QUALIFIER}implementations?\b",
    rf"\bnone{SEP}of{SEP}(?:the{SEP})?{QUALIFIER}implementations\b",
))

ACCEPTED_RECORDS = ("broker profile Section 14, the reference implementation's repository, "
                    "or the aap-conformance repository's conformance.json")

RULES = (
    (
        "dated implementation status",
        re.compile(rf"\bas{SEP}of{SEP}(?:{DATE})", re.IGNORECASE),
        f"state the status without a date and name the record that holds it ({ACCEPTED_RECORDS})",
    ),
    (
        "unscoped universal negative",
        # "no implementation-defined ..." is a different phrase.
        re.compile(rf"(?:{NEGATIVE})(?!-)(?!{SEP}(?:{MODIFIED})\b)", re.IGNORECASE),
        'write "no known implementation", or name the record that holds the status '
        f"({ACCEPTED_RECORDS})",
    ),
)

ACCEPTED = {name: accepted for name, _, accepted in RULES}


def matches(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, rule name, matched words) per match, in document order."""
    line_starts = [0, *(match.end() for match in re.finditer("\n", text))]
    found = []
    for name, pattern, _ in RULES:
        for match in pattern.finditer(text):
            lineno = bisect.bisect_right(line_starts, match.start())
            words = " ".join(re.sub(SEP, " ", match.group(0)).split())
            found.append((match.start(), lineno, name, words))
    return [(lineno, name, words) for _, lineno, name, words in sorted(found)]


def findings(text: str) -> list[str]:
    """Return one reason per match of a rule in text, in document order."""
    return [f"line {lineno}: {name}: {words!r}" for lineno, name, words in matches(text)]


def documents(root: pathlib.Path = ROOT) -> list[str]:
    """Return the documents the check covers, as paths relative to root."""
    drafts = sorted(
        path.name
        for path in root.glob("draft-*.xml")
        if not ((match := DRAFT.fullmatch(path.name))
                and int(match.group(1)) <= LAST_FILED_REVISION)
    )
    return [*DOCUMENTS, *drafts]


def check(root: pathlib.Path = ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    for name in documents(root):
        path = root / name
        if not path.is_file():
            print(f"FAIL  {name}: required document not found")
            failures += 1
            continue
        found = matches(path.read_text(encoding="utf-8"))
        for lineno, rule, words in found:
            print(f"FAIL  {name}: line {lineno}: {rule}: {words!r}; {ACCEPTED[rule]}")
        if found:
            failures += 1
        else:
            print(f"ok    {name}: no rejected implementation-status wording")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
