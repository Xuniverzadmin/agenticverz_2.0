# capability_id: CAP-012
# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-5 Logs replay feed facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.auth.gateway_middleware import get_auth_context
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class LogsFeedTopic(str, Enum):
    LLM_RUNS = "llm_runs"
    SYSTEM_RECORDS = "system_records"


class ReplaySourceKind(str, Enum):
    LLM_RUN = "llm_run"
    SYSTEM_RECORD = "system_record"


class LogsFeedPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class LogsFeedMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class ReplayFeedItem(BaseModel):
    item_id: str
    source_kind: ReplaySourceKind
    timestamp: str
    run_id: str | None = None
    trace_id: str | None = None
    provider: str | None = None
    model: str | None = None
    execution_status: str | None = None
    component: str | None = None
    event_type: str | None = None
    severity: str | None = None
    summary: str | None = None
    correlation_id: str | None = None
    is_synthetic: bool | None = None


class LogsFeedResponse(BaseModel):
    topic: LogsFeedTopic
    records: list[ReplayFeedItem]
    total: int
    has_more: bool
    pagination: LogsFeedPagination
    generated_at: str
    meta: LogsFeedMeta


router = APIRouter(prefix="/cus/logs", tags=["cus-logs-public"])


_ALLOWED = {
    "topic",
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


def _pick(item: Any, field: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


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


def _parse_topic(query_params, field_errors: list[dict[str, str]]) -> LogsFeedTopic | None:
    values = query_params.getlist("topic")
    if not values:
        field_errors.append({"field": "topic", "reason": "is required"})
        return None
    if len(values) > 1:
        field_errors.append({"field": "topic", "reason": "must be provided once"})
        return None
    raw = values[0]
    try:
        return LogsFeedTopic(raw)
    except ValueError:
        field_errors.append({"field": "topic", "reason": "must be one of: llm_runs, system_records"})
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


def _reject_unknown_params(query_params, allowed: set[str], field_errors: list[dict[str, str]]) -> None:
    for key in sorted(set(query_params.keys())):
        if key not in allowed:
            field_errors.append({"field": key, "reason": "unknown query parameter"})


def _to_replay_feed_item(topic: LogsFeedTopic, item: Any) -> ReplayFeedItem:
    if topic == LogsFeedTopic.LLM_RUNS:
        provider = _pick(item, "provider")
        model = _pick(item, "model")
        status = _pick(item, "execution_status")
        return ReplayFeedItem(
            item_id=str(_pick(item, "id", "")),
            source_kind=ReplaySourceKind.LLM_RUN,
            timestamp=_to_rfc3339z(_pick(item, "created_at")),
            run_id=_pick(item, "run_id"),
            trace_id=_pick(item, "trace_id"),
            provider=provider,
            model=model,
            execution_status=status,
            summary=f"{provider}/{model} [{status}]" if provider and model and status else None,
            is_synthetic=_pick(item, "is_synthetic"),
        )

    return ReplayFeedItem(
        item_id=str(_pick(item, "id", "")),
        source_kind=ReplaySourceKind.SYSTEM_RECORD,
        timestamp=_to_rfc3339z(_pick(item, "created_at")),
        component=_pick(item, "component"),
        event_type=_pick(item, "event_type"),
        severity=_pick(item, "severity"),
        summary=_pick(item, "summary"),
        correlation_id=_pick(item, "correlation_id"),
    )


@router.get(
    "/list",
    response_model=LogsFeedResponse,
    summary="PR-5 Logs replay feed facade endpoint",
)
async def list_logs_public(
    request: Request,
    session=Depends(get_session_dep),
) -> LogsFeedResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-5")

    field_errors: list[dict[str, str]] = []
    topic = _parse_topic(query_params, field_errors)
    _reject_unknown_params(query_params, _ALLOWED, field_errors)

    limit = _parse_int(query_params, "limit", default=20, minimum=1, maximum=100, field_errors=field_errors)
    offset = _parse_int(
        query_params,
        "offset",
        default=0,
        minimum=0,
        maximum=2_147_483_647,
        field_errors=field_errors,
    )

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)

    if topic == LogsFeedTopic.LLM_RUNS:
        params = {
            "method": "list_llm_run_records",
            "limit": limit,
            "offset": offset,
        }
    else:
        params = {
            "method": "list_system_records",
            "limit": limit,
            "offset": offset,
        }

    registry = get_operation_registry()
    op = await registry.execute(
        "logs.query",
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
                "message": op.error or "logs.query execution failed",
            },
        )

    result = op.data

    try:
        records = [_to_replay_feed_item(topic, item) for item in getattr(result, "items", [])]
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate logs payload",
                "field_errors": [{"field": "records", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    has_more = (offset + len(records)) < total
    next_offset = offset + len(records) if has_more else None

    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_REQUEST_ID_MISSING",
                "message": "Request id is missing from middleware context",
            },
        )

    generated_at = _to_rfc3339z(None)
    correlation_id = request.headers.get("X-Correlation-ID")

    return LogsFeedResponse(
        topic=topic,
        records=records,
        total=total,
        has_more=has_more,
        pagination=LogsFeedPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=LogsFeedMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
