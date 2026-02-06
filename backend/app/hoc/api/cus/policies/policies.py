# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Unified POLICIES domain facade - customer-only production API
# Callers: Customer Console frontend, SDSR validation (same API)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: POLICIES Domain - One Facade Architecture, PIN-412
#
# GOVERNANCE NOTE:
# This is the ONE facade for POLICIES domain.
# All policy rules and limits data flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Unified Policies API (L2)

Customer-facing endpoints for viewing policy rules and limits.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/policies/rules           → O2 list of policy rules
- GET /api/v1/policies/rules/{rule_id} → O3 rule detail
- GET /api/v1/policies/limits          → O2 list of limits
- GET /api/v1/policies/limits/{limit_id} → O3 limit detail

Architecture:
- ONE facade for all POLICIES needs (rules + limits)
- Queries PolicyRule, PolicyRuleIntegrity, Limit, LimitIntegrity tables
- Tenant isolation via auth_context (not header)
- SDSR validates this same production API
"""

import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from app.auth.gateway_middleware import get_auth_context
from app.schemas.response import wrap_dict
# L4 operation registry dispatch (migrated from L5 facade per HOC Topology V2.0.0)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)

# =============================================================================
# Environment Configuration
# =============================================================================

_CURRENT_ENVIRONMENT = os.getenv("AOS_ENVIRONMENT", "preflight")


def require_preflight() -> None:
    """Guard for preflight-only endpoints (O4, O5)."""
    if _CURRENT_ENVIRONMENT != "preflight":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "preflight_only",
                "message": "This endpoint is only available in preflight console.",
            },
        )


# =============================================================================
# Response Models — Policy Rules (O2)
# =============================================================================


class PolicyRuleSummary(BaseModel):
    """O2 Result Shape for policy rules."""

    rule_id: str
    name: str
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    source: str  # MANUAL, SYSTEM, LEARNED
    status: str  # ACTIVE, RETIRED
    created_at: datetime
    created_by: Optional[str]
    integrity_status: str  # VERIFIED, DEGRADED, FAILED
    integrity_score: Decimal
    trigger_count_30d: int
    last_triggered_at: Optional[datetime]


class RulesListResponse(BaseModel):
    """GET /rules response (O2)."""

    items: List[PolicyRuleSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class PolicyRuleDetailResponse(BaseModel):
    """GET /rules/{rule_id} response (O3)."""

    rule_id: str
    name: str
    description: Optional[str]
    enforcement_mode: str
    scope: str
    source: str
    status: str
    created_at: datetime
    created_by: Optional[str]
    updated_at: Optional[datetime]
    integrity_status: str
    integrity_score: Decimal
    trigger_count_30d: int
    last_triggered_at: Optional[datetime]
    # O3 additions
    rule_definition: Optional[dict] = None
    violation_count_total: int = 0


# =============================================================================
# Response Models — Limits (O2)
# =============================================================================


class LimitSummary(BaseModel):
    """O2 Result Shape for limits."""

    limit_id: str
    name: str
    limit_category: str  # BUDGET, RATE, THRESHOLD
    limit_type: str  # COST_USD, TOKENS_*, REQUESTS_*, etc.
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
    enforcement: str  # BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT
    status: str  # ACTIVE, DISABLED
    max_value: Decimal
    window_seconds: Optional[int]  # For RATE limits
    reset_period: Optional[str]  # For BUDGET limits: DAILY, WEEKLY, MONTHLY, NONE
    integrity_status: str  # VERIFIED, DEGRADED, FAILED
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime


class LimitsListResponse(BaseModel):
    """GET /limits response (O2)."""

    items: List[LimitSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class LimitDetailResponse(BaseModel):
    """GET /limits/{limit_id} response (O3)."""

    limit_id: str
    name: str
    description: Optional[str]
    limit_category: str
    limit_type: str
    scope: str
    enforcement: str
    status: str
    max_value: Decimal
    window_seconds: Optional[int]
    reset_period: Optional[str]
    integrity_status: str
    integrity_score: Decimal
    breach_count_30d: int
    last_breached_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    # O3 additions
    current_value: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


# =============================================================================
# Router
# =============================================================================


router = APIRouter(
    prefix="/api/v1/policies",
    tags=["policies"],
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
# GET /rules - O2 Policy Rules List
# =============================================================================


@router.get(
    "/rules",
    response_model=RulesListResponse,
    summary="List policy rules (O2)",
    description="""
    Returns paginated list of policy rules.
    Tenant isolation enforced via auth_context.
    Includes integrity status and trigger statistics.
    """,
)
async def list_policy_rules(
    request: Request,
    # Status filter
    status: Annotated[
        str,
        Query(
            description="Rule status: ACTIVE or RETIRED",
            pattern="^(ACTIVE|RETIRED)$",
        ),
    ] = "ACTIVE",
    # Optional filters
    enforcement_mode: Annotated[
        Optional[str],
        Query(
            description="Filter by enforcement mode: BLOCK, WARN, AUDIT, DISABLED",
            pattern="^(BLOCK|WARN|AUDIT|DISABLED)$",
        ),
    ] = None,
    scope: Annotated[
        Optional[str],
        Query(
            description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT",
            pattern="^(GLOBAL|TENANT|PROJECT|AGENT)$",
        ),
    ] = None,
    source: Annotated[
        Optional[str],
        Query(
            description="Filter by source: MANUAL, SYSTEM, LEARNED",
            pattern="^(MANUAL|SYSTEM|LEARNED)$",
        ),
    ] = None,
    rule_type: Annotated[
        Optional[str],
        Query(
            description="Filter by rule type: SYSTEM, SAFETY, ETHICAL, TEMPORAL (PIN-411 Gap Closure)",
            pattern="^(SYSTEM|SAFETY|ETHICAL|TEMPORAL)$",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max rules to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of rules to skip")] = 0,
    # Dependencies
    session = Depends(get_session_dep),
) -> RulesListResponse:
    """List policy rules with unified query filters. READ-ONLY."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_policy_rules",
                    "status": status,
                    "enforcement_mode": enforcement_mode,
                    "scope": scope,
                    "source": source,
                    "rule_type": rule_type,
                    "created_after": created_after,
                    "created_before": created_before,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        # Convert facade result to API response
        items = [
            PolicyRuleSummary(
                rule_id=item.rule_id,
                name=item.name,
                enforcement_mode=item.enforcement_mode,
                scope=item.scope,
                source=item.source,
                status=item.status,
                created_at=item.created_at,
                created_by=item.created_by,
                integrity_status=item.integrity_status,
                integrity_score=item.integrity_score,
                trigger_count_30d=item.trigger_count_30d,
                last_triggered_at=item.last_triggered_at,
            )
            for item in result.items
        ]

        return RulesListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /rules/{rule_id} - O3 Policy Rule Detail
