from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.controls import controls_public
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


def _control_payload(control_id: str, name: str, state: str = "disabled") -> dict:
    return {
        "id": control_id,
        "tenant_id": "tenant-test",
        "name": name,
        "control_type": "killswitch",
        "state": state,
        "scope": "global",
        "conditions": None,
        "enabled_at": None,
        "disabled_at": None,
        "enabled_by": None,
        "disabled_by": None,
        "created_at": "2026-02-16T10:00:00Z",
        "updated_at": None,
        "metadata": {},
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-901"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-901"
        return response

    app.include_router(controls_public.router)
    app.dependency_overrides[controls_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(controls_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(controls_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/controls/list") == 1
    assert "/hoc/api/cus/controls/list" not in paths


def test_missing_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/controls/list")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_invalid_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/controls/list?topic=active")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_repeated_topic_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/controls/list?topic=all&topic=enabled")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/controls/list?topic=all&foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/controls/list?topic=all&as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "topic=all&limit=0",
        "topic=all&limit=101",
        "topic=all&offset=-1",
    ],
)
def test_limit_and_offset_bounds(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/controls/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_invalid_control_type_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/controls/list?topic=all&control_type=unknown")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_all_topic_dispatches_without_state_filter(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_controls_page"] = SimpleNamespace(
        items=[_control_payload("ctrl-a", "A"), _control_payload("ctrl-b", "B")],
        total=2,
        generated_at=datetime(2026, 2, 16, 10, 20, tzinfo=timezone.utc),
    )

    response1 = client.get("/cus/controls/list?topic=all")
    response2 = client.get("/cus/controls/list?topic=all")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["id"] for item in body1["controls"]]
    ids2 = [item["id"] for item in body2["controls"]]

    assert ids1 == ["ctrl-a", "ctrl-b"]
    assert ids2 == ids1

    assert registry.calls[0]["params"]["method"] == "list_controls_page"
    assert registry.calls[0]["params"]["state"] is None


def test_enabled_topic_maps_state_filter(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_controls_page"] = SimpleNamespace(
        items=[_control_payload("ctrl-en", "Enabled", state="enabled")],
        total=1,
        generated_at=datetime(2026, 2, 16, 10, 20, tzinfo=timezone.utc),
    )

    response = client.get("/cus/controls/list?topic=enabled")

    assert response.status_code == 200
    assert registry.calls[0]["params"]["state"] == "enabled"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_controls_page"] = SimpleNamespace(
        items=[_control_payload("ctrl-req", "Req")],
        total=1,
        generated_at=datetime(2026, 2, 16, 10, 20, tzinfo=timezone.utc),
    )

    response = client.get(
        "/cus/controls/list?topic=all",
        headers={"X-Correlation-ID": "corr-ctrl-901"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-ctrl-901"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_controls_page"] = SimpleNamespace(
        items=[_control_payload("ctrl-more", "More")],
        total=2,
        generated_at=datetime(2026, 2, 16, 10, 20, tzinfo=timezone.utc),
    )

    response = client.get("/cus/controls/list?topic=all&limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1
