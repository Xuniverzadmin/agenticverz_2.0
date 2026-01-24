# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Data access for policy violation operations (async + sync)
# Callers: PolicyViolationService (L4)
# Allowed Imports: sqlalchemy, psycopg2
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for policy violation operations.
# NO business logic - only DB operations.
# Business logic (outcome mapping, verification mode, validation) stays in L4 engine.
#
# EXTRACTION STATUS:
# - 2026-01-23: Initial extraction from policy_violation_service.py (PIN-468)
#
# ============================================================================
# L6 DRIVER INVENTORY — POLICY VIOLATION DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose
# ----------------------------------- | ----------------------------------------
# insert_violation_record             | Create violation fact in prevention_records
# fetch_violation_exists              | Check if violation record exists
# fetch_policy_enabled                | Check if policy is active for tenant
# insert_evidence_event               | Create evidence capture event
# fetch_incident_by_violation         | Check for existing incident
# fetch_violation_truth_check         | Get violation truth verification data
# insert_policy_evaluation            | Create policy evaluation record (async)
# insert_policy_evaluation_sync       | Create policy evaluation record (sync)
# commit                              | Transaction commit
# ============================================================================
# This is the SINGLE persistence authority for policy violation writes.
# Do NOT create competing drivers. Extend this file.
# ============================================================================

