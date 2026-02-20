from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.cus.logs import logs_public
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


def _llm_run_item(run_id: str) -> dict:
    return {
        "id": f"llm-{run_id}",
        "run_id": run_id,
        "trace_id": f"trace-{run_id}",
        "provider": "openai",
        "model": "gpt-5",
        "execution_status": "completed",
        "is_synthetic": False,
        "created_at": "2026-02-16T10:00:00Z",
    }


def _system_record_item(record_id: str) -> dict:
    return {
        "id": record_id,
        "component": "policy_engine",
        "event_type": "THRESHOLD_TRIGGERED",
        "severity": "WARN",
        "summary": "Threshold exceeded",
        "correlation_id": "corr-1",
        "created_at": "2026-02-16T10:05:00Z",
    }


@pytest.fixture
def client_with_registry(monkeypatch):
    registry = FakeRegistry()

    app = FastAPI()

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        request.state.request_id = "req-test-1001"
        response = await call_next(request)
        response.headers["X-Request-ID"] = "req-test-1001"
        return response

    app.include_router(logs_public.router)
    app.dependency_overrides[logs_public.get_session_dep] = lambda: object()

    monkeypatch.setattr(logs_public, "get_tenant_id_from_auth", lambda _request: "tenant-test")
    monkeypatch.setattr(logs_public, "get_operation_registry", lambda: registry)

    with TestClient(app) as client:
        yield client, registry


def test_route_registered_once_and_no_double_prefix_alias():
    hoc_router = build_hoc_router()
    paths = [route.path for route in hoc_router.routes if hasattr(route, "path")]

    assert paths.count("/cus/logs/list") == 1
    assert "/hoc/api/cus/logs/list" not in paths


def test_missing_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/logs/list")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_invalid_topic_returns_invalid_query(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/logs/list?topic=replay")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_repeated_topic_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/logs/list?topic=llm_runs&topic=system_records")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_unknown_query_param_rejected(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/logs/list?topic=llm_runs&foo=bar")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_as_of_returns_unsupported_param(client_with_registry):
    client, registry = client_with_registry

    response = client.get("/cus/logs/list?topic=llm_runs&as_of=2026-02-16T00:00:00Z")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_PARAM"
    assert len(registry.calls) == 0


@pytest.mark.parametrize(
    "query",
    [
        "topic=llm_runs&limit=0",
        "topic=llm_runs&limit=101",
        "topic=llm_runs&offset=-1",
    ],
)
def test_limit_and_offset_bounds(query: str, client_with_registry):
    client, registry = client_with_registry

    response = client.get(f"/cus/logs/list?{query}")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_QUERY"
    assert len(registry.calls) == 0


def test_llm_runs_dispatch_and_order_stability(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_llm_run_records"] = SimpleNamespace(
        items=[_llm_run_item("run-b"), _llm_run_item("run-a")],
        total=2,
        has_more=False,
    )

    response1 = client.get("/cus/logs/list?topic=llm_runs&limit=20&offset=0")
    response2 = client.get("/cus/logs/list?topic=llm_runs&limit=20&offset=0")

    assert response1.status_code == 200
    assert response2.status_code == 200

    body1 = response1.json()
    body2 = response2.json()

    ids1 = [item["run_id"] for item in body1["records"]]
    ids2 = [item["run_id"] for item in body2["records"]]

    assert ids1 == ["run-b", "run-a"]
    assert ids2 == ids1

    assert registry.calls[0]["params"]["method"] == "list_llm_run_records"


def test_system_records_dispatch(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_system_records"] = SimpleNamespace(
        items=[_system_record_item("sys-1")],
        total=1,
        has_more=False,
    )

    response = client.get("/cus/logs/list?topic=system_records")

    assert response.status_code == 200
    body = response.json()
    assert body["records"][0]["source_kind"] == "system_record"
    assert registry.calls[0]["params"]["method"] == "list_system_records"


def test_request_id_and_correlation_echo(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_llm_run_records"] = SimpleNamespace(
        items=[_llm_run_item("run-req")],
        total=1,
        has_more=False,
    )

    response = client.get(
        "/cus/logs/list?topic=llm_runs",
        headers={"X-Correlation-ID": "corr-log-1001"},
    )

    assert response.status_code == 200
    body = response.json()

    assert response.headers["X-Request-ID"] == body["meta"]["request_id"]
    assert body["meta"]["correlation_id"] == "corr-log-1001"
    assert body["meta"]["as_of"] is None


def test_has_more_derived_from_total_and_page_math(client_with_registry):
    client, registry = client_with_registry

    registry.data_by_method["list_llm_run_records"] = SimpleNamespace(
        items=[_llm_run_item("run-more")],
        total=2,
        has_more=False,
    )

    response = client.get("/cus/logs/list?topic=llm_runs&limit=1&offset=0")

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is True
    assert body["pagination"]["next_offset"] == 1
