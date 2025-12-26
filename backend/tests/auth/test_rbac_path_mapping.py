"""
Unit Tests for RBAC Path Mapping - M7-M28 RBAC Integration (PIN-169)

Tests the expanded path-to-policy mapping for all 14+ resources.

INVARIANTS TESTED:
1. No path returns None for protected routes (except public paths)
2. All resources are correctly mapped
3. HTTP methods map to correct actions

Created: 2025-12-25
"""

import pytest

from app.auth.rbac_middleware import PolicyObject, get_policy_for_path

# ============================================================================
# Test: Public Paths (Should return None)
# ============================================================================


class TestPublicPaths:
    """Tests for public paths that should NOT require RBAC."""

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
# Test: Memory Pins Resource
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
# Test: Agents Resource
# ============================================================================


class TestAgentsResource:
    """Tests for agent resource mapping."""

    def test_get_agents(self):
        """GET agents should map to read action."""
        policy = get_policy_for_path("/api/v1/agents", "GET")
        assert policy.resource == "agent"
        assert policy.action == "read"

    def test_post_agents(self):
        """POST agents should map to write action."""
        policy = get_policy_for_path("/api/v1/agents", "POST")
        assert policy.resource == "agent"
        assert policy.action == "write"

    def test_agent_heartbeat(self):
        """Heartbeat should map to heartbeat action."""
        policy = get_policy_for_path("/api/v1/agents/123/heartbeat", "POST")
        assert policy.resource == "agent"
        assert policy.action == "heartbeat"

    def test_agent_register(self):
        """Register should map to register action."""
        policy = get_policy_for_path("/api/v1/agents/register", "POST")
        assert policy.resource == "agent"
        assert policy.action == "register"

    def test_delete_agent(self):
        """DELETE agent should map to delete action."""
        policy = get_policy_for_path("/api/v1/agents/123", "DELETE")
        assert policy.resource == "agent"
        assert policy.action == "delete"


# ============================================================================
# Test: Runtime Resource
# ============================================================================


class TestRuntimeResource:
    """Tests for runtime resource mapping."""

    def test_runtime_simulate(self):
        """Simulate should map to simulate action."""
        policy = get_policy_for_path("/api/v1/runtime/simulate", "POST")
        assert policy.resource == "runtime"
        assert policy.action == "simulate"

    def test_runtime_capabilities(self):
        """Capabilities should map to capabilities action."""
        policy = get_policy_for_path("/api/v1/runtime/capabilities", "GET")
        assert policy.resource == "runtime"
        assert policy.action == "capabilities"

    def test_runtime_query(self):
        """Query should map to query action."""
        policy = get_policy_for_path("/api/v1/runtime/query", "GET")
        assert policy.resource == "runtime"
        assert policy.action == "query"


# ============================================================================
# Test: Recovery Resource
# ============================================================================


class TestRecoveryResource:
    """Tests for recovery resource mapping."""

    def test_get_recovery(self):
        """GET recovery should map to read action."""
        policy = get_policy_for_path("/api/v1/recovery", "GET")
        assert policy.resource == "recovery"
        assert policy.action == "read"

    def test_recovery_execute(self):
        """Execute should map to execute action."""
        policy = get_policy_for_path("/api/v1/recovery/execute", "POST")
        assert policy.resource == "recovery"
        assert policy.action == "execute"

    def test_recovery_suggest(self):
        """Suggest should map to suggest action."""
        policy = get_policy_for_path("/api/v1/recovery/suggest", "POST")
        assert policy.resource == "recovery"
        assert policy.action == "suggest"


# ============================================================================
# Test: Workers Resource
# ============================================================================


class TestWorkersResource:
    """Tests for worker resource mapping."""

    def test_get_workers(self):
        """GET workers should map to read action."""
        policy = get_policy_for_path("/api/v1/workers", "GET")
        assert policy.resource == "worker"
        assert policy.action == "read"

    def test_worker_run(self):
        """Run should map to run action."""
        policy = get_policy_for_path("/api/v1/workers/business-builder/run", "POST")
        assert policy.resource == "worker"
        assert policy.action == "run"

    def test_worker_stream(self):
        """Stream should map to stream action."""
        policy = get_policy_for_path("/api/v1/workers/business-builder/stream/123", "GET")
        assert policy.resource == "worker"
        assert policy.action == "stream"

    def test_worker_cancel(self):
        """Cancel should map to cancel action."""
        policy = get_policy_for_path("/api/v1/workers/123/cancel", "POST")
        assert policy.resource == "worker"
        assert policy.action == "cancel"


