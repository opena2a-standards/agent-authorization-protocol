#!/usr/bin/env python3
"""Tests for the contact addresses in the documents. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py. A line that offers a reader more than
one address offers distinct ones, so "email A or B" never names the same channel twice.
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_naming  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")


def repeated_addresses(text: str) -> list[str]:
    """Return one "line N: address" entry per line that names an address more than once."""
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        seen = set()
        for address in ADDRESS.findall(line):
            if address.lower() in seen:
                found.append(f"line {number}: {address}")
                break
            seen.add(address.lower())
    return found


class RepeatedAddressesTest(unittest.TestCase):
    def test_same_address_twice_on_a_line_is_found(self):
        text = "Intro.\n- For security findings, email a@example.org or A@example.org.\n"
        self.assertEqual(repeated_addresses(text), ["line 2: A@example.org"])

    def test_distinct_addresses_and_one_per_line_pass(self):
        text = "Email a@example.org or b@example.org.\nOr email a@example.org.\n"
        self.assertEqual(repeated_addresses(text), [])


class DocumentsTest(unittest.TestCase):
    def test_no_document_line_names_an_address_twice(self):
        for name in check_naming.documents(ROOT):
            with self.subTest(document=name):
                text, error = check_naming.read_text(ROOT / name)
                self.assertIsNone(error)
                self.assertEqual(repeated_addresses(text), [])


if __name__ == "__main__":
    unittest.main()
