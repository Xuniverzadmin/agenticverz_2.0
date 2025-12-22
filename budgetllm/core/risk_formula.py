"""
Risk Scoring Formula for BudgetLLM Safety Governance.

Calculates overall risk score from:
- Input parameters (temperature, top_p, max_tokens)
- Output analysis signals (claims, hedging, contradictions)
- Model quality factor
- Prompt type weighting

Formula:
    risk_score = prompt_weight * (0.4 * input_risk + 0.6 * output_risk)

This produces a 0.0-1.0 score where:
- 0.0-0.3: Low risk (safe)
- 0.3-0.5: Moderate risk (acceptable)
- 0.5-0.7: Elevated risk (review recommended)
- 0.7-1.0: High risk (may be blocked)
"""

from typing import Any, Dict, Tuple


# Input risk weights
INPUT_WEIGHTS = {
    "temperature": 0.45,
    "top_p": 0.15,
    "max_tokens": 0.25,
    "model_quality": 0.15,
}

# Output risk weights
OUTPUT_WEIGHTS = {
    "unsupported_claims": 0.35,
    "hedging": 0.15,
    "self_contradiction": 0.35,
    "numeric_inconsistency": 0.15,
}

# Prompt type risk multipliers
PROMPT_TYPE_WEIGHTS = {
    "factual": 1.2,  # Highest sensitivity (facts need accuracy)
    "analytical": 1.0,
    "coding": 1.1,
    "instruction": 0.9,
    "general": 0.85,
    "opinion": 0.7,
    "creative": 0.3,  # Lowest sensitivity (creativity allows looseness)
}

# Model quality penalties (lower = better quality)
MODEL_QUALITY_PENALTY = {
    "gpt-4o": 0.0,
    "gpt-4-turbo": 0.05,
    "gpt-4": 0.05,
    "gpt-4o-mini": 0.15,
    "gpt-3.5-turbo": 0.25,
    "claude-3-opus": 0.0,
    "claude-3-5-sonnet": 0.05,
    "claude-3-sonnet": 0.1,
    "claude-3-5-haiku": 0.15,
    "claude-3-haiku": 0.2,
    "default": 0.15,
}


