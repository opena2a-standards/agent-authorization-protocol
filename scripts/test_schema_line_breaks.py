#!/usr/bin/env python3
"""Tests that no schema pattern ending with `$` admits a value followed by a line break.

JSON Schema names ECMA-262 as the dialect of `pattern`, in which `$` matches only at
the end of the value. The jsonschema package evaluates `pattern` with Python's
`re.search`, in which `$` also matches before a final line break, so a pattern that ends
with `$` admits there a well-formed value followed by one. In schemas/, each such pattern
sits beside a `not` keyword with the pattern `\\n`, or, for the two patterns of
`trust_class`, in an `anyOf` beside one (scripts/test_trust_class_grammar.py tests that
grammar).

FIELDS lists each member whose subschema holds a pattern that ends with `$`, with a
published example that holds a well-formed value of it. For each member the tests append
a line break to that value and check that the schema rejects the example at that member,
and check that the schema accepts the value, the value followed by a line break or by a
carriage return and a line break, and the value preceded by a line break where ECMA-262
matches it and only there. They read the final `$` of a pattern as ECMA-262 does by putting
Python's `\\Z`, which matches only at the end of the value, in its place. A schema that holds
a pattern ending with `$` at a member FIELDS does not list fails the tests, as does an
entry of FIELDS at which the schema holds none. The tests read the `pattern` keyword
only.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import copy
import json
import pathlib
import re
import unittest

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None

# A test that validates against a schema is skipped where the package is missing.
# The file still loads, so it runs when it is named by path.
NEEDS_JSONSCHEMA = unittest.skipUnless(
    Draft202012Validator, "the 'jsonschema' package is required (pip install jsonschema)")

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Each member whose subschema holds a pattern that ends with `$`: the schema in schemas/,
# the JSON pointer of the member's subschema in it, the example in examples/tokens/ that
# holds the member (None for the first value of the schema's own `examples`), and the
# member's path in that example.
FIELDS = (
    ("ait-claims-v1.schema.json", "/properties/atx_reference",
     "ait-v1.claims.json", ("atx_reference",)),
    ("ait-claims-v1.schema.json", "/properties/jti", "ait-v1.claims.json", ("jti",)),
    ("bac-claims-v1.schema.json", "/properties/atx_reference",
     "bac-v1.claims.json", ("atx_reference",)),
    ("bac-claims-v1.schema.json", "/properties/binary_hash",
     "bac-v1.claims.json", ("binary_hash",)),
    ("bac-claims-v1.schema.json", "/properties/jti", "bac-v1.claims.json", ("jti",)),
    ("cgt-claims-v1.schema.json", "/properties/trust_class",
     "cgt-v1.fgc.claims.json", ("trust_class",)),
    ("cgt-claims-v1.schema.json", "/properties/jti", "cgt-v1.fgc.claims.json", ("jti",)),
    ("cgt-claims-v1.schema.json", "/$defs/authorizationDetails/items/properties/type",
     "cgt-v1.fgc.claims.json", ("authorization_details", 0, "type")),
    ("cgt-claims-v1.schema.json", "/$defs/cnf/properties/jkt",
     "cgt-v1.fgc.claims.json", ("cnf", "jkt")),
    ("da-claims-v1.schema.json", "/properties/trust_class",
     "da-v1.fgc.claims.json", ("trust_class",)),
    ("da-claims-v1.schema.json", "/properties/delegator_atx",
     "da-v1.fgc.claims.json", ("delegator_atx",)),
    ("da-claims-v1.schema.json", "/properties/jti", "da-v1.fgc.claims.json", ("jti",)),
    ("da-claims-v1.schema.json", "/$defs/authorizationDetails/items/properties/type",
     "da-v1.fgc.claims.json", ("authorization_details", 0, "type")),
    ("da-claims-v1.schema.json", "/$defs/cnf/properties/jkt",
     "da-v1.fgc.claims.json", ("cnf", "jkt")),
    ("grant-reference-v1.schema.json", "", None, ()),
    ("jws-general-v1.schema.json", "/properties/payload", "cgt-v1.general.json", ("payload",)),
    ("jws-general-v1.schema.json", "/properties/signatures/items/properties/protected",
     "cgt-v1.general.json", ("signatures", 0, "protected")),
    ("jws-general-v1.schema.json", "/properties/signatures/items/properties/signature",
     "cgt-v1.general.json", ("signatures", 0, "signature")),
)

# A line break added to a well-formed value, as (before, after). Without the `not` keyword,
# the jsonschema package and ECMA-262 disagree on the first and agree on the other two.
LINE_BREAKS = (("", "\n"), ("", "\r\n"), ("\n", ""))


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def escape(key):
    """A member name or array index as a JSON pointer reference token (RFC 6901)."""
    return str(key).replace("~", "~0").replace("/", "~1")


def dollar_anchored(node, pointer=""):
    """Yield the JSON pointer of each object in `node` whose `pattern` is a string that ends
    with `$`."""
    if isinstance(node, dict):
        if isinstance(node.get("pattern"), str) and node["pattern"].endswith("$"):
            yield pointer
        children = node.items()
    elif isinstance(node, list):
        children = enumerate(node)
    else:
        return
    for key, child in children:
        yield from dollar_anchored(child, f"{pointer}/{escape(key)}")


def member(pointer):
    """The pointer of the member a pattern belongs to: a branch of an `anyOf` belongs to the
    subschema that holds the `anyOf`."""
    return re.sub(r"/anyOf/\d+$", "", pointer)


def resolve(document, pointer):
    """The value a JSON pointer names in `document`."""
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def patterns(subschema):
    """The patterns of a member's subschema: its own, or that of each branch of its `anyOf`."""
    if "pattern" in subschema:
        return [subschema["pattern"]]
    return [branch["pattern"] for branch in subschema["anyOf"]]


