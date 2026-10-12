#!/usr/bin/env python3
"""Tests that a printed policy binding names the reference loader's spelling of its `resolve` keys.

The worked example and Section 7.1 of the broker profile print a policy binding
for `grant://orders-db` in the non-normative policy grammar. The policy loader
of the reference implementation refuses a `resolve` key it does not know, and
it spells two keys of the grammar differently: `providerId` for `provider`, and
`ttlSeconds` with a number of seconds for a duration-valued `ttl`. A reader who
copies a binding into the reference implementation is refused unless the
spelling it accepts is printed next to the key. The tests read the `resolve`
clause of each binding and check that every key the loader does not accept
carries a comment naming the key it does, that a respelled entry keeps its
value, and that a note under the binding names the accepted keys and the commit
they were read at, so a key added to the grammar or to the set fails until the
documents are changed with it. The loader also refuses a `resolve` clause that
lacks `providerId`, `scope` or `audience`, so the tests check that each binding
carries all three once it is respelled.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

GRANT = "grant://orders-db"

# Each document that prints the binding, and the opening of its note on the reference spelling.
NOTES = {
    "examples/orders-db-exchange.md": "**Reference spelling.**",
    "AAP-BROKER-PROFILE.md": "> **Reference spelling (non-normative).**",
}

# The keys the reference policy loader accepts in a `resolve` clause, copied from
# `KNOWN_RESOLVE_KEYS` in `src/broker/grant-policy.ts` at REFERENCE_COMMIT.
REFERENCE_KEYS = ("mode", "providerId", "scope", "audience", "ttlSeconds")
REFERENCE_COMMIT = "660af0d"
REFERENCE_SOURCE = "src/broker/grant-policy.ts"

# The keys the reference policy loader requires in a `resolve` clause: it refuses a clause in
# which one of them is not a non-empty string. Read from REFERENCE_SOURCE at REFERENCE_COMMIT.
REQUIRED_KEYS = ("providerId", "scope", "audience")

# The keys of the policy grammar that the reference loader spells differently.
RESPELLED = {"provider": "providerId", "ttl": "ttlSeconds"}

ENTRY = re.compile(r"    (?P<key>[A-Za-z]+): (?P<value>[^#]*?) *(?:# (?P<comment>.*))?")
ANNOTATION = re.compile(r"\breference loader: (?P<key>[A-Za-z]+)(?:: (?P<value>\w+))?")

# The `resolve` clause of the worked example as it read before it named the reference spelling.
UNANNOTATED = """\
- grant: grant://orders-db
  match:
    trustClass: acme.com/orders:read                          # ATX capability
  resolve:
    mode: exchange
    provider: orders-idp        # thin adapter (e.g. Okta), name lives ONLY here
    scope: orders.read
    audience: https://api.orders.internal
    ttl: 300s
"""


def binding(name):
    """The one fenced yaml block of `name` that binds GRANT."""
    text = (ROOT / name).read_text(encoding="utf-8")
    blocks = re.findall(r"^```yaml\n(.*?)^```$", text, flags=re.M | re.S)
    found = [block for block in blocks if f"- grant: {GRANT}\n" in block]
    if len(found) != 1:
        raise AssertionError(f"{name}: {len(found)} yaml blocks bind {GRANT}, want 1")
    return found[0]


def resolve_entries(block):
    """A (key, value, comment) tuple for each entry of the `resolve` clause of a binding."""
    lines = block.splitlines()
    entries = []
    for line in lines[lines.index("  resolve:") + 1:]:
        if not line.startswith("    "):
            break
        entry = ENTRY.fullmatch(line)
        if entry is None:
            raise AssertionError(f"not a `key: value` entry of a resolve clause: {line!r}")
        entries.append((entry["key"], entry["value"], entry["comment"] or ""))
    if not entries:
        raise AssertionError("the resolve clause has no entries")
    return entries


def reference_spelling(entries):
    """The entries as their comments say the reference loader spells them."""
    spelled = []
    for key, value, comment in entries:
        note = ANNOTATION.search(comment)
        if note:
            key, value = note["key"], note["value"] or value
        spelled.append((key, value))
    return spelled


def refused_keys(entries):
    """The keys the reference loader refuses once each annotated entry is respelled."""
    return [key for key, _ in reference_spelling(entries) if key not in REFERENCE_KEYS]


def missing_keys(entries):
    """The keys the reference loader requires that the respelled clause lacks or leaves empty."""
    spelled = dict(reference_spelling(entries))
    return [key for key in REQUIRED_KEYS if not spelled.get(key)]


def seconds(duration):
    """The number of seconds of a duration such as `300s`, as the loader's integer is written."""
    return re.fullmatch(r"(\d+)s", duration)[1]


