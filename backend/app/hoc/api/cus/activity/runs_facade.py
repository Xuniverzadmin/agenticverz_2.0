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

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

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


_SCAFFOLD_FIXTURE_HEADER = "X-HOC-Scaffold-Fixture"
_SCAFFOLD_PR1_LIVE_FIXTURE_KEY = "pr1-runs-live-v1"
_SCAFFOLD_PR1_COMPLETED_FIXTURE_KEY = "pr1-runs-completed-v1"
_SCAFFOLD_ALLOWED_HOSTS = {
    "stagetest.agenticverz.com",
    "localhost",
    "127.0.0.1",
    "testserver",
}
_SCAFFOLD_ALLOWED_MODES = {
    "local",
    "test",
    "preflight",
    "preprod",
    "staging",
}


def _host_from_request(request: Request) -> str:
    raw_host = request.headers.get("X-Forwarded-Host") or request.headers.get("host", "")
    return raw_host.split(",")[0].strip().split(":")[0].lower()


def _fixture_enabled() -> bool:
    if os.getenv("HOC_PR1_RUNS_SCAFFOLD_FIXTURE_ENABLED", "false").lower() != "true":
        return False
    return os.getenv("AOS_MODE", "prod").lower() in _SCAFFOLD_ALLOWED_MODES


def _should_use_pr1_live_fixture(request: Request, topic: RunsTopic | None) -> bool:
    if not _fixture_enabled():
        return False
    if topic != RunsTopic.LIVE:
        return False
    if request.headers.get(_SCAFFOLD_FIXTURE_HEADER) != _SCAFFOLD_PR1_LIVE_FIXTURE_KEY:
        return False
    return _host_from_request(request) in _SCAFFOLD_ALLOWED_HOSTS


def _should_use_pr1_completed_fixture(request: Request, topic: RunsTopic | None) -> bool:
    if not _fixture_enabled():
        return False
    if topic != RunsTopic.COMPLETED:
        return False
    if request.headers.get(_SCAFFOLD_FIXTURE_HEADER) != _SCAFFOLD_PR1_COMPLETED_FIXTURE_KEY:
        return False
    return _host_from_request(request) in _SCAFFOLD_ALLOWED_HOSTS


def _validate_fixture_header(request: Request) -> None:
    fixture_key = request.headers.get(_SCAFFOLD_FIXTURE_HEADER)
    if fixture_key is None:
        return
    if fixture_key in {_SCAFFOLD_PR1_LIVE_FIXTURE_KEY, _SCAFFOLD_PR1_COMPLETED_FIXTURE_KEY}:
        return
    _invalid_query(
        [
            {
                "field": _SCAFFOLD_FIXTURE_HEADER,
                "reason": f"unsupported fixture '{fixture_key}'",
            }
        ],
        message="Invalid scaffold fixture header",
    )


def _validate_fixture_topic_match(request: Request, topic: RunsTopic | None) -> None:
    fixture_key = request.headers.get(_SCAFFOLD_FIXTURE_HEADER)
    if fixture_key is None or topic is None:
        return

    expected_topic = {
        _SCAFFOLD_PR1_LIVE_FIXTURE_KEY: RunsTopic.LIVE,
        _SCAFFOLD_PR1_COMPLETED_FIXTURE_KEY: RunsTopic.COMPLETED,
    }.get(fixture_key)
    if expected_topic is None:
        return
    if topic == expected_topic:
        return

    _invalid_query(
        [
            {
                "field": "topic",
                "reason": f"fixture '{fixture_key}' requires topic '{expected_topic.value}'",
            }
        ],
        message="Invalid scaffold fixture usage",
    )


