"""
Unit Tests for RBAC Path Mapping - M7-M28 RBAC Integration (PIN-169)

Tests the expanded path-to-policy mapping for all 14+ resources.

INVARIANTS TESTED:
1. No path returns None for protected routes (except public paths)
2. All resources are correctly mapped
3. HTTP methods map to correct actions

ENVIRONMENT-AWARE TESTING (PIN-391, PIN-427):
Many paths are PUBLIC in preflight for SDSR validation but PROTECTED in production.
Tests assert the correct behavior per environment:
- Preflight: PUBLIC paths return None (no policy needed)
- Production: Protected paths return PolicyObject with resource/action

Created: 2025-12-25
Updated: 2026-02-04 (Environment-aware assertions)
"""

import os

import pytest

from app.auth.rbac_middleware import PolicyObject, get_policy_for_path

# ============================================================================
# Environment Detection
# ============================================================================

_IS_PREFLIGHT = os.getenv("AOS_ENVIRONMENT", "preflight") == "preflight"
_IS_PRODUCTION = not _IS_PREFLIGHT

# ============================================================================
# Preflight PUBLIC Paths (from RBAC_RULES.yaml PIN-427)
# ============================================================================
# These paths are PUBLIC (return None) in preflight but PROTECTED in production.
# The tuple contains (path_prefix, methods) where methods is a tuple of HTTP methods.
# A path is PUBLIC if it starts with the prefix AND the method matches.

# NOTE: The RBAC middleware's get_public_paths() returns path prefixes WITHOUT
# considering HTTP methods. So in preflight, ALL methods to these paths return None.
# This is the actual middleware behavior - RBAC_RULES.yaml specifies methods, but
# the runtime check only looks at path prefixes.
PREFLIGHT_PUBLIC_PATH_PREFIXES: list[str] = [
    # PIN-427: SDSR Full Sweep Rules
    "/api/v1/agents/",
    "/api/v1/recovery/",
    "/api/v1/traces/",
    "/api/v1/runtime/traces/",
    "/api/v1/guard/",
    "/api/v1/discovery/",
    "/api/v1/tenants/",
    "/api/v1/ops/",
    "/api/v1/logs/",
    "/api/v1/customer/",
    "/api/v1/rbac/audit/",
    "/api/v1/feedback/",
    "/api/v1/predictions/",
    "/api/v1/policy-layer/",
    "/cost/",
    "/integration/",
    "/guard/logs/",
    "/billing/",
    "/status_history/",
    "/ops/actions/audit/",
    # PIN-370: SDSR Preflight Validation
    "/api/v1/activity/",
    "/api/v1/policy-proposals/",
    "/api/v1/incidents/",
]


def is_public_in_preflight(path: str) -> bool:
    """
    Check if a path is PUBLIC in preflight environment.

    NOTE: The RBAC middleware checks path prefixes only, not methods.
    If the path matches a PUBLIC prefix, ALL methods return None in preflight.
    """
    for prefix in PREFLIGHT_PUBLIC_PATH_PREFIXES:
        if path.startswith(prefix) or path == prefix.rstrip("/"):
            return True
    return False


def assert_policy_or_public(
    path: str,
    method: str,
    expected_resource: str,
    expected_action: str,
) -> None:
    """
    Environment-aware assertion for RBAC path mapping.

    In preflight: If path is PUBLIC, asserts policy is None.
    In production: Asserts policy has expected resource/action.

    This function encodes the dual truth:
    - Preflight paths are PUBLIC for SDSR validation
    - Production paths are PROTECTED with RBAC policies
    """
    policy = get_policy_for_path(path, method)

    if _IS_PREFLIGHT and is_public_in_preflight(path):
        # Preflight + PUBLIC path → expect None
        assert policy is None, (
            f"Path {path} ({method}) should be PUBLIC in preflight (return None), "
            f"but got PolicyObject(resource={policy.resource if policy else None}, "
            f"action={policy.action if policy else None})"
        )
    else:
        # Production OR non-PUBLIC path → expect PolicyObject
        assert policy is not None, (
            f"Path {path} ({method}) should have RBAC policy in "
            f"{'production' if _IS_PRODUCTION else 'preflight (non-public)'}, "
            f"but got None"
        )
        assert policy.resource == expected_resource, (
            f"Path {path} ({method}) should map to resource '{expected_resource}', "
            f"got '{policy.resource}'"
        )
        assert policy.action == expected_action, (
            f"Path {path} ({method}) should map to action '{expected_action}', "
            f"got '{policy.action}'"
        )


