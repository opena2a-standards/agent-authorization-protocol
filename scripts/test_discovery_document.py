#!/usr/bin/env python3
"""Tests for the discovery document: its location, its schema and the browser session member.

Broker profile Section 8.5 has a broker publish a discovery document on the operator's
own origin. Section 8.5.1 names its location, `/.well-known/aap`, and its schema,
schemas/discovery-v1.schema.json, whose first example is the example of that section.
Section 8.5.2 defines the `browserSession` member, which a browser-side consumer reads to
hold an agent's requests in a customer's signed-in session. AAP-SPEC Section 10 requests
the `aap` suffix in the Well-Known URIs registry, and broker profile Section 10 lists the
location and the member in the extensible edge and not in the mandatory core.

The schema tests validate the documents of CASES, each built from one of the schema's
two examples with at most one change, and check each outcome: ACCEPT for a document with
the broker members and `browserSession`, a document with `browserSession` alone, a
document with the broker members alone and a document with an unknown member at each
level; REJECT for a `delegationPath` that a URL parser can resolve to another origin
(`//other.example/x`, an absolute URL, a backslash, a tab), a `pathPrefix` holding a
character the member excludes, a `method` other than POST, PUT, PATCH and DELETE, 65
entries, a broker member without the other four, and the other cases CASES lists. A
further test checks that each string a consumer reads is bounded by `const`, `enum` or
`pattern`, so the member and the two top-level members it reads carry no free text.

The text tests read AAP-BROKER-PROFILE.md and AAP-SPEC.md: Section 8.5 names the
location on the operator's own origin; Section 8.5.1 names the schema and each of its
top-level members; Section 8.5.2 names each method and category the schema allows, and
its paragraph on the floor names each method; the AAP-SPEC Section 10 registration
names the suffix and RFC 8615; and Section 10 of the broker profile lists the location
and the member under the extensible edge only.

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
PROFILE = "AAP-BROKER-PROFILE.md"
SPEC = "AAP-SPEC.md"
SCHEMA = "schemas/discovery-v1.schema.json"
EXAMPLES_MAP = "schemas/examples-map.json"
LOCATION = "`/.well-known/aap`"

BROKER_MEMBERS = ("aapVersions", "signatureSuites", "authorizationDetailsTypes",
                  "presentationBindings", "jwks")

# A numbered Markdown heading: its level and its number ("#### 8.5.1 Title" is 4, "8.5.1").
HEADING = re.compile(r"(#{1,6})\s+(\d+(?:\.\d+)*)\.?\s")
CODE_SPAN = re.compile(r"`([^`]+)`")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def schema():
    return json.loads(read(SCHEMA))


def section(text, number):
    """The text of a numbered section, from its heading to the next heading of the same or a
    higher level."""
    lines = text.splitlines()
    start = level = None
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match is None:
            continue
        if start is None:
            if match.group(2) == number:
                start, level = index, len(match.group(1))
        elif len(match.group(1)) <= level:
            return "\n".join(lines[start:index])
    if start is None:
        raise AssertionError(f"no section {number}")
    return "\n".join(lines[start:])


def blocks(text):
    """The paragraphs and list items of a text, each with its whitespace collapsed."""
    parts = []
    for paragraph in text.split("\n\n"):
        parts.extend(re.split(r"\n(?=\s*(?:\d+\.|[-*])\s)", paragraph))
    return [" ".join(part.split()) for part in parts]


def first_json_block(text):
    """The first fenced ```json block of a text, parsed."""
    match = re.search(r"^```json\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError("no ```json block")
    return json.loads(match.group(1))


def full():
    """The schema's first example: the broker members, the two top-level members a
    consumer reads, and `browserSession`."""
    return copy.deepcopy(schema()["examples"][0])


def browser_only():
    """The schema's second example: `browserSession` alone."""
    return copy.deepcopy(schema()["examples"][1])


def changed(document, change):
    """A copy of the document with `change` applied to it."""
    document = copy.deepcopy(document)
    change(document)
    return document


def entries(document):
    return document["browserSession"]["protectedRequests"]


def entry_with(**members):
    """A change that sets members of the first entry of `protectedRequests`."""
    return lambda document: entries(document)[0].update(members)


def entry_count(n):
    """A change that gives `protectedRequests` n entries, each a copy of the first."""
    def change(document):
        first = entries(document)[0]
        document["browserSession"]["protectedRequests"] = [dict(first) for _ in range(n)]
    return change


def top_level(**members):
    return lambda document: document.update(members)


def without(*names):
    def change(document):
        for name in names:
            document.pop(name)
    return change


def browser_session(**members):
    return lambda document: document["browserSession"].update(members)


def first_key(**members):
    return lambda document: document["jwks"]["keys"][0].update(members)


ACCEPT, REJECT = True, False

