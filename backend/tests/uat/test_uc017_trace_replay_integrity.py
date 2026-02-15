# Layer: TEST
# AUDIENCE: INTERNAL
# Role: UAT scenario test for UC-017 Trace Replay Integrity — structural/contract validation
# artifact_class: TEST
"""
UAT-UC017: Trace Replay Integrity Validation

Validates UC-017 execution paths at the code structure level:
- L5 TraceApiEngine has get_trace_by_root_hash and compare_traces methods
- L6 PostgresTraceStore has get_trace_by_root_hash and check_idempotency_key methods
- L5 engine has no direct DB/ORM imports at runtime (AST check)
- No live DB required — pure structural assertions

Evidence IDs: UAT-UC017-001 through UAT-UC017-003
"""

import ast
import os


_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

_TRACE_API_ENGINE_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "logs", "L5_engines",
    "trace_api_engine.py",
)

_PG_STORE_PATH = os.path.join(
    _BACKEND,
    "app", "hoc", "cus", "logs", "L6_drivers",
    "pg_store.py",
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


class TestUC017TraceReplayIntegrity:
    """UAT tests for UC-017 Trace Replay Integrity."""

    # -----------------------------------------------------------------
    # Happy path: L5 TraceApiEngine methods
    # -----------------------------------------------------------------

    def test_l5_trace_api_engine_methods(self) -> None:
        """UAT-UC017-001: TraceApiEngine has get_trace_by_root_hash and compare_traces."""
        test_id = "UAT-UC017-001"

        methods = _get_class_methods(_TRACE_API_ENGINE_PATH, "TraceApiEngine")
        required = {"get_trace_by_root_hash", "compare_traces"}
        missing = required - methods

        assert not missing, (
            f"{test_id}: TraceApiEngine missing methods: {missing}. "
            f"Found: {methods & required}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — TraceApiEngine has "
            "get_trace_by_root_hash and compare_traces"
        )

    # -----------------------------------------------------------------
    # Happy path: L6 PostgresTraceStore methods
    # -----------------------------------------------------------------

    def test_l6_postgres_trace_store_methods(self) -> None:
        """UAT-UC017-002: PostgresTraceStore has get_trace_by_root_hash and check_idempotency_key."""
        test_id = "UAT-UC017-002"

        methods = _get_class_methods(_PG_STORE_PATH, "PostgresTraceStore")
        required = {"get_trace_by_root_hash", "check_idempotency_key"}
        missing = required - methods

        assert not missing, (
            f"{test_id}: PostgresTraceStore missing methods: {missing}. "
            f"Found: {methods & required}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — PostgresTraceStore has "
            "get_trace_by_root_hash and check_idempotency_key"
        )

    # -----------------------------------------------------------------
    # Fail path: L5 engine no DB/ORM runtime imports
    # -----------------------------------------------------------------

    def test_l5_engine_no_db_imports(self) -> None:
        """UAT-UC017-003: trace_api_engine.py has no sqlalchemy/sqlmodel/asyncpg runtime imports."""
        test_id = "UAT-UC017-003"

        forbidden_prefixes = ("sqlalchemy", "sqlmodel", "asyncpg", "psycopg")
        runtime_imports = _get_runtime_imports(_TRACE_API_ENGINE_PATH)

        violations = [
            imp for imp in runtime_imports
            if any(imp.startswith(prefix) for prefix in forbidden_prefixes)
        ]

        assert not violations, (
            f"{test_id}: L5 engine has forbidden runtime DB imports: {violations}"
        )
        print(
            f"EVIDENCE: {test_id} PASS — trace_api_engine.py has "
            f"zero forbidden DB imports (checked {len(runtime_imports)} imports)"
        )
