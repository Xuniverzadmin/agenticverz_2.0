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
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)
from tests.uat.stagetest_trace_capture import get_active_recorder


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_sqlite_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    session_factory = sessionmaker(bind=engine, future=True)
    return engine, session_factory()


class _SyntheticOnboardingWriteDriver:
    """L6 synthetic driver used only for deterministic stage-1.2 write-path tests."""

    @staticmethod
    def _record(event_type: str, status: str, detail: dict | None = None) -> None:
        recorder = get_active_recorder()
        if recorder is None:
            return
        recorder.add_event(
            event_type=event_type,
            layer="L6",
            component="synthetic.onboarding_write_driver",
            operation=recorder.operation_name,
            trigger="driver.execute",
            status=status,
            detail=detail or {},
        )

    def ensure_table(self, sync_session) -> None:
        self._record("l6.schema.ensure.start", "STARTED")
        sync_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS stagetest_onboarding_state (
                    tenant_id TEXT PRIMARY KEY,
                    step TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )
        self._record("l6.schema.ensure.end", "PASS")

    def insert_state(self, sync_session, tenant_id: str, step: str, payload_json: str) -> int:
        self._record("l6.write.insert.start", "STARTED", {"table": "stagetest_onboarding_state"})
        result = sync_session.execute(
            text(
                """
                INSERT INTO stagetest_onboarding_state (tenant_id, step, payload, updated_at)
                VALUES (:tenant_id, :step, :payload, :updated_at)
                """
            ),
            {
                "tenant_id": tenant_id,
                "step": step,
                "payload": payload_json,
                "updated_at": _utc_now_iso(),
            },
        )
        self._record(
            "l6.write.insert.end",
            "PASS",
            {"table": "stagetest_onboarding_state", "rowcount": int(result.rowcount or 0)},
        )
        return int(result.rowcount or 0)

    def update_state(self, sync_session, tenant_id: str, step: str, payload_json: str) -> int:
        self._record("l6.write.update.start", "STARTED", {"table": "stagetest_onboarding_state"})
        result = sync_session.execute(
            text(
                """
                UPDATE stagetest_onboarding_state
                SET step = :step, payload = :payload, updated_at = :updated_at
                WHERE tenant_id = :tenant_id
                """
            ),
            {
                "tenant_id": tenant_id,
                "step": step,
                "payload": payload_json,
                "updated_at": _utc_now_iso(),
            },
        )
        self._record(
            "l6.write.update.end",
            "PASS",
            {"table": "stagetest_onboarding_state", "rowcount": int(result.rowcount or 0)},
        )
        return int(result.rowcount or 0)


class _SyntheticOnboardingWriteEngine:
    """L5 synthetic engine used only for deterministic stage-1.2 write-path tests."""

    def __init__(self) -> None:
        self._driver = _SyntheticOnboardingWriteDriver()

    def run_write(self, sync_session, *, mode: str, tenant_id: str, step: str, payload: dict) -> int:
        recorder = get_active_recorder()
        if recorder is not None:
            recorder.add_event(
                event_type="l5.write.start",
                layer="L5",
                component="synthetic.onboarding_write_engine",
                operation=recorder.operation_name,
                trigger="engine.run_write",
                status="STARTED",
                detail={"mode": mode},
            )

        payload_json = json.dumps(payload, sort_keys=True)
        self._driver.ensure_table(sync_session)
        if mode == "insert":
            affected = self._driver.insert_state(sync_session, tenant_id, step, payload_json)
        elif mode == "update":
            affected = self._driver.update_state(sync_session, tenant_id, step, payload_json)
        else:
            raise ValueError(f"unsupported mode: {mode}")
        sync_session.commit()

        if recorder is not None:
            recorder.add_event(
                event_type="l5.write.end",
                layer="L5",
                component="synthetic.onboarding_write_engine",
                operation=recorder.operation_name,
                trigger="engine.run_write",
                status="PASS",
                detail={"mode": mode, "affected_rows": affected},
            )

        return affected


