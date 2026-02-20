from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.api_keys import api_keys_public
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


def _key_item(key_id: str, created_at: str) -> dict:
    return {
        "key_id": key_id,
        "name": f"Key {key_id}",
        "prefix": "aos_abc123",
        "status": "ACTIVE",
        "created_at": created_at,
        "last_used_at": "2026-02-16T10:05:00Z",
        "expires_at": None,
        "total_requests": 9,
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-1401"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-1401"
        return response

    app.include_router(api_keys_public.router)
    app.dependency_overrides[api_keys_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(api_keys_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(api_keys_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/api_keys/list") == 1
    assert "/hoc/api/cus/api_keys/list" not in paths


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/api_keys/list?foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/api_keys/list?as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
        "status=disabled",
        "status=active&status=revoked",
    ],
)
def test_query_validation_errors(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/api_keys/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_api_keys_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_api_keys"] = SimpleNamespace(
        items=[
            _key_item("key-b", "2026-02-16T10:00:00Z"),
            _key_item("key-a", "2026-02-16T10:00:00Z"),
        ],
        total=2,
        has_more=False,
        filters_applied={"tenant_id": "tenant-test"},
    )

    response1 = client.get("/cus/api_keys/list?status=active&limit=50&offset=0")
    response2 = client.get("/cus/api_keys/list?status=active&limit=50&offset=0")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["key_id"] for item in body1["keys"]]
    ids2 = [item["key_id"] for item in body2["keys"]]

    assert ids1 == ["key-b", "key-a"]
    assert ids2 == ids1

    assert registry.calls[0]["operation"] == "api_keys.query"
    assert registry.calls[0]["params"]["method"] == "list_api_keys"
    assert registry.calls[0]["params"]["status"] == "active"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_api_keys"] = SimpleNamespace(
        items=[_key_item("key-req", "2026-02-16T10:00:00Z")],
        total=1,
        has_more=False,
        filters_applied={"tenant_id": "tenant-test"},
    )

    response = client.get(
        "/cus/api_keys/list",
        headers={"X-Correlation-ID": "corr-ak-1401"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-ak-1401"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_api_keys"] = SimpleNamespace(
        items=[_key_item("key-more", "2026-02-16T10:00:00Z")],
        total=2,
        has_more=False,
        filters_applied={"tenant_id": "tenant-test"},
    )

    response = client.get("/cus/api_keys/list?limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1
