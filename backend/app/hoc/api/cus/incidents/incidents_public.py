# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-2 Incidents list facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.hoc.api.cus.incidents.incidents import (
    CauseType,
    IncidentSummary,
    Severity,
    get_tenant_id_from_auth,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class IncidentListTopic(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    HISTORICAL = "historical"


class IncidentsListPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class IncidentsListMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class IncidentsListResponse(BaseModel):
    topic: IncidentListTopic
    incidents: list[IncidentSummary]
    total: int
    has_more: bool
    pagination: IncidentsListPagination
    generated_at: str
    meta: IncidentsListMeta


router = APIRouter(prefix="/cus/incidents", tags=["cus-incidents-public"])


_ACTIVE_ALLOWED = {
    "topic",
    "severity",
    "category",
    "cause_type",
    "is_synthetic",
    "created_after",
    "created_before",
    "limit",
    "offset",
}

_RESOLVED_ALLOWED = {
    "topic",
    "severity",
    "category",
    "cause_type",
    "is_synthetic",
    "resolved_after",
    "resolved_before",
    "limit",
    "offset",
}

_HISTORICAL_ALLOWED = {
    "topic",
    "retention_days",
    "severity",
    "category",
    "cause_type",
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


def _parse_topic(query_params, field_errors: list[dict[str, str]]) -> IncidentListTopic | None:
    values = query_params.getlist("topic")
    if not values:
        field_errors.append({"field": "topic", "reason": "is required"})
        return None
    if len(values) > 1:
        field_errors.append({"field": "topic", "reason": "must be provided once"})
        return None
    raw = values[0]
    try:
        return IncidentListTopic(raw)
    except ValueError:
        field_errors.append({"field": "topic", "reason": "must be one of: active, resolved, historical"})
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


def _parse_bool(query_params, name: str, field_errors: list[dict[str, str]]) -> bool | None:
    raw = _single_value(query_params, name, field_errors)
    if raw is None:
        return None
    lowered = raw.lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    field_errors.append({"field": name, "reason": "must be a boolean"})
    return None


def _parse_enum(query_params, name: str, enum_cls: type[Enum], field_errors: list[dict[str, str]]) -> str | None:
    raw = _single_value(query_params, name, field_errors)
    if raw is None:
        return None
    try:
        return enum_cls(raw).value
    except ValueError:
        allowed = ", ".join([member.value for member in enum_cls])
        field_errors.append({"field": name, "reason": f"invalid value '{raw}'. Allowed: {allowed}"})
        return None


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


def _to_incident_summary(item: Any) -> IncidentSummary:
    return IncidentSummary.model_validate(item, from_attributes=True)


@router.get(
    "/list",
    response_model=IncidentsListResponse,
    summary="PR-2 Incidents list facade endpoint",
)
async def list_incidents_public(
    request: Request,
    session=Depends(get_session_dep),
) -> IncidentsListResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-2")

    field_errors: list[dict[str, str]] = []
    topic = _parse_topic(query_params, field_errors)

    if topic is not None:
        if topic == IncidentListTopic.ACTIVE:
            allowed = _ACTIVE_ALLOWED
        elif topic == IncidentListTopic.RESOLVED:
            allowed = _RESOLVED_ALLOWED
        else:
            allowed = _HISTORICAL_ALLOWED
        _reject_unknown_params(query_params, allowed, field_errors)

    limit = _parse_int(query_params, "limit", default=20, minimum=1, maximum=100, field_errors=field_errors)
    offset = _parse_int(
        query_params,
        "offset",
        default=0,
        minimum=0,
        maximum=2_147_483_647,
        field_errors=field_errors,
    )

    severity = _parse_enum(query_params, "severity", Severity, field_errors)
    category = _single_value(query_params, "category", field_errors)
    cause_type = _parse_enum(query_params, "cause_type", CauseType, field_errors)
    is_synthetic = _parse_bool(query_params, "is_synthetic", field_errors)

    created_after = _parse_datetime_tz(query_params, "created_after", field_errors)
    created_before = _parse_datetime_tz(query_params, "created_before", field_errors)
    resolved_after = _parse_datetime_tz(query_params, "resolved_after", field_errors)
    resolved_before = _parse_datetime_tz(query_params, "resolved_before", field_errors)

    retention_days = _parse_int(
        query_params,
        "retention_days",
        default=30,
        minimum=7,
        maximum=365,
        field_errors=field_errors,
    )

    if created_after and created_before and created_after > created_before:
        field_errors.append({"field": "created_after", "reason": "must be less than or equal to created_before"})

    if resolved_after and resolved_before and resolved_after > resolved_before:
        field_errors.append({"field": "resolved_after", "reason": "must be less than or equal to resolved_before"})

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)

    if topic == IncidentListTopic.ACTIVE:
        params = {
            "method": "list_active_incidents",
            "severity": severity,
            "category": category,
            "cause_type": cause_type,
            "is_synthetic": is_synthetic,
            "created_after": created_after,
            "created_before": created_before,
            "limit": limit,
            "offset": offset,
            "sort_by": "created_at",
            "sort_order": "desc",
        }
    elif topic == IncidentListTopic.RESOLVED:
        params = {
            "method": "list_resolved_incidents",
            "severity": severity,
            "category": category,
            "cause_type": cause_type,
            "is_synthetic": is_synthetic,
            "resolved_after": resolved_after,
            "resolved_before": resolved_before,
            "limit": limit,
            "offset": offset,
            "sort_by": "resolved_at",
            "sort_order": "desc",
        }
    else:
        params = {
            "method": "list_historical_incidents",
            "retention_days": retention_days,
            "severity": severity,
            "category": category,
            "cause_type": cause_type,
            "limit": limit,
            "offset": offset,
            "sort_by": "resolved_at",
            "sort_order": "desc",
        }

    registry = get_operation_registry()
    op = await registry.execute(
        "incidents.query",
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
                "message": op.error or "incidents.query execution failed",
            },
        )

    result = op.data

    try:
        incidents = [_to_incident_summary(item) for item in getattr(result, "items", [])]
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate incident payload",
                "field_errors": [{"field": "incidents", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    has_more = (offset + len(incidents)) < total
    next_offset = offset + len(incidents) if has_more else None

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

    return IncidentsListResponse(
        topic=topic,
        incidents=incidents,
        total=total,
        has_more=has_more,
        pagination=IncidentsListPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=IncidentsListMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
