# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: PROPOSAL_CREATED, PROPOSAL_APPROVED, PROPOSAL_REJECTED
#   Subscribes: none
# Data Access:
#   Reads: pattern_feedback, policy_proposals, policy_versions (via driver)
#   Writes: policy_proposals, policy_rules, policy_versions (via driver)
# Role: Policy proposal lifecycle engine - manages proposal state machine
# Callers: L2 policies API
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Policy Proposal Engine (L5)

Proposes policy changes based on observed feedback WITHOUT auto-enforcement.

PB-S4 Contract:
- Observe feedback patterns → propose policy → wait for human
- NO auto-enforcement
- NO execution modification
- Human approval is MANDATORY

Rule: Propose → Review → Decide (Human)

State Machine:
    DRAFT → PENDING → APPROVED/REJECTED
                ↓
            ACTIVE (on activation)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.hoc.cus.policies.L6_drivers.policy_proposal_read_driver import (
    PolicyProposalReadDriver,
    get_policy_proposal_read_driver,
)
from app.hoc.cus.policies.L6_drivers.policy_proposal_write_driver import (
    PolicyProposalWriteDriver,
    get_policy_proposal_write_driver,
)
from app.hoc.cus.hoc_spine.schemas.domain_enums import ActorType
from app.hoc.cus.policies.L5_engines.policy_graph import (
    ConflictSeverity,
    get_conflict_engine,
    get_dependency_engine,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.policy import PolicyApprovalRequest, PolicyProposalCreate

logger = logging.getLogger("nova.services.policy_proposal")


# =============================================================================
# Governance Invariant Exceptions (PIN-411)
# =============================================================================


class PolicyActivationBlockedError(Exception):
    """
    GOV-POL-001: Raised when policy activation is blocked due to BLOCKING conflicts.

    This exception is CONSTITUTIONAL - it cannot be caught and ignored.
    The caller must surface the conflict to the human reviewer.
    """

    def __init__(self, message: str, conflicts: list[dict]):
        super().__init__(message)
        self.conflicts = conflicts


class PolicyDeletionBlockedError(Exception):
    """
    GOV-POL-002: Raised when policy deletion is blocked due to dependents.

    This exception is CONSTITUTIONAL - it cannot be caught and ignored.
    The caller must resolve dependencies before deletion.
    """

    def __init__(self, message: str, dependents: list[str]):
        super().__init__(message)
        self.dependents = dependents


# Configuration for proposal thresholds
FEEDBACK_THRESHOLD_FOR_PROPOSAL = 3  # Minimum feedback entries to propose
PROPOSAL_TYPES = {
    "failure_pattern": "retry_policy",
    "cost_spike": "cost_cap",
}


# =============================================================================
# Policy Proposal Engine
# =============================================================================


class PolicyProposalEngine:
    """
    L5 Domain Engine for policy proposal lifecycle management.

    Responsibilities:
    - Eligibility checking (business logic)
    - Proposal creation orchestration
    - State machine transitions (DRAFT → APPROVED/REJECTED)
    - Conflict detection coordination
    - Approval workflow

    Does NOT own:
    - Direct DB queries (delegated to L6 drivers)
    - HTTP concerns (that's L2/L3)
    """

    def __init__(
        self,
        read_driver: PolicyProposalReadDriver,
        write_driver: PolicyProposalWriteDriver,
    ):
        self._read = read_driver
        self._write = write_driver

    async def check_proposal_eligibility(
        self,
        tenant_id: Optional[UUID] = None,
        feedback_type: Optional[str] = None,
        threshold: int = FEEDBACK_THRESHOLD_FOR_PROPOSAL,
    ) -> list[dict]:
        """
        Check if feedback patterns are eligible for policy proposals.

        PB-S4: This function READS feedback data only. No modifications.

        Returns list of eligible patterns with:
        - feedback_type: type of feedback
        - count: number of occurrences
        - feedback_ids: list of affected feedback IDs (provenance)
        - signature: common signature if any
        """
        # Fetch unacknowledged feedback via driver
        feedback_records = await self._read.fetch_unacknowledged_feedback(
            tenant_id=tenant_id,
            feedback_type=feedback_type,
        )

        if not feedback_records:
            return []

        # Group by pattern_type and signature (business logic stays in engine)
        groups: dict[str, list[dict]] = {}
        for fb in feedback_records:
            key = f"{fb['pattern_type']}:{fb['signature'] or 'none'}"
            if key not in groups:
                groups[key] = []
            groups[key].append(fb)

        # Find eligible groups
        eligible = []
        for key, fbs in groups.items():
            if len(fbs) >= threshold:
                pattern_type = fbs[0]["pattern_type"]
                eligible.append(
                    {
                        "feedback_type": pattern_type,
                        "count": len(fbs),
                        "feedback_ids": [f["id"] for f in fbs],
                        "signature": fbs[0]["signature"],
                        "tenant_id": fbs[0]["tenant_id"],
                        "suggested_policy_type": PROPOSAL_TYPES.get(
                            pattern_type, "custom"
                        ),
                    }
                )

        logger.info(
            "proposal_eligibility_checked",
            extra={
                "eligible_count": len(eligible),
                "threshold": threshold,
            },
        )

        return eligible

    async def create_proposal(
        self,
        proposal: PolicyProposalCreate,
    ) -> str:
        """
        Create a policy proposal.

        PB-S4: This creates a DRAFT record. No enforcement.
        Status starts as 'draft' - human approval required.

        Returns the proposal ID.
        """
        proposal_id = await self._write.create_proposal(
            tenant_id=str(proposal.tenant_id),
            proposal_name=proposal.proposal_name,
            proposal_type=proposal.proposal_type,
            rationale=proposal.rationale,
            proposed_rule=proposal.proposed_rule,
            triggering_feedback_ids=proposal.triggering_feedback_ids,
        )

        logger.info(
            "policy_proposal_created",
            extra={
                "proposal_id": proposal_id,
                "proposal_type": proposal.proposal_type,
                "tenant_id": str(proposal.tenant_id),
                "status": "draft",
                "provenance_count": len(proposal.triggering_feedback_ids),
            },
        )

        return proposal_id

    async def review_proposal(
        self,
        session: "AsyncSession",
        proposal_id: UUID,
        review: PolicyApprovalRequest,
        audit: Any = None,
    ) -> dict:
        """
        Review (approve/reject) a policy proposal.

        PB-S4: This is a HUMAN action. The system cannot auto-approve.
        - Approval creates a new version and sets effective_from
        - Rejection marks the proposal as rejected (preserved for audit)

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, proposal review rolls back
        - No partial state is possible

        Returns the updated proposal as dict.
        """
        # Fetch the proposal
        proposal = await self._read.fetch_proposal_by_id(proposal_id)

        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal["status"] != "draft":
            raise ValueError(
                f"Proposal {proposal_id} is not in draft status "
                f"(current: {proposal['status']})"
            )

        now = utc_now()

        if review.action == "approve":
            # =====================================================================
            # GOV-POL-001: Conflict detection is mandatory pre-activation
            # =====================================================================
            conflict_engine = get_conflict_engine(proposal["tenant_id"])
            conflict_result = await conflict_engine.detect_conflicts(
                session,
                severity_filter=ConflictSeverity.BLOCKING,
            )

            if conflict_result.unresolved_count > 0:
                blocking_conflicts = [c.to_dict() for c in conflict_result.conflicts]
                logger.warning(
                    "GOV-POL-001_ACTIVATION_BLOCKED",
                    extra={
                        "proposal_id": str(proposal_id),
                        "blocking_conflicts": len(blocking_conflicts),
                        "conflicts": blocking_conflicts,
                    },
                )
                raise PolicyActivationBlockedError(
                    f"Cannot activate: {conflict_result.unresolved_count} "
                    f"BLOCKING conflicts exist. Resolve conflicts before approval.",
                    conflicts=blocking_conflicts,
                )

            logger.info(
                "GOV-POL-001_CONFLICT_CHECK_PASSED",
                extra={
                    "proposal_id": str(proposal_id),
                    "blocking_conflicts": 0,
                },
            )

            effective_from = review.effective_from or now

            # Update proposal status
            await self._write.update_proposal_status(
                proposal_id=proposal_id,
                new_status="approved",
                reviewed_at=now,
                reviewed_by=review.reviewed_by,
                review_notes=review.review_notes,
                effective_from=effective_from,
            )

            # Count existing versions
            version_count = await self._read.count_versions_for_proposal(proposal_id)

            # Create version snapshot
            version_id = await self._write.create_version(
                proposal_id=proposal_id,
                version_number=version_count + 1,
                rule_snapshot=proposal["proposed_rule"],
                created_by=review.reviewed_by,
                change_reason=f"Approved: {review.review_notes or 'No notes'}",
            )

            # Create policy rule from approved proposal
            rule_id = await self._create_policy_rule_from_proposal(
                proposal=proposal,
                approved_by=review.reviewed_by,
            )

            # Emit audit event for approval (PIN-504: audit injected by L4)
            if audit:
                await audit.policy_proposal_approved(
                    tenant_id=proposal["tenant_id"],
                    proposal_id=str(proposal_id),
                    actor_id=review.reviewed_by,
                    actor_type=ActorType.HUMAN,
                    reason=review.review_notes,
                )

            logger.info(
                "policy_proposal_approved",
                extra={
                    "proposal_id": str(proposal_id),
                    "reviewed_by": review.reviewed_by,
                    "effective_from": effective_from.isoformat(),
                    "version": version_count + 1,
                    "policy_rule_id": rule_id,
                },
            )

            return {
                "id": str(proposal_id),
                "status": "approved",
                "reviewed_by": review.reviewed_by,
                "reviewed_at": now.isoformat(),
                "effective_from": effective_from.isoformat(),
                "policy_rule_id": rule_id,
            }

        elif review.action == "reject":
            # Update proposal status
            await self._write.update_proposal_status(
                proposal_id=proposal_id,
                new_status="rejected",
                reviewed_at=now,
                reviewed_by=review.reviewed_by,
                review_notes=review.review_notes,
            )

            # Emit audit event for rejection (PIN-504: audit injected by L4)
            if audit:
                await audit.policy_proposal_rejected(
                    tenant_id=proposal["tenant_id"],
                    proposal_id=str(proposal_id),
                    actor_id=review.reviewed_by,
                    actor_type=ActorType.HUMAN,
                    reason=review.review_notes,
                )

            logger.info(
                "policy_proposal_rejected",
                extra={
                    "proposal_id": str(proposal_id),
                    "reviewed_by": review.reviewed_by,
                    "reason": review.review_notes,
                },
            )

            return {
                "id": str(proposal_id),
                "status": "rejected",
                "reviewed_by": review.reviewed_by,
                "reviewed_at": now.isoformat(),
            }

        else:
            raise ValueError(
                f"Invalid action: {review.action}. Must be 'approve' or 'reject'."
            )

    async def _create_policy_rule_from_proposal(
        self,
        proposal: dict,
        approved_by: str,
    ) -> str:
        """
        Create a policy_rule from an approved proposal.

        POST-APPROVAL HOOK (PB-S4 Bridge):
        - Called only when a human approves a proposal
        - Creates exactly 1 policy_rule per proposal (idempotent via ON CONFLICT)
        - Rule is immediately active for enforcement
        """
        # Deterministic rule_id from proposal_id (idempotency)
        proposal_id = proposal["id"].replace("-", "")[:16]
        rule_id = f"rule_{proposal_id}"

        # Check if rule already exists
        if await self._read.check_rule_exists(rule_id):
            logger.info(
                "policy_rule_already_exists",
                extra={"rule_id": rule_id, "proposal_id": proposal["id"]},
            )
            return rule_id

        # Extract conditions and actions from proposed_rule
        proposed_rule = proposal["proposed_rule"] or {}
        conditions = proposed_rule.get("trigger", proposed_rule.get("conditions", {}))
        actions = proposed_rule.get("action", proposed_rule.get("actions", {}))

        # Extract source incident ID from triggering_feedback_ids if present
        triggering_ids = proposal["triggering_feedback_ids"] or []
        source_incident_id = triggering_ids[0] if triggering_ids else None

        # Create the rule via driver
        await self._write.create_policy_rule(
            rule_id=rule_id,
            tenant_id=proposal["tenant_id"],
            name=proposal["proposal_name"],
            description=proposal["rationale"] or "",
            rule_type=proposal["proposal_type"],
            conditions=conditions,
            actions=actions,
            source_incident_id=source_incident_id,
            is_synthetic=proposal.get("is_synthetic", False),
            synthetic_scenario_id=proposal.get("synthetic_scenario_id"),
        )

        logger.info(
            "policy_rule_created_from_proposal",
            extra={
                "rule_id": rule_id,
                "proposal_id": proposal["id"],
                "proposal_type": proposal["proposal_type"],
                "tenant_id": proposal["tenant_id"],
                "approved_by": approved_by,
                "is_synthetic": proposal.get("is_synthetic", False),
            },
        )

        return rule_id

    async def delete_policy_rule(
        self,
        session: "AsyncSession",
        rule_id: str,
        tenant_id: str,
        deleted_by: str,
    ) -> bool:
        """
        Delete a policy rule with GOV-POL-002 enforcement.

        GOV-POL-002: Dependency resolution is mandatory pre-delete.
        A policy cannot be deleted if other policies depend on it.

        Returns True if deleted successfully.

        Raises:
            PolicyDeletionBlockedError: If dependents exist (GOV-POL-002)
            ValueError: If rule not found
        """
        # =========================================================================
        # GOV-POL-002: Dependency resolution is mandatory pre-delete
        # =========================================================================
        dependency_engine = get_dependency_engine(tenant_id)
        can_delete, dependents = await dependency_engine.check_can_delete(
            session, rule_id
        )

        if not can_delete:
            logger.warning(
                "GOV-POL-002_DELETION_BLOCKED",
                extra={
                    "rule_id": rule_id,
                    "tenant_id": tenant_id,
                    "dependent_count": len(dependents),
                    "dependents": dependents,
                },
            )
            raise PolicyDeletionBlockedError(
                f"Cannot delete: {len(dependents)} policies depend on this rule. "
                f"Dependents: {', '.join(dependents)}",
                dependents=dependents,
            )

        # Check if rule exists and belongs to tenant
        rule = await self._read.fetch_rule_by_id(rule_id, tenant_id)

        if not rule:
            raise ValueError(
                f"Policy rule {rule_id} not found or does not belong to tenant"
            )

        # Delete the rule
        deleted = await self._write.delete_policy_rule(rule_id, tenant_id)

        logger.info(
            "GOV-POL-002_DELETION_ALLOWED",
            extra={
                "rule_id": rule_id,
                "rule_name": rule["name"],
                "tenant_id": tenant_id,
                "deleted_by": deleted_by,
            },
        )

        return deleted

    async def get_proposal_summary(
        self,
        tenant_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> dict:
        """
        Get policy proposal summary for ops visibility.

        PB-S4: Read-only query of proposals table.
        """
        proposals = await self._read.fetch_proposals(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
        )

        # Count by status (business logic)
        status_counts: dict[str, int] = {}
        for proposal in proposals:
            s = proposal["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total": len(proposals),
            "by_status": status_counts,
            "proposals": [
                {
                    "id": p["id"],
                    "proposal_name": p["proposal_name"],
                    "proposal_type": p["proposal_type"],
                    "status": p["status"],
                    "rationale": (p["rationale"] or "")[:200],
                    "created_at": (
                        p["created_at"].isoformat() if p["created_at"] else None
                    ),
                    "reviewed_at": (
                        p["reviewed_at"].isoformat() if p["reviewed_at"] else None
                    ),
                    "reviewed_by": p["reviewed_by"],
                    "effective_from": (
                        p["effective_from"].isoformat() if p["effective_from"] else None
                    ),
                    "provenance_count": (
                        len(p["triggering_feedback_ids"])
                        if p["triggering_feedback_ids"]
                        else 0
                    ),
                }
                for p in proposals
            ],
        }


# =============================================================================
# Helper Functions (Backward Compatibility)
# =============================================================================


def generate_default_rule(policy_type: str, feedback_type: str) -> dict:
    """
    Generate a default rule template based on policy type.

    PB-S4: These are SUGGESTIONS only. Human must review.
    """
    if policy_type == "retry_policy":
        return {
            "type": "retry_policy",
            "max_retries": 3,
            "backoff_seconds": [1, 5, 15],
            "retry_on_errors": ["timeout", "rate_limit"],
            "note": "DRAFT - Requires human approval before enforcement",
        }
    elif policy_type == "cost_cap":
        return {
            "type": "cost_cap",
            "max_cost_cents_per_run": 100,
            "warning_threshold_percent": 80,
            "action_on_exceed": "warn",
            "note": "DRAFT - Requires human approval before enforcement",
        }
    else:
        return {
            "type": policy_type,
            "rule": "custom",
            "note": "DRAFT - Requires human review and customization",
        }


# =============================================================================
# Factory Functions
# =============================================================================


def get_policy_proposal_engine(session: "AsyncSession") -> PolicyProposalEngine:
    """Get a PolicyProposalEngine instance with drivers."""
    return PolicyProposalEngine(
        read_driver=get_policy_proposal_read_driver(session),
        write_driver=get_policy_proposal_write_driver(session),
    )


# =============================================================================
# Backward Compatibility - Module-Level Functions
# =============================================================================
# These functions maintain backward compatibility with existing callers.
# They create an engine instance and delegate to the appropriate method.


async def check_proposal_eligibility(
    session: "AsyncSession",
    tenant_id: Optional[UUID] = None,
    feedback_type: Optional[str] = None,
    threshold: int = FEEDBACK_THRESHOLD_FOR_PROPOSAL,
) -> list[dict]:
    """Backward-compatible wrapper for eligibility checking."""
    engine = get_policy_proposal_engine(session)
    return await engine.check_proposal_eligibility(
        tenant_id=tenant_id,
        feedback_type=feedback_type,
        threshold=threshold,
    )


async def create_policy_proposal(
    session: "AsyncSession",
    proposal: PolicyProposalCreate,
) -> str:
    """Backward-compatible wrapper for proposal creation."""
    engine = get_policy_proposal_engine(session)
    return await engine.create_proposal(proposal)


async def review_policy_proposal(
    session: "AsyncSession",
    proposal_id: UUID,
    review: PolicyApprovalRequest,
    audit: Any = None,
) -> dict:
    """Backward-compatible wrapper for proposal review."""
    engine = get_policy_proposal_engine(session)
    return await engine.review_proposal(session, proposal_id, review, audit=audit)


async def delete_policy_rule(
    session: "AsyncSession",
    rule_id: str,
    tenant_id: str,
    deleted_by: str,
) -> bool:
    """Backward-compatible wrapper for rule deletion."""
    engine = get_policy_proposal_engine(session)
    return await engine.delete_policy_rule(session, rule_id, tenant_id, deleted_by)


async def get_proposal_summary(
    session: "AsyncSession",
    tenant_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Backward-compatible wrapper for proposal summary."""
    engine = get_policy_proposal_engine(session)
    return await engine.get_proposal_summary(
        tenant_id=tenant_id,
        status=status,
        limit=limit,
    )


__all__ = [
    # Engine
    "PolicyProposalEngine",
    "get_policy_proposal_engine",
    # Exceptions
    "PolicyActivationBlockedError",
    "PolicyDeletionBlockedError",
    # Constants
    "FEEDBACK_THRESHOLD_FOR_PROPOSAL",
    "PROPOSAL_TYPES",
    # Helper functions
    "generate_default_rule",
    # Backward-compatible functions
    "check_proposal_eligibility",
    "create_policy_proposal",
    "review_policy_proposal",
    "delete_policy_rule",
    "get_proposal_summary",
]
