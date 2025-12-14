"""
Tests for BudgetLLM Safety Governance features.

Tests:
- Prompt classification
- Output analysis
- Risk scoring formula
- SafetyController
- Parameter clamping
- Safety enforcement
- Integration with Client

Run with: pytest tests/test_safety_governance.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# PROMPT CLASSIFIER TESTS
# =============================================================================

class TestPromptClassifier:
    """Tests for prompt classification."""

    def test_factual_prompt_classification(self):
        """Factual prompts should be classified correctly."""
        from budgetllm.core.prompt_classifier import classify_prompt

        messages = [{"role": "user", "content": "What is machine learning?"}]
        prompt_type, confidence = classify_prompt(messages)

        assert prompt_type == "factual"
        assert confidence > 0.5

    def test_creative_prompt_classification(self):
        """Creative prompts should be classified correctly."""
        from budgetllm.core.prompt_classifier import classify_prompt

        messages = [{"role": "user", "content": "Write a poem about the ocean"}]
        prompt_type, confidence = classify_prompt(messages)

        assert prompt_type == "creative"
        assert confidence > 0.5

    def test_coding_prompt_classification(self):
        """Coding prompts should be classified correctly."""
        from budgetllm.core.prompt_classifier import classify_prompt

        messages = [{"role": "user", "content": "Write a Python function to sort a list"}]
        prompt_type, confidence = classify_prompt(messages)

        assert prompt_type == "coding"
        assert confidence > 0.5

    def test_analytical_prompt_classification(self):
        """Analytical prompts should be classified correctly."""
        from budgetllm.core.prompt_classifier import classify_prompt

        messages = [{"role": "user", "content": "Compare the pros and cons of electric cars versus gasoline cars"}]
        prompt_type, confidence = classify_prompt(messages)

        assert prompt_type == "analytical"
        assert confidence > 0.5

    def test_empty_messages_returns_general(self):
        """Empty messages should return general type."""
        from budgetllm.core.prompt_classifier import classify_prompt

        messages = []
        prompt_type, confidence = classify_prompt(messages)

        assert prompt_type == "general"

    def test_unclassified_prompt_returns_general(self):
        """Unclassified prompts should return general."""
        from budgetllm.core.prompt_classifier import classify_prompt

        messages = [{"role": "user", "content": "Hello there"}]
        prompt_type, confidence = classify_prompt(messages)

        assert prompt_type == "general"


# =============================================================================
# OUTPUT ANALYSIS TESTS
# =============================================================================

class TestOutputAnalysis:
    """Tests for output analysis."""

    def test_unsupported_claims_detection(self):
        """Should detect unsupported claims."""
        from budgetllm.core.output_analysis import analyze_output

        text = "Studies show that 90% of people prefer this method."
        signals = analyze_output(text)

        assert signals["unsupported_claims"] > 0

    def test_citations_reduce_unsupported_score(self):
        """Citations should reduce unsupported claims score."""
        from budgetllm.core.output_analysis import analyze_output

        text = "Studies show that 90% of people prefer this method [1]."
        signals = analyze_output(text)

        assert signals["unsupported_claims"] == 0.0

    def test_hedging_detection(self):
        """Should detect hedging language."""
        from budgetllm.core.output_analysis import analyze_output

        text = "I think this might be correct, probably, but I'm not sure."
        signals = analyze_output(text)

        assert signals["hedging"] > 0

    def test_clean_output_low_risk(self):
        """Clean output should have low risk signals."""
        from budgetllm.core.output_analysis import analyze_output

        text = "Python is a programming language. It was created by Guido van Rossum."
        signals = analyze_output(text)

        assert signals["unsupported_claims"] == 0.0
        assert signals["hedging"] < 0.3
        assert signals["self_contradiction"] == 0.0

    def test_empty_text_returns_zeros(self):
        """Empty text should return all zeros."""
        from budgetllm.core.output_analysis import analyze_output

        signals = analyze_output("")

        assert signals["unsupported_claims"] == 0.0
        assert signals["hedging"] == 0.0
        assert signals["self_contradiction"] == 0.0
        assert signals["numeric_inconsistency"] == 0.0


# =============================================================================
# RISK FORMULA TESTS
# =============================================================================

class TestRiskFormula:
    """Tests for risk scoring formula."""

    def test_low_risk_calculation(self):
        """Low temperature + clean output = low risk."""
        from budgetllm.core.risk_formula import calculate_risk_score

        risk_score, factors = calculate_risk_score(
            prompt_type="general",
            input_params={"temperature": 0.2, "top_p": 1.0, "max_tokens": 100},
            output_signals={
                "unsupported_claims": 0.0,
                "hedging": 0.0,
                "self_contradiction": 0.0,
                "numeric_inconsistency": 0.0,
            },
            model="gpt-4o",
        )

        assert risk_score < 0.3

    def test_high_risk_calculation(self):
        """High temperature + risky output = high risk."""
        from budgetllm.core.risk_formula import calculate_risk_score

        risk_score, factors = calculate_risk_score(
            prompt_type="factual",  # Higher weight for factual
            input_params={"temperature": 1.0, "top_p": 0.5, "max_tokens": 2000},
            output_signals={
                "unsupported_claims": 0.8,
                "hedging": 0.5,
                "self_contradiction": 0.3,
                "numeric_inconsistency": 0.2,
            },
            model="gpt-3.5-turbo",  # Lower quality model
        )

        assert risk_score > 0.5

    def test_creative_prompt_lower_risk(self):
        """Creative prompts should have lower risk multiplier."""
        from budgetllm.core.risk_formula import calculate_risk_score

        # Same parameters, different prompt types
        factual_score, _ = calculate_risk_score(
            prompt_type="factual",
            input_params={"temperature": 0.7, "top_p": 1.0, "max_tokens": 500},
            output_signals={"unsupported_claims": 0.3, "hedging": 0.2, "self_contradiction": 0.0, "numeric_inconsistency": 0.0},
            model="gpt-4o-mini",
        )

        creative_score, _ = calculate_risk_score(
            prompt_type="creative",
            input_params={"temperature": 0.7, "top_p": 1.0, "max_tokens": 500},
            output_signals={"unsupported_claims": 0.3, "hedging": 0.2, "self_contradiction": 0.0, "numeric_inconsistency": 0.0},
            model="gpt-4o-mini",
        )

        assert creative_score < factual_score

    def test_model_quality_affects_risk(self):
        """Lower quality models should increase risk."""
        from budgetllm.core.risk_formula import calculate_risk_score

        gpt4_score, _ = calculate_risk_score(
            prompt_type="factual",
            input_params={"temperature": 0.5, "top_p": 1.0, "max_tokens": 500},
            output_signals={"unsupported_claims": 0.0, "hedging": 0.0, "self_contradiction": 0.0, "numeric_inconsistency": 0.0},
            model="gpt-4o",
        )

        gpt35_score, _ = calculate_risk_score(
            prompt_type="factual",
            input_params={"temperature": 0.5, "top_p": 1.0, "max_tokens": 500},
            output_signals={"unsupported_claims": 0.0, "hedging": 0.0, "self_contradiction": 0.0, "numeric_inconsistency": 0.0},
            model="gpt-3.5-turbo",
        )

        assert gpt35_score > gpt4_score

    def test_risk_factors_breakdown(self):
        """Risk factors should include detailed breakdown."""
        from budgetllm.core.risk_formula import calculate_risk_score

        risk_score, factors = calculate_risk_score(
            prompt_type="factual",
            input_params={"temperature": 0.5, "top_p": 1.0, "max_tokens": 500},
            output_signals={"unsupported_claims": 0.1, "hedging": 0.1, "self_contradiction": 0.0, "numeric_inconsistency": 0.0},
            model="gpt-4o-mini",
        )

        assert "prompt_type" in factors
        assert "input_risk" in factors
        assert "output_risk" in factors
        assert "determinism_score" in factors
        assert "input_breakdown" in factors
        assert "output_breakdown" in factors


# =============================================================================
# SAFETY CONTROLLER TESTS
# =============================================================================

class TestSafetyController:
    """Tests for SafetyController class."""

    def test_parameter_clamping(self):
        """Parameters should be clamped to limits."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController(
            max_temperature=0.7,
            max_top_p=0.9,
            max_tokens=500,
        )

        temp, top_p, max_tokens = controller.clamp_params(1.2, 1.0, 1000)

        assert temp == 0.7
        assert top_p == 0.9
        assert max_tokens == 500

    def test_clamping_not_needed(self):
        """Values below limits should not be clamped."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController(
            max_temperature=1.0,
            max_top_p=1.0,
            max_tokens=4096,
        )

        temp, top_p, max_tokens = controller.clamp_params(0.5, 0.9, 500)

        assert temp == 0.5
        assert top_p == 0.9
        assert max_tokens == 500

    def test_was_clamped_detection(self):
        """Should detect which parameters were clamped."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController(max_temperature=0.7)

        clamped = controller.was_clamped(
            original_temp=1.0, original_top_p=None, original_max_tokens=None,
            clamped_temp=0.7, clamped_top_p=None, clamped_max_tokens=None,
        )

        assert "temperature" in clamped
        assert clamped["temperature"]["original"] == 1.0
        assert clamped["temperature"]["clamped_to"] == 0.7

    def test_enforce_disabled_by_default(self):
        """Enforcement should be disabled by default."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController(enforce_safety=False)

        # Should not raise even with high risk
        controller.enforce(risk_score=0.9, risk_factors={})

    def test_enforce_raises_on_high_risk(self):
        """Enforcement should raise when risk exceeds threshold."""
        from budgetllm.core.safety import SafetyController, HighRiskOutputError

        controller = SafetyController(
            enforce_safety=True,
            block_on_high_risk=True,
            risk_threshold=0.5,
        )

        with pytest.raises(HighRiskOutputError) as exc:
            controller.enforce(risk_score=0.7, risk_factors={"test": "data"})

        assert exc.value.risk_score == 0.7
        assert "test" in exc.value.risk_factors

    def test_enforce_allows_below_threshold(self):
        """Enforcement should allow below threshold."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController(
            enforce_safety=True,
            block_on_high_risk=True,
            risk_threshold=0.5,
        )

        # Should not raise
        controller.enforce(risk_score=0.3, risk_factors={})

    def test_correction_suggestions(self):
        """Should generate correction suggestions."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController()

        suggestions = controller.get_correction_suggestions(
            risk_score=0.6,
            temperature=0.9,
            top_p=1.0,
            prompt_type="factual",
        )

        assert len(suggestions) > 0
        assert any("temperature" in s.lower() for s in suggestions)


# =============================================================================
# CLIENT INTEGRATION TESTS
# =============================================================================

class TestClientSafetyIntegration:
    """Tests for safety governance integration with Client."""

    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI client."""
        mock_openai_module = MagicMock()

        mock_response = MagicMock()
        mock_response.id = "chatcmpl-safety-test"
        mock_response.model = "gpt-4o-mini"
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response."
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 8

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            yield mock_openai_module, mock_client

    def test_response_includes_risk_score(self, mock_openai):
        """Response should include risk_score."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)
        response = client.chat("What is Python?")

        assert "risk_score" in response
        assert isinstance(response["risk_score"], float)
        assert 0.0 <= response["risk_score"] <= 1.0

    def test_response_includes_risk_factors(self, mock_openai):
        """Response should include risk_factors breakdown."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(openai_key="test-key", budget_cents=1000)
        response = client.chat("What is Python?")

        assert "risk_factors" in response
        assert "prompt_type" in response["risk_factors"]

    def test_parameter_clamping_in_client(self, mock_openai):
        """Client should clamp parameters."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(
            openai_key="test-key",
            budget_cents=1000,
            max_temperature=0.5,
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=1.0,  # Should be clamped to 0.5
        )

        # Check that OpenAI was called with clamped temperature
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.5

    def test_params_clamped_in_response(self, mock_openai):
        """Response should indicate which params were clamped."""
        mock_module, mock_client = mock_openai
        from budgetllm import Client

        client = Client(
            openai_key="test-key",
            budget_cents=1000,
            max_temperature=0.5,
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=1.0,  # Will be clamped
        )

        assert "params_clamped" in response
        assert "temperature" in response["params_clamped"]

    def test_safety_enforcement_blocks_high_risk(self, mock_openai):
        """Safety enforcement should block high-risk outputs."""
        mock_module, mock_client = mock_openai

        # Make mock return very risky content with many risk signals
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices[0].message.content = (
            "Studies show that this is always true. Research indicates "
            "everyone agrees. Experts say this is proven. Data shows "
            "100% of people and also 0% of people agree. I think maybe "
            "probably approximately this might be correct perhaps."
        )

        from budgetllm import Client, HighRiskOutputError

        client = Client(
            openai_key="test-key",
            budget_cents=1000,
            enforce_safety=True,
            risk_threshold=0.15,  # Very low threshold to trigger
        )

        # Should raise HighRiskOutputError
        with pytest.raises(HighRiskOutputError):
            client.chat.completions.create(
                model="gpt-3.5-turbo",  # Lower quality model adds risk
                messages=[{"role": "user", "content": "What is the exact GDP of every country?"}],  # Factual prompt
                temperature=1.0,  # High temperature adds risk
            )

    def test_safety_enforcement_disabled_allows_all(self, mock_openai):
        """Disabled safety enforcement should allow all outputs."""
        mock_module, mock_client = mock_openai

        # Make mock return risky content
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices[0].message.content = (
            "Studies show that this is always true. Research indicates everyone agrees."
        )

        from budgetllm import Client

        client = Client(
            openai_key="test-key",
            budget_cents=1000,
            enforce_safety=False,  # Disabled
        )

        # Should NOT raise
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Give me facts"}],
            temperature=1.0,
        )

        assert "risk_score" in response


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_none_parameters_handling(self):
        """Should handle None parameters gracefully."""
        from budgetllm.core.safety import SafetyController

        controller = SafetyController()
        temp, top_p, max_tokens = controller.clamp_params(None, None, None)

        assert temp is None
        assert top_p is None
        assert max_tokens is None

    def test_empty_messages_classification(self):
        """Should handle empty messages."""
        from budgetllm.core.prompt_classifier import classify_prompt

        prompt_type, confidence = classify_prompt([])
        assert prompt_type == "general"

    def test_unicode_content_analysis(self):
        """Should handle unicode content."""
        from budgetllm.core.output_analysis import analyze_output

        text = "研究表明这是正确的。This probably might be true. 🤖"
        signals = analyze_output(text)

        assert "hedging" in signals
        assert "unsupported_claims" in signals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
