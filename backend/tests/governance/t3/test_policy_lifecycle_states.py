# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 policy lifecycle state governance requirements (GAP-020, GAP-021)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-006: Policy Lifecycle State Tests (GAP-020, GAP-021)

Tests the policy lifecycle state management:
- GAP-020: DRAFT state - status: DRAFT before activation
- GAP-021: SUSPENDED state - status: SUSPENDED (temporary disable)

The system already has lifecycle state patterns for other entities:
- IncidentLifecycleState: ACTIVE, ACKED, RESOLVED
- PolicyRuleStatus: ACTIVE, RETIRED
- ContractStatus: DRAFT, QUEUED, ACTIVE, LAPSED, COMPLETED

Key Principle:
> Policies follow a lifecycle from draft through active to retired.
"""

import pytest

from app.models.policy_control_plane import (
    EnforcementMode,
    LimitStatus,
    PolicyRule,
    PolicyRuleStatus,
    PolicyScope,
    PolicySource,
    RuleType,
)
from app.models.killswitch import IncidentLifecycleState


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestPolicyLifecycleImports:
    """Verify all policy lifecycle related imports are accessible."""

    def test_policy_rule_status_import(self) -> None:
        """Test PolicyRuleStatus enum is importable."""
        assert PolicyRuleStatus is not None

    def test_policy_rule_import(self) -> None:
        """Test PolicyRule model is importable."""
        assert PolicyRule is not None

    def test_limit_status_import(self) -> None:
        """Test LimitStatus enum is importable."""
        assert LimitStatus is not None

    def test_incident_lifecycle_state_import(self) -> None:
        """Test IncidentLifecycleState enum is importable (reference pattern)."""
        assert IncidentLifecycleState is not None


# ===========================================================================
# GAP-020: DRAFT State
# ===========================================================================


class TestGAP020DraftState:
    """
    GAP-020: DRAFT State

    CURRENT: Not supported (policies start ACTIVE)
    REQUIRED: `status: DRAFT` before activation

    Note: The DRAFT concept exists in ContractStatus and policy proposals.
    PolicyRuleStatus currently has ACTIVE and RETIRED only.
    """

    def test_policy_rule_has_status_field(self) -> None:
        """PolicyRule has status field."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
        )
        assert hasattr(rule, "status")

    def test_policy_rule_status_defaults_to_active(self) -> None:
        """PolicyRule status defaults to ACTIVE."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
        )
        assert rule.status == PolicyRuleStatus.ACTIVE.value

    def test_policy_rule_status_enum_has_active(self) -> None:
        """PolicyRuleStatus enum has ACTIVE value."""
        assert PolicyRuleStatus.ACTIVE is not None
        assert PolicyRuleStatus.ACTIVE.value == "ACTIVE"

    def test_policy_rule_status_enum_has_retired(self) -> None:
        """PolicyRuleStatus enum has RETIRED value."""
        assert PolicyRuleStatus.RETIRED is not None
        assert PolicyRuleStatus.RETIRED.value == "RETIRED"

    def test_draft_pattern_exists_in_contracts(self) -> None:
        """DRAFT state pattern exists in ContractStatus (reference)."""
        from app.models.contract import ContractStatus

        assert ContractStatus.DRAFT is not None
        assert ContractStatus.DRAFT.value == "DRAFT"

    def test_draft_pattern_in_policy_proposals(self) -> None:
        """Policy proposals can be in draft state."""
        # Policy proposals support draft state before approval
        # The PolicyProposal model uses status column with "draft" as server_default
        from app.models.policy import PolicyProposal

        # PolicyProposal has a status column
        assert hasattr(PolicyProposal, "status")

        # Can create proposal with draft status
        proposal = PolicyProposal(status="draft")
        assert proposal.status == "draft"

        # Can also set to other statuses like "approved" or "rejected"
        proposal.status = "approved"
        assert proposal.status == "approved"


# ===========================================================================
# GAP-021: SUSPENDED State
# ===========================================================================


class TestGAP021SuspendedState:
    """
    GAP-021: SUSPENDED State

    CURRENT: Not supported
    REQUIRED: `status: SUSPENDED` (temporary disable)

    Note: The SUSPENDED concept exists in tenant lifecycle.
    LimitStatus has ACTIVE and DISABLED which serves similar purpose.
    """

    def test_limit_status_has_disabled(self) -> None:
        """LimitStatus enum has DISABLED value (similar to SUSPENDED)."""
        assert LimitStatus.DISABLED is not None
        assert LimitStatus.DISABLED.value == "DISABLED"

    def test_tenant_lifecycle_has_suspended(self) -> None:
        """TenantLifecycleState has SUSPENDED (reference pattern)."""
        from app.hoc.cus.account.L5_schemas.tenant_lifecycle_state import TenantLifecycleState

        assert TenantLifecycleState.SUSPENDED is not None
        # Note: TenantLifecycleState is IntEnum
        assert TenantLifecycleState.SUSPENDED.name == "SUSPENDED"

    def test_policy_rule_retire_method(self) -> None:
        """PolicyRule has retire method for deactivation."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
        )
        assert hasattr(rule, "retire")
        assert callable(rule.retire)

    def test_policy_rule_retire_changes_status(self) -> None:
        """Retiring a policy changes status to RETIRED."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
        )
        assert rule.status == PolicyRuleStatus.ACTIVE.value

        rule.retire(by="user-123", reason="No longer needed")

        assert rule.status == PolicyRuleStatus.RETIRED.value

    def test_disabled_limits_pattern(self) -> None:
        """Limits can be DISABLED (temporary suspension pattern)."""
        from decimal import Decimal
        from app.models.policy_control_plane import Limit

        limit = Limit(
            id="LIM-001",
            tenant_id="tenant-001",
            name="Test Limit",
            limit_category="BUDGET",
            limit_type="COST_USD",
            max_value=Decimal("1000"),
        )
        # Limits can be set to DISABLED status
        limit.status = LimitStatus.DISABLED.value
        assert limit.status == "DISABLED"


# ===========================================================================
# Test: Policy Rule Status
# ===========================================================================


class TestPolicyRuleStatusEnum:
    """Test PolicyRuleStatus enum values."""

    def test_active_status(self) -> None:
        """ACTIVE status exists."""
        assert PolicyRuleStatus.ACTIVE.value == "ACTIVE"

    def test_retired_status(self) -> None:
        """RETIRED status exists."""
        assert PolicyRuleStatus.RETIRED.value == "RETIRED"

    def test_status_count(self) -> None:
        """PolicyRuleStatus has expected number of values."""
        # Currently has 2: ACTIVE, RETIRED
        # GAP-020/021 would add DRAFT, SUSPENDED
        statuses = list(PolicyRuleStatus)
        assert len(statuses) >= 2


# ===========================================================================
# Test: Limit Status
# ===========================================================================


class TestLimitStatusEnum:
    """Test LimitStatus enum values."""

    def test_active_status(self) -> None:
        """ACTIVE status exists."""
        assert LimitStatus.ACTIVE.value == "ACTIVE"

    def test_disabled_status(self) -> None:
        """DISABLED status exists (serves as SUSPENDED equivalent)."""
        assert LimitStatus.DISABLED.value == "DISABLED"

    def test_status_count(self) -> None:
        """LimitStatus has expected number of values."""
        statuses = list(LimitStatus)
        assert len(statuses) >= 2


# ===========================================================================
# Test: Incident Lifecycle Reference Pattern
# ===========================================================================


class TestIncidentLifecyclePattern:
    """Test IncidentLifecycleState as reference pattern for lifecycle states."""

    def test_active_state(self) -> None:
        """ACTIVE state exists."""
        assert IncidentLifecycleState.ACTIVE.value == "ACTIVE"

    def test_acked_state(self) -> None:
        """ACKED state exists."""
        assert IncidentLifecycleState.ACKED.value == "ACKED"

    def test_resolved_state(self) -> None:
        """RESOLVED state exists."""
        assert IncidentLifecycleState.RESOLVED.value == "RESOLVED"

    def test_lifecycle_progression(self) -> None:
        """Incident lifecycle follows ACTIVE -> ACKED -> RESOLVED pattern."""
        states = [s.value for s in IncidentLifecycleState]
        assert "ACTIVE" in states
        assert "ACKED" in states
        assert "RESOLVED" in states


# ===========================================================================
# Test: Policy Rule Fields
# ===========================================================================


class TestPolicyRuleFields:
    """Test PolicyRule model fields for lifecycle support."""

    def test_enforcement_mode_field(self) -> None:
        """PolicyRule has enforcement_mode field."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
        )
        assert hasattr(rule, "enforcement_mode")

    def test_enforcement_mode_can_be_disabled(self) -> None:
        """Enforcement mode can be DISABLED (soft suspension)."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
            enforcement_mode=EnforcementMode.DISABLED.value,
        )
        assert rule.enforcement_mode == "DISABLED"

    def test_policy_scope_field(self) -> None:
        """PolicyRule has scope field."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
        )
        assert hasattr(rule, "scope")

    def test_policy_source_field(self) -> None:
        """PolicyRule tracks creation source."""
        rule = PolicyRule(
            id="POL-001",
            tenant_id="tenant-001",
            name="Test Policy",
            created_by="user-123",
            source=PolicySource.MANUAL.value,
        )
        assert rule.source == "MANUAL"


