"""
Safety Governance Controller for BudgetLLM.

Provides hallucination risk scoring, parameter clamping, and safety enforcement.
This is the core "LLM Governor" that makes BudgetLLM unique.

Usage:
    from budgetllm.core.safety import SafetyController, HighRiskOutputError

    controller = SafetyController(
        max_temperature=0.7,
        risk_threshold=0.6,
        enforce_safety=True,
    )

    # Clamp parameters
    temp, top_p, max_tokens = controller.clamp_params(1.2, 0.9, 500)

    # Score risk after getting response
    risk_score, risk_factors = controller.score_risk(
        prompt_type="factual",
        input_params={"temperature": 0.7, "top_p": 0.9, "max_tokens": 300},
        output_signals={"unsupported_claims": 0.0, "vagueness": 0.2},
        model="gpt-4o-mini",
    )

    # Enforce (raises if risk too high)
    controller.enforce(risk_score)
"""

from typing import Any, Dict, List, Optional, Tuple


class HighRiskOutputError(Exception):
    """Raised when output risk exceeds configured threshold."""

    def __init__(self, message: str, risk_score: float, risk_factors: Dict[str, Any]):
        super().__init__(message)
        self.risk_score = risk_score
        self.risk_factors = risk_factors


# Model quality penalties (lower = better quality, less risk)
MODEL_QUALITY_PENALTY = {
    # OpenAI
    "gpt-4o": 0.0,
    "gpt-4-turbo": 0.05,
    "gpt-4": 0.05,
    "gpt-4o-mini": 0.15,
    "gpt-3.5-turbo": 0.25,
    # Anthropic (future)
    "claude-3-opus": 0.0,
    "claude-3-5-sonnet": 0.05,
    "claude-3-sonnet": 0.1,
    "claude-3-5-haiku": 0.15,
    "claude-3-haiku": 0.2,
    # Default
    "default": 0.15,
}

# Prompt type risk multipliers
# Higher = more sensitive to risk (factual queries need accuracy)
# Lower = more tolerant (creative writing can be loose)
PROMPT_TYPE_WEIGHTS = {
    "factual": 1.2,
    "analytical": 1.0,
    "coding": 1.1,
    "instruction": 0.9,
    "general": 0.85,
    "opinion": 0.7,
    "creative": 0.3,
}


