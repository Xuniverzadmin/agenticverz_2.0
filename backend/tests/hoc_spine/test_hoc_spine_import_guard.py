# Layer: L0 — Test
# AUDIENCE: INTERNAL
# Role: Pytest guard for hoc_spine package importability
# Reference: ITER3.3 — hoc_spine runtime hardening

"""
HOC Spine Import Guard Test (ITER3.3)

This test ensures ALL modules under app.hoc.cus.hoc_spine import without errors.
If any module fails to import, this test fails — blocking CI.

Purpose:
- Catch broken imports (ModuleNotFoundError, NameError) at test time
- Prevent import regressions from merging
- Enforce package-wide importability as a system invariant

Reference: docs/memory-pins/TODO_ITER3.3.md
"""

import importlib
import pkgutil
from typing import List, Tuple

import pytest


def _scan_hoc_spine_modules() -> Tuple[List[str], List[Tuple[str, str, str]]]:
    """
    Scan all modules in app.hoc.cus.hoc_spine and attempt to import each.

    Returns:
        Tuple of (passed_modules, failed_modules)
        failed_modules is a list of (module_name, error_type, error_message)
    """
    passed = []
    failed = []

    package_path = "app/hoc/cus/hoc_spine"
    package_name = "app.hoc.cus.hoc_spine"

    for importer, modname, ispkg in pkgutil.walk_packages(
        path=[package_path], prefix=package_name + "."
    ):
        # Skip test files and __pycache__
        if "__pycache__" in modname or modname.endswith("_test"):
            continue

        try:
            importlib.import_module(modname)
            passed.append(modname)
        except Exception as e:
            failed.append((modname, type(e).__name__, str(e)[:200]))

    return passed, failed


class TestHocSpineImportGuard:
    """
    Import guard tests for app.hoc.cus.hoc_spine.

    These tests enforce that the hoc_spine package is import-clean,
    meaning all modules can be imported without runtime errors.
    """

    def test_all_hoc_spine_modules_import_successfully(self):
        """
        ITER3.3 Acceptance Criterion #1 & #2:
        Package import scan passes — 0 failures allowed.

        This test walks all modules under app.hoc.cus.hoc_spine
        and attempts to import each. If ANY module fails to import,
        this test fails with details about the failing modules.
        """
        passed, failed = _scan_hoc_spine_modules()

        if failed:
            failure_details = "\n".join(
                f"  - {mod}: {etype}: {emsg}" for mod, etype, emsg in failed
            )
            pytest.fail(
                f"HOC Spine import guard failed!\n"
                f"{len(failed)} module(s) failed to import:\n{failure_details}\n\n"
                f"Fix these import errors before merging."
            )

        # Sanity check: we should have a significant number of modules
        assert len(passed) >= 100, (
            f"Expected at least 100 modules in hoc_spine, found {len(passed)}. "
            f"Package structure may have changed."
        )

    def test_critical_modules_import(self):
        """
        Test that critical hoc_spine modules are importable.

        These are the 6 modules that were fixed in ITER3.3.
        """
        critical_modules = [
            "app.hoc.cus.hoc_spine.consequences.adapters.export_bundle_adapter",
            "app.hoc.cus.hoc_spine.drivers.guard_cache",
            "app.hoc.cus.hoc_spine.drivers.idempotency",
            "app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.onboarding",
            "app.hoc.cus.hoc_spine.orchestrator.lifecycle.engines.offboarding",
            "app.hoc.cus.hoc_spine.orchestrator.plan_generation_engine",
        ]

        failed = []
        for module in critical_modules:
            try:
                importlib.import_module(module)
            except Exception as e:
                failed.append((module, type(e).__name__, str(e)[:100]))

        if failed:
            failure_details = "\n".join(
                f"  - {mod}: {etype}: {emsg}" for mod, etype, emsg in failed
            )
            pytest.fail(
                f"Critical hoc_spine modules failed to import:\n{failure_details}"
            )

    def test_operation_registry_importable(self):
        """
        Test that the central OperationRegistry is importable.

        OperationRegistry is the single composition node for hoc_spine.
        """
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            get_operation_registry,
        )

        registry = get_operation_registry()
        assert registry is not None
        assert isinstance(registry, OperationRegistry)