# ===========================================================================
# Test: Enforcement Mode
# ===========================================================================


class TestEnforcementMode:
    """Test EnforcementMode enum for policy enforcement states."""

    def test_block_mode(self) -> None:
        """BLOCK enforcement mode exists."""
        assert EnforcementMode.BLOCK.value == "BLOCK"

    def test_warn_mode(self) -> None:
        """WARN enforcement mode exists."""
        assert EnforcementMode.WARN.value == "WARN"

    def test_audit_mode(self) -> None:
        """AUDIT enforcement mode exists."""
        assert EnforcementMode.AUDIT.value == "AUDIT"

    def test_disabled_mode(self) -> None:
        """DISABLED enforcement mode exists (soft suspension)."""
        assert EnforcementMode.DISABLED.value == "DISABLED"


# ===========================================================================
# Test: Policy Scope
# ===========================================================================


class TestPolicyScope:
    """Test PolicyScope enum for policy targeting."""

    def test_global_scope(self) -> None:
        """GLOBAL scope exists."""
        assert PolicyScope.GLOBAL.value == "GLOBAL"

    def test_tenant_scope(self) -> None:
        """TENANT scope exists."""
        assert PolicyScope.TENANT.value == "TENANT"

    def test_project_scope(self) -> None:
        """PROJECT scope exists."""
        assert PolicyScope.PROJECT.value == "PROJECT"

    def test_agent_scope(self) -> None:
        """AGENT scope exists."""
        assert PolicyScope.AGENT.value == "AGENT"


