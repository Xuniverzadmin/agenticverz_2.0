# capability_id: CAP-009
# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: PR-3 Policies list facade (boundary validation + single dispatch)
# Callers: Customer Console frontend
# Allowed Imports: L3, L4
# Forbidden Imports: L1, L5, L6 (direct)

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ValidationError

from app.hoc.api.cus.policies.policies import PolicyRuleSummary, get_tenant_id_from_auth
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
    get_session_dep,
)


class PoliciesListTopic(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class PolicyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class EnforcementMode(str, Enum):
    BLOCK = "BLOCK"
    WARN = "WARN"
    AUDIT = "AUDIT"
    DISABLED = "DISABLED"


class PolicyScope(str, Enum):
    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    PROJECT = "PROJECT"
    AGENT = "AGENT"


class PolicySource(str, Enum):
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"
    LEARNED = "LEARNED"


class PolicyRuleType(str, Enum):
    SYSTEM = "SYSTEM"
    SAFETY = "SAFETY"
    ETHICAL = "ETHICAL"
    TEMPORAL = "TEMPORAL"


class PoliciesListPagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None


class PoliciesListMeta(BaseModel):
    request_id: str
    correlation_id: str | None = None
    as_of: str | None = None


class PoliciesListResponse(BaseModel):
    topic: PoliciesListTopic
    rules: list[PolicyRuleSummary]
    total: int
    has_more: bool
    pagination: PoliciesListPagination
    generated_at: str
    meta: PoliciesListMeta


router = APIRouter(prefix="/cus/policies", tags=["cus-policies-public"])


_ACTIVE_ALLOWED = {
    "topic",
    "enforcement_mode",
    "scope",
    "source",
    "rule_type",
    "created_after",
    "created_before",
    "limit",
    "offset",
}

_RETIRED_ALLOWED = {
    "topic",
    "enforcement_mode",
    "scope",
    "source",
    "rule_type",
    "created_after",
    "created_before",
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


def _parse_topic(query_params, field_errors: list[dict[str, str]]) -> PoliciesListTopic | None:
    values = query_params.getlist("topic")
    if not values:
        field_errors.append({"field": "topic", "reason": "is required"})
        return None
    if len(values) > 1:
        field_errors.append({"field": "topic", "reason": "must be provided once"})
        return None
    raw = values[0]
    try:
        return PoliciesListTopic(raw)
    except ValueError:
        field_errors.append({"field": "topic", "reason": "must be one of: active, retired"})
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


def _to_policy_rule_summary(item: Any) -> PolicyRuleSummary:
    return PolicyRuleSummary.model_validate(item, from_attributes=True)


@router.get(
    "/list",
    response_model=PoliciesListResponse,
    summary="PR-3 Policies list facade endpoint",
)
async def list_policies_public(
    request: Request,
    session=Depends(get_session_dep),
) -> PoliciesListResponse:
    query_params = request.query_params

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-3")

    field_errors: list[dict[str, str]] = []
    topic = _parse_topic(query_params, field_errors)

    if topic is not None:
        allowed = _ACTIVE_ALLOWED if topic == PoliciesListTopic.ACTIVE else _RETIRED_ALLOWED
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

    enforcement_mode = _parse_enum(query_params, "enforcement_mode", EnforcementMode, field_errors)
    scope = _parse_enum(query_params, "scope", PolicyScope, field_errors)
    source = _parse_enum(query_params, "source", PolicySource, field_errors)
    rule_type = _parse_enum(query_params, "rule_type", PolicyRuleType, field_errors)
    created_after = _parse_datetime_tz(query_params, "created_after", field_errors)
    created_before = _parse_datetime_tz(query_params, "created_before", field_errors)

    if created_after and created_before and created_after > created_before:
        field_errors.append({"field": "created_after", "reason": "must be less than or equal to created_before"})

    if field_errors:
        _invalid_query(field_errors)

    tenant_id = get_tenant_id_from_auth(request)
    status = PolicyStatus.ACTIVE.value if topic == PoliciesListTopic.ACTIVE else PolicyStatus.RETIRED.value

    params = {
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
    }

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.query",
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
                "message": op.error or "policies.query execution failed",
            },
        )

    result = op.data

    try:
        rules = [_to_policy_rule_summary(item) for item in getattr(result, "items", [])]
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONTRACT_MISMATCH",
                "message": "Unable to validate policy rule payload",
                "field_errors": [{"field": "rules", "reason": str(exc)}],
            },
        )

    total = int(getattr(result, "total", 0))
    has_more = (offset + len(rules)) < total
    next_offset = offset + len(rules) if has_more else None

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

    return PoliciesListResponse(
        topic=topic,
        rules=rules,
        total=total,
        has_more=has_more,
        pagination=PoliciesListPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=generated_at,
        meta=PoliciesListMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )
