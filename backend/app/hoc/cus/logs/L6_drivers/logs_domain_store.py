# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: AuditLedger, LogExport, LLMRunRecord, SystemRecord
#   Writes: none
# Database:
#   Scope: domain (logs)
#   Models: AuditLedger, LogExport, LLMRunRecord, SystemRecord
# Role: Database operations for Logs domain (LLM runs, system records, audit ledger)
# Callers: L5 LogsFacade
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# DRIVER CONTRACT:
# - Returns domain objects (dataclasses), not ORM models
# - Owns query logic
# - Owns data shape transformation
# - NO business logic (no "if severity >", no "if policy.allows")

"""
Logs Domain Store (L6)

Database driver for all Logs domain data access:
- LLM Run Records
- System Records
- Audit Ledger
- Log Exports

All methods return immutable snapshots, never ORM models.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_ledger import AuditLedger
from app.models.log_exports import LogExport
from app.models.logs_records import LLMRunRecord, SystemRecord


# =============================================================================
# Snapshot Types (Immutable results returned to L4)
# =============================================================================


@dataclass(frozen=True)
class LLMRunSnapshot:
    """Immutable snapshot of LLM run record."""

    id: str
    run_id: str
    trace_id: Optional[str]
    tenant_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cents: int
    execution_status: str
    started_at: datetime
    completed_at: Optional[datetime]
    source: str
    is_synthetic: bool
    created_at: datetime


@dataclass(frozen=True)
class SystemRecordSnapshot:
    """Immutable snapshot of system record."""

    id: str
    tenant_id: Optional[str]
    component: str
    event_type: str
    severity: str
    summary: str
    details: Optional[dict]
    caused_by: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class AuditLedgerSnapshot:
    """Immutable snapshot of audit ledger entry."""

    id: str
    tenant_id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    action_reason: Optional[str]
    before_state: Optional[dict]
    after_state: Optional[dict]
    correlation_id: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class LogExportSnapshot:
    """Immutable snapshot of log export record."""

    id: str
    tenant_id: str
    scope: str
    format: str
    requested_by: str
    status: str
    checksum: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]


@dataclass(frozen=True)
class TraceStepSnapshot:
    """Immutable snapshot of trace step."""

    step_index: int
    timestamp: datetime
    skill_name: str
    status: str
    outcome_category: str
    cost_cents: int
    duration_ms: int


@dataclass
class QueryResult:
    """Generic query result with pagination info."""

    items: list
    total: int
    has_more: bool


# =============================================================================
# Logs Domain Store
# =============================================================================


class LogsDomainStore:
    """
    L6 Database Driver for Logs domain.

    All methods:
    - Accept AsyncSession as parameter
    - Return immutable snapshots
    - Contain NO business logic
    """

    # -------------------------------------------------------------------------
    # LLM Run Records
    # -------------------------------------------------------------------------

    async def list_llm_runs(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        run_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        execution_status: Optional[str] = None,
        is_synthetic: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QueryResult:
        """Query LLM run records with filters."""
        stmt = (
            select(LLMRunRecord)
            .where(LLMRunRecord.tenant_id == tenant_id)
            .order_by(LLMRunRecord.created_at.desc())
        )

        if run_id:
            stmt = stmt.where(LLMRunRecord.run_id == run_id)
        if provider:
            stmt = stmt.where(LLMRunRecord.provider == provider)
        if model:
            stmt = stmt.where(LLMRunRecord.model == model)
        if execution_status:
            stmt = stmt.where(LLMRunRecord.execution_status == execution_status)
        if is_synthetic is not None:
            stmt = stmt.where(LLMRunRecord.is_synthetic == is_synthetic)
        if created_after:
            stmt = stmt.where(LLMRunRecord.created_at >= created_after)
        if created_before:
            stmt = stmt.where(LLMRunRecord.created_at <= created_before)

        # Count total
        count_stmt = select(func.count(LLMRunRecord.id)).where(
            LLMRunRecord.tenant_id == tenant_id
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

        items = [self._to_llm_run_snapshot(e) for e in entries]

        return QueryResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    async def get_llm_run(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[LLMRunSnapshot]:
        """Get single LLM run record by run_id."""
        stmt = select(LLMRunRecord).where(
            LLMRunRecord.run_id == run_id,
            LLMRunRecord.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        return self._to_llm_run_snapshot(entry)

    def _to_llm_run_snapshot(self, entry: LLMRunRecord) -> LLMRunSnapshot:
        """Transform ORM model to immutable snapshot."""
        return LLMRunSnapshot(
            id=entry.id,
            run_id=entry.run_id,
            trace_id=entry.trace_id,
            tenant_id=entry.tenant_id,
            provider=entry.provider,
            model=entry.model,
            input_tokens=entry.input_tokens,
            output_tokens=entry.output_tokens,
            cost_cents=entry.cost_cents,
            execution_status=entry.execution_status,
            started_at=entry.started_at,
            completed_at=entry.completed_at,
            source=entry.source,
            is_synthetic=entry.is_synthetic,
            created_at=entry.created_at,
        )

    # -------------------------------------------------------------------------
    # Trace Steps
    # -------------------------------------------------------------------------

    async def get_trace_id_for_run(
        self,
        session: AsyncSession,
        tenant_id: str,
        run_id: str,
    ) -> Optional[str]:
        """Get trace_id from aos_traces for a run."""
        stmt = text("""
            SELECT trace_id FROM aos_traces
            WHERE run_id = :run_id AND tenant_id = :tenant_id
        """)
        result = await session.execute(stmt, {"run_id": run_id, "tenant_id": tenant_id})
        row = result.fetchone()
        return row[0] if row else None

    async def get_trace_steps(
        self,
        session: AsyncSession,
        trace_id: str,
    ) -> list[TraceStepSnapshot]:
        """Get trace steps for a trace_id."""
        stmt = text("""
            SELECT step_index, timestamp, skill_name, status,
                   outcome_category, cost_cents, duration_ms
            FROM aos_trace_steps
            WHERE trace_id = :trace_id
            ORDER BY step_index
        """)
        result = await session.execute(stmt, {"trace_id": trace_id})
        rows = result.fetchall()

        return [
            TraceStepSnapshot(
                step_index=row[0],
                timestamp=row[1],
                skill_name=row[2],
                status=row[3],
                outcome_category=row[4] or "unknown",
                cost_cents=int(row[5] or 0),
                duration_ms=int(row[6] or 0),
            )
            for row in rows
        ]

    async def get_replay_window_events(
        self,
        session: AsyncSession,
        tenant_id: str,
        trace_id: str,
        window_start: datetime,
        window_end: datetime,
    ) -> list[dict]:
        """Get replay window events from multiple sources."""
        replay_query = text("""
            SELECT 'llm' as source, step_index, timestamp, skill_name as action, outcome_category as outcome
            FROM aos_trace_steps
            WHERE trace_id = :trace_id
            AND timestamp BETWEEN :window_start AND :window_end

            UNION ALL

            SELECT 'system' as source, NULL as step_index, created_at as timestamp,
                   event_type as action, severity as outcome
            FROM system_records
            WHERE (tenant_id = :tenant_id OR tenant_id IS NULL)
            AND created_at BETWEEN :window_start AND :window_end

            UNION ALL

            SELECT 'policy' as source, NULL as step_index, created_at as timestamp,
                   event_type as action, entity_type as outcome
            FROM audit_ledger
            WHERE tenant_id = :tenant_id
            AND entity_type IN ('POLICY_RULE', 'LIMIT')
            AND created_at BETWEEN :window_start AND :window_end

            ORDER BY timestamp
        """)

        result = await session.execute(
            replay_query,
            {
                "trace_id": trace_id,
                "tenant_id": tenant_id,
                "window_start": window_start,
                "window_end": window_end,
            },
        )
        rows = result.fetchall()

        return [
            {
                "source": row[0],
                "step_index": row[1],
                "timestamp": row[2],
                "action": row[3] or "unknown",
                "outcome": row[4] or "unknown",
            }
            for row in rows
        ]

    # -------------------------------------------------------------------------
    # System Records
    # -------------------------------------------------------------------------

    async def list_system_records(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        component: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        correlation_id: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QueryResult:
        """Query system records with filters."""
        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
            )
            .order_by(SystemRecord.created_at.desc())
        )

        if component:
            stmt = stmt.where(SystemRecord.component == component)
        if event_type:
            stmt = stmt.where(SystemRecord.event_type == event_type)
        if severity:
            stmt = stmt.where(SystemRecord.severity == severity)
        if correlation_id:
            stmt = stmt.where(SystemRecord.correlation_id == correlation_id)
        if created_after:
            stmt = stmt.where(SystemRecord.created_at >= created_after)
        if created_before:
            stmt = stmt.where(SystemRecord.created_at <= created_before)

        # Count
        count_stmt = select(func.count(SystemRecord.id)).where(
            (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

        items = [self._to_system_record_snapshot(e) for e in entries]

        return QueryResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    async def get_system_record_by_correlation(
        self,
        session: AsyncSession,
        tenant_id: str,
        correlation_id: str,
    ) -> Optional[SystemRecordSnapshot]:
        """Get first system record for a correlation_id."""
        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
            )
            .where(SystemRecord.correlation_id == correlation_id)
            .order_by(SystemRecord.created_at.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        return self._to_system_record_snapshot(entry)

    async def get_system_records_in_window(
        self,
        session: AsyncSession,
        tenant_id: str,
        window_start: datetime,
        window_end: datetime,
    ) -> list[SystemRecordSnapshot]:
        """Get system records in a time window."""
        stmt = (
            select(SystemRecord)
            .where(
                (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
            )
            .where(SystemRecord.created_at.between(window_start, window_end))
            .order_by(SystemRecord.created_at)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        return [self._to_system_record_snapshot(e) for e in entries]

    def _to_system_record_snapshot(self, entry: SystemRecord) -> SystemRecordSnapshot:
        """Transform ORM model to immutable snapshot."""
        return SystemRecordSnapshot(
            id=entry.id,
            tenant_id=entry.tenant_id,
            component=entry.component,
            event_type=entry.event_type,
            severity=entry.severity,
            summary=entry.summary,
            details=entry.details,
            caused_by=entry.caused_by,
            correlation_id=entry.correlation_id,
            created_at=entry.created_at,
        )

    # -------------------------------------------------------------------------
    # Audit Ledger
    # -------------------------------------------------------------------------

    async def list_audit_entries(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        actor_type: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QueryResult:
        """Query audit ledger entries with filters."""
        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .order_by(AuditLedger.created_at.desc())
        )

        if event_type:
            stmt = stmt.where(AuditLedger.event_type == event_type)
        if entity_type:
            stmt = stmt.where(AuditLedger.entity_type == entity_type)
        if actor_type:
            stmt = stmt.where(AuditLedger.actor_type == actor_type)
        if created_after:
            stmt = stmt.where(AuditLedger.created_at >= created_after)
        if created_before:
            stmt = stmt.where(AuditLedger.created_at <= created_before)

        count_stmt = select(func.count(AuditLedger.id)).where(
            AuditLedger.tenant_id == tenant_id
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

        items = [self._to_audit_snapshot(e) for e in entries]

        return QueryResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    async def get_audit_entry(
        self,
        session: AsyncSession,
        tenant_id: str,
        entry_id: str,
    ) -> Optional[AuditLedgerSnapshot]:
        """Get single audit ledger entry."""
        stmt = select(AuditLedger).where(
            AuditLedger.id == entry_id,
            AuditLedger.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            return None

        return self._to_audit_snapshot(entry)

    async def get_governance_events(
        self,
        session: AsyncSession,
        tenant_id: str,
        limit: int = 100,
    ) -> list[AuditLedgerSnapshot]:
        """Get governance (policy) related audit events."""
        stmt = (
            select(AuditLedger)
            .where(AuditLedger.tenant_id == tenant_id)
            .where(
                AuditLedger.entity_type.in_(["POLICY_RULE", "LIMIT", "POLICY_PROPOSAL"])
            )
            .order_by(AuditLedger.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        return [self._to_audit_snapshot(e) for e in entries]

    def _to_audit_snapshot(self, entry: AuditLedger) -> AuditLedgerSnapshot:
        """Transform ORM model to immutable snapshot."""
        return AuditLedgerSnapshot(
            id=entry.id,
            tenant_id=entry.tenant_id,
            event_type=entry.event_type,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            actor_type=entry.actor_type,
            actor_id=entry.actor_id,
            action_reason=entry.action_reason,
            before_state=entry.before_state,
            after_state=entry.after_state,
            correlation_id=getattr(entry, "correlation_id", None),
            created_at=entry.created_at,
        )

    # -------------------------------------------------------------------------
    # Log Exports
    # -------------------------------------------------------------------------

    async def list_log_exports(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> QueryResult:
        """Query log export records."""
        stmt = (
            select(LogExport)
            .where(LogExport.tenant_id == tenant_id)
            .order_by(LogExport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        count_stmt = select(func.count(LogExport.id)).where(
            LogExport.tenant_id == tenant_id
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        items = [self._to_export_snapshot(e) for e in entries]

        return QueryResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    def _to_export_snapshot(self, entry: LogExport) -> LogExportSnapshot:
        """Transform ORM model to immutable snapshot."""
        return LogExportSnapshot(
            id=entry.id,
            tenant_id=entry.tenant_id,
            scope=entry.scope,
            format=entry.format,
            requested_by=entry.requested_by,
            status=entry.status,
            checksum=entry.checksum,
            created_at=entry.created_at,
            delivered_at=entry.delivered_at,
        )


# =============================================================================
# Singleton Factory
# =============================================================================

_store_instance: LogsDomainStore | None = None


def get_logs_domain_store() -> LogsDomainStore:
    """Get the singleton LogsDomainStore instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = LogsDomainStore()
    return _store_instance


__all__ = [
    "LogsDomainStore",
    "get_logs_domain_store",
    # Snapshots
    "LLMRunSnapshot",
    "SystemRecordSnapshot",
    "AuditLedgerSnapshot",
    "LogExportSnapshot",
    "TraceStepSnapshot",
    "QueryResult",
]
