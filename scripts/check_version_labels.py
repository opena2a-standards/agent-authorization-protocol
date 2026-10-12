#!/usr/bin/env python3
"""Check that the version line of each specification document says when main has moved on.

AAP-SPEC.md and AAP-BROKER-PROFILE.md each name a draft version on their
"**Version:**" line. A reader compares that label with the Internet-Draft
submitted under the same version, so between releases the line must say that
the text carries changes the release does not:

  **Version:** 0.5.1-draft plus unreleased changes (see [Unreleased] in [CHANGELOG.md](./CHANGELOG.md))

The check reads the [Unreleased] section of CHANGELOG.md. When it records a
change (any line other than a blank line or a "###" subheading), each version
line must carry that suffix; when it records none, neither line may carry it.
The version AAP-SPEC.md names must be the one of the newest released section
of CHANGELOG.md, so the label is the last release and not the next one. At a
release the entries under [Unreleased] move to the new version's section, and
both version lines move to the new versions without the suffix. The broker
profile's version is not in a section heading and is not compared.

Exit code 0 = both documents pass. Also run by validate_examples.py so the
check runs in CI.
"""

import pathlib
import re
import sys

import check_naming

ROOT = check_naming.ROOT

CHANGELOG = "CHANGELOG.md"
SPEC = "AAP-SPEC.md"
DOCUMENTS = (SPEC, "AAP-BROKER-PROFILE.md")

SUFFIX = " plus unreleased changes (see [Unreleased] in [CHANGELOG.md](./CHANGELOG.md))"

VERSION_LINE = re.compile(r"\*\*Version:\*\*.*")
VERSION = re.compile(
    r"\*\*Version:\*\* (\d+\.\d+\.\d+-(?:draft|rc\d+|final))(" + re.escape(SUFFIX) + r")?"
)
UNRELEASED = re.compile(r"##\s+\[Unreleased\]\s*")
RELEASED = re.compile(r"##\s+\[(?!Unreleased\])([^\]]+)\].*")


def changelog_state(changelog: str) -> tuple[bool, str | None]:
    """Return whether [Unreleased] records a change, and the newest released version."""
    unreleased = False
    in_section = False
    for line in changelog.splitlines():
        if line.startswith("## "):
            released = RELEASED.fullmatch(line)
            if released:
                return unreleased, released.group(1)
            in_section = UNRELEASED.fullmatch(line) is not None
            continue
        if in_section and line.strip() and not line.startswith("### "):
            unreleased = True
    return unreleased, None


def version_line(text: str) -> tuple[int, str] | None:
    """Return the line number and text of the first version line, or None."""
    for lineno, line in enumerate(text.splitlines(), start=1):
        if VERSION_LINE.match(line):
            return lineno, line
    return None


def findings(name: str, text: str, unreleased: bool, released: str | None) -> list[str]:
    """Return one reason per way the version line of the document fails."""
    found = version_line(text)
    if found is None:
        return ["no **Version:** line"]
    lineno, line = found
    match = VERSION.fullmatch(line.rstrip())
    if match is None:
        return [f"line {lineno}: {line.strip()!r} is not '**Version:** MAJOR.MINOR.PATCH-draft',"
                f" optionally followed by {SUFFIX.strip()!r}"]
    version, suffix = match.group(1), match.group(2)
    reasons = []
    if unreleased and not suffix:
        reasons.append(f"line {lineno}: {CHANGELOG} [Unreleased] records changes, but the label"
                       f" names {version} alone; append {SUFFIX.strip()!r}")
    if not unreleased and suffix:
        reasons.append(f"line {lineno}: {CHANGELOG} [Unreleased] records no change; remove"
                       f" {SUFFIX.strip()!r}")
    if name == SPEC and released is None:
        reasons.append(f"line {lineno}: names {version}, but {CHANGELOG} has no released section")
    elif name == SPEC and version != released:
        reasons.append(f"line {lineno}: names {version}, but the newest released section of"
                       f" {CHANGELOG} is {released}; the label names the last release")
    return reasons


def check(root: pathlib.Path = ROOT) -> int:
    """Print one line per document and return the number of failures."""
    path = root / CHANGELOG
    if not path.is_file():
        print(f"FAIL  {CHANGELOG}: required document not found")
        return 1
    changelog, error = check_naming.read_text(path)
    if error:
        print(f"FAIL  {CHANGELOG}: {error}")
        return 1
    unreleased, released = changelog_state(changelog)
    failures = 0
    for name in DOCUMENTS:
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
        reasons = findings(name, text, unreleased, released)
        for reason in reasons:
            print(f"FAIL  {name}: {reason}")
        if reasons:
            failures += 1
        elif unreleased:
            print(f"ok    {name}: version line names the release and the unreleased changes")
        else:
            print(f"ok    {name}: version line names the release")
    return failures


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
