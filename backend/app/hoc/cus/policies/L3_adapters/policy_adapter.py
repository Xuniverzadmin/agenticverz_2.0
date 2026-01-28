# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L4)
# Role: Policy evaluation boundary adapter (L2 → L3 → L4)
# Callers: policy.py (L2)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-258 Phase F-3 Policy Cluster
# Contract: PHASE_F_FIX_DESIGN (F-P-RULE-1 to F-P-RULE-5)
#
# GOVERNANCE NOTE (F-P-RULE-3):
# This L3 adapter is TRANSLATION ONLY. No branching, no thresholds,
# no interpretation. It accepts API requests, normalizes inputs,
# calls L4, and returns the decision/result.
#
# F-P-RULE-1: Policy Decisions Live Only in L4 - we don't decide here
# F-P-RULE-3: L3 Is Translation Only - no branching, no thresholds

"""
Policy Boundary Adapter (L3)

This adapter sits between L2 (policy.py API) and L4 (policy_command.py).

L2 (API) → L3 (this adapter) → L4 (command) → L5 (workflow execution)

The adapter:
1. Receives API requests with execution context
2. Translates to domain facts
3. Delegates to L4 commands
4. Returns results to L2

This is a thin translation layer - no branching, no thresholds, no interpretation.

Reference: PIN-258 Phase F-3 Policy Cluster
"""

from typing import Any, Dict, List, Optional

from app.commands.policy_command import (
    PolicyEvaluationResult,
    PolicyViolation,
    check_policy_violations,
    evaluate_policy,
    record_approval_created,
    record_approval_outcome,
    record_escalation,
    record_webhook_used,
    simulate_cost,
)

# =============================================================================
# L3 Adapter Class
# =============================================================================


class PolicyAdapter:
    """
    Boundary adapter for policy operations.

    This class provides the ONLY interface that L2 (policy.py) may use
    to access policy functionality. It translates API context to domain
    facts and delegates to L4 commands.

    F-P-RULE-3: L3 Is Translation Only
    """

    async def simulate_cost(
        self,
        skill_id: str,
        tenant_id: str,
        payload: Dict[str, Any],
    ) -> Optional[int]:
        """
        Simulate cost for a skill execution.

        This L3 method translates API context to domain facts and
        delegates to L4 simulate_cost command.

        Args:
            skill_id: Skill to simulate
            tenant_id: Tenant context
            payload: Execution payload

        Returns:
            Estimated cost in cents

        Reference: PIN-258 Phase F-3 (F-P-RULE-3: Translation Only)
        """
        # L3 → L4 delegation (allowed import)
        return await simulate_cost(
            skill_id=skill_id,
            tenant_id=tenant_id,
            payload=payload,
        )

    async def check_policy_violations(
        self,
        skill_id: str,
        tenant_id: str,
        agent_id: Optional[str],
        payload: Dict[str, Any],
        simulated_cost: Optional[int],
    ) -> List[Dict[str, Any]]:
        """
        Check for policy violations.

        This L3 method translates API context to domain facts and
        delegates to L4 check_policy_violations command.

        Args:
            skill_id: Skill being evaluated
            tenant_id: Tenant context
            agent_id: Optional agent context
            payload: Execution payload
            simulated_cost: Cost estimate from simulation

        Returns:
            List of policy violations as dicts (for API compatibility)

        Reference: PIN-258 Phase F-3 (F-P-RULE-3: Translation Only)
        """
        # L3 → L4 delegation (allowed import)
        violations = await check_policy_violations(
            skill_id=skill_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            payload=payload,
            simulated_cost=simulated_cost,
        )
        # Convert L4 result types to dicts for API compatibility
        return [
            {
                "type": v.type,
                "message": v.message,
                "policy": v.policy,
                "details": v.details,
            }
            for v in violations
        ]

    async def evaluate_policy(
        self,
        skill_id: str,
        tenant_id: str,
        agent_id: Optional[str],
        payload: Dict[str, Any],
        auto_approve_max_cost_cents: int = 0,
        approval_level: int = 1,
    ) -> PolicyEvaluationResult:
        """
        Evaluate policy for a skill execution.

        This L3 method translates API context to domain facts and
        delegates to L4 evaluate_policy command.

        Args:
            skill_id: Skill to evaluate
            tenant_id: Tenant context
            agent_id: Optional agent context
            payload: Execution payload
            auto_approve_max_cost_cents: Threshold for auto-approval
            approval_level: Required approval level

        Returns:
            PolicyEvaluationResult from L4 command

        Reference: PIN-258 Phase F-3 (F-P-RULE-3: Translation Only)
        """
        # L3 → L4 delegation (allowed import)
        return await evaluate_policy(
            skill_id=skill_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            payload=payload,
            auto_approve_max_cost_cents=auto_approve_max_cost_cents,
            approval_level=approval_level,
        )

    def record_approval_created(self, policy_type: str) -> None:
        """
        Record that an approval request was created.

        This L3 method delegates to L4 for metric emission.

        Args:
            policy_type: Type of policy (e.g., "cost")

        Reference: PIN-258 Phase F-3 (F-P-RULE-2: Metrics via L4→L5)
        """
        # L3 → L4 delegation (allowed import)
        record_approval_created(policy_type)

    def record_approval_outcome(self, result: str) -> None:
        """
        Record approval outcome.

        This L3 method delegates to L4 for metric emission.

        Args:
            result: Outcome (approved/rejected/expired)

        Reference: PIN-258 Phase F-3 (F-P-RULE-2: Metrics via L4→L5)
        """
        # L3 → L4 delegation (allowed import)
        record_approval_outcome(result)

    def record_escalation(self) -> None:
        """
        Record that an escalation occurred.

        This L3 method delegates to L4 for metric emission.

        Reference: PIN-258 Phase F-3 (F-P-RULE-2: Metrics via L4→L5)
        """
        # L3 → L4 delegation (allowed import)
        record_escalation()

    def record_webhook_used(self) -> None:
        """
        Record that webhook fallback was used.

        This L3 method delegates to L4 for metric emission.

        Reference: PIN-258 Phase F-3 (F-P-RULE-2: Metrics via L4→L5)
        """
        # L3 → L4 delegation (allowed import)
        record_webhook_used()


# =============================================================================
# Singleton Factory
# =============================================================================

_policy_adapter_instance: Optional[PolicyAdapter] = None


def get_policy_adapter() -> PolicyAdapter:
    """
    Get the singleton PolicyAdapter instance.

    This is the ONLY way L2 should obtain a policy adapter.
    Direct instantiation is discouraged.

    Returns:
        PolicyAdapter singleton instance

    Reference: PIN-258 Phase F-3 (F-P-RULE-3: L3 Is the Only Entry)
    """
    global _policy_adapter_instance
    if _policy_adapter_instance is None:
        _policy_adapter_instance = PolicyAdapter()
    return _policy_adapter_instance


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PolicyAdapter",
    "get_policy_adapter",
    # Re-export result types for L2 convenience
    "PolicyEvaluationResult",
    "PolicyViolation",
]
