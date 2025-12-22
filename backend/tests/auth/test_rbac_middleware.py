"""
RBAC Middleware Tests - M7 Implementation

Tests for PolicyObject-based RBAC enforcement.

Run with:
    pytest tests/auth/test_rbac_middleware.py -v
"""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Import RBAC components
from app.auth.rbac_middleware import (
    RBAC_MATRIX,
    Decision,
    PolicyObject,
    RBACMiddleware,
    enforce,
    extract_roles_from_request,
    get_policy_for_path,
)


class TestPolicyObject:
    """Tests for PolicyObject dataclass."""

    def test_create_policy_object(self):
        """Test creating a PolicyObject."""
        policy = PolicyObject(resource="memory_pin", action="write")
        assert policy.resource == "memory_pin"
        assert policy.action == "write"
        assert policy.attrs == {}

    def test_policy_object_with_attrs(self):
        """Test PolicyObject with attributes."""
        policy = PolicyObject(resource="memory_pin", action="write", attrs={"tenant_id": "test", "key": "foo"})
        assert policy.attrs["tenant_id"] == "test"
        assert policy.attrs["key"] == "foo"


class TestDecision:
    """Tests for Decision dataclass."""

    def test_allowed_decision(self):
        """Test allowed decision."""
        decision = Decision(allowed=True, reason="role:admin", roles=["admin"])
        assert decision.allowed is True
        assert decision.reason == "role:admin"
        assert "admin" in decision.roles

    def test_denied_decision(self):
        """Test denied decision."""
        decision = Decision(allowed=False, reason="no-credentials", roles=[])
        assert decision.allowed is False
        assert decision.reason == "no-credentials"
        assert decision.roles == []


