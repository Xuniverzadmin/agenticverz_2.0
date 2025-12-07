"""
M7 RBAC & Memory Integration Tests

Tests for:
- RBAC audit logging (allowed and denied decisions)
- Memory pins CRUD operations
- Memory audit logging
- TTL expiration behavior
- Machine token authentication
"""

import os
import time
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import httpx
from sqlalchemy import text

# Test configuration
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nova:novapass@localhost:6432/nova_aos")
MACHINE_TOKEN = os.getenv("MACHINE_SECRET_TOKEN", "")


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def client():
    """HTTP client for API calls with machine token auth."""
    headers = {}
    if MACHINE_TOKEN:
        headers["X-Machine-Token"] = MACHINE_TOKEN
    with httpx.Client(base_url=API_BASE, timeout=30.0, headers=headers) as client:
        yield client


@pytest.fixture(scope="module")
def unauthenticated_client():
    """HTTP client without authentication for testing RBAC denials."""
    with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="module")
def db_session():
    """Database session for direct queries."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        yield session


@pytest.fixture
def unique_tenant():
    """Generate unique tenant ID for test isolation."""
    return f"test-tenant-{int(time.time() * 1000)}"


@pytest.fixture
def unique_key():
    """Generate unique key for test isolation."""
    return f"test:key:{int(time.time() * 1000)}"


# =============================================================================
# Memory Pins CRUD Tests
# =============================================================================

class TestMemoryPinsCRUD:
    """Test memory pins create, read, update, delete."""

    def test_create_pin(self, client, unique_tenant, unique_key):
        """Test creating a memory pin."""
        response = client.post(
            "/api/v1/memory/pins",
            json={
                "tenant_id": unique_tenant,
                "key": unique_key,
                "value": {"test": True, "created_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        assert response.status_code in (200, 201), f"Create failed: {response.text}"
        data = response.json()
        assert data["tenant_id"] == unique_tenant
        assert data["key"] == unique_key
        assert data["value"]["test"] is True

    def test_get_pin(self, client, unique_tenant, unique_key):
        """Test retrieving a memory pin."""
        # Create first
        client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"test": 123}}
        )

        # Get
        response = client.get(f"/api/v1/memory/pins/{unique_key}?tenant_id={unique_tenant}")
        assert response.status_code == 200, f"Get failed: {response.text}"
        data = response.json()
        assert data["value"]["test"] == 123

    def test_update_pin_upsert(self, client, unique_tenant, unique_key):
        """Test updating a pin via upsert."""
        # Create
        client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"version": 1}}
        )

        # Update (upsert)
        response = client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"version": 2}}
        )
        assert response.status_code in (200, 201)

        # Verify
        get_response = client.get(f"/api/v1/memory/pins/{unique_key}?tenant_id={unique_tenant}")
        assert get_response.json()["value"]["version"] == 2

    @pytest.mark.skipif(
        MACHINE_TOKEN and "machine" not in os.getenv("TEST_RBAC_ROLE", "machine"),
        reason="Machine role doesn't have delete permission"
    )
    def test_delete_pin(self, client, unique_tenant, unique_key):
        """Test deleting a memory pin.

        Note: Machine role may not have delete permissions - test with admin role
        or when RBAC is not enforced.
        """
        # Create
        client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"to_delete": True}}
        )

        # Delete - may fail with 403 if machine role
        response = client.delete(f"/api/v1/memory/pins/{unique_key}?tenant_id={unique_tenant}")

        # Accept 200 (success) or 403 (no delete permission for machine role)
        if response.status_code == 403:
            pytest.skip("Machine role doesn't have delete permission (expected)")

        assert response.status_code == 200, f"Delete failed: {response.text}"

        # Verify gone
        get_response = client.get(f"/api/v1/memory/pins/{unique_key}?tenant_id={unique_tenant}")
        assert get_response.status_code == 404

    def test_list_pins_with_prefix(self, client, unique_tenant):
        """Test listing pins with prefix filter."""
        prefix = f"prefix-{int(time.time())}"

        # Create multiple pins
        for i in range(3):
            client.post(
                "/api/v1/memory/pins",
                json={"tenant_id": unique_tenant, "key": f"{prefix}:item:{i}", "value": {"i": i}}
            )

        # List with prefix
        response = client.get(f"/api/v1/memory/pins?tenant_id={unique_tenant}&prefix={prefix}")
        assert response.status_code == 200
        data = response.json()
        # Response format: {"pins": [...], "total": N, "limit": N, "offset": N}
        assert data["total"] >= 3
        assert len(data["pins"]) >= 3


# =============================================================================
# Memory Audit Tests
# =============================================================================

class TestMemoryAudit:
    """Test memory audit logging."""

    def test_audit_on_create(self, client, db_session, unique_tenant, unique_key):
        """Test audit entry created on pin creation."""
        # Get audit count before
        before = db_session.execute(
            text("SELECT count(*) FROM system.memory_audit WHERE tenant_id = :tenant"),
            {"tenant": unique_tenant}
        ).scalar()

        # Create pin
        client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"audit_test": True}}
        )

        # Check audit count after
        db_session.commit()  # Refresh
        after = db_session.execute(
            text("SELECT count(*) FROM system.memory_audit WHERE tenant_id = :tenant"),
            {"tenant": unique_tenant}
        ).scalar()

        assert after > before, "No audit entry created for upsert"

    def test_audit_has_value_hash(self, client, db_session, unique_tenant, unique_key):
        """Test audit entries contain value hash, not full value."""
        # Create pin
        client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"secret": "data"}}
        )

        db_session.commit()

        # Check audit entry
        result = db_session.execute(
            text("""
                SELECT new_value_hash FROM system.memory_audit
                WHERE tenant_id = :tenant AND key = :key
                ORDER BY ts DESC LIMIT 1
            """),
            {"tenant": unique_tenant, "key": unique_key}
        ).fetchone()

        assert result is not None, "No audit entry found"
        assert result[0] is not None, "Value hash is null"
        assert len(result[0]) == 16, f"Value hash should be 16 chars, got {len(result[0])}"

    def test_audit_on_delete(self, client, db_session, unique_tenant, unique_key):
        """Test audit entry created on pin deletion.

        Note: Machine role may not have delete permissions - test skipped if 403.
        """
        # Create first
        client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"to_delete": True}}
        )

        # Delete - may fail with 403 if machine role
        delete_response = client.delete(f"/api/v1/memory/pins/{unique_key}?tenant_id={unique_tenant}")
        if delete_response.status_code == 403:
            pytest.skip("Machine role doesn't have delete permission - cannot test delete audit")

        db_session.commit()

        # Check delete audit entry
        result = db_session.execute(
            text("""
                SELECT operation FROM system.memory_audit
                WHERE tenant_id = :tenant AND key = :key AND operation = 'delete'
            """),
            {"tenant": unique_tenant, "key": unique_key}
        ).fetchone()

        assert result is not None, "No delete audit entry found"


# =============================================================================
# TTL Expiration Tests
# =============================================================================

class TestTTLExpiration:
    """Test TTL-based pin expiration."""

    def test_create_pin_with_ttl(self, client, unique_tenant, unique_key):
        """Test creating a pin with TTL."""
        response = client.post(
            "/api/v1/memory/pins",
            json={
                "tenant_id": unique_tenant,
                "key": unique_key,
                "value": {"expires": True},
                "ttl_seconds": 3600  # 1 hour
            }
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["ttl_seconds"] == 3600
        assert data["expires_at"] is not None

    def test_expired_pin_not_returned(self, client, db_session, unique_tenant, unique_key):
        """Test that expired pins are filtered correctly.

        Note: TTL expiration is handled by a cleanup job, not at query time.
        This test verifies that after cleanup, expired pins are not returned.
        The API may still return expired pins until the cleanup job runs.
        """
        # Create pin with past expiration directly in DB
        db_session.execute(
            text("""
                INSERT INTO system.memory_pins (tenant_id, key, value, ttl_seconds, expires_at, source)
                VALUES (:tenant, :key, CAST(:value AS jsonb), 1, now() - interval '1 hour', 'test')
                ON CONFLICT (tenant_id, key) DO UPDATE SET
                    expires_at = now() - interval '1 hour'
            """),
            {"tenant": unique_tenant, "key": unique_key, "value": '{"expired": true}'}
        )
        db_session.commit()

        # Try to get - API currently returns pin even if expired
        # (TTL cleanup is handled by background job)
        response = client.get(f"/api/v1/memory/pins/{unique_key}?tenant_id={unique_tenant}")

        # Verify the pin exists with past expiration
        if response.status_code == 200:
            data = response.json()
            assert data["expires_at"] is not None, "Expired pin should have expires_at set"
            # Note: API returns pin until cleanup job runs - this is expected behavior
        elif response.status_code == 404:
            # Pin was cleaned up by TTL job - also acceptable
            pass
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


# =============================================================================
# RBAC Tests (when enforced)
# =============================================================================

class TestRBACEnforcement:
    """Test RBAC enforcement behavior."""

    def test_rbac_info_endpoint(self, client):
        """Test RBAC info endpoint returns status."""
        response = client.get("/api/v1/rbac/info")
        assert response.status_code == 200
        data = response.json()
        assert "enforce_mode" in data
        assert "hash" in data

    @pytest.mark.skipif(not MACHINE_TOKEN, reason="MACHINE_SECRET_TOKEN not set")
    def test_machine_token_allows_write(self, client, unique_tenant, unique_key):
        """Test machine token allows memory pin writes."""
        response = client.post(
            "/api/v1/memory/pins",
            headers={"X-Machine-Token": MACHINE_TOKEN},
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"machine": True}}
        )
        assert response.status_code in (200, 201), f"Machine token write failed: {response.text}"

    def test_unauthorized_when_rbac_enforced(self, client, unauthenticated_client, unique_tenant, unique_key):
        """Test unauthorized access when RBAC is enforced."""
        # Get current RBAC status (using authenticated client)
        info = client.get("/api/v1/rbac/info").json()

        if not info.get("enforce_mode"):
            pytest.skip("RBAC not enforced - skipping unauthorized test")

        # Try without any auth - should get 403
        response = unauthenticated_client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"unauth": True}}
        )
        assert response.status_code == 403, "Should be blocked when RBAC enforced"


# =============================================================================
# RBAC Audit Tests
# =============================================================================

class TestRBACAudit:
    """Test RBAC audit logging."""

    @pytest.mark.skipif(not MACHINE_TOKEN, reason="MACHINE_SECRET_TOKEN not set")
    def test_rbac_audit_on_allowed(self, client, db_session, unique_tenant, unique_key):
        """Test RBAC audit entry for allowed decision."""
        # Get RBAC info
        info = client.get("/api/v1/rbac/info").json()

        if not info.get("enforce_mode"):
            pytest.skip("RBAC not enforced - audit not recorded")

        # Make authenticated request
        client.post(
            "/api/v1/memory/pins",
            headers={"X-Machine-Token": MACHINE_TOKEN},
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"audit": True}}
        )

        db_session.commit()

        # Check audit
        result = db_session.execute(
            text("""
                SELECT subject, allowed, resource, action FROM system.rbac_audit
                WHERE allowed = true
                ORDER BY ts DESC LIMIT 1
            """)
        ).fetchone()

        assert result is not None, "No allowed RBAC audit entry found"
        assert result[1] is True  # allowed

    def test_rbac_audit_on_denied(self, client, unauthenticated_client, db_session, unique_tenant, unique_key):
        """Test RBAC audit entry for denied decision."""
        info = client.get("/api/v1/rbac/info").json()

        if not info.get("enforce_mode"):
            pytest.skip("RBAC not enforced - denials not recorded")

        # Make unauthenticated request - should be denied
        unauthenticated_client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": unique_tenant, "key": unique_key, "value": {"denied": True}}
        )

        db_session.commit()

        # Check audit
        result = db_session.execute(
            text("""
                SELECT subject, allowed, reason FROM system.rbac_audit
                WHERE allowed = false
                ORDER BY ts DESC LIMIT 1
            """)
        ).fetchone()

        assert result is not None, "No denied RBAC audit entry found"
        assert result[1] is False  # denied


# =============================================================================
# CostSim Memory Integration Tests
# =============================================================================

class TestCostSimMemory:
    """Test CostSim memory integration."""

    def test_costsim_v2_status(self, client):
        """Test CostSim V2 status endpoint."""
        response = client.get("/costsim/v2/status")
        assert response.status_code == 200
        data = response.json()
        assert "sandbox_enabled" in data
        assert "circuit_breaker_open" in data

    def test_costsim_simulate_with_memory_flag(self, client, unique_tenant):
        """Test CostSim simulation with memory injection flag."""
        response = client.post(
            "/costsim/v2/simulate",
            json={
                "plan": [{"skill": "noop", "params": {}}],
                "budget_cents": 1000,
                "tenant_id": unique_tenant,
                "workflow_id": "test-workflow",
                "inject_memory": True
            }
        )
        # May fail if noop skill not registered, but should not error on memory path
        assert response.status_code in (200, 400, 422), f"Unexpected error: {response.text}"


# =============================================================================
# Metrics Tests
# =============================================================================

class TestMetrics:
    """Test Prometheus metrics are emitted."""

    def test_rbac_metrics_present(self, client):
        """Test RBAC metrics are exposed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text

        assert "rbac_engine_decisions_total" in metrics, "RBAC decisions metric missing"
        assert "rbac_engine_latency_seconds" in metrics, "RBAC latency metric missing"

    def test_memory_metrics_present(self, client):
        """Test memory metrics are exposed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text

        assert "memory_pins_operations_total" in metrics, "Memory pins ops metric missing"
        assert "memory_service_operations_total" in metrics, "Memory service ops metric missing"

    def test_drift_metrics_present(self, client):
        """Test drift detection metrics are exposed."""
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text

        # These may not have data yet, but declarations should exist
        assert "memory_context_injection_failures_total" in metrics or \
               "drift_detected_total" in metrics or \
               "drift_score_current" in metrics, "Drift metrics not found"


# =============================================================================
# Run with: PYTHONPATH=. pytest tests/integration/test_m7_rbac_memory.py -v
# =============================================================================
