# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: Trace API domain logic (store/query/compare orchestration)
# Callers: L4 logs handler (logs.traces_api)
# Allowed Imports: L5, L6 (drivers), stdlib
# Forbidden Imports: L1, L2, DB/ORM
# Reference: PIN-553 (trace store migration)

from typing import Any, Optional

from app.hoc.cus.logs.L6_drivers.redact import redact_trace_data


class TraceApiEngine:
    """Trace API orchestration over trace store capability."""

    def __init__(self, trace_store: Any) -> None:
        self._store = trace_store

    async def list_traces(
        self,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        root_hash: Optional[str] = None,
        plan_hash: Optional[str] = None,
        seed: Optional[int] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        traces = await self._store.search_traces(
            tenant_id=tenant_id,
            agent_id=agent_id,
            root_hash=root_hash,
            plan_hash=plan_hash,
            seed=seed,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
        total = await self._store.get_trace_count(tenant_id)
        return {"traces": traces, "total": total}

    async def store_trace(
        self,
        trace: dict[str, Any],
        tenant_id: str,
        stored_by: Optional[str],
        use_postgres: bool,
        *,
        replay_mode: Optional[str] = None,
        replay_attempt_id: Optional[str] = None,
        replay_artifact_version: Optional[str] = None,
        trace_completeness_status: Optional[str] = None,
    ) -> dict[str, Any]:
        redacted_trace = redact_trace_data(trace)

        if use_postgres:
            trace_id = await self._store.store_trace(
                trace=redacted_trace,
                tenant_id=tenant_id,
                stored_by=stored_by,
                redact_pii=False,
                replay_mode=replay_mode,
                replay_attempt_id=replay_attempt_id,
                replay_artifact_version=replay_artifact_version,
                trace_completeness_status=trace_completeness_status,
            )
        else:
            run_id = redacted_trace.get("run_id") or redacted_trace.get("trace_id")
            await self._store.start_trace(
                run_id=run_id,
                correlation_id=redacted_trace.get("correlation_id", run_id),
                tenant_id=tenant_id,
                agent_id=redacted_trace.get("agent_id"),
                plan=redacted_trace.get("plan", []),
            )
            trace_id = run_id

        return {
            "trace_id": trace_id,
            "root_hash": redacted_trace.get("root_hash"),
            "stored": True,
            "replay_mode": replay_mode,
        }

    async def get_trace(
        self,
        run_id: str,
        tenant_id: Optional[str] = None,
    ) -> Any:
        if tenant_id is None:
            return await self._store.get_trace(run_id)
        try:
            return await self._store.get_trace(run_id, tenant_id=tenant_id)
        except TypeError:
            return await self._store.get_trace(run_id)

    async def get_trace_by_root_hash(
        self,
        root_hash: str,
        tenant_id: Optional[str] = None,
    ) -> Any:
        if tenant_id is None:
            return await self._store.get_trace_by_root_hash(root_hash)
        try:
            return await self._store.get_trace_by_root_hash(root_hash, tenant_id=tenant_id)
        except TypeError:
            return await self._store.get_trace_by_root_hash(root_hash)

    async def compare_traces(self, run_id1: str, run_id2: str) -> dict[str, Any]:
        trace1 = await self._store.get_trace(run_id1)
        trace2 = await self._store.get_trace(run_id2)
        return {"trace1": trace1, "trace2": trace2}

    async def delete_trace(
        self,
        run_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        if tenant_id is None:
            return await self._store.delete_trace(run_id)
        try:
            return await self._store.delete_trace(run_id, tenant_id=tenant_id)
        except TypeError:
            return await self._store.delete_trace(run_id)

    async def cleanup_old_traces(self, days: int = 30) -> int:
        return await self._store.cleanup_old_traces(days)

    async def check_idempotency(
        self,
        idempotency_key: str,
        tenant_id: str,
    ) -> Any:
        return await self._store.check_idempotency_key(idempotency_key, tenant_id)


def get_trace_api_engine(trace_store: Any) -> TraceApiEngine:
    return TraceApiEngine(trace_store)
