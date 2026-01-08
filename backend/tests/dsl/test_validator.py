# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: DSL validator tests
# Reference: PIN-341, PIN-345

"""
Tests for Policy DSL Validator.

COVERAGE:
- Mode enforcement (MONITOR vs ENFORCE)
- Metric validation
- Structural validation
- Warning generation
- Custom rules
"""

import pytest

from app.dsl.ast import (
    PolicyAST,
)
from app.dsl.parser import parse
from app.dsl.validator import (
    V001,
    V002,
    V010,
    W001,
    PolicyValidator,
    Severity,
    ValidationIssue,
    ValidationResult,
    is_valid,
    validate,
)

# =============================================================================
# HELPER FIXTURES
# =============================================================================


@pytest.fixture
def monitor_policy_warn_only() -> PolicyAST:
    """Valid MONITOR policy with only WARN actions."""
    return parse("""
    policy TestMonitor
    version 1
    scope PROJECT
    mode MONITOR

    when cost > 100
    then WARN "High cost"
    """)


@pytest.fixture
def enforce_policy_with_block() -> PolicyAST:
    """Valid ENFORCE policy with BLOCK action."""
    return parse("""
    policy TestEnforce
    version 1
    scope PROJECT
    mode ENFORCE

    when cost > 100
    then BLOCK
    """)


@pytest.fixture
def monitor_policy_with_block() -> PolicyAST:
    """Invalid MONITOR policy with BLOCK action."""
    return parse("""
    policy TestMonitor
    version 1
    scope PROJECT
    mode MONITOR

    when cost > 100
    then BLOCK
    """)


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================