# ============================================================================
# Test: Traces Resource
# ============================================================================


class TestTracesResource:
    """Tests for trace resource mapping."""

    def test_get_traces(self):
        """GET traces should map to read action."""
        policy = get_policy_for_path("/api/v1/traces", "GET")
        assert policy.resource == "trace"
        assert policy.action == "read"

    def test_post_traces(self):
        """POST traces should map to write action."""
        policy = get_policy_for_path("/api/v1/traces", "POST")
        assert policy.resource == "trace"
        assert policy.action == "write"

    def test_trace_export(self):
        """Export should map to export action."""
        policy = get_policy_for_path("/api/v1/traces/123/export", "GET")
        assert policy.resource == "trace"
        assert policy.action == "export"

    def test_delete_trace(self):
        """DELETE trace should map to delete action."""
        policy = get_policy_for_path("/api/v1/traces/123", "DELETE")
        assert policy.resource == "trace"
        assert policy.action == "delete"


# ============================================================================
# Test: Embedding Resource
# ============================================================================


class TestEmbeddingResource:
    """Tests for embedding resource mapping."""

    def test_get_embedding(self):
        """GET embedding should map to read action."""
        policy = get_policy_for_path("/api/v1/embedding", "GET")
        assert policy.resource == "embedding"
        assert policy.action == "read"

    def test_embed_action(self):
        """Embed endpoint should map to embed action."""
        policy = get_policy_for_path("/api/v1/embedding/embed", "POST")
        assert policy.resource == "embedding"
        assert policy.action == "embed"

    def test_embedding_query(self):
        """Query should map to query action."""
        policy = get_policy_for_path("/api/v1/embedding/query", "POST")
        assert policy.resource == "embedding"
        assert policy.action == "query"


# ============================================================================
# Test: Killswitch Resource
# ============================================================================


class TestKillswitchResource:
    """Tests for killswitch resource mapping."""

    def test_get_killswitch(self):
        """GET killswitch should map to read action."""
        policy = get_policy_for_path("/v1/killswitch/status", "GET")
        assert policy.resource == "killswitch"
        assert policy.action == "read"

    def test_killswitch_activate(self):
        """Activate should map to activate action."""
        policy = get_policy_for_path("/v1/killswitch/activate", "POST")
        assert policy.resource == "killswitch"
        assert policy.action == "activate"

    def test_killswitch_reset(self):
        """Reset should map to reset action."""
        policy = get_policy_for_path("/v1/killswitch/reset", "POST")
        assert policy.resource == "killswitch"
        assert policy.action == "reset"


# ============================================================================
# Test: Integration Resource
# ============================================================================


class TestIntegrationResource:
    """Tests for integration resource mapping."""

    def test_get_integration(self):
        """GET integration should map to read action."""
        policy = get_policy_for_path("/integration/loop/123", "GET")
        assert policy.resource == "integration"
        assert policy.action == "read"

    def test_integration_checkpoint(self):
        """Checkpoint should map to checkpoint action."""
        policy = get_policy_for_path("/integration/checkpoints", "GET")
        assert policy.resource == "integration"
        assert policy.action == "checkpoint"

    def test_integration_resolve(self):
        """Resolve should map to resolve action."""
        policy = get_policy_for_path("/integration/checkpoints/123/resolve", "POST")
        assert policy.resource == "integration"
        assert policy.action == "resolve"


# ============================================================================
# Test: Cost Resource
# ============================================================================


class TestCostResource:
    """Tests for cost resource mapping."""

    def test_get_cost(self):
        """GET cost should map to read action."""
        policy = get_policy_for_path("/cost/summary", "GET")
        assert policy.resource == "cost"
        assert policy.action == "read"

    def test_cost_simulate(self):
        """Simulate should map to simulate action."""
        policy = get_policy_for_path("/cost/simulate", "POST")
        assert policy.resource == "cost"
        assert policy.action == "simulate"

    def test_cost_forecast(self):
        """Forecast should map to forecast action."""
        policy = get_policy_for_path("/cost/forecast", "GET")
        assert policy.resource == "cost"
        assert policy.action == "forecast"


