# Layer: TEST
# AUDIENCE: INTERNAL
# Role: UAT scenario test for UC-002 Onboarding Flow — structural/contract validation
# artifact_class: TEST
"""
UAT-UC002: Onboarding Flow Validation

Validates UC-002 execution paths at the code structure level:
- Operation registrations exist in L4 handler
- L5/L6 exports and method signatures are correct
- Activation predicate fail-path returns expected (False, missing) tuple
- No live DB required — pure structural assertions

Evidence IDs: UAT-UC002-001 through UAT-UC002-005
"""

import ast
import os
import sys


# ---------------------------------------------------------------------------
# Absolute paths for file-level AST inspection
# ---------------------------------------------------------------------------
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_ONBOARDING_HANDLER_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "hoc_spine", "orchestrator", "handlers",
    "onboarding_handler.py",
)

_ONBOARDING_POLICY_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "hoc_spine", "authority",
    "onboarding_policy.py",
)


class TestUC002OnboardingFlow:
    """UAT tests for UC-002 Onboarding Flow."""

    # -----------------------------------------------------------------
    # Happy path: operation registrations
    # -----------------------------------------------------------------

    def test_onboarding_query_operation_registered(self) -> None:
        """UAT-UC002-001: account.onboarding.query is a registered operation."""
        test_id = "UAT-UC002-001"

        # Parse the handler file AST and look for the register() function
        # that calls registry.register("account.onboarding.query", ...)
        with open(_ONBOARDING_HANDLER_PATH) as f:
            source = f.read()

        tree = ast.parse(source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "account.onboarding.query":
                found = True
                break

        assert found, (
            f"{test_id}: 'account.onboarding.query' not found as a registered "
            f"operation in {_ONBOARDING_HANDLER_PATH}"
        )
        print(f"EVIDENCE: {test_id} PASS — account.onboarding.query is registered")

    def test_onboarding_advance_operation_registered(self) -> None:
        """UAT-UC002-002: account.onboarding.advance is a registered operation."""
        test_id = "UAT-UC002-002"

        with open(_ONBOARDING_HANDLER_PATH) as f:
            source = f.read()

        tree = ast.parse(source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "account.onboarding.advance":
                found = True
                break

        assert found, (
            f"{test_id}: 'account.onboarding.advance' not found as a registered "
            f"operation in {_ONBOARDING_HANDLER_PATH}"
        )
        print(f"EVIDENCE: {test_id} PASS — account.onboarding.advance is registered")

    # -----------------------------------------------------------------
    # Happy path: L5 policy exports
    # -----------------------------------------------------------------

    def test_onboarding_policy_exports(self) -> None:
        """UAT-UC002-003: onboarding_policy.py exports check_activation_predicate and get_required_state."""
        test_id = "UAT-UC002-003"

        with open(_ONBOARDING_POLICY_PATH) as f:
            source = f.read()

        tree = ast.parse(source)

        # Collect top-level function definitions
        top_level_functions = {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, ast.FunctionDef)
        }

        assert "check_activation_predicate" in top_level_functions, (
            f"{test_id}: 'check_activation_predicate' not defined in {_ONBOARDING_POLICY_PATH}"
        )
        assert "get_required_state" in top_level_functions, (
            f"{test_id}: 'get_required_state' not defined in {_ONBOARDING_POLICY_PATH}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — onboarding_policy.py exports "
            "check_activation_predicate and get_required_state"
        )

    # -----------------------------------------------------------------
    # Happy path: L4 handler method
    # -----------------------------------------------------------------

    def test_handler_has_check_activation_conditions(self) -> None:
        """UAT-UC002-004: onboarding_handler.py has _check_activation_conditions method."""
        test_id = "UAT-UC002-004"

        with open(_ONBOARDING_HANDLER_PATH) as f:
            source = f.read()

        tree = ast.parse(source)

        # Look for _check_activation_conditions as a top-level function def
        function_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        assert "_check_activation_conditions" in function_names, (
            f"{test_id}: '_check_activation_conditions' not found in {_ONBOARDING_HANDLER_PATH}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — onboarding_handler.py defines "
            "_check_activation_conditions"
        )

    # -----------------------------------------------------------------
    # Fail path: activation predicate with all-false inputs
    # -----------------------------------------------------------------

    def test_activation_predicate_all_false_fails(self) -> None:
        """UAT-UC002-005: check_activation_predicate(False,False,False,False) returns (False, missing_list)."""
        test_id = "UAT-UC002-005"

        # Import the actual function — it is a pure-policy module with no DB deps
        sys.path.insert(0, _BACKEND)
        try:
            from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
                check_activation_predicate,
            )

            passed, missing = check_activation_predicate(False, False, False, False)

            assert passed is False, (
                f"{test_id}: Expected passed=False but got passed={passed}"
            )
            assert isinstance(missing, list), (
                f"{test_id}: Expected missing to be a list but got {type(missing)}"
            )

            # All four conditions should be missing
            expected_missing = {"project_ready", "key_ready", "connector_validated", "sdk_attested"}
            actual_missing = set(missing)
            assert actual_missing == expected_missing, (
                f"{test_id}: Expected missing={expected_missing} but got {actual_missing}"
            )
        finally:
            sys.path.pop(0)

        print(
            f"EVIDENCE: {test_id} PASS — check_activation_predicate(False,False,False,False) "
            f"returns (False, {sorted(expected_missing)})"
        )
