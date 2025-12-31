# Layer Integration Test: L2 (API) ↔ L6 (Platform)
# Reference: PIN-245 (Integration Integrity System)
"""
L2 ↔ L6 Integration Tests

Tests that API endpoints correctly wire to platform services.
Focuses on auth wiring and persistence contract shapes.

What is tested:
- Auth header propagation
- Platform service response shapes
- Error propagation format

What is NOT tested:
- Auth policy correctness
- Data persistence accuracy
"""

import pytest


@pytest.mark.lit
@pytest.mark.lit_l2_l6
class TestAuthWiringShape:
    """Auth header propagation tests."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client):
        self.client = test_client

    def test_missing_auth_returns_401_or_403(self):
        """Protected endpoints reject missing auth."""
        # No auth headers
        response = self.client.get("/api/v1/runs")

        # Should be 401 (unauthenticated) or 403 (forbidden)
        # NOT 500 (server error from null auth)
        assert response.status_code in (401, 403), f"Expected 401/403, got {response.status_code}"

    def test_invalid_auth_returns_401_or_403(self):
        """Protected endpoints reject invalid auth."""
        response = self.client.get(
            "/api/v1/runs",
            headers={"X-AOS-Key": "definitely-invalid-key"},
        )

        # Should be 401 or 403, not 500
        assert response.status_code in (401, 403), f"Expected 401/403, got {response.status_code}"

    def test_auth_error_response_shape(self):
        """Auth errors have consistent shape."""
        response = self.client.get("/api/v1/runs")

        if response.status_code in (401, 403):
            data = response.json()
            assert isinstance(data, dict)

            # Should have detail or error message
            assert "detail" in data or "error" in data or "message" in data


@pytest.mark.lit
@pytest.mark.lit_l2_l6
class TestMetricsWiringShape:
    """Metrics endpoint integration."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client):
        self.client = test_client

    def test_metrics_endpoint_exists(self):
        """GET /metrics is wired and public."""
        response = self.client.get("/metrics")

        assert response.status_code != 405, "Metrics endpoint not wired"
        assert response.status_code in (200, 404)

    def test_metrics_content_type(self):
        """Metrics returns Prometheus format."""
        response = self.client.get("/metrics")

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            # Prometheus format
            assert "text/plain" in content_type or "text/html" in content_type


@pytest.mark.lit
@pytest.mark.lit_l2_l6
class TestPlatformErrorShape:
    """Platform service error propagation."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, mock_auth_headers):
        self.client = test_client
        self.headers = mock_auth_headers

    def test_database_errors_not_exposed(self):
        """Database errors don't leak implementation details."""
        # This tests that if DB errors occur, they're wrapped properly
        # We can't force a DB error in LIT, but we can check error format
        response = self.client.get(
            "/api/v1/runs/deliberately-malformed-uuid-that-should-fail",
            headers=self.headers,
        )

        if response.status_code == 500:
            data = response.json()
            # Should not contain raw SQL or stack traces
            response_text = str(data)
            assert "SELECT" not in response_text.upper()
            assert "INSERT" not in response_text.upper()
            assert "postgresql" not in response_text.lower()