def ecma_262_matches(pattern, value):
    """True if `value` matches `pattern`, which ends with `$`, with that `$` read as ECMA-262
    reads it: Python's `\\Z`, which matches only at the end of the value, takes its place."""
    return re.search(pattern[:-1] + r"\Z", value) is not None


def value_at(document, path):
    """The value at `path`, a sequence of member names and array indexes, in `document`."""
    for step in path:
        document = document[step]
    return document


def replaced(document, path, value):
    """A copy of `document` with `value` at `path`; `value` itself where `path` is empty."""
    if not path:
        return value
    document = copy.deepcopy(document)
    value_at(document, path[:-1])[path[-1]] = value
    return document


def example(schema, name):
    """The example `name` in examples/tokens/, or the first value of the schema's own
    `examples` where `name` is None."""
    return load(f"examples/tokens/{name}") if name else schema["examples"][0]


class ListedMembersTest(unittest.TestCase):
    def test_dollar_anchored_finds_each_pattern_that_ends_with_a_dollar_anchor(self):
        schema = {
            "properties": {
                "a": {"type": "string", "pattern": "^a$"},
                "b": {"anyOf": [{"pattern": "^b$"}, {"pattern": "^c"}]},
                "pattern": {"pattern": "^p$"},
                "prefix": {"pattern": "^did:"},
                "not_anchored": {"not": {"pattern": "\\n"}},
            },
            "$defs": {"d/e": {"items": {"pattern": "^e$"}}},
        }
        found = list(dollar_anchored(schema))
        self.assertEqual(found, [
            "/properties/a",
            "/properties/b/anyOf/0",
            "/properties/pattern",
            "/$defs/d~1e/items",
        ])
        self.assertEqual([member(p) for p in found], [
            "/properties/a",
            "/properties/b",
            "/properties/pattern",
            "/$defs/d~1e/items",
        ])
        self.assertEqual(resolve(schema, "/$defs/d~1e/items"), {"pattern": "^e$"})

    def test_fields_lists_each_member_whose_pattern_ends_with_a_dollar_anchor(self):
        found = {}
        for path in sorted((ROOT / "schemas").glob("*.schema.json")):
            for pointer in dollar_anchored(load(f"schemas/{path.name}")):
                found.setdefault(path.name, set()).add(member(pointer))
        listed = {}
        for name, pointer, _, _ in FIELDS:
            listed.setdefault(name, set()).add(pointer)
        self.assertEqual(len(FIELDS), sum(len(pointers) for pointers in listed.values()))
        self.assertEqual(found, listed)


@NEEDS_JSONSCHEMA
class LineBreakTest(unittest.TestCase):
    def test_a_value_followed_by_a_line_break_is_rejected_at_its_member(self):
        for name, pointer, source, path in FIELDS:
            schema = load(f"schemas/{name}")
            validator = Draft202012Validator(schema)
            document = example(schema, source)
            broken = replaced(document, path, value_at(document, path) + "\n")
            with self.subTest(schema=name, member=pointer):
                self.assertEqual([e.message for e in validator.iter_errors(document)], [])
                errors = list(validator.iter_errors(broken))
                self.assertNotEqual(errors, [])
                self.assertEqual({tuple(e.absolute_path) for e in errors}, {path})

    def test_the_schema_accepts_a_value_where_ecma_262_matches_it_and_only_there(self):
        for name, pointer, source, path in FIELDS:
            schema = load(f"schemas/{name}")
            validator = Draft202012Validator(schema)
            document = example(schema, source)
            value = value_at(document, path)
            member_patterns = patterns(resolve(schema, pointer))
            for candidate in [value] + [before + value + after for before, after in LINE_BREAKS]:
                want = any(ecma_262_matches(p, candidate) for p in member_patterns)
                with self.subTest(schema=name, member=pointer, value=candidate):
                    self.assertEqual(want, candidate == value)
                    self.assertEqual(validator.is_valid(replaced(document, path, candidate)), want)


if __name__ == "__main__":
    unittest.main()