def note(name):
    """The reference spelling note of `name`, without quote markers, its whitespace collapsed."""
    text = (ROOT / name).read_text(encoding="utf-8")
    found = [p for p in text.split("\n\n") if p.startswith(NOTES[name])]
    if len(found) != 1:
        raise AssertionError(f"{name}: {len(found)} paragraphs start with {NOTES[name]!r}, want 1")
    return " ".join(re.sub(r"^> ?", "", found[0], flags=re.M).split())


class ResolveKeySpellingTest(unittest.TestCase):
    def test_no_key_is_refused_in_the_reference_spelling(self):
        for name in NOTES:
            with self.subTest(document=name):
                self.assertEqual(refused_keys(resolve_entries(binding(name))), [])

    def test_no_required_key_is_missing_in_the_reference_spelling(self):
        for name in NOTES:
            with self.subTest(document=name):
                self.assertEqual(missing_keys(resolve_entries(binding(name))), [])

    def test_required_keys_are_among_the_accepted_keys(self):
        self.assertTrue(set(REQUIRED_KEYS) <= set(REFERENCE_KEYS))

    def test_only_the_respelled_keys_are_annotated(self):
        for name in NOTES:
            with self.subTest(document=name):
                entries = resolve_entries(binding(name))
                annotated = {key: ANNOTATION.search(comment)["key"]
                             for key, _, comment in entries if ANNOTATION.search(comment)}
                want = {key: RESPELLED[key] for key, _, _ in entries if key in RESPELLED}
                self.assertEqual(annotated, want)

    def test_a_respelled_entry_keeps_its_value(self):
        for name in NOTES:
            with self.subTest(document=name):
                entries = resolve_entries(binding(name))
                grammar = {key: value for key, value, _ in entries}
                reference = dict(reference_spelling(entries))
                self.assertEqual(reference["providerId"], grammar["provider"])
                self.assertEqual(reference["ttlSeconds"], seconds(grammar["ttl"]))

    def test_note_names_the_accepted_keys_and_where_they_were_read(self):
        for name in NOTES:
            with self.subTest(document=name):
                text = note(name)
                for key in REFERENCE_KEYS:
                    self.assertIn(f"`{key}`", text)
                self.assertIn(f"commit `{REFERENCE_COMMIT}`", text)
                self.assertIn(f"`{REFERENCE_SOURCE}`", text)

    def test_note_names_each_respelled_key_as_the_grammar_writes_it(self):
        for name in NOTES:
            with self.subTest(document=name):
                text = note(name)
                for key, value, _ in resolve_entries(binding(name)):
                    if key in RESPELLED:
                        self.assertRegex(text, rf"`{key}(?:`|: {re.escape(value)}`)")

    def test_note_gives_the_ttl_in_seconds(self):
        for name in NOTES:
            with self.subTest(document=name):
                reference = dict(reference_spelling(resolve_entries(binding(name))))
                self.assertIn(f"`ttlSeconds: {reference['ttlSeconds']}`", note(name))

    def test_unannotated_binding_is_detected(self):
        self.assertEqual(refused_keys(resolve_entries(UNANNOTATED)), ["provider", "ttl"])

    def test_annotated_binding_reads_in_the_reference_spelling(self):
        annotated = UNANNOTATED.replace(
            "ONLY here\n", "ONLY here (reference loader: providerId)\n"
        ).replace("ttl: 300s\n", "ttl: 300s   # reference loader: ttlSeconds: 300\n")
        self.assertEqual(reference_spelling(resolve_entries(annotated)), [
            ("mode", "exchange"),
            ("providerId", "orders-idp"),
            ("scope", "orders.read"),
            ("audience", "https://api.orders.internal"),
            ("ttlSeconds", "300"),
        ])

    def test_annotation_naming_a_key_the_loader_refuses_is_detected(self):
        misspelled = UNANNOTATED.replace(
            "ONLY here\n", "ONLY here (reference loader: providerID)\n")
        self.assertEqual(refused_keys(resolve_entries(misspelled)), ["providerID", "ttl"])

    def test_binding_without_a_required_key_is_detected(self):
        annotated = UNANNOTATED.replace(
            "ONLY here\n", "ONLY here (reference loader: providerId)\n")
        self.assertEqual(missing_keys(resolve_entries(annotated)), [])
        without = annotated.replace("    audience: https://api.orders.internal\n", "")
        self.assertEqual(missing_keys(resolve_entries(without)), ["audience"])
        empty = annotated.replace("scope: orders.read\n", "scope: # none\n")
        self.assertEqual(missing_keys(resolve_entries(empty)), ["scope"])
        self.assertEqual(missing_keys(resolve_entries(UNANNOTATED)), ["providerId"])

    def test_clause_that_is_not_key_value_entries_is_not_read_as_empty(self):
        with self.assertRaises(AssertionError):
            resolve_entries("- grant: grant://orders-db\n  resolve:\n")
        with self.assertRaises(AssertionError):
            resolve_entries("- grant: grant://orders-db\n  resolve:\n    - exchange\n")


if __name__ == "__main__":
    unittest.main()
