# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-9 API keys list facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.auth.tenant_resolver import resolve_tenant_id
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class APIKeyStatusFilter(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKeyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class APIKeysPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class APIKeysMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class APIKeySummaryPublic(BaseModel):
    key_id: str
    name: str
    prefix: str
    status: APIKeyStatus
    created_at: str
    last_used_at: str | None = None
    expires_at: str | None = None
    total_requests: int


class APIKeysListPublicResponse(BaseModel):
    keys: list[APIKeySummaryPublic]
    total: int
    has_more: bool
    pagination: APIKeysPagination
    generated_at: str
    meta: APIKeysMeta


router = APIRouter(prefix="/cus/api_keys", tags=["cus-api_keys-public"])


_ALLOWED = {
    "status",
    "limit",
    "offset",
}


def get_tenant_id_from_auth(request: Request) -> str:
    """Resolve tenant_id via single-authority resolver and return string form."""
    return str(resolve_tenant_id(request))


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


def _parse_status(query_params, field_errors: list[dict[str, str]]) -> str | None:
    raw = _single_value(query_params, "status", field_errors)
    if raw is None:
        return None
    try:
        return APIKeyStatusFilter(raw).value
    except ValueError:
        field_errors.append({"field": "status", "reason": "must be one of: active, revoked, expired"})
        return None


def _reject_unknown_params(query_params, allowed: set[str], field_errors: list[dict[str, str]]) -> None:
    for key in sorted(set(query_params.keys())):
        if key not in allowed:
            field_errors.append({"field": key, "reason": "unknown query parameter"})


def _to_summary(item: Any) -> APIKeySummaryPublic:
    return APIKeySummaryPublic(
        key_id=str(_pick(item, "key_id", "")),
        name=str(_pick(item, "name", "")),
        prefix=str(_pick(item, "prefix", "")),
        status=APIKeyStatus(str(_pick(item, "status", "ACTIVE"))),
        created_at=_to_rfc3339z(_pick(item, "created_at")),
        last_used_at=_to_rfc3339z(_pick(item, "last_used_at")) if _pick(item, "last_used_at") else None,
        expires_at=_to_rfc3339z(_pick(item, "expires_at")) if _pick(item, "expires_at") else None,
        total_requests=int(_pick(item, "total_requests", 0)),
    )


@router.get(
    "/list",
    response_model=APIKeysListPublicResponse,
    summary="PR-9 API keys list facade endpoint",
)
async def list_api_keys_public(
    request: Request,
    session=Depends(get_session_dep),
) -> APIKeysListPublicResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-9")

    field_errors: list[dict[str, str]] = []
    _reject_unknown_params(query_params, _ALLOWED, field_errors)

    limit = _parse_int(query_params, "limit", default=50, minimum=1, maximum=100, field_errors=field_errors)
    offset = _parse_int(
        query_params,
        "offset",
        default=0,
        minimum=0,
        maximum=2_147_483_647,
        field_errors=field_errors,
    )
    status = _parse_status(query_params, field_errors)

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)

    params = {
        "method": "list_api_keys",
        "status": status,
        "limit": limit,
        "offset": offset,
    }

    registry = get_operation_registry()
    op = await registry.execute(
        "api_keys.query",
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
                "message": op.error or "api_keys.query execution failed",
            },
        )

    result = op.data

    try:
        keys = [_to_summary(item) for item in getattr(result, "items", [])]
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate api keys payload",
                "field_errors": [{"field": "keys", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    has_more = (offset + len(keys)) < total
    next_offset = offset + len(keys) if has_more else None

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

    return APIKeysListPublicResponse(
        keys=keys,
        total=total,
        has_more=has_more,
        pagination=APIKeysPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=APIKeysMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
