"""
Pytest configuration and shared fixtures for AOS tests.

Test Categories:
- Unit tests: Fast, no external dependencies (tests/schemas/, tests/unit/)
- Integration tests: Require Redis/PostgreSQL (tests/test_integration.py)
- E2E tests: Full stack tests (tests/test_phase4_e2e.py)
- Security tests: Security validation (tests/test_phase5_security.py)

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string
- AOS_API_KEY: API key for authenticated endpoints
- ENFORCE_TENANCY: Whether to enforce tenant isolation
"""
import os
import sys
from pathlib import Path

import pytest

# Add backend/app to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Default test environment
os.environ.setdefault("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AOS_API_KEY", "test-key-for-testing")
os.environ.setdefault("ENFORCE_TENANCY", "false")


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API tests."""
    return os.environ.get("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_key():
    """API key for authenticated requests."""
    return os.environ.get("AOS_API_KEY", "test-key-for-testing")


@pytest.fixture
def auth_headers(api_key):
    """Headers with API key authentication."""
    return {"X-AOS-Key": api_key}


@pytest.fixture
def sample_agent_profile():
    """Sample agent profile for testing."""
    return {
        "agent_id": "test-agent-001",
        "name": "Test Agent",
        "version": "1.0.0",
        "description": "Agent for testing",
        "allowed_skills": ["http_call", "json_transform"],
        "budget": {
            "max_cost_cents_per_run": 100,
            "max_cost_cents_per_day": 1000
        },
        "policies": {
            "require_human_approval": False,
            "allowed_domains": ["api.example.com"]
        }
    }


@pytest.fixture
def sample_skill_metadata():
    """Sample skill metadata for testing."""
    return {
        "skill_id": "http_call",
        "version": "1.0.0",
        "name": "HTTP Call",
        "description": "Make HTTP requests",
        "deterministic": False,
        "side_effects": ["network"],
        "cost_estimate_cents": 0,
        "avg_latency_ms": 500,
        "retry": {
            "max_retries": 3,
            "backoff_base_ms": 100,
            "backoff_multiplier": 2.0
        }
    }


@pytest.fixture
def sample_structured_outcome():
    """Sample StructuredOutcome for testing."""
    from datetime import datetime, timezone
    return {
        "status": "success",
        "code": "OK_HTTP_CALL",
        "message": "HTTP call completed successfully",
        "cost_cents": 0,
        "latency_ms": 250,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retryable": False,
        "details": {"status_code": 200},
        "side_effects": [],
        "metadata": {"skill_id": "http_call", "skill_version": "1.0.0"}
    }


# Markers for test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (require services)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full stack)")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests (>5s)")
    config.addinivalue_line("markers", "determinism: Determinism validation tests")
    config.addinivalue_line("markers", "chaos: Chaos tests (resource stress, failure injection)")
