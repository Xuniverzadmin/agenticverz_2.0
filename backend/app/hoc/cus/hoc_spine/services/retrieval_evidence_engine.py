# Layer: L4 — HOC Spine (Engine)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api|worker (mediated retrieval)
#   Execution: async
# Lifecycle:
#   Emits: retrieval_evidence (append-only)
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: retrieval_evidence table
# Role: DB-backed evidence recording for RetrievalMediator (Phase 4)
# Callers: hoc_spine RetrievalMediator wiring
# Allowed Imports: hoc_spine drivers, hoc_spine orchestrator session context
# Forbidden Imports: L2 routes

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import RetrievalEvidenceDriver
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_async_session_context


class DbRetrievalEvidenceService:
    """
    EvidenceService implementation that persists evidence to Postgres.

    Contract:
    - append-only (DB trigger prevents UPDATE/DELETE)
    - single write contains requested_at/completed_at/duration_ms
    """

    def __init__(self, driver: Optional[RetrievalEvidenceDriver] = None) -> None:
        self._driver = driver or RetrievalEvidenceDriver()

    async def record(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        connector_id: str,
        action: str,
        query_hash: str,
        doc_ids: List[str],
        token_count: int,
        policy_snapshot_id: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
        duration_ms: Optional[int],
    ):
        from app.hoc.cus.hoc_spine.services.retrieval_mediator import EvidenceRecord

        async with get_async_session_context() as session:
            async with session.begin():
                record = await self._driver.append(
                    session,
                    tenant_id=tenant_id,
                    run_id=run_id,
                    plane_id=plane_id,
                    connector_id=connector_id,
                    action=action,
                    query_hash=query_hash,
                    doc_ids=doc_ids,
                    token_count=token_count,
                    policy_snapshot_id=policy_snapshot_id,
                    requested_at=requested_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )

        return EvidenceRecord(
            id=record.id,
            tenant_id=record.tenant_id,
            run_id=record.run_id,
            plane_id=record.plane_id,
            connector_id=record.connector_id,
            action=record.action,
            query_hash=record.query_hash,
            doc_ids=record.doc_ids,
            token_count=record.token_count,
            policy_snapshot_id=record.policy_snapshot_id,
            requested_at=record.requested_at.isoformat(),
            completed_at=record.completed_at.isoformat() if record.completed_at else None,
            duration_ms=record.duration_ms,
        )


_evidence_service: Optional[DbRetrievalEvidenceService] = None


def get_db_retrieval_evidence_service() -> DbRetrievalEvidenceService:
    global _evidence_service
    if _evidence_service is None:
        _evidence_service = DbRetrievalEvidenceService()
    return _evidence_service


__all__ = ["DbRetrievalEvidenceService", "get_db_retrieval_evidence_service"]

