#!/usr/bin/env python3
"""Tests for the `trust_class` grammar of the CGT and DA claim schemas.

AAP-SPEC section 4.2: `trust_class` is a capability in the grammar of AIP
section 4.1 (a reserved namespace, or a namespace prefixed with the defining
organization's domain, then a colon and an action). Claim schema v1 also
accepts the legacy `namespace:action` form, so a value a deployed broker
mints today stays valid.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import json
import pathlib
import re
import unittest

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise unittest.SkipTest("the 'jsonschema' package is required (pip install jsonschema)")

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The AIP section 4.1 capability grammar, copied from that section.
AIP_GRAMMAR = r"^(?:[a-z0-9-]+(?:\.[a-z0-9-]+)+/)?[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$"
# The pattern claim schema v1 carried before it adopted the AIP grammar.
LEGACY = r"^[a-z0-9_-]+:[a-z0-9_-]+$"

DOMAIN_PREFIXED = "acme.com/orders:read"

ACCEPTED = [
    DOMAIN_PREFIXED,
    "acme.com/billing:charge",
    "acme.com/internal:deploy",
    "eu.acme.co.uk/ledger:write",
    "acme-corp.example/orders:read",
    "file:read",
    "db:read",
    "mcp:tool_use",
    "data:pii_access",
]

# A bare namespace that AIP section 4.2 does not reserve is not an AIP
# capability, but the legacy v1 form admits it and deployed brokers mint it.
LEGACY_ONLY = [
    "orders:read",
    "orders-db:read-only",
    "1orders:read",
]

REJECTED = [
    "",
    "orders",
    "orders.read",
    "orders:",
    ":read",
    "orders:read:write",
    "orders:*",
    "Orders:read",
    "Acme.com/orders:read",
    "acme/orders:read",
    "acme.com/orders",
    "acme.com/:read",
    "acme.com/orders:*",
    "acme.com/orders-db:read",
    "acme.com/1orders:read",
    "acme.com//orders:read",
    "/orders:read",
    ".com/orders:read",
    "acme.com/orders:read ",
]

SCHEMAS = {
    "cgt": ("schemas/cgt-claims-v1.schema.json", "examples/tokens/cgt-v1.claims.json"),
    "da": ("schemas/da-claims-v1.schema.json", "examples/tokens/da-v1.claims.json"),
}

# Every committed claim set that carries `trust_class`.
CLAIM_FIXTURES = {
    "cgt-v1.claims.json": "cgt",
    "cgt-v1.mldsa65.claims.json": "cgt",
    "cgt-v1.fgc.claims.json": "cgt",
    "da-v1.claims.json": "da",
    "da-v1.fgc.claims.json": "da",
}


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class TrustClassSchemaTest(unittest.TestCase):
    def setUp(self):
        self.validators = {}
        self.claims = {}
        for kind, (schema, example) in SCHEMAS.items():
            self.validators[kind] = Draft202012Validator(load(schema))
            self.claims[kind] = load(example)

    def errors(self, kind, value):
        claims = dict(self.claims[kind], trust_class=value)
        return [e.message for e in self.validators[kind].iter_errors(claims)]

    def test_domain_prefixed_and_reserved_capabilities_are_accepted(self):
        for kind in SCHEMAS:
            for value in ACCEPTED:
                with self.subTest(schema=kind, trust_class=value):
                    self.assertEqual(self.errors(kind, value), [])

    def test_unreserved_bare_namespace_is_accepted_as_the_legacy_v1_form(self):
        for kind in SCHEMAS:
            for value in LEGACY_ONLY:
                with self.subTest(schema=kind, trust_class=value):
                    self.assertEqual(self.errors(kind, value), [])

    def test_values_outside_both_forms_are_rejected(self):
        for kind in SCHEMAS:
            for value in REJECTED:
                with self.subTest(schema=kind, trust_class=value):
                    self.assertNotEqual(self.errors(kind, value), [])

    def test_schema_accepts_exactly_the_union_of_the_aip_grammar_and_the_legacy_form(self):
        aip, legacy = re.compile(AIP_GRAMMAR), re.compile(LEGACY)
        for kind in SCHEMAS:
            for value in ACCEPTED + LEGACY_ONLY + REJECTED:
                want = bool(aip.fullmatch(value) or legacy.fullmatch(value))
                with self.subTest(schema=kind, trust_class=value):
                    self.assertEqual(self.errors(kind, value) == [], want)

    def test_cgt_and_da_schemas_define_trust_class_identically(self):
        cgt = load(SCHEMAS["cgt"][0])["properties"]["trust_class"]
        da = load(SCHEMAS["da"][0])["properties"]["trust_class"]
        self.assertEqual(cgt, da)


class TrustClassExamplesTest(unittest.TestCase):
    def test_committed_claim_sets_carry_the_domain_prefixed_class(self):
        for name, kind in CLAIM_FIXTURES.items():
            with self.subTest(fixture=name):
                claims = load(f"examples/tokens/{name}")
                self.assertEqual(claims["trust_class"], DOMAIN_PREFIXED)
                errors = list(Draft202012Validator(load(SCHEMAS[kind][0])).iter_errors(claims))
                self.assertEqual([e.message for e in errors], [])

    def test_every_specification_example_carries_the_domain_prefixed_class(self):
        spec = (ROOT / "AAP-SPEC.md").read_text(encoding="utf-8")
        values = re.findall(r'"trust_class": "([^"]*)"', spec)
        self.assertGreater(len(values), 0)
        self.assertEqual(set(values), {DOMAIN_PREFIXED})


if __name__ == "__main__":
    unittest.main()
