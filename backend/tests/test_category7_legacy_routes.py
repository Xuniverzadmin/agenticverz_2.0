"""M29 Category 7: Legacy Route CI Guardrail Tests

These tests serve as CI guardrails to prevent regression on legacy route handling.
They verify that deprecated endpoints return 410 Gone (not 404 or redirects).

PIN-153: M29 Category 7 - Redirect Expiry & Cleanup

Test Categories:
1. Legacy paths return 410 Gone
2. No redirect responses (301/302/307/308)
3. Response contains migration guidance
4. Valid paths still work (sanity check)

Run with: PYTHONPATH=. python -m pytest tests/test_category7_legacy_routes.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# Test: Legacy Paths Return 410 Gone
# =============================================================================


class TestLegacyPathsReturn410:
    """Verify all legacy paths return 410 Gone."""

    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard",
            "/operator",
            "/operator/status",
            "/operator/tenants",
            "/operator/tenants/123",
            "/operator/incidents",
            "/operator/incidents/456",
            "/demo",
            "/demo/simulate-incident",
            "/demo/seed-data",
            "/simulation",
            "/simulation/cost",
            "/simulation/run",
            "/api/v1/operator",
            "/api/v1/operator/replay/batch",
        ],
    )
    def test_legacy_path_returns_410(self, path: str):
        """Legacy paths must return 410 Gone, not 404."""
        response = client.get(path)
        assert response.status_code == 410, (
            f"Expected 410 Gone for {path}, got {response.status_code}. "
            f"Legacy paths must return 410 to indicate permanent removal."
        )

    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard",
            "/operator",
            "/operator/test",
            "/demo",
            "/demo/test",
            "/simulation",
            "/simulation/test",
        ],
    )
    def test_legacy_path_post_returns_410(self, path: str):
        """POST to legacy paths must also return 410."""
        response = client.post(path, json={})
        assert response.status_code == 410, f"Expected 410 Gone for POST {path}, got {response.status_code}"


# =============================================================================
# Test: No Redirect Responses
# =============================================================================


class TestNoRedirects:
    """Verify legacy paths don't redirect - they return 410 Gone."""

    REDIRECT_CODES = {301, 302, 303, 307, 308}

    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard",
            "/operator",
            "/operator/status",
            "/demo",
            "/simulation",
        ],
    )
    def test_no_redirect_on_legacy_path(self, path: str):
        """Legacy paths must NOT return redirect status codes."""
        response = client.get(path, follow_redirects=False)
        assert response.status_code not in self.REDIRECT_CODES, (
            f"Legacy path {path} returned redirect {response.status_code}. "
            f"Legacy paths must return 410 Gone, not redirects."
        )


# =============================================================================
# Test: Response Contains Migration Guidance
# =============================================================================


class TestMigrationGuidance:
    """Verify 410 responses include migration guidance."""

    def test_dashboard_410_has_error_field(self):
        """410 response must include 'error' field."""
        response = client.get("/dashboard")
        assert response.status_code == 410
        data = response.json()
        assert "error" in data
        assert data["error"] == "GONE"

    def test_dashboard_410_has_message(self):
        """410 response must include explanatory message."""
        response = client.get("/dashboard")
        data = response.json()
        assert "message" in data
        assert "removed" in data["message"].lower() or "permanently" in data["message"].lower()

    def test_operator_410_has_migration_hint(self):
        """410 for /operator should hint to use /ops/*."""
        response = client.get("/operator")
        data = response.json()
        assert (
            "migration" in data or "replacement" in data.get("migration", {}).get("new_path", "") or "/ops" in str(data)
        )

    def test_410_response_structure(self):
        """410 response should have consistent structure."""
        response = client.get("/dashboard")
        data = response.json()

        # Required fields
        assert "error" in data
        assert "status" in data
        assert data["status"] == 410
        assert "path" in data
        assert "message" in data


# =============================================================================
# Test: Valid Paths Still Work (Sanity Check)
# =============================================================================


class TestValidPathsStillWork:
    """Sanity check that valid paths are not affected."""

    def test_health_endpoint_works(self):
        """/health should return 200, not 410."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_healthz_endpoint_works(self):
        """/healthz should return 200, not 410."""
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_metrics_endpoint_works(self):
        """/metrics should return 200, not 410."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_ops_incidents_requires_auth(self):
        """/ops/incidents should require auth (403), not return 410."""
        response = client.get("/ops/incidents")
        # Should be 401 or 403, not 410
        assert response.status_code in [401, 403], f"Expected auth error for /ops/incidents, got {response.status_code}"

    def test_guard_status_requires_auth(self):
        """/guard/status should require auth, not return 410."""
        response = client.get("/guard/status")
        # Should be 401 or 403, not 410
        assert response.status_code in [401, 403], f"Expected auth error for /guard/status, got {response.status_code}"


# =============================================================================
# Test: Invariants
# =============================================================================


class TestCategoryInvariants:
    """Test Category 7 invariants from PIN-153."""

    def test_invariant_no_bare_path_redirects(self):
        """INVARIANT: No bare-path redirects - 410 Gone, not 301/302."""
        legacy_paths = ["/dashboard", "/operator", "/demo", "/simulation"]
        for path in legacy_paths:
            response = client.get(path, follow_redirects=False)
            assert response.status_code == 410, f"Invariant violation: {path} returned {response.status_code}, not 410"

    def test_invariant_consistent_410_structure(self):
        """INVARIANT: All 410 responses have consistent structure."""
        paths = ["/dashboard", "/operator", "/demo", "/simulation"]
        required_fields = {"error", "status", "path", "message"}

        for path in paths:
            response = client.get(path)
            if response.status_code == 410:
                data = response.json()
                missing = required_fields - set(data.keys())
                assert not missing, f"410 response for {path} missing required fields: {missing}"


# =============================================================================
# Test: Route Registration
# =============================================================================


class TestLegacyRouterRegistration:
    """Verify legacy_routes router is properly registered."""

    def test_legacy_routes_registered(self):
        """Legacy routes should be registered in the app."""
        route_paths = [route.path for route in app.routes if hasattr(route, "path")]

        # Check that at least some legacy paths are registered
        assert "/dashboard" in route_paths, "/dashboard route not registered"

    def test_legacy_routes_have_correct_tags(self):
        """Legacy routes should be tagged for documentation."""
        from app.api.legacy_routes import router

        assert router.tags == ["Legacy (Deprecated)"]