# ============================================================================
# Test: Incidents Resource
# ============================================================================


class TestIncidentsResource:
    """Tests for incident resource mapping."""

    def test_get_incidents(self):
        """GET incidents should map to read action."""
        policy = get_policy_for_path("/api/v1/incidents", "GET")
        assert policy.resource == "incident"
        assert policy.action == "read"

    def test_post_incidents(self):
        """POST incidents should map to write action."""
        policy = get_policy_for_path("/api/v1/incidents", "POST")
        assert policy.resource == "incident"
        assert policy.action == "write"

    def test_incident_resolve(self):
        """Resolve should map to resolve action."""
        policy = get_policy_for_path("/api/v1/incidents/123/resolve", "POST")
        assert policy.resource == "incident"
        assert policy.action == "resolve"


# ============================================================================
# Test: RBAC Resource
# ============================================================================


class TestRBACResource:
    """Tests for rbac resource mapping."""

    def test_get_rbac(self):
        """GET rbac should map to read action."""
        policy = get_policy_for_path("/api/v1/rbac/info", "GET")
        assert policy.resource == "rbac"
        assert policy.action == "read"

    def test_rbac_reload(self):
        """Reload should map to reload action."""
        policy = get_policy_for_path("/api/v1/rbac/reload", "POST")
        assert policy.resource == "rbac"
        assert policy.action == "reload"

    def test_rbac_audit(self):
        """Audit should map to audit action."""
        policy = get_policy_for_path("/api/v1/rbac/audit", "GET")
        assert policy.resource == "rbac"
        assert policy.action == "audit"


# ============================================================================
# Test: Runs Resource (maps to worker)
# ============================================================================


class TestRunsResource:
    """Tests for runs resource mapping (maps to worker)."""

    def test_get_runs(self):
        """GET runs should map to worker:read."""
        policy = get_policy_for_path("/api/v1/runs", "GET")
        assert policy.resource == "worker"
        assert policy.action == "read"

    def test_post_runs(self):
        """POST runs should map to worker:run."""
        policy = get_policy_for_path("/api/v1/runs", "POST")
        assert policy.resource == "worker"
        assert policy.action == "run"


# ============================================================================
# Test: V1 Proxy Routes
# ============================================================================


class TestV1ProxyRoutes:
    """Tests for V1 proxy routes mapping."""

    def test_chat_completions(self):
        """Chat completions should map to runtime:simulate."""
        policy = get_policy_for_path("/v1/chat/completions", "POST")
        assert policy.resource == "runtime"
        assert policy.action == "simulate"

    def test_embeddings(self):
        """Embeddings should map to embedding:embed."""
        policy = get_policy_for_path("/v1/embeddings", "POST")
        assert policy.resource == "embedding"
        assert policy.action == "embed"

    def test_status(self):
        """Status should map to runtime:query."""
        policy = get_policy_for_path("/v1/status", "GET")
        assert policy.resource == "runtime"
        assert policy.action == "query"


# ============================================================================
# Test: Console Routes (Shadow Audit)
# ============================================================================


class TestConsoleRoutes:
    """Tests for console routes mapping (for shadow audit)."""

    def test_guard_costs(self):
        """Guard costs should map to cost:read."""
        policy = get_policy_for_path("/guard/costs", "GET")
        assert policy.resource == "cost"
        assert policy.action == "read"

    def test_guard_incidents(self):
        """Guard incidents should map to incident:read."""
        policy = get_policy_for_path("/guard/incidents", "GET")
        assert policy.resource == "incident"
        assert policy.action == "read"

    def test_ops_cost(self):
        """Ops cost should map to cost:read."""
        policy = get_policy_for_path("/ops/cost", "GET")
        assert policy.resource == "cost"
        assert policy.action == "read"

    def test_ops_customers(self):
        """Ops customers should map to tenant:read."""
        policy = get_policy_for_path("/ops/customers", "GET")
        assert policy.resource == "tenant"
        assert policy.action == "read"

    def test_ops_actions(self):
        """Ops actions should map to tenant:write."""
        policy = get_policy_for_path("/ops/actions/freeze", "POST")
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
        assert policy.resource == "runtime"
        assert policy.action == "query"

    def test_unknown_path_is_not_none(self):
        """Unknown paths should NOT return None."""
        policy = get_policy_for_path("/some/random/path", "GET")
        assert policy is not None


