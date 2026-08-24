import ast
import re
import unittest
from pathlib import Path

from helpers import ROOT


class DependencyBoundaryTests(unittest.TestCase):
    def test_universal_core_contains_no_domain_names(self):
        forbidden = ("factory", "dairy", "eco", "chemistry", "neural")
        for path in (ROOT / "src" / "riec_core").rglob("*.py"):
            text = path.read_text(encoding="utf-8").lower()
            for name in forbidden:
                self.assertIsNone(re.search(rf"\b{re.escape(name)}\b", text), f"{name} leaked into Universal Core file {path.name}")

    def test_core_does_not_import_adapter_or_result_layers(self):
        forbidden_roots = {"adapters", "results", "reports", "examples"}
        for path in (ROOT / "src" / "riec_core").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".")[0] for alias in node.names}
                    self.assertTrue(roots.isdisjoint(forbidden_roots), f"forbidden import in {path}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module.split(".")[0], forbidden_roots, f"forbidden import in {path}")


if __name__ == "__main__":
    unittest.main()