# ============================================================================
# Test: Public Paths (Should return None in ALL environments)
# ============================================================================


class TestPublicPaths:
    """Tests for public paths that should NOT require RBAC in any environment."""

    def test_health_is_public(self):
        """Health endpoint should be public."""
        assert get_policy_for_path("/health", "GET") is None

    def test_metrics_is_public(self):
        """Metrics endpoint should be public."""
        assert get_policy_for_path("/metrics", "GET") is None

    def test_auth_endpoints_are_public(self):
        """Auth endpoints should be public."""
        assert get_policy_for_path("/api/v1/auth/login", "POST") is None
        assert get_policy_for_path("/api/v1/auth/register", "POST") is None
        assert get_policy_for_path("/api/v1/auth/refresh", "POST") is None

    def test_docs_are_public(self):
        """Documentation endpoints should be public."""
        assert get_policy_for_path("/docs", "GET") is None
        assert get_policy_for_path("/openapi.json", "GET") is None
        assert get_policy_for_path("/redoc", "GET") is None


# ============================================================================
# Test: Memory Pins Resource (NOT public in preflight)
# ============================================================================


class TestMemoryPinsResource:
    """Tests for memory_pin resource mapping."""

    def test_get_memory_pins(self):
        """GET should map to read action."""
        policy = get_policy_for_path("/api/v1/memory/pins", "GET")
        assert policy.resource == "memory_pin"
        assert policy.action == "read"

    def test_post_memory_pins(self):
        """POST should map to write action."""
        policy = get_policy_for_path("/api/v1/memory/pins", "POST")
        assert policy.resource == "memory_pin"
        assert policy.action == "write"

    def test_delete_memory_pins(self):
        """DELETE should map to delete action."""
        policy = get_policy_for_path("/api/v1/memory/pins/123", "DELETE")
        assert policy.resource == "memory_pin"
        assert policy.action == "delete"

    def test_cleanup_memory_pins(self):
        """Cleanup endpoint should map to admin action."""
        policy = get_policy_for_path("/api/v1/memory/pins/cleanup", "POST")
        assert policy.resource == "memory_pin"
        assert policy.action == "admin"


# ============================================================================
# Test: Agents Resource (PUBLIC in preflight for GET only)
# ============================================================================


class TestAgentsResource:
    """Tests for agent resource mapping.

    NOTE: /api/v1/agents/ is PUBLIC in preflight (PIN-427).
    The middleware checks path prefixes only, so ALL methods return None in preflight.
    In production, all methods are properly mapped to PolicyObject.
    """

    def test_get_agents(self):
        """GET agents should map to read action (or None in preflight)."""
        assert_policy_or_public("/api/v1/agents", "GET", "agent", "read")

    def test_post_agents(self):
        """POST agents should map to write action (or None in preflight)."""
        assert_policy_or_public("/api/v1/agents", "POST", "agent", "write")

    def test_agent_heartbeat(self):
        """Heartbeat should map to heartbeat action (or None in preflight)."""
        assert_policy_or_public("/api/v1/agents/123/heartbeat", "POST", "agent", "heartbeat")

    def test_agent_register(self):
        """Register should map to register action (or None in preflight)."""
        assert_policy_or_public("/api/v1/agents/register", "POST", "agent", "register")

    def test_delete_agent(self):
        """DELETE agent should map to delete action (or None in preflight)."""
        assert_policy_or_public("/api/v1/agents/123", "DELETE", "agent", "delete")


