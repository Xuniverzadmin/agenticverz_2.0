# Layer: L4 — Test Utility
# AUDIENCE: INTERNAL
# Role: Deterministic runtime trace and DB-write capture for stagetest artifacts
# artifact_class: CODE
"""
Stagetest Runtime Trace Capture

Provides lightweight, deterministic capture primitives for UAT case execution:
- execution_trace: ordered sequence of events and layer transitions
- db_writes: observed SQL DML write operations (INSERT/UPDATE/DELETE/MERGE)

Capture is test-scoped via contextvars and is safe when no DB/runtime activity
occurs (empty db_writes, minimal execution_trace).
"""

from __future__ import annotations

import contextvars
import hashlib
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_ACTIVE_RECORDER: contextvars.ContextVar["CaseRecorder | None"] = contextvars.ContextVar(
    "stagetest_active_recorder",
    default=None,
)
_HOOKS_LOCK = threading.Lock()
_HOOKS_INSTALLED = False

_SQL_OP_RE = re.compile(r"^\s*(INSERT|UPDATE|DELETE|MERGE)\b", re.IGNORECASE)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_sql(statement: str) -> str:
    return " ".join(statement.split())


def _extract_sql_write(statement: str) -> tuple[str | None, str | None]:
    normalized = _normalize_sql(statement)
    match = _SQL_OP_RE.match(normalized)
    if not match:
        return None, None

    op = match.group(1).upper()
    table = "unknown"

    if op == "INSERT":
        t = re.search(r"\bINTO\s+([A-Za-z0-9_\"`\.\[\]]+)", normalized, re.IGNORECASE)
        if t:
            table = t.group(1)
    elif op == "UPDATE":
        t = re.search(r"^\s*UPDATE\s+([A-Za-z0-9_\"`\.\[\]]+)", normalized, re.IGNORECASE)
        if t:
            table = t.group(1)
    elif op == "DELETE":
        t = re.search(r"\bFROM\s+([A-Za-z0-9_\"`\.\[\]]+)", normalized, re.IGNORECASE)
        if t:
            table = t.group(1)
    elif op == "MERGE":
        t = re.search(r"\bINTO\s+([A-Za-z0-9_\"`\.\[\]]+)", normalized, re.IGNORECASE)
        if t:
            table = t.group(1)

    table = table.strip('`"[]')
    return op, table


