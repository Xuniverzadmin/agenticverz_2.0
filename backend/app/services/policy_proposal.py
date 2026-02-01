# Layer: L3 — Boundary Adapter (Console → Platform)
# Product: AI Console
# Callers: None (ORPHAN - pending M25+ integration)
# Reference: PIN-240
# NOTE: Service complete, UI integration missing. Human approval required.

"""
Policy Proposal Service (PB-S4)

Proposes policy changes based on observed feedback WITHOUT auto-enforcement.

PB-S4 Contract:
- Observe feedback patterns → propose policy → wait for human
- NO auto-enforcement
- NO execution modification
- Human approval is MANDATORY

Rule: Propose → Review → Decide (Human)
"""

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.audit_ledger import ActorType
from app.models.feedback import PatternFeedback
from app.models.policy import (
    PolicyApprovalRequest,
    PolicyProposal,
    PolicyProposalCreate,
    PolicyVersion,
)
# TRANSITIONAL: services→hoc (migrate policy_proposal to HOC L5 per PIN-507)
from app.hoc.cus.logs.L6_drivers.audit_ledger_driver import AuditLedgerServiceAsync
from app.services.policy_graph_engine import (
    ConflictSeverity,
    get_conflict_engine,
    get_dependency_engine,
)

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


async def check_proposal_eligibility(
    session: AsyncSession,
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
    query = (
        select(PatternFeedback).where(PatternFeedback.acknowledged == False)  # Only unacknowledged
    )

    if tenant_id:
        query = query.where(PatternFeedback.tenant_id == str(tenant_id))
    if feedback_type:
        query = query.where(PatternFeedback.pattern_type == feedback_type)

    result = await session.execute(query)
    feedback_records = result.scalars().all()

    if not feedback_records:
        return []

    # Group by pattern_type and signature
    groups: dict[str, list[PatternFeedback]] = {}
    for fb in feedback_records:
        key = f"{fb.pattern_type}:{fb.signature or 'none'}"
        if key not in groups:
            groups[key] = []
        groups[key].append(fb)

    # Find eligible groups
    eligible = []
    for key, fbs in groups.items():
        if len(fbs) >= threshold:
            pattern_type = fbs[0].pattern_type
            eligible.append(
                {
                    "feedback_type": pattern_type,
                    "count": len(fbs),
                    "feedback_ids": [str(f.id) for f in fbs],
                    "signature": fbs[0].signature,
                    "tenant_id": str(fbs[0].tenant_id),
                    "suggested_policy_type": PROPOSAL_TYPES.get(pattern_type, "custom"),
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


async def create_policy_proposal(
    session: AsyncSession,
    proposal: PolicyProposalCreate,
) -> PolicyProposal:
    """
    Create a policy proposal.

    PB-S4: This creates a DRAFT record. No enforcement.
    Status starts as 'draft' - human approval required.
    """
    record = PolicyProposal(
        tenant_id=proposal.tenant_id,
        proposal_name=proposal.proposal_name,
        proposal_type=proposal.proposal_type,
        rationale=proposal.rationale,
        proposed_rule=proposal.proposed_rule,
        triggering_feedback_ids=proposal.triggering_feedback_ids,
        status="draft",  # Always starts as draft
        created_at=datetime.utcnow(),
    )

    session.add(record)
    await session.flush()

    logger.info(
        "policy_proposal_created",
        extra={
            "proposal_id": str(record.id),
            "proposal_type": record.proposal_type,
            "tenant_id": str(record.tenant_id),
            "status": record.status,
            "provenance_count": len(record.triggering_feedback_ids),
        },
    )

    return record


async def _create_policy_rule_from_proposal(
    session: AsyncSession,
    proposal: PolicyProposal,
    version_id: Optional[UUID],
    approved_by: str,
) -> str:
    """
    Create a policy_rule from an approved proposal.

    POST-APPROVAL HOOK (PB-S4 Bridge):
    - Called only when a human approves a proposal
    - Creates exactly 1 policy_rule per proposal (idempotent via ON CONFLICT)
    - Rule is immediately active for enforcement
    - No SDSR-specific logic - works identically for real and synthetic

    Args:
        session: Database session
        proposal: The approved PolicyProposal
        version_id: The PolicyVersion ID (for provenance)
        approved_by: User who approved

    Returns:
        policy_rule ID (deterministic from proposal_id)
    """
    # Deterministic rule_id from proposal_id (idempotency)
    rule_id = f"rule_{str(proposal.id).replace('-', '')[:16]}"

    # Extract conditions and actions from proposed_rule
    proposed_rule = proposal.proposed_rule or {}
    conditions = proposed_rule.get("trigger", proposed_rule.get("conditions", {}))
    actions = proposed_rule.get("action", proposed_rule.get("actions", {}))

    # Build rule metadata
    now = datetime.utcnow()

    # Check if rule already exists (idempotency)
    existing = await session.execute(
        text("SELECT id FROM policy_rules WHERE id = :rule_id"),
        {"rule_id": rule_id},
    )
    if existing.scalar_one_or_none():
        logger.info(
            "policy_rule_already_exists",
            extra={"rule_id": rule_id, "proposal_id": str(proposal.id)},
        )
        return rule_id

    # Extract source incident ID from triggering_feedback_ids if present
    triggering_ids = proposal.triggering_feedback_ids or []
    source_incident_id = triggering_ids[0] if triggering_ids else None

    # Insert policy_rule
    await session.execute(
        text("""
            INSERT INTO policy_rules (
                id, tenant_id, name, description, rule_type,
                conditions, actions, priority, is_active,
                source_type, source_incident_id,
                mode, confirmations_required, confirmations_received,
                regret_count, shadow_evaluations, shadow_would_block,
                activated_at, created_at, updated_at,
                is_synthetic, synthetic_scenario_id
            ) VALUES (
                :id, :tenant_id, :name, :description, :rule_type,
                CAST(:conditions AS jsonb), CAST(:actions AS jsonb),
                :priority, :is_active,
                :source_type, :source_incident_id,
                :mode, :confirmations_required, :confirmations_received,
                0, 0, 0,
                :activated_at, :created_at, :updated_at,
                :is_synthetic, :synthetic_scenario_id
            )
        """),
        {
            "id": rule_id,
            "tenant_id": str(proposal.tenant_id),
            "name": str(proposal.proposal_name),
            "description": str(proposal.rationale)[:500] if proposal.rationale else "",
            "rule_type": str(proposal.proposal_type),
            "conditions": json.dumps(conditions),
            "actions": json.dumps(actions),
            "priority": 100,
            "is_active": True,
            "source_type": "proposal",
            "source_incident_id": source_incident_id,
            "mode": "active",
            "confirmations_required": 0,  # Already approved by human
            "confirmations_received": 1,  # Human approval counts
            "activated_at": now,
            "created_at": now,
            "updated_at": now,
            # Propagate synthetic flags from proposal (works for both real and SDSR)
            # Note: SQLAlchemy columns are accessed directly, not via getattr
            "is_synthetic": proposal.is_synthetic if hasattr(proposal, 'is_synthetic') and proposal.is_synthetic else False,
            "synthetic_scenario_id": proposal.synthetic_scenario_id if hasattr(proposal, 'synthetic_scenario_id') else None,
        },
    )

    logger.info(
        "policy_rule_created_from_proposal",
        extra={
            "rule_id": rule_id,
            "proposal_id": str(proposal.id),
            "proposal_type": str(proposal.proposal_type),
            "tenant_id": str(proposal.tenant_id),
            "approved_by": approved_by,
            "is_synthetic": getattr(proposal, 'is_synthetic', False),
        },
    )

    return rule_id


async def review_policy_proposal(
    session: AsyncSession,
    proposal_id: UUID,
    review: PolicyApprovalRequest,
) -> PolicyProposal:
    """
    Review (approve/reject) a policy proposal.

    PB-S4: This is a HUMAN action. The system cannot auto-approve.
    - Approval creates a new version and sets effective_from
    - Rejection marks the proposal as rejected (preserved for audit)

    TRANSACTION CONTRACT:
    - State change and audit event commit together (atomic)
    - If audit emit fails, proposal review rolls back
    - No partial state is possible
    """
    # Fetch the proposal
    result = await session.execute(select(PolicyProposal).where(PolicyProposal.id == proposal_id))
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found")

    if proposal.status != "draft":
        raise ValueError(f"Proposal {proposal_id} is not in draft status (current: {proposal.status})")

    # Create audit service for this session
    audit = AuditLedgerServiceAsync(session)

    # ATOMIC BLOCK: state change + audit must succeed together
    async with session.begin():
        # Update review metadata
        proposal.reviewed_at = datetime.utcnow()
        proposal.reviewed_by = review.reviewed_by
        proposal.review_notes = review.review_notes

        if review.action == "approve":
            # =====================================================================
            # GOV-POL-001: Conflict detection is mandatory pre-activation
            # =====================================================================
            # Check for BLOCKING conflicts before allowing activation.
            # This is CONSTITUTIONAL - cannot be bypassed.
            # =====================================================================
            conflict_engine = get_conflict_engine(str(proposal.tenant_id))
            conflict_result = await conflict_engine.detect_conflicts(
                session,
                severity_filter=ConflictSeverity.BLOCKING,
            )

            if conflict_result.unresolved_count > 0:
                blocking_conflicts = [c.to_dict() for c in conflict_result.conflicts]
                logger.warning(
                    "GOV-POL-001_ACTIVATION_BLOCKED",
                    extra={
                        "proposal_id": str(proposal.id),
                        "blocking_conflicts": len(blocking_conflicts),
                        "conflicts": blocking_conflicts,
                    },
                )
                raise PolicyActivationBlockedError(
                    f"Cannot activate: {conflict_result.unresolved_count} BLOCKING conflicts exist. "
                    f"Resolve conflicts before approval.",
                    conflicts=blocking_conflicts,
                )

            logger.info(
                "GOV-POL-001_CONFLICT_CHECK_PASSED",
                extra={
                    "proposal_id": str(proposal.id),
                    "blocking_conflicts": 0,
                },
            )

            proposal.status = "approved"
            proposal.effective_from = review.effective_from or datetime.utcnow()

            # Create a version snapshot
            # Count existing versions for this proposal
            version_count_result = await session.execute(
                select(func.count()).select_from(PolicyVersion).where(PolicyVersion.proposal_id == proposal_id)
            )
            version_count = version_count_result.scalar() or 0

            version = PolicyVersion(
                proposal_id=proposal.id,
                version=version_count + 1,
                rule_snapshot=proposal.proposed_rule,
                created_at=datetime.utcnow(),
                created_by=review.reviewed_by,
                change_reason=f"Approved: {review.review_notes or 'No notes'}",
            )
            session.add(version)

            # =====================================================================
            # POST-APPROVAL HOOK: Create policy_rule from approved proposal
            # =====================================================================
            # This bridges the gap between policy_proposals and policy_rules.
            # When a proposal is approved, it becomes an enforceable rule.
            #
            # Contract:
            # - Exactly 1 policy_rule per approved proposal (idempotent)
            # - Rule is_active=true, mode='active' (enforcement ready)
            # - No auto-approval logic - this only runs on human action
            # =====================================================================
            rule_id = await _create_policy_rule_from_proposal(
                session=session,
                proposal=proposal,
                version_id=version.id if hasattr(version, 'id') else None,
                approved_by=review.reviewed_by,
            )

            # Emit audit event for approval (PIN-413: Logs Domain)
            await audit.policy_proposal_approved(
                tenant_id=str(proposal.tenant_id),
                proposal_id=str(proposal.id),
                actor_id=review.reviewed_by,
                actor_type=ActorType.HUMAN,
                reason=review.review_notes,
            )

            logger.info(
                "policy_proposal_approved",
                extra={
                    "proposal_id": str(proposal.id),
                    "reviewed_by": review.reviewed_by,
                    "effective_from": proposal.effective_from.isoformat(),
                    "version": version_count + 1,
                    "policy_rule_id": rule_id,
                },
            )

        elif review.action == "reject":
            proposal.status = "rejected"
            # No version created for rejections
            # Proposal preserved for audit trail

            # Emit audit event for rejection (PIN-413: Logs Domain)
            await audit.policy_proposal_rejected(
                tenant_id=str(proposal.tenant_id),
                proposal_id=str(proposal.id),
                actor_id=review.reviewed_by,
                actor_type=ActorType.HUMAN,
                reason=review.review_notes,
            )

            logger.info(
                "policy_proposal_rejected",
                extra={
                    "proposal_id": str(proposal.id),
                    "reviewed_by": review.reviewed_by,
                    "reason": review.review_notes,
                },
            )

        else:
            raise ValueError(f"Invalid action: {review.action}. Must be 'approve' or 'reject'.")

    return proposal


async def generate_proposals_from_feedback(
    tenant_id: Optional[UUID] = None,
    threshold: int = FEEDBACK_THRESHOLD_FOR_PROPOSAL,
) -> dict:
    """
    Generate policy proposals from eligible feedback patterns.

    PB-S4: Creates DRAFT proposals only. No enforcement.

    Returns summary of generated proposals.
    """
    result = {
        "eligible_patterns": [],
        "proposals_created": 0,
        "errors": [],
    }

    try:
        async with get_async_session() as session:
            # Check eligibility
            eligible = await check_proposal_eligibility(session, tenant_id=tenant_id, threshold=threshold)
            result["eligible_patterns"] = eligible

            # Create proposals for eligible patterns
            for pattern in eligible:
                try:
                    # Generate proposal name and rationale
                    proposal_name = f"{pattern['suggested_policy_type']}_{pattern['signature'][:8] if pattern['signature'] else 'general'}"
                    rationale = (
                        f"Based on {pattern['count']} observed {pattern['feedback_type']} patterns. "
                        f"Signature: {pattern['signature'] or 'N/A'}"
                    )

                    # Generate proposed rule based on type
                    proposed_rule = generate_default_rule(
                        pattern["suggested_policy_type"],
                        pattern["feedback_type"],
                    )

                    proposal = PolicyProposalCreate(
                        tenant_id=pattern["tenant_id"],
                        proposal_name=proposal_name,
                        proposal_type=pattern["suggested_policy_type"],
                        rationale=rationale,
                        proposed_rule=proposed_rule,
                        triggering_feedback_ids=pattern["feedback_ids"],
                    )

                    await create_policy_proposal(session, proposal)
                    result["proposals_created"] += 1

                except Exception as e:
                    result["errors"].append(f"Failed to create proposal: {e}")

            await session.commit()

    except Exception as e:
        logger.error(f"policy_proposal_generation_error: {e}", exc_info=True)
        result["errors"].append(str(e))

    return result


async def delete_policy_rule(
    session: AsyncSession,
    rule_id: str,
    tenant_id: str,
    deleted_by: str,
) -> bool:
    """
    Delete a policy rule with GOV-POL-002 enforcement.

    GOV-POL-002: Dependency resolution is mandatory pre-delete.
    A policy cannot be deleted if other policies depend on it.

    Args:
        session: Database session
        rule_id: The rule ID to delete
        tenant_id: Tenant ID for authorization
        deleted_by: User performing the deletion

    Returns:
        True if deleted successfully

    Raises:
        PolicyDeletionBlockedError: If dependents exist (GOV-POL-002)
        ValueError: If rule not found
    """
    # =========================================================================
    # GOV-POL-002: Dependency resolution is mandatory pre-delete
    # =========================================================================
    # Check if any policies depend on this one before allowing deletion.
    # This is CONSTITUTIONAL - cannot be bypassed.
    # =========================================================================
    dependency_engine = get_dependency_engine(tenant_id)
    can_delete, dependents = await dependency_engine.check_can_delete(session, rule_id)

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
    result = await session.execute(
        text("""
            SELECT id, name FROM policy_rules
            WHERE id = :rule_id AND tenant_id = :tenant_id
        """),
        {"rule_id": rule_id, "tenant_id": tenant_id},
    )
    row = result.fetchone()

    if not row:
        raise ValueError(f"Policy rule {rule_id} not found or does not belong to tenant")

    rule_name = row[1]

    # Delete the rule
    await session.execute(
        text("""
            DELETE FROM policy_rules
            WHERE id = :rule_id AND tenant_id = :tenant_id
        """),
        {"rule_id": rule_id, "tenant_id": tenant_id},
    )

    logger.info(
        "GOV-POL-002_DELETION_ALLOWED",
        extra={
            "rule_id": rule_id,
            "rule_name": rule_name,
            "tenant_id": tenant_id,
            "deleted_by": deleted_by,
        },
    )

    return True


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
            "action_on_exceed": "warn",  # warn, not block - human decides
            "note": "DRAFT - Requires human approval before enforcement",
        }
    else:
        return {
            "type": policy_type,
            "rule": "custom",
            "note": "DRAFT - Requires human review and customization",
        }


async def get_proposal_summary(
    tenant_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """
    Get policy proposal summary for ops visibility.

    PB-S4: Read-only query of proposals table.
    """
    async with get_async_session() as session:
        query = select(PolicyProposal).order_by(PolicyProposal.created_at.desc())

        if tenant_id:
            query = query.where(PolicyProposal.tenant_id == str(tenant_id))
        if status:
            query = query.where(PolicyProposal.status == status)

        query = query.limit(limit)

        result = await session.execute(query)
        proposals = result.scalars().all()

        # Count by status
        status_counts: dict[str, int] = {}
        for proposal in proposals:
            s = proposal.status
            status_counts[s] = status_counts.get(s, 0) + 1

        return {
            "total": len(proposals),
            "by_status": status_counts,
            "proposals": [
                {
                    "id": str(p.id),
                    "proposal_name": p.proposal_name,
                    "proposal_type": p.proposal_type,
                    "status": p.status,
                    "rationale": p.rationale[:200],
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None,
                    "reviewed_by": p.reviewed_by,
                    "effective_from": p.effective_from.isoformat() if p.effective_from else None,
                    "provenance_count": len(p.triggering_feedback_ids) if p.triggering_feedback_ids else 0,
                }
                for p in proposals
            ],
        }
