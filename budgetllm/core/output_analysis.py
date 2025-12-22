"""
Output Analysis Module for BudgetLLM Safety Governance.

Analyzes LLM output for risk signals:
- Unsupported claims (assertions without evidence)
- Hedging language (uncertainty markers)
- Self-contradiction (conflicting statements)
- Numeric inconsistency (conflicting numbers)

These are HEURISTICS, not ground truth. Use for guidance, not absolute decisions.
"""

import re
from typing import Dict, List


# Hedging/uncertainty phrases
HEDGING_PHRASES = [
    "i think",
    "probably",
    "likely",
    "might be",
    "could be",
    "possibly",
    "perhaps",
    "maybe",
    "i'm not sure",
    "i believe",
    "it seems",
    "appears to",
    "approximately",
    "roughly",
    "about",
    "around",
    "estimated",
    "as far as i know",
    "to my knowledge",
    "i'm uncertain",
]

# Patterns suggesting unsupported claims
UNSUPPORTED_CLAIM_PATTERNS = [
    r"studies show",
    r"research shows",
    r"experts say",
    r"scientists say",
    r"according to experts",
    r"research indicates",
    r"data shows",
    r"statistics show",
    r"evidence suggests",
    r"it is proven",
    r"it has been proven",
    r"it is well known",
    r"everyone knows",
]

# Patterns suggesting citations ARE present (reduces unsupported claim score)
CITATION_PATTERNS = [
    r"\[\d+\]",  # [1], [2], etc.
    r"\(\d{4}\)",  # (2024), etc.
    r"according to [\w\s]+,",  # According to Smith,
    r"source:",
    r"reference:",
    r"cited from",
    r"as stated in",
]

# Contradiction indicators (actual contradictions, not just transition words)
CONTRADICTION_PAIRS = [
    (r"always", r"never"),
    (r"all", r"none"),
    (r"everyone", r"no one"),
    (r"is true", r"is false"),
    (r"is correct", r"is incorrect"),
    (r"increases", r"decreases"),
    (r"more than", r"less than"),
]


def analyze_output(text: str) -> Dict[str, float]:
    """
    Analyze output content for risk signals.

    Args:
        text: The LLM output text to analyze

    Returns:
        Dict of signal_name -> signal_value (0.0-1.0)
        - unsupported_claims: Likelihood of unverified assertions
        - hedging: Amount of uncertainty language
        - self_contradiction: Likelihood of conflicting statements
        - numeric_inconsistency: Conflicting numeric values
    """
    if not text or not text.strip():
        return {
            "unsupported_claims": 0.0,
            "hedging": 0.0,
            "self_contradiction": 0.0,
            "numeric_inconsistency": 0.0,
        }

    text_lower = text.lower()

    return {
        "unsupported_claims": _score_unsupported_claims(text_lower),
        "hedging": _score_hedging(text_lower),
        "self_contradiction": _score_contradictions(text_lower),
        "numeric_inconsistency": _score_numeric_inconsistency(text),
    }


def _score_unsupported_claims(text: str) -> float:
    """
    Score likelihood of unsupported claims (0.0-1.0).

    Looks for phrases like "studies show" without citations.
    """
    # Count claim patterns
    claim_count = 0
    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        matches = len(re.findall(pattern, text, re.IGNORECASE))
        claim_count += matches

    if claim_count == 0:
        return 0.0

    # Check for citations
    citation_count = 0
    for pattern in CITATION_PATTERNS:
        matches = len(re.findall(pattern, text, re.IGNORECASE))
        citation_count += matches

    # If citations present, reduce score
    if citation_count >= claim_count:
        return 0.0
    elif citation_count > 0:
        return min(1.0, (claim_count - citation_count) * 0.2)
    else:
        # No citations for claims
        return min(1.0, claim_count * 0.3)


def _score_hedging(text: str) -> float:
    """
    Score amount of hedging/uncertainty language (0.0-1.0).

    Some hedging is appropriate (honest uncertainty).
    Excessive hedging suggests low confidence.
    """
    word_count = len(text.split())
    if word_count == 0:
        return 0.0

    hedging_count = 0
    for phrase in HEDGING_PHRASES:
        if phrase in text:
            hedging_count += text.count(phrase)

    # Normalize by text length
    # ~5% hedging words is normal, >15% is high
    hedging_ratio = hedging_count / (word_count / 10)  # Per 10 words

    if hedging_ratio < 0.5:
        return 0.0
    elif hedging_ratio < 1.0:
        return 0.2
    elif hedging_ratio < 2.0:
        return 0.4
    else:
        return min(1.0, hedging_ratio * 0.2)


def _score_contradictions(text: str) -> float:
    """
    Score likelihood of self-contradiction (0.0-1.0).

    Looks for actual contradictory statements, not just transition words.
    """
    contradiction_score = 0.0

    for pattern_a, pattern_b in CONTRADICTION_PAIRS:
        has_a = bool(re.search(pattern_a, text, re.IGNORECASE))
        has_b = bool(re.search(pattern_b, text, re.IGNORECASE))

        if has_a and has_b:
            # Both contradictory terms present
            contradiction_score += 0.25

    # Also check for explicit contradiction markers
    explicit_markers = [
        r"this contradicts",
        r"wait,? no",
        r"actually,? that's wrong",
        r"let me correct",
        r"i made an error",
        r"that was incorrect",
    ]

    for marker in explicit_markers:
        if re.search(marker, text, re.IGNORECASE):
            contradiction_score += 0.3

    return min(1.0, contradiction_score)


def _score_numeric_inconsistency(text: str) -> float:
    """
    Score numeric inconsistency in output (0.0-1.0).

    Looks for conflicting numbers that should be the same.
    """
    # Extract all numbers with context
    number_pattern = r"(\d+(?:\.\d+)?)\s*(%|percent|dollars?|euros?|pounds?|usd|eur|gbp|million|billion|trillion)?"
    matches = re.findall(number_pattern, text, re.IGNORECASE)

    if len(matches) < 2:
        return 0.0

    # Group numbers by unit type
    numbers_by_unit: Dict[str, List[float]] = {}
    for value, unit in matches:
        unit_key = (unit or "none").lower()
        try:
            numbers_by_unit.setdefault(unit_key, []).append(float(value))
        except ValueError:
            continue

    # Check for inconsistency within same unit type
    inconsistency_score = 0.0

    for unit, values in numbers_by_unit.items():
        if len(values) < 2:
            continue

        # Check if values vary significantly (>50% difference)
        min_val = min(values)
        max_val = max(values)

        if min_val > 0:
            variance_ratio = (max_val - min_val) / min_val
            if variance_ratio > 0.5:
                inconsistency_score += 0.2

    return min(1.0, inconsistency_score)


def get_risk_signals_summary(signals: Dict[str, float]) -> str:
    """
    Generate human-readable summary of risk signals.

    Args:
        signals: Dict from analyze_output()

    Returns:
        Human-readable summary string
    """
    parts = []

    if signals.get("unsupported_claims", 0) > 0.3:
        parts.append("contains unsupported claims")

    if signals.get("hedging", 0) > 0.4:
        parts.append("high uncertainty language")

    if signals.get("self_contradiction", 0) > 0.2:
        parts.append("potential self-contradiction")

    if signals.get("numeric_inconsistency", 0) > 0.3:
        parts.append("numeric inconsistency detected")

    if not parts:
        return "No significant risk signals detected"

    return "Risk signals: " + ", ".join(parts)
