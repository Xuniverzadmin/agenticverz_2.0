# capability_id: CAP-012
# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-10 account users list facade (boundary validation + single dispatch)
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


class AccountUserRoleFilter(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class AccountUserStatusFilter(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"


class AccountUserRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class AccountUserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"


class AccountUsersPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class AccountUsersMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class AccountUserSummaryPublic(BaseModel):
    user_id: str
    email: str
    name: str | None = None
    role: AccountUserRole
    status: AccountUserStatus
    created_at: str
    last_login_at: str | None = None


class AccountUsersListPublicResponse(BaseModel):
    users: list[AccountUserSummaryPublic]
    total: int
    has_more: bool
    pagination: AccountUsersPagination
    generated_at: str
    meta: AccountUsersMeta


router = APIRouter(prefix="/cus/account", tags=["cus-account-public"])


_ALLOWED = {
    "role",
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


def _parse_role(query_params, field_errors: list[dict[str, str]]) -> str | None:
    raw = _single_value(query_params, "role", field_errors)
    if raw is None:
        return None
    try:
        return AccountUserRoleFilter(raw).value
    except ValueError:
        field_errors.append({"field": "role", "reason": "must be one of: owner, admin, member, viewer"})
        return None


def _parse_status(query_params, field_errors: list[dict[str, str]]) -> str | None:
    raw = _single_value(query_params, "status", field_errors)
    if raw is None:
        return None
    try:
        return AccountUserStatusFilter(raw).value
    except ValueError:
        field_errors.append({"field": "status", "reason": "must be one of: active, invited, suspended"})
        return None


def _reject_unknown_params(query_params, allowed: set[str], field_errors: list[dict[str, str]]) -> None:
    for key in sorted(set(query_params.keys())):
        if key not in allowed:
            field_errors.append({"field": key, "reason": "unknown query parameter"})


def _to_summary(item: Any) -> AccountUserSummaryPublic:
    return AccountUserSummaryPublic(
        user_id=str(_pick(item, "user_id", "")),
        email=str(_pick(item, "email", "")),
        name=_pick(item, "name"),
        role=AccountUserRole(str(_pick(item, "role", "MEMBER"))),
        status=AccountUserStatus(str(_pick(item, "status", "ACTIVE"))),
        created_at=_to_rfc3339z(_pick(item, "created_at")),
        last_login_at=_to_rfc3339z(_pick(item, "last_login_at")) if _pick(item, "last_login_at") else None,
    )


@router.get(
    "/users/list",
    response_model=AccountUsersListPublicResponse,
    summary="PR-10 account users list facade endpoint",
)
async def list_account_users_public(
    request: Request,
    session=Depends(get_session_dep),
) -> AccountUsersListPublicResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-10")

    field_errors: list[dict[str, str]] = []
    _reject_unknown_params(query_params, _ALLOWED, field_errors)

    role = _parse_role(query_params, field_errors)
    status = _parse_status(query_params, field_errors)
    limit = _parse_int(query_params, "limit", default=50, minimum=1, maximum=100, field_errors=field_errors)
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

    registry = get_operation_registry()
    op = await registry.execute(
        "account.query",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "list_users",
                "role": role,
                "status": status,
                "limit": limit,
                "offset": offset,
            },
        ),
    )

    if not op.success:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "OPERATION_FAILED",
                "message": op.error or "account.query execution failed",
            },
        )

    result = op.data

    try:
        users = [_to_summary(item) for item in getattr(result, "items", [])]
    except (ValidationError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate account users payload",
                "field_errors": [{"field": "users", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    has_more = (offset + len(users)) < total
    next_offset = offset + len(users) if has_more else None

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

    return AccountUsersListPublicResponse(
        users=users,
        total=total,
        has_more=has_more,
        pagination=AccountUsersPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=AccountUsersMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
