#!/usr/bin/env python3
"""Check the specification for three wordings of implementation status that go stale.

A sentence such as "as of 2026-09-08 no implementation mints cnf" is true on
the day it is written and goes stale without the text changing; "as of the
date of this revision" moves the claim's date silently every time a revision
is cut; "the daemon does not yet serve it" carries an unstated date in "yet".
None can be checked by a reader. The specification instead names the record
that answers the question (broker profile Section 14, the reference
implementation's repository, the aap-conformance repository's
conformance.json), or scopes a negative to what is known.

The check fails on three wordings, in prose and in table rows, also when the
words are split across lines or by inline markup (emphasis, a code span, an
HTML or xml2rfc element such as <em>):

  - a date anchor: "as of" followed by a date ("2026-09-08", "October 2026",
    "6 October 2026", "October 6, 2026", "2026") or by a moving anchor ("the
    date of this revision", "this revision", "this writing", "today", "now");
  - an unscoped universal negative: "no implementation", "no implementations",
    "no" with one word before "implementation" ("no reference implementation",
    "no current implementation") and "none of the implementations". A negative
    scoped to what is known passes ("no known implementation"), and so do a
    normative statement, whose qualifier makes it a requirement and not a
    status ("no conforming implementation accepts ...", "no compliant
    implementation", "no conformant implementation"), and "no implementation"
    used as a modifier ("no implementation requirement", "no
    implementation-defined claim");
  - a status stated with "yet": "not yet" ("does not yet construct", "doesn't
    yet resolve"), "yet to" ("has yet to ship"), "as yet", and "yet" closing a
    negative in the same clause ("no reference implementation yet", "no
    standalone act-chain minting yet"). "yet" as a conjunction passes ("short
    yet complete", "no cnf member, yet the broker binds it"), and so does a
    token's own validity window ("not yet valid", "not yet expired", "a jti
    not yet seen"), which is protocol state and not implementation status.

The documents are AAP-SPEC.md, AAP-BROKER-PROFILE.md, README.md and
docs/use-cases.md (their use cases state what the reference implementation
does), docs/reference-implementation.md (what the reference implementation
does and its limits), docs/status.md (the released versions and the current
Internet-Draft revision), schemas/README.md (its Status column states what the
reference implementation mints), every JSON file in schemas/ (schemas/*.json),
of which the check reads each "description" string, at any depth, as prose and
reports the line of that string, and the XML source of every Internet-Draft
(draft-*.xml at the top level) except the filed revisions -00 to -02 of
draft-fane-opena2a-aap, which are left as filed. A document that is not valid
UTF-8 fails with the line of the first byte that does not decode, and a JSON
file that does not parse fails with the line of the error.

Exit code 0 = every document passes. Also run by validate_examples.py so the
check runs in CI.
"""

import bisect
import json
import pathlib
import re
import sys

import check_naming

ROOT = pathlib.Path(__file__).resolve().parent.parent

DOCUMENTS = (
    "AAP-SPEC.md",
    "AAP-BROKER-PROFILE.md",
    "README.md",
    "docs/use-cases.md",
    "docs/reference-implementation.md",
    "docs/status.md",
    "schemas/README.md",
)

# The JSON files whose "description" strings the check reads as prose.
SCHEMA_DIR = "schemas"

# A JSON string token. Outside a string, valid JSON holds no quotation mark, so one
# left-to-right scan finds every string of a document that parses.
JSON_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')

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
# unless the word scopes the negative to what is known or makes it a normative
# statement ("no conforming implementation accepts ..." is a requirement).
SCOPED = r"known|conforming|conformant|compliant"
QUALIFIER = rf"(?:(?!(?:{SCOPED})\b)[A-Za-z][A-Za-z-]*{SEP})?"

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

# "yet" dates a status without naming the date. A negative and "yet" count only
# within one clause, so "yet" as a conjunction after a comma or in the next
# sentence passes; a token's own validity window ("not yet valid") is protocol
# state, not implementation status.
NEGATION = r"\bno(?:ne|thing)?\b|\bnot\b|\b[A-Za-z]+n['’]t\b"
CLAUSE = r"[^.;:,()\[\]|]{0,80}?"
WINDOW = r"valid|expired|seen|used|elapsed|reached"