def _pr1_live_fixture_runs() -> list[dict[str, Any]]:
    return [
        {
            "run_id": "run_live_003",
            "tenant_id": "tenant-scaffold",
            "project_id": "proj-alpha",
            "is_synthetic": True,
            "source": "agent",
            "provider_type": "openai",
            "state": "LIVE",
            "status": "running",
            "started_at": "2026-02-18T06:08:00Z",
            "last_seen_at": "2026-02-18T06:31:00Z",
            "completed_at": None,
            "duration_ms": 1380000.0,
            "risk_level": "ELEVATED",
            "latency_bucket": "HIGH",
            "evidence_health": "FLOWING",
            "integrity_status": "VERIFIED",
            "incident_count": 1,
            "policy_draft_count": 0,
            "policy_violation": False,
            "input_tokens": 13200,
            "output_tokens": 1820,
            "estimated_cost_usd": 0.46,
            "policy_context": {
                "policy_id": "pol_cost_guard_01",
                "policy_name": "Cost Guardrail",
                "policy_scope": "TENANT",
                "limit_type": "cost_per_run_usd",
                "threshold_value": 0.5,
                "threshold_unit": "USD",
                "threshold_source": "POLICY",
                "evaluation_outcome": "NEAR_THRESHOLD",
                "actual_value": 0.46,
                "risk_type": "COST",
                "proximity_pct": 92.0,
                "facade_ref": "/policy/active/pol_cost_guard_01",
                "threshold_ref": "/policy/thresholds/cost_per_run_usd",
                "violation_ref": None,
            },
        },
        {
            "run_id": "run_live_002",
            "tenant_id": "tenant-scaffold",
            "project_id": "proj-beta",
            "is_synthetic": True,
            "source": "api",
            "provider_type": "anthropic",
            "state": "LIVE",
            "status": "running",
            "started_at": "2026-02-18T06:03:00Z",
            "last_seen_at": "2026-02-18T06:30:30Z",
            "completed_at": None,
            "duration_ms": 1650000.0,
            "risk_level": "NORMAL",
            "latency_bucket": "OK",
            "evidence_health": "FLOWING",
            "integrity_status": "VERIFIED",
            "incident_count": 0,
            "policy_draft_count": 0,
            "policy_violation": False,
            "input_tokens": 10900,
            "output_tokens": 1510,
            "estimated_cost_usd": 0.31,
            "policy_context": {
                "policy_id": "pol_latency_guard_01",
                "policy_name": "Latency Guardrail",
                "policy_scope": "PROJECT",
                "limit_type": "p95_latency_ms",
                "threshold_value": 5000.0,
                "threshold_unit": "ms",
                "threshold_source": "POLICY",
                "evaluation_outcome": "OK",
                "actual_value": 2210.0,
                "risk_type": "TIME",
                "proximity_pct": 44.2,
                "facade_ref": "/policy/active/pol_latency_guard_01",
                "threshold_ref": "/policy/thresholds/p95_latency_ms",
                "violation_ref": None,
            },
        },
        {
            "run_id": "run_live_001",
            "tenant_id": "tenant-scaffold",
            "project_id": "proj-gamma",
            "is_synthetic": True,
            "source": "agent",
            "provider_type": "openai",
            "state": "LIVE",
            "status": "running",
            "started_at": "2026-02-18T05:56:00Z",
            "last_seen_at": "2026-02-18T06:29:50Z",
            "completed_at": None,
            "duration_ms": 2030000.0,
            "risk_level": "HIGH",
            "latency_bucket": "DEGRADED",
            "evidence_health": "DEGRADED",
            "integrity_status": "PENDING",
            "incident_count": 2,
            "policy_draft_count": 1,
            "policy_violation": True,
            "input_tokens": 18700,
            "output_tokens": 2430,
            "estimated_cost_usd": 0.79,
            "policy_context": {
                "policy_id": "pol_token_cap_01",
                "policy_name": "Token Cap",
                "policy_scope": "TENANT",
                "limit_type": "tokens_per_run",
                "threshold_value": 20000.0,
                "threshold_unit": "tokens",
                "threshold_source": "POLICY",
                "evaluation_outcome": "BREACH",
                "actual_value": 21130.0,
                "risk_type": "TOKENS",
                "proximity_pct": 105.65,
                "facade_ref": "/policy/active/pol_token_cap_01",
                "threshold_ref": "/policy/thresholds/tokens_per_run",
                "violation_ref": "/policy/violations/vio_20260218_001",
            },
        },
    ]


