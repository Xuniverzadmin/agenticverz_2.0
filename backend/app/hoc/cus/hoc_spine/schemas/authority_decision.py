# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: INTERNAL
# Role: Unified authority decision schema for all L4 authority checks
# Consumers: orchestrator, authority/concurrent_runs, authority/degraded_mode_checker, authority/contracts
# Reference: PIN-520 (L4 Uniformity Initiative), HOC_LAYER_TOPOLOGY_V2.0.0.md
# artifact_class: CODE

"""
AuthorityDecision — Unified Schema for L4 Authority Gates

All authority checks in hoc_spine return this unified schema.
This ensures consistent handling of allow/deny/degraded states
across concurrent_runs, degraded_mode_checker, contract_engine, etc.

Usage:
    from app.hoc.cus.hoc_spine.schemas.authority_decision import AuthorityDecision

    # In authority module
    def check_concurrent_runs(tenant_id: str, limit: int) -> AuthorityDecision:
        current = get_active_runs(tenant_id)
        if current >= limit:
            return AuthorityDecision.deny(
                reason=f"Concurrent run limit ({limit}) exceeded",
                code="CONCURRENT_LIMIT_EXCEEDED",
            )
        return AuthorityDecision.allow()

    # In executor
    authority = check_concurrent_runs(tenant_id, limit=5)
    if not authority.allowed:
        return OperationResult.fail(authority.reason, authority.code)
    if authority.degraded:
        logger.warning("operation.degraded_mode", extra={"reason": authority.reason})

Design Principles:
    1. IMMUTABLE — frozen dataclass, no mutation after creation
    2. EXPLICIT — allow/deny/degraded are separate states, not inferred
    3. AUDITABLE — every decision has reason and optional code
    4. COMPOSABLE — conditions list allows compound decisions
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AuthorityDecision:
    """
    Unified authority decision returned by all L4 authority checks.

    Attributes:
        allowed: Whether the operation is permitted
        reason: Human-readable explanation of the decision
        degraded: Whether system is in degraded mode (operation allowed but flagged)
        code: Machine-readable error/status code
        conditions: List of conditions that affected the decision
    """

    allowed: bool
    reason: str
    degraded: bool = False
    code: Optional[str] = None
    conditions: tuple[str, ...] = field(default_factory=tuple)

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @staticmethod
    def allow(
        reason: str = "Operation permitted",
        degraded: bool = False,
        conditions: tuple[str, ...] = (),
    ) -> "AuthorityDecision":
        """
        Create an ALLOW decision.

        Args:
            reason: Why the operation is allowed
            degraded: Whether system is in degraded mode
            conditions: Conditions that were checked

        Returns:
            AuthorityDecision with allowed=True
        """
        return AuthorityDecision(
            allowed=True,
            reason=reason,
            degraded=degraded,
            code="ALLOWED" if not degraded else "ALLOWED_DEGRADED",
            conditions=conditions,
        )

    @staticmethod
    def deny(
        reason: str,
        code: str = "DENIED",
        conditions: tuple[str, ...] = (),
    ) -> "AuthorityDecision":
        """
        Create a DENY decision.

        Args:
            reason: Why the operation is denied
            code: Machine-readable denial code
            conditions: Conditions that caused the denial

        Returns:
            AuthorityDecision with allowed=False
        """
        return AuthorityDecision(
            allowed=False,
            reason=reason,
            degraded=False,
            code=code,
            conditions=conditions,
        )

    @staticmethod
    def allow_with_degraded_flag(
        reason: str,
        conditions: tuple[str, ...] = (),
    ) -> "AuthorityDecision":
        """
        Create an ALLOW decision with degraded mode flag.

        The operation is permitted but the system is in degraded state.
        This should be logged/audited but not block execution.

        Args:
            reason: Why degraded mode is active
            conditions: Conditions indicating degradation

        Returns:
            AuthorityDecision with allowed=True, degraded=True
        """
        return AuthorityDecision(
            allowed=True,
            reason=reason,
            degraded=True,
            code="ALLOWED_DEGRADED",
            conditions=conditions,
        )

    # =========================================================================
    # Composition
    # =========================================================================

    def with_condition(self, condition: str) -> "AuthorityDecision":
        """
        Return a new decision with an additional condition.

        Since AuthorityDecision is frozen, this creates a new instance.

        Args:
            condition: Condition to add

        Returns:
            New AuthorityDecision with the condition added
        """
        return AuthorityDecision(
            allowed=self.allowed,
            reason=self.reason,
            degraded=self.degraded,
            code=self.code,
            conditions=self.conditions + (condition,),
        )

    @staticmethod
    def combine(*decisions: "AuthorityDecision") -> "AuthorityDecision":
        """
        Combine multiple authority decisions into one.

        Rules:
            - If ANY decision is deny → result is deny (first deny wins)
            - If ALL decisions are allow but ANY is degraded → result is degraded
            - If ALL decisions are allow and none degraded → result is allow

        Args:
            decisions: Multiple AuthorityDecision instances

        Returns:
            Combined AuthorityDecision
        """
        if not decisions:
            return AuthorityDecision.allow()

        # Check for any denials
        for decision in decisions:
            if not decision.allowed:
                # First deny wins
                all_conditions = tuple(
                    cond for d in decisions for cond in d.conditions
                )
                return AuthorityDecision(
                    allowed=False,
                    reason=decision.reason,
                    degraded=False,
                    code=decision.code,
                    conditions=all_conditions,
                )

        # All allowed — check for degraded
        any_degraded = any(d.degraded for d in decisions)
        all_conditions = tuple(cond for d in decisions for cond in d.conditions)
        all_reasons = [d.reason for d in decisions if d.reason != "Operation permitted"]

        if any_degraded:
            degraded_reasons = [d.reason for d in decisions if d.degraded]
            return AuthorityDecision.allow_with_degraded_flag(
                reason="; ".join(degraded_reasons) if degraded_reasons else "Degraded mode",
                conditions=all_conditions,
            )

        return AuthorityDecision.allow(
            reason="; ".join(all_reasons) if all_reasons else "Operation permitted",
            conditions=all_conditions,
        )

    # =========================================================================
    # Representation
    # =========================================================================

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization/logging."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "degraded": self.degraded,
            "code": self.code,
            "conditions": list(self.conditions),
        }

    def __str__(self) -> str:
        status = "ALLOW" if self.allowed else "DENY"
        if self.degraded:
            status = "DEGRADED"
        return f"AuthorityDecision({status}: {self.reason})"