# =============================================================================


@router.get(
    "/rules/{rule_id}",
    response_model=PolicyRuleDetailResponse,
    summary="Get policy rule detail (O3)",
    description="Returns detailed information about a specific policy rule.",
)
async def get_policy_rule_detail(
    request: Request,
    rule_id: str,
    session = Depends(get_session_dep),
) -> PolicyRuleDetailResponse:
    """Get policy rule detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_policy_rule_detail",
                    "rule_id": rule_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        if not result:
            raise HTTPException(status_code=404, detail="Policy rule not found")

        return PolicyRuleDetailResponse(
            rule_id=result.rule_id,
            name=result.name,
            description=result.description,
            enforcement_mode=result.enforcement_mode,
            scope=result.scope,
            source=result.source,
            status=result.status,
            created_at=result.created_at,
            created_by=result.created_by,
            updated_at=result.updated_at,
            integrity_status=result.integrity_status,
            integrity_score=result.integrity_score,
            trigger_count_30d=result.trigger_count_30d,
            last_triggered_at=result.last_triggered_at,
            rule_definition=result.rule_definition,
            violation_count_total=result.violation_count_total,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /limits - O2 Limits List
# =============================================================================


@router.get(
    "/limits",
    response_model=LimitsListResponse,
    summary="List limits (O2)",
    description="""
    Returns paginated list of limits.
    Tenant isolation enforced via auth_context.
    Includes integrity status and breach statistics.
    """,
)
async def list_limits(
    request: Request,
    # Category filter
    category: Annotated[
        str,
        Query(
            alias="type",
            description="Limit category: BUDGET, RATE, or THRESHOLD",
            pattern="^(BUDGET|RATE|THRESHOLD)$",
        ),
    ] = "BUDGET",
    # Status filter
    status: Annotated[
        str,
        Query(
            description="Limit status: ACTIVE or DISABLED",
            pattern="^(ACTIVE|DISABLED)$",
        ),
    ] = "ACTIVE",
    # Optional filters
    scope: Annotated[
        Optional[str],
        Query(
            description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT, PROVIDER",
            pattern="^(GLOBAL|TENANT|PROJECT|AGENT|PROVIDER)$",
        ),
    ] = None,
    enforcement: Annotated[
        Optional[str],
        Query(
            description="Filter by enforcement: BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT",
            pattern="^(BLOCK|WARN|REJECT|QUEUE|DEGRADE|ALERT)$",
        ),
    ] = None,
    limit_type: Annotated[
        Optional[str],
        Query(
            description="Filter by limit_type. Supports prefix match, e.g. RUNS_*, TOKENS_*, RISK_CEILING, COOLDOWN (PIN-411 Gap Closure)",
        ),
    ] = None,
    created_after: Annotated[Optional[datetime], Query(description="Filter by created_at >= value")] = None,
    created_before: Annotated[Optional[datetime], Query(description="Filter by created_at <= value")] = None,
    # Pagination
    max_limit: Annotated[int, Query(ge=1, le=100, alias="limit", description="Max limits to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of limits to skip")] = 0,
    # Dependencies
    session = Depends(get_session_dep),
) -> LimitsListResponse:
    """List limits with unified query filters. READ-ONLY."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_limits",
                    "category": category,
                    "status": status,
                    "scope": scope,
                    "enforcement": enforcement,
                    "limit_type": limit_type,
                    "created_after": created_after,
                    "created_before": created_before,
                    "limit": max_limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        # Convert facade result to API response
        items = [
            LimitSummary(
                limit_id=item.limit_id,
                name=item.name,
                limit_category=item.limit_category,
                limit_type=item.limit_type,
                scope=item.scope,
                enforcement=item.enforcement,
                status=item.status,
                max_value=item.max_value,
                window_seconds=item.window_seconds,
                reset_period=item.reset_period,
                integrity_status=item.integrity_status,
                integrity_score=item.integrity_score,
                breach_count_30d=item.breach_count_30d,
                last_breached_at=item.last_breached_at,
                created_at=item.created_at,
            )
            for item in result.items
        ]

        return LimitsListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /limits/{limit_id} - O3 Limit Detail