YET = "|".join((
    rf"(?:{NEGATION}){CLAUSE}\byet\b(?!{SEP}(?:{WINDOW})\b)",
    rf"\byet{SEP}to\b",
    rf"\bas{SEP}yet\b",
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
    (
        "status stated with yet",
        re.compile(YET, re.IGNORECASE),
        'state what the text defines without "yet", and name the record that holds the '
        f"status ({ACCEPTED_RECORDS})",
    ),
)

ACCEPTED = {name: accepted for name, _, accepted in RULES}


def spoken(separator: re.Match) -> str:
    """Read a separator as a space if it holds whitespace, else as markup inside a word."""
    run = separator.group(0)
    if any(char.isspace() for char in run):
        return " "
    # "fga_constraints" keeps its underscore; "`act`-chain" reads "act-chain".
    text, start, end = separator.string, separator.start(), separator.end()
    if run == "_" and text[start - 1:start].isalnum() and text[end:end + 1].isalnum():
        return run
    return ""


def matches(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, rule name, matched words) per match, in document order."""
    line_starts = [0, *(match.end() for match in re.finditer("\n", text))]
    found = []
    for name, pattern, _ in RULES:
        for match in pattern.finditer(text):
            lineno = bisect.bisect_right(line_starts, match.start())
            words = " ".join(re.sub(SEP, spoken, match.group(0)).split())
            found.append((match.start(), lineno, name, words))
    return [(lineno, name, words) for _, lineno, name, words in sorted(found)]


def findings(text: str) -> list[str]:
    """Return one reason per match of a rule in text, in document order."""
    return [f"line {lineno}: {name}: {words!r}" for lineno, name, words in matches(text)]


def descriptions(text: str) -> list[tuple[int, str]]:
    """Return (line number, value) for every "description" member whose value is a string.

    text must parse as JSON. A string token followed by a colon is a member name, and a
    string that follows the name "description" and its colon is that member's value, at
    any depth of the document.
    """
    line_starts = [0, *(match.end() for match in re.finditer("\n", text))]
    tokens = list(JSON_STRING.finditer(text))
    return [
        (bisect.bisect_right(line_starts, value.start()), json.loads(value.group(0)))
        for name, value in zip(tokens, tokens[1:])
        if json.loads(name.group(0)) == "description"
        and re.fullmatch(r"\s*:\s*", text[name.end():value.start()])
    ]


def description_matches(text: str) -> list[tuple[int, str, str]]:
    """Return (line number, rule name, matched words) per match in a description string.

    Each description is read on its own, so words in two descriptions never form one
    match, and a match is reported at the line of its string in the JSON file.
    """
    return [(lineno, name, words)
            for lineno, description in descriptions(text)
            for _, name, words in matches(description)]


def documents(root: pathlib.Path = ROOT) -> list[str]:
    """Return the documents the check covers, as paths relative to root."""
    schemas = sorted(f"{SCHEMA_DIR}/{path.name}" for path in (root / SCHEMA_DIR).glob("*.json"))
    drafts = sorted(
        path.name
        for path in root.glob("draft-*.xml")
        if not ((match := DRAFT.fullmatch(path.name))
                and int(match.group(1)) <= LAST_FILED_REVISION)
    )
    return [*DOCUMENTS, *schemas, *drafts]


def check(root: pathlib.Path = ROOT) -> int:
    """Print one line per document and return the number of failures."""
    failures = 0
    for name in documents(root):
        path = root / name
        if not path.is_file():
            print(f"FAIL  {name}: required document not found")
            failures += 1
            continue
        text, error = check_naming.read_text(path)
        if error:
            print(f"FAIL  {name}: {error}")
            failures += 1
            continue
        if name.endswith(".json"):
            try:
                json.loads(text)
            except json.JSONDecodeError as invalid:
                print(f"FAIL  {name}: line {invalid.lineno}: not valid JSON ({invalid.msg} at "
                      f"column {invalid.colno}); correct the JSON so the check can read its "
                      "description strings")
                failures += 1
                continue
            found = description_matches(text)
        else:
            found = matches(text)
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
