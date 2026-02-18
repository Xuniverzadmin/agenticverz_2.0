from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.activity import runs_facade
from app.hoc.app import build_hoc_router


class FakeRegistry:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.data_by_method: dict[str, SimpleNamespace] = {}

    async def execute(self, operation: str, ctx) -> SimpleNamespace:
        params = dict(ctx.params)
        self.calls.append(
            {
                "operation": operation,
                "tenant_id": ctx.tenant_id,
                "params": params,
            }
        )
        method = params["method"]
        return SimpleNamespace(success=True, data=self.data_by_method[method], error=None)


def _run_payload(run_id: str, started_at: str, completed_at: str | None) -> dict:
    return {
        "run_id": run_id,
        "tenant_id": "tenant-test",
        "project_id": "project-1",
        "is_synthetic": False,
        "source": "agent",
        "provider_type": "openai",
        "state": "COMPLETED" if completed_at else "LIVE",
        "status": "succeeded" if completed_at else "running",
        "started_at": started_at,
        "last_seen_at": started_at,
        "completed_at": completed_at,
        "duration_ms": 101.0,
        "risk_level": "NORMAL",
        "latency_bucket": "OK",
        "evidence_health": "FLOWING",
        "integrity_status": "VERIFIED",
        "incident_count": 0,
        "policy_draft_count": 0,
        "policy_violation": False,
        "input_tokens": 10,
        "output_tokens": 20,
        "estimated_cost_usd": 0.001,
        "policy_context": {
            "policy_id": "pol-1",
            "policy_name": "Default Policy",
            "policy_scope": "TENANT",
            "limit_type": None,
            "threshold_value": None,
            "threshold_unit": None,
            "threshold_source": "DEFAULT",
            "evaluation_outcome": "OK",
            "actual_value": None,
            "risk_type": None,
            "proximity_pct": None,
            "facade_ref": None,
            "threshold_ref": None,
            "violation_ref": None,
        },
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-123"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-123"
        return response

    app.include_router(runs_facade.router)
    app.dependency_overrides[runs_facade.get_session_dep] = lambda: object()

    monkeypatch.setattr(runs_facade, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(runs_facade, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/activity/runs") == 1
    assert "/hoc/api/cus/activity/runs" not in paths


def test_missing_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/activity/runs")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_invalid_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/activity/runs?topic=signals")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_repeated_topic_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/activity/runs?topic=live&topic=completed")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(response.json()["detail"]["field_errors"]) >= 1
    assert len(registry.calls) == 0


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/activity/runs?topic=live&foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/activity/runs?topic=live&as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "topic=live&limit=0",
        "topic=live&limit=201",
        "topic=live&offset=-1",
    ],
)
def test_limit_and_offset_bounds(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/activity/runs?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_completed_date_range_validation(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/activity/runs"
        "?topic=completed"
        "&completed_after=2026-02-16T10:00:00Z"
        "&completed_before=2026-02-16T09:00:00Z"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_live_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    live_items = [
        _run_payload("run-b", "2026-02-16T10:00:00Z", None),
        _run_payload("run-a", "2026-02-16T10:00:00Z", None),
    ]
    registry.data_by_method["get_live_runs"] = SimpleNamespace(
        items=live_items,
        total=2,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 5, tzinfo=timezone.utc),
    )

    response1 = client.get("/cus/activity/runs?topic=live&limit=50&offset=0")
    response2 = client.get("/cus/activity/runs?topic=live&limit=50&offset=0")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["run_id"] for item in body1["runs"]]
    ids2 = [item["run_id"] for item in body2["runs"]]

    assert ids1 == ["run-b", "run-a"]
    assert ids2 == ids1

    assert registry.calls[0]["params"]["method"] == "get_live_runs"
    assert registry.calls[0]["params"]["sort_by"] == "started_at"
    assert registry.calls[0]["params"]["sort_order"] == "desc"


