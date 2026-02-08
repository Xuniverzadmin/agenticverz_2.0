# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: DB I/O for retrieval evidence (append-only)
# Callers: hoc_spine retrieval mediation
# Allowed Imports: sqlmodel/sqlalchemy only
# Forbidden Imports: hoc_spine orchestrator, L2 routes
# Reference: GAP-058, DRIVER_ENGINE_PATTERN_LOCKED.md

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.retrieval_evidence import RetrievalEvidence


class RetrievalEvidenceDriver:
    """Append-only retrieval evidence writer."""

    async def append(
        self,
        session: AsyncSession,
        *,
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
        completed_at: Optional[datetime],
        duration_ms: Optional[int],
    ) -> RetrievalEvidence:
        record = RetrievalEvidence(
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
        session.add(record)
        await session.flush()
        return record


__all__ = ["RetrievalEvidenceDriver"]

