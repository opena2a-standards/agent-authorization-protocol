#!/usr/bin/env python3
"""Tests that a `cnf.jwk` carries only the public key members of a registry key type.

AAP-SPEC Section 4.6 states that a `cnf.jwk` MUST carry only the public key members of
a key type of an active row of the suite registry (Section 9.5), with `kid` and `use`
(`sig`) as the only other members, and that a verifier MUST reject a token whose
`cnf.jwk` carries any other member or names any other key type. The claim schemas
schemas/cgt-claims-v1.schema.json and schemas/da-claims-v1.schema.json state the same
member sets, one `oneOf` branch per key type with `additionalProperties` false.

The schema tests take the claim sets of AAP-SPEC Sections 4.7 and 5.5,
examples/tokens/cgt-v1.fgc.claims.json and examples/tokens/da-v1.fgc.claims.json, which
bind by `jkt`, and validate 16 cells against the schema of each. The first cell is the
claim set unchanged. Each other cell replaces `cnf` by `{"jwk": K}`, where K is built
when the test runs, from the `publicJwk` of a published test key in
examples/tokens/test-keys.json (no other member of that file is read) with one change,
or as a key of another type; a key member a cell adds or makes up holds the literal
FAKE-NOT-A-KEY, which is not a key. No cell is stored in the repository.

ACCEPT: the claim set unchanged; K the `OKP` key of `agent-key-1`; K the `AKP` key of
`broker-pqc-1`. These are the positive controls of the run.

REJECT, each with every error inside `cnf.jwk`: the `OKP` key with the private member
`d`; the `AKP` key with the private member `priv`; a symmetric `oct` key with `k`; an
`EC` `P-256` public key; an `RSA` public key; the `OKP` key with `x5c`; the `OKP` key
with `key_ops`; the `OKP` key with `crv` `X25519`; the `OKP` key without `x`; the `OKP`
key with `use` `enc`; the `AKP` key with `alg` `ML-DSA-44`; `{"kty": "OKP"}` alone; and
`{}`.

The text test reads AAP-SPEC.md: the sentence "MUST carry only the public key members"
appears once, in Section 4.6, and the member set it states for each key type, with each
value it names for a member, is the member set of that key type's branch of `cnf.jwk` in
both claim schemas.

Refs #160

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
SPEC = "AAP-SPEC.md"
TEST_KEYS = "examples/tokens/test-keys.json"
CGT_CLAIMS = "examples/tokens/cgt-v1.fgc.claims.json"
DA_CLAIMS = "examples/tokens/da-v1.fgc.claims.json"
CGT_SCHEMA = "schemas/cgt-claims-v1.schema.json"
DA_SCHEMA = "schemas/da-claims-v1.schema.json"

RULE = "MUST carry only the public key members"
FAKE = "FAKE-NOT-A-KEY"  # a literal that is not a key
OKP_KEY = "agent-key-1"
AKP_KEY = "broker-pqc-1"

# A Markdown heading: its level and its first word ("### 4.6 Proof" is 3, "4.6").
HEADING = re.compile(r"(#{1,6})\s+(\S+)")
# A member name in backquotes, with the value the sentence names for it in parentheses.
MEMBER = re.compile(r"`([^`]+)`(?: \(`([^`]+)`\))?")


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def public_jwk(kid):
    """Return a copy of the `publicJwk` of the published test key `kid`. No other member
    of the key's entry is read."""
    for entry in read_json(TEST_KEYS)["keys"]:
        if entry["kid"] == kid:
            return copy.deepcopy(entry["publicJwk"])
    raise LookupError(f"{TEST_KEYS} holds no key {kid!r}")


def changed(kid, **members):
    """The public key of `kid` with `members` set."""
    key = public_jwk(kid)
    key.update(members)
    return key


def without(kid, member):
    """The public key of `kid` without `member`."""
    key = public_jwk(kid)
    del key[member]
    return key


ACCEPT, REJECT = True, False

# (cell, builder of the `cnf.jwk` value, outcome). The builders run when a test runs, so
# the published keys are read then.
CELLS = (
    ("the OKP key of agent-key-1", lambda: public_jwk(OKP_KEY), ACCEPT),
    ("the AKP key of broker-pqc-1", lambda: public_jwk(AKP_KEY), ACCEPT),
    ("the OKP key with the private member d", lambda: changed(OKP_KEY, d=FAKE), REJECT),
    ("the AKP key with the private member priv", lambda: changed(AKP_KEY, priv=FAKE), REJECT),
    ("a symmetric oct key with k", lambda: {"kty": "oct", "k": FAKE}, REJECT),
    ("an EC P-256 public key",
     lambda: {"kty": "EC", "crv": "P-256", "x": FAKE, "y": FAKE}, REJECT),
    ("an RSA public key", lambda: {"kty": "RSA", "n": FAKE, "e": "AQAB"}, REJECT),
    ("the OKP key with x5c", lambda: changed(OKP_KEY, x5c=[FAKE]), REJECT),
    ("the OKP key with key_ops", lambda: changed(OKP_KEY, key_ops=["verify"]), REJECT),
    ("the OKP key with crv X25519", lambda: changed(OKP_KEY, crv="X25519"), REJECT),
    ("the OKP key without x", lambda: without(OKP_KEY, "x"), REJECT),
    ("the OKP key with use enc", lambda: changed(OKP_KEY, use="enc"), REJECT),
    ("the AKP key with alg ML-DSA-44", lambda: changed(AKP_KEY, alg="ML-DSA-44"), REJECT),
    ("kty OKP alone", lambda: {"kty": "OKP"}, REJECT),
    ("an empty object", lambda: {}, REJECT),
)


