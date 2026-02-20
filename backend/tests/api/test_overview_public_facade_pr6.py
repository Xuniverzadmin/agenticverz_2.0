from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.overview import overview_public
from app.hoc.app import build_hoc_router


class FakeRegistry:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.data: SimpleNamespace | None = None

    async def execute(self, operation: str, ctx) -> SimpleNamespace:
        self.calls.append(
            {
                "operation": operation,
                "tenant_id": ctx.tenant_id,
                "params": dict(ctx.params),
            }
        )
        return SimpleNamespace(success=True, data=self.data, error=None)


def _highlights_payload() -> SimpleNamespace:
    return SimpleNamespace(
        pulse=SimpleNamespace(
            status="ATTENTION_NEEDED",
            active_incidents=1,
            pending_decisions=2,
            recent_breaches=1,
            live_runs=3,
            queued_runs=1,
        ),
        domain_counts=[
            SimpleNamespace(domain="Activity", total=10, pending=1, critical=0),
            SimpleNamespace(domain="Incidents", total=2, pending=1, critical=1),
            SimpleNamespace(domain="Policies", total=5, pending=1, critical=1),
        ],
        last_activity_at=datetime(2026, 2, 16, 10, 0, tzinfo=timezone.utc),
    )


def _build_client(monkeypatch):
    registry = FakeRegistry()
    registry.data = _highlights_payload()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-1101"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-1101"
        return response

    app.include_router(overview_public.router)
    app.dependency_overrides[overview_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(overview_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(overview_public, "get_operation_registry", lambda: registry)

    client = TestClient(app)
    return client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/overview/highlights") == 1
    assert "/hoc/api/cus/overview/highlights" not in paths


def test_unknown_query_param_rejected(monkeypatch):
    client, registry = _build_client(monkeypatch)

    response = client.get("/cus/overview/highlights?foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(monkeypatch):
    client, registry = _build_client(monkeypatch)

    response = client.get("/cus/overview/highlights?as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


def test_highlights_dispatch_and_order_stability(monkeypatch):
    client, registry = _build_client(monkeypatch)

    response1 = client.get("/cus/overview/highlights")
    response2 = client.get("/cus/overview/highlights")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    domains1 = [item["domain"] for item in body1["highlights"]["domain_counts"]]
    domains2 = [item["domain"] for item in body2["highlights"]["domain_counts"]]

    assert domains1 == ["Activity", "Incidents", "Policies"]
    assert domains2 == domains1

    assert registry.calls[0]["operation"] == "overview.query"
    assert registry.calls[0]["params"]["method"] == "get_highlights"


def test_request_id_and_correlation_echo(monkeypatch):
    client, registry = _build_client(monkeypatch)

    response = client.get(
        "/cus/overview/highlights",
        headers={"X-Correlation-ID": "corr-ov-1101"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-ov-1101"
    assert body["meta"]["as_of"] is None
    assert len(registry.calls) == 1