@dataclass
class CaseRecorder:
    case_id: str
    uc_id: str
    operation_name: str
    _seq: int = 0
    execution_trace: list[dict[str, Any]] = field(default_factory=list)
    db_writes: list[dict[str, Any]] = field(default_factory=list)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def add_event(
        self,
        *,
        event_type: str,
        layer: str,
        component: str,
        operation: str,
        trigger: str,
        status: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.execution_trace.append(
            {
                "seq": self._next_seq(),
                "ts_utc": _utc_now(),
                "event_type": event_type,
                "layer": layer,
                "component": component,
                "operation": operation,
                "trigger": trigger,
                "status": status,
                "detail": detail or {},
            }
        )

    def add_db_write(
        self,
        *,
        layer: str,
        component: str,
        operation: str,
        table: str,
        sql_op: str,
        rowcount: int,
        statement_fingerprint: str,
        success: bool,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.db_writes.append(
            {
                "seq": self._next_seq(),
                "ts_utc": _utc_now(),
                "layer": layer,
                "component": component,
                "operation": operation,
                "table": table,
                "sql_op": sql_op,
                "rowcount": rowcount,
                "statement_fingerprint": statement_fingerprint,
                "success": success,
                "detail": detail or {},
            }
        )


def get_active_recorder() -> CaseRecorder | None:
    return _ACTIVE_RECORDER.get()


def start_case_capture(case_id: str, uc_id: str, operation_name: str) -> None:
    recorder = CaseRecorder(case_id=case_id, uc_id=uc_id, operation_name=operation_name)
    recorder.add_event(
        event_type="test.start",
        layer="TEST",
        component="pytest",
        operation=operation_name,
        trigger="pytest_runtest_setup",
        status="STARTED",
        detail={"case_id": case_id, "uc_id": uc_id},
    )
    _ACTIVE_RECORDER.set(recorder)


def finish_case_capture(status: str, detail: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recorder = get_active_recorder()
    if recorder is None:
        return [], []

    recorder.add_event(
        event_type="test.end",
        layer="TEST",
        component="pytest",
        operation=recorder.operation_name,
        trigger="pytest_runtest_makereport",
        status=status,
        detail=detail or {},
    )
    _ACTIVE_RECORDER.set(None)
    return recorder.execution_trace, recorder.db_writes


def _install_operation_registry_hook() -> None:
    try:
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import OperationRegistry
    except Exception:
        return

    if getattr(OperationRegistry.execute, "_stagetest_trace_wrapped", False):
        return

    original_execute = OperationRegistry.execute

    async def wrapped_execute(self, operation, ctx):  # type: ignore[no-untyped-def]
        recorder = get_active_recorder()
        started = time.monotonic()
        if recorder is not None:
            recorder.add_event(
                event_type="dispatch.start",
                layer="L4",
                component="OperationRegistry",
                operation=str(operation),
                trigger="registry.execute",
                status="STARTED",
                detail={"tenant_id": getattr(ctx, "tenant_id", "")},
            )

        try:
            result = await original_execute(self, operation, ctx)
        except Exception as exc:
            recorder = get_active_recorder()
            if recorder is not None:
                recorder.add_event(
                    event_type="dispatch.error",
                    layer="L4",
                    component="OperationRegistry",
                    operation=str(operation),
                    trigger="registry.execute",
                    status="ERROR",
                    detail={"error": str(exc), "error_type": type(exc).__name__},
                )
            raise

        recorder = get_active_recorder()
        if recorder is not None:
            success = bool(getattr(result, "success", True))
            recorder.add_event(
                event_type="dispatch.end",
                layer="L4",
                component="OperationRegistry",
                operation=str(operation),
                trigger="registry.execute",
                status="PASS" if success else "FAIL",
                detail={
                    "duration_ms": round((time.monotonic() - started) * 1000, 3),
                    "error_code": getattr(result, "error_code", None),
                },
            )
        return result

    setattr(wrapped_execute, "_stagetest_trace_wrapped", True)
    OperationRegistry.execute = wrapped_execute  # type: ignore[assignment]


def _install_sqlalchemy_hooks() -> None:
    try:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
    except Exception:
        return

    if getattr(Engine, "_stagetest_trace_sql_hooks", False):
        return

    @event.listens_for(Engine, "before_cursor_execute")
    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        op, table = _extract_sql_write(statement or "")
        if not op:
            return
        context._stagetest_write_capture = {
            "op": op,
            "table": table or "unknown",
            "statement": _normalize_sql(statement or ""),
            "started": time.monotonic(),
        }

    @event.listens_for(Engine, "after_cursor_execute")
    def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
        recorder = get_active_recorder()
        if recorder is None:
            return

        meta = getattr(context, "_stagetest_write_capture", None)
        if not isinstance(meta, dict):
            return

        statement_norm = meta.get("statement", "")
        fingerprint = hashlib.sha256(statement_norm.encode("utf-8")).hexdigest()[:16]
        started = float(meta.get("started", time.monotonic()))
        duration_ms = round((time.monotonic() - started) * 1000, 3)

        rowcount = -1
        try:
            rc = getattr(cursor, "rowcount", -1)
            rowcount = int(rc) if rc is not None else -1
        except Exception:
            rowcount = -1

        recorder.add_db_write(
            layer="DB",
            component="sqlalchemy.Engine",
            operation=recorder.operation_name,
            table=str(meta.get("table", "unknown")),
            sql_op=str(meta.get("op", "UNKNOWN")),
            rowcount=rowcount,
            statement_fingerprint=fingerprint,
            success=True,
            detail={"duration_ms": duration_ms},
        )
        recorder.add_event(
            event_type="db.write",
            layer="DB",
            component="sqlalchemy.Engine",
            operation=recorder.operation_name,
            trigger="sqlalchemy.after_cursor_execute",
            status="PASS",
            detail={
                "sql_op": str(meta.get("op", "UNKNOWN")),
                "table": str(meta.get("table", "unknown")),
                "rowcount": rowcount,
                "duration_ms": duration_ms,
            },
        )
        setattr(context, "_stagetest_write_capture", None)

    setattr(Engine, "_stagetest_trace_sql_hooks", True)


def install_runtime_hooks() -> None:
    global _HOOKS_INSTALLED
    with _HOOKS_LOCK:
        if _HOOKS_INSTALLED:
            return
        _install_operation_registry_hook()
        _install_sqlalchemy_hooks()
        _HOOKS_INSTALLED = True
