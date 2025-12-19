# M24 Prevention Engine Tests
# Tests for multi-policy prevention with severity levels


import pytest

from app.policy.validators.prevention_engine import (
    BudgetValidator,
    ContentAccuracyValidatorV2,
    HallucinationValidator,
    PIIValidator,
    PolicyType,
    PolicyViolation,
    PreventionAction,
    PreventionContext,
    PreventionEngine,
    PreventionResult,
    SafetyValidator,
    Severity,
    evaluate_prevention,
)


class TestPreventionContext:
    """Tests for PreventionContext."""

    def test_context_creation(self):
        ctx = PreventionContext(
            tenant_id="tenant_123",
            call_id="call_abc",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract is auto-renewed.",
            context_data={"auto_renew": None},
        )
        assert ctx.tenant_id == "tenant_123"
        assert ctx.call_id == "call_abc"
        assert ctx.timestamp is not None

    def test_hash_output(self):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="test",
            llm_output="Hello, world!",
            context_data={},
        )
        hash1 = ctx.hash_output()
        hash2 = ctx.hash_output()
        assert hash1 == hash2
        assert len(hash1) == 16


class TestContentAccuracyValidatorV2:
    """Tests for enhanced content accuracy validator."""

    @pytest.fixture
    def validator(self):
        return ContentAccuracyValidatorV2(strict_mode=True)

    def test_pass_when_data_present(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract is set to auto-renew.",
            context_data={"auto_renew": True},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0

    def test_fail_when_data_missing(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract is set to auto-renew on January 1.",
            context_data={"auto_renew": None},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert violations[0].policy == PolicyType.CONTENT_ACCURACY
        assert violations[0].severity == Severity.HIGH
        assert violations[0].field_name == "auto_renew"

    def test_pass_when_expressing_uncertainty(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Is my contract auto-renewed?",
            llm_output="I don't have information about your auto-renew settings.",
            context_data={"auto_renew": None},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0

    def test_multiple_field_violations(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Tell me about my account",
            llm_output="Your subscription tier is Premium and your payment is confirmed.",
            context_data={"subscription_tier": None, "payment_status": None},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 2


class TestPIIValidator:
    """Tests for PII detection validator."""

    @pytest.fixture
    def validator(self):
        return PIIValidator()

    def test_detect_ssn(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What is my SSN?",
            llm_output="Your SSN is 123-45-6789.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert violations[0].policy == PolicyType.PII
        assert violations[0].severity == Severity.CRITICAL
        assert "ssn" in violations[0].rule_id.lower()

    def test_detect_credit_card(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What is my card number?",
            llm_output="Your credit card is 4111-1111-1111-1111.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert "credit_card" in violations[0].rule_id.lower()

    def test_detect_email(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What email?",
            llm_output="Your email is john.doe@example.com.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert violations[0].policy == PolicyType.PII

    def test_detect_api_key(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What is the key?",
            llm_output="Your API key is token_test_abcdefghijklmnopqrstuvwxyz123456.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert "api_key" in violations[0].rule_id.lower()

    def test_no_pii_detected(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Hello",
            llm_output="Hello! How can I help you today?",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0

    def test_allowed_pii(self):
        validator = PIIValidator(allowed_pii={"email"})
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What email?",
            llm_output="Your email is john.doe@example.com.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0


class TestSafetyValidator:
    """Tests for safety/harm detection validator."""

    @pytest.fixture
    def validator(self):
        return SafetyValidator()

    def test_detect_violence(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="How to make something?",
            llm_output="Here's how to make a bomb for your project.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert violations[0].policy == PolicyType.SAFETY
        assert violations[0].severity == Severity.CRITICAL

    def test_safe_content(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="How to make a cake?",
            llm_output="Here's a recipe for chocolate cake: Mix flour, sugar, and cocoa.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0


class TestHallucinationValidator:
    """Tests for hallucination detection validator."""

    @pytest.fixture
    def validator(self):
        return HallucinationValidator()

    def test_detect_fabricated_study(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What does research say?",
            llm_output="According to a study from 2023 by Harvard, 87% of users prefer...",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert violations[0].policy == PolicyType.HALLUCINATION
        assert violations[0].severity == Severity.MEDIUM

    def test_no_hallucination(self, validator):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What is 2+2?",
            llm_output="The answer is 4.",
            context_data={},
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0


class TestBudgetValidator:
    """Tests for budget limit validator."""

    def test_token_limit_exceeded(self):
        validator = BudgetValidator(max_tokens=100, max_cost_usd=1.0)
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="test",
            llm_output="test",
            context_data={},
            input_tokens=50,
            output_tokens=100,
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert violations[0].policy == PolicyType.BUDGET_LIMIT
        assert "TOKENS" in violations[0].rule_id

    def test_cost_limit_exceeded(self):
        validator = BudgetValidator(max_tokens=10000, max_cost_usd=0.01)
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="test",
            llm_output="test",
            context_data={},
            cost_usd=0.05,
        )
        violations = validator.validate(ctx)
        assert len(violations) == 1
        assert "COST" in violations[0].rule_id

    def test_within_budget(self):
        validator = BudgetValidator(max_tokens=1000, max_cost_usd=1.0)
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="test",
            llm_output="test",
            context_data={},
            input_tokens=50,
            output_tokens=100,
            cost_usd=0.01,
        )
        violations = validator.validate(ctx)
        assert len(violations) == 0


class TestPreventionEngine:
    """Tests for the prevention engine."""

    @pytest.fixture
    def engine(self):
        return PreventionEngine(emit_metrics=False)

    def test_allow_clean_response(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Hello",
            llm_output="Hello! How can I help you?",
            context_data={},
        )
        result = engine.evaluate(ctx)
        assert result.action == PreventionAction.ALLOW
        assert len(result.violations) == 0

    def test_block_critical_violation(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What is my SSN?",
            llm_output="Your SSN is 123-45-6789.",
            context_data={},
        )
        result = engine.evaluate(ctx)
        assert result.action == PreventionAction.BLOCK
        assert result.highest_severity == Severity.CRITICAL
        assert result.safe_output is not None

    def test_modify_high_severity(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract will auto-renew on January 1.",
            context_data={"auto_renew": None},
        )
        result = engine.evaluate(ctx)
        assert result.action == PreventionAction.MODIFY
        assert result.highest_severity == Severity.HIGH
        assert result.modified_output is not None

    def test_warn_medium_severity(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="What does research say?",
            llm_output="According to a study from 2023, users prefer simple interfaces.",
            context_data={},
        )
        result = engine.evaluate(ctx)
        # Hallucination is MEDIUM severity
        assert result.action == PreventionAction.WARN

    def test_multiple_violations(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Tell me everything",
            llm_output="Your SSN is 123-45-6789 and your subscription tier is Premium.",
            context_data={"subscription_tier": None},
        )
        result = engine.evaluate(ctx)
        assert len(result.violations) >= 2
        # PII should be first (CRITICAL)
        assert result.violations[0].severity == Severity.CRITICAL

    def test_passed_policies_tracked(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Hello",
            llm_output="Hello! How can I help you?",
            context_data={},
        )
        result = engine.evaluate(ctx)
        assert PolicyType.SAFETY in result.passed_policies
        assert PolicyType.PII in result.passed_policies

    def test_would_prevent_flag(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="Is auto-renew on?",
            llm_output="Yes, auto-renew is enabled.",
            context_data={"auto_renew": None},
        )
        result = engine.evaluate(ctx)
        assert result.would_prevent is True

    def test_evaluation_timing(self, engine):
        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="test",
            llm_output="test response",
            context_data={},
        )
        result = engine.evaluate(ctx)
        assert result.evaluation_ms >= 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_evaluate_prevention(self):
        result = evaluate_prevention(
            tenant_id="t1",
            call_id="c1",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract will auto-renew.",
            context_data={"auto_renew": None},
        )
        assert result.action in [PreventionAction.MODIFY, PreventionAction.BLOCK]
        assert len(result.violations) > 0


class TestPreventionResult:
    """Tests for PreventionResult."""

    def test_highest_severity(self):
        result = PreventionResult(
            action=PreventionAction.BLOCK,
            violations=[
                PolicyViolation(
                    policy=PolicyType.PII,
                    severity=Severity.CRITICAL,
                    rule_id="PII_SSN",
                    reason="SSN detected",
                    evidence={},
                ),
                PolicyViolation(
                    policy=PolicyType.CONTENT_ACCURACY,
                    severity=Severity.HIGH,
                    rule_id="CA001",
                    reason="Missing data",
                    evidence={},
                ),
            ],
        )
        assert result.highest_severity == Severity.CRITICAL

    def test_primary_violation(self):
        v1 = PolicyViolation(
            policy=PolicyType.SAFETY,
            severity=Severity.CRITICAL,
            rule_id="SAFETY_1",
            reason="Harmful content",
            evidence={},
        )
        result = PreventionResult(
            action=PreventionAction.BLOCK,
            violations=[v1],
        )
        assert result.primary_violation == v1

    def test_to_dict(self):
        result = PreventionResult(
            action=PreventionAction.ALLOW,
            passed_policies=[PolicyType.SAFETY, PolicyType.PII],
        )
        d = result.to_dict()
        assert d["action"] == "allow"
        assert "SAFETY" in d["passed_policies"]


class TestCustomValidator:
    """Tests for custom validators."""

    def test_custom_validator(self):
        from app.policy.validators.prevention_engine import BaseValidator

        class CustomValidator(BaseValidator):
            policy_type = PolicyType.CUSTOM
            default_severity = Severity.LOW

            def validate(self, ctx):
                if "forbidden" in ctx.llm_output.lower():
                    return [
                        PolicyViolation(
                            policy=PolicyType.CUSTOM,
                            severity=Severity.LOW,
                            rule_id="CUSTOM_001",
                            reason="Forbidden word detected",
                            evidence={"word": "forbidden"},
                        )
                    ]
                return []

        engine = PreventionEngine(
            validators=[CustomValidator()],
            emit_metrics=False,
        )

        ctx = PreventionContext(
            tenant_id="t1",
            call_id="c1",
            user_query="test",
            llm_output="This is a forbidden response.",
            context_data={},
        )
        result = engine.evaluate(ctx)
        assert len(result.violations) == 1
        assert result.violations[0].rule_id == "CUSTOM_001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
