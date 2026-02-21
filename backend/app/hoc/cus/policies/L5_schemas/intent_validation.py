# capability_id: CAP-009
# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: M19 intent validation contract for policy intents
# Callers: IntentEmitter, policy validators
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L6, L7, sqlalchemy
# Reference: PIN-470, Policy System

"""
M19 Intent Validation Protocol.

Defines the contract between IntentEmitter and external M19 validators.
Enforcement-weight intents (EXECUTE, ROUTE, ESCALATE) require validation;
observability intents (LOG, ALLOW, ALERT) skip M19 validation.
"""

from typing import Protocol, runtime_checkable

from typing_extensions import TypedDict


class PolicyIntentValidationResult(TypedDict):
    """Result of M19 intent validation."""

    allowed: bool
    errors: list[str]


@runtime_checkable
class PolicyIntentValidator(Protocol):
    """Protocol for M19 intent validators."""

    async def validate_intent(self, intent) -> PolicyIntentValidationResult: ...
