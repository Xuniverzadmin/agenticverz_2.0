# C3 Envelope Declarations
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md

from app.optimization.envelopes.s1_retry_backoff import (
    S1_RETRY_BACKOFF_ENVELOPE,
    create_s1_envelope,
)
from app.optimization.envelopes.s2_cost_smoothing import (
    S2_ABSOLUTE_FLOOR,
    S2_COST_SMOOTHING_ENVELOPE,
    calculate_s2_bounded_value,
    create_s2_envelope,
    validate_s2_envelope,
)

__all__ = [
    # S1: Bounded Retry Optimization
    "S1_RETRY_BACKOFF_ENVELOPE",
    "create_s1_envelope",
    # S2: Cost Smoothing Optimization
    "S2_COST_SMOOTHING_ENVELOPE",
    "S2_ABSOLUTE_FLOOR",
    "create_s2_envelope",
    "validate_s2_envelope",
    "calculate_s2_bounded_value",
]
