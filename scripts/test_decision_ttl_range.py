#!/usr/bin/env python3
"""Tests that the ML-DSA-65 decision note's token lifetime range matches the specification.

decisions/2026-07-16-mldsa65-serialization-profile.md argues from the range of
token lifetimes ("AAP tokens are short-TTL (60 s BAC to 4 h STANDARD CGT)"). The
range must cover every lifetime the specification defines: its lower end is the
60-second TTL of the BAC (AAP-SPEC Section 6.1), and its upper end is the longest
CGT tier of AAP-SPEC Section 4.3, named by its tier. A DA expires no later than
its grant (Section 5.3), so the CGT tiers bound it too.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTE = ROOT / "decisions" / "2026-07-16-mldsa65-serialization-profile.md"
SPEC = ROOT / "AAP-SPEC.md"

TIERS_HEADING = "### 4.3 TTL Tiers"
TIER = re.compile(r"^- ([A-Z_]+): (\d+) (hours?|minutes?|seconds?)\b")
BAC_TTL = re.compile(r"`exp - iat` MUST be ≤ (\d+) \(the \d+-second TTL, §6\.1\)")
RANGE = re.compile(
    r"short-TTL \((\d+) (s|min|h) ([A-Z]+) to (\d+) (s|min|h) ([A-Z_]+(?: [A-Z]+)?)\)"
)

UNIT_SECONDS = {
    "s": 1, "second": 1, "seconds": 1,
    "min": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hour": 3600, "hours": 3600,
}


def spec_tiers():
    """Return the TTL tiers of AAP-SPEC Section 4.3 as {name: seconds}."""
    lines = SPEC.read_text(encoding="utf-8").splitlines()
    start = lines.index(TIERS_HEADING)
    tiers = {}
    for line in lines[start + 1:]:
        if line.startswith("#"):
            break
        match = TIER.match(line)
        if match:
            tiers[match.group(1)] = int(match.group(2)) * UNIT_SECONDS[match.group(3)]
    return tiers


def spec_bac_ttl():
    """Return the BAC's maximum lifetime in seconds from the Section 6 claims table."""
    matches = BAC_TTL.findall(SPEC.read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise AssertionError(f"expected one BAC TTL row in AAP-SPEC.md, found {len(matches)}")
    return int(matches[0])


def note_ranges():
    """Return each lifetime range stated in the note, the line breaks joined."""
    text = " ".join(NOTE.read_text(encoding="utf-8").split())
    return RANGE.findall(text)


class DecisionTtlRangeTest(unittest.TestCase):
    def test_spec_defines_tiers(self):
        tiers = spec_tiers()
        self.assertGreaterEqual(len(tiers), 3, tiers)

    def test_note_states_one_range(self):
        self.assertEqual(len(note_ranges()), 1, "expected one short-TTL range in the note")

    def test_lower_end_is_the_bac_ttl(self):
        (low, low_unit, low_token, _, _, _), = note_ranges()
        self.assertEqual(low_token, "BAC")
        self.assertEqual(int(low) * UNIT_SECONDS[low_unit], spec_bac_ttl())

    def test_upper_end_is_the_longest_cgt_tier(self):
        (_, _, _, high, high_unit, high_name), = note_ranges()
        tiers = spec_tiers()
        longest = max(tiers, key=tiers.get)
        self.assertEqual(high_name, f"{longest} CGT")
        self.assertEqual(int(high) * UNIT_SECONDS[high_unit], tiers[longest])

    def test_range_covers_every_defined_lifetime(self):
        (low, low_unit, _, high, high_unit, _), = note_ranges()
        low_s = int(low) * UNIT_SECONDS[low_unit]
        high_s = int(high) * UNIT_SECONDS[high_unit]
        for name, seconds in {**spec_tiers(), "BAC": spec_bac_ttl()}.items():
            with self.subTest(token=name):
                self.assertLessEqual(low_s, seconds)
                self.assertGreaterEqual(high_s, seconds)


if __name__ == "__main__":
    unittest.main()
