# Layer: TEST
# AUDIENCE: INTERNAL
# Role: UAT scenario test for UC-006 Signal Feedback Flow — structural/contract validation
# artifact_class: TEST
"""
UAT-UC006: Signal Feedback Flow Validation

Validates UC-006 execution paths at the code structure level:
- activity.signal_feedback is registered in L4 handler
- L5 SignalFeedbackService has acknowledge_signal, suppress_signal, reopen_signal
- L6 SignalFeedbackDriver has insert_feedback, query_feedback
- L5 engine has no sqlalchemy/sqlmodel runtime imports (AST check)
- No live DB required — pure structural assertions

Evidence IDs: UAT-UC006-001 through UAT-UC006-004
"""

import ast
import os


_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_ACTIVITY_HANDLER_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "hoc_spine", "orchestrator", "handlers",
    "activity_handler.py",
)

_SIGNAL_FEEDBACK_ENGINE_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "activity", "L5_engines",
    "signal_feedback_engine.py",
)

_SIGNAL_FEEDBACK_DRIVER_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "activity", "L6_drivers",
    "signal_feedback_driver.py",
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


def _get_runtime_imports(filepath: str) -> list[str]:
    """
    Return module names imported at runtime (not under TYPE_CHECKING).

    Walks the AST and collects Import/ImportFrom nodes that are NOT inside
    an `if TYPE_CHECKING:` block.
    """
    with open(filepath) as f:
        source = f.read()
    tree = ast.parse(source)

    type_checking_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Detect `if TYPE_CHECKING:` guard
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                start = node.lineno
                end = max(
                    getattr(child, "end_lineno", start) or start
                    for child in ast.walk(node)
                )
                type_checking_ranges.append((start, end))

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            lineno = node.lineno
            in_type_checking = any(
                start <= lineno <= end for start, end in type_checking_ranges
            )
            if in_type_checking:
                continue
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif node.module:
                imports.append(node.module)
    return imports


class TestUC006SignalFeedbackFlow:
    """UAT tests for UC-006 Signal Feedback Flow."""

    # -----------------------------------------------------------------
    # Happy path: operation registration
    # -----------------------------------------------------------------

    def test_signal_feedback_operation_registered(self) -> None:
        """UAT-UC006-001: activity.signal_feedback is a registered operation."""
        test_id = "UAT-UC006-001"

        with open(_ACTIVITY_HANDLER_PATH) as f:
            source = f.read()

        tree = ast.parse(source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "activity.signal_feedback":
                found = True
                break

        assert found, (
            f"{test_id}: 'activity.signal_feedback' not found as a registered "
            f"operation in {_ACTIVITY_HANDLER_PATH}"
        )
        print(f"EVIDENCE: {test_id} PASS — activity.signal_feedback is registered")

    # -----------------------------------------------------------------
    # Happy path: L5 SignalFeedbackService methods
    # -----------------------------------------------------------------

    def test_l5_signal_feedback_service_methods(self) -> None:
        """UAT-UC006-002: SignalFeedbackService has acknowledge, suppress, reopen methods."""
        test_id = "UAT-UC006-002"

        methods = _get_class_methods(_SIGNAL_FEEDBACK_ENGINE_PATH, "SignalFeedbackService")
        required = {"acknowledge_signal", "suppress_signal", "reopen_signal"}
        missing = required - methods

        assert not missing, (
            f"{test_id}: SignalFeedbackService missing methods: {missing}. "
            f"Found: {methods & required}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — SignalFeedbackService has "
            "acknowledge_signal, suppress_signal, reopen_signal"
        )

    # -----------------------------------------------------------------
    # Happy path: L6 SignalFeedbackDriver methods
    # -----------------------------------------------------------------

    def test_l6_signal_feedback_driver_methods(self) -> None:
        """UAT-UC006-003: SignalFeedbackDriver has insert_feedback, query_feedback."""
        test_id = "UAT-UC006-003"

        methods = _get_class_methods(_SIGNAL_FEEDBACK_DRIVER_PATH, "SignalFeedbackDriver")
        required = {"insert_feedback", "query_feedback"}
        missing = required - methods

        assert not missing, (
            f"{test_id}: SignalFeedbackDriver missing methods: {missing}. "
            f"Found: {methods & required}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — SignalFeedbackDriver has "
            "insert_feedback, query_feedback"
        )

    # -----------------------------------------------------------------
    # Fail path: L5 engine no sqlalchemy/sqlmodel runtime imports
    # -----------------------------------------------------------------

    def test_l5_engine_no_db_imports(self) -> None:
        """UAT-UC006-004: signal_feedback_engine.py has no sqlalchemy/sqlmodel runtime imports."""
        test_id = "UAT-UC006-004"

        forbidden_prefixes = ("sqlalchemy", "sqlmodel", "asyncpg", "psycopg")
        runtime_imports = _get_runtime_imports(_SIGNAL_FEEDBACK_ENGINE_PATH)

        violations = [
            imp for imp in runtime_imports
            if any(imp.startswith(prefix) for prefix in forbidden_prefixes)
        ]

        assert not violations, (
            f"{test_id}: L5 engine has forbidden runtime DB imports: {violations}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — signal_feedback_engine.py has "
            f"zero forbidden DB imports (checked {len(runtime_imports)} imports)"
        )
