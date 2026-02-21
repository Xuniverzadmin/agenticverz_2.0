# capability_id: CAP-012
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: Customer Telemetry Driver
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-520 (L6 Purity)
"""Customer Telemetry Driver

L6 driver for customer telemetry data access.

Pure persistence - no business logic.
Handles: ingestion, queries, aggregation.

L6 Contract:
    - Session REQUIRED (passed from L4 handler)
    - L6 does NOT commit (L4 owns transaction boundary)
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import func, select, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cus_models import (
    CusIntegration,
    CusLLMUsage,
    CusPolicyResult,
    CusUsageDaily,
)


def utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UsageRow:
    """Immutable usage record DTO."""

    id: str
    integration_id: str
    call_id: str
    session_id: Optional[str]
    agent_id: Optional[str]
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_cents: int
    latency_ms: Optional[int]
    policy_result: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class UsageSummaryRow:
    """Immutable usage summary DTO."""

    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_cents: int
    avg_latency_ms: Optional[int]
    error_count: int
    blocked_count: int


@dataclass(frozen=True)
class IntegrationUsageRow:
    """Immutable per-integration usage DTO."""

    integration_id: str
    integration_name: str
    provider_type: str
    total_calls: int
    total_tokens: int
    total_cost_cents: int
    error_count: int


@dataclass(frozen=True)
class DailyAggregateRow:
    """Immutable daily aggregate DTO."""

    date: date
    integration_id: str
    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_cents: int
    avg_latency_ms: Optional[int]
    error_count: int
    blocked_count: int


class CusTelemetryDriver:
    """L6 driver for customer telemetry data access.

    Pure persistence - no business logic.
    L6 does NOT commit — L4 handler owns transaction boundary.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with required session.

        Args:
            session: AsyncSession from L4 handler (required)
        """
        self._session = session

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    async def fetch_by_call_id(self, call_id: str) -> Optional[str]:
        """Fetch usage record ID by call_id.

        Args:
            call_id: The call ID to look up

        Returns:
            Record ID if found, None otherwise
        """
        result = await self._session.execute(
            select(CusLLMUsage.id).where(CusLLMUsage.call_id == call_id)
        )
        return result.scalar_one_or_none()

    async def fetch_call_ids_batch(self, call_ids: List[str]) -> set:
        """Fetch existing call_ids from a list.

        Args:
            call_ids: List of call IDs to check

        Returns:
            Set of call_ids that already exist
        """
        result = await self._session.execute(
            select(CusLLMUsage.call_id).where(CusLLMUsage.call_id.in_(call_ids))
        )
        return set(result.scalars().all())

    async def fetch_integration(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Optional[CusIntegration]:
        """Fetch integration by ID with tenant verification.

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID

        Returns:
            CusIntegration if found, None otherwise
        """
        result = await self._session.execute(
            select(CusIntegration).where(
                and_(
                    CusIntegration.id == integration_id,
                    CusIntegration.tenant_id == tenant_id,
                    CusIntegration.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def fetch_usage_summary(
        self,
        tenant_id: str,
        integration_id: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> UsageSummaryRow:
        """Fetch aggregated usage summary.

        Args:
            tenant_id: Tenant ID
            integration_id: Optional filter
            start_date: Period start
            end_date: Period end

        Returns:
            UsageSummaryRow with aggregated metrics
        """
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

        if integration_id:
            query = query.where(CusLLMUsage.integration_id == integration_id)
        if start_date:
            query = query.where(CusLLMUsage.created_at >= start_date)
        if end_date:
            query = query.where(CusLLMUsage.created_at <= end_date)

        result = await self._session.execute(query)
        row = result.one()

        return UsageSummaryRow(
            total_calls=row.total_calls or 0,
            total_tokens_in=row.total_tokens_in or 0,
            total_tokens_out=row.total_tokens_out or 0,
            total_cost_cents=row.total_cost_cents or 0,
            avg_latency_ms=int(row.avg_latency_ms) if row.avg_latency_ms else None,
            error_count=row.error_count or 0,
            blocked_count=row.blocked_count or 0,
        )

    async def fetch_per_integration_usage(
        self,
        tenant_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[IntegrationUsageRow]:
        """Fetch usage breakdown by integration.

        Args:
            tenant_id: Tenant ID
            start_date: Period start
            end_date: Period end

        Returns:
            List of IntegrationUsageRow
        """
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

        result = await self._session.execute(query)
        rows = result.all()

        # Get integration details
        integration_ids = [r.integration_id for r in rows]
        integrations_result = await self._session.execute(
            select(CusIntegration).where(CusIntegration.id.in_(integration_ids))
        )
        integrations = {i.id: i for i in integrations_result.scalars().all()}

        return [
            IntegrationUsageRow(
                integration_id=row.integration_id,
                integration_name=integrations.get(row.integration_id).name
                if integrations.get(row.integration_id)
                else "Unknown",
                provider_type=integrations.get(row.integration_id).provider_type
                if integrations.get(row.integration_id)
                else "custom",
                total_calls=row.total_calls or 0,
                total_tokens=row.total_tokens or 0,
                total_cost_cents=row.total_cost_cents or 0,
                error_count=row.error_count or 0,
            )
            for row in rows
        ]

    async def fetch_usage_history(
        self,
        tenant_id: str,
        integration_id: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[List[UsageRow], int]:
        """Fetch paginated usage history.

        Args:
            tenant_id: Tenant ID
            integration_id: Optional filter
            limit: Max records
            offset: Pagination offset

        Returns:
            Tuple of (records, total_count)
        """
        base_filter = CusLLMUsage.tenant_id == tenant_id
        if integration_id:
            base_filter = and_(
                base_filter, CusLLMUsage.integration_id == integration_id
            )

        # Get total count
        count_result = await self._session.execute(
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
        result = await self._session.execute(query)
        records = result.scalars().all()

        return (
            [
                UsageRow(
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

    async def fetch_daily_aggregates(
        self,
        tenant_id: str,
        integration_id: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[DailyAggregateRow]:
        """Fetch daily aggregated usage.

        Args:
            tenant_id: Tenant ID
            integration_id: Optional filter
            start_date: Period start
            end_date: Period end

        Returns:
            List of DailyAggregateRow
        """
        query = select(CusUsageDaily).where(CusUsageDaily.tenant_id == tenant_id)

        if integration_id:
            query = query.where(CusUsageDaily.integration_id == integration_id)
        if start_date:
            query = query.where(CusUsageDaily.date >= start_date)
        if end_date:
            query = query.where(CusUsageDaily.date <= end_date)

        query = query.order_by(CusUsageDaily.date.asc())

        result = await self._session.execute(query)
        records = result.scalars().all()

        return [
            DailyAggregateRow(
                date=r.date,
                integration_id=r.integration_id,
                total_calls=r.total_calls,
                total_tokens_in=r.total_tokens_in,
                total_tokens_out=r.total_tokens_out,
                total_cost_cents=r.total_cost_cents,
                avg_latency_ms=r.avg_latency_ms,
                error_count=r.error_count,
                blocked_count=r.blocked_count,
            )
            for r in records
        ]

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def create_usage(
        self,
        tenant_id: str,
        integration_id: str,
        session_id: Optional[str],
        agent_id: Optional[str],
        call_id: str,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost_cents: int,
        latency_ms: Optional[int],
        policy_result: Optional[str],
        error_code: Optional[str],
        error_message: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        """Create a usage record.

        Args:
            All fields for the usage record

        Returns:
            Created record ID

        Note:
            L6 does NOT commit — L4 handler owns transaction boundary.
        """
        record = CusLLMUsage(
            id=str(uuid4()),
            tenant_id=tenant_id,
            integration_id=integration_id,
            session_id=session_id,
            agent_id=agent_id,
            call_id=call_id,
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_cents=cost_cents,
            latency_ms=latency_ms,
            policy_result=policy_result,
            error_code=error_code,
            error_message=error_message,
            extra_data=metadata,
            created_at=utc_now(),
        )

        self._session.add(record)
        await self._session.flush()

        return record.id

    async def create_usage_batch(
        self,
        records_data: List[Dict[str, Any]],
    ) -> int:
        """Create multiple usage records.

        Args:
            records_data: List of record dicts

        Returns:
            Count of records created

        Note:
            L6 does NOT commit — L4 handler owns transaction boundary.
        """
        count = 0
        for data in records_data:
            record = CusLLMUsage(
                id=str(uuid4()),
                tenant_id=data["tenant_id"],
                integration_id=data["integration_id"],
                session_id=data.get("session_id"),
                agent_id=data.get("agent_id"),
                call_id=data["call_id"],
                provider=data["provider"],
                model=data["model"],
                tokens_in=data["tokens_in"],
                tokens_out=data["tokens_out"],
                cost_cents=data["cost_cents"],
                latency_ms=data.get("latency_ms"),
                policy_result=data.get("policy_result"),
                error_code=data.get("error_code"),
                error_message=data.get("error_message"),
                extra_data=data.get("metadata"),
                created_at=utc_now(),
            )
            self._session.add(record)
            count += 1

        await self._session.flush()
        return count

    async def upsert_daily_aggregate(
        self,
        tenant_id: str,
        integration_id: str,
        target_date: date,
        total_calls: int,
        total_tokens_in: int,
        total_tokens_out: int,
        total_cost_cents: int,
        avg_latency_ms: Optional[int],
        error_count: int,
        blocked_count: int,
    ) -> None:
        """Upsert a daily aggregate record.

        Args:
            All fields for the daily aggregate

        Note:
            L6 does NOT commit — L4 handler owns transaction boundary.
        """
        stmt = pg_insert(CusUsageDaily).values(
            tenant_id=tenant_id,
            integration_id=integration_id,
            date=target_date,
            total_calls=total_calls,
            total_tokens_in=total_tokens_in,
            total_tokens_out=total_tokens_out,
            total_cost_cents=total_cost_cents,
            avg_latency_ms=avg_latency_ms,
            error_count=error_count,
            blocked_count=blocked_count,
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
        await self._session.execute(stmt)

    async def compute_daily_aggregates_raw(
        self,
        tenant_id: str,
        target_date: date,
    ) -> List[Dict[str, Any]]:
        """Compute raw aggregation data for a date.

        Args:
            tenant_id: Tenant ID
            target_date: Date to aggregate

        Returns:
            List of aggregation dicts by integration
        """
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

        result = await self._session.execute(query)
        rows = result.all()

        return [
            {
                "integration_id": row.integration_id,
                "total_calls": row.total_calls or 0,
                "total_tokens_in": row.total_tokens_in or 0,
                "total_tokens_out": row.total_tokens_out or 0,
                "total_cost_cents": row.total_cost_cents or 0,
                "avg_latency_ms": int(row.avg_latency_ms) if row.avg_latency_ms else None,
                "error_count": row.error_count or 0,
                "blocked_count": row.blocked_count or 0,
            }
            for row in rows
        ]


# Factory function
def get_cus_telemetry_driver(session: AsyncSession) -> CusTelemetryDriver:
    """Get driver instance.

    Args:
        session: AsyncSession from L4 handler (required)

    Returns:
        CusTelemetryDriver instance

    Note:
        Session is REQUIRED. L4 handler owns transaction boundary.
    """
    return CusTelemetryDriver(session=session)