"""
Policy Violation Driver (L6)

Pure database operations for policy violation handling.
All business logic stays in L4 engine.

Operations:
- Create violation facts
- Check violation/policy existence
- Create evidence events
- Policy evaluation records (both async and sync patterns)

NO business logic:
- NO outcome mapping (L4)
- NO verification mode decisions (L4)
- NO validation decisions (L4)
- NO severity mapping (L4)

Reference: PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.drivers.policy_violation")


class PolicyViolationDriver:
    """
    L6 driver for policy violation operations (async).

    Pure database access - no business logic.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    async def insert_violation_record(
        self,
        violation_id: str,
        policy_id: str,
        rule_id: str,
        run_id: str,
        tenant_id: str,
        created_at: datetime,
    ) -> None:
        """
        Insert a violation fact record into prevention_records.

        Args:
            violation_id: Generated violation ID
            policy_id: Policy that was violated
            rule_id: Specific rule within policy
            run_id: Run that triggered the violation
            tenant_id: Tenant scope
            created_at: Timestamp (naive datetime for asyncpg)
        """
        # Use naive datetime for asyncpg compatibility
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)

        await self._session.execute(
            text(
                """
                INSERT INTO prevention_records (
                    id, policy_id, pattern_id, original_incident_id, blocked_incident_id,
                    tenant_id, outcome, signature_match_confidence, created_at, is_simulated
                ) VALUES (
                    :id, :policy_id, :rule_id, :run_id, :run_id,
                    :tenant_id, 'violation_incident', 1.0, :created_at, false
                )
            """
            ),
            {
                "id": violation_id,
                "policy_id": policy_id,
                "rule_id": rule_id,
                "run_id": run_id,
                "tenant_id": tenant_id,
                "created_at": created_at,
            },
        )

    async def fetch_violation_exists(self, violation_id: str) -> bool:
        """
        Check if a violation fact has been persisted.

        Args:
            violation_id: Violation ID to check

        Returns:
            True if exists, False otherwise
        """
        result = await self._session.execute(
            text("SELECT id FROM prevention_records WHERE id = :id"),
            {"id": violation_id},
        )
        return result.scalar_one_or_none() is not None

    async def fetch_policy_enabled(self, tenant_id: str, policy_id: str) -> bool:
        """
        Check if policy is active for tenant.

        Args:
            tenant_id: Tenant scope
            policy_id: Policy to check

        Returns:
            True if policy is enabled, False otherwise
        """
        result = await self._session.execute(
            text(
                """
                SELECT id FROM policy_rules
                WHERE tenant_id = :tenant_id
                AND (id = :policy_id OR policy_type = :policy_id)
                AND is_active = true
                AND status = 'active'
                LIMIT 1
            """
            ),
            {"tenant_id": tenant_id, "policy_id": policy_id},
        )
        return result.scalar_one_or_none() is not None

    async def insert_evidence_event(
        self,
        evidence_id: str,
        incident_id: str,
        violation_id: str,
        evidence: Dict[str, Any],
    ) -> None:
        """
        Insert evidence capture event.

        Args:
            evidence_id: Generated evidence ID
            incident_id: Parent incident
            violation_id: Related violation
            evidence: Evidence data dict
        """
        await self._session.execute(
            text(
                """
                INSERT INTO incident_events (
                    id, incident_id, event_type, description, data_json, created_at
                ) VALUES (
                    :id, :incident_id, 'evidence_captured', :description, :data_json, NOW()
                )
            """
            ),
            {
                "id": evidence_id,
                "incident_id": incident_id,
                "description": f"Evidence captured for violation {violation_id}",
                "data_json": json.dumps(
                    {
                        "violation_id": violation_id,
                        "evidence": evidence,
                        "immutable": True,
                    }
                ),
            },
        )

    async def fetch_incident_by_violation(
        self,
        run_id: str,
        policy_id: str,
        tenant_id: str,
    ) -> Optional[str]:
        """
        Check for existing incident by violation pattern.

        Args:
            run_id: Run ID
            policy_id: Policy ID
            tenant_id: Tenant scope

        Returns:
            incident_id if exists, None otherwise
        """
        result = await self._session.execute(
            text(
                """
                SELECT id FROM incidents
                WHERE tenant_id = :tenant_id
                AND trigger_type = 'policy_violation'
                AND trigger_value LIKE :pattern
                LIMIT 1
            """
            ),
            {
                "tenant_id": tenant_id,
                "pattern": f"%run_id={run_id}%policy_id={policy_id}%",
            },
        )
        return result.scalar_one_or_none()

    async def fetch_violation_truth_check(
        self,
        run_id: str,
        tenant_id: str,
        policy_id: str,
    ) -> Dict[str, Any]:
        """
        Fetch all data needed for violation truth verification.

        Args:
            run_id: Run ID
            tenant_id: Tenant scope
            policy_id: Policy ID

        Returns:
            Dict with violation, incident, evidence, and duplicate data
        """
        # AC-1: Violation fact exists
        violation_result = await self._session.execute(
            text(
                """
                SELECT id, policy_id, pattern_id as rule_id, created_at
                FROM prevention_records
                WHERE (original_incident_id = :run_id OR blocked_incident_id = :run_id)
                AND tenant_id = :tenant_id
                AND policy_id = :policy_id
                AND outcome = 'violation_incident'
            """
            ),
            {"run_id": run_id, "tenant_id": tenant_id, "policy_id": policy_id},
        )
        violation_row = violation_result.fetchone()

        # AC-2: Incident exists
        incident_result = await self._session.execute(
            text(
                """
                SELECT id, severity, status, trigger_value
                FROM incidents
                WHERE tenant_id = :tenant_id
                AND trigger_type = 'policy_violation'
                AND trigger_value LIKE :pattern
            """
            ),
            {
                "tenant_id": tenant_id,
                "pattern": f"%run_id={run_id}%policy_id={policy_id}%",
            },
        )
        incident_row = incident_result.fetchone()

        # AC-3: Evidence exists (if incident exists)
        evidence_row = None
        if incident_row:
            evidence_result = await self._session.execute(
                text(
                    """
                    SELECT id, data_json
                    FROM incident_events
                    WHERE incident_id = :incident_id
                    AND event_type = 'evidence_captured'
                """
                ),
                {"incident_id": incident_row[0]},
            )
            evidence_row = evidence_result.fetchone()

        # AC-7: Duplicate check
        duplicate_result = await self._session.execute(
            text(
                """
                SELECT COUNT(*) FROM incidents
                WHERE tenant_id = :tenant_id
                AND trigger_type = 'policy_violation'
                AND trigger_value LIKE :pattern
            """
            ),
            {
                "tenant_id": tenant_id,
                "pattern": f"%run_id={run_id}%policy_id={policy_id}%",
            },
        )
        duplicate_count = duplicate_result.scalar() or 0

        return {
            "violation_row": violation_row,
            "incident_row": incident_row,
            "evidence_row": evidence_row,
            "duplicate_count": duplicate_count,
        }

    async def insert_policy_evaluation(
        self,
        evaluation_id: str,
        run_id: str,
        tenant_id: str,
        outcome: str,
        policies_checked: int,
        confidence: float,
        created_at: datetime,
        is_synthetic: bool,
        synthetic_scenario_id: Optional[str],
    ) -> None:
        """
        Insert policy evaluation record.

        Args:
            evaluation_id: Generated evaluation ID
            run_id: Run being evaluated
            tenant_id: Tenant scope
            outcome: Policy outcome
            policies_checked: Number of policies checked
            confidence: Match confidence
            created_at: Timestamp
            is_synthetic: SDSR flag
            synthetic_scenario_id: Scenario ID for SDSR
        """
        # Use naive datetime for asyncpg compatibility
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)

        await self._session.execute(
            text(
                """
                INSERT INTO prevention_records (
                    id, policy_id, pattern_id, original_incident_id, blocked_incident_id,
                    tenant_id, outcome, signature_match_confidence, created_at,
                    is_synthetic, synthetic_scenario_id
                ) VALUES (
                    :id, :policy_id, :pattern_id, :run_id, :run_id,
                    :tenant_id, :outcome, :confidence, :created_at,
                    :is_synthetic, :synthetic_scenario_id
                )
            """
            ),
            {
                "id": evaluation_id,
                "policy_id": f"policy_eval_{run_id[:8]}",
                "pattern_id": f"policies_checked:{policies_checked}",
                "run_id": run_id,
                "tenant_id": tenant_id,
                "outcome": outcome,
                "confidence": confidence,
                "created_at": created_at,
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
            },
        )

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()


