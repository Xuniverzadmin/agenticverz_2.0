# C3 Optimization Safety Layer
# Phase: C3_OPTIMIZATION
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md, C3_KILLSWITCH_ROLLBACK_MODEL.md
#
# This module provides the safety cage for prediction-driven optimization.
# Predictions may influence behavior ONLY via declared optimization envelopes.
#
# Core invariants (I-C3-1 to I-C3-6):
# - Predictions influence via declared envelopes only
# - Every change bounded (impact + time)
# - All influence reversible
# - Human override always wins
# - Replay without predictions = baseline behavior
# - Optimization failure never creates incidents

from app.optimization.envelope import (
    Envelope,
    EnvelopeLifecycle,
    EnvelopeValidationError,
    RevertReason,
    calculate_bounded_value,
    validate_envelope,
)
from app.optimization.killswitch import (
    KillSwitch,
    KillSwitchEvent,
    KillSwitchState,
    get_killswitch,
    reset_killswitch_for_testing,
)
from app.optimization.manager import (
    EnvelopeManager,
    get_envelope_manager,
    reset_manager_for_testing,
)

__all__ = [
    # Kill-switch
    "KillSwitch",
    "KillSwitchState",
    "KillSwitchEvent",
    "get_killswitch",
    "reset_killswitch_for_testing",
    # Envelope
    "Envelope",
    "EnvelopeLifecycle",
    "EnvelopeValidationError",
    "RevertReason",
    "validate_envelope",
    "calculate_bounded_value",
    # Manager
    "EnvelopeManager",
    "get_envelope_manager",
    "reset_manager_for_testing",
]
