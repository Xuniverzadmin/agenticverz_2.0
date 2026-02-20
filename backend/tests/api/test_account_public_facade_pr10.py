from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.account import account_public
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


def _user_item(user_id: str, email: str, role: str = "MEMBER", status: str = "ACTIVE") -> dict:
    return {
        "user_id": user_id,
        "email": email,
        "name": f"User {user_id}",
        "role": role,
        "status": status,
        "created_at": "2026-02-16T10:00:00Z",
        "last_login_at": "2026-02-16T10:05:00Z",
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-1501"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-1501"
        return response

    app.include_router(account_public.router)
    app.dependency_overrides[account_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(account_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(account_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/account/users/list") == 1
    assert "/hoc/api/cus/account/users/list" not in paths


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/account/users/list?foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/account/users/list?as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
        "role=superadmin",
        "status=disabled",
        "role=owner&role=admin",
    ],
)
def test_query_validation_errors(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/account/users/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_account_users_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_users"] = SimpleNamespace(
        items=[
            _user_item("user-b", "alex@example.com"),
            _user_item("user-a", "alex@example.com"),
        ],
        total=2,
    )

    response1 = client.get("/cus/account/users/list?role=member&status=active&limit=50&offset=0")
    response2 = client.get("/cus/account/users/list?role=member&status=active&limit=50&offset=0")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["user_id"] for item in body1["users"]]
    ids2 = [item["user_id"] for item in body2["users"]]

    assert ids1 == ["user-b", "user-a"]
    assert ids2 == ids1

    assert registry.calls[0]["operation"] == "account.query"
    assert registry.calls[0]["params"]["method"] == "list_users"
    assert registry.calls[0]["params"]["role"] == "member"
    assert registry.calls[0]["params"]["status"] == "active"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_users"] = SimpleNamespace(
        items=[_user_item("user-req", "request@example.com")],
        total=1,
    )

    response = client.get(
        "/cus/account/users/list",
        headers={"X-Correlation-ID": "corr-ac-1501"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-ac-1501"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_users"] = SimpleNamespace(
        items=[_user_item("user-more", "more@example.com")],
        total=2,
    )

    response = client.get("/cus/account/users/list?limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1


def test_contract_mismatch_returns_500(client_with_registry):
    client, _registry = client_with_registry

    _registry.data_by_method["list_users"] = SimpleNamespace(
        items=[_user_item("user-bad", "bad@example.com", role="ROOT")],
        total=1,
    )

    response = client.get("/cus/account/users/list")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "CONTRACT_MISMATCH"
