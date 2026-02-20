# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-7 Analytics usage facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class UsageResolution(str, Enum):
    HOUR = "hour"
    DAY = "day"


class UsageScope(str, Enum):
    ORG = "org"
    PROJECT = "project"
    ENV = "env"


class UsageWindow(BaseModel):
    from_ts: str
    to_ts: str
    resolution: UsageResolution


class UsageTotals(BaseModel):
    requests: int
    compute_units: int
    tokens: int


class UsageDataPoint(BaseModel):
    ts: str
    requests: int
    compute_units: int
    tokens: int


class UsageSignals(BaseModel):
    sources: list[str]
    freshness_sec: int


class AnalyticsUsageMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class AnalyticsUsagePublicResponse(BaseModel):
    window: UsageWindow
    totals: UsageTotals
    series: list[UsageDataPoint]
    signals: UsageSignals
    generated_at: str
    meta: AnalyticsUsageMeta


router = APIRouter(prefix="/cus/analytics", tags=["cus-analytics-public"])


_ALLOWED = {
    "from",
    "to",
    "resolution",
    "scope",
}


def get_tenant_id_from_auth(request: Request) -> str:
    """Extract tenant_id from auth context. Raises 401/403 if missing."""
    auth_context = get_auth_context(request)
    if auth_context is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "NOT_AUTHENTICATED", "message": "Authentication required."},
        )

    tenant_id = getattr(auth_context, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail={"code": "TENANT_REQUIRED", "message": "Tenant context required."},
        )
    return tenant_id


def _to_rfc3339z(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _invalid_query(field_errors: list[dict[str, str]], message: str = "Invalid query parameters") -> None:
    raise HTTPException(
        status_code=400,
        detail={
            "code": "INVALID_QUERY",
            "message": message,
            "field_errors": field_errors,
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


def _single_value(query_params, name: str, field_errors: list[dict[str, str]]) -> str | None:
    values = query_params.getlist(name)
    if not values:
        return None
    if len(values) > 1:
        field_errors.append({"field": name, "reason": "must be provided once"})
        return None
    return values[0]


def _parse_datetime_tz_required(
    query_params,
    name: str,
    field_errors: list[dict[str, str]],
) -> datetime | None:
    raw = _single_value(query_params, name, field_errors)
    if raw is None:
        field_errors.append({"field": name, "reason": "is required"})
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        field_errors.append({"field": name, "reason": "must be RFC3339/ISO8601"})
        return None

    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        field_errors.append({"field": name, "reason": "timezone is required"})
        return None

    return parsed


def _parse_resolution(query_params, field_errors: list[dict[str, str]]) -> UsageResolution:
    raw = _single_value(query_params, "resolution", field_errors)
    if raw is None:
        return UsageResolution.DAY
    try:
        return UsageResolution(raw)
    except ValueError:
        field_errors.append({"field": "resolution", "reason": "must be one of: hour, day"})
        return UsageResolution.DAY


def _parse_scope(query_params, field_errors: list[dict[str, str]]) -> UsageScope:
    raw = _single_value(query_params, "scope", field_errors)
    if raw is None:
        return UsageScope.ORG
    try:
        return UsageScope(raw)
    except ValueError:
        field_errors.append({"field": "scope", "reason": "must be one of: org, project, env"})
        return UsageScope.ORG


def _reject_unknown_params(query_params, allowed: set[str], field_errors: list[dict[str, str]]) -> None:
    for key in sorted(set(query_params.keys())):
        if key not in allowed:
            field_errors.append({"field": key, "reason": "unknown query parameter"})


@router.get(
    "/statistics/usage",
    response_model=AnalyticsUsagePublicResponse,
    summary="PR-7 Analytics usage facade endpoint",
)
async def get_usage_statistics_public(
    request: Request,
    session=Depends(get_session_dep),
) -> AnalyticsUsagePublicResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-7")

    field_errors: list[dict[str, str]] = []
    _reject_unknown_params(query_params, _ALLOWED, field_errors)

    from_ts = _parse_datetime_tz_required(query_params, "from", field_errors)
    to_ts = _parse_datetime_tz_required(query_params, "to", field_errors)
    resolution = _parse_resolution(query_params, field_errors)
    scope = _parse_scope(query_params, field_errors)

    if from_ts and to_ts:
        if from_ts >= to_ts:
            field_errors.append({"field": "from", "reason": "must be before 'to'"})
        if (to_ts - from_ts) > timedelta(days=90):
            field_errors.append({"field": "to", "reason": "time window cannot exceed 90 days"})

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)

    # L2 imports shared query enums from L5_schemas per pinned cross-layer exception.
    from app.hoc.cus.analytics.L5_schemas.query_types import (
        ResolutionType as FacadeResolution,
        ScopeType as FacadeScope,
    )

    registry = get_operation_registry()
    op = await registry.execute(
        "analytics.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "get_usage_statistics",
                "from_ts": from_ts,
                "to_ts": to_ts,
                "resolution": FacadeResolution(resolution.value),
                "scope": FacadeScope(scope.value),
            },
        ),
    )

    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "OPERATION_FAILED",
                "message": op.error or "analytics.query execution failed",
            },
        )

    result = op.data

    try:
        series = [UsageDataPoint.model_validate(point, from_attributes=True) for point in getattr(result, "series", [])]
        totals = UsageTotals.model_validate(result.totals, from_attributes=True)
        signals = UsageSignals.model_validate(result.signals, from_attributes=True)
        window = UsageWindow(
            from_ts=_to_rfc3339z(getattr(result.window, "from_ts", from_ts)),
            to_ts=_to_rfc3339z(getattr(result.window, "to_ts", to_ts)),
            resolution=UsageResolution(getattr(result.window, "resolution", resolution.value)),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate analytics usage payload",
                "field_errors": [{"field": "usage", "reason": str(exc)}],
            },
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

    return AnalyticsUsagePublicResponse(
        window=window,
        totals=totals,
        series=series,
        signals=signals,
        generated_at=_to_rfc3339z(None),
        meta=AnalyticsUsageMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