class TestValidationResult:
    """Tests for ValidationResult structure."""

    def test_valid_result_is_truthy(self, monitor_policy_warn_only: PolicyAST) -> None:
        """Test that valid result is truthy."""
        result = validate(monitor_policy_warn_only)
        assert result.is_valid
        assert bool(result) is True

    def test_invalid_result_is_falsy(self, monitor_policy_with_block: PolicyAST) -> None:
        """Test that invalid result is falsy."""
        result = validate(monitor_policy_with_block)
        assert not result.is_valid
        assert bool(result) is False

    def test_errors_property(self, monitor_policy_with_block: PolicyAST) -> None:
        """Test errors property filters correctly."""
        result = validate(monitor_policy_with_block)
        assert len(result.errors) > 0
        assert all(e.severity == Severity.ERROR for e in result.errors)

    def test_warnings_property(self) -> None:
        """Test warnings property filters correctly."""
        # ENFORCE mode with only WARN actions should produce a warning
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then WARN "Alert"
        """)
        result = validate(policy)
        assert len(result.warnings) > 0
        assert all(w.severity == Severity.WARNING for w in result.warnings)

    def test_issue_str_representation(self) -> None:
        """Test ValidationIssue string representation."""
        issue = ValidationIssue(
            code="V001",
            message="Test message",
            severity=Severity.ERROR,
            path="clauses[0].then[0]",
        )
        s = str(issue)
        assert "V001" in s
        assert "ERROR" in s
        assert "clauses[0].then[0]" in s
        assert "Test message" in s


# =============================================================================
# MODE ENFORCEMENT TESTS
# =============================================================================


class TestModeEnforcement:
    """Tests for mode enforcement validation."""

    def test_monitor_mode_allows_warn(self, monitor_policy_warn_only: PolicyAST) -> None:
        """MONITOR mode allows WARN actions."""
        result = validate(monitor_policy_warn_only)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_monitor_mode_rejects_block(self, monitor_policy_with_block: PolicyAST) -> None:
        """MONITOR mode rejects BLOCK actions."""
        result = validate(monitor_policy_with_block)
        assert not result.is_valid
        assert any(e.code == V001 for e in result.errors)

    def test_monitor_mode_rejects_require_approval(self) -> None:
        """MONITOR mode rejects REQUIRE_APPROVAL actions."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then REQUIRE_APPROVAL
        """)
        result = validate(policy)
        assert not result.is_valid
        assert any(e.code == V002 for e in result.errors)

    def test_monitor_mode_rejects_mixed_actions(self) -> None:
        """MONITOR mode rejects policies with any BLOCK/REQUIRE_APPROVAL."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert" BLOCK
        """)
        result = validate(policy)
        assert not result.is_valid
        assert any(e.code == V001 for e in result.errors)

    def test_enforce_mode_allows_all_actions(self, enforce_policy_with_block: PolicyAST) -> None:
        """ENFORCE mode allows all action types."""
        result = validate(enforce_policy_with_block)
        # Should be valid (no errors)
        assert len(result.errors) == 0

    def test_enforce_mode_allows_warn(self) -> None:
        """ENFORCE mode allows WARN actions."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then WARN "Alert"
        """)
        result = validate(policy)
        assert len(result.errors) == 0

    def test_enforce_mode_allows_require_approval(self) -> None:
        """ENFORCE mode allows REQUIRE_APPROVAL actions."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then REQUIRE_APPROVAL
        """)
        result = validate(policy)
        assert len(result.errors) == 0

    def test_enforce_mode_allows_mixed_actions(self) -> None:
        """ENFORCE mode allows mixed action types."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 100
        then WARN "High" BLOCK

        when x > 1000
        then WARN "Very High" REQUIRE_APPROVAL
        """)
        result = validate(policy)
        assert len(result.errors) == 0

    def test_multiple_violations_reported(self) -> None:
        """Multiple violations are all reported."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then BLOCK

        when y > 0
        then REQUIRE_APPROVAL

        when z > 0
        then BLOCK REQUIRE_APPROVAL
        """)
        result = validate(policy)
        # Should have 4 errors: 3 BLOCK + 2 REQUIRE_APPROVAL
        # (clause 0: BLOCK, clause 1: REQUIRE_APPROVAL, clause 2: BLOCK + REQUIRE_APPROVAL)
        assert len(result.errors) == 4


# =============================================================================
# METRIC VALIDATION TESTS
# =============================================================================


class TestMetricValidation:
    """Tests for metric validation."""

    def test_no_metric_validation_by_default(self) -> None:
        """By default, any metric is allowed."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when unknown_metric > 0
        then WARN "Alert"
        """)
        result = validate(policy)
        assert result.is_valid

    def test_metric_validation_with_allowed_set(self) -> None:
        """Metrics are validated against allowed set."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 100
        then WARN "Alert"
        """)
        allowed = {"cost", "error_rate", "latency"}
        result = validate(policy, allowed_metrics=allowed)
        assert result.is_valid

    def test_unknown_metric_rejected(self) -> None:
        """Unknown metrics are rejected when validation is enabled."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when unknown_metric > 0
        then WARN "Alert"
        """)
        allowed = {"cost", "error_rate"}
        result = validate(policy, allowed_metrics=allowed)
        assert not result.is_valid
        assert any(e.code == V010 for e in result.errors)

    def test_multiple_unknown_metrics(self) -> None:
        """Multiple unknown metrics are all reported."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when bad1 > 0 AND bad2 > 0
        then WARN "Alert"
        """)
        allowed = {"good"}
        result = validate(policy, allowed_metrics=allowed)
        errors = [e for e in result.errors if e.code == V010]
        assert len(errors) == 2

    def test_exists_predicate_metric_validation(self) -> None:
        """Exists predicates are also validated."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when exists(unknown_flag)
        then WARN "Alert"
        """)
        allowed = {"cost"}
        result = validate(policy, allowed_metrics=allowed)
        assert not result.is_valid
        assert any(e.code == V010 for e in result.errors)


# =============================================================================
# WARNING TESTS
# =============================================================================


class TestWarnings:
    """Tests for validation warnings."""

    def test_enforce_with_only_warn_produces_warning(self) -> None:
        """ENFORCE mode with only WARN actions produces warning."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then WARN "Alert"
        """)
        result = validate(policy)
        # Should be valid but have warnings
        assert result.is_valid
        assert any(w.code == W001 for w in result.warnings)

    def test_enforce_with_block_no_warning(self) -> None:
        """ENFORCE mode with BLOCK does not produce W001 warning."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then BLOCK
        """)
        result = validate(policy)
        assert not any(w.code == W001 for w in result.warnings)

    def test_enforce_with_require_approval_no_warning(self) -> None:
        """ENFORCE mode with REQUIRE_APPROVAL does not produce W001 warning."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then REQUIRE_APPROVAL
        """)
        result = validate(policy)
        assert not any(w.code == W001 for w in result.warnings)

    def test_monitor_mode_no_w001_warning(self) -> None:
        """MONITOR mode does not produce W001 warning."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        result = validate(policy)
        assert not any(w.code == W001 for w in result.warnings)