def _pr1_completed_fixture_runs() -> list[dict[str, Any]]:
    return [
        {
            "run_id": "run_comp_003",
            "tenant_id": "tenant-scaffold",
            "project_id": "proj-alpha",
            "is_synthetic": True,
            "source": "agent",
            "provider_type": "openai",
            "state": "COMPLETED",
            "status": "succeeded",
            "started_at": "2026-02-18T05:15:00Z",
            "last_seen_at": "2026-02-18T05:47:30Z",
            "completed_at": "2026-02-18T05:47:30Z",
            "duration_ms": 1950000.0,
            "risk_level": "NORMAL",
            "latency_bucket": "OK",
            "evidence_health": "FLOWING",
            "integrity_status": "VERIFIED",
            "incident_count": 0,
            "policy_draft_count": 0,
            "policy_violation": False,
            "input_tokens": 8400,
            "output_tokens": 960,
            "estimated_cost_usd": 0.19,
            "policy_context": {
                "policy_id": "pol_cost_guard_01",
                "policy_name": "Cost Guardrail",
                "policy_scope": "TENANT",
                "limit_type": "cost_per_run_usd",
                "threshold_value": 0.5,
                "threshold_unit": "USD",
                "threshold_source": "POLICY",
                "evaluation_outcome": "OK",
                "actual_value": 0.19,
                "risk_type": "COST",
                "proximity_pct": 38.0,
                "facade_ref": "/policy/active/pol_cost_guard_01",
                "threshold_ref": "/policy/thresholds/cost_per_run_usd",
                "violation_ref": None,
            },
        },
        {
            "run_id": "run_comp_002",
            "tenant_id": "tenant-scaffold",
            "project_id": "proj-beta",
            "is_synthetic": True,
            "source": "api",
            "provider_type": "anthropic",
            "state": "COMPLETED",
            "status": "failed",
            "started_at": "2026-02-18T04:42:00Z",
            "last_seen_at": "2026-02-18T05:12:00Z",
            "completed_at": "2026-02-18T05:12:00Z",
            "duration_ms": 1800000.0,
            "risk_level": "HIGH",
            "latency_bucket": "DEGRADED",
            "evidence_health": "DEGRADED",
            "integrity_status": "VERIFIED",
            "incident_count": 1,
            "policy_draft_count": 0,
            "policy_violation": True,
            "input_tokens": 12300,
            "output_tokens": 1470,
            "estimated_cost_usd": 0.41,
            "policy_context": {
                "policy_id": "pol_latency_guard_01",
                "policy_name": "Latency Guardrail",
                "policy_scope": "PROJECT",
                "limit_type": "p95_latency_ms",
                "threshold_value": 5000.0,
                "threshold_unit": "ms",
                "threshold_source": "POLICY",
                "evaluation_outcome": "BREACH",
                "actual_value": 6120.0,
                "risk_type": "TIME",
                "proximity_pct": 122.4,
                "facade_ref": "/policy/active/pol_latency_guard_01",
                "threshold_ref": "/policy/thresholds/p95_latency_ms",
                "violation_ref": "/policy/violations/vio_20260218_002",
            },
        },
        {
            "run_id": "run_comp_001",
            "tenant_id": "tenant-scaffold",
            "project_id": "proj-gamma",
            "is_synthetic": True,
            "source": "agent",
            "provider_type": "openai",
            "state": "COMPLETED",
            "status": "succeeded",
            "started_at": "2026-02-18T03:22:00Z",
            "last_seen_at": "2026-02-18T04:03:00Z",
            "completed_at": "2026-02-18T04:03:00Z",
            "duration_ms": 2460000.0,
            "risk_level": "ELEVATED",
            "latency_bucket": "HIGH",
            "evidence_health": "FLOWING",
            "integrity_status": "VERIFIED",
            "incident_count": 0,
            "policy_draft_count": 1,
            "policy_violation": False,
            "input_tokens": 15400,
            "output_tokens": 2120,
            "estimated_cost_usd": 0.52,
            "policy_context": {
                "policy_id": "pol_token_cap_01",
                "policy_name": "Token Cap",
                "policy_scope": "TENANT",
                "limit_type": "tokens_per_run",
                "threshold_value": 20000.0,
                "threshold_unit": "tokens",
                "threshold_source": "POLICY",
                "evaluation_outcome": "NEAR_THRESHOLD",
                "actual_value": 17520.0,
                "risk_type": "TOKENS",
                "proximity_pct": 87.6,
                "facade_ref": "/policy/active/pol_token_cap_01",
                "threshold_ref": "/policy/thresholds/tokens_per_run",
                "violation_ref": None,
            },
        },
    ]


def _build_pr1_live_fixture_response(request: Request, topic: RunsTopic, limit: int, offset: int) -> RunsFacadeResponse:
    fixture_all = _pr1_live_fixture_runs()
    total = len(fixture_all)
    page_items = fixture_all[offset : offset + limit]
    runs = [_to_run_summary_v2(item) for item in page_items]
    has_more = (offset + len(runs)) < total
    next_offset = offset + len(runs) if has_more else None
    request_id = getattr(request.state, "request_id", None) or f"req-scaffold-{uuid4().hex[:12]}"
    correlation_id = request.headers.get("X-Correlation-ID")

    return RunsFacadeResponse(
        topic=topic,
        runs=runs,
        total=total,
        has_more=has_more,
        pagination=RunsPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=_to_rfc3339z(datetime.now(timezone.utc)),
        meta=RunsMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )


def _build_pr1_completed_fixture_response(request: Request, topic: RunsTopic, limit: int, offset: int) -> RunsFacadeResponse:
    fixture_all = _pr1_completed_fixture_runs()
    total = len(fixture_all)
    page_items = fixture_all[offset : offset + limit]
    runs = [_to_run_summary_v2(item) for item in page_items]
    has_more = (offset + len(runs)) < total
    next_offset = offset + len(runs) if has_more else None
    request_id = getattr(request.state, "request_id", None) or f"req-scaffold-{uuid4().hex[:12]}"
    correlation_id = request.headers.get("X-Correlation-ID")

    return RunsFacadeResponse(
        topic=topic,
        runs=runs,
        total=total,
        has_more=has_more,
        pagination=RunsPagination(limit=limit, offset=offset, next_offset=next_offset),
        generated_at=_to_rfc3339z(datetime.now(timezone.utc)),
        meta=RunsMeta(request_id=request_id, correlation_id=correlation_id, as_of=None),
    )


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
    _validate_fixture_header(request)

    if "as_of" in query_params:
        _unsupported_param("as_of", "Parameter 'as_of' is unsupported in PR-1")

    field_errors: list[dict[str, str]] = []
    topic = _parse_topic(query_params, field_errors)
    _validate_fixture_topic_match(request, topic)

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

    assert topic is not None

    if _should_use_pr1_live_fixture(request, topic):
        return _build_pr1_live_fixture_response(request=request, topic=topic, limit=limit, offset=offset)
    if _should_use_pr1_completed_fixture(request, topic):
        return _build_pr1_completed_fixture_response(request=request, topic=topic, limit=limit, offset=offset)

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