# =============================================================================


@router.get(
    "/limits/{limit_id}",
    response_model=LimitDetailResponse,
    summary="Get limit detail (O3)",
    description="Returns detailed information about a specific limit.",
)
async def get_limit_detail(
    request: Request,
    limit_id: str,
    session = Depends(get_session_dep),
) -> LimitDetailResponse:
    """Get limit detail (O3). Tenant isolation enforced."""

    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_limit_detail",
                    "limit_id": limit_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        if not result:
            raise HTTPException(status_code=404, detail="Limit not found")

        return LimitDetailResponse(
            limit_id=result.limit_id,
            name=result.name,
            description=result.description,
            limit_category=result.limit_category,
            limit_type=result.limit_type,
            scope=result.scope,
            enforcement=result.enforcement,
            status=result.status,
            max_value=result.max_value,
            window_seconds=result.window_seconds,
            reset_period=result.reset_period,
            integrity_status=result.integrity_status,
            integrity_score=result.integrity_score,
            breach_count_30d=result.breach_count_30d,
            last_breached_at=result.last_breached_at,
            created_at=result.created_at,
            updated_at=result.updated_at,
            current_value=result.current_value,
            utilization_percent=result.utilization_percent,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "query_failed", "message": str(e)},
        )


# =============================================================================
# GET /rules/{rule_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/rules/{rule_id}/evidence",
    summary="Get rule evidence (O4)",
    description="Returns enforcement context and impact. Preflight only.",
)
async def get_rule_evidence(
    request: Request,
    rule_id: str,
) -> dict[str, Any]:
    """Get rule evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return wrap_dict({
        "rule_id": rule_id,
        "recent_enforcements": [],
        "affected_runs": [],
        "violations_triggered": [],
    })


# =============================================================================
# GET /limits/{limit_id}/evidence - O4 Context (Preflight Only)
# =============================================================================


@router.get(
    "/limits/{limit_id}/evidence",
    summary="Get limit evidence (O4)",
    description="Returns breach history and impact. Preflight only.",
)
async def get_limit_evidence(
    request: Request,
    limit_id: str,
) -> dict[str, Any]:
    """Get limit evidence (O4). Preflight console only."""
    require_preflight()
    _ = get_tenant_id_from_auth(request)  # Enforce auth

    return wrap_dict({
        "limit_id": limit_id,
        "recent_breaches": [],
        "affected_runs": [],
        "usage_history": [],
    })


# =============================================================================
# Lessons Learned - Customer Facade (L2)
# Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11
# =============================================================================


class LessonSummaryResponse(BaseModel):
    """O2 Result Shape for lessons."""

    id: str
    lesson_type: str
    severity: Optional[str]
    title: str
    status: str
    source_event_type: str
    created_at: datetime
    has_proposed_action: bool


class LessonsListResponse(BaseModel):
    """GET /lessons response (O2)."""

    items: List[LessonSummaryResponse]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


class LessonDetailResponse(BaseModel):
    """GET /lessons/{id} response (O3)."""

    id: str
    lesson_type: str
    severity: Optional[str]
    source_event_id: Optional[str]
    source_event_type: str
    source_run_id: Optional[str]
    title: str
    description: str
    proposed_action: Optional[str]
    detected_pattern: Optional[dict[str, Any]]
    status: str
    draft_proposal_id: Optional[str]
    created_at: str
    converted_at: Optional[str]
    deferred_until: Optional[str]


class LessonStatsResponse(BaseModel):
    """Lesson statistics response."""

    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]


@router.get(
    "/lessons",
    response_model=LessonsListResponse,
    summary="List lessons learned (O2)",
    description="""
    Returns paginated list of lessons learned.
    Tenant isolation enforced via auth_context.
    """,
)
async def list_lessons(
    request: Request,
    # Optional filters
    lesson_type: Annotated[
        Optional[str],
        Query(
            description="Filter by type: failure, near_threshold, critical_success",
            pattern="^(failure|near_threshold|critical_success)$",
        ),
    ] = None,
    status: Annotated[
        Optional[str],
        Query(
            description="Filter by status: pending, converted_to_draft, deferred, dismissed",
            pattern="^(pending|converted_to_draft|deferred|dismissed)$",
        ),
    ] = None,
    severity: Annotated[
        Optional[str],
        Query(
            description="Filter by severity: CRITICAL, HIGH, MEDIUM, LOW",
            pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$",
        ),
    ] = None,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max lessons to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of lessons to skip")] = 0,
    # Dependencies
    session = Depends(get_session_dep),
) -> LessonsListResponse:
    """List lessons learned (O2). READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "policies.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "list_lessons",
                "lesson_type": lesson_type,
                "status": status,
                "severity": severity,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    items = [
        LessonSummaryResponse(
            id=item.id,
            lesson_type=item.lesson_type,
            severity=item.severity,
            title=item.title,
            status=item.status,
            source_event_type=item.source_event_type,
            created_at=item.created_at,
            has_proposed_action=item.has_proposed_action,
        )
        for item in result.items
    ]

    return LessonsListResponse(
        items=items,
        total=result.total,
        has_more=result.has_more,
        filters_applied=result.filters_applied,
    )


