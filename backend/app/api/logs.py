# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified LOGS domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: LOGS Domain - One Facade Architecture, PIN-413
#
# GOVERNANCE NOTE:
# This is the ONE facade for LOGS domain.
# All log data (audit, LLM runs, system) flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Logs API (L2)

Customer-facing endpoints for viewing logs: audit ledger, LLM run records, and system records.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/logs/audit                → O2 list audit entries
- GET /api/v1/logs/audit/{entry_id}     → O3 audit entry detail
- GET /api/v1/logs/llm-runs             → O2 list LLM run records
- GET /api/v1/logs/llm-runs/{record_id} → O3 LLM run record detail
- GET /api/v1/logs/system               → O2 list system records
- GET /api/v1/logs/system/{record_id}   → O3 system record detail

Three immutable record types:
1. Audit Ledger: Governance action log (HUMAN, SYSTEM, AGENT actions)
2. LLM Run Records: Immutable execution records for every LLM run
3. System Records: System-level events that affect trust

All records are:
- APPEND-ONLY (enforced by DB trigger)
- WRITE-ONCE (no UPDATE, no DELETE)
- Trust anchors for verification

Architecture:
- ONE facade for all LOGS needs
- Queries AuditLedger, LLMRunRecord, SystemRecord tables
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

from datetime import datetime
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.models.audit_ledger import AuditLedger
from app.models.logs_records import LLMRunRecord, SystemRecord

# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/logs",
    tags=["logs"],
)


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth_context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)

    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "not_authenticated", "message": "Authentication required."},
        )

    tenant_id: str | None = getattr(auth_context, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_required",
                "message": "This endpoint requires tenant context.",
            },
        )

    return tenant_id


# =============================================================================
# Response Models — Audit Ledger (O2, O3)
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
    filters_applied: dict[str, Any]


# =============================================================================
# Response Models — LLM Run Records (O2, O3)
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
    filters_applied: dict[str, Any]


# =============================================================================
# Response Models — System Records (O2, O3)
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
    filters_applied: dict[str, Any]


# =============================================================================
# GET /audit - O2 Audit Ledger List
# =============================================================================