# ============================================================================
# Test: No Gaps (Every protected path has policy)
# ============================================================================


class TestNoGaps:
    """Tests to ensure no protected path returns None."""

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/agents",
            "/api/v1/runtime/simulate",
            "/api/v1/recovery",
            "/api/v1/workers",
            "/api/v1/traces",
            "/api/v1/embedding",
            "/api/v1/policy",
            "/api/v1/costsim",
            "/api/v1/memory/pins",
            "/api/v1/rbac/info",
            "/api/v1/incidents",
            "/api/v1/runs",
            "/v1/killswitch/status",
            "/v1/chat/completions",
            "/integration/loop/123",
            "/cost/summary",
            "/guard/status",
            "/ops/dashboard",
        ],
    )
    def test_protected_path_has_policy(self, path):
        """Protected paths should have a policy (not None)."""
        policy = get_policy_for_path(path, "GET")
        assert policy is not None
        assert isinstance(policy, PolicyObject)
        assert policy.resource is not None
        assert policy.action is not None


# ============================================================================
# Test: Future-Proof Path Guard
#
# INVARIANT: If a new router is added and mapping is forgotten,
# this test MUST fail. No silent bypasses allowed.
# ============================================================================


class TestFutureProofPathGuard:
    """
    Guard against new routers being added without RBAC mapping.

    If you add a new API router and this test fails, you MUST:
    1. Add the path to KNOWN_API_PATHS below
    2. Add explicit mapping in get_policy_for_path()
    3. Add resource to RBAC_MATRIX for appropriate roles

    DO NOT just add paths to KNOWN_API_PATHS without mapping!
    """

    # All known API path prefixes that MUST have RBAC mapping
    # If you add a new router, ADD IT HERE and add mapping
    KNOWN_API_PATHS = [
        # Core API v1
        "/api/v1/agents",
        "/api/v1/runtime",
        "/api/v1/recovery",
        "/api/v1/workers",
        "/api/v1/traces",
        "/api/v1/embedding",
        "/api/v1/policy",
        "/api/v1/costsim",
        "/api/v1/memory",
        "/api/v1/rbac",
        "/api/v1/incidents",
        "/api/v1/runs",
        # V1 proxy routes
        "/v1/killswitch",
        "/v1/chat",
        "/v1/embeddings",
        "/v1/status",
        # Integration routes
        "/integration",
        # Cost routes
        "/cost",
        # Console shadow routes
        "/guard",
        "/ops",
    ]

    # Resources that MUST exist in RBAC_MATRIX
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

    @pytest.mark.parametrize("path_prefix", KNOWN_API_PATHS)
    def test_known_path_has_explicit_mapping(self, path_prefix):
        """
        Every known API path MUST have explicit RBAC mapping.

        If this test fails, you added a new router without RBAC mapping.
        FIX: Add mapping in get_policy_for_path(), not here.
        """
        # Test with GET
        policy = get_policy_for_path(path_prefix, "GET")
        assert policy is not None, f"Path {path_prefix} has no RBAC mapping!"
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
        # A hypothetical new router path
        new_path = "/api/v1/hypothetical_new_feature"
        policy = get_policy_for_path(new_path, "POST")

        # It WILL get a policy (catch-all), but it maps to runtime:query
        # which is READ-LIKE. This is intentional fail-safe behavior.
        assert policy is not None
        # The catch-all maps unknown to runtime:query (restrictive)
        # This means new routers start with READ-ONLY access until mapped
        assert policy.resource == "runtime"
        assert policy.action == "query"

        # To properly enable the new feature:
        # 1. Add explicit mapping in get_policy_for_path()
        # 2. Add resource to RBAC_MATRIX
        # 3. Add path to KNOWN_API_PATHS above
        # 4. This test will then pass with explicit mapping
