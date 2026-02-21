# Layer: TEST
# Product: system-wide
# AUDIENCE: INTERNAL
# Role: Smoke tests for Clove Identity API route scaffolds
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
Identity API Route Smoke Tests

Validates that scaffold endpoints:
1. Are registered in the router.
2. Return 501 Not Implemented (scaffold behavior) where applicable.
3. Have correct request/response schema shapes.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.hoc.api.auth.routes import router


@pytest.fixture
def client():
    """Create a test client with the auth router."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# =============================================================================
# Route Registration Tests
# =============================================================================


class TestRouteRegistration:
    """Verify all expected endpoints are registered."""

    def test_routes_registered(self):
        paths = {r.path for r in router.routes if hasattr(r, 'path')}
        expected = {
            "/hoc/api/auth/register",
            "/hoc/api/auth/login",
            "/hoc/api/auth/refresh",
            "/hoc/api/auth/switch-tenant",
            "/hoc/api/auth/logout",
            "/hoc/api/auth/me",
            "/hoc/api/auth/provider/status",
            "/hoc/api/auth/password/reset/request",
            "/hoc/api/auth/password/reset/confirm",
        }
        assert expected.issubset(paths), f"Missing routes: {expected - paths}"

    def test_route_count(self):
        """9 auth endpoints registered (8 scaffold + 1 provider status)."""
        routes_with_methods = [r for r in router.routes if hasattr(r, 'methods')]
        assert len(routes_with_methods) == 9


# =============================================================================
# Scaffold Response Tests (all return 501)
# =============================================================================


class TestScaffoldResponses:
    """Scaffold endpoints return 501 Not Implemented."""

    def test_register_returns_501(self, client):
        resp = client.post(
            "/hoc/api/auth/register",
            json={"email": "test@example.com", "password": "SecurePass123"},
        )
        assert resp.status_code == 501
        assert resp.json()["error"] == "not_implemented"

    def test_login_returns_501(self, client):
        resp = client.post(
            "/hoc/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert resp.status_code == 501
        assert resp.json()["error"] == "not_implemented"

    def test_refresh_returns_501(self, client):
        resp = client.post("/hoc/api/auth/refresh")
        assert resp.status_code == 501

    def test_switch_tenant_returns_501(self, client):
        resp = client.post(
            "/hoc/api/auth/switch-tenant",
            json={"tenant_id": "tenant_123", "csrf_token": "tok"},
        )
        assert resp.status_code == 501

    def test_logout_returns_501(self, client):
        resp = client.post("/hoc/api/auth/logout")
        assert resp.status_code == 501

    def test_me_returns_501(self, client):
        resp = client.get("/hoc/api/auth/me")
        assert resp.status_code == 501

    def test_provider_status_returns_200(self, client):
        resp = client.get("/hoc/api/auth/provider/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["effective_provider"] == "clove"
        assert body["canonical_provider"] == "clove"
        assert "configured" in body
        assert "deprecation" in body
        assert body["deprecation"]["clerk"]["status"] == "deprecated"

    def test_password_reset_request_returns_501(self, client):
        resp = client.post(
            "/hoc/api/auth/password/reset/request",
            json={"email": "test@example.com"},
        )
        assert resp.status_code == 501

    def test_password_reset_confirm_returns_501(self, client):
        resp = client.post(
            "/hoc/api/auth/password/reset/confirm",
            json={"token": "reset_tok", "new_password": "NewSecure123"},
        )
        assert resp.status_code == 501


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Request schema validation works on scaffold endpoints."""

    def test_register_rejects_short_password(self, client):
        resp = client.post(
            "/hoc/api/auth/register",
            json={"email": "test@example.com", "password": "short"},
        )
        # Should fail validation (password min_length=8), not 501
        assert resp.status_code == 422

    def test_register_rejects_invalid_email(self, client):
        resp = client.post(
            "/hoc/api/auth/register",
            json={"email": "not-an-email", "password": "SecurePass123"},
        )
        assert resp.status_code == 422

    def test_login_rejects_missing_fields(self, client):
        resp = client.post("/hoc/api/auth/login", json={})
        assert resp.status_code == 422

    def test_switch_tenant_rejects_missing_csrf(self, client):
        resp = client.post(
            "/hoc/api/auth/switch-tenant",
            json={"tenant_id": "tenant_123"},
        )
        assert resp.status_code == 422

    def test_password_reset_rejects_short_password(self, client):
        resp = client.post(
            "/hoc/api/auth/password/reset/confirm",
            json={"token": "tok", "new_password": "short"},
        )
        assert resp.status_code == 422
