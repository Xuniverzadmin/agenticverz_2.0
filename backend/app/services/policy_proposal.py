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

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.feedback import PatternFeedback
from app.models.policy import (
    PolicyApprovalRequest,
    PolicyProposal,
    PolicyProposalCreate,
    PolicyVersion,
)

logger = logging.getLogger("nova.services.policy_proposal")

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
    """
    # Fetch the proposal
    result = await session.execute(select(PolicyProposal).where(PolicyProposal.id == proposal_id))
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found")

    if proposal.status != "draft":
        raise ValueError(f"Proposal {proposal_id} is not in draft status (current: {proposal.status})")

    # Update review metadata
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by = review.reviewed_by
    proposal.review_notes = review.review_notes

    if review.action == "approve":
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

        logger.info(
            "policy_proposal_approved",
            extra={
                "proposal_id": str(proposal.id),
                "reviewed_by": review.reviewed_by,
                "effective_from": proposal.effective_from.isoformat(),
                "version": version_count + 1,
            },
        )

    elif review.action == "reject":
        proposal.status = "rejected"
        # No version created for rejections
        # Proposal preserved for audit trail

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

    await session.flush()
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
