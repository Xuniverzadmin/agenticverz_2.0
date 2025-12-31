# Layer Integration Test Fixtures
# Reference: PIN-245 (Integration Integrity System)
"""
LIT Test Fixtures

These fixtures provide layer-boundary testing without database or external deps.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """
    TestClient for API layer testing.
    Uses app directly without database connection for shape tests.
    """
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_auth_headers():
    """Standard auth headers for LIT tests."""
    return {
        "X-AOS-Key": "lit-test-key-not-real",
        "X-Tenant-Id": "lit-test-tenant",
    }


@pytest.fixture
def minimal_run_payload():
    """Minimal valid run payload for shape testing."""
    return {
        "worker_id": "test-worker",
        "input": {"test": True},
    }


@pytest.fixture
def minimal_simulate_payload():
    """Minimal valid simulate payload for shape testing."""
    return {
        "plan": {"steps": []},
        "budget_cents": 1000,
    }


# pytest markers for LIT
def pytest_configure(config):
    """Register LIT markers."""
    config.addinivalue_line("markers", "lit: Layer Integration Test")
    config.addinivalue_line("markers", "lit_l2_l3: L2 API to L3 Adapter seam")
    config.addinivalue_line("markers", "lit_l3_l4: L3 Adapter to L4 Domain seam")
    config.addinivalue_line("markers", "lit_l4_l5: L4 Domain to L5 Worker seam")
    config.addinivalue_line("markers", "lit_l2_l6: L2 API to L6 Platform seam")
