# Layer: L0 — Test
# AUDIENCE: INTERNAL
# Role: Pytest guard — veil policy determinism (env-driven posture controls)
# Reference: veil_policy.py, HOC_LAYER_TOPOLOGY_V2.0.0.md

"""
Veil Policy Unit Tests.

Proves that veil controls are deterministic and driven entirely by env vars:
  A. Non-prod defaults (preprod)
  B. Prod docs gating (HOC_DOCS_ENABLED)
  C. Deny-as-404 posture toggle (HOC_DENY_AS_404)
  D. Probe rate parsing (HOC_PROBE_RATE_PER_MIN)
"""

import pytest


# Re-import the module under test in each test via monkeypatch to ensure
# env var changes are picked up (the module reads os.getenv at call time).
MODULE = "app.hoc.cus.hoc_spine.authority.veil_policy"


def _import_veil():
    import importlib
    return importlib.import_module(MODULE)


class TestVeilPolicyNonProdDefaults:
    """Test A: Non-prod (preprod) defaults."""

    def test_schema_urls_empty(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "preprod")
        veil = _import_veil()
        assert veil.fastapi_schema_urls() == {}

    def test_deny_as_404_disabled(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "preprod")
        veil = _import_veil()
        assert veil.deny_as_404_enabled() is False

    def test_probe_rate_limit_disabled(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "preprod")
        veil = _import_veil()
        assert veil.probe_rate_limit_enabled() is False


class TestVeilPolicyProdDocsGating:
    """Test B: Prod docs gating via HOC_DOCS_ENABLED."""

    def test_docs_hidden_by_default(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "prod")
        monkeypatch.setenv("HOC_DOCS_ENABLED", "false")
        veil = _import_veil()
        result = veil.fastapi_schema_urls()
        assert result == {"openapi_url": None, "docs_url": None, "redoc_url": None}

    def test_docs_enabled_explicitly(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "prod")
        monkeypatch.setenv("HOC_DOCS_ENABLED", "true")
        veil = _import_veil()
        assert veil.fastapi_schema_urls() == {}


class TestVeilPolicyDenyAs404:
    """Test C: Deny-as-404 posture toggle."""

    def test_deny_as_404_enabled_prod(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "prod")
        monkeypatch.setenv("HOC_DENY_AS_404", "true")
        veil = _import_veil()
        assert veil.unauthenticated_http_status_code() == 404
        assert veil.unauthorized_http_status_code() == 404

    def test_deny_as_404_disabled_prod(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "prod")
        monkeypatch.setenv("HOC_DENY_AS_404", "false")
        veil = _import_veil()
        assert veil.unauthenticated_http_status_code(401) == 401
        assert veil.unauthorized_http_status_code(403) == 403


class TestVeilPolicyProbeRate:
    """Test D: Probe rate parsing."""

    def test_invalid_rate_returns_default(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "prod")
        monkeypatch.setenv("HOC_PROBE_RATE_PER_MIN", "abc")
        veil = _import_veil()
        assert veil.probe_rate_per_minute() == 60

    def test_valid_rate_parsed(self, monkeypatch):
        monkeypatch.setenv("AOS_MODE", "prod")
        monkeypatch.setenv("HOC_PROBE_RATE_PER_MIN", "120")
        veil = _import_veil()
        assert veil.probe_rate_per_minute() == 120