@router.get(
    "/lessons/stats",
    response_model=LessonStatsResponse,
    summary="Get lesson statistics (O1)",
    description="Returns lesson counts by type and status.",
)
async def get_lesson_stats(
    request: Request,
    session = Depends(get_session_dep),
) -> LessonStatsResponse:
    """Get lesson statistics (O1). READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "policies.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_lesson_stats",
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    return LessonStatsResponse(
        total=result.total,
        by_type=result.by_type,
        by_status=result.by_status,
    )


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetailResponse,
    summary="Get lesson detail (O3)",
    description="Returns detailed information about a specific lesson.",
)
async def get_lesson_detail(
    request: Request,
    lesson_id: str,
    session = Depends(get_session_dep),
) -> LessonDetailResponse:
    """Get lesson detail (O3). READ-ONLY customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    op = await registry.execute(
        "policies.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_lesson_detail",
                "lesson_id": lesson_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
    result = op.data

    if not result:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return LessonDetailResponse(
        id=result.id,
        lesson_type=result.lesson_type,
        severity=result.severity,
        source_event_id=result.source_event_id,
        source_event_type=result.source_event_type,
        source_run_id=result.source_run_id,
        title=result.title,
        description=result.description,
        proposed_action=result.proposed_action,
        detected_pattern=result.detected_pattern,
        status=result.status,
        draft_proposal_id=result.draft_proposal_id,
        created_at=result.created_at,
        converted_at=result.converted_at,
        deferred_until=result.deferred_until,
    )


# =============================================================================
# Policy State - ACT-O4 (PIN-411 Gap Closure)
# =============================================================================


class PolicyStateResponse(BaseModel):
    """Policy layer state summary (ACT-O4)."""

    total_policies: int
    active_policies: int
    drafts_pending_review: int
    conflicts_detected: int
    violations_24h: int
    lessons_pending_action: int
    last_updated: datetime


@router.get(
    "/state",
    response_model=PolicyStateResponse,
    summary="Get policy layer state (ACT-O4)",
    description="""
    Returns synthesized snapshot of the governance system.
    Shows what is currently being enforced.
    """,
)
async def get_policy_state(
    request: Request,
    session = Depends(get_session_dep),
) -> PolicyStateResponse:
    """Get policy layer state (ACT-O4). Customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_policy_state",
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        return PolicyStateResponse(
            total_policies=result.total_policies,
            active_policies=result.active_policies,
            drafts_pending_review=result.drafts_pending_review,
            conflicts_detected=result.conflicts_detected,
            violations_24h=result.violations_24h,
            lessons_pending_action=result.lessons_pending_action,
            last_updated=result.last_updated,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "state_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Metrics - ACT-O5 (PIN-411 Gap Closure)
# =============================================================================


class PolicyMetricsResponse(BaseModel):
    """Policy enforcement metrics (ACT-O5)."""

    total_evaluations: int
    total_blocks: int
    total_allows: int
    block_rate: float
    avg_evaluation_ms: float
    violations_by_type: dict[str, int]
    evaluations_by_action: dict[str, int]
    window_hours: int


@router.get(
    "/metrics",
    response_model=PolicyMetricsResponse,
    summary="Get policy metrics (ACT-O5)",
    description="""
    Returns policy enforcement effectiveness metrics.
    Shows how policies are performing.
    """,
)
async def get_policy_metrics(
    request: Request,
    hours: Annotated[int, Query(ge=1, le=720, description="Time window in hours")] = 24,
    session = Depends(get_session_dep),
) -> PolicyMetricsResponse:
    """Get policy metrics (ACT-O5). Customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_policy_metrics",
                    "hours": hours,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        return PolicyMetricsResponse(
            total_evaluations=result.total_evaluations,
            total_blocks=result.total_blocks,
            total_allows=result.total_allows,
            block_rate=result.block_rate,
            avg_evaluation_ms=result.avg_evaluation_ms,
            violations_by_type=result.violations_by_type,
            evaluations_by_action=result.evaluations_by_action,
            window_hours=result.window_hours,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "metrics_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Conflicts - DFT-O4 (PIN-411 Gap Closure)
# Uses PolicyConflictEngine for static conflict detection
# Conflict Types: SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE
# =============================================================================


class PolicyConflictResponse(BaseModel):
    """Policy conflict summary (DFT-O4 spec)."""

    policy_a_id: str
    policy_b_id: str
    policy_a_name: str
    policy_b_name: str
    conflict_type: str  # SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE
    severity: str  # BLOCKING, WARNING
    explanation: str
    recommended_action: str
    detected_at: datetime


class ConflictsListResponse(BaseModel):
    """GET /conflicts response (DFT-O4)."""

    items: List[PolicyConflictResponse]
    total: int
    unresolved_count: int
    computed_at: datetime


@router.get(
    "/conflicts",
    response_model=ConflictsListResponse,
    summary="Detect policy conflicts (DFT-O4)",
    description="""
    Detects logical contradictions, overlaps, or unsafe coexistence between policies.

    Conflict Types:
    - SCOPE_OVERLAP: Same scope, incompatible behavior
    - THRESHOLD_CONTRADICTION: Limits cannot both be satisfied
    - TEMPORAL_CONFLICT: Time windows clash
    - PRIORITY_OVERRIDE: Lower-priority rule nullifies higher-priority

    Severity:
    - BLOCKING: Activation must be prevented
    - WARNING: Allowed but requires review
    """,
)
async def list_policy_conflicts(
    request: Request,
    policy_id: Annotated[
        Optional[str],
        Query(description="Filter to conflicts involving this policy"),
    ] = None,
    severity: Annotated[
        Optional[str],
        Query(description="Filter by severity: BLOCKING, WARNING"),
    ] = None,
    include_resolved: Annotated[bool, Query(description="Include resolved conflicts")] = False,
    session = Depends(get_session_dep),
) -> ConflictsListResponse:
    """Detect policy conflicts (DFT-O4). Uses PolicyConflictEngine via facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_policy_conflicts",
                    "policy_id": policy_id,
                    "severity": severity,
                    "include_resolved": include_resolved,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        items = [
            PolicyConflictResponse(
                policy_a_id=item.policy_a_id,
                policy_b_id=item.policy_b_id,
                policy_a_name=item.policy_a_name,
                policy_b_name=item.policy_b_name,
                conflict_type=item.conflict_type,
                severity=item.severity,
                explanation=item.explanation,
                recommended_action=item.recommended_action,
                detected_at=item.detected_at,
            )
            for item in result.items
        ]

        return ConflictsListResponse(
            items=items,
            total=result.total,
            unresolved_count=result.unresolved_count,
            computed_at=result.computed_at,
        )

    except Exception as e:
        logger.exception("Failed to detect policy conflicts")
        raise HTTPException(
            status_code=500,
            detail={"error": "conflicts_detection_failed", "message": str(e)},
        )


# =============================================================================
# Policy Dependencies - DFT-O5 (PIN-411 Gap Closure)
# Uses PolicyDependencyEngine for structural relationship analysis
# Dependency Types: EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
# =============================================================================


class PolicyDependencyRelation(BaseModel):
    """A dependency relationship detail."""

    policy_id: str
    policy_name: str
    dependency_type: str  # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
    reason: str


class PolicyNodeResponse(BaseModel):
    """A node in the dependency graph (DFT-O5 spec)."""

    id: str
    name: str
    rule_type: str  # SYSTEM, SAFETY, ETHICAL, TEMPORAL
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    status: str  # ACTIVE, RETIRED
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    depends_on: List[PolicyDependencyRelation]
    required_by: List[PolicyDependencyRelation]


class PolicyDependencyEdge(BaseModel):
    """A dependency edge in the graph."""

    policy_id: str
    depends_on_id: str
    policy_name: str
    depends_on_name: str
    dependency_type: str  # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
    reason: str


class DependencyGraphResponse(BaseModel):
    """GET /dependencies response (DFT-O5)."""

    nodes: List[PolicyNodeResponse]
    edges: List[PolicyDependencyEdge]
    nodes_count: int
    edges_count: int
    computed_at: datetime


@router.get(
    "/dependencies",
    response_model=DependencyGraphResponse,
    summary="Get policy dependency graph (DFT-O5)",
    description="""
    Computes structural relationships between policies.

    Dependency Types:
    - EXPLICIT: Declared via parent_rule_id or requires_policy_id
    - IMPLICIT_SCOPE: Same scope, rely on each other's assumptions
    - IMPLICIT_LIMIT: Limit-based dependencies (e.g., cooldown depends on run quota)

    Each node shows:
    - depends_on: Policies this one requires
    - required_by: Policies that depend on this one

    Enforcement Rules:
    - Cannot delete a policy with active required_by
    - Cannot activate a policy if depends_on is inactive
    """,
)
async def get_policy_dependencies(
    request: Request,
    policy_id: Annotated[
        Optional[str],
        Query(description="Filter to dependencies involving this policy"),
    ] = None,
    session = Depends(get_session_dep),
) -> DependencyGraphResponse:
    """Get policy dependency graph (DFT-O5). Uses PolicyDependencyEngine via facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "get_policy_dependencies",
                    "policy_id": policy_id,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        nodes = [
            PolicyNodeResponse(
                id=n.id,
                name=n.name,
                rule_type=n.rule_type,
                scope=n.scope,
                status=n.status,
                enforcement_mode=n.enforcement_mode,
                depends_on=[
                    PolicyDependencyRelation(
                        policy_id=d.policy_id,
                        policy_name=d.policy_name,
                        dependency_type=d.dependency_type,
                        reason=d.reason,
                    )
                    for d in n.depends_on
                ],
                required_by=[
                    PolicyDependencyRelation(
                        policy_id=d.policy_id,
                        policy_name=d.policy_name,
                        dependency_type=d.dependency_type,
                        reason=d.reason,
                    )
                    for d in n.required_by
                ],
            )
            for n in result.nodes
        ]

        edges = [
            PolicyDependencyEdge(
                policy_id=e.policy_id,
                depends_on_id=e.depends_on_id,
                policy_name=e.policy_name,
                depends_on_name=e.depends_on_name,
                dependency_type=e.dependency_type,
                reason=e.reason,
            )
            for e in result.edges
        ]

        return DependencyGraphResponse(
            nodes=nodes,
            edges=edges,
            nodes_count=result.nodes_count,
            edges_count=result.edges_count,
            computed_at=result.computed_at,
        )

    except Exception as e:
        logger.exception("Failed to compute dependency graph")
        raise HTTPException(
            status_code=500,
            detail={"error": "dependencies_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Violations - VIO-O1 (PIN-411 Gap Closure - Unified Facade)
# =============================================================================


class PolicyViolationSummary(BaseModel):
    """Policy violation summary (VIO-O1)."""

    id: str
    policy_id: Optional[str]
    policy_name: Optional[str]
    violation_type: str  # cost, quota, rate, temporal, safety, ethical
    severity: float
    source: str  # guard, sim, runtime
    agent_id: Optional[str]
    description: Optional[str]
    occurred_at: datetime
    is_synthetic: bool = False


class ViolationsListResponse(BaseModel):
    """GET /violations response (VIO-O1)."""

    items: List[PolicyViolationSummary]
    total: int
    has_more: bool
    filters_applied: dict[str, Any]


@router.get(
    "/violations",
    response_model=ViolationsListResponse,
    summary="List policy violations (VIO-O1)",
    description="""
    Returns unified list of policy violations.
    A violation is a normalized governance fact, regardless of origin.
    """,
)
async def list_policy_violations(
    request: Request,
    # Filters
    violation_type: Annotated[
        Optional[str],
        Query(
            description="Filter by type: cost, quota, rate, temporal, safety, ethical",
            pattern="^(cost|quota|rate|temporal|safety|ethical)$",
        ),
    ] = None,
    source: Annotated[
        Optional[str],
        Query(
            description="Filter by source: guard, sim, runtime, cost (PIN-411 Gap Closure)",
            pattern="^(guard|sim|runtime|cost)$",
        ),
    ] = None,
    severity_min: Annotated[
        Optional[float],
        Query(ge=0.0, le=1.0, description="Minimum severity (0.0-1.0)"),
    ] = None,
    violation_kind: Annotated[
        Optional[str],
        Query(
            description="Filter by violation kind: STANDARD, ANOMALY, DIVERGENCE (PIN-411 Gap Closure)",
            pattern="^(STANDARD|ANOMALY|DIVERGENCE)$",
        ),
    ] = None,
    hours: Annotated[int, Query(ge=1, le=720, description="Time window in hours")] = 24,
    include_synthetic: Annotated[bool, Query(description="Include synthetic/simulated")] = False,
    # Pagination
    limit: Annotated[int, Query(ge=1, le=100, description="Max items")] = 50,
    offset: Annotated[int, Query(ge=0, description="Offset")] = 0,
    session = Depends(get_session_dep),
) -> ViolationsListResponse:
    """List policy violations (VIO-O1). Unified customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_policy_violations",
                    "violation_type": violation_type,
                    "source": source,
                    "severity_min": severity_min,
                    "violation_kind": violation_kind,
                    "hours": hours,
                    "include_synthetic": include_synthetic,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        items = [
            PolicyViolationSummary(
                id=item.id,
                policy_id=item.policy_id,
                policy_name=item.policy_name,
                violation_type=item.violation_type,
                severity=item.severity,
                source=item.source,
                agent_id=item.agent_id,
                description=item.description,
                occurred_at=item.occurred_at,
                is_synthetic=item.is_synthetic,
            )
            for item in result.items
        ]

        return ViolationsListResponse(
            items=items,
            total=result.total,
            has_more=result.has_more,
            filters_applied=result.filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "violations_query_failed", "message": str(e)},
        )


# =============================================================================
# Policy Budgets - THR-O2 (PIN-411 Gap Closure)
# =============================================================================


class BudgetDefinitionSummary(BaseModel):
    """Budget definition summary (THR-O2)."""

    id: str
    name: str
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    max_value: Decimal
    reset_period: Optional[str]  # DAILY, WEEKLY, MONTHLY, NONE
    enforcement: str  # BLOCK, WARN
    status: str  # ACTIVE, DISABLED
    current_usage: Optional[Decimal] = None
    utilization_percent: Optional[float] = None


class BudgetsListResponse(BaseModel):
    """GET /budgets response (THR-O2)."""

    items: List[BudgetDefinitionSummary]
    total: int
    filters_applied: dict[str, Any]


@router.get(
    "/budgets",
    response_model=BudgetsListResponse,
    summary="List budget definitions (THR-O2)",
    description="""
    Returns budget definitions (enforcement limits).
    Budgets define spending ceilings, not analytics.
    """,
)
async def list_budget_definitions(
    request: Request,
    scope: Annotated[
        Optional[str],
        Query(
            description="Filter by scope: GLOBAL, TENANT, PROJECT, AGENT",
            pattern="^(GLOBAL|TENANT|PROJECT|AGENT)$",
        ),
    ] = None,
    status: Annotated[
        str,
        Query(
            description="Filter by status: ACTIVE, DISABLED",
            pattern="^(ACTIVE|DISABLED)$",
        ),
    ] = "ACTIVE",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    session = Depends(get_session_dep),
) -> BudgetsListResponse:
    """List budget definitions (THR-O2). Customer facade."""

    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_budgets",
                    "scope": scope,
                    "status": status,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        # Map facade result to API response
        items = [
            BudgetDefinitionSummary(
                id=item.id,
                name=item.name,
                scope=item.scope,
                max_value=item.max_value,
                reset_period=item.reset_period,
                enforcement=item.enforcement,
                status=item.status,
                current_usage=item.current_usage,
                utilization_percent=item.utilization_percent,
            )
            for item in result.items
        ]

        return BudgetsListResponse(
            items=items,
            total=result.total,
            filters_applied=result.filters_applied,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "budgets_query_failed", "message": str(e)},
        )


# =============================================================================
# ACT-O3: Policy Requests (Pending Approvals)
# =============================================================================


class PolicyRequestSummary(BaseModel):
    """Summary of a pending policy request (draft proposal)."""

    id: str
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict
    status: str
    created_at: datetime
    triggering_feedback_count: int
    days_pending: int


class PolicyRequestsListResponse(BaseModel):
    """Response for policy requests list (ACT-O3)."""

    items: List[PolicyRequestSummary]
    total: int
    pending_count: int
    filters_applied: dict


@router.get(
    "/requests",
    response_model=PolicyRequestsListResponse,
    summary="List pending policy requests (ACT-O3)",
    description="""
    Returns pending policy requests (draft proposals awaiting human approval).
    These are recommendations generated by the system that need human review.

    PB-S4 Contract: Proposals are INERT until human approval.
    """,
)
async def list_policy_requests(
    request: Request,
    status: Annotated[
        str,
        Query(
            description="Filter by status: draft, approved, rejected (default: draft)",
            pattern="^(draft|approved|rejected)$",
        ),
    ] = "draft",
    proposal_type: Annotated[
        Optional[str],
        Query(
            description="Filter by proposal type: rate_limit, cost_cap, retry_policy",
        ),
    ] = None,
    days_old: Annotated[
        Optional[int],
        Query(
            ge=1,
            le=365,
            description="Filter to requests older than N days",
        ),
    ] = None,
    include_synthetic: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session = Depends(get_session_dep),
) -> PolicyRequestsListResponse:
    """List pending policy requests (ACT-O3). Customer facade."""
    tenant_id = get_tenant_id_from_auth(request)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.query",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "method": "list_policy_requests",
                    "status": status,
                    "proposal_type": proposal_type,
                    "days_old": days_old,
                    "include_synthetic": include_synthetic,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        result = op.data

        items = [
            PolicyRequestSummary(
                id=item.id,
                proposal_name=item.proposal_name,
                proposal_type=item.proposal_type,
                rationale=item.rationale,
                proposed_rule=item.proposed_rule,
                status=item.status,
                created_at=item.created_at,
                triggering_feedback_count=item.triggering_feedback_count,
                days_pending=item.days_pending,
            )
            for item in result.items
        ]

        return PolicyRequestsListResponse(
            items=items,
            total=result.total,
            pending_count=result.pending_count,
            filters_applied=result.filters_applied,
        )

    except Exception as e:
        logger.exception("Failed to list policy requests")
        raise HTTPException(
            status_code=500,
            detail={"error": "policy_requests_query_failed", "message": str(e)},
        )
