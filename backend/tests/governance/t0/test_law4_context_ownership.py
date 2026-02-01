# Layer: L0 — Governance Test
# AUDIENCE: INTERNAL
# Role: Sentinel test — Law 4 context ownership invariant (PIN-507)
# artifact_class: TEST

"""
Law 4 Sentinel Tests (PIN-507)

Directly asserts the Law 4 invariant:
- Coordinators must be context-free (no session in signatures)
- L6 drivers must not import sibling domains (orchestration belongs at L4)
"""

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent
COORD_DIR = BACKEND_ROOT / "app" / "hoc" / "hoc_spine" / "orchestrator" / "coordinators"
CUS_DIR = BACKEND_ROOT / "app" / "hoc" / "cus"


class TestLaw4ContextOwnership:
    """Law 4: Only handlers bind sessions. Coordinators must be context-free."""

    def test_no_session_in_coordinator_signatures(self):
        """No coordinator method may accept 'session' as a parameter."""
        violations = []
        for py_file in COORD_DIR.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Only check methods inside coordinator classes
                    for item in ast.walk(node):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            arg_names = [a.arg for a in item.args.args]
                            if "session" in arg_names:
                                violations.append(
                                    f"{py_file.name}:{item.lineno} — "
                                    f"{node.name}.{item.name}() accepts 'session'. "
                                    f"Law 4: coordinators must be context-free."
                                )
        assert not violations, "\n".join(violations)

    def test_no_l6_cross_domain_imports(self):
        """No L6 driver may import from a sibling domain's L5/L6."""
        domains = [
            d.name for d in CUS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]
        violations = []
        for domain in domains:
            l6_dir = CUS_DIR / domain / "L6_drivers"
            if not l6_dir.exists():
                continue
            for py_file in l6_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                try:
                    tree = ast.parse(py_file.read_text())
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        for other in domains:
                            if other == domain:
                                continue
                            if f"hoc.cus.{other}." in node.module:
                                violations.append(
                                    f"{py_file.name}:{node.lineno} imports sibling domain '{other}'. "
                                    f"Cross-domain orchestration belongs at L4."
                                )
        assert not violations, "\n".join(violations)

    def test_audit_coordinator_deleted(self):
        """audit_coordinator.py must not exist (PIN-507 Law 4 tombstone)."""
        assert not (COORD_DIR / "audit_coordinator.py").exists(), (
            "audit_coordinator.py must remain deleted. "
            "See tombstone in coordinators/__init__.py."
        )
