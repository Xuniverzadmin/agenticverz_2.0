# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Business logic for customer LLM telemetry ingestion and querying
# Callers: cus_telemetry.py API
# Allowed Imports: L5, L6 (cus_models, database)
# Forbidden Imports: L1, L2, L3
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer LLM Telemetry Service

PURPOSE:
    Domain engine for telemetry data. Handles:
    - Ingesting individual and batch LLM usage records
    - Idempotency checking via call_id
    - Usage aggregation and summary computation
    - Daily aggregate management

SEMANTIC:
    This service owns the DATA PLANE for customer integrations.
    It records FACTS about what happened - append-only by design.

INVARIANTS:
    - Telemetry records are never updated once created
    - call_id provides idempotency (duplicates silently ignored)
    - All queries are tenant-scoped
    - Daily aggregates are derived and can be regenerated
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import func, select, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.cus_models import (
    CusIntegration,
    CusLLMUsage,
    CusPolicyResult,
    CusUsageDaily,
)
from app.schemas.cus_schemas import (
    CusIntegrationUsage,
    CusLLMUsageIngest,
    CusLLMUsageResponse,
    CusUsageSummary,
)


def utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class CusTelemetryService:
    """Service for customer LLM telemetry operations.

    This service provides:
    - Telemetry ingestion (single and batch)
    - Usage summaries and aggregations
    - History queries with pagination

    All operations are tenant-scoped for isolation.
    """

    # =========================================================================
    # INGESTION
    # =========================================================================

    async def ingest_usage(
        self,
        tenant_id: str,
        integration_id: str,
        payload: CusLLMUsageIngest,
    ) -> Dict[str, Any]:
        """Ingest a single LLM usage record.

        Args:
            tenant_id: Tenant owning this data
            integration_id: Integration that made the call
            payload: Telemetry data

        Returns:
            Dict with ingestion result:
            - status: "accepted" or "duplicate"
            - id: Record ID (if accepted)

        IDEMPOTENCY:
            If call_id already exists, returns "duplicate" status
            without error. This supports at-least-once delivery.
        """
        async for session in get_async_session():
            # Check for existing call_id (idempotency)
            existing = await session.execute(
                select(CusLLMUsage.id).where(CusLLMUsage.call_id == payload.call_id)
            )
            if existing.scalar_one_or_none():
                return {"status": "duplicate", "call_id": payload.call_id}

            # Validate integration exists and belongs to tenant
            integration = await session.execute(
                select(CusIntegration).where(
                    and_(
                        CusIntegration.id == integration_id,
                        CusIntegration.tenant_id == tenant_id,
                        CusIntegration.deleted_at.is_(None),
                    )
                )
            )
            if not integration.scalar_one_or_none():
                raise ValueError(f"Integration {integration_id} not found for tenant")

            # Create usage record
            record = CusLLMUsage(
                id=str(uuid4()),
                tenant_id=tenant_id,
                integration_id=integration_id,
                session_id=payload.session_id,
                agent_id=payload.agent_id,
                call_id=payload.call_id,
                provider=payload.provider,
                model=payload.model,
                tokens_in=payload.tokens_in,
                tokens_out=payload.tokens_out,
                cost_cents=payload.cost_cents,
                latency_ms=payload.latency_ms,
                policy_result=payload.policy_result,
                error_code=payload.error_code,
                error_message=payload.error_message,
                metadata=payload.metadata,
                created_at=utc_now(),
            )

            session.add(record)
            await session.commit()

            return {
                "status": "accepted",
                "id": record.id,
                "call_id": payload.call_id,
            }

    async def ingest_batch(
        self,
        tenant_id: str,
        default_integration_id: Optional[str],
        records: List[CusLLMUsageIngest],
    ) -> Dict[str, Any]:
        """Ingest a batch of LLM usage records.

        Args:
            tenant_id: Tenant owning this data
            default_integration_id: Default integration if not in record
            records: List of telemetry records

        Returns:
            Dict with batch result:
            - accepted: Count of new records
            - duplicates: Count of duplicate call_ids
            - errors: Count of validation errors
        """
        accepted = 0
        duplicates = 0
        errors = 0

        async for session in get_async_session():
            # Get all existing call_ids in one query
            call_ids = [r.call_id for r in records]
            existing_result = await session.execute(
                select(CusLLMUsage.call_id).where(CusLLMUsage.call_id.in_(call_ids))
            )
            existing_call_ids = set(existing_result.scalars().all())

            # Process each record
            for payload in records:
                if payload.call_id in existing_call_ids:
                    duplicates += 1
                    continue

                integration_id = payload.integration_id or default_integration_id
                if not integration_id:
                    errors += 1
                    continue

                try:
                    record = CusLLMUsage(
                        id=str(uuid4()),
                        tenant_id=tenant_id,
                        integration_id=integration_id,
                        session_id=payload.session_id,
                        agent_id=payload.agent_id,
                        call_id=payload.call_id,
                        provider=payload.provider,
                        model=payload.model,
                        tokens_in=payload.tokens_in,
                        tokens_out=payload.tokens_out,
                        cost_cents=payload.cost_cents,
                        latency_ms=payload.latency_ms,
                        policy_result=payload.policy_result,
                        error_code=payload.error_code,
                        error_message=payload.error_message,
                        metadata=payload.metadata,
                        created_at=utc_now(),
                    )
                    session.add(record)
                    accepted += 1
                except Exception:
                    errors += 1

            await session.commit()

        return {
            "accepted": accepted,
            "duplicates": duplicates,
            "errors": errors,
            "total": len(records),
        }

    # =========================================================================
    # QUERIES
    # =========================================================================

    async def get_usage_summary(
        self,
        tenant_id: str,
        integration_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> CusUsageSummary:
        """Get aggregated usage summary for a tenant.

        Args:
            tenant_id: Tenant to query
            integration_id: Optional filter for specific integration
            start_date: Period start
            end_date: Period end

        Returns:
            CusUsageSummary with aggregated metrics
        """
        async for session in get_async_session():
            # Build base query
            query = select(
                func.count(CusLLMUsage.id).label("total_calls"),
                func.sum(CusLLMUsage.tokens_in).label("total_tokens_in"),
                func.sum(CusLLMUsage.tokens_out).label("total_tokens_out"),
                func.sum(CusLLMUsage.cost_cents).label("total_cost_cents"),
                func.avg(CusLLMUsage.latency_ms).label("avg_latency_ms"),
                func.count(CusLLMUsage.id).filter(
                    CusLLMUsage.error_code.isnot(None)
                ).label("error_count"),
                func.count(CusLLMUsage.id).filter(
                    CusLLMUsage.policy_result == CusPolicyResult.BLOCKED
                ).label("blocked_count"),
            ).where(CusLLMUsage.tenant_id == tenant_id)

            # Apply filters
            if integration_id:
                query = query.where(CusLLMUsage.integration_id == integration_id)
            if start_date:
                query = query.where(CusLLMUsage.created_at >= start_date)
            if end_date:
                query = query.where(CusLLMUsage.created_at <= end_date)

            result = await session.execute(query)
            row = result.one()

            # Get per-integration breakdown if no specific integration filtered
            by_integration = None
            if not integration_id:
                by_integration = await self._get_per_integration_usage(
                    session, tenant_id, start_date, end_date
                )

            return CusUsageSummary(
                tenant_id=tenant_id,
                period_start=start_date or date.today(),
                period_end=end_date or date.today(),
                total_calls=row.total_calls or 0,
                total_tokens_in=row.total_tokens_in or 0,
                total_tokens_out=row.total_tokens_out or 0,
                total_cost_cents=row.total_cost_cents or 0,
                avg_latency_ms=int(row.avg_latency_ms) if row.avg_latency_ms else None,
                error_count=row.error_count or 0,
                blocked_count=row.blocked_count or 0,
                by_integration=by_integration,
            )

    async def _get_per_integration_usage(
        self,
        session: AsyncSession,
        tenant_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[CusIntegrationUsage]:
        """Get usage breakdown by integration."""
        query = (
            select(
                CusLLMUsage.integration_id,
                func.count(CusLLMUsage.id).label("total_calls"),
                func.sum(CusLLMUsage.tokens_in + CusLLMUsage.tokens_out).label(
                    "total_tokens"
                ),
                func.sum(CusLLMUsage.cost_cents).label("total_cost_cents"),
                func.count(CusLLMUsage.id).filter(
                    CusLLMUsage.error_code.isnot(None)
                ).label("error_count"),
            )
            .where(CusLLMUsage.tenant_id == tenant_id)
            .group_by(CusLLMUsage.integration_id)
        )

        if start_date:
            query = query.where(CusLLMUsage.created_at >= start_date)
        if end_date:
            query = query.where(CusLLMUsage.created_at <= end_date)

        result = await session.execute(query)
        rows = result.all()

        # Get integration details
        integration_ids = [r.integration_id for r in rows]
        integrations_result = await session.execute(
            select(CusIntegration).where(CusIntegration.id.in_(integration_ids))
        )
        integrations = {i.id: i for i in integrations_result.scalars().all()}

        return [
            CusIntegrationUsage(
                integration_id=row.integration_id,
                integration_name=integrations.get(row.integration_id, {}).name
                if integrations.get(row.integration_id)
                else "Unknown",
                provider_type=integrations.get(row.integration_id, {}).provider_type
                if integrations.get(row.integration_id)
                else "custom",
                total_calls=row.total_calls or 0,
                total_tokens=row.total_tokens or 0,
                total_cost_cents=row.total_cost_cents or 0,
                error_count=row.error_count or 0,
            )
            for row in rows
        ]

    async def get_usage_history(
        self,
        tenant_id: str,
        integration_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CusLLMUsageResponse], int]:
        """Get paginated usage history.

        Args:
            tenant_id: Tenant to query
            integration_id: Optional filter
            limit: Max records
            offset: Pagination offset

        Returns:
            Tuple of (records, total_count)
        """
        async for session in get_async_session():
            # Base query
            base_filter = CusLLMUsage.tenant_id == tenant_id
            if integration_id:
                base_filter = and_(
                    base_filter, CusLLMUsage.integration_id == integration_id
                )

            # Get total count
            count_result = await session.execute(
                select(func.count(CusLLMUsage.id)).where(base_filter)
            )
            total = count_result.scalar_one()

            # Get records
            query = (
                select(CusLLMUsage)
                .where(base_filter)
                .order_by(CusLLMUsage.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            records = result.scalars().all()

            return (
                [
                    CusLLMUsageResponse(
                        id=r.id,
                        integration_id=r.integration_id,
                        call_id=r.call_id,
                        session_id=r.session_id,
                        agent_id=r.agent_id,
                        provider=r.provider,
                        model=r.model,
                        tokens_in=r.tokens_in,
                        tokens_out=r.tokens_out,
                        cost_cents=r.cost_cents,
                        latency_ms=r.latency_ms,
                        policy_result=r.policy_result,
                        error_code=r.error_code,
                        error_message=r.error_message,
                        created_at=r.created_at,
                    )
                    for r in records
                ],
                total,
            )

    async def get_daily_aggregates(
        self,
        tenant_id: str,
        integration_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get daily aggregated usage for charts.

        Args:
            tenant_id: Tenant to query
            integration_id: Optional filter
            start_date: Period start
            end_date: Period end

        Returns:
            List of daily aggregate dicts
        """
        async for session in get_async_session():
            query = select(CusUsageDaily).where(CusUsageDaily.tenant_id == tenant_id)

            if integration_id:
                query = query.where(CusUsageDaily.integration_id == integration_id)
            if start_date:
                query = query.where(CusUsageDaily.date >= start_date)
            if end_date:
                query = query.where(CusUsageDaily.date <= end_date)

            query = query.order_by(CusUsageDaily.date.asc())

            result = await session.execute(query)
            records = result.scalars().all()

            return [
                {
                    "date": r.date.isoformat(),
                    "integration_id": r.integration_id,
                    "total_calls": r.total_calls,
                    "total_tokens_in": r.total_tokens_in,
                    "total_tokens_out": r.total_tokens_out,
                    "total_cost_cents": r.total_cost_cents,
                    "avg_latency_ms": r.avg_latency_ms,
                    "error_count": r.error_count,
                    "blocked_count": r.blocked_count,
                }
                for r in records
            ]

    # =========================================================================
    # AGGREGATION JOB
    # =========================================================================

    async def compute_daily_aggregates(
        self,
        tenant_id: str,
        target_date: date,
    ) -> int:
        """Compute or update daily aggregates for a date.

        PURPOSE:
            Called by scheduled job to roll up cus_llm_usage
            into cus_usage_daily for performance.

        Args:
            tenant_id: Tenant to aggregate
            target_date: Date to aggregate

        Returns:
            Number of integration aggregates created/updated
        """
        async for session in get_async_session():
            # Aggregate usage by integration for the date
            query = (
                select(
                    CusLLMUsage.integration_id,
                    func.count(CusLLMUsage.id).label("total_calls"),
                    func.sum(CusLLMUsage.tokens_in).label("total_tokens_in"),
                    func.sum(CusLLMUsage.tokens_out).label("total_tokens_out"),
                    func.sum(CusLLMUsage.cost_cents).label("total_cost_cents"),
                    func.avg(CusLLMUsage.latency_ms).label("avg_latency_ms"),
                    func.count(CusLLMUsage.id).filter(
                        CusLLMUsage.error_code.isnot(None)
                    ).label("error_count"),
                    func.count(CusLLMUsage.id).filter(
                        CusLLMUsage.policy_result == CusPolicyResult.BLOCKED
                    ).label("blocked_count"),
                )
                .where(
                    and_(
                        CusLLMUsage.tenant_id == tenant_id,
                        func.date(CusLLMUsage.created_at) == target_date,
                    )
                )
                .group_by(CusLLMUsage.integration_id)
            )

            result = await session.execute(query)
            rows = result.all()

            count = 0
            for row in rows:
                # Upsert daily aggregate
                stmt = pg_insert(CusUsageDaily).values(
                    tenant_id=tenant_id,
                    integration_id=row.integration_id,
                    date=target_date,
                    total_calls=row.total_calls or 0,
                    total_tokens_in=row.total_tokens_in or 0,
                    total_tokens_out=row.total_tokens_out or 0,
                    total_cost_cents=row.total_cost_cents or 0,
                    avg_latency_ms=int(row.avg_latency_ms) if row.avg_latency_ms else None,
                    error_count=row.error_count or 0,
                    blocked_count=row.blocked_count or 0,
                    updated_at=utc_now(),
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["tenant_id", "integration_id", "date"],
                    set_={
                        "total_calls": stmt.excluded.total_calls,
                        "total_tokens_in": stmt.excluded.total_tokens_in,
                        "total_tokens_out": stmt.excluded.total_tokens_out,
                        "total_cost_cents": stmt.excluded.total_cost_cents,
                        "avg_latency_ms": stmt.excluded.avg_latency_ms,
                        "error_count": stmt.excluded.error_count,
                        "blocked_count": stmt.excluded.blocked_count,
                        "updated_at": stmt.excluded.updated_at,
                    },
                )
                await session.execute(stmt)
                count += 1

            await session.commit()
            return count