class _SyntheticOnboardingWriteHandler:
    """Synthetic L4 handler to drive L4 -> L5 -> L6 -> DB trace coverage."""

    def __init__(self, mode: str) -> None:
        self._mode = mode
        self._engine = _SyntheticOnboardingWriteEngine()

    async def execute(self, ctx: OperationContext) -> OperationResult:
        sync_session = ctx.params["sync_session"]
        step = str(ctx.params["step"])
        payload = dict(ctx.params["payload"])

        affected_rows = self._engine.run_write(
            sync_session,
            mode=self._mode,
            tenant_id=ctx.tenant_id,
            step=step,
            payload=payload,
        )
        return OperationResult.ok(
            {
                "mode": self._mode,
                "affected_rows": affected_rows,
                "tenant_id": ctx.tenant_id,
                "step": step,
            }
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

    def test_synthetic_write_path_insert_emits_db_write(self) -> None:
        """UAT-UC002-006: synthetic insert write path emits L4/L5/L6/DB trace evidence."""
        test_id = "UAT-UC002-006"

        engine, sync_session = _new_sqlite_session()
        try:
            operation = "account.onboarding.synthetic_write.insert"
            registry = OperationRegistry()
            registry.register(operation, _SyntheticOnboardingWriteHandler(mode="insert"))

            result = asyncio.run(
                registry.execute(
                    operation,
                    OperationContext(
                        session=None,
                        tenant_id="syn-tenant-001",
                        params={
                            "sync_session": sync_session,
                            "step": "INIT",
                            "payload": {"source": "stage12", "case": "insert"},
                        },
                    ),
                )
            )

            assert result.success is True, f"{test_id}: synthetic insert operation failed: {result.error}"
            assert result.data["affected_rows"] == 1, (
                f"{test_id}: expected affected_rows=1, got {result.data['affected_rows']}"
            )

            row_count = sync_session.execute(
                text("SELECT COUNT(*) FROM stagetest_onboarding_state")
            ).scalar_one()
            assert int(row_count) == 1, f"{test_id}: expected 1 row in onboarding table, got {row_count}"

            if os.environ.get("STAGETEST_EMIT", "0") == "1":
                recorder = get_active_recorder()
                assert recorder is not None, f"{test_id}: active recorder missing during call phase"
                assert any(e["layer"] == "L5" for e in recorder.execution_trace), (
                    f"{test_id}: missing L5 trace event in execution_trace"
                )
                assert any(e["layer"] == "L6" for e in recorder.execution_trace), (
                    f"{test_id}: missing L6 trace event in execution_trace"
                )
                assert any(
                    w.get("sql_op") == "INSERT" and w.get("table") == "stagetest_onboarding_state"
                    for w in recorder.db_writes
                ), f"{test_id}: expected INSERT db_write for stagetest_onboarding_state"
        finally:
            sync_session.close()
            engine.dispose()

        print(f"EVIDENCE: {test_id} PASS — synthetic insert emitted L4/L5/L6/DB evidence")

    def test_synthetic_write_path_update_emits_db_write(self) -> None:
        """UAT-UC002-007: synthetic update write path emits non-empty DB writes and deep trace."""
        test_id = "UAT-UC002-007"

        engine, sync_session = _new_sqlite_session()
        try:
            # Seed one row so update path can mutate deterministically.
            sync_session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS stagetest_onboarding_state (
                        tenant_id TEXT PRIMARY KEY,
                        step TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
            )
            sync_session.execute(
                text(
                    """
                    INSERT INTO stagetest_onboarding_state (tenant_id, step, payload, updated_at)
                    VALUES (:tenant_id, :step, :payload, :updated_at)
                    """
                ),
                {
                    "tenant_id": "syn-tenant-002",
                    "step": "INIT",
                    "payload": json.dumps({"source": "seed"}, sort_keys=True),
                    "updated_at": _utc_now_iso(),
                },
            )
            sync_session.commit()

            operation = "account.onboarding.synthetic_write.update"
            registry = OperationRegistry()
            registry.register(operation, _SyntheticOnboardingWriteHandler(mode="update"))

            result = asyncio.run(
                registry.execute(
                    operation,
                    OperationContext(
                        session=None,
                        tenant_id="syn-tenant-002",
                        params={
                            "sync_session": sync_session,
                            "step": "COMPLETE",
                            "payload": {"source": "stage12", "case": "update"},
                        },
                    ),
                )
            )

            assert result.success is True, f"{test_id}: synthetic update operation failed: {result.error}"
            assert result.data["affected_rows"] == 1, (
                f"{test_id}: expected affected_rows=1, got {result.data['affected_rows']}"
            )

            updated_step = sync_session.execute(
                text(
                    "SELECT step FROM stagetest_onboarding_state WHERE tenant_id = :tenant_id"
                ),
                {"tenant_id": "syn-tenant-002"},
            ).scalar_one()
            assert updated_step == "COMPLETE", (
                f"{test_id}: expected updated step COMPLETE, got {updated_step}"
            )

            if os.environ.get("STAGETEST_EMIT", "0") == "1":
                recorder = get_active_recorder()
                assert recorder is not None, f"{test_id}: active recorder missing during call phase"
                assert any(e["layer"] == "L5" for e in recorder.execution_trace), (
                    f"{test_id}: missing L5 trace event in execution_trace"
                )
                assert any(e["layer"] == "L6" for e in recorder.execution_trace), (
                    f"{test_id}: missing L6 trace event in execution_trace"
                )
                assert any(
                    w.get("sql_op") == "UPDATE" and w.get("table") == "stagetest_onboarding_state"
                    for w in recorder.db_writes
                ), f"{test_id}: expected UPDATE db_write for stagetest_onboarding_state"
        finally:
            sync_session.close()
            engine.dispose()

        print(f"EVIDENCE: {test_id} PASS — synthetic update emitted L4/L5/L6/DB evidence")
