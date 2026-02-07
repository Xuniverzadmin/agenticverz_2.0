# Layer: L4 — Tests
# AUDIENCE: INTERNAL
# Role: Guard: /api/v1/* must remain legacy-only (410 Gone), never canonical.

from __future__ import annotations


def test_api_v1_routes_are_legacy_only() -> None:
    from app.main import app

    api_v1_routes = []
    for route in app.routes:
        path = getattr(route, "path", None)
        if not path or not path.startswith("/api/v1"):
            continue
        api_v1_routes.append(route)

        endpoint = getattr(route, "endpoint", None)
        mod = getattr(endpoint, "__module__", "")
        assert (
            mod == "app.hoc.api.int.general.legacy_routes"
        ), f"Non-legacy /api/v1 route detected: path={path} module={mod}"

    assert api_v1_routes, "Expected legacy /api/v1 routes to exist (410 Gone handlers)."