def error_paths(validator, instance):
    """The instance path of each error the validator reports for `instance`."""
    return [list(error.absolute_path) for error in validator.iter_errors(instance)]


def section(path, number):
    """The text of section `number` of `path`, from its heading to the next heading of the
    same or a higher level, with each run of white space read as one space."""
    body, level = [], None
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        heading = HEADING.match(line)
        if level is None:
            if heading and heading.group(2).rstrip(".") == number:
                level = len(heading.group(1))
        elif heading and len(heading.group(1)) <= level:
            break
        else:
            body.append(line)
    return " ".join(" ".join(body).split())


def stated_member_sets(sentence):
    """Return {key type: (required members, other members, {member: value})} as the
    sentence states them: the members it names for each key type, the members it names
    as the only other members, and each value it names in parentheses after a member."""
    shared = re.search(r"with (.*?) as the only other members", sentence)
    shared_members = MEMBER.findall(shared.group(1)) if shared else []
    stated = {}
    for kty, clause in re.findall(r"for `([^`]+)`, (.*?)(?:; |\.$)", sentence):
        required_part, _, optional_part = clause.partition(", with ")
        required = MEMBER.findall(required_part)
        others = MEMBER.findall(optional_part) + shared_members
        values = {name: value for name, value in required + others if value}
        values["kty"] = kty
        stated[kty] = ({name for name, _ in required}, {name for name, _ in others}, values)
    return stated


@NEEDS_JSONSCHEMA
class ClaimSchemaCellTest(unittest.TestCase):
    def check_cells(self, claims_path, schema_path):
        claims = read_json(claims_path)
        validator = Draft202012Validator(read_json(schema_path))
        with self.subTest(cell="the claim set unchanged"):
            self.assertIn("jkt", claims["cnf"])
            self.assertEqual(error_paths(validator, claims), [])
        for cell, build, outcome in CELLS:
            with self.subTest(cell=cell):
                instance = copy.deepcopy(claims)
                instance["cnf"] = {"jwk": build()}
                paths = error_paths(validator, instance)
                if outcome is ACCEPT:
                    self.assertEqual(paths, [], f"{schema_path} rejects {cell}")
                else:
                    self.assertNotEqual(paths, [], f"{schema_path} accepts {cell}")
                    for path in paths:
                        self.assertEqual(path[:2], ["cnf", "jwk"])

    def test_each_cell_has_its_outcome_under_the_cgt_claims_schema(self):
        self.check_cells(CGT_CLAIMS, CGT_SCHEMA)

    def test_each_cell_has_its_outcome_under_the_da_claims_schema(self):
        self.check_cells(DA_CLAIMS, DA_SCHEMA)


class SectionTextTest(unittest.TestCase):
    def test_section_4_6_states_the_member_sets_of_both_claim_schemas(self):
        spec = " ".join((ROOT / SPEC).read_text(encoding="utf-8").split())
        self.assertEqual(spec.count(RULE), 1, f"{SPEC} does not state {RULE!r} once")
        text = section(SPEC, "4.6")
        self.assertEqual(text.count(RULE), 1, f"Section 4.6 of {SPEC} does not state the rule")
        sentence = re.search(r"A `cnf\.jwk` " + re.escape(RULE) + r".*?\.(?= |$)", text)
        self.assertIsNotNone(sentence)
        stated = stated_member_sets(sentence.group(0))
        self.assertEqual(set(stated), {"OKP", "AKP"})
        for path in (CGT_SCHEMA, DA_SCHEMA):
            with self.subTest(schema=path):
                jwk = read_json(path)["$defs"]["cnf"]["properties"]["jwk"]
                self.assertEqual(set(jwk["properties"]["kty"]["enum"]), set(stated))
                branches = {branch["properties"]["kty"]["const"]: branch
                            for branch in jwk["oneOf"]}
                self.assertEqual(set(branches), set(stated))
                for kty, (required, others, values) in stated.items():
                    branch = branches[kty]
                    self.assertEqual(set(branch["properties"]), required | others)
                    self.assertEqual(set(branch["required"]), required)
                    self.assertIs(branch["additionalProperties"], False)
                    for member, value in values.items():
                        self.assertEqual(branch["properties"][member].get("const"), value,
                                         f"{path} {kty} {member}")


if __name__ == "__main__":
    unittest.main()
