# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Customer Telemetry Engine
"""Customer Telemetry Engine

L4 engine for customer telemetry decisions.

Decides: Idempotency checks, integration validation
Delegates: All persistence to CusTelemetryDriver
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from app.schemas.cus_schemas import (
    CusIntegrationUsage,
    CusLLMUsageIngest,
    CusLLMUsageResponse,
    CusUsageSummary,
)
from app.hoc.cus.activity.L6_drivers.cus_telemetry_driver import (
    CusTelemetryDriver,
    get_cus_telemetry_driver,
)

if TYPE_CHECKING:
    pass


@dataclass
class IngestResult:
    """Result of single usage ingestion."""

    status: str  # "accepted" or "duplicate"
    id: Optional[str] = None
    call_id: Optional[str] = None


@dataclass
class BatchIngestResult:
    """Result of batch usage ingestion."""

    accepted: int
    duplicates: int
    errors: int
    total: int


class CusTelemetryEngine:
    """L4 engine for customer telemetry decisions.

    Decides: Idempotency, integration validation
    Delegates: All persistence to CusTelemetryDriver
    """

    def __init__(self, driver: CusTelemetryDriver):
        """Initialize engine with driver.

        Args:
            driver: CusTelemetryDriver instance for persistence
        """
        self._driver = driver

    # =========================================================================
    # INGESTION
    # =========================================================================

    async def ingest_usage(
        self,
        tenant_id: str,
        integration_id: str,
        payload: CusLLMUsageIngest,
    ) -> IngestResult:
        """Ingest a single LLM usage record.

        Business logic:
        - Checks idempotency via call_id
        - Validates integration exists and belongs to tenant

        Args:
            tenant_id: Tenant owning this data
            integration_id: Integration that made the call
            payload: Telemetry data

        Returns:
            IngestResult with status and id

        Raises:
            ValueError: If integration not found
        """
        # DECISION: Idempotency check
        existing_id = await self._driver.fetch_by_call_id(payload.call_id)
        if existing_id:
            return IngestResult(status="duplicate", call_id=payload.call_id)

        # DECISION: Validate integration belongs to tenant
        integration = await self._driver.fetch_integration(tenant_id, integration_id)
        if not integration:
            raise ValueError(f"Integration {integration_id} not found for tenant")

        # Delegate persistence
        record_id = await self._driver.create_usage(
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
        )

        return IngestResult(status="accepted", id=record_id, call_id=payload.call_id)

    async def ingest_batch(
        self,
        tenant_id: str,
        default_integration_id: Optional[str],
        records: List[CusLLMUsageIngest],
    ) -> BatchIngestResult:
        """Ingest a batch of LLM usage records.

        Business logic:
        - Batch idempotency check
        - Missing integration validation

        Args:
            tenant_id: Tenant owning this data
            default_integration_id: Default integration if not in record
            records: List of telemetry records

        Returns:
            BatchIngestResult with counts
        """
        # DECISION: Batch idempotency check
        call_ids = [r.call_id for r in records]
        existing_call_ids = await self._driver.fetch_call_ids_batch(call_ids)

        accepted = 0
        duplicates = 0
        errors = 0
        records_to_create = []

        for payload in records:
            # DECISION: Skip duplicates
            if payload.call_id in existing_call_ids:
                duplicates += 1
                continue

            # DECISION: Require integration
            integration_id = payload.integration_id or default_integration_id
            if not integration_id:
                errors += 1
                continue

            records_to_create.append({
                "tenant_id": tenant_id,
                "integration_id": integration_id,
                "session_id": payload.session_id,
                "agent_id": payload.agent_id,
                "call_id": payload.call_id,
                "provider": payload.provider,
                "model": payload.model,
                "tokens_in": payload.tokens_in,
                "tokens_out": payload.tokens_out,
                "cost_cents": payload.cost_cents,
                "latency_ms": payload.latency_ms,
                "policy_result": payload.policy_result,
                "error_code": payload.error_code,
                "error_message": payload.error_message,
                "metadata": payload.metadata,
            })

        # Delegate batch persistence
        if records_to_create:
            accepted = await self._driver.create_usage_batch(records_to_create)

        return BatchIngestResult(
            accepted=accepted,
            duplicates=duplicates,
            errors=errors,
            total=len(records),
        )

    # =========================================================================
    # QUERIES (pure delegation)
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
            integration_id: Optional filter
            start_date: Period start
            end_date: Period end

        Returns:
            CusUsageSummary with aggregated metrics
        """
        summary = await self._driver.fetch_usage_summary(
            tenant_id, integration_id, start_date, end_date
        )

        by_integration = None
        if not integration_id:
            integration_rows = await self._driver.fetch_per_integration_usage(
                tenant_id, start_date, end_date
            )
            by_integration = [
                CusIntegrationUsage(
                    integration_id=row.integration_id,
                    integration_name=row.integration_name,
                    provider_type=row.provider_type,
                    total_calls=row.total_calls,
                    total_tokens=row.total_tokens,
                    total_cost_cents=row.total_cost_cents,
                    error_count=row.error_count,
                )
                for row in integration_rows
            ]

        return CusUsageSummary(
            tenant_id=tenant_id,
            period_start=start_date or date.today(),
            period_end=end_date or date.today(),
            total_calls=summary.total_calls,
            total_tokens_in=summary.total_tokens_in,
            total_tokens_out=summary.total_tokens_out,
            total_cost_cents=summary.total_cost_cents,
            avg_latency_ms=summary.avg_latency_ms,
            error_count=summary.error_count,
            blocked_count=summary.blocked_count,
            by_integration=by_integration,
        )

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
        rows, total = await self._driver.fetch_usage_history(
            tenant_id, integration_id, limit, offset
        )

        return (
            [
                CusLLMUsageResponse(
                    id=row.id,
                    integration_id=row.integration_id,
                    call_id=row.call_id,
                    session_id=row.session_id,
                    agent_id=row.agent_id,
                    provider=row.provider,
                    model=row.model,
                    tokens_in=row.tokens_in,
                    tokens_out=row.tokens_out,
                    cost_cents=row.cost_cents,
                    latency_ms=row.latency_ms,
                    policy_result=row.policy_result,
                    error_code=row.error_code,
                    error_message=row.error_message,
                    created_at=row.created_at,
                )
                for row in rows
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
        rows = await self._driver.fetch_daily_aggregates(
            tenant_id, integration_id, start_date, end_date
        )

        return [
            {
                "date": row.date.isoformat(),
                "integration_id": row.integration_id,
                "total_calls": row.total_calls,
                "total_tokens_in": row.total_tokens_in,
                "total_tokens_out": row.total_tokens_out,
                "total_cost_cents": row.total_cost_cents,
                "avg_latency_ms": row.avg_latency_ms,
                "error_count": row.error_count,
                "blocked_count": row.blocked_count,
            }
            for row in rows
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

        Args:
            tenant_id: Tenant to aggregate
            target_date: Date to aggregate

        Returns:
            Number of integration aggregates created/updated
        """
        # Fetch raw aggregation data
        agg_data = await self._driver.compute_daily_aggregates_raw(tenant_id, target_date)

        # Upsert each integration's aggregate
        count = 0
        for data in agg_data:
            await self._driver.upsert_daily_aggregate(
                tenant_id=tenant_id,
                integration_id=data["integration_id"],
                target_date=target_date,
                total_calls=data["total_calls"],
                total_tokens_in=data["total_tokens_in"],
                total_tokens_out=data["total_tokens_out"],
                total_cost_cents=data["total_cost_cents"],
                avg_latency_ms=data["avg_latency_ms"],
                error_count=data["error_count"],
                blocked_count=data["blocked_count"],
            )
            count += 1

        return count


# Factory function
def get_cus_telemetry_engine() -> CusTelemetryEngine:
    """Get engine instance with default driver.

    Returns:
        CusTelemetryEngine instance
    """
    driver = get_cus_telemetry_driver()
    return CusTelemetryEngine(driver=driver)