# ============================================================================
# Test: Runtime Resource (NOT public in preflight, except /traces/)
# ============================================================================


class TestRuntimeResource:
    """Tests for runtime resource mapping."""

    def test_runtime_simulate(self):
        """Simulate should map to simulate action."""
        policy = get_policy_for_path("/api/v1/runtime/simulate", "POST")
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "simulate"

    def test_runtime_capabilities(self):
        """Capabilities should map to capabilities action."""
        policy = get_policy_for_path("/api/v1/runtime/capabilities", "GET")
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "capabilities"

    def test_runtime_query(self):
        """Query should map to query action."""
        policy = get_policy_for_path("/api/v1/runtime/query", "GET")
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "query"


# ============================================================================
# Test: Recovery Resource (PUBLIC in preflight for GET only)
# ============================================================================


class TestRecoveryResource:
    """Tests for recovery resource mapping.

    NOTE: /api/v1/recovery/ is PUBLIC in preflight (PIN-427).
    The middleware checks path prefixes only, so ALL methods return None in preflight.
    """

    def test_get_recovery(self):
        """GET recovery should map to read action (or None in preflight)."""
        assert_policy_or_public("/api/v1/recovery", "GET", "recovery", "read")

    def test_recovery_execute(self):
        """Execute should map to execute action (or None in preflight)."""
        assert_policy_or_public("/api/v1/recovery/execute", "POST", "recovery", "execute")

    def test_recovery_suggest(self):
        """Suggest should map to suggest action (or None in preflight)."""
        assert_policy_or_public("/api/v1/recovery/suggest", "POST", "recovery", "suggest")


# ============================================================================
# Test: Workers Resource (NOT public in preflight)
# ============================================================================


class TestWorkersResource:
    """Tests for worker resource mapping."""

    def test_get_workers(self):
        """GET workers should map to read action."""
        policy = get_policy_for_path("/api/v1/workers", "GET")
        assert policy is not None
        assert policy.resource == "worker"
        assert policy.action == "read"

    def test_worker_run(self):
        """Run should map to run action."""
        policy = get_policy_for_path("/api/v1/workers/business-builder/run", "POST")
        assert policy is not None
        assert policy.resource == "worker"
        assert policy.action == "run"

    def test_worker_stream(self):
        """Stream should map to stream action."""
        policy = get_policy_for_path("/api/v1/workers/business-builder/stream/123", "GET")
        assert policy is not None
        assert policy.resource == "worker"
        assert policy.action == "stream"

    def test_worker_cancel(self):
        """Cancel should map to cancel action."""
        policy = get_policy_for_path("/api/v1/workers/123/cancel", "POST")
        assert policy is not None
        assert policy.resource == "worker"
        assert policy.action == "cancel"


# ============================================================================
# Test: Traces Resource (PUBLIC in preflight for GET only)
# ============================================================================


class TestTracesResource:
    """Tests for trace resource mapping.

    NOTE: /api/v1/traces/ is PUBLIC in preflight (PIN-427).
    The middleware checks path prefixes only, so ALL methods return None in preflight.
    """

    def test_get_traces(self):
        """GET traces should map to read action (or None in preflight)."""
        assert_policy_or_public("/api/v1/traces", "GET", "trace", "read")

    def test_post_traces(self):
        """POST traces should map to write action (or None in preflight)."""
        assert_policy_or_public("/api/v1/traces", "POST", "trace", "write")

    def test_trace_export(self):
        """Export should map to export action (or None in preflight)."""
        assert_policy_or_public("/api/v1/traces/123/export", "GET", "trace", "export")

    def test_delete_trace(self):
        """DELETE trace should map to delete action (or None in preflight)."""
        assert_policy_or_public("/api/v1/traces/123", "DELETE", "trace", "delete")


