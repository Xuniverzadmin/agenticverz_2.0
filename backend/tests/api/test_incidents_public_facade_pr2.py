from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.incidents import incidents_public
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


def _incident_payload(incident_id: str, created_at: str, resolved_at: str | None = None) -> dict:
    return {
        "incident_id": incident_id,
        "tenant_id": "tenant-test",
        "lifecycle_state": "ACTIVE" if resolved_at is None else "RESOLVED",
        "severity": "high",
        "category": "policy",
        "title": f"Incident {incident_id}",
        "description": "test incident",
        "llm_run_id": "run-1",
        "cause_type": "LLM_RUN",
        "error_code": None,
        "error_message": None,
        "created_at": created_at,
        "resolved_at": resolved_at,
        "is_synthetic": False,
        "policy_ref": "/policy/active/pol-1",
        "violation_ref": "/policy/violations/vio-1",
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-456"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-456"
        return response

    app.include_router(incidents_public.router)
    app.dependency_overrides[incidents_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(incidents_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(incidents_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/incidents/list") == 1
    assert "/hoc/api/cus/incidents/list" not in paths


def test_missing_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/incidents/list")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_invalid_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/incidents/list?topic=signals")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_repeated_topic_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/incidents/list?topic=active&topic=resolved")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/incidents/list?topic=active&foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/incidents/list?topic=active&as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "topic=active&limit=0",
        "topic=active&limit=101",
        "topic=active&offset=-1",
        "topic=historical&retention_days=6",
        "topic=historical&retention_days=366",
    ],
)
def test_bounds_validation(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/incidents/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_active_date_range_validation(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/incidents/list"
        "?topic=active"
        "&created_after=2026-02-16T10:00:00Z"
        "&created_before=2026-02-16T09:00:00Z"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_resolved_date_range_validation(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/incidents/list"
        "?topic=resolved"
        "&resolved_after=2026-02-16T10:00:00Z"
        "&resolved_before=2026-02-16T09:00:00Z"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_active_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    active_items = [
        _incident_payload("inc-b", "2026-02-16T10:00:00Z"),
        _incident_payload("inc-a", "2026-02-16T10:00:00Z"),
    ]
    registry.data_by_method["list_active_incidents"] = SimpleNamespace(
        items=active_items,
        total=2,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 5, tzinfo=timezone.utc),
    )

    response1 = client.get("/cus/incidents/list?topic=active&limit=20&offset=0")
    response2 = client.get("/cus/incidents/list?topic=active&limit=20&offset=0")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["incident_id"] for item in body1["incidents"]]
    ids2 = [item["incident_id"] for item in body2["incidents"]]

    assert ids1 == ["inc-b", "inc-a"]
    assert ids2 == ids1

    assert registry.calls[0]["params"]["method"] == "list_active_incidents"
    assert registry.calls[0]["params"]["sort_by"] == "created_at"
    assert registry.calls[0]["params"]["sort_order"] == "desc"


def test_historical_dispatch_includes_retention_days(client_with_registry):
    client, registry = client_with_registry

    historical_items = [
        _incident_payload("inc-h1", "2026-02-10T10:00:00Z", "2026-02-11T10:00:00Z"),
    ]
    registry.data_by_method["list_historical_incidents"] = SimpleNamespace(
        items=historical_items,
        total=1,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 8, 5, tzinfo=timezone.utc),
    )

    response = client.get("/cus/incidents/list?topic=historical&retention_days=45")

    assert response.status_code == 200
    assert registry.calls[0]["params"]["method"] == "list_historical_incidents"
    assert registry.calls[0]["params"]["retention_days"] == 45
    assert registry.calls[0]["params"]["sort_by"] == "resolved_at"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_active_incidents"] = SimpleNamespace(
        items=[_incident_payload("inc-req", "2026-02-16T10:00:00Z")],
        total=1,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get(
        "/cus/incidents/list?topic=active",
        headers={"X-Correlation-ID": "corr-inc-456"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-inc-456"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_resolved_incidents"] = SimpleNamespace(
        items=[_incident_payload("inc-has-more", "2026-02-16T08:00:00Z", "2026-02-16T09:00:00Z")],
        total=2,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get("/cus/incidents/list?topic=resolved&limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1
