from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.policies import policies_public
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


def _policy_rule_payload(rule_id: str, created_at: str, last_triggered_at: str | None = None) -> dict:
    return {
        "rule_id": rule_id,
        "name": f"Rule {rule_id}",
        "enforcement_mode": "BLOCK",
        "scope": "TENANT",
        "source": "MANUAL",
        "status": "ACTIVE",
        "created_at": created_at,
        "created_by": "system",
        "integrity_status": "VERIFIED",
        "integrity_score": "0.95",
        "trigger_count_30d": 3,
        "last_triggered_at": last_triggered_at,
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-789"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-789"
        return response

    app.include_router(policies_public.router)
    app.dependency_overrides[policies_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(policies_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(policies_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/policies/list") == 1
    assert "/hoc/api/cus/policies/list" not in paths


def test_missing_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/policies/list")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_invalid_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/policies/list?topic=invalid")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_repeated_topic_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/policies/list?topic=active&topic=retired")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/policies/list?topic=active&foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/policies/list?topic=active&as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "topic=active&limit=0",
        "topic=active&limit=101",
        "topic=active&offset=-1",
    ],
)
def test_limit_and_offset_bounds(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/policies/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_created_date_range_validation(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/policies/list"
        "?topic=active"
        "&created_after=2026-02-16T10:00:00Z"
        "&created_before=2026-02-16T09:00:00Z"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_active_dispatch_maps_to_list_policy_rules(client_with_registry):
    client, registry = client_with_registry

    active_items = [
        _policy_rule_payload("rule-b", "2026-02-16T10:00:00Z", "2026-02-16T10:10:00Z"),
        _policy_rule_payload("rule-a", "2026-02-16T10:00:00Z", "2026-02-16T10:10:00Z"),
    ]
    registry.data_by_method["list_policy_rules"] = SimpleNamespace(
        items=active_items,
        total=2,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response1 = client.get(
        "/cus/policies/list"
        "?topic=active"
        "&enforcement_mode=BLOCK"
        "&scope=TENANT"
        "&source=MANUAL"
        "&rule_type=SYSTEM"
        "&created_after=2026-02-16T00:00:00Z"
        "&created_before=2026-02-16T23:59:59Z"
    )
    response2 = client.get("/cus/policies/list?topic=active")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["rule_id"] for item in body1["rules"]]
    ids2 = [item["rule_id"] for item in body2["rules"]]

    assert ids1 == ["rule-b", "rule-a"]
    assert ids2 == ids1

    assert registry.calls[0]["params"]["method"] == "list_policy_rules"
    assert registry.calls[0]["params"]["status"] == "ACTIVE"
    assert isinstance(registry.calls[0]["params"]["created_after"], datetime)
    assert isinstance(registry.calls[0]["params"]["created_before"], datetime)


def test_retired_topic_maps_to_retires_status(client_with_registry):
    client, registry = client_with_registry

    retired_items = [_policy_rule_payload("rule-retired", "2026-02-10T10:00:00Z")]
    retired_items[0]["status"] = "RETIRED"
    registry.data_by_method["list_policy_rules"] = SimpleNamespace(
        items=retired_items,
        total=1,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get("/cus/policies/list?topic=retired")

    assert response.status_code == 200
    assert registry.calls[0]["params"]["method"] == "list_policy_rules"
    assert registry.calls[0]["params"]["status"] == "RETIRED"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_policy_rules"] = SimpleNamespace(
        items=[_policy_rule_payload("rule-req", "2026-02-16T10:00:00Z")],
        total=1,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get(
        "/cus/policies/list?topic=active",
        headers={"X-Correlation-ID": "corr-pol-789"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-pol-789"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_policy_rules"] = SimpleNamespace(
        items=[_policy_rule_payload("rule-more", "2026-02-16T10:00:00Z")],
        total=2,
        has_more=False,
        generated_at=datetime(2026, 2, 16, 10, 15, tzinfo=timezone.utc),
    )

    response = client.get("/cus/policies/list?topic=active&limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1
