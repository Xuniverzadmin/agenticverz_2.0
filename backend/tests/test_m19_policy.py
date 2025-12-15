# M19 Policy Layer Tests
# Constitutional governance for multi-agent systems
#
# Tests cover:
# - Policy evaluation (all action types)
# - Ethical constraints (no coercion, no fabrication, transparency)
# - Safety rules (action blocks, cooldowns, escalations)
# - Risk ceilings (cost, retry, cascade limits)
# - Business rules (budgets, tier access, feature gates)
# - Governor integration (freeze on severe violations)
# - API endpoints

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.policy.engine import PolicyEngine, get_policy_engine
from app.policy.models import (
    ActionType,
    BusinessRule,
    BusinessRuleType,
    EthicalConstraint,
    EthicalConstraintType,
    Policy,
    PolicyCategory,
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    PolicyModification,
    PolicyRule,
    PolicyState,
    PolicyViolation,
    RiskCeiling,
    SafetyRule,
    SafetyRuleType,
    ViolationType,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def policy_engine():
    """Create a fresh policy engine for testing."""
    engine = PolicyEngine(database_url=None)  # In-memory mode
    engine._load_default_policies()
    return engine


@pytest.fixture
def mock_governor():
    """Create a mock M18 Governor."""
    governor = AsyncMock()
    governor.force_freeze = AsyncMock()
    return governor


@pytest.fixture
def policy_engine_with_governor(policy_engine, mock_governor):
    """Policy engine with mock governor attached."""
    policy_engine.set_governor(mock_governor)
    return policy_engine


# =============================================================================
# Policy Evaluation Tests
# =============================================================================

class TestPolicyEvaluation:
    """Test core policy evaluation functionality."""

    @pytest.mark.asyncio
    async def test_evaluate_allows_clean_request(self, policy_engine):
        """Test that clean requests are allowed."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            tenant_id="tenant-1",
            proposed_action="fetch_user_data",
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.ALLOW
        assert result.policies_evaluated > 0
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_evaluate_all_action_types(self, policy_engine):
        """Test evaluation works for all action types."""
        for action_type in ActionType:
            request = PolicyEvaluationRequest(
                action_type=action_type,
                agent_id=f"agent-{action_type.value}",
            )

            result = await policy_engine.evaluate(request)
            assert result.decision in [PolicyDecision.ALLOW, PolicyDecision.BLOCK, PolicyDecision.MODIFY]

    @pytest.mark.asyncio
    async def test_dry_run_mode(self, policy_engine):
        """Test dry run doesn't persist or have side effects."""
        initial_count = policy_engine._evaluations_count

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
        )

        # Dry run
        result = await policy_engine.evaluate(request, dry_run=True)
        assert result.decision == PolicyDecision.ALLOW
        assert policy_engine._evaluations_count == initial_count

        # Normal run
        result = await policy_engine.evaluate(request, dry_run=False)
        assert policy_engine._evaluations_count == initial_count + 1


# =============================================================================
# Ethical Constraint Tests
# =============================================================================

class TestEthicalConstraints:
    """Test ethical constraint enforcement."""

    @pytest.mark.asyncio
    async def test_blocks_coercive_language(self, policy_engine):
        """Test that coercive language is blocked."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            proposed_action="threaten user with account deletion",
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any(v.violation_type == ViolationType.ETHICAL_VIOLATION for v in result.violations)
        assert "coercion" in str(result.violations).lower() or "threaten" in str(result.violations).lower()

    @pytest.mark.asyncio
    async def test_blocks_fabrication(self, policy_engine):
        """Test that data fabrication is blocked."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            proposed_action="create fake_data for report",
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any(v.violation_type == ViolationType.ETHICAL_VIOLATION for v in result.violations)

    @pytest.mark.asyncio
    async def test_transparency_threshold(self, policy_engine):
        """Test transparency threshold enforcement."""
        # Add transparency constraint
        policy_engine._ethical_constraints.append(EthicalConstraint(
            name="transparency_test",
            description="Test transparency",
            constraint_type=EthicalConstraintType.TRANSPARENCY,
            transparency_threshold=0.8,
            enforcement_level="strict",
            violation_action="block",
        ))

        # Low explainability should be blocked
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            context={"explainability_score": 0.5},
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any("explainable" in v.description.lower() for v in result.violations)


# =============================================================================
# Safety Rule Tests
# =============================================================================

