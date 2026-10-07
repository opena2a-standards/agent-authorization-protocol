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
words are split across lines:

  - a date anchor: "as of <YYYY-MM-DD>" or "as of the date of this revision";
  - an unscoped universal negative: "no implementation" or "no reference
    implementation" ("no known implementation" passes).

The documents are AAP-SPEC.md, AAP-BROKER-PROFILE.md and the XML source of
every Internet-Draft revision after the filed revisions -00 to -02, which are
left as filed.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

DOCUMENTS = ("AAP-SPEC.md", "AAP-BROKER-PROFILE.md")

# Internet-Draft revisions filed before this check existed; their text is not changed.
LAST_FILED_REVISION = 2
DRAFT = re.compile(r"draft-fane-opena2a-aap-(\d{2})\.xml")

# Words may be split across lines, including inside a Markdown blockquote ("> ").
SEP = r"[\s>]+"

RULES = (
    (
        "dated implementation status",
        re.compile(
            rf"\bas{SEP}of{SEP}(?:\d{{4}}-\d{{2}}-\d{{2}}|the{SEP}date{SEP}of{SEP}this{SEP}revision)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "unscoped universal negative",
        # "no implementation-defined ..." is a different phrase.
        re.compile(rf"\bno{SEP}(?:reference{SEP})?implementations?\b(?!-)", re.IGNORECASE),
    ),
)


def findings(text: str) -> list[str]:
    """Return one reason per match of a rule in text, in document order."""
    found = []
    for name, pattern in RULES:
        for match in pattern.finditer(text):
            lineno = text.count("\n", 0, match.start()) + 1
            words = " ".join(match.group(0).replace(">", " ").split())
            found.append((match.start(), f"line {lineno}: {name}: {words!r}"))
    return [reason for _, reason in sorted(found)]


def documents(root: pathlib.Path = ROOT) -> list[str]:
    """Return the documents the check covers, as paths relative to root."""
    drafts = sorted(
        path.name
        for path in root.glob("draft-fane-opena2a-aap-*.xml")
        if (match := DRAFT.fullmatch(path.name)) and int(match.group(1)) > LAST_FILED_REVISION
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
        reasons = findings(path.read_text(encoding="utf-8"))
        for reason in reasons:
            print(f"FAIL  {name}: {reason}")
        if reasons:
            failures += 1
        else:
            print(f"ok    {name}: no rejected implementation-status wording")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
