from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.integrations import integrations_public
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


def _integration_item(integration_id: str, name: str, created_at: str) -> dict:
    return {
        "id": integration_id,
        "name": name,
        "provider_type": "openai",
        "status": "enabled",
        "health_state": "healthy",
        "default_model": "gpt-5",
        "created_at": created_at,
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-1301"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-1301"
        return response

    app.include_router(integrations_public.router)
    app.dependency_overrides[integrations_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(integrations_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(integrations_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/integrations/list") == 1
    assert "/hoc/api/cus/integrations/list" not in paths


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/integrations/list?foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/integrations/list?as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
        "status=active",
        "provider_type=cohere",
        "status=enabled&status=disabled",
    ],
)
def test_query_validation_errors(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/integrations/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_integrations_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_integrations"] = SimpleNamespace(
        items=[
            _integration_item("int-b", "Integration B", "2026-02-16T10:00:00Z"),
            _integration_item("int-a", "Integration A", "2026-02-16T10:00:00Z"),
        ],
        total=2,
    )

    response1 = client.get("/cus/integrations/list?status=enabled&provider_type=openai")
    response2 = client.get("/cus/integrations/list?status=enabled&provider_type=openai")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["id"] for item in body1["integrations"]]
    ids2 = [item["id"] for item in body2["integrations"]]

    assert ids1 == ["int-b", "int-a"]
    assert ids2 == ids1

    assert registry.calls[0]["operation"] == "integrations.query"
    assert registry.calls[0]["params"]["method"] == "list_integrations"
    assert registry.calls[0]["params"]["status"] == "enabled"
    assert registry.calls[0]["params"]["provider_type"] == "openai"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_integrations"] = SimpleNamespace(
        items=[_integration_item("int-req", "Integration Req", "2026-02-16T10:00:00Z")],
        total=1,
    )

    response = client.get(
        "/cus/integrations/list",
        headers={"X-Correlation-ID": "corr-int-1301"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-int-1301"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_integrations"] = SimpleNamespace(
        items=[_integration_item("int-more", "Integration More", "2026-02-16T10:00:00Z")],
        total=2,
    )

    response = client.get("/cus/integrations/list?limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1