def insert_policy_evaluation_sync(
    database_url: str,
    evaluation_id: str,
    run_id: str,
    tenant_id: str,
    outcome: str,
    policies_checked: int,
    confidence: float,
    created_at: datetime,
    is_synthetic: bool,
    synthetic_scenario_id: Optional[str],
) -> Optional[str]:
    """
    Insert policy evaluation record using sync psycopg2 connection.

    This is used in worker contexts where async is not available.

    Args:
        database_url: Database connection URL
        evaluation_id: Generated evaluation ID
        run_id: Run being evaluated
        tenant_id: Tenant scope
        outcome: Policy outcome
        policies_checked: Number of policies checked
        confidence: Match confidence
        created_at: Timestamp
        is_synthetic: SDSR flag
        synthetic_scenario_id: Scenario ID for SDSR

    Returns:
        evaluation_id if inserted, None if failed
    """
    import psycopg2

    try:
        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO prevention_records (
                        id, policy_id, pattern_id, original_incident_id, blocked_incident_id,
                        tenant_id, outcome, signature_match_confidence, created_at,
                        is_synthetic, synthetic_scenario_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    (
                        evaluation_id,
                        f"policy_eval_{run_id[:8]}",
                        f"policies_checked:{policies_checked}",
                        run_id,
                        run_id,
                        tenant_id,
                        outcome,
                        confidence,
                        created_at,
                        is_synthetic,
                        synthetic_scenario_id,
                    ),
                )
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"policy_eval_sync_db_error: {e}")
        return None


def get_policy_violation_driver(session: AsyncSession) -> PolicyViolationDriver:
    """Factory function to get PolicyViolationDriver instance."""
    return PolicyViolationDriver(session)


__all__ = [
    "PolicyViolationDriver",
    "get_policy_violation_driver",
    "insert_policy_evaluation_sync",
]
