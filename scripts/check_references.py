#!/usr/bin/env python3
"""Check that AAP-SPEC.md and its newest Internet-Draft render agree on reference classes.

The References section of AAP-SPEC.md and the references of the newest
draft-fane-opena2a-aap-NN.xml each sort their entries into Normative and
Informative. A reference listed in both must be in the same class in both, so a
reader of either document sees the same dependencies.

Entries are matched by label: the Markdown label in square brackets ("[RFC 2119]",
"[AI Agent Threat Matrix]") against the render's anchor ("RFC2119") or title
("AI Agent Threat Matrix"), ignoring case, spaces and hyphens. An entry in only one
list is reported, not failed: the render carries references only it cites (RFC 8792
for folded lines, the naming appendix), and the Markdown can carry ones the render
does not. The exception is an OpenA2A family document (a target under opena2a.org or
the opena2a-standards GitHub organization): every one the render lists must be in the
Markdown list too, since both documents cite the same family.

Between drafts the Markdown is ahead of the render. A class the Markdown gives a
reference after the render was made is accepted when the [Unreleased] section of
CHANGELOG.md records it as "<label> is a normative reference" (or "an informative
reference") and the render is a submitted one: a released section of CHANGELOG.md
records it as "`draft-fane-opena2a-aap-NN` (submitted YYYY-MM-DD". A render no
released section records as submitted is the next render, and must carry the
recorded class; once the section is released, the exception lapses for every
render. A recorded class the Markdown does not list fails.

Prints one class-parity line. Exit code 0 = no shared reference differs in class and
the Markdown lists every family reference of the render.
Also run by validate_examples.py so the check runs in CI.
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

import check_naming

ROOT = pathlib.Path(__file__).resolve().parent.parent

SPEC = "AAP-SPEC.md"
CHANGELOG = "CHANGELOG.md"
DRAFT = re.compile(r"draft-fane-opena2a-aap-(\d+)\.xml")

REFERENCES_HEADING = re.compile(r"##\s+(?:\d+\.\s+)?References\s*")
CLASS_HEADING = re.compile(r"###\s+(Normative|Informative)\b.*")
CLASS_NAME = re.compile(r"\s*(Normative|Informative)\b")
# A list item that starts with one or more bracketed labels: "- [RFC 2119] / [RFC 8174], ...".
ENTRY = re.compile(r"\s*-\s+((?:\[[^\]]+\]\s*/\s*)*\[[^\]]+\])")
LABEL = re.compile(r"\[([^\]]+)\]")
# The target of an OpenA2A family document: the spec site, another opena2a.org site,
# or a repository of the opena2a-standards organization.
FAMILY = re.compile(r"https://(?:[a-z0-9-]+\.)*opena2a\.org(?:/|$)|https://github\.com/opena2a-standards/")
UNRELEASED = re.compile(r"##\s+\[Unreleased\]\s*")
RELEASED = re.compile(r"##\s+\[(?!Unreleased\])[^\]]+\].*")
# The Internet-Draft pairing of a released section: "`draft-fane-opena2a-aap-02`
# (submitted 2026-10-02; document date ...". "-02 was not submitted" is not a record.
SUBMITTED = re.compile(r"`?(draft-fane-opena2a-aap-\d+)`?\s+\(submitted\s+\d{4}-\d{2}-\d{2}\b")
# "AIP is a normative reference", "RFC 9162 is an informative reference", "[AI Agent
# Threat Matrix] is an informative reference".
RECORDED = re.compile(
    r"(?:\[([^\]]+)\]|\b([A-Z][A-Z0-9-]*(?: \d+)?)) is an? (normative|informative) reference\b"
)


def key(label: str) -> str:
    """Return the matching key of a label, anchor or title."""
    return re.sub(r"[\s-]", "", label).upper()


def markdown_references(text: str) -> list[tuple[str, str]]:
    """Return (label, class) for each entry of the References section of text."""
    entries = []
    in_section = False
    ref_class = None
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = REFERENCES_HEADING.fullmatch(line) is not None
            ref_class = None
            continue
        if not in_section:
            continue
        heading = CLASS_HEADING.fullmatch(line)
        if heading:
            ref_class = heading.group(1).lower()
            continue
        if line.startswith("#"):
            ref_class = None
            continue
        entry = ENTRY.match(line)
        if entry and ref_class:
            entries.extend((label, ref_class) for label in LABEL.findall(entry.group(1)))
    return entries


def render_references(data: bytes) -> list[tuple[str, str, str, str]]:
    """Return (anchor, title, class, target) for each reference of an RFCXML v3 document."""
    entries = []
    for group in ET.fromstring(data).iter("references"):
        name = CLASS_NAME.match(group.findtext("name", ""))
        if name is None:
            continue
        ref_class = name.group(1).lower()
        for ref in group.findall("reference"):
            title = " ".join(ref.findtext("front/title", "").split())
            entries.append((ref.get("anchor", ""), title, ref_class, ref.get("target", "")))
    return entries


def recorded_classes(changelog: str) -> dict[str, tuple[str, str]]:
    """Return {key: (label, class)} for each class the [Unreleased] section records."""
    section = []
    in_section = False
    for line in changelog.splitlines():
        if line.startswith("## "):
            in_section = UNRELEASED.fullmatch(line) is not None
            continue
        if in_section:
            section.append(line)
    recorded = {}
    for match in RECORDED.finditer(" ".join(" ".join(section).split())):
        label = match.group(1) or match.group(2)
        recorded[key(label)] = (label, match.group(3))
    return recorded


def submitted_renders(changelog: str) -> set[str]:
    """Return the draft names ("draft-fane-opena2a-aap-02") a released section records as submitted."""
    section = []
    in_section = False
    for line in changelog.splitlines():
        if line.startswith("## "):
            in_section = RELEASED.fullmatch(line) is not None
            continue
        if in_section:
            section.append(line)
    return set(SUBMITTED.findall(" ".join(" ".join(section).split())))


def render_submitted(root: pathlib.Path, render_name: str) -> bool:
    """Return whether a released section of the changelog in root records the render as submitted.

    A changelog that is not valid UTF-8 records nothing: the render is then the next render.
    """
    changelog = root / CHANGELOG
    if not changelog.is_file():
        return False
    text, error = check_naming.read_text(changelog)
    return error is None and pathlib.Path(render_name).stem in submitted_renders(text)


def render_status(render_name: str, submitted: bool) -> str:
    """Return the closing clause of a check line: whether the render is submitted or the next one."""
    if submitted:
        return f"{render_name} is submitted ({CHANGELOG})"
    return f"{render_name} is the next render (no released section of {CHANGELOG} records it as submitted)"


def newest_render(root: pathlib.Path) -> str | None:
    """Return the file name of the highest-numbered draft XML in root, or None."""
    drafts = []
    for path in root.glob("draft-fane-opena2a-aap-*.xml"):
        match = DRAFT.fullmatch(path.name)
        if match:
            drafts.append((int(match.group(1)), path.name))
    return max(drafts)[1] if drafts else None


def compare(
    md_entries: list[tuple[str, str]],
    render_entries: list[tuple[str, str, str, str]],
    recorded: dict[str, tuple[str, str]],
    render_name: str,
    submitted: bool = True,
) -> tuple[list[str], str]:
    """Return the failure lines and the class-parity summary.

    submitted: the render is a submitted one, so a class change the [Unreleased]
    section records is accepted; the next render must carry it.
    """
    failures = []
    md = {}
    for label, ref_class in md_entries:
        k = key(label)
        if k in md:
            failures.append(f"[{label}] is listed twice in {SPEC}")
            continue
        md[k] = (label, ref_class)

    render = {}
    for anchor, title, ref_class, _ in render_entries:
        render.setdefault(key(anchor), (anchor, ref_class))
        if title:
            render.setdefault(key(title), (anchor, ref_class))

    same = 0
    changed = []
    matched_anchors = set()
    for k, (label, md_class) in md.items():
        if k not in render:
            continue
        anchor, render_class = render[k]
        matched_anchors.add(anchor)
        if md_class == render_class:
            same += 1
        elif recorded.get(k, (None, None))[1] == md_class and submitted:
            changed.append(f"{label} {md_class}")
        elif recorded.get(k, (None, None))[1] == md_class:
            failures.append(
                f"[{label}] is {md_class} in {SPEC} and {render_class} in {render_name}, the"
                f" next render; {CHANGELOG} [Unreleased] records the change, so the next"
                f" render must carry it"
            )
        else:
            failures.append(
                f"[{label}] is {md_class} in {SPEC} and {render_class} in {render_name}"
                f" (record the change in the [Unreleased] section of {CHANGELOG} as"
                f' "{label} is a{"n" if md_class == "informative" else ""}'
                f' {md_class} reference", or move the entry)'
            )

    for k, (label, ref_class) in recorded.items():
        if k not in md:
            failures.append(
                f"{CHANGELOG} [Unreleased] records {label} as a {ref_class} reference;"
                f" {SPEC} does not list it"
            )
        elif md[k][1] != ref_class:
            failures.append(
                f"{CHANGELOG} [Unreleased] records {label} as a {ref_class} reference;"
                f" {SPEC} lists it as {md[k][1]}"
            )

    for anchor, _, ref_class, target in render_entries:
        if anchor not in matched_anchors and FAMILY.match(target):
            failures.append(
                f"[{anchor}] ({target}) is a family reference, {ref_class} in"
                f" {render_name}, and {SPEC} does not list it"
            )

    md_only = sorted(label for k, (label, _) in md.items() if k not in render)
    render_only = sorted({a for a, _, _, _ in render_entries} - matched_anchors)
    summary = (
        f"reference classes {SPEC} vs {render_name}: {len(matched_anchors)} shared,"
        f" {same} same class, {len(changed)} changed since the render and recorded in"
        f" {CHANGELOG} [Unreleased]{' (' + ', '.join(changed) + ')' if changed else ''},"
        f" {len(failures)} failure(s); only in {SPEC}: {', '.join(md_only) or 'none'};"
        f" only in the render: {', '.join(render_only) or 'none'};"
        f" {render_status(render_name, submitted)}"
    )
    return failures, summary


def check(root: pathlib.Path = ROOT) -> int:
    """Print the failures and the class-parity line; return the number of failures."""
    render_name = newest_render(root)
    if render_name is None:
        print("FAIL  reference classes: no draft-fane-opena2a-aap-NN.xml found")
        return 1
    texts = {}
    for name in (SPEC, *([CHANGELOG] if (root / CHANGELOG).is_file() else [])):
        texts[name], error = check_naming.read_text(root / name)
        if error:
            print(f"FAIL  reference classes: {name}: {error}")
            return 1
    md_entries = markdown_references(texts[SPEC])
    if not md_entries:
        print(f"FAIL  reference classes: no References section entries found in {SPEC}")
        return 1
    render_entries = render_references((root / render_name).read_bytes())
    if not render_entries:
        print(f"FAIL  reference classes: no references found in {render_name}")
        return 1
    recorded = recorded_classes(texts[CHANGELOG]) if CHANGELOG in texts else {}
    failures, summary = compare(
        md_entries, render_entries, recorded, render_name, render_submitted(root, render_name)
    )
    for failure in failures:
        print(f"FAIL  {failure}")
    print(f"{'FAIL' if failures else 'ok  '}  {summary}")
    return len(failures)


def main() -> int:
    return 1 if check() else 0


if __name__ == "__main__":
    sys.exit(main())
