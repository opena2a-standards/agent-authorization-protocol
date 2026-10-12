#!/usr/bin/env python3
"""Tests that AAP-SPEC.md states what governs the lifetime of each token it defines.

The `iat` / `exp` row of each claim table states what governs `exp - iat`: the
Section 4.3 tiers for the CGT, the 60-second TTL for the BAC, and, for the AIT,
the issuing Registry, since Section 3.2 sets no upper bound. The DA carries the
CGT claims (Section 5.3), so its row is the CGT's. Section 3.2 cites the lifetime
of its example, which must be the `exp - iat` of the generated AIT claim set and
of the decoded claim set printed in that section.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The section holding each claim table, with what its `iat` / `exp` row names as
# governing `exp - iat`.
LIFETIME = {
    "3.2": re.compile(r"the issuing Registry sets `exp - iat`"),
    "4.2": re.compile(r"`exp - iat` is the policy TTL \(§4\.3\)"),
    "6.4": re.compile(r"`exp - iat` MUST be ≤ 60"),
}

EXAMPLE_LIFETIME = re.compile(r"the example below uses (\d+) seconds")


def section(number):
    """The text of AAP-SPEC.md section `number`, up to the next heading of any level."""
    text = (ROOT / "AAP-SPEC.md").read_text(encoding="utf-8")
    start = re.search(rf"^### {re.escape(number)} ", text, re.MULTILINE)
    if start is None:
        raise AssertionError(f"AAP-SPEC.md has no section {number}")
    end = re.compile(r"^#{2,3} ", re.MULTILINE).search(text, start.end())
    return text[start.end():end.start() if end else len(text)]


def lifetime_row(number):
    """The `iat` / `exp` row of the claim table in section `number`."""
    rows = [line for line in section(number).splitlines() if line.startswith("| `iat` / `exp` |")]
    if len(rows) != 1:
        raise AssertionError(f"section {number}: {len(rows)} `iat` / `exp` rows, want 1")
    return rows[0]


def printed_claims(number):
    """The first JSON claim set printed in section `number`."""
    match = re.search(r"```json\n(.*?)\n```", section(number), re.DOTALL)
    if match is None:
        raise AssertionError(f"section {number} prints no JSON claim set")
    return json.loads(match.group(1))


class AitLifetimeTest(unittest.TestCase):
    def test_each_lifetime_row_states_what_governs_it(self):
        for number, governs in LIFETIME.items():
            with self.subTest(section=number):
                self.assertRegex(lifetime_row(number), governs)

    def test_section_3_2_states_that_no_upper_bound_is_set(self):
        prose = " ".join(section("3.2").split())
        self.assertIn("This specification sets no upper bound on it", prose)

    def test_cited_example_lifetime_matches_the_claim_sets(self):
        match = EXAMPLE_LIFETIME.search(" ".join(section("3.2").split()))
        self.assertIsNotNone(match, "section 3.2 no longer cites the lifetime of its example")
        cited = int(match.group(1))
        fixture = json.loads((ROOT / "examples/tokens/ait-v1.claims.json").read_text(encoding="utf-8"))
        printed = printed_claims("3.2")
        self.assertEqual(fixture["exp"] - fixture["iat"], cited)
        self.assertEqual(printed["exp"] - printed["iat"], cited)


if __name__ == "__main__":
    unittest.main()
