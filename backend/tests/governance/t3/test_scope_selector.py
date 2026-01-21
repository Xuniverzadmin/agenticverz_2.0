# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-001 to GAP-004 (Scope selector enhancements)
"""
Tests for Scope Selector Enhancements (GAP-001 to GAP-004).

GAP-001: API key targeting
GAP-002: Human actor targeting
GAP-003: ALL_RUNS scope
GAP-004: Scope resolution snapshot
"""

import pytest
from datetime import datetime, timezone


class TestScopeTypeImports:
    """Test that all scope components are properly exported."""

    def test_scope_type_import(self):
        """ScopeType should be importable."""
        from app.models.policy_scope import ScopeType
        assert ScopeType.ALL_RUNS == "all_runs"
        assert ScopeType.AGENT == "agent"
        assert ScopeType.API_KEY == "api_key"
        assert ScopeType.HUMAN_ACTOR == "human_actor"

    def test_policy_scope_import(self):
        """PolicyScope should be importable."""
        from app.models.policy_scope import PolicyScope
        assert PolicyScope is not None

    def test_run_context_import(self):
        """RunContext should be importable."""
        from app.policy.scope_resolver import RunContext
        ctx = RunContext(tenant_id="tenant-1")
        assert ctx.tenant_id == "tenant-1"

    def test_scope_resolution_result_import(self):
        """ScopeResolutionResult should be importable."""
        from app.policy.scope_resolver import ScopeResolutionResult, RunContext
        ctx = RunContext(tenant_id="tenant-1")
        result = ScopeResolutionResult(
            matching_policy_ids=[],
            all_runs_policies=[],
            agent_policies=[],
            api_key_policies=[],
            human_actor_policies=[],
            context=ctx,
            scopes_evaluated=0,
            resolution_timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assert result is not None


class TestGAP001ApiKeyTargeting:
    """Test GAP-001: API key targeting."""

    def test_scope_type_api_key_exists(self):
        """API_KEY scope type should exist."""
        from app.models.policy_scope import ScopeType
        assert hasattr(ScopeType, "API_KEY")
        assert ScopeType.API_KEY.value == "api_key"

    def test_create_api_key_scope(self):
        """Should create scope with API key targeting."""
        from app.models.policy_scope import PolicyScope, ScopeType

        scope = PolicyScope.create_api_key_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            api_key_ids=["key-1", "key-2"],
        )

        assert scope.scope_type == ScopeType.API_KEY.value
        assert scope.api_key_ids == ["key-1", "key-2"]
        assert scope.agent_ids == []
        assert scope.human_actor_ids == []

    def test_api_key_scope_matches(self):
        """API key scope should match correct API keys."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_api_key_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            api_key_ids=["key-1", "key-2"],
        )

        assert scope.matches(api_key_id="key-1") is True
        assert scope.matches(api_key_id="key-2") is True
        assert scope.matches(api_key_id="key-3") is False
        assert scope.matches(agent_id="agent-1") is False

    def test_api_key_scope_no_match_without_key(self):
        """API key scope should not match without API key."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_api_key_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            api_key_ids=["key-1"],
        )

        assert scope.matches() is False
        assert scope.matches(agent_id="agent-1") is False

    def test_api_key_ids_json_serialization(self):
        """API key IDs should serialize to JSON."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_api_key_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            api_key_ids=["key-1", "key-2", "key-3"],
        )

        assert scope.api_key_ids_json is not None
        assert "key-1" in scope.api_key_ids_json
        assert scope.api_key_ids == ["key-1", "key-2", "key-3"]


class TestGAP002HumanActorTargeting:
    """Test GAP-002: Human actor targeting."""

    def test_scope_type_human_actor_exists(self):
        """HUMAN_ACTOR scope type should exist."""
        from app.models.policy_scope import ScopeType
        assert hasattr(ScopeType, "HUMAN_ACTOR")
        assert ScopeType.HUMAN_ACTOR.value == "human_actor"

    def test_create_human_actor_scope(self):
        """Should create scope with human actor targeting."""
        from app.models.policy_scope import PolicyScope, ScopeType

        scope = PolicyScope.create_human_actor_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            human_actor_ids=["user-1", "user-2"],
        )

        assert scope.scope_type == ScopeType.HUMAN_ACTOR.value
        assert scope.human_actor_ids == ["user-1", "user-2"]
        assert scope.agent_ids == []
        assert scope.api_key_ids == []

    def test_human_actor_scope_matches(self):
        """Human actor scope should match correct actors."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_human_actor_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            human_actor_ids=["user-1", "user-2"],
        )

        assert scope.matches(human_actor_id="user-1") is True
        assert scope.matches(human_actor_id="user-2") is True
        assert scope.matches(human_actor_id="user-3") is False
        assert scope.matches(api_key_id="key-1") is False

    def test_human_actor_scope_no_match_without_actor(self):
        """Human actor scope should not match without actor ID."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_human_actor_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            human_actor_ids=["user-1"],
        )

        assert scope.matches() is False
        assert scope.matches(agent_id="agent-1") is False

    def test_human_actor_ids_json_serialization(self):
        """Human actor IDs should serialize to JSON."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_human_actor_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            human_actor_ids=["user-1", "user-2"],
        )

        assert scope.human_actor_ids_json is not None
        assert "user-1" in scope.human_actor_ids_json
        assert scope.human_actor_ids == ["user-1", "user-2"]