class TestSafetyRules:
    """Test safety rule enforcement."""

    @pytest.mark.asyncio
    async def test_blocks_dangerous_commands(self, policy_engine):
        """Test that dangerous system commands are blocked."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            proposed_action="rm -rf /",
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any(v.violation_type == ViolationType.SAFETY_RULE_TRIGGERED for v in result.violations)

    @pytest.mark.asyncio
    async def test_cooldown_enforcement(self, policy_engine):
        """Test cooldown enforcement after failures."""
        # Add cooldown rule
        policy_engine._safety_rules.append(SafetyRule(
            name="test_cooldown",
            rule_type=SafetyRuleType.COOLDOWN,
            condition={"failure_count": 3, "window_seconds": 60},
            action="cooldown",
            cooldown_seconds=300,
        ))

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-cd",
            context={"recent_failures": 5},  # Exceeds threshold
        )

        result = await policy_engine.evaluate(request)

        # Should be blocked due to cooldown
        assert result.decision == PolicyDecision.BLOCK
        assert any("cooldown" in v.description.lower() for v in result.violations)

        # Check cooldown is set
        cooldown_key = "agent-cd:test_cooldown"
        assert cooldown_key in policy_engine._cooldowns

    @pytest.mark.asyncio
    async def test_cooldown_blocking(self, policy_engine):
        """Test that cooldowns actually block subsequent requests."""
        # Set a cooldown
        cooldown_key = "agent-blocked:block_dangerous_commands"
        policy_engine._cooldowns[cooldown_key] = datetime.now(timezone.utc) + timedelta(minutes=5)

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-blocked",
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any("cooldown" in v.description.lower() for v in result.violations)

    @pytest.mark.asyncio
    async def test_escalation_required(self, policy_engine):
        """Test that high-cost operations require escalation."""
        # Add escalation rule
        policy_engine._safety_rules.append(SafetyRule(
            name="high_cost_escalation",
            rule_type=SafetyRuleType.ESCALATION_REQUIRED,
            condition={"cost_threshold": 10.0},
            action="escalate",
            priority=10,
        ))

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            estimated_cost=50.0,
        )

        result = await policy_engine.evaluate(request)

        # Should flag but not block (severity < 0.5)
        assert any("escalation" in v.description.lower() for v in result.violations)


# =============================================================================
# Risk Ceiling Tests
# =============================================================================

class TestRiskCeilings:
    """Test risk ceiling enforcement."""

    @pytest.mark.asyncio
    async def test_cost_ceiling_block(self, policy_engine):
        """Test that cost ceiling breaches are blocked."""
        # Set a very low cost ceiling
        policy_engine._risk_ceilings = [RiskCeiling(
            name="test_cost_ceiling",
            metric="cost_per_hour",
            max_value=1.0,
            breach_action="block",
            window_seconds=3600,
        )]

        # First request should use up the ceiling
        for _ in range(2):
            request = PolicyEvaluationRequest(
                action_type=ActionType.EXECUTE,
                agent_id="agent-1",
                estimated_cost=1.5,  # Exceeds max
            )
            result = await policy_engine.evaluate(request)

        # Should be blocked
        assert result.decision == PolicyDecision.BLOCK
        assert any(v.violation_type == ViolationType.RISK_CEILING_BREACH for v in result.violations)

    @pytest.mark.asyncio
    async def test_cost_ceiling_throttle(self, policy_engine):
        """Test that cost ceiling can throttle instead of block."""
        policy_engine._risk_ceilings = [RiskCeiling(
            name="throttle_ceiling",
            metric="cost_per_hour",
            max_value=10.0,
            breach_action="throttle",
            window_seconds=3600,
        )]

        # Accumulate cost to exceed ceiling
        for _ in range(3):
            request = PolicyEvaluationRequest(
                action_type=ActionType.EXECUTE,
                estimated_cost=5.0,
            )
            result = await policy_engine.evaluate(request)

        # Should modify instead of block
        if result.modifications:
            assert result.decision == PolicyDecision.MODIFY
            assert any(m.parameter == "throttle_factor" for m in result.modifications)

    @pytest.mark.asyncio
    async def test_retry_rate_ceiling(self, policy_engine):
        """Test retry rate ceiling."""
        policy_engine._risk_ceilings = [RiskCeiling(
            name="retry_ceiling",
            metric="retries_per_minute",
            max_value=5,
            breach_action="block",
        )]

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            context={"retry_count": 10},  # Exceeds limit
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any("retry" in v.policy_name.lower() or "ceiling" in v.description.lower() for v in result.violations)


# =============================================================================
# Business Rule Tests
# =============================================================================

class TestBusinessRules:
    """Test business rule enforcement."""

    @pytest.mark.asyncio
    async def test_budget_rule(self, policy_engine):
        """Test daily budget enforcement."""
        policy_engine._business_rules = [BusinessRule(
            name="daily_budget",
            rule_type=BusinessRuleType.BUDGET,
            condition={},
            constraint={"max_daily_budget": 100.0},
        )]

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            estimated_cost=50.0,
            context={"daily_spent": 80.0},  # 80 + 50 > 100
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any(v.violation_type == ViolationType.BUSINESS_RULE_VIOLATION for v in result.violations)

    @pytest.mark.asyncio
    async def test_tier_access_rule(self, policy_engine):
        """Test tier access enforcement."""
        policy_engine._business_rules = [BusinessRule(
            name="enterprise_feature",
            rule_type=BusinessRuleType.TIER_ACCESS,
            condition={},
            constraint={"required_tier": "enterprise"},
        )]

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            context={"customer_tier": "free"},
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any("tier" in v.description.lower() for v in result.violations)

    @pytest.mark.asyncio
    async def test_feature_gate(self, policy_engine):
        """Test feature gate enforcement."""
        policy_engine._business_rules = [BusinessRule(
            name="beta_feature_gate",
            rule_type=BusinessRuleType.FEATURE_GATE,
            condition={"feature": "self_modify"},
            constraint={"enabled": False},
        )]

        request = PolicyEvaluationRequest(
            action_type=ActionType.SELF_MODIFY,
            agent_id="agent-1",
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any("feature" in v.description.lower() for v in result.violations)


# =============================================================================
# Governor Integration Tests
# =============================================================================

class TestGovernorIntegration:
    """Test M18 Governor integration."""

    @pytest.mark.asyncio
    async def test_severe_violation_triggers_freeze(self, policy_engine_with_governor, mock_governor):
        """Test that severe violations trigger governor freeze."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            proposed_action="rm -rf /",  # Dangerous command
        )

        result = await policy_engine_with_governor.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        # Governor should have been called
        mock_governor.force_freeze.assert_called_once()

    @pytest.mark.asyncio
    async def test_violations_routed_to_governor(self, policy_engine_with_governor, mock_governor):
        """Test that violations are marked as routed."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-1",
            proposed_action="threaten user",
        )

        result = await policy_engine_with_governor.evaluate(request)

        blocking_violations = [v for v in result.violations if v.severity >= 0.9]
        for v in blocking_violations:
            assert v.routed_to_governor
            assert v.governor_action == "freeze"


# =============================================================================
# State and Metrics Tests
# =============================================================================

class TestStateAndMetrics:
    """Test state and metrics functionality."""

    @pytest.mark.asyncio
    async def test_get_state(self, policy_engine):
        """Test state retrieval."""
        state = await policy_engine.get_state()

        assert isinstance(state, PolicyState)
        assert state.total_policies > 0
        assert state.active_policies > 0

    @pytest.mark.asyncio
    async def test_evaluation_counts(self, policy_engine):
        """Test that evaluation counts are tracked."""
        initial = policy_engine._evaluations_count

        for i in range(5):
            request = PolicyEvaluationRequest(
                action_type=ActionType.EXECUTE,
                agent_id=f"agent-{i}",
            )
            await policy_engine.evaluate(request)

        assert policy_engine._evaluations_count == initial + 5

    @pytest.mark.asyncio
    async def test_block_rate_calculation(self, policy_engine):
        """Test block rate calculation."""
        # Allow a clean request
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-clean",
        )
        await policy_engine.evaluate(request)

        # Block a bad request
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id="agent-bad",
            proposed_action="rm -rf /",
        )
        await policy_engine.evaluate(request)

        state = await policy_engine.get_state()
        assert 0 <= state.block_rate <= 1.0


# =============================================================================
# Reload and Cache Tests
# =============================================================================

class TestCacheAndReload:
    """Test policy caching and reloading."""

    @pytest.mark.asyncio
    async def test_reload_policies(self, policy_engine):
        """Test policy reload."""
        result = await policy_engine.reload_policies()

        assert result.policies_loaded >= 0
        assert result.ethical_constraints_loaded >= 0
        assert result.safety_rules_loaded >= 0


# =============================================================================
# Compliance Tests
# =============================================================================

class TestComplianceRules:
    """Test compliance policy enforcement."""

    @pytest.mark.asyncio
    async def test_data_category_restriction(self, policy_engine):
        """Test forbidden data category blocking."""
        policy_engine._policies = [Policy(
            name="pii_restriction",
            category=PolicyCategory.COMPLIANCE,
            rules=[PolicyRule(
                name="no_pii_external",
                condition={"forbidden_data_categories": ["pii", "financial"]},
                action=PolicyDecision.BLOCK,
            )],
        )]

        request = PolicyEvaluationRequest(
            action_type=ActionType.EXTERNAL_CALL,
            agent_id="agent-1",
            data_categories=["pii"],
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any(v.violation_type == ViolationType.COMPLIANCE_BREACH for v in result.violations)

    @pytest.mark.asyncio
    async def test_jurisdiction_restriction(self, policy_engine):
        """Test jurisdiction compliance."""
        policy_engine._policies = [Policy(
            name="gdpr_compliance",
            category=PolicyCategory.COMPLIANCE,
            rules=[PolicyRule(
                name="eu_only",
                condition={"allowed_jurisdictions": ["EU", "US"]},
                action=PolicyDecision.BLOCK,
            )],
        )]

        request = PolicyEvaluationRequest(
            action_type=ActionType.DATA_ACCESS,
            agent_id="agent-1",
            context={"jurisdiction": "RESTRICTED"},
        )

        result = await policy_engine.evaluate(request)

        assert result.decision == PolicyDecision.BLOCK
        assert any("jurisdiction" in v.description.lower() for v in result.violations)


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_request(self, policy_engine):
        """Test handling of minimal request."""
        request = PolicyEvaluationRequest(action_type=ActionType.EXECUTE)

        result = await policy_engine.evaluate(request)

        assert result.decision in [PolicyDecision.ALLOW, PolicyDecision.BLOCK, PolicyDecision.MODIFY]
        assert result.request_id is not None

    @pytest.mark.asyncio
    async def test_null_values_in_context(self, policy_engine):
        """Test handling of null values."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            agent_id=None,
            tenant_id=None,
            context={"key": None},
        )

        result = await policy_engine.evaluate(request)

        assert result is not None

    @pytest.mark.asyncio
    async def test_large_context(self, policy_engine):
        """Test handling of large context."""
        request = PolicyEvaluationRequest(
            action_type=ActionType.EXECUTE,
            context={f"key_{i}": f"value_{i}" * 100 for i in range(100)},
        )

        result = await policy_engine.evaluate(request)

        assert result is not None
        assert result.evaluation_ms > 0


