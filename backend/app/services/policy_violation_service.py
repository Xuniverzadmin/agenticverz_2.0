# Layer: L4 — Service Wrapper
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: worker (sync context)
#   Execution: sync
# Role: L4 wrapper for policy violation sync operations - owns transaction boundary
# Callers: run_governance_facade.py
# Allowed Imports: L6 drivers, stdlib
# Forbidden Imports: L1, L2
# Reference: PIN-520 (L4 Transaction Ownership)

"""
Policy Violation Service (L4 Transaction Owner)

This service wraps the L6 driver's sync operations and owns the
transaction boundary (connection lifecycle and commit).

L4 Contract:
    - L4 creates the psycopg2 connection
    - L4 calls L6 driver (which executes, does NOT commit)
    - L4 commits and closes the connection

Why This Exists:
    - L6 drivers must NOT commit (PIN-520)
    - Sync worker contexts need psycopg2 (async not available)
    - This L4 wrapper owns the transaction boundary for sync paths
"""

import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger("nova.services.policy_violation")


def create_policy_evaluation_sync(
    run_id: str,
    tenant_id: str,
    run_status: str,
    policies_checked: int = 0,
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
) -> Optional[str]:
    """
    Create a policy evaluation record for a run (sync path).

    L4 Transaction Owner: This function owns the psycopg2 connection
    lifecycle and commits after the L6 driver executes.

    Args:
        run_id: ID of the run
        tenant_id: Tenant scope
        run_status: Run outcome (succeeded, failed, halted, etc.)
        policies_checked: Number of policies evaluated
        is_synthetic: Whether this is a synthetic/test run
        synthetic_scenario_id: SDSR scenario ID if synthetic

    Returns:
        policy_evaluation_id if created, None otherwise
    """
    import uuid
    from datetime import timezone

    import psycopg2

    from app.hoc.cus.incidents.L6_drivers.policy_violation_driver import (
        insert_policy_evaluation_sync_with_cursor,
    )

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return None

    # Generate evaluation ID
    evaluation_id = str(uuid.uuid4())

    # Map run_status to policy outcome
    outcome = "no_violation" if run_status == "succeeded" else "evaluation_error"
    confidence = 1.0 if outcome == "no_violation" else 0.0
    created_at = datetime.now(timezone.utc)

    try:
        # L4 owns connection lifecycle
        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor() as cursor:
                # L6 executes, L4 commits
                result = insert_policy_evaluation_sync_with_cursor(
                    cursor=cursor,
                    evaluation_id=evaluation_id,
                    run_id=run_id,
                    tenant_id=tenant_id,
                    outcome=outcome,
                    policies_checked=policies_checked,
                    confidence=confidence,
                    created_at=created_at,
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )
                # L4 owns transaction boundary - commit here
                conn.commit()
                return result
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"policy_eval_sync_error: {e}")
        return None


__all__ = [
    "create_policy_evaluation_sync",
]
