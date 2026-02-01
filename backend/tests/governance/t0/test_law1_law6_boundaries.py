# Layer: L0 — Governance Test
# AUDIENCE: INTERNAL
# Role: Sentinel tests for Law 1 (downward authority) and Law 6 (schema purity)
# Reference: PIN-507 Law 1 + Law 6 remediation
# artifact_class: TEST

"""
Law 1 + Law 6 Boundary Sentinel Tests

These tests assert structural invariants by parsing the AST of source files.
They prevent regression of PIN-507 Law 1 and Law 6 remediation.

Law 1: L6 drivers must not import L5_engines (upward reach).
Law 6: hoc_spine/schemas/ must not contain standalone functions (behavior in schemas).
"""

import ast
from pathlib import Path


HOC_ROOT = Path("app/hoc")

DOMAIN_NAMES = [
    d.name
    for d in (HOC_ROOT / "cus").iterdir()
    if d.is_dir() and not d.name.startswith("_")
]


class TestLaw1NoL6ToL5EngineImports:
    """Law 1: L6 drivers must not import from L5_engines."""

    def test_no_l6_imports_l5_engines(self):
        """No L6 driver file may import from any L5_engines module."""
        violations = []
        for py_file in HOC_ROOT.rglob("cus/*/L6_drivers/*.py"):
            if py_file.name == "__init__.py":
                continue
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if ".L5_engines." in node.module or node.module.endswith(".L5_engines"):
                        violations.append(
                            f"{py_file.name}:{node.lineno} imports '{node.module}'. "
                            f"Law 1: L6 may only import L5_schemas, not L5_engines."
                        )
        assert violations == [], "\n".join(violations)


class TestLaw6SchemaPurity:
    """Law 6: hoc_spine/schemas/ must not contain standalone functions."""

    # Pre-existing schema construction helpers exempt from Law 6.
    EXCEPTIONS: set[tuple[str, str]] = {
        ("plan.py", "_utc_now"),
        ("artifact.py", "_utc_now"),
        ("agent.py", "_utc_now"),
        ("response.py", "ok"),
        ("response.py", "error"),
        ("response.py", "paginated"),
        ("response.py", "wrap_dict"),
        ("response.py", "wrap_list"),
        ("response.py", "wrap_error"),
        ("rac_models.py", "create_run_expectations"),
        ("rac_models.py", "create_domain_ack"),
    }

    def test_no_standalone_functions_in_schemas(self):
        """No hoc_spine/schemas/ file may define standalone functions (except known exemptions)."""
        schemas_dir = HOC_ROOT / "hoc_spine" / "schemas"
        violations = []
        for py_file in schemas_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            tree = ast.parse(py_file.read_text())
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if (py_file.name, node.name) in self.EXCEPTIONS:
                        continue
                    violations.append(
                        f"{py_file.name}:{node.lineno} defines '{node.name}()'. "
                        f"Law 6: move to hoc_spine/utilities/ or domain *_policy.py."
                    )
        assert violations == [], "\n".join(violations)


class TestUtilitiesPurity:
    """hoc_spine/utilities/ must not import engines, drivers, or app.db."""

    def test_utilities_no_forbidden_imports(self):
        """Utility files must not import from L5_engines, L6_drivers, or app.db."""
        utils_dir = HOC_ROOT / "hoc_spine" / "utilities"
        if not utils_dir.exists():
            return
        forbidden = [".L5_engines.", ".L6_drivers.", "app.db"]
        violations = []
        for py_file in utils_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for pattern in forbidden:
                        if pattern in node.module or node.module == pattern.lstrip("."):
                            violations.append(
                                f"{py_file.name}:{node.lineno} imports '{node.module}'. "
                                f"Utilities must not import engines, drivers, or app.db."
                            )
        assert violations == [], "\n".join(violations)


class TestLaw1NoL6CrossDomainImports:
    """Law 1: L6 drivers must not import from sibling domain L5/L6."""

    def test_no_l6_cross_domain_imports(self):
        """No L6 driver may import from a sibling domain's L5/L6."""
        violations = []
        for py_file in HOC_ROOT.rglob("cus/*/L6_drivers/*.py"):
            if py_file.name == "__init__.py":
                continue
            parts = py_file.relative_to(HOC_ROOT / "cus").parts
            own_domain = parts[0]
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for other in DOMAIN_NAMES:
                        if other == own_domain:
                            continue
                        if f"hoc.cus.{other}." in node.module:
                            violations.append(
                                f"{py_file.name}:{node.lineno} imports sibling domain '{other}'. "
                                f"Cross-domain orchestration belongs at L4."
                            )
        assert violations == [], "\n".join(violations)