class TestRoleExtraction:
    """Tests for role extraction from requests."""

    def test_extract_machine_token(self, monkeypatch):
        """Test extracting machine role from X-Machine-Token header."""
        monkeypatch.setenv("MACHINE_SECRET_TOKEN", "test-machine-token")

        # Reload module to pick up new env
        import app.auth.rbac_middleware as rbac_mod

        rbac_mod.MACHINE_SECRET_TOKEN = "test-machine-token"

        request = MagicMock(spec=Request)
        request.headers = {"X-Machine-Token": "test-machine-token"}

        roles = extract_roles_from_request(request)
        assert roles == ["machine"]

    def test_extract_jwt_roles(self):
        """Test extracting roles from JWT token."""
        import jwt as pyjwt

        # Create a test JWT
        token = pyjwt.encode({"roles": ["admin", "dev"]}, "secret", algorithm="HS256")

        # Properly mock headers.get
        headers_dict = {"Authorization": f"Bearer {token}"}
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: headers_dict.get(k, d)

        roles = extract_roles_from_request(request)
        assert "admin" in roles
        assert "dev" in roles

    def test_extract_no_credentials(self):
        """Test extraction with no credentials."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: None

        roles = extract_roles_from_request(request)
        assert roles == []


class TestPolicyMapping:
    """Tests for path-to-policy mapping."""

    def test_memory_pins_get(self):
        """Test policy for GET /api/v1/memory/pins."""
        policy = get_policy_for_path("/api/v1/memory/pins/test-key", "GET")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "read"

    def test_memory_pins_post(self):
        """Test policy for POST /api/v1/memory/pins."""
        policy = get_policy_for_path("/api/v1/memory/pins", "POST")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "write"

    def test_memory_pins_delete(self):
        """Test policy for DELETE /api/v1/memory/pins."""
        policy = get_policy_for_path("/api/v1/memory/pins/test-key", "DELETE")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "delete"

    def test_memory_pins_cleanup(self):
        """Test policy for cleanup endpoint."""
        policy = get_policy_for_path("/api/v1/memory/pins/cleanup", "POST")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "admin"

    def test_prometheus_reload(self):
        """Test policy for Prometheus reload."""
        policy = get_policy_for_path("/-/reload", "POST")
        assert policy is not None
        assert policy.resource == "prometheus"
        assert policy.action == "reload"

    def test_unprotected_path(self):
        """Test that unprotected paths return None."""
        policy = get_policy_for_path("/health", "GET")
        assert policy is None

        policy = get_policy_for_path("/api/v1/agents", "GET")
        assert policy is None


class TestEnforcement:
    """Tests for policy enforcement."""

    def test_enforce_allowed_admin(self):
        """Test that admin role is allowed for memory_pin write."""
        policy = PolicyObject(resource="memory_pin", action="write")

        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {"X-Roles": "admin"}.get(k, d)

        decision = enforce(policy, request)
        assert decision.allowed is True
        assert "admin" in decision.roles

    def test_enforce_allowed_machine(self, monkeypatch):
        """Test that machine token allows memory_pin write."""
        monkeypatch.setenv("MACHINE_SECRET_TOKEN", "test-token")
        import app.auth.rbac_middleware as rbac_mod

        rbac_mod.MACHINE_SECRET_TOKEN = "test-token"

        policy = PolicyObject(resource="memory_pin", action="write")

        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {"X-Machine-Token": "test-token"}.get(k, d)

        decision = enforce(policy, request)
        assert decision.allowed is True
        assert "machine" in decision.roles

    def test_enforce_denied_insufficient_role(self):
        """Test that readonly role is denied for memory_pin write."""
        policy = PolicyObject(resource="memory_pin", action="write")

        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {"X-Roles": "readonly"}.get(k, d)

        decision = enforce(policy, request)
        assert decision.allowed is False
        assert decision.reason == "insufficient-permissions"

    def test_enforce_denied_no_credentials(self):
        """Test denial when no credentials provided."""
        policy = PolicyObject(resource="memory_pin", action="write")

        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: None

        decision = enforce(policy, request)
        assert decision.allowed is False
        assert decision.reason == "no-credentials"


class TestRBACMatrix:
    """Tests for RBAC matrix configuration."""

    def test_infra_has_admin_perms(self):
        """Test that infra role has admin permissions."""
        perms = RBAC_MATRIX.get("infra", {})
        assert "admin" in perms.get("memory_pin", [])
        assert "reload" in perms.get("prometheus", [])

    def test_machine_limited_perms(self):
        """Test that machine role has limited permissions."""
        perms = RBAC_MATRIX.get("machine", {})
        assert "read" in perms.get("memory_pin", [])
        assert "write" in perms.get("memory_pin", [])
        assert "delete" not in perms.get("memory_pin", [])
        assert "admin" not in perms.get("memory_pin", [])

    def test_readonly_only_reads(self):
        """Test that readonly role only has read access."""
        perms = RBAC_MATRIX.get("readonly", {})
        assert "read" in perms.get("memory_pin", [])
        assert "write" not in perms.get("memory_pin", [])
        assert "delete" not in perms.get("memory_pin", [])


class TestMiddlewareIntegration:
    """Integration tests for RBAC middleware."""

    @pytest.fixture
    def app_with_rbac(self):
        """Create a test FastAPI app with RBAC middleware."""
        app = FastAPI()

        # Add test endpoints
        @app.post("/api/v1/memory/pins")
        async def create_pin():
            return {"status": "created"}

        @app.get("/api/v1/memory/pins/{key}")
        async def get_pin(key: str):
            return {"key": key}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        # Add middleware with RBAC enforced
        app.add_middleware(RBACMiddleware, enforce_rbac=True)

        return app

    @pytest.fixture
    def client(self, app_with_rbac):
        """Create test client."""
        return TestClient(app_with_rbac, raise_server_exceptions=False)

    def test_unprotected_path_allowed(self, client):
        """Test that unprotected paths work without auth."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_protected_path_denied_no_auth(self, client):
        """Test that protected paths are denied without auth."""
        response = client.post("/api/v1/memory/pins", json={"tenant_id": "t1", "key": "k", "value": {}})
        assert response.status_code == 403
        assert "forbidden" in response.json().get("error", "")

    def test_protected_path_allowed_with_role(self, client, monkeypatch):
        """Test that protected paths work with valid role."""
        # Use X-Roles header for testing
        response = client.post(
            "/api/v1/memory/pins", json={"tenant_id": "t1", "key": "k", "value": {}}, headers={"X-Roles": "admin"}
        )
        assert response.status_code == 200

    def test_protected_path_allowed_with_machine_token(self, client, monkeypatch):
        """Test that machine token works."""
        monkeypatch.setenv("MACHINE_SECRET_TOKEN", "test-machine-token")
        import app.auth.rbac_middleware as rbac_mod

        rbac_mod.MACHINE_SECRET_TOKEN = "test-machine-token"

        response = client.post(
            "/api/v1/memory/pins",
            json={"tenant_id": "t1", "key": "k", "value": {}},
            headers={"X-Machine-Token": "test-machine-token"},
        )
        assert response.status_code == 200


class TestMiddlewareDisabled:
    """Tests for RBAC middleware when disabled."""

    @pytest.fixture
    def app_without_rbac(self):
        """Create a test FastAPI app with RBAC disabled."""
        app = FastAPI()

        @app.post("/api/v1/memory/pins")
        async def create_pin():
            return {"status": "created"}

        # Add middleware with RBAC disabled
        app.add_middleware(RBACMiddleware, enforce_rbac=False)

        return app

    @pytest.fixture
    def client(self, app_without_rbac):
        """Create test client."""
        return TestClient(app_without_rbac)

    def test_protected_path_allowed_when_disabled(self, client):
        """Test that protected paths work when RBAC is disabled."""
        response = client.post("/api/v1/memory/pins", json={"tenant_id": "t1", "key": "k", "value": {}})
        assert response.status_code == 200