@router.get(
    "/audit",
    response_model=AuditLedgerResponse,
    summary="List audit entries (O2)",
    description="""
    Audit Ledger: Immutable governance action log.

    Records governance-relevant actions taken by actors.
    Only canonical events from the approved list create rows.
    APPEND-ONLY: No UPDATE, no DELETE (enforced by DB trigger).
    """,
)
async def list_audit_entries(
    request: Request,
    # Optional filters
    event_type: Annotated[Optional[str], Query(description="Filter by event type")] = None,
    entity_type: Annotated[
        Optional[str],
        Query(
            description="Filter by entity type: POLICY_RULE, POLICY_PROPOSAL, LIMIT, INCIDENT",
            pattern="^(POLICY_RULE|POLICY_PROPOSAL|LIMIT|INCIDENT)$",
        ),
    ] = None,
    actor_type: Annotated[
        Optional[str],
        Query(
            description="Filter by actor type: HUMAN, SYSTEM, AGENT",
            pattern="^(HUMAN|SYSTEM|AGENT)$",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditLedgerResponse:
    """List audit entries. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Base query
        stmt = select(AuditLedger).where(AuditLedger.tenant_id == tenant_id).order_by(AuditLedger.created_at.desc())

        # Apply filters
        if event_type is not None:
            stmt = stmt.where(AuditLedger.event_type == event_type)
            filters_applied["event_type"] = event_type

        if entity_type is not None:
            stmt = stmt.where(AuditLedger.entity_type == entity_type)
            filters_applied["entity_type"] = entity_type

        if actor_type is not None:
            stmt = stmt.where(AuditLedger.actor_type == actor_type)
            filters_applied["actor_type"] = actor_type

        if created_after is not None:
            stmt = stmt.where(AuditLedger.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(AuditLedger.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count total
        count_stmt = select(func.count(AuditLedger.id)).where(AuditLedger.tenant_id == tenant_id)
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

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

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
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /audit/{entry_id} - O3 Audit Entry Detail
# =============================================================================


@router.get(
    "/audit/{entry_id}",
    response_model=AuditLedgerDetailItem,
    summary="Get audit entry detail (O3)",
    description="Audit Ledger Entry Detail: Full entry with state snapshots.",
)
async def get_audit_entry(
    request: Request,
    entry_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> AuditLedgerDetailItem:
    """Get audit entry detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        stmt = select(AuditLedger).where(AuditLedger.id == entry_id).where(AuditLedger.tenant_id == tenant_id)

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /llm-runs - O2 LLM Run Records List
# =============================================================================


@router.get(
    "/llm-runs",
    response_model=LLMRunRecordsResponse,
    summary="List LLM run records (O2)",
    description="""
    LLM Run Records: Immutable execution records for every LLM run.

    This is the TRUST ANCHOR for execution verification.
    Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger).

    Answers:
    - Did this run really happen?
    - What provider, model, tokens, cost?
    - What was the execution outcome?
    """,
)
async def list_llm_run_records(
    request: Request,
    # Optional filters
    run_id: Annotated[Optional[str], Query(description="Filter by run ID")] = None,
    provider: Annotated[Optional[str], Query(description="Filter by provider: anthropic, openai, stub")] = None,
    model: Annotated[Optional[str], Query(description="Filter by model name")] = None,
    execution_status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: SUCCEEDED, FAILED, ABORTED, TIMEOUT",
            pattern="^(SUCCEEDED|FAILED|ABORTED|TIMEOUT)$",
        ),
    ] = None,
    is_synthetic: Annotated[Optional[bool], Query(description="Filter by synthetic flag")] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunRecordsResponse:
    """List LLM run records. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Base query
        stmt = select(LLMRunRecord).where(LLMRunRecord.tenant_id == tenant_id).order_by(LLMRunRecord.created_at.desc())

        # Apply filters
        if run_id is not None:
            stmt = stmt.where(LLMRunRecord.run_id == run_id)
            filters_applied["run_id"] = run_id

        if provider is not None:
            stmt = stmt.where(LLMRunRecord.provider == provider)
            filters_applied["provider"] = provider

        if model is not None:
            stmt = stmt.where(LLMRunRecord.model == model)
            filters_applied["model"] = model

        if execution_status is not None:
            stmt = stmt.where(LLMRunRecord.execution_status == execution_status)
            filters_applied["execution_status"] = execution_status

        if is_synthetic is not None:
            stmt = stmt.where(LLMRunRecord.is_synthetic == is_synthetic)
            filters_applied["is_synthetic"] = is_synthetic

        if created_after is not None:
            stmt = stmt.where(LLMRunRecord.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(LLMRunRecord.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count total
        count_stmt = select(func.count(LLMRunRecord.id)).where(LLMRunRecord.tenant_id == tenant_id)
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

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

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
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /llm-runs/{record_id} - O3 LLM Run Record Detail
# =============================================================================


@router.get(
    "/llm-runs/{record_id}",
    response_model=LLMRunRecordDetailItem,
    summary="Get LLM run record detail (O3)",
    description="LLM Run Record Detail: Full record with content hashes for verification.",
)
async def get_llm_run_record(
    request: Request,
    record_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> LLMRunRecordDetailItem:
    """Get LLM run record detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        stmt = select(LLMRunRecord).where(LLMRunRecord.id == record_id).where(LLMRunRecord.tenant_id == tenant_id)

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /system - O2 System Records List
# =============================================================================


@router.get(
    "/system",
    response_model=SystemRecordsResponse,
    summary="List system records (O2)",
    description="""
    System Records: Immutable records for system-level events.

    NOT infra noise or stdout spam. YES:
    - Worker restarts
    - Deployment changes
    - Schema migrations
    - Auth / permission changes

    Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger).
    """,
)
async def list_system_records(
    request: Request,
    # Optional filters
    component: Annotated[
        Optional[str],
        Query(
            description="Filter by component: worker, api, scheduler, db, auth, migration",
            pattern="^(worker|api|scheduler|db|auth|migration)$",
        ),
    ] = None,
    event_type: Annotated[
        Optional[str],
        Query(
            description="Filter by event type: STARTUP, SHUTDOWN, RESTART, DEPLOY, MIGRATION, AUTH_CHANGE, CONFIG_CHANGE, ERROR, HEALTH_CHECK",
        ),
    ] = None,
    severity: Annotated[
        Optional[str],
        Query(
            description="Filter by severity: INFO, WARN, CRITICAL",
            pattern="^(INFO|WARN|CRITICAL)$",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
    # Dependencies
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemRecordsResponse:
    """List system records. READ-ONLY."""

    tenant_id = get_tenant_id_from_auth(request)
    filters_applied: dict[str, Any] = {"tenant_id": tenant_id}

    try:
        # Base query - system records can be tenant-specific or system-wide (NULL)
        # For customer console, show tenant-specific + system-wide records
        stmt = (
            select(SystemRecord)
            .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
            .order_by(SystemRecord.created_at.desc())
        )

        # Apply filters
        if component is not None:
            stmt = stmt.where(SystemRecord.component == component)
            filters_applied["component"] = component

        if event_type is not None:
            stmt = stmt.where(SystemRecord.event_type == event_type)
            filters_applied["event_type"] = event_type

        if severity is not None:
            stmt = stmt.where(SystemRecord.severity == severity)
            filters_applied["severity"] = severity

        if created_after is not None:
            stmt = stmt.where(SystemRecord.created_at >= created_after)
            filters_applied["created_after"] = created_after.isoformat()

        if created_before is not None:
            stmt = stmt.where(SystemRecord.created_at <= created_before)
            filters_applied["created_before"] = created_before.isoformat()

        # Count total
        count_stmt = select(func.count(SystemRecord.id)).where(
            (SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None))
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

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        entries = result.scalars().all()

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
            filters_applied=filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /system/{record_id} - O3 System Record Detail
# =============================================================================


@router.get(
    "/system/{record_id}",
    response_model=SystemRecordDetailItem,
    summary="Get system record detail (O3)",
    description="System Record Detail: Full record with details payload.",
)
async def get_system_record(
    request: Request,
    record_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SystemRecordDetailItem:
    """Get system record detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)

    try:
        # System records can be tenant-specific or system-wide
        stmt = (
            select(SystemRecord)
            .where(SystemRecord.id == record_id)
            .where((SystemRecord.tenant_id == tenant_id) | (SystemRecord.tenant_id.is_(None)))
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )
