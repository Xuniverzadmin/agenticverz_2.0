"""
RBAC Engine Tests - M7 Implementation

Tests for the enhanced RBAC engine with hot-reload and audit capabilities.

Run with:
    pytest tests/auth/test_rbac_engine.py -v
"""

import json
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request

# Import RBAC engine components
from app.auth.rbac_engine import (
    PolicyObject,
    Decision,
    PolicyConfig,
    RBACEngine,
    get_policy_for_path,
    check_permission,
    get_rbac_engine,
    init_rbac_engine,
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
        policy = PolicyObject(
            resource="memory_pin",
            action="write",
            attrs={"tenant_id": "test", "key": "foo"}
        )
        assert policy.attrs["tenant_id"] == "test"
        assert policy.attrs["key"] == "foo"

    def test_policy_object_hashable(self):
        """Test PolicyObject is hashable for use in sets/dicts."""
        p1 = PolicyObject(resource="memory_pin", action="read")
        p2 = PolicyObject(resource="memory_pin", action="read")
        p3 = PolicyObject(resource="memory_pin", action="write")

        # Same resource+action should hash the same
        assert hash(p1) == hash(p2)
        # Different actions should hash differently
        assert hash(p1) != hash(p3)

        # Can be used in sets
        policy_set = {p1, p2, p3}
        assert len(policy_set) == 2  # p1 and p2 should dedupe


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

    def test_decision_with_policy(self):
        """Test decision with policy object attached."""
        policy = PolicyObject(resource="memory_pin", action="write")
        decision = Decision(allowed=True, reason="test", policy=policy)
        assert decision.policy is not None
        assert decision.policy.resource == "memory_pin"


class TestRBACEngineBasics:
    """Tests for RBACEngine basic functionality."""

    @pytest.fixture
    def engine_without_policy_file(self, monkeypatch):
        """Create engine without policy file (uses defaults)."""
        # Reset singleton
        RBACEngine._instance = None

        # Set env to ensure RBAC is enforced
        monkeypatch.setenv("RBAC_ENFORCE", "true")
        monkeypatch.setenv("RBAC_FAIL_OPEN", "false")
        monkeypatch.setenv("RBAC_AUDIT_ENABLED", "false")

        # Use non-existent policy file
        engine = RBACEngine(policy_file="/tmp/nonexistent_policy.json")
        yield engine

        # Cleanup
        RBACEngine._instance = None

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"
        return request

    def test_engine_singleton(self, engine_without_policy_file):
        """Test that RBACEngine is a singleton."""
        engine2 = RBACEngine()
        assert engine_without_policy_file is engine2

    def test_default_policy_loaded(self, engine_without_policy_file):
        """Test default policy is loaded when file not found."""
        info = engine_without_policy_file.get_policy_info()
        assert info["version"] == "default"
        assert "infra" in info["roles"]
        assert "admin" in info["roles"]

    def test_check_allowed_admin(self, engine_without_policy_file, mock_request, monkeypatch):
        """Test admin role is allowed for all actions."""
        # Import and patch RBAC_ENFORCE
        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", True)

        mock_request.headers.get = lambda k, d=None: {
            "X-Roles": "admin"
        }.get(k, d)

        policy = PolicyObject(resource="memory_pin", action="admin")
        decision = engine_without_policy_file.check(policy, mock_request)

        assert decision.allowed is True
        assert "admin" in decision.roles

    def test_check_denied_readonly(self, engine_without_policy_file, mock_request, monkeypatch):
        """Test readonly role is denied for write actions."""
        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", True)
        monkeypatch.setattr(rbac_mod, "RBAC_FAIL_OPEN", False)

        mock_request.headers.get = lambda k, d=None: {
            "X-Roles": "readonly"
        }.get(k, d)

        policy = PolicyObject(resource="memory_pin", action="write")
        decision = engine_without_policy_file.check(policy, mock_request)

        assert decision.allowed is False
        assert "readonly" in decision.roles

    def test_check_rbac_disabled(self, mock_request, monkeypatch):
        """Test all requests allowed when RBAC disabled."""
        # Reset singleton
        RBACEngine._instance = None

        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", False)

        engine = RBACEngine(policy_file="/tmp/nonexistent.json")
        mock_request.headers.get = lambda k, d=None: None  # No credentials

        policy = PolicyObject(resource="memory_pin", action="admin")
        decision = engine.check(policy, mock_request)

        assert decision.allowed is True
        assert decision.reason == "rbac-disabled"

        # Cleanup
        RBACEngine._instance = None


class TestPolicyHotReload:
    """Tests for policy hot-reload functionality."""

    @pytest.fixture
    def temp_policy_file(self):
        """Create a temporary policy file."""
        policy_data = {
            "version": "1.0.0",
            "matrix": {
                "test_role": {
                    "test_resource": ["read", "write"]
                }
            },
            "path_mappings": []
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(policy_data, f)
            f.flush()
            yield f.name

        # Cleanup
        os.unlink(f.name)

    @pytest.fixture
    def engine_with_policy(self, temp_policy_file, monkeypatch):
        """Create engine with policy file."""
        RBACEngine._instance = None
        monkeypatch.setenv("RBAC_AUDIT_ENABLED", "false")
        engine = RBACEngine(policy_file=temp_policy_file)
        yield engine
        RBACEngine._instance = None

    def test_policy_loaded_from_file(self, engine_with_policy):
        """Test policy is loaded from file."""
        info = engine_with_policy.get_policy_info()
        assert info["version"] == "1.0.0"
        assert "test_role" in info["roles"]

    def test_reload_policy_success(self, engine_with_policy, temp_policy_file):
        """Test successful policy reload."""
        # Update policy file
        new_policy = {
            "version": "2.0.0",
            "matrix": {
                "new_role": {
                    "new_resource": ["admin"]
                }
            },
            "path_mappings": []
        }

        with open(temp_policy_file, 'w') as f:
            json.dump(new_policy, f)

        # Reload
        success, message = engine_with_policy.reload_policy()

        assert success is True
        info = engine_with_policy.get_policy_info()
        assert info["version"] == "2.0.0"
        assert "new_role" in info["roles"]

    def test_reload_policy_invalid_json(self, engine_with_policy, temp_policy_file):
        """Test reload with invalid JSON."""
        # Write invalid JSON
        with open(temp_policy_file, 'w') as f:
            f.write("{ invalid json }")

        success, message = engine_with_policy.reload_policy()

        assert success is False
        assert "JSON parse error" in message

    def test_policy_hash_changes_on_reload(self, engine_with_policy, temp_policy_file):
        """Test policy hash changes when content changes."""
        old_info = engine_with_policy.get_policy_info()
        old_hash = old_info["hash"]

        # Update policy
        new_policy = {
            "version": "3.0.0",
            "matrix": {"changed": {}},
            "path_mappings": []
        }

        with open(temp_policy_file, 'w') as f:
            json.dump(new_policy, f)

        engine_with_policy.reload_policy()
        new_info = engine_with_policy.get_policy_info()

        assert new_info["hash"] != old_hash


class TestMachineTokenAuth:
    """Tests for machine token authentication."""

    @pytest.fixture
    def engine_with_machine_token(self, monkeypatch):
        """Create engine with machine token configured."""
        RBACEngine._instance = None
        monkeypatch.setenv("MACHINE_SECRET_TOKEN", "test-machine-secret")
        monkeypatch.setenv("RBAC_ENFORCE", "true")
        monkeypatch.setenv("RBAC_AUDIT_ENABLED", "false")

        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "MACHINE_SECRET_TOKEN", "test-machine-secret")
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", True)

        engine = RBACEngine(policy_file="/tmp/nonexistent.json")
        yield engine
        RBACEngine._instance = None

    def test_valid_machine_token(self, engine_with_machine_token):
        """Test valid machine token grants machine role."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {
            "X-Machine-Token": "test-machine-secret"
        }.get(k, d)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "POST"

        policy = PolicyObject(resource="memory_pin", action="write")
        decision = engine_with_machine_token.check(policy, request)

        assert decision.allowed is True
        assert "machine" in decision.roles

    def test_invalid_machine_token(self, engine_with_machine_token):
        """Test invalid machine token is rejected."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {
            "X-Machine-Token": "wrong-token"
        }.get(k, d)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "POST"

        policy = PolicyObject(resource="memory_pin", action="admin")
        decision = engine_with_machine_token.check(policy, request)

        # Should fail since wrong token doesn't give machine role
        # and machine role doesn't have admin permission anyway
        assert decision.allowed is False


class TestJWTAuth:
    """Tests for JWT authentication."""

    @pytest.fixture
    def engine_with_jwt(self, monkeypatch):
        """Create engine with JWT configured."""
        RBACEngine._instance = None
        monkeypatch.setenv("RBAC_ENFORCE", "true")
        monkeypatch.setenv("RBAC_AUDIT_ENABLED", "false")
        monkeypatch.setenv("JWT_VERIFY_SIGNATURE", "false")

        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", True)
        monkeypatch.setattr(rbac_mod, "JWT_VERIFY_SIGNATURE", False)

        engine = RBACEngine(policy_file="/tmp/nonexistent.json")
        yield engine
        RBACEngine._instance = None

    def test_jwt_roles_extraction(self, engine_with_jwt):
        """Test roles are extracted from JWT token."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"roles": ["admin", "dev"]},
            "secret",
            algorithm="HS256"
        )

        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {
            "Authorization": f"Bearer {token}"
        }.get(k, d)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        policy = PolicyObject(resource="memory_pin", action="admin")
        decision = engine_with_jwt.check(policy, request)

        assert decision.allowed is True
        assert "admin" in decision.roles

    def test_jwt_single_role_string(self, engine_with_jwt):
        """Test JWT with single role as string (not list)."""
        import jwt as pyjwt

        token = pyjwt.encode(
            {"roles": "infra"},  # Single string instead of list
            "secret",
            algorithm="HS256"
        )

        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {
            "Authorization": f"Bearer {token}"
        }.get(k, d)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        policy = PolicyObject(resource="memory_pin", action="admin")
        decision = engine_with_jwt.check(policy, request)

        assert decision.allowed is True


class TestPathToPolicy:
    """Tests for path-to-policy mapping."""

    def test_memory_pins_get(self):
        """Test GET memory pins maps to read."""
        policy = get_policy_for_path("/api/v1/memory/pins/test-key", "GET")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "read"

    def test_memory_pins_post(self):
        """Test POST memory pins maps to write."""
        policy = get_policy_for_path("/api/v1/memory/pins", "POST")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "write"

    def test_memory_pins_delete(self):
        """Test DELETE memory pins maps to delete."""
        policy = get_policy_for_path("/api/v1/memory/pins/key", "DELETE")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "delete"

    def test_memory_pins_cleanup(self):
        """Test cleanup endpoint maps to admin."""
        policy = get_policy_for_path("/api/v1/memory/pins/cleanup", "POST")
        assert policy is not None
        assert policy.resource == "memory_pin"
        assert policy.action == "admin"

    def test_rbac_reload(self):
        """Test RBAC reload endpoint."""
        policy = get_policy_for_path("/api/v1/rbac/reload", "POST")
        assert policy is not None
        assert policy.resource == "rbac"
        assert policy.action == "reload"

    def test_rbac_info(self):
        """Test RBAC info endpoint."""
        policy = get_policy_for_path("/api/v1/rbac/info", "GET")
        assert policy is not None
        assert policy.resource == "rbac"
        assert policy.action == "read"

    def test_prometheus_reload(self):
        """Test Prometheus reload endpoint."""
        policy = get_policy_for_path("/-/reload", "POST")
        assert policy is not None
        assert policy.resource == "prometheus"
        assert policy.action == "reload"

    def test_costsim_get(self):
        """Test CostSim GET endpoint."""
        policy = get_policy_for_path("/api/v1/costsim/status", "GET")
        assert policy is not None
        assert policy.resource == "costsim"
        assert policy.action == "read"

    def test_unprotected_path(self):
        """Test unprotected paths return None."""
        policy = get_policy_for_path("/health", "GET")
        assert policy is None

        policy = get_policy_for_path("/metrics", "GET")
        assert policy is None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def setup_engine(self, monkeypatch):
        """Setup engine for convenience function tests."""
        RBACEngine._instance = None
        monkeypatch.setenv("RBAC_ENFORCE", "false")
        monkeypatch.setenv("RBAC_AUDIT_ENABLED", "false")

        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", False)
        rbac_mod._engine = None

        yield

        RBACEngine._instance = None
        rbac_mod._engine = None

    def test_get_rbac_engine(self, setup_engine):
        """Test getting engine instance."""
        engine = get_rbac_engine()
        assert engine is not None
        assert isinstance(engine, RBACEngine)

    def test_init_rbac_engine(self, setup_engine):
        """Test initializing engine with db factory."""
        mock_factory = MagicMock()
        engine = init_rbac_engine(db_session_factory=mock_factory)
        assert engine is not None

    def test_check_permission_function(self, setup_engine):
        """Test check_permission convenience function."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: None
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        decision = check_permission("memory_pin", "read", request)

        # Should be allowed since RBAC_ENFORCE is false
        assert decision.allowed is True


class TestFailOpenMode:
    """Tests for fail-open mode."""

    @pytest.fixture
    def engine_fail_open(self, monkeypatch):
        """Create engine with fail-open enabled."""
        RBACEngine._instance = None
        monkeypatch.setenv("RBAC_ENFORCE", "true")
        monkeypatch.setenv("RBAC_FAIL_OPEN", "true")
        monkeypatch.setenv("RBAC_AUDIT_ENABLED", "false")

        import app.auth.rbac_engine as rbac_mod
        monkeypatch.setattr(rbac_mod, "RBAC_ENFORCE", True)
        monkeypatch.setattr(rbac_mod, "RBAC_FAIL_OPEN", True)

        engine = RBACEngine(policy_file="/tmp/nonexistent.json")
        yield engine
        RBACEngine._instance = None

    def test_no_credentials_fail_open(self, engine_fail_open):
        """Test no credentials allowed in fail-open mode."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: None
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        policy = PolicyObject(resource="memory_pin", action="write")
        decision = engine_fail_open.check(policy, request)

        assert decision.allowed is True
        assert "fail-open" in decision.reason

    def test_insufficient_perms_fail_open(self, engine_fail_open):
        """Test insufficient permissions allowed in fail-open mode."""
        request = MagicMock(spec=Request)
        request.headers = MagicMock()
        request.headers.get = lambda k, d=None: {
            "X-Roles": "readonly"
        }.get(k, d)
        request.url = MagicMock()
        request.url.path = "/test"
        request.method = "GET"

        policy = PolicyObject(resource="memory_pin", action="admin")
        decision = engine_fail_open.check(policy, request)

        assert decision.allowed is True
        assert "fail-open" in decision.reason
