# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-4 Controls list facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class ControlsListTopic(str, Enum):
    ALL = "all"
    ENABLED = "enabled"
    DISABLED = "disabled"
    AUTO = "auto"


class ControlType(str, Enum):
    KILLSWITCH = "killswitch"
    CIRCUIT_BREAKER = "circuit_breaker"
    FEATURE_FLAG = "feature_flag"
    THROTTLE = "throttle"
    MAINTENANCE = "maintenance"


class ControlsListPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class ControlsListMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class ControlSummary(BaseModel):
    id: str
    tenant_id: str
    name: str
    control_type: str
    state: str
    scope: str
    conditions: dict[str, Any] | None = None
    enabled_at: str | None = None
    disabled_at: str | None = None
    enabled_by: str | None = None
    disabled_by: str | None = None
    created_at: str
    updated_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ControlsListResponse(BaseModel):
    topic: ControlsListTopic
    controls: list[ControlSummary]
    total: int
    has_more: bool
    pagination: ControlsListPagination
    generated_at: str
    meta: ControlsListMeta


router = APIRouter(prefix="/cus/controls", tags=["cus-controls-public"])


_COMMON_ALLOWED = {
    "topic",
    "control_type",
    "limit",
    "offset",
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


def _to_rfc3339z(value: datetime | str | None) -> str:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            value = None

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


def _parse_topic(query_params, field_errors: list[dict[str, str]]) -> ControlsListTopic | None:
    values = query_params.getlist("topic")
    if not values:
        field_errors.append({"field": "topic", "reason": "is required"})
        return None
    if len(values) > 1:
        field_errors.append({"field": "topic", "reason": "must be provided once"})
        return None

    raw = values[0]
    try:
        return ControlsListTopic(raw)
    except ValueError:
        field_errors.append({"field": "topic", "reason": "must be one of: all, enabled, disabled, auto"})
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


def _reject_unknown_params(query_params, allowed: set[str], field_errors: list[dict[str, str]]) -> None:
    for key in sorted(set(query_params.keys())):
        if key not in allowed:
            field_errors.append({"field": key, "reason": "unknown query parameter"})


def _to_control_summary(item: Any) -> ControlSummary:
    return ControlSummary.model_validate(item, from_attributes=True)


@router.get(
    "/list",
    response_model=ControlsListResponse,
    summary="PR-4 Controls list facade endpoint",
)
async def list_controls_public(
    request: Request,
    session=Depends(get_session_dep),
) -> ControlsListResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-4")

    field_errors: list[dict[str, str]] = []
    topic = _parse_topic(query_params, field_errors)
    _reject_unknown_params(query_params, _COMMON_ALLOWED, field_errors)

    limit = _parse_int(query_params, "limit", default=20, minimum=1, maximum=100, field_errors=field_errors)
    offset = _parse_int(
        query_params,
        "offset",
        default=0,
        minimum=0,
        maximum=2_147_483_647,
        field_errors=field_errors,
    )

    control_type = _parse_enum(query_params, "control_type", ControlType, field_errors)

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)

    state = None
    if topic == ControlsListTopic.ENABLED:
        state = "enabled"
    elif topic == ControlsListTopic.DISABLED:
        state = "disabled"
    elif topic == ControlsListTopic.AUTO:
        state = "auto"

    params = {
        "method": "list_controls_page",
        "control_type": control_type,
        "state": state,
        "limit": limit,
        "offset": offset,
    }

    registry = get_operation_registry()
    op = await registry.execute(
        "controls.query",
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
                "message": op.error or "controls.query execution failed",
            },
        )

    result = op.data

    try:
        controls = [_to_control_summary(item) for item in getattr(result, "items", [])]
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate controls payload",
                "field_errors": [{"field": "controls", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    has_more = (offset + len(controls)) < total
    next_offset = offset + len(controls) if has_more else None

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

    return ControlsListResponse(
        topic=topic,
        controls=controls,
        total=total,
        has_more=has_more,
        pagination=ControlsListPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=ControlsListMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