# =============================================================================
# CUSTOM RULES TESTS
# =============================================================================


class TestCustomRules:
    """Tests for custom validation rules."""

    def test_custom_rule_is_called(self) -> None:
        """Custom rules are invoked during validation."""
        called = []

        def custom_rule(policy: PolicyAST) -> list[ValidationIssue]:
            called.append(policy.name)
            return []

        validator = PolicyValidator(custom_rules=[custom_rule])
        policy = parse("""
        policy CustomTest
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        validator.validate(policy)
        assert "CustomTest" in called

    def test_custom_rule_can_add_errors(self) -> None:
        """Custom rules can add validation errors."""

        def no_cost_policy(policy: PolicyAST) -> list[ValidationIssue]:
            # Rule: Policies named "NoCost" cannot use cost metric
            issues = []
            if policy.name == "NoCost":
                for clause_idx, clause in enumerate(policy.clauses):
                    # Check if any predicate uses "cost"
                    # (simplified check)
                    issues.append(
                        ValidationIssue(
                            code="CUSTOM-001",
                            message="NoCost policies cannot use cost metric",
                            severity=Severity.ERROR,
                            path=f"clauses[{clause_idx}]",
                        )
                    )
            return issues

        validator = PolicyValidator(custom_rules=[no_cost_policy])
        policy = parse("""
        policy NoCost
        version 1
        scope ORG
        mode MONITOR

        when cost > 100
        then WARN "Alert"
        """)
        result = validator.validate(policy)
        assert not result.is_valid
        assert any(e.code == "CUSTOM-001" for e in result.errors)

    def test_multiple_custom_rules(self) -> None:
        """Multiple custom rules are all invoked."""
        results = []

        def rule1(policy: PolicyAST) -> list[ValidationIssue]:
            results.append("rule1")
            return []

        def rule2(policy: PolicyAST) -> list[ValidationIssue]:
            results.append("rule2")
            return []

        validator = PolicyValidator(custom_rules=[rule1, rule2])
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        validator.validate(policy)
        assert "rule1" in results
        assert "rule2" in results


# =============================================================================
# PUBLIC API TESTS
# =============================================================================


class TestPublicAPI:
    """Tests for public API functions."""

    def test_validate_function(self, monitor_policy_warn_only: PolicyAST) -> None:
        """Test validate() function."""
        result = validate(monitor_policy_warn_only)
        assert isinstance(result, ValidationResult)

    def test_is_valid_function_true(self, monitor_policy_warn_only: PolicyAST) -> None:
        """Test is_valid() returns True for valid policy."""
        assert is_valid(monitor_policy_warn_only) is True

    def test_is_valid_function_false(self, monitor_policy_with_block: PolicyAST) -> None:
        """Test is_valid() returns False for invalid policy."""
        assert is_valid(monitor_policy_with_block) is False

    def test_is_valid_with_metrics(self) -> None:
        """Test is_valid() with metric validation."""
        policy = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 0
        then WARN "Alert"
        """)
        assert is_valid(policy, allowed_metrics={"cost"}) is True
        assert is_valid(policy, allowed_metrics={"error_rate"}) is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests with parser."""

    def test_parse_and_validate_valid_policy(self) -> None:
        """Test parse → validate flow for valid policy."""
        source = """
        policy CostGuard
        version 3
        scope PROJECT
        mode ENFORCE

        when cost_per_hour > 200
        then WARN "Cost exceeded threshold"

        when cost_per_hour > 500
        then BLOCK
        """
        ast = parse(source)
        result = validate(ast)
        assert result.is_valid

    def test_parse_and_validate_invalid_policy(self) -> None:
        """Test parse → validate flow for invalid policy."""
        source = """
        policy BadPolicy
        version 1
        scope ORG
        mode MONITOR

        when cost > 100
        then WARN "Alert" BLOCK
        """
        ast = parse(source)
        result = validate(ast)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].code == V001
