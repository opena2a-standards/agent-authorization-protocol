#!/usr/bin/env python3
"""Validate the spec's inline JSON examples against the repo's JSON Schemas.

Reads schemas/examples-map.json, a list of entries:
    { "file": "core.md",
      "heading": "### 1.1 ATX schema",
      "schema": "schemas/atx-credential-v1.1.schema.json" }

For each entry: find the heading line in the file, take the first fenced
```json block after it, parse it, and validate it against the schema.
Also metaschema-checks every schemas/*.schema.json, runs check_naming.py
(first use of the name AIM in every Markdown document and Internet-Draft source)
and check_status_claims.py (rejects "as of <YYYY-MM-DD>", "as of the date of
this revision", "no implementation" and "no reference implementation") and
check_references.py (AAP-SPEC.md and its newest Internet-Draft render agree
on reference classes), and runs the unit tests in scripts/ (test_*.py), so CI
runs them.

Formats (date-time, uuid) are treated as annotations, not assertions, matching
library defaults across implementations; structural keywords (type, enum,
pattern, required) carry the contract.

Exit code 0 = all schemas well-formed, all mapped examples valid, every
document expands the name AIM at first use, the specification uses none of
the wordings check_status_claims.py rejects, the specification and its newest
render agree on reference classes, and every unit test passes.
"""

import json
import pathlib
import sys
import unittest

import check_naming
import check_status_claims
import check_references

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("error: the 'jsonschema' package is required (pip install jsonschema)")
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def extract_block(md_path: pathlib.Path, heading: str) -> str:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        raise SystemExit(f"error: heading {heading!r} not found in {md_path}")
    in_block = False
    block: list[str] = []
    for line in lines[start + 1:]:
        if not in_block and line.strip() == "```json":
            in_block = True
            continue
        if in_block:
            if line.strip() == "```":
                return "\n".join(block)
            block.append(line)
        elif line.startswith("#") and not block:
            raise SystemExit(
                f"error: no ```json block between {heading!r} and the next heading in {md_path}"
            )
    raise SystemExit(f"error: unterminated ```json block after {heading!r} in {md_path}")


def run_unit_tests(start_dir: pathlib.Path = SCRIPTS) -> int:
    """Run the unit tests (test_*.py) in start_dir and return the number of failures.

    Finding no test at all counts as one failure, so a moved or renamed test file
    cannot drop the tests from CI.
    """
    suite = unittest.TestLoader().discover(
        str(start_dir), pattern="test_*.py", top_level_dir=str(start_dir)
    )
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    if result.testsRun == 0:
        print(f"unit tests FAIL  no test_*.py tests found in {start_dir}")
        return 1
    failed = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    if failed:
        print(f"unit tests FAIL  {failed} of {result.testsRun} failed")
    else:
        print(f"unit tests OK    {result.testsRun} passed")
    return failed


def main() -> int:
    failures = 0

    schema_files = sorted((ROOT / "schemas").glob("*.schema.json"))
    if not schema_files:
        print("error: no schemas/*.schema.json found")
        return 1
    for sf in schema_files:
        schema = json.loads(sf.read_text(encoding="utf-8"))
        try:
            Draft202012Validator.check_schema(schema)
            print(f"schema OK      {sf.relative_to(ROOT)}")
        except Exception as exc:  # noqa: BLE001 - report and fail
            print(f"schema INVALID {sf.relative_to(ROOT)}: {exc}")
            failures += 1

    map_path = ROOT / "schemas" / "examples-map.json"
    entries = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else []
    for entry in entries:
        md = ROOT / entry["file"]
        schema_path = ROOT / entry["schema"]
        raw = extract_block(md, entry["heading"])
        try:
            instance = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"example INVALID JSON  {entry['file']} @ {entry['heading']!r}: {exc}")
            failures += 1
            continue
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.json_path)
        if errors:
            print(f"example FAIL   {entry['file']} @ {entry['heading']!r} vs {entry['schema']}")
            for err in errors:
                print(f"    {err.json_path}: {err.message}")
            failures += 1
        else:
            print(f"example OK     {entry['file']} @ {entry['heading']!r}")

    failures += check_naming.check()
    failures += check_status_claims.check()
    failures += check_references.check()
    failures += run_unit_tests()

    if failures:
        print(f"\n{failures} failure(s)")
        return 1
    print(
        "\nall schemas and mapped examples valid; first use of AIM expanded; "
        "no rejected implementation-status wording; reference classes agree; "
        "unit tests pass"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
