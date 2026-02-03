# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L4 coordinator)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_enforcements, policy_rules
#   Writes: none (read-only)
# Database:
#   Scope: domain (policies)
#   Models: PolicyEnforcement, PolicyRule
# Role: Policy enforcement read operations for run introspection
# Callers: L4 coordinators (run_evidence_coordinator)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-519 (System Run Introspection)

"""
Policy Enforcement Read Driver (PIN-519)

Provides async read operations for policy enforcement records.
Used by L4 coordinators to gather policy evaluations for runs.

INVARIANTS:
- Read-only operations (no INSERT, UPDATE, DELETE)
- Queries are tenant-scoped
- Returns enforcement records with rule details
"""

import logging
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import PolicyEnforcement, PolicyRule

logger = logging.getLogger("nova.hoc.policies.policy_enforcement_driver")


class PolicyEnforcementReadDriver:
    """
    Async driver for reading policy enforcement records.

    L6 CONTRACT:
    - Pure database reads, no business logic
    - All methods are async (for use with AsyncSession)
    - Queries happen within caller's transaction
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def fetch_policy_evaluations_for_run(
        self,
        tenant_id: str,
        run_id: str,
        max_results: int = 100,
    ) -> list[dict]:
        """
        Fetch all policy evaluations (enforcements) for a run.

        Args:
            tenant_id: Tenant owning the run
            run_id: Run ID to query evaluations for
            max_results: Maximum records to return

        Returns:
            List of enforcement records with rule details
        """
        stmt = (
            select(
                PolicyEnforcement.id.label("enforcement_id"),
                PolicyEnforcement.rule_id,
                PolicyEnforcement.action_taken,
                PolicyEnforcement.triggered_at,
                PolicyEnforcement.details,
                PolicyRule.name.label("rule_name"),
                PolicyRule.rule_type,
                PolicyRule.severity,
            )
            .join(PolicyRule, PolicyRule.id == PolicyEnforcement.rule_id)
            .where(
                and_(
                    PolicyEnforcement.tenant_id == tenant_id,
                    PolicyEnforcement.run_id == run_id,
                )
            )
            .order_by(desc(PolicyEnforcement.triggered_at))
            .limit(max_results)
        )

        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]

    async def fetch_enforcement_by_id(
        self,
        tenant_id: str,
        enforcement_id: str,
    ) -> Optional[dict]:
        """
        Fetch a single enforcement record by ID.

        Args:
            tenant_id: Tenant owning the enforcement
            enforcement_id: Enforcement ID to fetch

        Returns:
            Enforcement record with rule details, or None if not found
        """
        stmt = (
            select(
                PolicyEnforcement.id.label("enforcement_id"),
                PolicyEnforcement.rule_id,
                PolicyEnforcement.run_id,
                PolicyEnforcement.incident_id,
                PolicyEnforcement.action_taken,
                PolicyEnforcement.triggered_at,
                PolicyEnforcement.details,
                PolicyRule.name.label("rule_name"),
                PolicyRule.rule_type,
                PolicyRule.severity,
            )
            .join(PolicyRule, PolicyRule.id == PolicyEnforcement.rule_id)
            .where(
                and_(
                    PolicyEnforcement.tenant_id == tenant_id,
                    PolicyEnforcement.id == enforcement_id,
                )
            )
        )

        result = await self._session.execute(stmt)
        row = result.first()

        if not row:
            return None

        return dict(row._mapping)


# =============================================================================
# Factory
# =============================================================================


def get_policy_enforcement_read_driver(
    session: AsyncSession,
) -> PolicyEnforcementReadDriver:
    """
    Get a PolicyEnforcementReadDriver instance.

    Args:
        session: Async database session

    Returns:
        PolicyEnforcementReadDriver instance
    """
    return PolicyEnforcementReadDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PolicyEnforcementReadDriver",
    "get_policy_enforcement_read_driver",
]
