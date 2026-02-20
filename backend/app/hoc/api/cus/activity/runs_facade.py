# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-1 Runs Facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.hoc.api.cus.activity.activity import (
    EvidenceHealth,
    ProviderType,
    RiskLevel,
    RunSource,
    RunStatus,
    RunSummaryV2,
    get_tenant_id_from_auth,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class RunsTopic(str, Enum):
    LIVE = "live"
    COMPLETED = "completed"


class RunsPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class RunsMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class RunsFacadeResponse(BaseModel):
    topic: RunsTopic
    runs: list[RunSummaryV2]
    total: int
    has_more: bool
    pagination: RunsPagination
    generated_at: str
    meta: RunsMeta


router = APIRouter(prefix="/cus/activity", tags=["cus-activity-facade"])


_LIVE_ALLOWED = {
    "topic",
    "project_id",
    "risk_level",
    "evidence_health",
    "source",
    "provider_type",
    "limit",
    "offset",
}

_COMPLETED_ALLOWED = {
    "topic",
    "project_id",
    "status",
    "risk_level",
    "completed_after",
    "completed_before",
    "limit",
    "offset",
}


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


def _parse_topic(query_params, field_errors: list[dict[str, str]]) -> RunsTopic | None:
    values = query_params.getlist("topic")
    if not values:
        field_errors.append({"field": "topic", "reason": "is required"})
        return None
    if len(values) > 1:
        field_errors.append({"field": "topic", "reason": "must be provided once"})
        return None
    raw = values[0]
    try:
        return RunsTopic(raw)
    except ValueError:
        field_errors.append({"field": "topic", "reason": "must be one of: live, completed"})
        return None


def _parse_int(
    query_params,
    name: str,
    default: int,
    minimum: int,
    maximum: int,
    field_errors: list[dict[str, str]],
) -> int:
    raw = _single_value(query_params, name, field_errors)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        field_errors.append({"field": name, "reason": "must be an integer"})
        return default
    if value < minimum or value > maximum:
        field_errors.append({"field": name, "reason": f"must be between {minimum} and {maximum}"})
        return default
    return value


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _parse_enum_list(query_params, name: str, enum_cls: type[Enum], field_errors: list[dict[str, str]]) -> list[str] | None:
    raw_values = query_params.getlist(name)
    if not raw_values:
        return None

    parsed: list[str] = []
    for raw in _dedupe(raw_values):
        try:
            parsed.append(enum_cls(raw).value)
        except ValueError:
            allowed = ", ".join([member.value for member in enum_cls])
            field_errors.append({"field": name, "reason": f"invalid value '{raw}'. Allowed: {allowed}"})
    return parsed if parsed else None


def _parse_datetime_tz(query_params, name: str, field_errors: list[dict[str, str]]) -> datetime | None:
    raw = _single_value(query_params, name, field_errors)
    if raw is None:
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


def _reject_unknown_params(query_params, allowed: set[str], field_errors: list[dict[str, str]]) -> None:
    for key in sorted(set(query_params.keys())):
        if key not in allowed:
            field_errors.append({"field": key, "reason": "unknown query parameter"})


def _to_run_summary_v2(item: Any) -> RunSummaryV2:
    return RunSummaryV2.model_validate(item, from_attributes=True)


@router.get(
    "/runs",
    response_model=RunsFacadeResponse,
    summary="PR-1 Runs facade endpoint",
)
async def list_runs_facade(
    request: Request,
    session=Depends(get_session_dep),
) -> RunsFacadeResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-1")

    field_errors: list[dict[str, str]] = []
    topic = _parse_topic(query_params, field_errors)

    if topic is not None:
        allowed = _LIVE_ALLOWED if topic == RunsTopic.LIVE else _COMPLETED_ALLOWED
        _reject_unknown_params(query_params, allowed, field_errors)

    limit = _parse_int(query_params, "limit", default=50, minimum=1, maximum=200, field_errors=field_errors)
    offset = _parse_int(
        query_params,
        "offset",
        default=0,
        minimum=0,
        maximum=2_147_483_647,
        field_errors=field_errors,
    )

    project_id = _single_value(query_params, "project_id", field_errors)

    risk_level = _parse_enum_list(query_params, "risk_level", RiskLevel, field_errors)
    completed_after = _parse_datetime_tz(query_params, "completed_after", field_errors)
    completed_before = _parse_datetime_tz(query_params, "completed_before", field_errors)

    status = _parse_enum_list(query_params, "status", RunStatus, field_errors)
    evidence_health = _parse_enum_list(query_params, "evidence_health", EvidenceHealth, field_errors)
    source = _parse_enum_list(query_params, "source", RunSource, field_errors)
    provider_type = _parse_enum_list(query_params, "provider_type", ProviderType, field_errors)

    if completed_after and completed_before and completed_after > completed_before:
        field_errors.append({
            "field": "completed_after",
            "reason": "must be less than or equal to completed_before",
        })

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)

    if topic == RunsTopic.LIVE:
        params = {
            "method": "get_live_runs",
            "project_id": project_id,
            "risk_level": risk_level,
            "evidence_health": evidence_health,
            "source": source,
            "provider_type": provider_type,
            "limit": limit,
            "offset": offset,
            "sort_by": "started_at",
            "sort_order": "desc",
        }
    else:
        params = {
            "method": "get_completed_runs",
            "project_id": project_id,
            "status": status,
            "risk_level": risk_level,
            "completed_after": completed_after,
            "completed_before": completed_before,
            "limit": limit,
            "offset": offset,
            "sort_by": "completed_at",
            "sort_order": "desc",
        }

    registry = get_operation_registry()
    op = await registry.execute(
        "activity.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params=params,
        ),
    )

    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "OPERATION_FAILED",
                "message": op.error or "activity.query execution failed",
            },
        )

    result = op.data

    try:
        runs = [_to_run_summary_v2(item) for item in getattr(result, "items", [])]
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate activity run payload",
                "field_errors": [{"field": "runs", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    # PR-1 contract: derive has_more from page math, not backend-provided flags.
    has_more = (offset + len(runs)) < total
    next_offset = offset + len(runs) if has_more else None

    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_REQUEST_ID_MISSING",
                "message": "Request id is missing from middleware context",
            },
        )

    generated_at = _to_rfc3339z(getattr(result, "generated_at", None))
    correlation_id = request.headers.get("X-Correlation-ID")

    return RunsFacadeResponse(
        topic=topic,
        runs=runs,
        total=total,
        has_more=has_more,
        pagination=RunsPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=RunsMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