# (case, document builder, outcome). The builders are called after the schema is read,
# so a missing schema fails the test that reads it instead of this module's import.
CASES = (
    ("the broker members and browserSession", full, ACCEPT),
    ("browserSession alone", browser_only, ACCEPT),
    ("the broker members alone", lambda: changed(full(), without("browserSession")), ACCEPT),
    ("an unknown top-level member",
     lambda: changed(full(), top_level(laterMember={"any": ["value"]})), ACCEPT),
    ("an unknown member in browserSession",
     lambda: changed(browser_only(), browser_session(laterMember=1)), ACCEPT),
    ("an unknown member in an entry",
     lambda: changed(browser_only(), entry_with(laterMember="x")), ACCEPT),
    ("64 entries", lambda: changed(browser_only(), entry_count(64)), ACCEPT),
    ("a pathPrefix of 255 characters",
     lambda: changed(browser_only(), entry_with(pathPrefix="/" + "a" * 254)), ACCEPT),
    ("the pathPrefix /", lambda: changed(browser_only(), entry_with(pathPrefix="/")), ACCEPT),
    ("method PUT", lambda: changed(browser_only(), entry_with(method="PUT")), ACCEPT),
    ("method PATCH", lambda: changed(browser_only(), entry_with(method="PATCH")), ACCEPT),
    ("method DELETE", lambda: changed(browser_only(), entry_with(method="DELETE")), ACCEPT),
    ("delegationPath //other.example/x",
     lambda: changed(full(), top_level(delegationPath="//other.example/x")), REJECT),
    ("delegationPath as an absolute URL",
     lambda: changed(full(), top_level(delegationPath="https://other.example/x")), REJECT),
    ("delegationPath with a backslash",
     lambda: changed(full(), top_level(delegationPath="/\\other.example/x")), REJECT),
    ("delegationPath with a tab",
     lambda: changed(full(), top_level(delegationPath="/\t/other.example/x")), REJECT),
    ("delegationPath without a leading slash",
     lambda: changed(full(), top_level(delegationPath="agents/delegate")), REJECT),
    *(
        (f"a pathPrefix containing {char!r}",
         (lambda c: lambda: changed(browser_only(), entry_with(pathPrefix=f"/api{c}x")))(char),
         REJECT)
        for char in ("*", "^", "|", "?", "#", "\\", " ", "\n", "\t")
    ),
    ("a pathPrefix without a leading slash",
     lambda: changed(browser_only(), entry_with(pathPrefix="api/transfers")), REJECT),
    ("a pathPrefix of 256 characters",
     lambda: changed(browser_only(), entry_with(pathPrefix="/" + "a" * 255)), REJECT),
    ("method GET", lambda: changed(browser_only(), entry_with(method="GET")), REJECT),
    ("method post, in lowercase",
     lambda: changed(browser_only(), entry_with(method="post")), REJECT),
    ("65 entries", lambda: changed(browser_only(), entry_count(65)), REJECT),
    ("no entry", lambda: changed(browser_only(), entry_count(0)), REJECT),
    ("an entry without a category",
     lambda: changed(browser_only(), lambda d: entries(d)[0].pop("category")), REJECT),
    ("a category the member does not list",
     lambda: changed(browser_only(), entry_with(category="other")), REJECT),
    ("profile 2", lambda: changed(browser_only(), browser_session(profile="2")), REJECT),
    ("profile 1 as a number",
     lambda: changed(browser_only(), browser_session(profile=1)), REJECT),
    ("browserSession as a string",
     lambda: changed(browser_only(), top_level(browserSession="hold payments")), REJECT),
    ("an empty document", lambda: {}, REJECT),
    ("aapVersions without the other broker members",
     lambda: {"aapVersions": [1]}, REJECT),
    ("the broker members without jwks",
     lambda: changed(full(), without("jwks", "browserSession")), REJECT),
    ("an accepted issuer given as a web address",
     lambda: changed(full(), top_level(acceptedIssuers=["https://issuer.example"])), REJECT),
    ("an accepted issuer given as a name",
     lambda: changed(full(), top_level(acceptedIssuers=["Example Issuer"])), REJECT),
    ("an accepted issuer given as a DID URL with a fragment",
     lambda: changed(full(), top_level(acceptedIssuers=["did:example:abc#key-1"])), REJECT),
    ("a key with the private member d",
     lambda: changed(full(), first_key(d="FAKE-NOT-A-KEY")), REJECT),
    ("a key without kid", lambda: changed(full(), lambda d: d["jwks"]["keys"][0].pop("kid")),
     REJECT),
    ("an entry type outside the registry",
     lambda: changed(full(), top_level(authorizationDetailsTypes=["mcp_tool"])), REJECT),
)


def consumer_strings(node, pointer=""):
    """Yield (pointer, subschema) for each subschema in `node` that types a value as a
    string or bounds it by `const` or `enum`."""
    if isinstance(node, dict):
        if node.get("type") == "string" or "const" in node or "enum" in node:
            yield pointer, node
        for key, child in node.items():
            yield from consumer_strings(child, f"{pointer}/{key}")
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from consumer_strings(child, f"{pointer}/{index}")


