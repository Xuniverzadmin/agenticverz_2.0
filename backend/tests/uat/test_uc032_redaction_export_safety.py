# Layer: TEST
# AUDIENCE: INTERNAL
# Role: UAT scenario test for UC-032 Redaction Export Safety — structural/contract validation
# artifact_class: TEST
"""
UAT-UC032: Redaction Export Safety Validation

Validates UC-032 execution paths at the code structure level:
- L6 SQLiteTraceStore (trace_store.py) has find_matching_traces and update_trace_determinism
- The redact module exists in the logs domain (L5_engines/redact.py or L6_drivers/redact.py)
- trace_store.py L6 driver has no business conditionals (AST check)
- No live DB required — pure structural assertions

Evidence IDs: UAT-UC032-001 through UAT-UC032-003
"""

import ast
import os


_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_TRACE_STORE_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "logs", "L6_drivers",
    "trace_store.py",
)

_REDACT_L6_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "logs", "L6_drivers",
    "redact.py",
)

_REDACT_L5_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "logs", "L5_engines",
    "redact.py",
)


def _get_class_methods(filepath: str, class_name: str) -> set[str]:
    """Parse a file and return method names for a given class."""
    with open(filepath) as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


def _collect_if_test_names(filepath: str) -> list[str]:
    """
    Collect the names used in `if <name>` tests inside a file.

    Returns identifier strings found as the test expression of `if` statements.
    Used to detect business-logic conditionals that should not appear in L6 drivers.
    """
    with open(filepath) as f:
        source = f.read()
    tree = ast.parse(source)

    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if isinstance(node.test, ast.Name):
                names.append(node.test.id)
            elif isinstance(node.test, ast.Compare):
                if isinstance(node.test.left, ast.Name):
                    names.append(node.test.left.id)
    return names


class TestUC032RedactionExportSafety:
    """UAT tests for UC-032 Redaction Export Safety."""

    # -----------------------------------------------------------------
    # Happy path: SQLiteTraceStore methods
    # -----------------------------------------------------------------

    def test_trace_store_has_required_methods(self) -> None:
        """UAT-UC032-001: SQLiteTraceStore has find_matching_traces and update_trace_determinism."""
        test_id = "UAT-UC032-001"

        methods = _get_class_methods(_TRACE_STORE_PATH, "SQLiteTraceStore")
        required = {"find_matching_traces", "update_trace_determinism"}
        missing = required - methods

        assert not missing, (
            f"{test_id}: SQLiteTraceStore missing methods: {missing}. "
            f"Found: {methods & required}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — SQLiteTraceStore has "
            "find_matching_traces and update_trace_determinism"
        )

    # -----------------------------------------------------------------
    # Happy path: redact module exists
    # -----------------------------------------------------------------

    def test_redact_module_exists(self) -> None:
        """UAT-UC032-002: A redact module exists in the logs domain."""
        test_id = "UAT-UC032-002"

        # The redact module may live in L6_drivers/redact.py or L5_engines/redact.py
        # (it was reclassified L6->L5 but remains in L6_drivers/ per Layer != Directory)
        l6_exists = os.path.isfile(_REDACT_L6_PATH)
        l5_exists = os.path.isfile(_REDACT_L5_PATH)

        assert l6_exists or l5_exists, (
            f"{test_id}: No redact module found in logs domain. "
            f"Checked: {_REDACT_L6_PATH}, {_REDACT_L5_PATH}"
        )

        # Verify the module exports redact_trace_data
        redact_path = _REDACT_L6_PATH if l6_exists else _REDACT_L5_PATH
        with open(redact_path) as f:
            source = f.read()
        tree = ast.parse(source)

        function_names = {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, ast.FunctionDef)
        }

        assert "redact_trace_data" in function_names, (
            f"{test_id}: redact module at {redact_path} does not export redact_trace_data"
        )

        location = "L6_drivers" if l6_exists else "L5_engines"
        print(
            f"EVIDENCE: {test_id} PASS — redact module exists in logs/{location}/ "
            "and exports redact_trace_data"
        )

    # -----------------------------------------------------------------
    # Fail path: trace_store.py no business conditionals
    # -----------------------------------------------------------------

    def test_trace_store_no_business_conditionals(self) -> None:
        """UAT-UC032-003: trace_store.py has no business-logic conditionals."""
        test_id = "UAT-UC032-003"

        # Business-logic names that should NOT appear as `if <name>` in L6 drivers.
        # L6 drivers should only have data-routing conditionals (if tenant_id, if run_id, etc.)
        forbidden_if_names = {"severity", "policy", "risk_level", "decision", "action"}

        if_names = _collect_if_test_names(_TRACE_STORE_PATH)
        violations = [name for name in if_names if name in forbidden_if_names]

        assert not violations, (
            f"{test_id}: trace_store.py contains business-logic conditionals: "
            f"if {violations}. L6 drivers must be data-access only."
        )
        print(
            f"EVIDENCE: {test_id} PASS — trace_store.py has "
            f"zero business-logic conditionals (scanned {len(if_names)} if-tests)"
        )
