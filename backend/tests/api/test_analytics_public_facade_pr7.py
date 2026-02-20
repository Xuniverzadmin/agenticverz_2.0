from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.analytics import analytics_public
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


def _usage_payload() -> SimpleNamespace:
    return SimpleNamespace(
        window=SimpleNamespace(
            from_ts=datetime(2026, 2, 10, 0, 0, tzinfo=timezone.utc),
            to_ts=datetime(2026, 2, 16, 0, 0, tzinfo=timezone.utc),
            resolution="day",
        ),
        totals=SimpleNamespace(requests=12, compute_units=6, tokens=2400),
        series=[
            SimpleNamespace(ts="2026-02-10", requests=5, compute_units=2, tokens=900),
            SimpleNamespace(ts="2026-02-11", requests=7, compute_units=4, tokens=1500),
        ],
        signals=SimpleNamespace(sources=["cost_records", "llm.usage"], freshness_sec=32),
    )


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-1201"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-1201"
        return response

    app.include_router(analytics_public.router)
    app.dependency_overrides[analytics_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(analytics_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(analytics_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/analytics/statistics/usage") == 1
    assert "/hoc/api/cus/analytics/statistics/usage" not in paths


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/analytics/statistics/usage?from=2026-02-10T00:00:00Z&to=2026-02-11T00:00:00Z&foo=bar"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get(
        "/cus/analytics/statistics/usage"
        "?from=2026-02-10T00:00:00Z"
        "&to=2026-02-11T00:00:00Z"
        "&as_of=2026-02-10T00:00:00Z"
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "to=2026-02-11T00:00:00Z",
        "from=2026-02-10T00:00:00Z",
        "from=2026-02-10T00:00:00&to=2026-02-11T00:00:00Z",
        "from=2026-02-11T00:00:00Z&to=2026-02-10T00:00:00Z",
        "from=2025-10-01T00:00:00Z&to=2026-02-11T00:00:00Z",
        "from=2026-02-10T00:00:00Z&to=2026-02-11T00:00:00Z&resolution=week",
        "from=2026-02-10T00:00:00Z&to=2026-02-11T00:00:00Z&scope=workspace",
    ],
)
def test_query_validation_errors(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/analytics/statistics/usage?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_usage_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["get_usage_statistics"] = _usage_payload()

    response1 = client.get(
        "/cus/analytics/statistics/usage"
        "?from=2026-02-10T00:00:00Z"
        "&to=2026-02-16T00:00:00Z"
        "&resolution=hour"
        "&scope=project"
    )
    response2 = client.get(
        "/cus/analytics/statistics/usage"
        "?from=2026-02-10T00:00:00Z"
        "&to=2026-02-16T00:00:00Z"
        "&resolution=hour"
        "&scope=project"
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ts1 = [item["ts"] for item in body1["series"]]
    ts2 = [item["ts"] for item in body2["series"]]

    assert ts1 == ["2026-02-10", "2026-02-11"]
    assert ts2 == ts1

    assert registry.calls[0]["operation"] == "analytics.query"
    assert registry.calls[0]["params"]["method"] == "get_usage_statistics"
    assert registry.calls[0]["params"]["resolution"].value == "hour"
    assert registry.calls[0]["params"]["scope"].value == "project"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["get_usage_statistics"] = _usage_payload()

    response = client.get(
        "/cus/analytics/statistics/usage"
        "?from=2026-02-10T00:00:00Z"
        "&to=2026-02-16T00:00:00Z",
        headers={"X-Correlation-ID": "corr-an-1201"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-an-1201"
    assert body["meta"]["as_of"] is None