class TestGAP003AllRunsScope:
    """Test GAP-003: ALL_RUNS scope."""

    def test_scope_type_all_runs_exists(self):
        """ALL_RUNS scope type should exist."""
        from app.models.policy_scope import ScopeType
        assert hasattr(ScopeType, "ALL_RUNS")
        assert ScopeType.ALL_RUNS.value == "all_runs"

    def test_create_all_runs_scope(self):
        """Should create ALL_RUNS scope."""
        from app.models.policy_scope import PolicyScope, ScopeType

        scope = PolicyScope.create_all_runs_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
        )

        assert scope.scope_type == ScopeType.ALL_RUNS.value
        assert scope.agent_ids == []
        assert scope.api_key_ids == []
        assert scope.human_actor_ids == []

    def test_all_runs_scope_matches_everything(self):
        """ALL_RUNS scope should match any context."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_all_runs_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
        )

        # Should match everything
        assert scope.matches() is True
        assert scope.matches(agent_id="agent-1") is True
        assert scope.matches(api_key_id="key-1") is True
        assert scope.matches(human_actor_id="user-1") is True
        assert scope.matches(
            agent_id="agent-1",
            api_key_id="key-1",
            human_actor_id="user-1",
        ) is True

    def test_all_runs_is_default_scope_type(self):
        """ALL_RUNS should be the default scope type."""
        from app.models.policy_scope import PolicyScope, ScopeType

        scope = PolicyScope(
            policy_id="policy-1",
            tenant_id="tenant-1",
        )

        assert scope.scope_type == ScopeType.ALL_RUNS.value


class TestGAP004ScopeResolutionSnapshot:
    """Test GAP-004: Scope resolution snapshot."""

    def test_scope_has_to_snapshot_method(self):
        """PolicyScope should have to_snapshot method."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_all_runs_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
        )

        snapshot = scope.to_snapshot()
        assert isinstance(snapshot, dict)
        assert "scope_id" in snapshot
        assert "scope_type" in snapshot

    def test_scope_snapshot_contains_all_fields(self):
        """Scope snapshot should contain all relevant fields."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_api_key_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            api_key_ids=["key-1", "key-2"],
        )

        snapshot = scope.to_snapshot()

        assert snapshot["scope_type"] == "api_key"
        assert snapshot["api_key_ids"] == ["key-1", "key-2"]
        assert snapshot["agent_ids"] == []
        assert snapshot["human_actor_ids"] == []

    def test_resolution_result_has_to_snapshot_method(self):
        """ScopeResolutionResult should have to_snapshot method."""
        from app.policy.scope_resolver import ScopeResolutionResult, RunContext

        ctx = RunContext(
            tenant_id="tenant-1",
            agent_id="agent-1",
            api_key_id="key-1",
            human_actor_id="user-1",
        )

        result = ScopeResolutionResult(
            matching_policy_ids=["policy-1", "policy-2"],
            all_runs_policies=["policy-1"],
            agent_policies=["policy-2"],
            api_key_policies=[],
            human_actor_policies=[],
            context=ctx,
            scopes_evaluated=5,
            resolution_timestamp="2026-01-21T12:00:00Z",
        )

        snapshot = result.to_snapshot()
        assert isinstance(snapshot, dict)

    def test_resolution_snapshot_contains_all_fields(self):
        """Resolution snapshot should contain all relevant fields."""
        from app.policy.scope_resolver import ScopeResolutionResult, RunContext

        ctx = RunContext(
            tenant_id="tenant-1",
            agent_id="agent-1",
            api_key_id="key-1",
            human_actor_id="user-1",
        )

        result = ScopeResolutionResult(
            matching_policy_ids=["policy-1", "policy-2"],
            all_runs_policies=["policy-1"],
            agent_policies=["policy-2"],
            api_key_policies=["policy-3"],
            human_actor_policies=["policy-4"],
            context=ctx,
            scopes_evaluated=10,
            resolution_timestamp="2026-01-21T12:00:00Z",
        )

        snapshot = result.to_snapshot()

        assert snapshot["matching_policy_ids"] == ["policy-1", "policy-2"]
        assert snapshot["all_runs_policies"] == ["policy-1"]
        assert snapshot["agent_policies"] == ["policy-2"]
        assert snapshot["api_key_policies"] == ["policy-3"]
        assert snapshot["human_actor_policies"] == ["policy-4"]
        assert snapshot["scopes_evaluated"] == 10
        assert snapshot["resolution_timestamp"] == "2026-01-21T12:00:00Z"

    def test_resolution_snapshot_contains_context(self):
        """Resolution snapshot should contain run context."""
        from app.policy.scope_resolver import ScopeResolutionResult, RunContext

        ctx = RunContext(
            tenant_id="tenant-1",
            agent_id="agent-1",
            api_key_id="key-1",
            human_actor_id="user-1",
        )

        result = ScopeResolutionResult(
            matching_policy_ids=[],
            all_runs_policies=[],
            agent_policies=[],
            api_key_policies=[],
            human_actor_policies=[],
            context=ctx,
            scopes_evaluated=0,
            resolution_timestamp="2026-01-21T12:00:00Z",
        )

        snapshot = result.to_snapshot()

        assert "context" in snapshot
        assert snapshot["context"]["tenant_id"] == "tenant-1"
        assert snapshot["context"]["agent_id"] == "agent-1"
        assert snapshot["context"]["api_key_id"] == "key-1"
        assert snapshot["context"]["human_actor_id"] == "user-1"


class TestRunContext:
    """Test RunContext dataclass."""

    def test_run_context_creation(self):
        """RunContext should be created with required fields."""
        from app.policy.scope_resolver import RunContext

        ctx = RunContext(tenant_id="tenant-1")
        assert ctx.tenant_id == "tenant-1"
        assert ctx.agent_id is None
        assert ctx.api_key_id is None
        assert ctx.human_actor_id is None
        assert ctx.run_id is None

    def test_run_context_with_all_fields(self):
        """RunContext should accept all fields."""
        from app.policy.scope_resolver import RunContext

        ctx = RunContext(
            tenant_id="tenant-1",
            agent_id="agent-1",
            api_key_id="key-1",
            human_actor_id="user-1",
            run_id="run-1",
        )

        assert ctx.tenant_id == "tenant-1"
        assert ctx.agent_id == "agent-1"
        assert ctx.api_key_id == "key-1"
        assert ctx.human_actor_id == "user-1"
        assert ctx.run_id == "run-1"


class TestAgentScope:
    """Test AGENT scope targeting."""

    def test_scope_type_agent_exists(self):
        """AGENT scope type should exist."""
        from app.models.policy_scope import ScopeType
        assert hasattr(ScopeType, "AGENT")
        assert ScopeType.AGENT.value == "agent"

    def test_create_agent_scope(self):
        """Should create scope with agent targeting."""
        from app.models.policy_scope import PolicyScope, ScopeType

        scope = PolicyScope.create_agent_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            agent_ids=["agent-1", "agent-2"],
        )

        assert scope.scope_type == ScopeType.AGENT.value
        assert scope.agent_ids == ["agent-1", "agent-2"]

    def test_agent_scope_matches(self):
        """Agent scope should match correct agents."""
        from app.models.policy_scope import PolicyScope

        scope = PolicyScope.create_agent_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            agent_ids=["agent-1", "agent-2"],
        )

        assert scope.matches(agent_id="agent-1") is True
        assert scope.matches(agent_id="agent-2") is True
        assert scope.matches(agent_id="agent-3") is False


class TestScopePydanticModels:
    """Test Pydantic models for scope API."""

    def test_policy_scope_create_model(self):
        """PolicyScopeCreate should work with all scope types."""
        from app.models.policy_scope import PolicyScopeCreate, ScopeType

        # API key scope
        create = PolicyScopeCreate(
            policy_id="policy-1",
            scope_type=ScopeType.API_KEY,
            api_key_ids=["key-1", "key-2"],
        )
        assert create.scope_type == ScopeType.API_KEY
        assert create.api_key_ids == ["key-1", "key-2"]

        # Human actor scope
        create = PolicyScopeCreate(
            policy_id="policy-1",
            scope_type=ScopeType.HUMAN_ACTOR,
            human_actor_ids=["user-1"],
        )
        assert create.scope_type == ScopeType.HUMAN_ACTOR
        assert create.human_actor_ids == ["user-1"]

    def test_policy_scope_response_model(self):
        """PolicyScopeResponse should contain all fields."""
        from app.models.policy_scope import PolicyScopeResponse, ScopeType

        response = PolicyScopeResponse(
            scope_id="SCOPE-123",
            policy_id="policy-1",
            tenant_id="tenant-1",
            scope_type=ScopeType.API_KEY,
            api_key_ids=["key-1"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert response.scope_id == "SCOPE-123"
        assert response.scope_type == ScopeType.API_KEY
        assert response.api_key_ids == ["key-1"]


class TestScopeIsolation:
    """Test scope isolation and mutual exclusivity."""

    def test_scope_types_are_mutually_exclusive(self):
        """Different scope types should not interfere."""
        from app.models.policy_scope import PolicyScope

        # API key scope should not match agent
        api_scope = PolicyScope.create_api_key_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            api_key_ids=["key-1"],
        )
        assert api_scope.matches(agent_id="key-1") is False
        assert api_scope.matches(human_actor_id="key-1") is False
        assert api_scope.matches(api_key_id="key-1") is True

        # Human actor scope should not match API key
        human_scope = PolicyScope.create_human_actor_scope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            human_actor_ids=["user-1"],
        )
        assert human_scope.matches(api_key_id="user-1") is False
        assert human_scope.matches(agent_id="user-1") is False
        assert human_scope.matches(human_actor_id="user-1") is True

    def test_empty_target_list_matches_nothing(self):
        """Scope with empty target list should match nothing."""
        from app.models.policy_scope import PolicyScope, ScopeType

        scope = PolicyScope(
            policy_id="policy-1",
            tenant_id="tenant-1",
            scope_type=ScopeType.API_KEY.value,
            api_key_ids_json="[]",
        )

        assert scope.matches(api_key_id="key-1") is False
        assert scope.matches() is False
