# Layer: TEST
# AUDIENCE: INTERNAL
# Role: UAT scenario test for UC-008 Analytics Artifacts — structural/contract validation
# artifact_class: TEST
"""
UAT-UC008: Analytics Artifacts Validation

Validates UC-008 execution paths at the code structure level:
- analytics.artifacts is registered in L4 handler
- L6 AnalyticsArtifactsDriver has save_artifact, get_artifact, list_artifacts
- L6 driver has no business conditionals (no `if severity`, `if policy` via AST)
- No live DB required — pure structural assertions

Evidence IDs: UAT-UC008-001 through UAT-UC008-003
"""

import ast
import os


_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_ANALYTICS_HANDLER_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "hoc_spine", "orchestrator", "handlers",
    "analytics_handler.py",
)

_ANALYTICS_ARTIFACTS_DRIVER_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "analytics", "L6_drivers",
    "analytics_artifacts_driver.py",
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

    Returns a list of identifier strings found as the test expression
    of `if` statements (handles ast.Name nodes in test positions).
    This is used to detect business-logic conditionals like `if severity`
    or `if policy` which should not appear in L6 drivers.
    """
    with open(filepath) as f:
        source = f.read()
    tree = ast.parse(source)

    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Direct name test: `if severity:`
            if isinstance(node.test, ast.Name):
                names.append(node.test.id)
            # Comparison tests: `if severity == ...`
            elif isinstance(node.test, ast.Compare):
                if isinstance(node.test.left, ast.Name):
                    names.append(node.test.left.id)
    return names


class TestUC008AnalyticsArtifacts:
    """UAT tests for UC-008 Analytics Artifacts."""

    # -----------------------------------------------------------------
    # Happy path: operation registration
    # -----------------------------------------------------------------

    def test_analytics_artifacts_operation_registered(self) -> None:
        """UAT-UC008-001: analytics.artifacts is a registered operation."""
        test_id = "UAT-UC008-001"

        with open(_ANALYTICS_HANDLER_PATH) as f:
            source = f.read()

        tree = ast.parse(source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "analytics.artifacts":
                found = True
                break

        assert found, (
            f"{test_id}: 'analytics.artifacts' not found as a registered "
            f"operation in {_ANALYTICS_HANDLER_PATH}"
        )
        print(f"EVIDENCE: {test_id} PASS — analytics.artifacts is registered")

    # -----------------------------------------------------------------
    # Happy path: L6 driver methods
    # -----------------------------------------------------------------

    def test_l6_analytics_artifacts_driver_methods(self) -> None:
        """UAT-UC008-002: AnalyticsArtifactsDriver has save_artifact, get_artifact, list_artifacts."""
        test_id = "UAT-UC008-002"

        methods = _get_class_methods(
            _ANALYTICS_ARTIFACTS_DRIVER_PATH, "AnalyticsArtifactsDriver"
        )
        required = {"save_artifact", "get_artifact", "list_artifacts"}
        missing = required - methods

        assert not missing, (
            f"{test_id}: AnalyticsArtifactsDriver missing methods: {missing}. "
            f"Found: {methods & required}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — AnalyticsArtifactsDriver has "
            "save_artifact, get_artifact, list_artifacts"
        )

    # -----------------------------------------------------------------
    # Fail path: L6 driver has no business conditionals
    # -----------------------------------------------------------------

    def test_l6_driver_no_business_conditionals(self) -> None:
        """UAT-UC008-003: analytics_artifacts_driver.py has no business-logic conditionals."""
        test_id = "UAT-UC008-003"

        # Business-logic names that should NOT appear as `if <name>` in L6 drivers.
        # L6 drivers should only have data-routing conditionals (if run_id, if tenant_id)
        # not policy/business conditionals.
        forbidden_if_names = {"severity", "policy", "risk_level", "decision", "action"}

        if_names = _collect_if_test_names(_ANALYTICS_ARTIFACTS_DRIVER_PATH)
        violations = [name for name in if_names if name in forbidden_if_names]

        assert not violations, (
            f"{test_id}: L6 driver contains business-logic conditionals: "
            f"if {violations}. L6 drivers must be data-access only."
        )
        print(
            f"EVIDENCE: {test_id} PASS — analytics_artifacts_driver.py has "
            f"zero business-logic conditionals (scanned {len(if_names)} if-tests)"
        )
