# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: worker (during step enforcement)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: policy_enforcements
# Database:
#   Scope: domain (policies)
#   Models: PolicyEnforcement
# Role: Policy enforcement write operations for recording enforcement outcomes
# Callers: step_enforcement (int/general/drivers), prevention_engine (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-524 (Phase 3 Legacy Import Deprecation), GAP-016

"""
Policy Enforcement Write Driver

Provides async write operations for policy enforcement records.
Records when policy rules trigger STOP/KILL/BLOCK actions.

INVARIANTS:
- Append-only writes (no UPDATE, DELETE)
- All writes are tenant-scoped
- Records include rule_id, run_id, action_taken, details

PIN-412: Enforcements are append-only history.
Used for trigger_count_30d and last_triggered_at derivations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import PolicyEnforcement

logger = logging.getLogger("nova.hoc.policies.policy_enforcement_write_driver")


def _generate_enforcement_id() -> str:
    """Generate a unique enforcement ID."""
    return f"enf_{uuid4().hex[:16]}"


def _utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class PolicyEnforcementWriteDriver:
    """
    Async driver for writing policy enforcement records.

    L6 CONTRACT:
    - Pure database writes, no business logic
    - All methods are async (for use with AsyncSession)
    - Writes happen within caller's transaction (caller owns commit)
    - Append-only: no updates or deletes
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def record_enforcement(
        self,
        tenant_id: str,
        rule_id: str,
        action_taken: str,
        run_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a policy enforcement event.

        Called when a policy rule triggers an enforcement action (BLOCKED, WARNED, etc.).
        This creates an append-only audit trail of policy enforcement history.

        Args:
            tenant_id: Tenant owning the run
            rule_id: Policy rule that triggered
            action_taken: Action taken (BLOCKED, WARNED, AUDITED, STOPPED, KILLED)
            run_id: Optional run ID that was affected
            incident_id: Optional incident ID if one was created
            details: Optional enforcement details (context, reason, etc.)

        Returns:
            Enforcement record ID

        Transaction Semantics:
            - This method does NOT commit the transaction
            - Caller owns the transaction and must commit when ready
            - This allows atomic recording with other operations
        """
        enforcement_id = _generate_enforcement_id()

        enforcement = PolicyEnforcement(
            id=enforcement_id,
            tenant_id=tenant_id,
            rule_id=rule_id,
            run_id=run_id,
            incident_id=incident_id,
            action_taken=action_taken,
            details=details or {},
            triggered_at=_utc_now(),
        )

        self._session.add(enforcement)
        await self._session.flush()  # Flush to validate, but don't commit

        logger.info(
            "policy_enforcement.recorded",
            extra={
                "enforcement_id": enforcement_id,
                "tenant_id": tenant_id,
                "rule_id": rule_id,
                "run_id": run_id,
                "action_taken": action_taken,
            },
        )

        return enforcement_id

    async def record_enforcement_batch(
        self,
        tenant_id: str,
        enforcements: list[Dict[str, Any]],
    ) -> list[str]:
        """
        Record multiple policy enforcement events atomically.

        Args:
            tenant_id: Tenant owning the enforcements
            enforcements: List of enforcement dicts with keys:
                - rule_id (required)
                - action_taken (required)
                - run_id (optional)
                - incident_id (optional)
                - details (optional)

        Returns:
            List of enforcement record IDs

        Transaction Semantics:
            - All records are created within the same flush
            - Caller owns commit
        """
        enforcement_ids = []

        for enf_data in enforcements:
            enforcement_id = _generate_enforcement_id()

            enforcement = PolicyEnforcement(
                id=enforcement_id,
                tenant_id=tenant_id,
                rule_id=enf_data["rule_id"],
                run_id=enf_data.get("run_id"),
                incident_id=enf_data.get("incident_id"),
                action_taken=enf_data["action_taken"],
                details=enf_data.get("details", {}),
                triggered_at=_utc_now(),
            )

            self._session.add(enforcement)
            enforcement_ids.append(enforcement_id)

        await self._session.flush()

        logger.info(
            "policy_enforcement.batch_recorded",
            extra={
                "tenant_id": tenant_id,
                "count": len(enforcement_ids),
            },
        )

        return enforcement_ids


# =============================================================================
# Factory
# =============================================================================


def get_policy_enforcement_write_driver(
    session: AsyncSession,
) -> PolicyEnforcementWriteDriver:
    """
    Get a PolicyEnforcementWriteDriver instance.

    Args:
        session: Async database session

    Returns:
        PolicyEnforcementWriteDriver instance
    """
    return PolicyEnforcementWriteDriver(session)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "PolicyEnforcementWriteDriver",
    "get_policy_enforcement_write_driver",
]
