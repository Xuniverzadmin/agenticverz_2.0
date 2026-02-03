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
# Role: IRCheckPolicy validation contract for deterministic engine
# Callers: DeterministicEngine
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L6, L7, sqlalchemy
# Reference: PIN-470, Policy System

"""
IRCheckPolicy Validation Protocol.

Defines the contract for policy check validators used by
the deterministic engine's IRCheckPolicy instruction handler.
"""

from typing import Protocol, runtime_checkable

from typing_extensions import TypedDict


class PolicyCheckResult(TypedDict):
    """Result of an IR policy check."""

    allowed: bool
    errors: list[str]


@runtime_checkable
class PolicyCheckValidator(Protocol):
    """Protocol for IR policy check validators."""

    async def validate_policy(self, policy_id: str, context: dict) -> PolicyCheckResult: ...
