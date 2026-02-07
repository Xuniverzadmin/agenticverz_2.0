# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: internal
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: policy_proposals, policy_versions, policy_rules
# Role: Write operations for policy proposal engine
# Callers: L5 policy_proposal_engine
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase 3B P3 Design-First
"""
Policy Proposal Write Driver (L6)

Pure data access layer for policy proposal write operations.
No business logic - only persistence and mutations.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import PolicyProposal, PolicyVersion


class PolicyProposalWriteDriver:
    """Write operations for policy proposals."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_proposal(
        self,
        tenant_id: str,
        proposal_name: str,
        proposal_type: str,
        rationale: str,
        proposed_rule: dict[str, Any],
        triggering_feedback_ids: list[str],
    ) -> str:
        """
        Create a new policy proposal in draft status.

        Returns the proposal ID.
        """
        record = PolicyProposal(
            tenant_id=tenant_id,
            proposal_name=proposal_name,
            proposal_type=proposal_type,
            rationale=rationale,
            proposed_rule=proposed_rule,
            triggering_feedback_ids=triggering_feedback_ids,
            status="draft",
            created_at=datetime.now(timezone.utc),
        )

        self._session.add(record)
        await self._session.flush()

        return str(record.id)

    async def update_proposal_status(
        self,
        proposal_id: UUID,
        new_status: str,
        reviewed_at: Optional[datetime] = None,
        reviewed_by: Optional[str] = None,
        review_notes: Optional[str] = None,
        effective_from: Optional[datetime] = None,
    ) -> bool:
        """
        Update a proposal's status and review metadata.

        Returns True if proposal was found and updated.
        """
        from sqlalchemy import update

        stmt = (
            update(PolicyProposal)
            .where(PolicyProposal.id == proposal_id)
            .values(
                status=new_status,
                reviewed_at=reviewed_at,
                reviewed_by=reviewed_by,
                review_notes=review_notes,
                effective_from=effective_from,
            )
        )

        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def create_version(
        self,
        proposal_id: UUID,
        version_number: int,
        rule_snapshot: dict[str, Any],
        created_by: str,
        change_reason: str,
    ) -> str:
        """
        Create a policy version snapshot.

        Returns the version ID.
        """
        version = PolicyVersion(
            proposal_id=proposal_id,
            version=version_number,
            rule_snapshot=rule_snapshot,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            change_reason=change_reason,
        )

        self._session.add(version)
        await self._session.flush()

        return str(version.id)

    async def create_policy_rule(
        self,
        rule_id: str,
        tenant_id: str,
        name: str,
        description: str,
        rule_type: str,
        conditions: dict[str, Any],
        actions: dict[str, Any],
        source_incident_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> str:
        """
        Create a policy rule from an approved proposal.

        Idempotent - uses ON CONFLICT DO NOTHING pattern.
        Returns the rule ID.
        """
        now = datetime.now(timezone.utc)

        await self._session.execute(
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
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": rule_id,
                "tenant_id": tenant_id,
                "name": name,
                "description": description[:500] if description else "",
                "rule_type": rule_type,
                "conditions": json.dumps(conditions),
                "actions": json.dumps(actions),
                "priority": 100,
                "is_active": True,
                "source_type": "proposal",
                "source_incident_id": source_incident_id,
                "mode": "active",
                "confirmations_required": 0,
                "confirmations_received": 1,
                "activated_at": now,
                "created_at": now,
                "updated_at": now,
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
            },
        )

        return rule_id

    async def delete_policy_rule(
        self,
        rule_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete a policy rule.

        Returns True if rule was deleted.
        """
        result = await self._session.execute(
            text("""
                DELETE FROM policy_rules
                WHERE id = :rule_id AND tenant_id = :tenant_id
            """),
            {"rule_id": rule_id, "tenant_id": tenant_id},
        )

        return result.rowcount > 0


def get_policy_proposal_write_driver(
    session: AsyncSession,
) -> PolicyProposalWriteDriver:
    """Factory function for PolicyProposalWriteDriver."""
    return PolicyProposalWriteDriver(session)


__all__ = [
    "PolicyProposalWriteDriver",
    "get_policy_proposal_write_driver",
]