# ===========================================================================
# Test: Policy Source
# ===========================================================================


class TestPolicySource:
    """Test PolicySource enum for policy provenance."""

    def test_manual_source(self) -> None:
        """MANUAL source exists (human-created)."""
        assert PolicySource.MANUAL.value == "MANUAL"

    def test_system_source(self) -> None:
        """SYSTEM source exists (system-generated)."""
        assert PolicySource.SYSTEM.value == "SYSTEM"

    def test_learned_source(self) -> None:
        """LEARNED source exists (ML-derived)."""
        assert PolicySource.LEARNED.value == "LEARNED"


# ===========================================================================
# Test: Rule Type
# ===========================================================================


class TestRuleType:
    """Test RuleType enum for policy semantics."""

    def test_system_type(self) -> None:
        """SYSTEM rule type exists."""
        assert RuleType.SYSTEM.value == "SYSTEM"

    def test_safety_type(self) -> None:
        """SAFETY rule type exists."""
        assert RuleType.SAFETY.value == "SAFETY"

    def test_ethical_type(self) -> None:
        """ETHICAL rule type exists."""
        assert RuleType.ETHICAL.value == "ETHICAL"

    def test_temporal_type(self) -> None:
        """TEMPORAL rule type exists (time-bound rules)."""
        assert RuleType.TEMPORAL.value == "TEMPORAL"
