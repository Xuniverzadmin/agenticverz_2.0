# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-6 Overview highlights facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.hoc.api.cus.overview.overview import (
    DomainCount,
    HighlightsResponse,
    SystemPulse,
    get_tenant_id_from_auth,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class OverviewHighlightsMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class OverviewHighlightsPublicResponse(BaseModel):
    highlights: HighlightsResponse
    generated_at: str
    meta: OverviewHighlightsMeta


router = APIRouter(prefix="/cus/overview", tags=["cus-overview-public"])


def _to_rfc3339z(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _invalid_query(field: str, reason: str) -> None:
    raise HTTPException(
        status_code=400,
        detail={
            "code": "INVALID_QUERY",
            "message": "Invalid query parameters",
            "field_errors": [{"field": field, "reason": reason}],
        },
    )


def _unsupported_param(field: str, message: str) -> None:
    raise HTTPException(
        status_code=400,
        detail={
            "code": "UNSUPPORTED_PARAM",
            "message": message,
            "field_errors": [{"field": field, "reason": message}],
        },
    )


@router.get(
    "/highlights",
    response_model=OverviewHighlightsPublicResponse,
    summary="PR-6 Overview highlights facade endpoint",
)
async def get_overview_highlights_public(
    request: Request,
    session=Depends(get_session_dep),
) -> OverviewHighlightsPublicResponse:
    query_params = request.query_params
    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-6")
    if query_params:
        first_unknown = next(iter(query_params.keys()))
        _invalid_query(first_unknown, "unknown query parameter")

    tenant_id = get_tenant_id_from_auth(request)

    registry = get_operation_registry()
    op = await registry.execute(
        "overview.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"method": "get_highlights"},
        ),
    )

    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "OPERATION_FAILED",
                "message": op.error or "overview.query execution failed",
            },
        )

    result = op.data
    highlights = HighlightsResponse(
        pulse=SystemPulse(
            status=result.pulse.status,
            active_incidents=result.pulse.active_incidents,
            pending_decisions=result.pulse.pending_decisions,
            recent_breaches=result.pulse.recent_breaches,
            live_runs=result.pulse.live_runs,
            queued_runs=result.pulse.queued_runs,
        ),
        domain_counts=[
            DomainCount(
                domain=item.domain,
                total=item.total,
                pending=item.pending,
                critical=item.critical,
            )
            for item in result.domain_counts
        ],
        last_activity_at=result.last_activity_at,
    )

    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_REQUEST_ID_MISSING",
                "message": "Request id is missing from middleware context",
            },
        )

    correlation_id = request.headers.get("X-Correlation-ID")

    return OverviewHighlightsPublicResponse(
        highlights=highlights,
        generated_at=_to_rfc3339z(None),
        meta=OverviewHighlightsMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
