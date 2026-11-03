#!/usr/bin/env python3
"""Tests that the specification states one rule for the session label across a hop.

AAP-SPEC Section 4.4.2 says the session label is per broker: no token or message
carries an accumulated session label across a `peer_agent` hop, and the receiving
broker's session label is the union of what that broker admits. Broker profile
Section 6.10, Rule 2, defines the session label as the union of the label sets of
every field the broker has admitted. A sentence about the BAC that lets a receiver
add the BAC `session_label` to its own session label contradicts both: the
receiver's session label would then hold labels it never admitted, and the BAC
would be the carrier that Section 4.4.2 says this revision does not define.

Run: python3 -m unittest discover -s scripts -p 'test_session_label_per_broker.py'
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "AAP-SPEC.md"
PROFILE = ROOT / "AAP-BROKER-PROFILE.md"
DOCUMENTS = (SPEC, PROFILE)

# A BCP 14 keyword that grants or requires (a negated keyword forbids, so it is
# skipped), then a verb that puts labels into a set, then a receiver's own
# session label, all inside one clause.
PERMITS_ADDING = re.compile(
    r"\b(?:MAY|SHOULD|MUST|SHALL|REQUIRED|RECOMMENDED|OPTIONAL)\b(?! NOT\b)"
    r"[^.;:]*?\b(?:add|adds|merge|merges|union|unions|fold|folds|take|takes|"
    r"import|imports|include|includes|copy|copies)\b"
    r"[^.;:]*?\b(?:its own|its|their own|their|the receiver's|"
    r"the receiving broker's) session labels?\b"
)
# A sentence about the BAC names the token or its claim.
NAMES_BAC = re.compile(r"\bBAC\b|`session_label`")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*(])")
# A line that opens a new block: a heading, a list item or a table row.
BLOCK_START = re.compile(r"^\s*(?:#|[-*] |\d+\. |\|)")


def sentences(path):
    """Return the sentences of a document, never joining two paragraphs, items or rows."""
    blocks, block = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or BLOCK_START.match(line):
            if block:
                blocks.append(" ".join(" ".join(block).split()))
            block = [line] if line.strip() else []
        else:
            block.append(line)
    if block:
        blocks.append(" ".join(" ".join(block).split()))
    return [sentence for text in blocks for sentence in SENTENCE_END.split(text)]


def section(path, heading):
    """Return the normalized text of the section under a heading, up to the next heading."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(heading)
    body = []
    for line in lines[start + 1:]:
        if line.startswith("#"):
            break
        body.append(line)
    return " ".join(" ".join(body).split())


def bac_sentences_that_add(candidates):
    """Return each sentence that names the BAC and lets a receiver add to its session label."""
    return [
        sentence
        for sentence in candidates
        if NAMES_BAC.search(sentence) and PERMITS_ADDING.search(sentence)
    ]


class SessionLabelPerBrokerTest(unittest.TestCase):
    def test_section_4_4_2_keeps_the_session_label_per_broker(self):
        text = section(SPEC, "#### 4.4.2 Label semantics")
        self.assertIn(
            "no token or message carries an accumulated session label across a "
            "`peer_agent` hop",
            text,
        )
        self.assertIn(
            "the receiving broker's session label is the union of what that broker admits",
            text,
        )

    def test_rule_2_defines_the_session_label_by_what_the_broker_admitted(self):
        text = section(PROFILE, "### 6.10 Data clearance rules")
        self.assertIn(
            "the union of the label sets of every field it has admitted into the agent "
            "context: the **session label**",
            text,
        )

    def test_no_bac_sentence_lets_a_receiver_add_to_its_session_label(self):
        for path in DOCUMENTS:
            with self.subTest(document=path.name):
                self.assertEqual(bac_sentences_that_add(sentences(path)), [])

    def test_the_pattern_finds_a_permission_or_duty_to_add(self):
        for sentence in (
            "`session_label` (§6.4) is the signed report of the session high water "
            "mark: a receiver that understands it MAY refuse the subject on it or add "
            "it to its own session label (a union only adds labels).",
            "A receiving broker SHOULD merge the BAC `session_label` into its session label.",
            "On a `peer_agent` hop the broker MUST union the BAC labels with the "
            "receiving broker's session label.",
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(bac_sentences_that_add([sentence]), [sentence])

    def test_the_pattern_passes_a_prohibition_and_a_statement(self):
        for sentence in (
            "A receiver of the BAC MUST NOT add its `session_label` to its own session label.",
            "The report does not enter the receiving broker's session label, which is "
            "the union of what that broker admits (§4.4.2).",
            "The broker MUST expose it as the `session_label` claim of any L3 BAC "
            "issued for the subject.",
        ):
            with self.subTest(sentence=sentence):
                self.assertEqual(bac_sentences_that_add([sentence]), [])


if __name__ == "__main__":
    unittest.main()
