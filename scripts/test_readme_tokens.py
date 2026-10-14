#!/usr/bin/env python3
"""Tests that the use cases say which published tokens the aap-conformance verifiers accept.

README.md and docs/use-cases.md point readers to the aap-conformance suite to
check the token bytes in examples/tokens/. The suite's Node and Python
verifiers, at the commit they name, match `trust_class` against the legacy
`namespace:action` pattern alone, so they accept a token that carries no
`trust_class` or one in that form and reject a token that carries the
domain-prefixed class AAP-SPEC Section 4.2 says a broker should mint. The tests
read each token's payload and check that README.md and docs/use-cases.md name
the tokens the verifiers accept, and that docs/use-cases.md, which carries the
use cases in full, names the tokens they reject, so a regenerated token that
moves from one side to the other fails until the text is changed with it.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import base64
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "examples" / "tokens"
README = "README.md"
# The use cases in full; the README carries a short form of each.
USE_CASES = "docs/use-cases.md"

# The aap-conformance commit whose verifiers README.md and docs/use-cases.md describe.
SUITE_COMMIT = "99e213a"
# The `trust_class` pattern those verifiers match.
LEGACY = r"^[a-z0-9_-]+:[a-z0-9_-]+$"
DOMAIN_PREFIXED = "acme.com/orders:read"


def b64url_json(segment):
    return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))


def payload(path):
    text = path.read_text(encoding="utf-8")
    if path.name.endswith(".jwt"):
        return b64url_json(text.strip().split(".")[1])
    return b64url_json(json.loads(text)["payload"])


def published_tokens():
    """Each token in examples/tokens/, compact or JWS JSON, and its `trust_class` (None if absent)."""
    return {
        path.name: payload(path).get("trust_class")
        for path in sorted(TOKENS.iterdir())
        if path.name.endswith(".jwt") or path.name.endswith(".general.json")
    }


def paragraph(opening, document):
    """The paragraphs of `document` that start with `opening` and link examples/tokens/."""
    text = (ROOT / document).read_text(encoding="utf-8")
    return [p for p in text.split("\n\n") if p.startswith(opening) and "examples/tokens/" in p]


class ReadmeTokenStatementTest(unittest.TestCase):
    def setUp(self):
        self.tokens = published_tokens()
        legacy = re.compile(LEGACY)
        self.accepted = {n for n, tc in self.tokens.items() if tc is None or legacy.fullmatch(tc)}
        self.rejected = set(self.tokens) - self.accepted

    def named_tokens(self, text):
        return set(re.findall(r"`([^`]+)`", text)) & set(self.tokens)

    def test_both_sides_are_populated(self):
        self.assertEqual(len(self.tokens), 10)
        self.assertEqual(self.accepted, {"ait-v1.jwt", "bac-v1.jwt", "bac-v1.session.jwt"})
        self.assertEqual({self.tokens[n] for n in self.rejected}, {DOMAIN_PREFIXED})

    def test_readme_names_the_tokens_the_suite_accepts(self):
        for document in (README, USE_CASES):
            with self.subTest(document=document):
                found = paragraph("What you can do today:", document)
                self.assertEqual(len(found), 1)
                self.assertIn(f"`{SUITE_COMMIT}`", found[0])
                self.assertEqual(self.named_tokens(found[0]), self.accepted)

    def test_readme_names_the_tokens_the_suite_rejects_and_the_pattern_it_matches(self):
        found = paragraph("Where it stops today:", USE_CASES)
        self.assertEqual(len(found), 1)
        self.assertIn(f"`{SUITE_COMMIT}`", found[0])
        self.assertIn(f"`{LEGACY}`", found[0])
        self.assertIn(f"`{DOMAIN_PREFIXED}`", found[0])
        self.assertIn("conformance.json", found[0])
        self.assertEqual(self.named_tokens(found[0]), self.rejected)

    def test_readme_states_the_pattern_limit_and_links_the_token_list(self):
        readme = (ROOT / README).read_text(encoding="utf-8")
        found = [p for p in readme.split("\n\n")
                 if p.startswith("Where it stops today:") and f"`{LEGACY}`" in p]
        self.assertEqual(len(found), 1)
        self.assertIn(f"`{SUITE_COMMIT}`", found[0])
        self.assertIn(f"]({'./' + USE_CASES}#", found[0])

    def test_readme_does_not_call_every_published_token_valid(self):
        for document in (README, USE_CASES):
            with self.subTest(document=document):
                text = (ROOT / document).read_text(encoding="utf-8")
                self.assertFalse("valid token bytes" in text, f'{document} calls examples/tokens/ "the valid token bytes"')


if __name__ == "__main__":
    unittest.main()