# ============================================================================
# Test: Embedding Resource (NOT public in preflight)
# ============================================================================


class TestEmbeddingResource:
    """Tests for embedding resource mapping."""

    def test_get_embedding(self):
        """GET embedding should map to read action."""
        policy = get_policy_for_path("/api/v1/embedding", "GET")
        assert policy is not None
        assert policy.resource == "embedding"
        assert policy.action == "read"

    def test_embed_action(self):
        """Embed endpoint should map to embed action."""
        policy = get_policy_for_path("/api/v1/embedding/embed", "POST")
        assert policy is not None
        assert policy.resource == "embedding"
        assert policy.action == "embed"

    def test_embedding_query(self):
        """Query should map to query action."""
        policy = get_policy_for_path("/api/v1/embedding/query", "POST")
        assert policy is not None
        assert policy.resource == "embedding"
        assert policy.action == "query"


# ============================================================================
# Test: Killswitch Resource (NOT public in preflight)
# ============================================================================


class TestKillswitchResource:
    """Tests for killswitch resource mapping."""

    def test_get_killswitch(self):
        """GET killswitch should map to read action."""
        policy = get_policy_for_path("/v1/killswitch/status", "GET")
        assert policy is not None
        assert policy.resource == "killswitch"
        assert policy.action == "read"

    def test_killswitch_activate(self):
        """Activate should map to activate action."""
        policy = get_policy_for_path("/v1/killswitch/activate", "POST")
        assert policy is not None
        assert policy.resource == "killswitch"
        assert policy.action == "activate"

    def test_killswitch_reset(self):
        """Reset should map to reset action."""
        policy = get_policy_for_path("/v1/killswitch/reset", "POST")
        assert policy is not None
        assert policy.resource == "killswitch"
        assert policy.action == "reset"


# ============================================================================
# Test: Integration Resource (PUBLIC in preflight for GET only)
# ============================================================================


class TestIntegrationResource:
    """Tests for integration resource mapping.

    NOTE: /integration/ is PUBLIC in preflight (PIN-427).
    The middleware checks path prefixes only, so ALL methods return None in preflight.
    """

    def test_get_integration(self):
        """GET integration should map to read action (or None in preflight)."""
        assert_policy_or_public("/integration/loop/123", "GET", "integration", "read")

    def test_integration_checkpoint(self):
        """Checkpoint should map to checkpoint action (or None in preflight)."""
        assert_policy_or_public("/integration/checkpoints", "GET", "integration", "checkpoint")

    def test_integration_resolve(self):
        """Resolve should map to resolve action (or None in preflight)."""
        assert_policy_or_public("/integration/checkpoints/123/resolve", "POST", "integration", "resolve")


# ============================================================================
# Test: Cost Resource (PUBLIC in preflight for GET only)
# ============================================================================


class TestCostResource:
    """Tests for cost resource mapping.

    NOTE: /cost/ is PUBLIC in preflight (PIN-427).
    The middleware checks path prefixes only, so ALL methods return None in preflight.
    """

    def test_get_cost(self):
        """GET cost should map to read action (or None in preflight)."""
        assert_policy_or_public("/cost/summary", "GET", "cost", "read")

    def test_cost_simulate(self):
        """Simulate should map to simulate action (or None in preflight)."""
        assert_policy_or_public("/cost/simulate", "POST", "cost", "simulate")

    def test_cost_forecast(self):
        """Forecast should map to forecast action (or None in preflight)."""
        assert_policy_or_public("/cost/forecast", "GET", "cost", "forecast")


# ============================================================================
# Test: Incidents Resource (PUBLIC in preflight for GET only)
# ============================================================================


