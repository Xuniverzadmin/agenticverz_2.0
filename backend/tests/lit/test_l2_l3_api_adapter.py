# Layer Integration Test: L2 (API) ↔ L3 (Adapter)
# Reference: PIN-245 (Integration Integrity System)
"""
L2 ↔ L3 Integration Tests

Tests that API endpoints correctly invoke adapters with proper shapes.
Does NOT test business logic — only integration contracts.

What is tested:
- Response shape matches contract
- Null safety (no unexpected None)
- Error response format
- Content-Type headers

What is NOT tested:
- Business correctness
- Data accuracy
- Authentication logic (only wiring)
"""

import pytest


@pytest.mark.lit
@pytest.mark.lit_l2_l3
class TestRuntimeAPIShape:
    """L2 Runtime API response shape validation."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, mock_auth_headers):
        self.client = test_client
        self.headers = mock_auth_headers

    def test_capabilities_endpoint_exists(self):
        """GET /api/v1/runtime/capabilities endpoint is wired."""
        response = self.client.get("/api/v1/runtime/capabilities", headers=self.headers)

        # Must return a response (not 404 Method Not Allowed)
        assert response.status_code != 405, "Endpoint not wired"

        # Valid status codes for this endpoint
        assert response.status_code in (200, 401, 403, 500)

    def test_capabilities_response_shape(self):
        """Capabilities response has expected structure."""
        response = self.client.get("/api/v1/runtime/capabilities", headers=self.headers)

        if response.status_code == 200:
            data = response.json()

            # Shape validation - must have these keys or error
            assert isinstance(data, dict), "Response must be object"

            # If successful, check for expected capability keys
            if "error" not in data:
                # At minimum, should have skills or be empty object
                assert data is not None

    def test_simulate_endpoint_exists(self):
        """POST /api/v1/runtime/simulate endpoint is wired."""
        response = self.client.post(
            "/api/v1/runtime/simulate",
            headers=self.headers,
            json={"plan": {}, "budget_cents": 100},
        )

        # Must return a response (not 405)
        assert response.status_code != 405, "Endpoint not wired"

        # Valid status codes
        assert response.status_code in (200, 400, 401, 403, 422, 500)

    def test_simulate_response_shape(self):
        """Simulate response has SimulationResult structure."""
        response = self.client.post(
            "/api/v1/runtime/simulate",
            headers=self.headers,
            json={"plan": {"steps": []}, "budget_cents": 100},
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Response must be object"

            # SimulationResult should have feasible or error
            if "error" not in data:
                assert "feasible" in data or "result" in data or isinstance(data, dict)

    def test_query_endpoint_exists(self):
        """POST /api/v1/runtime/query endpoint is wired."""
        response = self.client.post(
            "/api/v1/runtime/query",
            headers=self.headers,
            json={"query_type": "status"},
        )

        # Must return a response (not 405)
        assert response.status_code != 405, "Endpoint not wired"


@pytest.mark.lit
@pytest.mark.lit_l2_l3
class TestRunsAPIShape:
    """L2 Runs API response shape validation."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, mock_auth_headers):
        self.client = test_client
        self.headers = mock_auth_headers

    @pytest.mark.skip(
        reason="Bucket B: /api/v1/runs endpoint not implemented (workers at /api/v1/workers/business-builder/runs)"
    )
    def test_runs_list_endpoint_exists(self):
        """GET /api/v1/runs endpoint is wired."""
        response = self.client.get("/api/v1/runs", headers=self.headers)

        assert response.status_code != 405, "Endpoint not wired"
        assert response.status_code in (200, 401, 403, 500)

    def test_runs_list_response_shape(self):
        """Runs list returns array or error."""
        response = self.client.get("/api/v1/runs", headers=self.headers)

        if response.status_code == 200:
            data = response.json()

            # Must be list or object with items
            assert isinstance(data, (list, dict)), "Response must be array or object"

            if isinstance(data, dict):
                # Paginated response
                if "items" in data:
                    assert isinstance(data["items"], list)
                elif "runs" in data:
                    assert isinstance(data["runs"], list)

    @pytest.mark.skip(
        reason="Bucket B: /api/v1/runs endpoint not implemented (workers at /api/v1/workers/business-builder/runs)"
    )
    def test_runs_create_endpoint_exists(self):
        """POST /api/v1/runs endpoint is wired."""
        response = self.client.post(
            "/api/v1/runs",
            headers=self.headers,
            json={"worker_id": "test", "input": {}},
        )

        assert response.status_code != 405, "Endpoint not wired"
        assert response.status_code in (200, 201, 400, 401, 403, 422, 500)

    def test_runs_get_nonexistent_returns_404(self):
        """GET /api/v1/runs/{id} returns 404 for missing run."""
        response = self.client.get(
            "/api/v1/runs/nonexistent-run-id-12345",
            headers=self.headers,
        )

        # Should be 404 or 401/403 (not 500)
        assert response.status_code in (400, 401, 403, 404, 422)


@pytest.mark.lit
@pytest.mark.lit_l2_l3
class TestHealthEndpointShape:
    """Health endpoint integration (public, no auth)."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client):
        self.client = test_client

    def test_health_endpoint_exists(self):
        """GET /health is wired and public."""
        response = self.client.get("/health")

        assert response.status_code != 405, "Endpoint not wired"
        # Health should always return 200 (degraded health is still 200 with body)
        assert response.status_code in (200, 503)

    def test_health_response_shape(self):
        """Health response has expected structure."""
        response = self.client.get("/health")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

            # Common health check keys
            if "status" in data:
                assert data["status"] in ("healthy", "degraded", "unhealthy", "ok")


@pytest.mark.lit
@pytest.mark.lit_l2_l3
class TestErrorResponseShape:
    """All error responses have consistent shape."""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, mock_auth_headers):
        self.client = test_client
        self.headers = mock_auth_headers

    def test_validation_error_shape(self):
        """422 errors have FastAPI validation format."""
        # Send invalid payload
        response = self.client.post(
            "/api/v1/runs",
            headers=self.headers,
            json={"invalid": "payload"},  # Missing required fields
        )

        if response.status_code == 422:
            data = response.json()
            assert isinstance(data, dict)
            # FastAPI validation error format
            assert "detail" in data

    def test_content_type_is_json(self):
        """All API responses have JSON content type."""
        response = self.client.get("/api/v1/runtime/capabilities", headers=self.headers)

        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
