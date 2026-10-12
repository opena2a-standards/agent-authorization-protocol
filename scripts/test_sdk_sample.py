#!/usr/bin/env python3
"""Tests for the SDK sample in examples/orders-db-exchange.md.

The sample uses the `@agent.perform_action` decorator of the AIM Python SDK
(`aim_sdk`). With a `grant` argument the decorator passes the broker-backed
handle to the function as a `grant` keyword argument when the function declares
one; the same handle is returned by `aim_sdk.current_grant()`. The handle has
one method, `request(method, path, query, body)`, which carries a logical
operation to the broker. Each test reads the sample as text and checks it
against that surface, so a sample that names a handle the SDK does not provide
fails here.

Run: python3 -m unittest discover -s scripts -p 'test_*.py'
"""

import ast
import builtins
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "orders-db-exchange.md"

HANDLE_METHODS = {"request"}
REQUEST_PARAMS = ("method", "path", "query", "body")


def python_blocks(text):
    return re.findall(r"^```python\n(.*?)^```", text, re.M | re.S)


def decorated_functions(tree):
    """The functions decorated with `<name>.perform_action(..., grant=...)`."""
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and dec.func.attr == "perform_action"
                    and any(k.arg == "grant" for k in dec.keywords)):
                found.append(node)
    return found


def module_bindings(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update((a.asname or a.name).split(".")[0] for a in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name))
    return names


def function_bindings(func):
    a = func.args
    names = {p.arg for p in a.posonlyargs + a.args + a.kwonlyargs}
    names.update(p.arg for p in (a.vararg, a.kwarg) if p is not None)
    names.update(n.id for n in ast.walk(func)
                 if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store))
    return names


def undefined_names(tree, func):
    defined = module_bindings(tree) | function_bindings(func) | set(dir(builtins))
    return {n.id for n in ast.walk(func)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in defined}


def handle_names(func):
    """Names in the function bound to the grant handle."""
    names = {"grant"} & function_bindings(func)
    for node in ast.walk(func):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "attr", getattr(node.value.func, "id", None))
                == "current_grant"):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


class SdkSampleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        blocks = python_blocks(EXAMPLE.read_text(encoding="utf-8"))
        if len(blocks) != 1:
            raise AssertionError(f"expected one python block in {EXAMPLE.name}, found {len(blocks)}")
        cls.tree = ast.parse(blocks[0])
        cls.funcs = decorated_functions(cls.tree)

    def test_sample_has_a_grant_decorated_function(self):
        self.assertEqual(len(self.funcs), 1)

    def test_every_name_the_function_reads_is_defined(self):
        for func in self.funcs:
            with self.subTest(function=func.name):
                self.assertEqual(sorted(undefined_names(self.tree, func)), [])

    def test_function_obtains_the_grant_handle(self):
        for func in self.funcs:
            with self.subTest(function=func.name):
                self.assertTrue(handle_names(func),
                                "declare a `grant` parameter or call aim_sdk.current_grant()")

    def test_handle_calls_use_the_request_method_only(self):
        for func in self.funcs:
            handles = handle_names(func)
            calls = [n for n in ast.walk(func)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and isinstance(n.func.value, ast.Name) and n.func.value.id in handles]
            with self.subTest(function=func.name):
                self.assertTrue(calls)
                for call in calls:
                    self.assertIn(call.func.attr, HANDLE_METHODS)
                    self.assertLessEqual(len(call.args), len(REQUEST_PARAMS))
                    for kw in call.keywords:
                        self.assertIn(kw.arg, REQUEST_PARAMS[len(call.args):])

    def test_undefined_handle_is_reported(self):
        tree = ast.parse(
            "from aim_sdk import secure\n"
            "agent = secure('a')\n"
            "@agent.perform_action(capability='acme.com/orders:read', grant='grant://orders-db')\n"
            "def f(customer_id):\n"
            "    return db.query('q', customer_id)\n")
        func = decorated_functions(tree)[0]
        self.assertEqual(undefined_names(tree, func), {"db"})
        self.assertEqual(handle_names(func), set())


if __name__ == "__main__":
    unittest.main()