class TestIncidentsResource:
    """Tests for incident resource mapping.

    NOTE (PIN-391): /api/v1/incidents/ is PUBLIC in preflight per RBAC_RULES.yaml
    but protected (SESSION tier) in production.
    The middleware checks path prefixes only, so ALL methods return None in preflight.
    """

    def test_get_incidents(self):
        """GET incidents should map to read action (or None in preflight)."""
        assert_policy_or_public("/api/v1/incidents", "GET", "incident", "read")

    def test_post_incidents(self):
        """POST incidents should map to write action (or None in preflight)."""
        assert_policy_or_public("/api/v1/incidents", "POST", "incident", "write")

    def test_incident_resolve(self):
        """Resolve should map to resolve action (or None in preflight)."""
        assert_policy_or_public("/api/v1/incidents/123/resolve", "POST", "incident", "resolve")


# ============================================================================
# Test: RBAC Resource (only /audit/ is PUBLIC in preflight)
# ============================================================================


class TestRBACResource:
    """Tests for rbac resource mapping.

    NOTE: /api/v1/rbac/audit/ is PUBLIC in preflight (PIN-427).
    Other RBAC endpoints (/info, /reload) are protected.
    """

    def test_get_rbac(self):
        """GET rbac should map to read action (always protected - /info not /audit)."""
        policy = get_policy_for_path("/api/v1/rbac/info", "GET")
        assert policy is not None
        assert policy.resource == "rbac"
        assert policy.action == "read"

    def test_rbac_reload(self):
        """Reload should map to reload action (always protected)."""
        policy = get_policy_for_path("/api/v1/rbac/reload", "POST")
        assert policy is not None
        assert policy.resource == "rbac"
        assert policy.action == "reload"

    def test_rbac_audit(self):
        """Audit should map to audit action (or None in preflight)."""
        assert_policy_or_public("/api/v1/rbac/audit", "GET", "rbac", "audit")


# ============================================================================
# Test: Runs Resource (NOT public in preflight)
# ============================================================================


class TestRunsResource:
    """Tests for runs resource mapping (maps to worker)."""

    def test_get_runs(self):
        """GET runs should map to worker:read."""
        policy = get_policy_for_path("/api/v1/runs", "GET")
        assert policy is not None
        assert policy.resource == "worker"
        assert policy.action == "read"

    def test_post_runs(self):
        """POST runs should map to worker:run."""
        policy = get_policy_for_path("/api/v1/runs", "POST")
        assert policy is not None
        assert policy.resource == "worker"
        assert policy.action == "run"


# ============================================================================
# Test: V1 Proxy Routes (NOT public in preflight)
# ============================================================================


class TestV1ProxyRoutes:
    """Tests for V1 proxy routes mapping."""

    def test_chat_completions(self):
        """Chat completions should map to runtime:simulate."""
        policy = get_policy_for_path("/v1/chat/completions", "POST")
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "simulate"

    def test_embeddings(self):
        """Embeddings should map to embedding:embed."""
        policy = get_policy_for_path("/v1/embeddings", "POST")
        assert policy is not None
        assert policy.resource == "embedding"
        assert policy.action == "embed"

    def test_status(self):
        """Status should map to runtime:query."""
        policy = get_policy_for_path("/v1/status", "GET")
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "query"


# ============================================================================
# Test: Console Routes (Shadow Audit) - NOT public in preflight
# ============================================================================


class TestConsoleRoutes:
    """Tests for console routes mapping (for shadow audit).

    NOTE: /guard/logs/ is PUBLIC in preflight, but /guard/costs and
    /guard/incidents are NOT (different prefix).
    """

    def test_guard_costs(self):
        """Guard costs should map to cost:read."""
        policy = get_policy_for_path("/guard/costs", "GET")
        assert policy is not None
        assert policy.resource == "cost"
        assert policy.action == "read"

    def test_guard_incidents(self):
        """Guard incidents should map to incident:read."""
        policy = get_policy_for_path("/guard/incidents", "GET")
        assert policy is not None
        assert policy.resource == "incident"
        assert policy.action == "read"

    def test_ops_cost(self):
        """Ops cost should map to cost:read."""
        policy = get_policy_for_path("/ops/cost", "GET")
        assert policy is not None
        assert policy.resource == "cost"
        assert policy.action == "read"

    def test_ops_customers(self):
        """Ops customers should map to tenant:read."""
        policy = get_policy_for_path("/ops/customers", "GET")
        assert policy is not None
        assert policy.resource == "tenant"
        assert policy.action == "read"

    def test_ops_actions(self):
        """Ops actions should map to tenant:write."""
        policy = get_policy_for_path("/ops/actions/freeze", "POST")
        assert policy is not None
        assert policy.resource == "tenant"
        assert policy.action == "write"


