"""
Prompt Type Classifier for BudgetLLM Safety Governance.

Classifies user prompts into categories to adjust risk scoring.
Factual queries need high accuracy, creative queries can be loose.

Categories:
- factual: "What is X?", "Explain Y", "Define Z"
- analytical: "Compare X and Y", "Analyze Z"
- coding: Code generation, debugging, technical
- instruction: "How to do X", step-by-step guides
- opinion: "What do you think?", subjective
- creative: Stories, poems, imaginative content
- general: Default catch-all
"""

import re
from typing import Dict, List, Tuple


# Pattern definitions with weights
# Higher weight = stronger signal for that category
PATTERNS = {
    "factual": [
        (r"\bwhat is\b", 0.8),
        (r"\bwhat are\b", 0.8),
        (r"\bwho is\b", 0.8),
        (r"\bwho was\b", 0.8),
        (r"\bwhen did\b", 0.7),
        (r"\bwhere is\b", 0.7),
        (r"\bexplain\b", 0.7),
        (r"\bdefine\b", 0.8),
        (r"\bdescribe\b", 0.6),
        (r"\bsummarize\b", 0.7),
        (r"\blist\b", 0.5),
        (r"\bfacts about\b", 0.9),
        (r"\btell me about\b", 0.6),
        (r"\bhow many\b", 0.7),
        (r"\bhow much\b", 0.7),
    ],
    "analytical": [
        (r"\bcompare\b", 0.8),
        (r"\bcontrast\b", 0.8),
        (r"\banalyze\b", 0.9),
        (r"\bevaluate\b", 0.8),
        (r"\bassess\b", 0.7),
        (r"\bdifference between\b", 0.8),
        (r"\bpros and cons\b", 0.9),
        (r"\badvantages\b", 0.6),
        (r"\bdisadvantages\b", 0.6),
        (r"\bwhy does\b", 0.5),
        (r"\bwhy is\b", 0.5),
    ],
    "coding": [
        (r"\bwrite code\b", 0.9),
        (r"\bwrite a function\b", 0.9),
        (r"\bpython\b", 0.6),
        (r"\bjavascript\b", 0.6),
        (r"\btypescript\b", 0.6),
        (r"\bjava\b", 0.5),
        (r"\brust\b", 0.5),
        (r"\bsql\b", 0.6),
        (r"\bcode\b", 0.5),
        (r"\bfunction\b", 0.4),
        (r"\bclass\b", 0.4),
        (r"\bdebug\b", 0.8),
        (r"\bfix this\b", 0.6),
        (r"\bbugfix\b", 0.8),
        (r"\brefactor\b", 0.7),
        (r"\bimplement\b", 0.6),
        (r"\balgorithm\b", 0.7),
        (r"```", 0.7),  # Code blocks
    ],
    "instruction": [
        (r"\bhow to\b", 0.8),
        (r"\bhow do i\b", 0.8),
        (r"\bhow can i\b", 0.7),
        (r"\bsteps to\b", 0.8),
        (r"\bguide\b", 0.6),
        (r"\btutorial\b", 0.7),
        (r"\binstruct\b", 0.7),
        (r"\bwalkthrough\b", 0.7),
    ],
    "opinion": [
        (r"\bwhat do you think\b", 0.9),
        (r"\byour opinion\b", 0.9),
        (r"\bdo you believe\b", 0.8),
        (r"\bshould i\b", 0.6),
        (r"\bwould you recommend\b", 0.7),
        (r"\bbest\b", 0.3),  # Weak signal
        (r"\bworst\b", 0.3),
    ],
    "creative": [
        (r"\bwrite a story\b", 0.9),
        (r"\bwrite a poem\b", 0.9),
        (r"\bcreative\b", 0.7),
        (r"\bimagine\b", 0.8),
        (r"\bfiction\b", 0.8),
        (r"\bstory about\b", 0.9),
        (r"\bonce upon a time\b", 0.9),
        (r"\bwrite me a\b", 0.5),
        (r"\bbrainstorm\b", 0.6),
        (r"\bideas for\b", 0.5),
    ],
}


def classify_prompt(messages: List[Dict[str, str]]) -> Tuple[str, float]:
    """
    Classify prompt type based on user message patterns.

    Args:
        messages: List of message dicts with role and content

    Returns:
        Tuple of (prompt_type, confidence)
        - prompt_type: One of factual, analytical, coding, instruction, opinion, creative, general
        - confidence: 0.0 to 1.0 indicating classification confidence
    """
    # Extract user messages only
    user_text = " ".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    ).lower()

    if not user_text.strip():
        return "general", 0.5

    # Score each category
    scores: Dict[str, float] = {}

    for category, patterns in PATTERNS.items():
        category_score = 0.0
        matches = 0

        for pattern, weight in patterns:
            if re.search(pattern, user_text, re.IGNORECASE):
                category_score += weight
                matches += 1

        if matches > 0:
            # Use raw score (not normalized) - patterns have different weights
            scores[category] = category_score

    if not scores:
        return "general", 0.5

    # Find best match
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # Calculate confidence based on margin over second-best
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) > 1:
        margin = sorted_scores[0] - sorted_scores[1]
        confidence = min(1.0, 0.5 + margin * 0.5)
    else:
        confidence = min(1.0, 0.5 + best_score * 0.3)

    # If score is too low, return general
    if best_score < 0.5:
        return "general", 0.5

    return best_category, round(confidence, 2)


def get_prompt_type_description(prompt_type: str) -> str:
    """Get human-readable description of prompt type."""
    descriptions = {
        "factual": "Factual query requiring accurate, verifiable information",
        "analytical": "Analytical query requiring comparison or evaluation",
        "coding": "Code generation or technical programming task",
        "instruction": "How-to or step-by-step instruction request",
        "opinion": "Subjective opinion or recommendation request",
        "creative": "Creative writing or imaginative content",
        "general": "General query (unclassified)",
    }
    return descriptions.get(prompt_type, "Unknown prompt type")
