# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — policy proposal lifecycle + snapshot governance
# Callers: Admin API (L2), policy enforcement paths
# Allowed Imports: hoc_spine, hoc.cus.policies.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 2B Wiring, PB-S4 (human-in-the-loop governance)
# artifact_class: CODE

"""
Policy Governance Handler (PIN-513 Batch 2B Wiring)

L4 handler that owns the policy proposal lifecycle and snapshot
governance operations.

Wires from policies/L5_engines/policy_proposal_engine.py:
- get_policy_proposal_engine(session)
- check_proposal_eligibility(session, ...)
- create_policy_proposal(session, proposal)
- review_policy_proposal(session, proposal_id, review, audit)
- delete_policy_rule(session, rule_id, tenant_id, deleted_by)
- get_proposal_summary(session, ...)
- generate_default_rule(policy_type, feedback_type) [pure import]

Wires from policies/L5_engines/snapshot_engine.py:
- create_policy_snapshot(tenant_id, policies, thresholds, ...)
- get_active_snapshot(tenant_id)
- get_policy_snapshot(snapshot_id)
- get_snapshot_history(tenant_id, limit)
- verify_snapshot(snapshot_id)
- get_snapshot_registry()

Flow:
  Admin API
    → PolicyGovernanceHandler.<method>(session, ...)
        → L5 engine call
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger("nova.hoc_spine.handlers.policy_governance")


class PolicyGovernanceHandler:
    """L4 handler: policy proposal lifecycle + snapshot governance.

    PB-S4: Proposals are HUMAN decisions. This handler enforces
    the draft → review → activate lifecycle.
    """

    # ── Proposal operations ──

    async def check_eligibility(
        self,
        session: Any,
        tenant_id: Optional[UUID] = None,
        feedback_type: Optional[str] = None,
        threshold: int = 3,
    ) -> List[Dict[str, Any]]:
        """Check which feedback patterns are eligible for proposals."""
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import (
            check_proposal_eligibility,
        )

        return await check_proposal_eligibility(
            session=session,
            tenant_id=tenant_id,
            feedback_type=feedback_type,
            threshold=threshold,
        )

    async def create_proposal(
        self,
        session: Any,
        proposal: Any,
    ) -> str:
        """Create a draft policy proposal. PB-S4: human approval required."""
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import (
            create_policy_proposal,
        )

        proposal_id = await create_policy_proposal(
            session=session,
            proposal=proposal,
        )
        logger.info(
            "policy_proposal_created",
            extra={"proposal_id": proposal_id},
        )
        return proposal_id

    async def review_proposal(
        self,
        session: Any,
        proposal_id: UUID,
        review: Any,
        audit: Any = None,
    ) -> Dict[str, Any]:
        """Approve or reject a proposal. PB-S4: HUMAN action only.

        Enforces GOV-POL-001 (conflict detection) on approval.
        """
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import (
            review_policy_proposal,
        )

        result = await review_policy_proposal(
            session=session,
            proposal_id=proposal_id,
            review=review,
            audit=audit,
        )
        logger.info(
            "policy_proposal_reviewed",
            extra={
                "proposal_id": str(proposal_id),
                "status": result.get("status"),
            },
        )
        return result

    async def delete_rule(
        self,
        session: Any,
        rule_id: str,
        tenant_id: str,
        deleted_by: str,
    ) -> bool:
        """Delete a policy rule. Enforces GOV-POL-002 (dependency resolution)."""
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import (
            delete_policy_rule,
        )

        result = await delete_policy_rule(
            session=session,
            rule_id=rule_id,
            tenant_id=tenant_id,
            deleted_by=deleted_by,
        )
        logger.info(
            "policy_rule_deleted",
            extra={
                "rule_id": rule_id,
                "tenant_id": tenant_id,
                "deleted_by": deleted_by,
            },
        )
        return result

    async def get_summary(
        self,
        session: Any,
        tenant_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get proposal summary for ops visibility. Read-only."""
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import (
            get_proposal_summary,
        )

        return await get_proposal_summary(
            session=session,
            tenant_id=tenant_id,
            status=status,
            limit=limit,
        )

    @staticmethod
    def generate_rule_template(
        policy_type: str,
        feedback_type: str,
    ) -> Dict[str, Any]:
        """Generate default rule template. Pure function."""
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import (
            generate_default_rule,
        )

        return generate_default_rule(
            policy_type=policy_type,
            feedback_type=feedback_type,
        )

    # ── Snapshot operations ──

    def create_snapshot(
        self,
        tenant_id: str,
        policies: List[Dict[str, Any]],
        thresholds: Dict[str, Any],
        policy_version: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Any:
        """Create immutable policy snapshot. Supersedes existing active."""
        from app.hoc.cus.policies.L5_engines.snapshot_engine import (
            create_policy_snapshot,
        )

        snapshot = create_policy_snapshot(
            tenant_id=tenant_id,
            policies=policies,
            thresholds=thresholds,
            policy_version=policy_version,
            description=description,
        )
        logger.info(
            "policy_snapshot_created",
            extra={"tenant_id": tenant_id, "snapshot_id": snapshot.id},
        )
        return snapshot

    def get_active_snapshot(self, tenant_id: str) -> Any:
        """Get current active snapshot for tenant."""
        from app.hoc.cus.policies.L5_engines.snapshot_engine import (
            get_active_snapshot,
        )

        return get_active_snapshot(tenant_id=tenant_id)

    def get_snapshot(self, snapshot_id: str) -> Any:
        """Get snapshot by ID."""
        from app.hoc.cus.policies.L5_engines.snapshot_engine import (
            get_policy_snapshot,
        )

        return get_policy_snapshot(snapshot_id=snapshot_id)

    def get_history(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> List[Any]:
        """Get snapshot version history for tenant."""
        from app.hoc.cus.policies.L5_engines.snapshot_engine import (
            get_snapshot_history,
        )

        return get_snapshot_history(tenant_id=tenant_id, limit=limit)

    def verify_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Verify snapshot integrity (SHA256 hash check, GAP-029)."""
        from app.hoc.cus.policies.L5_engines.snapshot_engine import (
            verify_snapshot,
        )

        result = verify_snapshot(snapshot_id=snapshot_id)
        logger.info(
            "policy_snapshot_verified",
            extra={
                "snapshot_id": snapshot_id,
                "is_valid": result.get("is_valid"),
            },
        )
        return result
