#!/usr/bin/env python3
"""Tests for .gitignore. Run: python3 -m unittest discover -s scripts -p 'test_*.py'

CI runs them through validate_examples.py. Each path is checked by git itself
against a copy of .gitignore in a scratch repository, so a global ignore file
or .git/info/exclude on the machine running the tests does not change the result.
"""

import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


class GitignoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("git") is None:
            raise unittest.SkipTest("git is not installed")
        cls.repo = pathlib.Path(tempfile.mkdtemp())
        cls.addClassCleanup(shutil.rmtree, cls.repo)
        subprocess.run(["git", "init", "--quiet", str(cls.repo)], env=ENV, check=True)
        shutil.copyfile(ROOT / ".gitignore", cls.repo / ".gitignore")

    def ignored(self, path):
        result = subprocess.run(
            ["git", "-C", str(self.repo), "-c", f"core.excludesFile={os.devnull}",
             "check-ignore", "--no-index", "--quiet", path],
            env=ENV, capture_output=True, text=True, check=False)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.returncode == 0

    def test_secret_files_are_ignored(self):
        for path in ("secrets.json", "config/secrets.json", ".env", ".env.local",
                     "server.pem", "server.key", "client.p12", "client.pfx"):
            with self.subTest(path=path):
                self.assertTrue(self.ignored(path))

    def test_templates_and_schemas_are_not_ignored(self):
        for path in (".env.example", "secrets.example.json",
                     "schemas/ait-claims-v1.schema.json", "examples/tokens/test-keys.json"):
            with self.subTest(path=path):
                self.assertFalse(self.ignored(path))


if __name__ == "__main__":
    unittest.main()