@NEEDS_JSONSCHEMA
class SchemaTest(unittest.TestCase):
    def test_the_schema_is_a_draft_2020_12_schema(self):
        Draft202012Validator.check_schema(schema())

    def test_each_document_has_its_outcome(self):
        validator = Draft202012Validator(schema())
        for case, build, outcome in CASES:
            with self.subTest(case=case):
                errors = [e.message for e in validator.iter_errors(build())]
                if outcome is ACCEPT:
                    self.assertEqual(errors, [])
                else:
                    self.assertNotEqual(errors, [])

    def test_the_cases_cover_the_eight_named_outcomes(self):
        # The eight documents with a named outcome: two ACCEPT, five REJECT on the
        # member or the path, one ACCEPT with an unknown member.
        named = {
            "the broker members and browserSession": ACCEPT,
            "browserSession alone": ACCEPT,
            "delegationPath //other.example/x": REJECT,
            "delegationPath as an absolute URL": REJECT,
            "a pathPrefix containing '*'": REJECT,
            "method GET": REJECT,
            "65 entries": REJECT,
            "an unknown top-level member": ACCEPT,
        }
        outcomes = {case: outcome for case, _, outcome in CASES}
        for case, outcome in named.items():
            with self.subTest(case=case):
                self.assertEqual(outcomes.get(case), outcome)

    def test_each_string_a_consumer_reads_is_bounded(self):
        properties = schema()["properties"]
        for member in ("browserSession", "delegationPath", "acceptedIssuers"):
            found = list(consumer_strings(properties[member], f"/properties/{member}"))
            self.assertNotEqual(found, [], member)
            for pointer, subschema in found:
                with self.subTest(pointer=pointer):
                    self.assertTrue(
                        {"const", "enum", "pattern"} & subschema.keys(),
                        f"{pointer} admits free text")


class TextTest(unittest.TestCase):
    def test_section_8_5_names_the_location_on_the_operators_own_origin(self):
        text = " ".join(section(read(PROFILE), "8.5").split())
        self.assertIn(f"at {LOCATION} on the **operator's own origin**", text)

    def test_section_8_5_1_names_the_schema_and_each_top_level_member(self):
        text = section(read(PROFILE), "8.5.1")
        self.assertIn(LOCATION, text)
        self.assertIn(f"`{SCHEMA}`", text)
        spans = set(CODE_SPAN.findall(text))
        for member in schema()["properties"]:
            with self.subTest(member=member):
                self.assertIn(member, spans)

    def test_the_example_of_section_8_5_1_is_the_first_example_of_the_schema(self):
        self.assertEqual(first_json_block(section(read(PROFILE), "8.5.1")),
                         schema()["examples"][0])
        mapped = [entry for entry in json.loads(read(EXAMPLES_MAP))
                  if entry["schema"] == SCHEMA]
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["file"], PROFILE)
        heading = HEADING.match(mapped[0]["heading"])
        self.assertIsNotNone(heading, mapped[0]["heading"])
        self.assertEqual(heading.group(2), "8.5.1")

    def test_section_8_5_2_names_each_method_and_category_the_schema_allows(self):
        spans = set(CODE_SPAN.findall(section(read(PROFILE), "8.5.2")))
        entry = schema()["properties"]["browserSession"]["properties"][
            "protectedRequests"]["items"]["properties"]
        for member in ("method", "category"):
            for value in entry[member]["enum"]:
                with self.subTest(member=member, value=value):
                    self.assertIn(value, spans)

    def test_the_floor_holds_each_method_the_member_can_name(self):
        floor = [block for block in blocks(section(read(PROFILE), "8.5.2")) if "the floor" in block]
        self.assertTrue(floor, "Section 8.5.2 has no paragraph or list item on the floor")
        methods = schema()["properties"]["browserSession"]["properties"][
            "protectedRequests"]["items"]["properties"]["method"]["enum"]
        self.assertEqual(sorted(methods), ["DELETE", "PATCH", "POST", "PUT"])
        for method in methods:
            with self.subTest(method=method):
                self.assertIn(method, floor[0])

    def test_aap_spec_section_10_requests_the_aap_well_known_suffix(self):
        text = " ".join(section(read(SPEC), "10").split())
        self.assertIn("Well-Known URIs registry", text)
        self.assertIn("RFC 8615", text)
        self.assertIn("URI suffix: `aap`", text)
        self.assertIn("broker profile Section 8.5.1", text)

    def test_the_extensible_edge_lists_the_location_and_the_member_and_the_core_does_not(self):
        text = " ".join(section(read(PROFILE), "10").split())
        core = text[text.index("**Mandatory core"):text.index("**Extensible edge")]
        edge = text[text.index("**Extensible edge"):]
        for name in (LOCATION, "`browserSession`"):
            with self.subTest(name=name):
                self.assertIn(name, edge)
                self.assertNotIn(name, core)


if __name__ == "__main__":
    unittest.main()