class SafetyController:
    """
    Safety governance controller for LLM requests.

    Controls:
    - Parameter clamping (temperature, top_p, max_tokens)
    - Risk scoring (input + output analysis)
    - Safety enforcement (block high-risk outputs)

    This is NOT auto-correction (that's disabled).
    This is governance - measuring and enforcing limits.
    """

    def __init__(
        self,
        max_temperature: float = 1.0,
        max_top_p: float = 1.0,
        max_tokens: int = 4096,
        enforce_safety: bool = False,  # Opt-in by default
        block_on_high_risk: bool = True,
        risk_threshold: float = 0.6,
    ):
        """
        Initialize SafetyController.

        Args:
            max_temperature: Maximum allowed temperature (clamped)
            max_top_p: Maximum allowed top_p (clamped)
            max_tokens: Maximum allowed completion tokens (clamped)
            enforce_safety: If True, enforce risk threshold
            block_on_high_risk: If True, raise error when risk > threshold
            risk_threshold: Risk score threshold (0.0-1.0)
        """
        self.max_temperature = max_temperature
        self.max_top_p = max_top_p
        self.max_tokens = max_tokens
        self.enforce_safety = enforce_safety
        self.block_on_high_risk = block_on_high_risk
        self.risk_threshold = risk_threshold

    def clamp_params(
        self,
        temperature: Optional[float],
        top_p: Optional[float],
        max_tokens: Optional[int],
    ) -> Tuple[Optional[float], Optional[float], Optional[int]]:
        """
        Clamp input parameters to configured limits.

        Returns:
            Tuple of (clamped_temperature, clamped_top_p, clamped_max_tokens)
        """
        clamped_temp = temperature
        clamped_top_p = top_p
        clamped_max_tokens = max_tokens

        if temperature is not None:
            clamped_temp = min(temperature, self.max_temperature)

        if top_p is not None:
            clamped_top_p = min(top_p, self.max_top_p)

        if max_tokens is not None:
            clamped_max_tokens = min(max_tokens, self.max_tokens)

        return clamped_temp, clamped_top_p, clamped_max_tokens

    def was_clamped(
        self,
        original_temp: Optional[float],
        original_top_p: Optional[float],
        original_max_tokens: Optional[int],
        clamped_temp: Optional[float],
        clamped_top_p: Optional[float],
        clamped_max_tokens: Optional[int],
    ) -> Dict[str, Any]:
        """
        Check if any parameters were clamped and return details.

        Returns:
            Dict with clamping info
        """
        clamped = {}

        if original_temp is not None and clamped_temp != original_temp:
            clamped["temperature"] = {
                "original": original_temp,
                "clamped_to": clamped_temp,
            }

        if original_top_p is not None and clamped_top_p != original_top_p:
            clamped["top_p"] = {
                "original": original_top_p,
                "clamped_to": clamped_top_p,
            }

        if (
            original_max_tokens is not None
            and clamped_max_tokens != original_max_tokens
        ):
            clamped["max_tokens"] = {
                "original": original_max_tokens,
                "clamped_to": clamped_max_tokens,
            }

        return clamped

    def classify_prompt(self, messages: List[Dict[str, str]]) -> Tuple[str, float]:
        """
        Classify prompt type from messages.

        Returns:
            Tuple of (prompt_type, confidence)
        """
        from budgetllm.core.prompt_classifier import classify_prompt

        return classify_prompt(messages)

    def analyze_output(self, content: str) -> Dict[str, float]:
        """
        Analyze output content for risk signals.

        Returns:
            Dict of signal_name -> signal_value (0.0-1.0)
        """
        from budgetllm.core.output_analysis import analyze_output

        return analyze_output(content)

    def score_risk(
        self,
        prompt_type: str,
        input_params: Dict[str, Any],
        output_signals: Dict[str, float],
        model: str,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate overall risk score.

        Args:
            prompt_type: Type of prompt (factual, creative, etc.)
            input_params: Dict with temperature, top_p, max_tokens
            output_signals: Dict from analyze_output()
            model: Model name

        Returns:
            Tuple of (risk_score, risk_factors)
        """
        from budgetllm.core.risk_formula import calculate_risk_score

        return calculate_risk_score(
            prompt_type=prompt_type,
            input_params=input_params,
            output_signals=output_signals,
            model=model,
        )

    def enforce(self, risk_score: float, risk_factors: Dict[str, Any]) -> None:
        """
        Enforce safety threshold.

        Raises:
            HighRiskOutputError: If risk exceeds threshold and enforcement enabled
        """
        if not self.enforce_safety:
            return

        if self.block_on_high_risk and risk_score > self.risk_threshold:
            raise HighRiskOutputError(
                f"Output blocked: risk score {risk_score:.2f} exceeds threshold {self.risk_threshold}",
                risk_score=risk_score,
                risk_factors=risk_factors,
            )

    def get_correction_suggestions(
        self,
        risk_score: float,
        temperature: Optional[float],
        top_p: Optional[float],
        prompt_type: str,
    ) -> List[str]:
        """
        Generate correction suggestions (informational only, not auto-applied).

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if risk_score > 0.5:
            if temperature is not None and temperature > 0.7:
                suggestions.append(
                    f"Consider lowering temperature from {temperature} to 0.5 for more stable output."
                )

            if (
                prompt_type == "factual"
                and temperature is not None
                and temperature > 0.3
            ):
                suggestions.append(
                    "For factual queries, temperature=0.2 or lower produces more reliable answers."
                )

        if risk_score > 0.7:
            suggestions.append(
                "High risk detected. Consider using a higher-quality model (e.g., gpt-4o)."
            )

        return suggestions
