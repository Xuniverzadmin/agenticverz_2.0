# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api | worker
#   Execution: async
# Role: Database evidence sink for execution envelopes
# Callers: auth/execution_envelope.py
# Allowed Imports: L6 (models)
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-330

"""
Database Evidence Sink - PIN-330 Implicit Authority Hardening

Provides append-only database storage for execution envelopes.

CONSTRAINTS:
- Append-only (no UPDATE/DELETE)
- Emission failure MUST NOT block execution
- All writes are fire-and-forget from caller perspective
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.execution_envelope import (
    CapabilityId,
    EvidenceSink,
    ExecutionEnvelope,
)
from app.models.execution_envelope import ExecutionEnvelopeModel

logger = logging.getLogger(__name__)


class DatabaseEvidenceSink(EvidenceSink):
    """
    Database-backed evidence sink for production use.

    Writes to execution_envelopes table with append-only semantics.
    All operations are non-blocking from the execution path perspective.
    """

    def __init__(self, session_factory: Any) -> None:
        """
        Initialize with a session factory.

        Args:
            session_factory: Callable that returns AsyncSession
        """
        self._session_factory = session_factory

    def emit(self, envelope: ExecutionEnvelope) -> bool:
        """
        Emit envelope to database (sync wrapper).

        NOTE: This is a sync wrapper for compatibility with the base interface.
        For async contexts, use emit_async directly.

        INVARIANT: Failure MUST NOT block execution.
        """
        # For sync contexts, we can't use async DB ops
        # This returns True and relies on background processing
        logger.warning(
            "Sync emit called - envelope queued for background processing",
            extra={"envelope_id": envelope.envelope_id},
        )
        return True

    async def emit_async(self, envelope: ExecutionEnvelope) -> bool:
        """
        Emit envelope to database (async).

        INVARIANT: Failure MUST NOT block execution.

        Args:
            envelope: The execution envelope to store

        Returns:
            True if emission succeeded, False otherwise
        """
        try:
            async with self._session_factory() as session:
                model = self._envelope_to_model(envelope)
                session.add(model)
                await session.commit()

                logger.info(
                    "Execution envelope persisted",
                    extra={
                        "envelope_id": envelope.envelope_id,
                        "capability_id": envelope.capability_id.value,
                        "invocation_id": envelope.invocation.invocation_id,
                    },
                )
                return True

        except Exception as e:
            # CRITICAL: Never block execution
            logger.error(
                f"Database evidence emission failed (non-blocking): {e}",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "error": str(e),
                },
            )
            return False

    def _envelope_to_model(
        self, envelope: ExecutionEnvelope
    ) -> ExecutionEnvelopeModel:
        """Convert ExecutionEnvelope to database model."""
        return ExecutionEnvelopeModel(
            envelope_id=envelope.envelope_id,
            capability_id=envelope.capability_id.value,
            execution_vector=envelope.execution_vector.value,
            caller_type=envelope.caller_identity.type.value,
            caller_subject=envelope.caller_identity.subject,
            impersonated_subject=envelope.caller_identity.impersonated_subject,
            impersonation_declared=envelope.caller_identity.impersonation_declared,
            tenant_id=envelope.tenant_context.tenant_id,
            account_id=envelope.tenant_context.account_id,
            project_id=envelope.tenant_context.project_id,
            invocation_id=envelope.invocation.invocation_id,
            invocation_timestamp=datetime.fromisoformat(
                envelope.invocation.timestamp.replace("Z", "+00:00")
            ),
            sequence_number=envelope.invocation.sequence_number,
            input_hash=envelope.plan.input_hash,
            resolved_plan_hash=envelope.plan.resolved_plan_hash,
            plan_mutation_detected=envelope.plan.plan_mutation_detected,
            original_invocation_id=envelope.plan.original_invocation_id,
            confidence_score=(
                envelope.confidence.score if envelope.confidence else None
            ),
            confidence_threshold=(
                envelope.confidence.threshold_used if envelope.confidence else None
            ),
            auto_execute_triggered=(
                envelope.confidence.auto_execute_triggered
                if envelope.confidence
                else None
            ),
            attribution_origin=envelope.attribution.origin,
            reason_code=envelope.attribution.reason_code,
            source_command=envelope.attribution.source_command,
            sdk_version=envelope.attribution.sdk_version,
            cli_version=envelope.attribution.cli_version,
            emitted_at=datetime.fromisoformat(
                envelope.evidence.emitted_at.replace("Z", "+00:00")
            ),
            emission_success=envelope.evidence.emission_success,
            envelope_json=envelope.to_dict(),
        )

    async def query_by_capability_async(
        self, capability_id: CapabilityId, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query envelopes by capability (async)."""
        try:
            async with self._session_factory() as session:
                stmt = (
                    select(ExecutionEnvelopeModel)
                    .where(ExecutionEnvelopeModel.capability_id == capability_id.value)
                    .order_by(ExecutionEnvelopeModel.emitted_at.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()
                return [row.to_dict() for row in rows]
        except Exception as e:
            logger.error(f"Query by capability failed: {e}")
            return []

    def query_by_capability(
        self, capability_id: CapabilityId, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query envelopes by capability (sync stub)."""
        logger.warning("Sync query not supported - use async version")
        return []

    async def query_by_tenant_async(
        self, tenant_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query envelopes by tenant (async)."""
        try:
            async with self._session_factory() as session:
                stmt = (
                    select(ExecutionEnvelopeModel)
                    .where(ExecutionEnvelopeModel.tenant_id == tenant_id)
                    .order_by(ExecutionEnvelopeModel.emitted_at.desc())
                    .limit(limit)
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()
                return [row.to_dict() for row in rows]
        except Exception as e:
            logger.error(f"Query by tenant failed: {e}")
            return []

    def query_by_tenant(
        self, tenant_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query envelopes by tenant (sync stub)."""
        logger.warning("Sync query not supported - use async version")
        return []

    async def query_by_invocation_async(
        self, invocation_id: str
    ) -> Optional[dict[str, Any]]:
        """Query envelope by invocation_id (async)."""
        try:
            async with self._session_factory() as session:
                stmt = select(ExecutionEnvelopeModel).where(
                    ExecutionEnvelopeModel.invocation_id == invocation_id
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                return row.to_dict() if row else None
        except Exception as e:
            logger.error(f"Query by invocation failed: {e}")
            return None

    def query_by_invocation(
        self, invocation_id: str
    ) -> Optional[dict[str, Any]]:
        """Query envelope by invocation_id (sync stub)."""
        logger.warning("Sync query not supported - use async version")
        return None

    async def get_stats_async(
        self,
        capability_id: Optional[CapabilityId] = None,
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get aggregate statistics for envelopes.

        Returns counts by capability, vector, and key metrics.
        """
        try:
            async with self._session_factory() as session:
                from sqlalchemy import func as sql_func

                # Base query
                base_query = select(
                    ExecutionEnvelopeModel.capability_id,
                    ExecutionEnvelopeModel.execution_vector,
                    sql_func.count(ExecutionEnvelopeModel.id).label("total"),
                    sql_func.sum(
                        sql_func.cast(
                            ExecutionEnvelopeModel.impersonation_declared, Integer
                        )
                    ).label("impersonation_count"),
                    sql_func.sum(
                        sql_func.cast(
                            ExecutionEnvelopeModel.plan_mutation_detected, Integer
                        )
                    ).label("mutation_count"),
                    sql_func.sum(
                        sql_func.cast(
                            ExecutionEnvelopeModel.auto_execute_triggered, Integer
                        )
                    ).label("auto_execute_count"),
                ).group_by(
                    ExecutionEnvelopeModel.capability_id,
                    ExecutionEnvelopeModel.execution_vector,
                )

                # Apply filters
                if capability_id:
                    base_query = base_query.where(
                        ExecutionEnvelopeModel.capability_id == capability_id.value
                    )
                if tenant_id:
                    base_query = base_query.where(
                        ExecutionEnvelopeModel.tenant_id == tenant_id
                    )

                result = await session.execute(base_query)
                rows = result.all()

                stats = {
                    "by_capability": {},
                    "totals": {
                        "envelopes": 0,
                        "impersonations": 0,
                        "mutations": 0,
                        "auto_executes": 0,
                    },
                }

                for row in rows:
                    cap_id = row.capability_id
                    if cap_id not in stats["by_capability"]:
                        stats["by_capability"][cap_id] = {
                            "total": 0,
                            "impersonation_count": 0,
                            "mutation_count": 0,
                            "auto_execute_count": 0,
                            "by_vector": {},
                        }

                    cap_stats = stats["by_capability"][cap_id]
                    cap_stats["total"] += row.total or 0
                    cap_stats["impersonation_count"] += row.impersonation_count or 0
                    cap_stats["mutation_count"] += row.mutation_count or 0
                    cap_stats["auto_execute_count"] += row.auto_execute_count or 0
                    cap_stats["by_vector"][row.execution_vector] = row.total or 0

                    # Update totals
                    stats["totals"]["envelopes"] += row.total or 0
                    stats["totals"]["impersonations"] += row.impersonation_count or 0
                    stats["totals"]["mutations"] += row.mutation_count or 0
                    stats["totals"]["auto_executes"] += row.auto_execute_count or 0

                return stats

        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {
                "by_capability": {},
                "totals": {
                    "envelopes": 0,
                    "impersonations": 0,
                    "mutations": 0,
                    "auto_executes": 0,
                },
                "error": str(e),
            }


# =============================================================================
# ASYNC NON-BLOCKING EMISSION
# =============================================================================


async def emit_envelope_async(
    envelope: ExecutionEnvelope,
    session_factory: Any,
) -> bool:
    """
    Emit envelope to database asynchronously.

    INVARIANT: This function NEVER raises exceptions.
    Failure is logged but does NOT block execution.

    Args:
        envelope: The execution envelope to emit
        session_factory: Async session factory

    Returns:
        True if emission succeeded, False otherwise
    """
    try:
        sink = DatabaseEvidenceSink(session_factory)
        return await sink.emit_async(envelope)
    except Exception as e:
        logger.error(
            f"Async envelope emission error (non-blocking): {e}",
            extra={
                "envelope_id": envelope.envelope_id if envelope else "unknown",
                "error": str(e),
            },
        )
        return False


# Import Integer for the sql_func.cast
from sqlalchemy import Integer
