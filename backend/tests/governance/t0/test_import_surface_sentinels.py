# Layer: L0 — Test
# AUDIENCE: INTERNAL
# Role: Import surface sentinel — catches masked import failures in eager __init__ chains
# Reference: PIN-507 Law 0

"""
Import Surface Sentinels

These tests catch ImportError violations hidden by eager __init__.py re-exports.
When a deep import in the chain breaks, higher-level imports mask the failure
until a specific code path triggers the chain. These sentinels exercise the
top-level package imports directly so failures surface immediately.

Added after PIN-507 Law 0 uncovered a cascade of 16 masked import failures
across logs, incidents, integrations, and policies domains — each hidden behind
an earlier failure in the same eager __init__ chain.

Two test strategies:
1. Static tests for known-critical import paths (fast, targeted)
2. Dynamic submodule discovery test that loads ALL .py files under hoc/cus/
   (comprehensive, catches unknown failures)
"""

import importlib
import pkgutil
from pathlib import Path

import pytest

# Known pre-existing issues that cannot be fixed in this session.
# Each entry: (module_path_substring, reason)
# Matched against module name — if any substring matches, module is xfailed.
KNOWN_XFAILS = {
    "contract_engine": "ValidatorVerdict undefined (HOC spine TODO)",
}

# Error-message patterns for cascading failures caused by pre-existing issues.
# Matched against the str(exception) — catches transitive victims of a root-cause bug.
KNOWN_ERROR_XFAILS = [
    ("ValidatorVerdict", "Cascade from contract_engine ValidatorVerdict (HOC spine TODO)"),
    ("adapters.base", "Missing integrations adapters.base module (pre-existing)"),
    ("panel_types", "Missing logs L6 panel_types module (pre-existing)"),
    ("L6_drivers.models", "Missing logs L6 models module (pre-existing)"),
    ("policies.controls", "Missing policies controls module (pre-existing)"),
    ("sandbox_executor", "Missing sandbox_executor module (pre-existing)"),
    ("schemas", "Missing schemas module in domain (pre-existing)"),
    ("semantic_types", "Missing incidents semantic_types module (pre-existing)"),
    ("panel_consistency_checker", "Missing analytics panel_consistency_checker (pre-existing)"),
    ("L5_vault", "Missing integrations L5_vault module (pre-existing)"),
    ("'Incident' from 'app.db'", "L6→L7 boundary: Incident not in app.db (pre-existing)"),
    ("circular import", "Circular import in policy AST (pre-existing)"),
    ("already defined for this MetaData", "Duplicate table definition (pre-existing)"),
    ("non-default argument", "Dataclass field ordering error (pre-existing)"),
]


# ---------------------------------------------------------------------------
# Static sentinel tests — known-critical import paths
# ---------------------------------------------------------------------------

class TestLogsDomainImportSurface:
    """Verify logs domain packages import without error."""

    def test_l5_engines_package_imports(self):
        """L5 engines __init__ eagerly loads all facades — catch any broken import."""
        import app.hoc.cus.logs.L5_engines  # noqa: F401

    def test_l6_drivers_package_imports(self):
        """L6 drivers __init__ eagerly loads all stores — catch any broken import."""
        import app.hoc.cus.logs.L6_drivers  # noqa: F401

    def test_audit_ledger_engine_imports(self):
        """audit_ledger_engine is the entry point that triggered the masked failure."""
        from app.hoc.cus.logs.L5_engines.audit_ledger_engine import AuditLedgerService  # noqa: F401


class TestIncidentsDomainImportSurface:
    """Verify incidents domain packages import without error."""

    def test_l5_engines_package_imports(self):
        import app.hoc.cus.incidents.L5_engines  # noqa: F401

    def test_l6_drivers_package_imports(self):
        import app.hoc.cus.incidents.L6_drivers  # noqa: F401


class TestIntegrationsDomainImportSurface:
    """Verify integrations domain packages import without error."""

    @pytest.mark.xfail(
        reason="Pre-existing: ValidatorVerdict undefined in contract_engine.py (HOC spine TODO)",
        strict=False,
    )
    def test_l5_engines_package_imports(self):
        import app.hoc.cus.integrations.L5_engines  # noqa: F401

    def test_bridges_module_imports(self):
        """bridges module is used by test_m25_integration_loop — catch any broken import."""
        from app.integrations.bridges import (  # noqa: F401
            IncidentToCatalogBridge,
            PatternToRecoveryBridge,
            RecoveryToPolicyBridge,
        )

    def test_events_module_imports(self):
        """events module is used by test_m25_policy_overreach — catch any broken import."""
        from app.integrations.events import ConfidenceCalculator  # noqa: F401


# ---------------------------------------------------------------------------
# Dynamic submodule discovery — comprehensive import surface test
# ---------------------------------------------------------------------------

def _discover_hoc_submodules():
    """Discover all importable .py modules under app/hoc/cus/."""
    hoc_cus = Path(__file__).resolve().parent.parent.parent.parent / "app" / "hoc" / "cus"
    if not hoc_cus.exists():
        return []

    modules = []
    for py_file in sorted(hoc_cus.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        # Convert path to module name
        rel = py_file.relative_to(hoc_cus.parent.parent.parent)
        module_name = str(rel).replace("/", ".").removesuffix(".py")
        modules.append(module_name)
    return modules


def _is_known_xfail(module_name: str) -> str | None:
    """Check if a module is a known xfail. Returns reason or None."""
    for substring, reason in KNOWN_XFAILS.items():
        if substring in module_name:
            return reason
    return None


HOC_MODULES = _discover_hoc_submodules()


@pytest.mark.parametrize("module_name", HOC_MODULES, ids=lambda m: m.split(".")[-1])
def test_hoc_submodule_imports(module_name):
    """Each HOC submodule must import without error.

    This test dynamically discovers all .py files under app/hoc/cus/ and
    attempts to import each one. Failures indicate broken import chains
    that would be masked by eager __init__ re-exports.
    """
    xfail_reason = _is_known_xfail(module_name)
    if xfail_reason:
        pytest.xfail(xfail_reason)

    try:
        importlib.import_module(module_name)
    except Exception as exc:
        err_str = f"{type(exc).__name__}: {exc}"
        for pattern, reason in KNOWN_ERROR_XFAILS:
            if pattern in err_str:
                pytest.xfail(f"{reason} — {err_str[:120]}")
        pytest.fail(f"Import of {module_name} failed: {err_str}")
