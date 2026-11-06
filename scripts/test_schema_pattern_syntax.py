#!/usr/bin/env python3
"""Tests that no schema pattern holds a lookaround group or a `\\u` escape.

JSON Schema names ECMA-262 as the dialect of `pattern`, and the jsonschema package
evaluates it with Python's `re`. Go's `regexp`, which accepts RE2 syntax, refuses to
compile a pattern that holds a lookaround group (`(?=`, `(?!`, `(?<=`, `(?<!`) or a `\\u`
escape, while ECMA-262 with the `u` flag and Python's `re` compile both, so a validator
built on Go's `regexp` cannot use a schema that holds either.

The tests read the `pattern` keyword of every schema in schemas/ and refuse two forms:

- a group that opens with `(?` other than `(?:`, the non-capturing group, which refuses
  each lookaround group;
- an escape other than these, which refuses each `\\u` escape: a backslash before one of
  the characters of ESCAPED_PUNCTUATION, or before `-` inside a character class; `\\f`,
  `\\n`, `\\r`, `\\t` and `\\v`; and `\\x` followed by two hexadecimal digits.

Each escape the second form allows compiles under Go's `regexp`, under ECMA-262 with the
`u` flag and under Python's `re`, and matches the same one character under each, over the
code points U+0000 to U+FFFF outside the surrogates. The tests read a character class as
Python's `re` reads it: `(` and `?` inside it are members, a backslash inside it opens an
escape, and a `]` directly after the `[` or `[^` that opens it is a member, not its end.
They read every member named `pattern` whose value is a string, at any depth, so one
inside an example is read as well.

The tests also check that each pattern compiles under Python's `re`, and that the three
patterns of FORMER_DISCOVERY_PATTERNS, which the discovery schema once held and Go's
`regexp` refuses to compile, are refused.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The characters that a backslash before them escapes to the character itself, inside a
# character class and outside one. A backslash before `-` does so inside a class only:
# outside one, ECMA-262 with the `u` flag refuses `\-`.
ESCAPED_PUNCTUATION = "^$\\.*+?()[]{}|/"
# The letters of the escapes for a form feed, a line feed, a carriage return, a tab and a
# vertical tab.
CONTROL_ESCAPES = "fnrtv"
HEX_DIGITS = "0123456789abcdefABCDEF"

# Three patterns the discovery schema once held, each written as its JSON text wrote it,
# which a Python string literal decodes as JSON does, with each form the tests refuse in it
# as (index, text).
FORMER_DISCOVERY_PATTERNS = (
    ("^/(?![/\\\\])", [(2, "(?!")]),
    ("[\\\\\\u0000-\\u0020\\u007f]", [(3, "\\u"), (10, "\\u"), (16, "\\u")]),
    ("[*^|?#\\\\\\u0000-\\u0020\\u007f]", [(8, "\\u"), (15, "\\u"), (21, "\\u")]),
)

# The members of the discovery schema whose patterns held those forms, by the pointer of
# each pattern.
DISCOVERY_POINTERS = (
    "/properties/delegationPath/pattern",
    "/properties/delegationPath/not/pattern",
    "/properties/browserSession/properties/protectedRequests/items/properties/pathPrefix"
    "/not/pattern",
)


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def escape(key):
    """A member name or array index as a JSON pointer reference token (RFC 6901)."""
    return str(key).replace("~", "~0").replace("/", "~1")


def patterns(node, pointer=""):
    """Yield (pointer, pattern) for each member named `pattern` in `node`, at any depth,
    whose value is a string."""
    if isinstance(node, dict):
        if isinstance(node.get("pattern"), str):
            yield f"{pointer}/pattern", node["pattern"]
        children = node.items()
    elif isinstance(node, list):
        children = enumerate(node)
    else:
        return
    for key, child in children:
        yield from patterns(child, f"{pointer}/{escape(key)}")


def schema_patterns():
    """Yield (file name, pointer, pattern) for each pattern of schemas/*.schema.json."""
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        for pointer, pattern in patterns(load(f"schemas/{path.name}")):
            yield path.name, pointer, pattern


def escape_length(pattern, index, in_class):
    """The length of the escape that starts at `index` of `pattern` where the tests allow
    it, and None where they refuse it."""
    letter = pattern[index + 1:index + 2]
    if letter and (letter in ESCAPED_PUNCTUATION or letter in CONTROL_ESCAPES
                   or (in_class and letter == "-")):
        return 2
    digits = pattern[index + 2:index + 4]
    if letter == "x" and len(digits) == 2 and all(digit in HEX_DIGITS for digit in digits):
        return 4
    return None


def refusals(pattern):
    """Each form of `pattern` the tests refuse, as (index, text): a group that opens with
    `(?` other than `(?:`, and an escape that escape_length() refuses."""
    found = []
    index = 0
    members = None  # inside a character class, the index of its first member
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            length = escape_length(pattern, index, members is not None)
            if length is None:
                found.append((index, pattern[index:index + 2]))
                length = 2
            index += length
        elif members is not None:
            if char == "]" and index > members:
                members = None
            index += 1
        elif char == "[":
            index += 2 if pattern.startswith("[^", index) else 1
            members = index
        elif pattern.startswith("(?", index) and not pattern.startswith("(?:", index):
            length = 4 if pattern.startswith("(?<", index) else 3
            found.append((index, pattern[index:index + length]))
            index += 2
        else:
            index += 1
    return found


class WalkTest(unittest.TestCase):
    def test_patterns_yields_each_member_named_pattern_whose_value_is_a_string(self):
        schema = {
            "properties": {
                "a": {"type": "string", "pattern": "^a"},
                "b": {"anyOf": [{"pattern": "^b$"}, {"not": {"pattern": "c"}}]},
                "pattern": {"pattern": "^p"},
            },
            "$defs": {"d/e": {"items": {"pattern": "^e"}}},
        }
        self.assertEqual(list(patterns(schema)), [
            ("/properties/a/pattern", "^a"),
            ("/properties/b/anyOf/0/pattern", "^b$"),
            ("/properties/b/anyOf/1/not/pattern", "c"),
            ("/properties/pattern/pattern", "^p"),
            ("/$defs/d~1e/items/pattern", "^e"),
        ])

    def test_the_walk_finds_the_discovery_schema_patterns_that_held_the_forms(self):
        found = [pointer for name, pointer, _ in schema_patterns()
                 if name == "discovery-v1.schema.json"]
        for pointer in DISCOVERY_POINTERS:
            with self.subTest(pointer=pointer):
                self.assertIn(pointer, found)


class SchemaPatternTest(unittest.TestCase):
    def test_each_schema_pattern_compiles_under_python_re(self):
        for name, pointer, pattern in schema_patterns():
            with self.subTest(schema=name, pointer=pointer):
                re.compile(pattern)

    def test_no_schema_pattern_holds_a_form_the_tests_refuse(self):
        found = [
            f"{name} {pointer} {pattern!r}: {text!r} at index {index}"
            for name, pointer, pattern in schema_patterns()
            for index, text in refusals(pattern)
        ]
        self.assertEqual(found, [])


class RefusalTest(unittest.TestCase):
    def assert_refusals(self, cases):
        for pattern, expected in cases:
            with self.subTest(pattern=pattern):
                self.assertEqual(refusals(pattern), expected)

    def test_the_former_discovery_patterns_are_refused(self):
        self.assert_refusals(FORMER_DISCOVERY_PATTERNS)

    def test_a_group_that_opens_with_a_question_mark_is_refused_unless_non_capturing(self):
        self.assert_refusals((
            ("(?=a)", [(0, "(?=")]),
            ("(?!a)", [(0, "(?!")]),
            ("(?<=a)b", [(0, "(?<=")]),
            ("(?<!a)b", [(0, "(?<!")]),
            ("(?P<n>a)", [(0, "(?P")]),
            ("(?<n>a)", [(0, "(?<n")]),
            ("(?i)a", [(0, "(?i")]),
            ("a(?>b)", [(1, "(?>")]),
            ("(?:a)(?=b)", [(5, "(?=")]),
            ("(?:a)", []),
            ("(a)|(?:b)", []),
        ))

    def test_an_escape_is_refused_unless_the_tests_allow_it(self):
        self.assert_refusals(tuple(
            (pattern, [(0, pattern[:2])])
            for pattern in ("\\u0041", "\\U00000041", "\\d", "\\w", "\\s", "\\b", "\\Z",
                            "\\1", "\\p{L}", "\\x4", "\\x{41}", "\\-", "\\")
        ))
        self.assert_refusals(tuple(
            (pattern, [])
            for pattern in (r"\x00", r"\x7f", r"\x7F", r"\f", r"\n", r"\r", r"\t", r"\v",
                            r"\^\$\\\.\*\+\?\(\)\[\]\{\}\|\/", r"[\-]", r"[\x00-\x20\x7f]")
        ))

    def test_inside_a_character_class_a_group_opening_is_read_as_members(self):
        for pattern in ("[(?!a)]", "[](?!a)]", "[a(?=b]"):
            with self.subTest(pattern=pattern):
                self.assertEqual(refusals(pattern), [])
                for member in pattern[1:-1]:
                    self.assertIsNotNone(re.fullmatch(pattern, member))

    def test_a_form_after_a_character_class_or_inside_one_is_refused(self):
        self.assert_refusals((
            ("[a](?!b)", [(3, "(?!")]),
            ("[]](?!b)", [(3, "(?!")]),
            ("[^]](?!b)", [(4, "(?!")]),
            (r"[\]](?!b)", [(4, "(?!")]),
            ("[\\u0041]", [(1, "\\u")]),
        ))

    def test_an_escaped_backslash_or_parenthesis_opens_no_refused_form(self):
        self.assert_refusals((
            (r"\\u0041", []),
            (r"[\\u]", []),
            (r"\(?!a", []),
        ))


if __name__ == "__main__":
    unittest.main()
