"""
Customer Integration Cost Calculator

PURPOSE:
    Deterministic, table-driven cost calculation for LLM providers.
    Provides accurate cost estimation for billing and governance.

SEMANTIC:
    Cost calculation is FACTUAL and DETERMINISTIC.
    - Table-driven: No magic strings or hard-coded values
    - Versioned: Pricing tables are timestamped
    - Auditable: All calculations are reproducible

SUPPORTED PROVIDERS:
    - OpenAI: All GPT-4, GPT-4o, GPT-3.5, o1 models
    - Anthropic: All Claude 3, 3.5, 4 models
    - Azure OpenAI: Same pricing as OpenAI

USAGE:
    from aos_sdk.aos_sdk_cus_cost import (
        calculate_cost,
        get_model_pricing,
        CusPricingTable,
    )

    # Calculate cost for a call
    cost_cents = calculate_cost(
        model="gpt-4o",
        tokens_in=1000,
        tokens_out=500,
    )

    # Get pricing info
    pricing = get_model_pricing("claude-sonnet-4-20250514")
    print(f"Input: ${pricing.input_per_1k_tokens}, Output: ${pricing.output_per_1k_tokens}")

COST REPRESENTATION:
    All costs are in CENTS (integer) to avoid floating-point errors.
    Internal calculations use microcents (1/1,000,000 of a dollar).

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass(frozen=True)
class CusModelPricing:
    """Pricing information for an LLM model.

    All prices are in dollars per 1,000 tokens.
    Frozen to ensure immutability.

    Attributes:
        provider: Provider name
        model_pattern: Model name pattern
        input_per_1k_tokens: Cost per 1K input tokens in dollars
        output_per_1k_tokens: Cost per 1K output tokens in dollars
        effective_date: Date this pricing became effective
        notes: Optional notes about this pricing
    """

    provider: str
    model_pattern: str
    input_per_1k_tokens: float
    output_per_1k_tokens: float
    effective_date: date
    notes: Optional[str] = None

    @property
    def input_per_token_microcents(self) -> int:
        """Cost per input token in microcents (1/10000 of a cent)."""
        return int(self.input_per_1k_tokens * 1000 * 100)  # dollars -> cents -> microcents/1000

    @property
    def output_per_token_microcents(self) -> int:
        """Cost per output token in microcents."""
        return int(self.output_per_1k_tokens * 1000 * 100)


# =============================================================================
# PRICING TABLES
# =============================================================================
# Last updated: 2026-01-17
# Sources:
#   - OpenAI: https://openai.com/api/pricing/
#   - Anthropic: https://anthropic.com/pricing


class CusPricingTable:
    """
    Centralized pricing table for all supported models.

    VERSIONING:
    - Each entry has an effective_date
    - New pricing should be added as new entries, not overwrites
    - Historical pricing preserved for audit

    MAINTENANCE:
    - Update this table when providers change pricing
    - Add notes for pricing changes
    """

    # Pricing effective date for this table
    TABLE_VERSION = "2026-01-17"

    # ==========================================================================
    # OPENAI PRICING (as of 2026-01-17)
    # ==========================================================================

    OPENAI_PRICING: Dict[str, CusModelPricing] = {
        # GPT-4o family
        "gpt-4o": CusModelPricing(
            provider="openai",
            model_pattern="gpt-4o",
            input_per_1k_tokens=0.0025,  # $2.50/1M = $0.0025/1K
            output_per_1k_tokens=0.010,  # $10/1M = $0.01/1K
            effective_date=date(2025, 10, 1),
            notes="GPT-4o main model",
        ),
        "gpt-4o-mini": CusModelPricing(
            provider="openai",
            model_pattern="gpt-4o-mini",
            input_per_1k_tokens=0.00015,  # $0.15/1M
            output_per_1k_tokens=0.0006,  # $0.60/1M
            effective_date=date(2024, 7, 18),
            notes="GPT-4o-mini, cost-effective",
        ),
        # GPT-4 Turbo family
        "gpt-4-turbo": CusModelPricing(
            provider="openai",
            model_pattern="gpt-4-turbo",
            input_per_1k_tokens=0.01,  # $10/1M
            output_per_1k_tokens=0.03,  # $30/1M
            effective_date=date(2024, 4, 9),
            notes="GPT-4 Turbo with vision",
        ),
        # GPT-4 family
        "gpt-4": CusModelPricing(
            provider="openai",
            model_pattern="gpt-4",
            input_per_1k_tokens=0.03,  # $30/1M
            output_per_1k_tokens=0.06,  # $60/1M
            effective_date=date(2023, 3, 14),
            notes="Original GPT-4 8K",
        ),
        "gpt-4-32k": CusModelPricing(
            provider="openai",
            model_pattern="gpt-4-32k",
            input_per_1k_tokens=0.06,  # $60/1M
            output_per_1k_tokens=0.12,  # $120/1M
            effective_date=date(2023, 3, 14),
            notes="GPT-4 32K context",
        ),
        # GPT-3.5 family
        "gpt-3.5-turbo": CusModelPricing(
            provider="openai",
            model_pattern="gpt-3.5-turbo",
            input_per_1k_tokens=0.0005,  # $0.50/1M
            output_per_1k_tokens=0.0015,  # $1.50/1M
            effective_date=date(2024, 1, 25),
            notes="GPT-3.5 Turbo",
        ),
        # o1 family
        "o1": CusModelPricing(
            provider="openai",
            model_pattern="o1",
            input_per_1k_tokens=0.015,  # $15/1M
            output_per_1k_tokens=0.06,  # $60/1M
            effective_date=date(2024, 12, 5),
            notes="o1 reasoning model",
        ),
        "o1-mini": CusModelPricing(
            provider="openai",
            model_pattern="o1-mini",
            input_per_1k_tokens=0.003,  # $3/1M
            output_per_1k_tokens=0.012,  # $12/1M
            effective_date=date(2024, 9, 12),
            notes="o1-mini reasoning model",
        ),
    }

    # ==========================================================================
    # ANTHROPIC PRICING (as of 2026-01-17)
    # ==========================================================================

    ANTHROPIC_PRICING: Dict[str, CusModelPricing] = {
        # Claude 4 family
        "claude-opus-4": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-opus-4",
            input_per_1k_tokens=0.015,  # $15/1M
            output_per_1k_tokens=0.075,  # $75/1M
            effective_date=date(2025, 5, 22),
            notes="Claude Opus 4.5",
        ),
        "claude-sonnet-4": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-sonnet-4",
            input_per_1k_tokens=0.003,  # $3/1M
            output_per_1k_tokens=0.015,  # $15/1M
            effective_date=date(2025, 5, 22),
            notes="Claude Sonnet 4",
        ),
        # Claude 3.5 family
        "claude-3-5-sonnet": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-3-5-sonnet",
            input_per_1k_tokens=0.003,  # $3/1M
            output_per_1k_tokens=0.015,  # $15/1M
            effective_date=date(2024, 6, 20),
            notes="Claude 3.5 Sonnet",
        ),
        "claude-3-5-haiku": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-3-5-haiku",
            input_per_1k_tokens=0.001,  # $1/1M
            output_per_1k_tokens=0.005,  # $5/1M
            effective_date=date(2024, 11, 4),
            notes="Claude 3.5 Haiku",
        ),
        # Claude 3 family
        "claude-3-opus": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-3-opus",
            input_per_1k_tokens=0.015,  # $15/1M
            output_per_1k_tokens=0.075,  # $75/1M
            effective_date=date(2024, 3, 4),
            notes="Claude 3 Opus",
        ),
        "claude-3-sonnet": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-3-sonnet",
            input_per_1k_tokens=0.003,  # $3/1M
            output_per_1k_tokens=0.015,  # $15/1M
            effective_date=date(2024, 3, 4),
            notes="Claude 3 Sonnet",
        ),
        "claude-3-haiku": CusModelPricing(
            provider="anthropic",
            model_pattern="claude-3-haiku",
            input_per_1k_tokens=0.00025,  # $0.25/1M
            output_per_1k_tokens=0.00125,  # $1.25/1M
            effective_date=date(2024, 3, 14),
            notes="Claude 3 Haiku",
        ),
    }

    # Combined pricing for lookups
    ALL_PRICING: Dict[str, CusModelPricing] = {
        **OPENAI_PRICING,
        **ANTHROPIC_PRICING,
    }


# =============================================================================
# DEFAULT PRICING (for unknown models)
# =============================================================================

_DEFAULT_PRICING = CusModelPricing(
    provider="unknown",
    model_pattern="default",
    input_per_1k_tokens=0.01,  # Conservative default
    output_per_1k_tokens=0.03,
    effective_date=date(2024, 1, 1),
    notes="Default pricing for unknown models",
)


# =============================================================================
# PRICING LOOKUP
# =============================================================================


def get_model_pricing(model: str) -> CusModelPricing:
    """Get pricing information for a model.

    Uses pattern matching to find the best pricing match.

    Args:
        model: Model name or identifier

    Returns:
        CusModelPricing for the model
    """
    model_lower = model.lower()

    # Exact match first
    if model_lower in CusPricingTable.ALL_PRICING:
        return CusPricingTable.ALL_PRICING[model_lower]

    # Prefix match (handles versioned models)
    for pattern, pricing in CusPricingTable.ALL_PRICING.items():
        if model_lower.startswith(pattern):
            return pricing

    # Partial match (handles models like "claude-sonnet-4-20250514")
    for pattern, pricing in CusPricingTable.ALL_PRICING.items():
        if pattern in model_lower:
            return pricing

    logger.warning(f"Unknown model '{model}', using default pricing")
    return _DEFAULT_PRICING


def get_provider_pricing(provider: str) -> Dict[str, CusModelPricing]:
    """Get all pricing for a provider.

    Args:
        provider: Provider name ('openai', 'anthropic')

    Returns:
        Dict of model pattern to pricing
    """
    provider_lower = provider.lower()

    if provider_lower == "openai":
        return CusPricingTable.OPENAI_PRICING
    elif provider_lower == "anthropic":
        return CusPricingTable.ANTHROPIC_PRICING
    else:
        return {}


# =============================================================================
# COST CALCULATION
# =============================================================================


def calculate_cost(
    model: str,
    tokens_in: int,
    tokens_out: int,
) -> int:
    """Calculate cost in cents for an LLM call.

    Uses integer arithmetic to avoid floating-point errors.
    Internal calculation uses microcents, then rounds to cents.

    Args:
        model: Model name
        tokens_in: Number of input tokens
        tokens_out: Number of output tokens

    Returns:
        Cost in cents (integer)
    """
    pricing = get_model_pricing(model)

    # Calculate in microcents (1/10000 of a cent) for precision
    # Formula: (tokens / 1000) * (price_per_1k * 100 cents * 10000 microcents)
    input_microcents = tokens_in * pricing.input_per_token_microcents
    output_microcents = tokens_out * pricing.output_per_token_microcents
    total_microcents = input_microcents + output_microcents

    # Convert to cents (round up for billing fairness)
    # 10000 microcents = 1 cent
    cents = (total_microcents + 9999) // 10000

    return max(cents, 0)


def calculate_cost_breakdown(
    model: str,
    tokens_in: int,
    tokens_out: int,
) -> Dict[str, int]:
    """Calculate detailed cost breakdown in cents.

    Args:
        model: Model name
        tokens_in: Number of input tokens
        tokens_out: Number of output tokens

    Returns:
        Dict with input_cost, output_cost, and total_cost in cents
    """
    pricing = get_model_pricing(model)

    # Calculate separately
    input_microcents = tokens_in * pricing.input_per_token_microcents
    output_microcents = tokens_out * pricing.output_per_token_microcents

    input_cents = (input_microcents + 9999) // 10000
    output_cents = (output_microcents + 9999) // 10000
    total_cents = calculate_cost(model, tokens_in, tokens_out)

    return {
        "input_cost_cents": max(input_cents, 0),
        "output_cost_cents": max(output_cents, 0),
        "total_cost_cents": total_cents,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "model": model,
        "pricing_version": CusPricingTable.TABLE_VERSION,
    }


def estimate_cost(
    model: str,
    estimated_tokens_in: int,
    estimated_tokens_out: int,
) -> int:
    """Estimate cost before making a call.

    Same as calculate_cost but semantically indicates pre-call estimation.

    Args:
        model: Model name
        estimated_tokens_in: Estimated input tokens
        estimated_tokens_out: Estimated output tokens

    Returns:
        Estimated cost in cents
    """
    return calculate_cost(model, estimated_tokens_in, estimated_tokens_out)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def format_cost(cents: int) -> str:
    """Format cost in cents as a dollar string.

    Args:
        cents: Cost in cents

    Returns:
        Formatted string like "$1.23"
    """
    dollars = cents / 100
    return f"${dollars:.2f}"


def cents_to_dollars(cents: int) -> float:
    """Convert cents to dollars.

    Args:
        cents: Cost in cents

    Returns:
        Cost in dollars
    """
    return cents / 100


def dollars_to_cents(dollars: float) -> int:
    """Convert dollars to cents.

    Args:
        dollars: Cost in dollars

    Returns:
        Cost in cents (rounded)
    """
    return int(round(dollars * 100))


def get_pricing_version() -> str:
    """Get the current pricing table version."""
    return CusPricingTable.TABLE_VERSION