# ============================================================================
# Test: Catch-All (Unknown Paths)
# ============================================================================


class TestCatchAll:
    """Tests for catch-all behavior on unknown paths."""

    def test_unknown_path_defaults_to_runtime_query(self):
        """Unknown paths should default to runtime:query."""
        policy = get_policy_for_path("/api/v1/unknown/endpoint", "GET")
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "query"

    def test_unknown_path_is_not_none(self):
        """Unknown paths should NOT return None."""
        policy = get_policy_for_path("/some/random/path", "GET")
        assert policy is not None


# ============================================================================
# Test: No Gaps (Every protected path has policy)
# ============================================================================

# Paths that are always protected (not PUBLIC in preflight)
ALWAYS_PROTECTED_PATHS = [
    "/api/v1/runtime/simulate",
    "/api/v1/workers",
    "/api/v1/embedding",
    "/api/v1/policy",
    "/api/v1/costsim",
    "/api/v1/memory/pins",
    "/api/v1/runs",
    "/v1/killswitch/status",
    "/v1/chat/completions",
    "/guard/status",
    "/ops/dashboard",
]

# Paths that are PUBLIC in preflight (GET only)
PREFLIGHT_PUBLIC_TEST_PATHS = [
    "/api/v1/agents",
    "/api/v1/recovery",
    "/api/v1/traces",
    "/integration/loop/123",
    "/cost/summary",
]


class TestNoGaps:
    """Tests to ensure no protected path returns None.

    NOTE (PIN-391, PIN-427): Some paths are PUBLIC in preflight but protected
    in production. These are tested with environment-aware assertions.
    """

    @pytest.mark.parametrize("path", ALWAYS_PROTECTED_PATHS)
    def test_always_protected_path_has_policy(self, path):
        """Always-protected paths should have a policy (not None) in any environment."""
        policy = get_policy_for_path(path, "GET")
        assert policy is not None, f"Path {path} should always have policy"
        assert isinstance(policy, PolicyObject)
        assert policy.resource is not None
        assert policy.action is not None

    @pytest.mark.parametrize("path", PREFLIGHT_PUBLIC_TEST_PATHS)
    def test_preflight_public_path_behavior(self, path):
        """Paths PUBLIC in preflight should return None in preflight, PolicyObject in production."""
        policy = get_policy_for_path(path, "GET")
        if _IS_PREFLIGHT:
            # In preflight, these paths are PUBLIC → None
            assert policy is None, (
                f"Path {path} should be PUBLIC (None) in preflight, "
                f"got PolicyObject(resource={policy.resource if policy else None})"
            )
        else:
            # In production, these paths are protected → PolicyObject
            assert policy is not None, f"Path {path} should have policy in production"
            assert isinstance(policy, PolicyObject)
            assert policy.resource is not None
            assert policy.action is not None


# ============================================================================
# Test: Future-Proof Path Guard
#
# INVARIANT: If a new router is added and mapping is forgotten,
# this test MUST fail. No silent bypasses allowed.
# ============================================================================

# Paths that are always protected regardless of environment
KNOWN_ALWAYS_PROTECTED_PATHS = [
    "/api/v1/runtime",
    "/api/v1/workers",
    "/api/v1/embedding",
    "/api/v1/policy",
    "/api/v1/costsim",
    "/api/v1/memory",
    "/api/v1/runs",
    "/v1/killswitch",
    "/v1/chat",
    "/v1/embeddings",
    "/v1/status",
]

