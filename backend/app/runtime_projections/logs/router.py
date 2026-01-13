# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Logs O2/O3 Runtime Projection API — Full Logs Domain (PIN-413)
# Callers: Customer Console Logs Views
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-413 Domain Design — Overview & Logs (CORRECTED + Expansion)

"""
LOG-RT-O2/O3 — Logs Runtime Projection Contract (GROUNDED)

Three immutable record types:
1. Audit Ledger: Governance action log (HUMAN, SYSTEM, AGENT actions)
2. LLM Run Records: Immutable execution records for every LLM run
3. System Records: System-level events that affect trust

All records are:
- APPEND-ONLY (enforced by DB trigger)
- WRITE-ONCE (no UPDATE, no DELETE)
- Trust anchors for verification

Contract Rules:
- Tenant isolation is mandatory (from auth_context)
- All tables are APPEND-ONLY
- Only canonical events create rows
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session_dep
from app.models.audit_ledger import AuditLedger
from app.models.logs_records import LLMRunRecord, SystemRecord
from app.auth.tenant_auth import TenantContext, get_tenant_context

router = APIRouter(prefix="/logs", tags=["runtime-logs"])


# =============================================================================
# Response Models — Audit Ledger (LOG-RT-O2-AUDIT)
# =============================================================================


class AuditLedgerItem(BaseModel):
    """Single audit ledger entry (O2)."""
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str]
    action_reason: Optional[str]
    created_at: datetime


class AuditLedgerDetailItem(AuditLedgerItem):
    """Audit ledger entry with state snapshots (O3)."""
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None


class AuditLedgerResponse(BaseModel):
    """Response envelope for audit ledger."""
    items: List[AuditLedgerItem]
    total: int
    has_more: bool


# =============================================================================
# Audit Ledger O2 Endpoint (LOG-RT-O2-AUDIT) — GROUNDED
# =============================================================================


@router.get("/audit", response_model=AuditLedgerResponse)
async def list_audit_entries(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_type: Optional[str] = Query(
        None,
        description="Filter by entity type: POLICY_RULE, POLICY_PROPOSAL, LIMIT, INCIDENT",
        regex="^(POLICY_RULE|POLICY_PROPOSAL|LIMIT|INCIDENT)$",
    ),
    actor_type: Optional[str] = Query(
        None,
        description="Filter by actor type: HUMAN, SYSTEM, AGENT",
        regex="^(HUMAN|SYSTEM|AGENT)$",
    ),
    created_after: Optional[datetime] = Query(None, description="Filter by created_at >= value"),
    created_before: Optional[datetime] = Query(None, description="Filter by created_at <= value"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/logs/audit

    Audit Ledger: Immutable governance action log.

    Records governance-relevant actions taken by actors.
    Only canonical events from the approved list create rows.
    APPEND-ONLY: No UPDATE, no DELETE (enforced by DB trigger).
    """
    # Base query
    stmt = (
        select(AuditLedger)
        .where(AuditLedger.tenant_id == tenant.tenant_id)
        .order_by(AuditLedger.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if event_type is not None:
        stmt = stmt.where(AuditLedger.event_type == event_type)

    if entity_type is not None:
        stmt = stmt.where(AuditLedger.entity_type == entity_type)

    if actor_type is not None:
        stmt = stmt.where(AuditLedger.actor_type == actor_type)

    if created_after is not None:
        stmt = stmt.where(AuditLedger.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(AuditLedger.created_at <= created_before)

    result = await session.execute(stmt)
    entries = result.scalars().all()

    # Count total
    count_stmt = (
        select(func.count(AuditLedger.id))
        .where(AuditLedger.tenant_id == tenant.tenant_id)
    )
    if event_type is not None:
        count_stmt = count_stmt.where(AuditLedger.event_type == event_type)
    if entity_type is not None:
        count_stmt = count_stmt.where(AuditLedger.entity_type == entity_type)
    if actor_type is not None:
        count_stmt = count_stmt.where(AuditLedger.actor_type == actor_type)
    if created_after is not None:
        count_stmt = count_stmt.where(AuditLedger.created_at >= created_after)
    if created_before is not None:
        count_stmt = count_stmt.where(AuditLedger.created_at <= created_before)

    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    items = [
        AuditLedgerItem(
            id=entry.id,
            event_type=entry.event_type,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            actor_type=entry.actor_type,
            actor_id=entry.actor_id,
            action_reason=entry.action_reason,
            created_at=entry.created_at,
        )
        for entry in entries
    ]

    return AuditLedgerResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )


# =============================================================================
# Audit Ledger O3 Detail Endpoint (LOG-RT-O3-AUDIT)
# =============================================================================


@router.get("/audit/{entry_id}", response_model=AuditLedgerDetailItem)
async def get_audit_entry(
    entry_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/logs/audit/{entry_id}

    Audit Ledger Entry Detail: Full entry with state snapshots.

    Shows before_state and after_state for MODIFY events.
    """
    stmt = (
        select(AuditLedger)
        .where(AuditLedger.id == entry_id)
        .where(AuditLedger.tenant_id == tenant.tenant_id)
    )

    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="Audit entry not found")

    return AuditLedgerDetailItem(
        id=entry.id,
        event_type=entry.event_type,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        actor_type=entry.actor_type,
        actor_id=entry.actor_id,
        action_reason=entry.action_reason,
        created_at=entry.created_at,
        before_state=entry.before_state,
        after_state=entry.after_state,
    )


# =============================================================================
# Response Models — LLM Run Records (LOG-RT-O2-LLM) — PIN-413
# =============================================================================


class LLMRunRecordItem(BaseModel):
    """Single LLM run record entry (O2)."""
    id: str
    run_id: str
    trace_id: Optional[str]
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


class LLMRunRecordDetailItem(LLMRunRecordItem):
    """LLM run record with hashes (O3)."""
    prompt_hash: Optional[str]
    response_hash: Optional[str]
    synthetic_scenario_id: Optional[str]


class LLMRunRecordsResponse(BaseModel):
    """Response envelope for LLM run records."""
    items: List[LLMRunRecordItem]
    total: int
    has_more: bool


# =============================================================================
# LLM Run Records O2 Endpoint (LOG-RT-O2-LLM) — PIN-413
# =============================================================================


@router.get("/llm-runs", response_model=LLMRunRecordsResponse)
async def list_llm_run_records(
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    provider: Optional[str] = Query(None, description="Filter by provider: anthropic, openai, stub"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    execution_status: Optional[str] = Query(
        None,
        description="Filter by status: SUCCEEDED, FAILED, ABORTED, TIMEOUT",
        regex="^(SUCCEEDED|FAILED|ABORTED|TIMEOUT)$",
    ),
    is_synthetic: Optional[bool] = Query(None, description="Filter by synthetic flag"),
    created_after: Optional[datetime] = Query(None, description="Filter by created_at >= value"),
    created_before: Optional[datetime] = Query(None, description="Filter by created_at <= value"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/logs/llm-runs

    LLM Run Records: Immutable execution records for every LLM run.

    This is the TRUST ANCHOR for execution verification.
    Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger).

    Answers:
    - Did this run really happen?
    - What provider, model, tokens, cost?
    - What was the execution outcome?
    """
    # Base query
    stmt = (
        select(LLMRunRecord)
        .where(LLMRunRecord.tenant_id == tenant.tenant_id)
        .order_by(LLMRunRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if run_id is not None:
        stmt = stmt.where(LLMRunRecord.run_id == run_id)

    if provider is not None:
        stmt = stmt.where(LLMRunRecord.provider == provider)

    if model is not None:
        stmt = stmt.where(LLMRunRecord.model == model)

    if execution_status is not None:
        stmt = stmt.where(LLMRunRecord.execution_status == execution_status)

    if is_synthetic is not None:
        stmt = stmt.where(LLMRunRecord.is_synthetic == is_synthetic)

    if created_after is not None:
        stmt = stmt.where(LLMRunRecord.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(LLMRunRecord.created_at <= created_before)

    result = await session.execute(stmt)
    entries = result.scalars().all()

    # Count total
    count_stmt = (
        select(func.count(LLMRunRecord.id))
        .where(LLMRunRecord.tenant_id == tenant.tenant_id)
    )
    if run_id is not None:
        count_stmt = count_stmt.where(LLMRunRecord.run_id == run_id)
    if provider is not None:
        count_stmt = count_stmt.where(LLMRunRecord.provider == provider)
    if model is not None:
        count_stmt = count_stmt.where(LLMRunRecord.model == model)
    if execution_status is not None:
        count_stmt = count_stmt.where(LLMRunRecord.execution_status == execution_status)
    if is_synthetic is not None:
        count_stmt = count_stmt.where(LLMRunRecord.is_synthetic == is_synthetic)
    if created_after is not None:
        count_stmt = count_stmt.where(LLMRunRecord.created_at >= created_after)
    if created_before is not None:
        count_stmt = count_stmt.where(LLMRunRecord.created_at <= created_before)

    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    items = [
        LLMRunRecordItem(
            id=entry.id,
            run_id=entry.run_id,
            trace_id=entry.trace_id,
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
        for entry in entries
    ]

    return LLMRunRecordsResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )


# =============================================================================
# LLM Run Record O3 Detail Endpoint (LOG-RT-O3-LLM) — PIN-413
# =============================================================================


@router.get("/llm-runs/{record_id}", response_model=LLMRunRecordDetailItem)
async def get_llm_run_record(
    record_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/logs/llm-runs/{record_id}

    LLM Run Record Detail: Full record with content hashes.

    Shows prompt_hash and response_hash for verification.
    """
    stmt = (
        select(LLMRunRecord)
        .where(LLMRunRecord.id == record_id)
        .where(LLMRunRecord.tenant_id == tenant.tenant_id)
    )

    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="LLM run record not found")

    return LLMRunRecordDetailItem(
        id=entry.id,
        run_id=entry.run_id,
        trace_id=entry.trace_id,
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
        prompt_hash=entry.prompt_hash,
        response_hash=entry.response_hash,
        synthetic_scenario_id=entry.synthetic_scenario_id,
    )


# =============================================================================
# Response Models — System Records (LOG-RT-O2-SYSTEM) — PIN-413
# =============================================================================


class SystemRecordItem(BaseModel):
    """Single system record entry (O2)."""
    id: str
    tenant_id: Optional[str]
    component: str
    event_type: str
    severity: str
    summary: str
    caused_by: Optional[str]
    correlation_id: Optional[str]
    created_at: datetime


class SystemRecordDetailItem(SystemRecordItem):
    """System record with details (O3)."""
    details: Optional[dict]


class SystemRecordsResponse(BaseModel):
    """Response envelope for system records."""
    items: List[SystemRecordItem]
    total: int
    has_more: bool


# =============================================================================
# System Records O2 Endpoint (LOG-RT-O2-SYSTEM) — PIN-413
# =============================================================================


@router.get("/system", response_model=SystemRecordsResponse)
async def list_system_records(
    component: Optional[str] = Query(
        None,
        description="Filter by component: worker, api, scheduler, db, auth, migration",
        regex="^(worker|api|scheduler|db|auth|migration)$",
    ),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type: STARTUP, SHUTDOWN, RESTART, DEPLOY, MIGRATION, AUTH_CHANGE, CONFIG_CHANGE, ERROR, HEALTH_CHECK",
    ),
    severity: Optional[str] = Query(
        None,
        description="Filter by severity: INFO, WARN, CRITICAL",
        regex="^(INFO|WARN|CRITICAL)$",
    ),
    created_after: Optional[datetime] = Query(None, description="Filter by created_at >= value"),
    created_before: Optional[datetime] = Query(None, description="Filter by created_at <= value"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/logs/system

    System Records: Immutable records for system-level events.

    NOT infra noise or stdout spam. YES:
    - Worker restarts
    - Deployment changes
    - Schema migrations
    - Auth / permission changes

    Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger).
    """
    # Base query - system records can be tenant-specific or system-wide (NULL)
    # For customer console, show tenant-specific + system-wide records
    stmt = (
        select(SystemRecord)
        .where(
            (SystemRecord.tenant_id == tenant.tenant_id) |
            (SystemRecord.tenant_id.is_(None))
        )
        .order_by(SystemRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if component is not None:
        stmt = stmt.where(SystemRecord.component == component)

    if event_type is not None:
        stmt = stmt.where(SystemRecord.event_type == event_type)

    if severity is not None:
        stmt = stmt.where(SystemRecord.severity == severity)

    if created_after is not None:
        stmt = stmt.where(SystemRecord.created_at >= created_after)

    if created_before is not None:
        stmt = stmt.where(SystemRecord.created_at <= created_before)

    result = await session.execute(stmt)
    entries = result.scalars().all()

    # Count total
    count_stmt = (
        select(func.count(SystemRecord.id))
        .where(
            (SystemRecord.tenant_id == tenant.tenant_id) |
            (SystemRecord.tenant_id.is_(None))
        )
    )
    if component is not None:
        count_stmt = count_stmt.where(SystemRecord.component == component)
    if event_type is not None:
        count_stmt = count_stmt.where(SystemRecord.event_type == event_type)
    if severity is not None:
        count_stmt = count_stmt.where(SystemRecord.severity == severity)
    if created_after is not None:
        count_stmt = count_stmt.where(SystemRecord.created_at >= created_after)
    if created_before is not None:
        count_stmt = count_stmt.where(SystemRecord.created_at <= created_before)

    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    items = [
        SystemRecordItem(
            id=entry.id,
            tenant_id=entry.tenant_id,
            component=entry.component,
            event_type=entry.event_type,
            severity=entry.severity,
            summary=entry.summary,
            caused_by=entry.caused_by,
            correlation_id=entry.correlation_id,
            created_at=entry.created_at,
        )
        for entry in entries
    ]

    return SystemRecordsResponse(
        items=items,
        total=total,
        has_more=(offset + len(items)) < total,
    )


# =============================================================================
# System Record O3 Detail Endpoint (LOG-RT-O3-SYSTEM) — PIN-413
# =============================================================================


@router.get("/system/{record_id}", response_model=SystemRecordDetailItem)
async def get_system_record(
    record_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/logs/system/{record_id}

    System Record Detail: Full record with details payload.
    """
    # System records can be tenant-specific or system-wide
    stmt = (
        select(SystemRecord)
        .where(SystemRecord.id == record_id)
        .where(
            (SystemRecord.tenant_id == tenant.tenant_id) |
            (SystemRecord.tenant_id.is_(None))
        )
    )

    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(status_code=404, detail="System record not found")

    return SystemRecordDetailItem(
        id=entry.id,
        tenant_id=entry.tenant_id,
        component=entry.component,
        event_type=entry.event_type,
        severity=entry.severity,
        summary=entry.summary,
        caused_by=entry.caused_by,
        correlation_id=entry.correlation_id,
        created_at=entry.created_at,
        details=entry.details,
    )