def calculate_risk_score(
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
        - risk_score: 0.0 to 1.0
        - risk_factors: Breakdown of contributing factors
    """
    # Calculate input risk
    input_risk, input_breakdown = _calculate_input_risk(input_params, model)

    # Calculate output risk
    output_risk, output_breakdown = _calculate_output_risk(output_signals)

    # Get prompt type weight
    prompt_weight = PROMPT_TYPE_WEIGHTS.get(prompt_type, PROMPT_TYPE_WEIGHTS["general"])

    # Calculate determinism score (for informational purposes)
    determinism = _calculate_determinism(input_params)

    # Final formula: weighted combination
    # Output risk is weighted higher (0.6) because it's based on actual content
    raw_score = 0.4 * input_risk + 0.6 * output_risk

    # Apply prompt type multiplier
    final_score = min(1.0, prompt_weight * raw_score)

    risk_factors = {
        "prompt_type": prompt_type,
        "prompt_weight": prompt_weight,
        "input_risk": round(input_risk, 3),
        "input_breakdown": input_breakdown,
        "output_risk": round(output_risk, 3),
        "output_breakdown": output_breakdown,
        "determinism_score": round(determinism, 3),
        "model": model,
        "model_penalty": MODEL_QUALITY_PENALTY.get(
            model, MODEL_QUALITY_PENALTY["default"]
        ),
    }

    return round(final_score, 3), risk_factors


def _calculate_input_risk(
    input_params: Dict[str, Any],
    model: str,
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate input parameter risk.

    Higher temperature, lower top_p, more tokens = higher risk.
    """
    temperature = input_params.get("temperature", 0.7) or 0.7
    top_p = input_params.get("top_p", 1.0) or 1.0
    max_tokens = input_params.get("max_tokens", 1000) or 1000

    # Temperature contribution (0-1 scale, higher = riskier)
    temp_risk = min(1.0, temperature)

    # Top_p contribution (only adds risk when combined with high temp)
    # top_p=1.0 is default (no restriction), lower values are more restrictive
    top_p_risk = (1.0 - top_p) * temperature

    # Max tokens contribution (normalized to 4096 as typical max)
    tokens_risk = min(1.0, max_tokens / 4096)

    # Model quality penalty
    model_risk = MODEL_QUALITY_PENALTY.get(model, MODEL_QUALITY_PENALTY["default"])

    # Weighted sum
    input_risk = (
        INPUT_WEIGHTS["temperature"] * temp_risk
        + INPUT_WEIGHTS["top_p"] * top_p_risk
        + INPUT_WEIGHTS["max_tokens"] * tokens_risk
        + INPUT_WEIGHTS["model_quality"] * model_risk
    )

    breakdown = {
        "temperature": round(temp_risk * INPUT_WEIGHTS["temperature"], 3),
        "top_p": round(top_p_risk * INPUT_WEIGHTS["top_p"], 3),
        "max_tokens": round(tokens_risk * INPUT_WEIGHTS["max_tokens"], 3),
        "model_quality": round(model_risk * INPUT_WEIGHTS["model_quality"], 3),
    }

    return input_risk, breakdown


def _calculate_output_risk(
    output_signals: Dict[str, float],
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate output content risk.
    """
    unsupported = output_signals.get("unsupported_claims", 0.0)
    hedging = output_signals.get("hedging", 0.0)
    contradiction = output_signals.get("self_contradiction", 0.0)
    numeric = output_signals.get("numeric_inconsistency", 0.0)

    # Weighted sum
    output_risk = (
        OUTPUT_WEIGHTS["unsupported_claims"] * unsupported
        + OUTPUT_WEIGHTS["hedging"] * hedging
        + OUTPUT_WEIGHTS["self_contradiction"] * contradiction
        + OUTPUT_WEIGHTS["numeric_inconsistency"] * numeric
    )

    breakdown = {
        "unsupported_claims": round(
            unsupported * OUTPUT_WEIGHTS["unsupported_claims"], 3
        ),
        "hedging": round(hedging * OUTPUT_WEIGHTS["hedging"], 3),
        "self_contradiction": round(
            contradiction * OUTPUT_WEIGHTS["self_contradiction"], 3
        ),
        "numeric_inconsistency": round(
            numeric * OUTPUT_WEIGHTS["numeric_inconsistency"], 3
        ),
    }

    return output_risk, breakdown


def _calculate_determinism(input_params: Dict[str, Any]) -> float:
    """
    Calculate determinism score (higher = more deterministic).

    This is informational - helps users understand output predictability.
    """
    temperature = input_params.get("temperature", 0.7) or 0.7
    top_p = input_params.get("top_p", 1.0) or 1.0

    # Temperature is the dominant factor
    # temp=0 → determinism=1.0, temp=1.0 → determinism=0.0
    temp_factor = 1.0 - min(1.0, temperature)

    # Top_p only matters when temperature > 0
    # Lower top_p with temp > 0 increases determinism slightly
    top_p_factor = 1.0 - (1.0 - top_p) * min(1.0, temperature) * 0.5

    # Weight temperature more heavily
    determinism = 0.7 * temp_factor + 0.3 * top_p_factor

    return determinism


def get_risk_level(score: float) -> str:
    """
    Get human-readable risk level from score.
    """
    if score < 0.3:
        return "low"
    elif score < 0.5:
        return "moderate"
    elif score < 0.7:
        return "elevated"
    else:
        return "high"


def get_risk_level_description(score: float) -> str:
    """
    Get detailed risk level description.
    """
    level = get_risk_level(score)

    descriptions = {
        "low": "Output appears reliable. Low hallucination risk.",
        "moderate": "Output is acceptable. Some uncertainty present.",
        "elevated": "Review recommended. Higher potential for inaccuracies.",
        "high": "Caution advised. High potential for hallucination or errors.",
    }

    return descriptions[level]