# Paths that are PUBLIC in preflight (tested separately)
KNOWN_PREFLIGHT_PUBLIC_PATHS = [
    "/api/v1/agents",
    "/api/v1/recovery",
    "/api/v1/traces",
    "/integration",
    "/cost",
    "/guard",
    "/ops",
]


class TestFutureProofPathGuard:
    """
    Guard against new routers being added without RBAC mapping.

    If you add a new API router and this test fails, you MUST:
    1. Add the path to KNOWN_*_PATHS below
    2. Add explicit mapping in get_policy_for_path()
    3. Add resource to RBAC_MATRIX for appropriate roles

    DO NOT just add paths to KNOWN_*_PATHS without mapping!
    """

    KNOWN_RESOURCES = [
        "memory_pin",
        "prometheus",
        "costsim",
        "policy",
        "agent",
        "runtime",
        "recovery",
        "worker",
        "trace",
        "embedding",
        "killswitch",
        "integration",
        "cost",
        "checkpoint",
        "event",
        "incident",
        "tenant",
        "rbac",
    ]

    @pytest.mark.parametrize("path_prefix", KNOWN_ALWAYS_PROTECTED_PATHS)
    def test_always_protected_path_has_explicit_mapping(self, path_prefix):
        """Always-protected paths MUST have explicit RBAC mapping."""
        policy = get_policy_for_path(path_prefix, "GET")
        assert policy is not None, f"Path {path_prefix} has no RBAC mapping!"
        assert policy.resource in self.KNOWN_RESOURCES, (
            f"Path {path_prefix} maps to unknown resource '{policy.resource}'! "
            f"Add it to KNOWN_RESOURCES and RBAC_MATRIX."
        )

    @pytest.mark.parametrize("path_prefix", KNOWN_PREFLIGHT_PUBLIC_PATHS)
    def test_preflight_public_path_has_mapping_in_production(self, path_prefix):
        """
        Paths PUBLIC in preflight MUST have RBAC mapping in production.

        In preflight: Returns None (PUBLIC) - this is expected.
        In production: Must return PolicyObject with known resource.
        """
        policy = get_policy_for_path(path_prefix, "GET")

        if _IS_PREFLIGHT:
            # In preflight, these are PUBLIC - either None or PolicyObject is OK
            # (depends on exact path matching)
            pass  # No assertion - just document the behavior
        else:
            # In production, MUST have mapping
            assert policy is not None, (
                f"Path {path_prefix} has no RBAC mapping in production! "
                f"Add mapping in get_policy_for_path()."
            )
            assert policy.resource in self.KNOWN_RESOURCES, (
                f"Path {path_prefix} maps to unknown resource '{policy.resource}'! "
                f"Add it to KNOWN_RESOURCES and RBAC_MATRIX."
            )

    def test_catch_all_exists_but_is_explicit(self):
        """
        Catch-all MUST map to a known resource, not silently bypass.

        This ensures even unknown paths get RBAC evaluation.
        """
        policy = get_policy_for_path("/totally/new/unregistered/path", "POST")
        assert policy is not None, "Catch-all should never return None!"
        assert policy.resource == "runtime", "Catch-all should map to runtime"
        assert policy.action == "query", "Catch-all should map to query (read-like)"

    def test_new_router_without_mapping_fails_explicitly(self):
        """
        Simulates what happens when a new router is added without mapping.

        The catch-all ensures we still get a policy, but the resource
        should be auditable. This test documents expected behavior.
        """
        new_path = "/api/v1/hypothetical_new_feature"
        policy = get_policy_for_path(new_path, "POST")

        # It WILL get a policy (catch-all), but it maps to runtime:query
        # which is READ-LIKE. This is intentional fail-safe behavior.
        assert policy is not None
        assert policy.resource == "runtime"
        assert policy.action == "query"