def test_completed_dispatch_uses_completed_sort_and_datetime_parsing(client_with_registry):
    client, registry = client_with_registry

    completed_items = [
        _run_payload("run-z", "2026-02-16T07:00:00Z", "2026-02-16T08:00:00Z"),
    ]
    registry.data_by_method["get_completed_runs"] = SimpleNamespace(
        items=completed_items,
        total=1,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 8, 5, tzinfo=timezone.utc),
    )

    response = client.get(
        "/cus/activity/runs"
        "?topic=completed"
        "&completed_after=2026-02-16T00:00:00Z"
        "&completed_before=2026-02-16T23:59:59Z"
    )

    assert response.status_code == 200
    assert registry.calls[0]["params"]["method"] == "get_completed_runs"
    assert registry.calls[0]["params"]["sort_by"] == "completed_at"
    assert registry.calls[0]["params"]["sort_order"] == "desc"
    assert isinstance(registry.calls[0]["params"]["completed_after"], datetime)
    assert isinstance(registry.calls[0]["params"]["completed_before"], datetime)


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["get_live_runs"] = SimpleNamespace(
        items=[_run_payload("run-id-check", "2026-02-16T10:00:00Z", None)],
        total=1,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get(
        "/cus/activity/runs?topic=live",
        headers={"X-Correlation-ID": "corr-abc-123"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-abc-123"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["get_live_runs"] = SimpleNamespace(
        items=[_run_payload("run-has-more", "2026-02-16T10:00:00Z", None)],
        total=2,
        # Deliberately inconsistent with contract; facade must recompute.
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get("/cus/activity/runs?topic=live&limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1


def test_pr1_live_fixture_payload_header_returns_contract_shape(client_with_registry, monkeypatch):
    client, registry = client_with_registry
    monkeypatch.setenv("HOC_PR1_RUNS_SCAFFOLD_FIXTURE_ENABLED", "true")
    monkeypatch.setenv("AOS_MODE", "test")

    response = client.get(
        "/cus/activity/runs?topic=live&limit=2&offset=0",
        headers={"X-HOC-Scaffold-Fixture": "pr1-runs-live-v1"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["topic"] == "live"
    assert body["total"] == 3
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["next_offset"] == 2
    assert body["runs"][0]["run_id"] == "run_live_003"
    assert body["runs"][0]["policy_context"]["policy_id"] == "pol_cost_guard_01"
    assert body["meta"]["request_id"] == "req-test-123"
    assert len(registry.calls) == 0


def test_pr1_completed_fixture_payload_header_returns_contract_shape(client_with_registry, monkeypatch):
    client, registry = client_with_registry
    monkeypatch.setenv("HOC_PR1_RUNS_SCAFFOLD_FIXTURE_ENABLED", "true")
    monkeypatch.setenv("AOS_MODE", "test")

    response = client.get(
        "/cus/activity/runs?topic=completed&limit=2&offset=0",
        headers={"X-HOC-Scaffold-Fixture": "pr1-runs-completed-v1"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["topic"] == "completed"
    assert body["total"] == 3
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["offset"] == 0
    assert body["pagination"]["next_offset"] == 2
    assert body["runs"][0]["run_id"] == "run_comp_003"
    assert body["runs"][0]["completed_at"] == "2026-02-18T05:47:30Z"
    assert body["meta"]["request_id"] == "req-test-123"
    assert len(registry.calls) == 0


def test_unknown_fixture_key_is_rejected_with_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/activity/runs?topic=live&limit=2&offset=0",
        headers={"X-HOC-Scaffold-Fixture": "unknown-fixture-key"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_pr1_live_fixture_header_rejects_non_live_topic():
    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-123"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-123"
        return response

    app.include_router(runs_facade.router)
    app.dependency_overrides[runs_facade.get_session_dep] = lambda: object()

    with TestClient(app) as client:
        response = client.get(
            "/cus/activity/runs?topic=completed",
            headers={"X-HOC-Scaffold-Fixture": "pr1-runs-live-v1"},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"


def test_pr1_completed_fixture_header_rejects_non_completed_topic():
    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-123"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-123"
        return response

    app.include_router(runs_facade.router)
    app.dependency_overrides[runs_facade.get_session_dep] = lambda: object()

    with TestClient(app) as client:
        response = client.get(
            "/cus/activity/runs?topic=live",
            headers={"X-HOC-Scaffold-Fixture": "pr1-runs-completed-v1"},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"


def test_fixture_header_with_fixture_mode_disabled_stays_on_auth_path(monkeypatch):
    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-123"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-123"
        return response

    app.include_router(runs_facade.router)
    app.dependency_overrides[runs_facade.get_session_dep] = lambda: object()

    monkeypatch.delenv("HOC_PR1_RUNS_SCAFFOLD_FIXTURE_ENABLED", raising=False)
    monkeypatch.setenv("AOS_MODE", "test")

    with TestClient(app) as client:
        response = client.get(
            "/cus/activity/runs?topic=live&limit=2&offset=0",
            headers={"X-HOC-Scaffold-Fixture": "pr1-runs-live-v1"},
        )

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "not_authenticated"
