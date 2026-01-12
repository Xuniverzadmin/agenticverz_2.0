# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Layer boundary tripwire tests
# Callers: pytest, CI pipeline
# Allowed Imports: stdlib, pytest
# Forbidden Imports: app.*
# Reference: docs/architecture/LAYER_MODEL.md

"""
Architecture Tripwire Tests

Mechanical verification of layer boundaries per LAYER_MODEL.md.

These tests run as part of the test suite to catch layer violations
early, before they can be committed.

Rules enforced:
- LAYER-001: Domain code must not import FastAPI
- LAYER-002: Domain code must not import from routes (app.api)
- LAYER-003: Router definitions must be in app/api/, not domain code
- LAYER-004: Domain code must not query observability (write-only)
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


# Determine the backend root
BACKEND_ROOT = Path(__file__).parent.parent.parent


def get_imports_from_file(filepath: Path) -> List[Tuple[int, str]]:
    """Extract all imports from a Python file."""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((node.lineno, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append((node.lineno, f"from {module} import ..."))
    except SyntaxError:
        pass
    except Exception:
        pass

    return imports


class TestLayerBoundaries:
    """Test suite for layer boundary enforcement."""

    def test_layer_001_billing_no_fastapi(self):
        """LAYER-001: app/billing/ must not import FastAPI."""
        billing_dir = BACKEND_ROOT / "app" / "billing"
        violations = []

        for py_file in billing_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            imports = get_imports_from_file(py_file)
            for line_no, import_str in imports:
                if "fastapi" in import_str.lower():
                    violations.append(
                        f"{py_file.relative_to(BACKEND_ROOT)}:{line_no}: {import_str}"
                    )

        assert not violations, (
            f"LAYER-001 violation: Billing code imports FastAPI\n"
            + "\n".join(violations)
        )

    def test_layer_001_protection_no_fastapi(self):
        """LAYER-001: app/protection/ must not import FastAPI."""
        protection_dir = BACKEND_ROOT / "app" / "protection"
        violations = []

        for py_file in protection_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            imports = get_imports_from_file(py_file)
            for line_no, import_str in imports:
                if "fastapi" in import_str.lower():
                    violations.append(
                        f"{py_file.relative_to(BACKEND_ROOT)}:{line_no}: {import_str}"
                    )

        assert not violations, (
            f"LAYER-001 violation: Protection code imports FastAPI\n"
            + "\n".join(violations)
        )

    def test_layer_001_observability_no_fastapi(self):
        """LAYER-001: app/observability/ must not import FastAPI."""
        observability_dir = BACKEND_ROOT / "app" / "observability"
        if not observability_dir.exists():
            return  # Observability may not exist yet

        violations = []

        for py_file in observability_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            imports = get_imports_from_file(py_file)
            for line_no, import_str in imports:
                if "fastapi" in import_str.lower():
                    violations.append(
                        f"{py_file.relative_to(BACKEND_ROOT)}:{line_no}: {import_str}"
                    )

        assert not violations, (
            f"LAYER-001 violation: Observability code imports FastAPI\n"
            + "\n".join(violations)
        )

    def test_layer_002_no_upward_imports(self):
        """LAYER-002: Domain code must not import from app.api."""
        domain_dirs = [
            BACKEND_ROOT / "app" / "billing",
            BACKEND_ROOT / "app" / "protection",
            BACKEND_ROOT / "app" / "observability",
        ]
        violations = []

        for domain_dir in domain_dirs:
            if not domain_dir.exists():
                continue

            for py_file in domain_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                imports = get_imports_from_file(py_file)
                for line_no, import_str in imports:
                    if "app.api" in import_str:
                        violations.append(
                            f"{py_file.relative_to(BACKEND_ROOT)}:{line_no}: {import_str}"
                        )

        assert not violations, (
            f"LAYER-002 violation: Domain code imports from routes\n"
            + "\n".join(violations)
        )

    def test_layer_003_no_routers_in_domain(self):
        """LAYER-003: Router definitions must be in app/api/, not domain code."""
        domain_dirs = [
            BACKEND_ROOT / "app" / "billing",
            BACKEND_ROOT / "app" / "protection",
            BACKEND_ROOT / "app" / "observability",
        ]
        router_patterns = [
            "APIRouter(",
            "@router.get",
            "@router.post",
            "@router.put",
            "@router.patch",
            "@router.delete",
        ]
        violations = []

        for domain_dir in domain_dirs:
            if not domain_dir.exists():
                continue

            for py_file in domain_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    for pattern in router_patterns:
                        if pattern in content:
                            violations.append(
                                f"{py_file.relative_to(BACKEND_ROOT)}: contains {pattern}"
                            )
                            break  # One violation per file is enough
                except Exception:
                    pass

        assert not violations, (
            f"LAYER-003 violation: Router definitions in domain code\n"
            + "\n".join(violations)
        )

    def test_layer_004_observability_write_only(self):
        """LAYER-004: Domain code must not query observability (write-only)."""
        domain_dirs = [
            BACKEND_ROOT / "app" / "billing",
            BACKEND_ROOT / "app" / "protection",
            # observability itself is allowed to define query()
        ]
        violations = []

        for domain_dir in domain_dirs:
            if not domain_dir.exists():
                continue

            for py_file in domain_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    if (
                        "get_observability_provider().query" in content
                        or "observability_provider.query" in content
                    ):
                        violations.append(
                            f"{py_file.relative_to(BACKEND_ROOT)}: queries observability"
                        )
                except Exception:
                    pass

        assert not violations, (
            f"LAYER-004 violation: Domain code queries observability\n"
            + "\n".join(violations)
        )

    def test_ci_boundary_checker_passes(self):
        """Verify the CI boundary checker passes (integration check)."""
        script_path = BACKEND_ROOT / "scripts" / "ci" / "check_layer_boundaries.py"

        if not script_path.exists():
            # Skip if CI script doesn't exist
            return

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"CI boundary checker failed:\n{result.stdout}\n{result.stderr}"
        )


class TestDependencyFileLocation:
    """Test that FastAPI dependencies are in the correct location."""

    def test_billing_dependencies_in_api(self):
        """Billing FastAPI dependencies should be in app/api/."""
        # Should exist in api/
        correct_path = BACKEND_ROOT / "app" / "api" / "billing_dependencies.py"
        assert correct_path.exists(), (
            "app/api/billing_dependencies.py should exist"
        )

        # Should NOT exist in billing/
        wrong_path = BACKEND_ROOT / "app" / "billing" / "dependencies.py"
        assert not wrong_path.exists(), (
            "app/billing/dependencies.py should not exist (moved to app/api/)"
        )

    def test_protection_dependencies_in_api(self):
        """Protection FastAPI dependencies should be in app/api/."""
        # Should exist in api/
        correct_path = BACKEND_ROOT / "app" / "api" / "protection_dependencies.py"
        assert correct_path.exists(), (
            "app/api/protection_dependencies.py should exist"
        )

        # Should NOT exist in protection/
        wrong_path = BACKEND_ROOT / "app" / "protection" / "dependencies.py"
        assert not wrong_path.exists(), (
            "app/protection/dependencies.py should not exist (moved to app/api/)"
        )