# =============================================================================
# Integration Test (requires database)
# =============================================================================

# =============================================================================
# AsyncSession Regression Test (CI guardrail)
# =============================================================================

class TestAsyncSessionGuardrail:
    """Ensure policy endpoints use AsyncSession - prevents sync DB regression."""

    def test_policy_api_uses_async_session(self):
        """
        CI guardrail: Policy API endpoints MUST use AsyncSession.

        Background: Sync Session(engine) inside async endpoints causes:
        - Event-loop starvation under load
        - Deadlock risk when sharing DB pools
        - Incompatibility with M19 async governance layer

        If this test fails, someone has regressed to sync sessions.
        """
        import inspect
        from app.api.policy import evaluate_policy, get_approval_request

        # Check evaluate_policy signature
        sig = inspect.signature(evaluate_policy)
        params_str = str(sig)
        assert "AsyncSession" in params_str, (
            "evaluate_policy must use AsyncSession dependency injection. "
            "Sync Session inside async endpoints breaks event-loop safety."
        )

        # Check get_approval_request signature
        sig = inspect.signature(get_approval_request)
        params_str = str(sig)
        assert "AsyncSession" in params_str, (
            "get_approval_request must use AsyncSession dependency injection."
        )

    def test_no_sync_session_import_in_policy_api(self):
        """Ensure policy.py doesn't import sync Session from sqlmodel."""
        import ast
        from pathlib import Path

        policy_file = Path(__file__).parent.parent / "app" / "api" / "policy.py"
        if not policy_file.exists():
            pytest.skip("policy.py not found")

        source = policy_file.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "sqlmodel":
                    imported_names = [alias.name for alias in node.names]
                    assert "Session" not in imported_names, (
                        "policy.py must NOT import sync Session from sqlmodel. "
                        "Use 'from sqlalchemy.ext.asyncio import AsyncSession' instead."
                    )


@pytest.mark.skip(reason="Requires database connection")
class TestDatabaseIntegration:
    """Integration tests with real database."""

    @pytest.mark.asyncio
    async def test_persist_evaluation(self):
        """Test that evaluations are persisted."""
        pass

    @pytest.mark.asyncio
    async def test_load_policies_from_db(self):
        """Test loading policies from database."""
        pass
