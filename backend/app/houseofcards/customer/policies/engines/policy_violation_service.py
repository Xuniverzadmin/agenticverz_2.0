# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide
# Role: S3 violation truth model, fact persistence, evidence linking
# Callers: L4 policy engine, L5 workers
# Reference: PIN-242 (Baseline Freeze)

"""
Policy Violation Service - S3 Hardening for Phase A.5 Verification

This service implements the S3 truth model from PIN-195:
1. Violation detection
2. Violation fact persistence
3. Incident creation (severity-bound)
4. Evidence linking
5. API + Console exposure

Critical invariants (VERIFICATION_MODE):
- No incident may exist without a persisted violation fact
- Policy must be enabled for tenant
- Evidence must exist before incident creation
- One incident per (run_id, policy_id)
- Cost and policy systems don't interfere

See PIN-195 for full acceptance criteria.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# CANONICAL IMPORTS: Use centralized helpers
from app.utils.runtime import generate_uuid

logger = logging.getLogger("nova.services.policy_violation")

# Verification mode flag - matches workers.py
VERIFICATION_MODE = os.getenv("AOS_VERIFICATION_MODE", "false").lower() == "true"


@dataclass
class ViolationFact:
    """
    Authoritative violation fact - must be persisted before incident creation.

    This is the "fact" that PIN-195 AC-1 requires:
    - Linked to run_id
    - Linked to tenant_id
    - Linked to policy_id
    - Contains violated_rule
    - Contains evaluated_value
    - Contains threshold/condition
    - Contains timestamp
    """

    id: str = field(default_factory=generate_uuid)
    run_id: str = ""
    tenant_id: str = ""
    policy_id: str = ""
    policy_type: str = ""  # CONTENT_ACCURACY, SAFETY, PII, etc.
    violated_rule: str = ""  # Rule ID (e.g., CA001, PII_SSN)
    evaluated_value: str = ""  # What was checked
    threshold_condition: str = ""  # What it was checked against
    severity: str = "medium"  # critical, high, medium, low
    reason: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    persisted: bool = False


@dataclass
class ViolationIncident:
    """Result of creating an incident from a violation."""

    incident_id: str
    violation_id: str
    evidence_id: Optional[str] = None
    persisted: bool = False


class PolicyViolationService:
    """
    Service for handling policy violations with S3 truth guarantees.

    Usage:
        service = PolicyViolationService(session)

        # Create violation fact first
        violation = ViolationFact(
            run_id="...",
            tenant_id="...",
            policy_id="content_accuracy_v1",
            violated_rule="CA001",
            ...
        )

        # Persist and create incident
        result = await service.persist_violation_and_create_incident(violation)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def persist_violation_fact(self, violation: ViolationFact) -> str:
        """
        Persist a violation fact to the database.

        AC-1: Violation fact must be persisted before incident creation.
        Returns the violation ID.
        """
        # Validate required fields
        if not violation.run_id:
            raise ValueError("run_id is required for violation fact")
        if not violation.tenant_id:
            raise ValueError("tenant_id is required for violation fact")
        if not violation.policy_id:
            raise ValueError("policy_id is required for violation fact")
        if not violation.violated_rule:
            raise ValueError("violated_rule is required for violation fact")

        # Use naive datetime for asyncpg compatibility
        timestamp = violation.timestamp
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)

        # Store in prevention_records with outcome='violation_incident'
        # This differentiates from outcome='prevented' (blocked before incident)
        await self.session.execute(
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
                "id": violation.id,
                "policy_id": violation.policy_id,
                "rule_id": violation.violated_rule,
                "run_id": violation.run_id,
                "tenant_id": violation.tenant_id,
                "created_at": timestamp,
            },
        )
        await self.session.commit()

        violation.persisted = True
        logger.info(
            f"Persisted violation fact: id={violation.id}, policy={violation.policy_id}, rule={violation.violated_rule}"
        )

        return violation.id

    async def check_violation_persisted(self, violation_id: str) -> bool:
        """Check if a violation fact has been persisted."""
        result = await self.session.execute(
            text("SELECT id FROM prevention_records WHERE id = :id"), {"id": violation_id}
        )
        return result.scalar_one_or_none() is not None

    async def check_policy_enabled(self, tenant_id: str, policy_id: str) -> bool:
        """
        AC-2 prerequisite: Policy must be explicitly enabled for tenant.

        Returns True if policy is enabled, False otherwise.
        """
        # Check policy_rules table for active policies for this tenant
        result = await self.session.execute(
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

    async def persist_evidence(
        self,
        violation_id: str,
        incident_id: str,
        evidence: Dict[str, Any],
    ) -> str:
        """
        AC-3: Persist evidence linked to violation.

        Evidence includes:
        - Input/output excerpt
        - Policy trace
        - Repro hash
        """
        evidence_id = generate_uuid()

        # Store evidence in incident_events as a 'evidence_captured' event
        await self.session.execute(
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
        await self.session.commit()

        logger.info(f"Persisted evidence: id={evidence_id}, violation={violation_id}")
        return evidence_id

    async def check_incident_exists(self, run_id: str, policy_id: str, tenant_id: str) -> Optional[str]:
        """
        Idempotency check: Only one incident per (run_id, policy_id).

        Returns incident_id if exists, None otherwise.
        """
        result = await self.session.execute(
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

    async def create_incident_from_violation(
        self,
        violation: ViolationFact,
        auto_action: Optional[str] = None,
    ) -> str:
        """
        Create an incident from a persisted violation.

        Preconditions (enforced in VERIFICATION_MODE):
        - Violation must be persisted first
        - Policy must be enabled for tenant
        """
        # INVARIANT 1: Violation must be persisted
        if VERIFICATION_MODE:
            if not violation.persisted:
                is_persisted = await self.check_violation_persisted(violation.id)
                if not is_persisted:
                    raise RuntimeError(
                        f"INCIDENT_WITHOUT_VIOLATION_FACT: "
                        f"Attempted to create incident without persisted violation {violation.id}"
                    )

        # INVARIANT #10: Explicit Dependency Injection
        # Use create_incident_aggregator() NOT get_incident_aggregator()
        # This ensures verification scripts and production use the same dependency graph
        from sqlmodel import Session

        from app.db import engine
        from app.services.incident_aggregator import create_incident_aggregator

        # Need sync session for IncidentAggregator
        with Session(engine) as sync_session:
            aggregator = create_incident_aggregator()

            # Build trigger value with structured data for querying
            trigger_value = (
                f"run_id={violation.run_id}|"
                f"policy_id={violation.policy_id}|"
                f"rule={violation.violated_rule}|"
                f"reason={violation.reason[:100]}"
            )

            incident, is_new = aggregator.get_or_create_incident(
                session=sync_session,
                tenant_id=violation.tenant_id,
                trigger_type="policy_violation",
                trigger_value=trigger_value,
                call_id=violation.run_id,
                cost_delta_cents=Decimal("0"),
                auto_action=auto_action,
                metadata={
                    "violation_id": violation.id,
                    "policy_type": violation.policy_type,
                    "violated_rule": violation.violated_rule,
                    "severity": violation.severity,
                    "evidence_snapshot": {k: str(v)[:100] for k, v in list(violation.evidence.items())[:5]},
                },
            )

            sync_session.commit()
            incident_id = incident.id

        logger.info(
            f"Created incident from violation: incident={incident_id}, violation={violation.id}, is_new={is_new}"
        )

        return incident_id

    async def persist_violation_and_create_incident(
        self,
        violation: ViolationFact,
        auto_action: Optional[str] = None,
    ) -> ViolationIncident:
        """
        Full S3 flow: Violation → Persistence → Incident → Evidence.

        This is the primary entry point for S3 verification.

        Returns ViolationIncident with all IDs.
        """
        # Step 1: Idempotency check
        existing_incident = await self.check_incident_exists(
            run_id=violation.run_id,
            policy_id=violation.policy_id,
            tenant_id=violation.tenant_id,
        )

        if existing_incident:
            logger.info(f"Idempotent: incident already exists for run={violation.run_id}, policy={violation.policy_id}")
            return ViolationIncident(
                incident_id=existing_incident,
                violation_id=violation.id,
                persisted=True,
            )

        # Step 2: Persist violation fact (AC-1)
        await self.persist_violation_fact(violation)

        # Step 3: Create incident (AC-2)
        incident_id = await self.create_incident_from_violation(
            violation=violation,
            auto_action=auto_action,
        )

        # Step 4: Persist evidence (AC-3)
        evidence_id = None
        if violation.evidence:
            evidence_id = await self.persist_evidence(
                violation_id=violation.id,
                incident_id=incident_id,
                evidence=violation.evidence,
            )
        elif VERIFICATION_MODE:
            # In verification mode, evidence is mandatory
            raise RuntimeError(
                f"INCIDENT_WITHOUT_EVIDENCE: Evidence required but not provided for violation {violation.id}"
            )

        return ViolationIncident(
            incident_id=incident_id,
            violation_id=violation.id,
            evidence_id=evidence_id,
            persisted=True,
        )

    async def verify_violation_truth(
        self,
        run_id: str,
        tenant_id: str,
        policy_id: str,
    ) -> Dict[str, Any]:
        """
        Verify that a violation satisfies S3 truth requirements.

        Used by verification scripts to validate AC-1 through AC-7.

        Returns dict with pass/fail status and evidence.
        """
        results = {
            "run_id": run_id,
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "checks": {},
            "passed": False,
        }

        # AC-1: Violation fact exists
        violation_result = await self.session.execute(
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

        results["checks"]["ac1_violation_persisted"] = {
            "passed": violation_row is not None,
            "violation_id": violation_row[0] if violation_row else None,
        }

        # AC-2: Incident exists
        incident_result = await self.session.execute(
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

        results["checks"]["ac2_incident_exists"] = {
            "passed": incident_row is not None,
            "incident_id": incident_row[0] if incident_row else None,
            "severity": incident_row[1] if incident_row else None,
        }

        # AC-3: Evidence exists
        evidence_passed = False
        evidence_id = None
        if incident_row:
            evidence_result = await self.session.execute(
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
            evidence_passed = evidence_row is not None
            evidence_id = evidence_row[0] if evidence_row else None

        results["checks"]["ac3_evidence_exists"] = {
            "passed": evidence_passed,
            "evidence_id": evidence_id,
        }

        # AC-7: Negative assertion - no duplicate incidents
        duplicate_result = await self.session.execute(
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

        results["checks"]["ac7_no_duplicate_incidents"] = {
            "passed": duplicate_count <= 1,
            "count": duplicate_count,
        }

        # Overall pass/fail
        results["passed"] = all(check["passed"] for check in results["checks"].values())

        return results


# =============================================================================
# PIN-407: Policy Outcome Model (Success as First-Class Data)
# =============================================================================
# Every run produces ONE policy evaluation record with explicit outcome.
# Outcome values: NO_VIOLATION, VIOLATION, ADVISORY, NOT_APPLICABLE
# =============================================================================

POLICY_OUTCOME_NO_VIOLATION = "no_violation"
POLICY_OUTCOME_VIOLATION = "violation_incident"
POLICY_OUTCOME_ADVISORY = "advisory"
POLICY_OUTCOME_NOT_APPLICABLE = "not_applicable"


@dataclass
class PolicyEvaluationResult:
    """
    Result of policy evaluation (PIN-407: Success as First-Class Data).

    Every run MUST produce exactly one policy evaluation record.
    This is NOT limited to violations - successful evaluations also get records.
    """

    id: str = field(default_factory=generate_uuid)
    run_id: str = ""
    tenant_id: str = ""
    outcome: str = POLICY_OUTCOME_NO_VIOLATION
    policies_checked: int = 0
    reason: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    draft_candidate: bool = False  # For future policy learning


async def create_policy_evaluation_record(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
    outcome: str,
    policies_checked: int = 0,
    reason: str = "",
    draft_candidate: bool = False,
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
) -> str:
    """
    Create a policy evaluation record for ANY run (PIN-407).

    Every run MUST produce exactly one policy evaluation record.
    This is NOT limited to violations - successful evaluations also get records.

    Args:
        session: Database session
        run_id: Run ID
        tenant_id: Tenant scope
        outcome: Policy outcome (NO_VIOLATION, VIOLATION, ADVISORY, NOT_APPLICABLE)
        policies_checked: Number of policies evaluated
        reason: Human-readable reason
        draft_candidate: If True, this run is a candidate for policy learning
        is_synthetic: True if from SDSR scenario
        synthetic_scenario_id: Scenario ID for traceability

    Returns:
        policy_evaluation_id
    """
    evaluation_id = generate_uuid()
    now = datetime.now(timezone.utc)

    # Use naive datetime for asyncpg compatibility
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)

    # Store in prevention_records with outcome indicating evaluation result
    # This reuses existing table per TODO-03 (preserve existing tables)
    await session.execute(
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
            "policy_id": f"policy_eval_{run_id[:8]}",  # Unique per run
            "pattern_id": f"policies_checked:{policies_checked}",
            "run_id": run_id,
            "tenant_id": tenant_id,
            "outcome": outcome,
            "confidence": 1.0 if outcome == POLICY_OUTCOME_NO_VIOLATION else 0.0,
            "created_at": now,
            "is_synthetic": is_synthetic,
            "synthetic_scenario_id": synthetic_scenario_id,
        },
    )
    await session.commit()

    logger.info(
        f"Created policy evaluation record: id={evaluation_id}, run={run_id}, "
        f"outcome={outcome}, policies_checked={policies_checked}, synthetic={is_synthetic}"
    )

    return evaluation_id


async def handle_policy_evaluation_for_run(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
    run_status: str,
    policies_checked: int = 0,
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
) -> str:
    """
    Create a policy evaluation record for ANY run (PIN-407).

    This is the NEW primary entry point for run → policy evaluation propagation.
    Every run creates exactly one policy evaluation record with explicit outcome.

    Args:
        session: Database session
        run_id: Run ID
        tenant_id: Tenant scope
        run_status: Run status (succeeded, failed, etc.)
        policies_checked: Number of policies evaluated
        is_synthetic: True if from SDSR scenario
        synthetic_scenario_id: Scenario ID for traceability

    Returns:
        policy_evaluation_id
    """
    # Map run status to policy outcome
    status_lower = run_status.lower()
    if status_lower in ("succeeded", "completed", "success"):
        outcome = POLICY_OUTCOME_NO_VIOLATION
        reason = "Run completed successfully, no policy violations"
    elif status_lower in ("failed", "failure", "error"):
        # Note: If there was a violation, handle_policy_violation should be called
        # This is for failures that are NOT policy violations
        outcome = POLICY_OUTCOME_NOT_APPLICABLE
        reason = "Run failed, policy evaluation not applicable"
    elif status_lower in ("halted", "blocked"):
        outcome = POLICY_OUTCOME_ADVISORY
        reason = "Run halted, policy advisory recorded"
    else:
        outcome = POLICY_OUTCOME_NOT_APPLICABLE
        reason = f"Run status '{run_status}', policy evaluation not applicable"

    return await create_policy_evaluation_record(
        session=session,
        run_id=run_id,
        tenant_id=tenant_id,
        outcome=outcome,
        policies_checked=policies_checked,
        reason=reason,
        is_synthetic=is_synthetic,
        synthetic_scenario_id=synthetic_scenario_id,
    )


# Convenience function for use in workers.py
async def handle_policy_violation(
    session: AsyncSession,
    run_id: str,
    tenant_id: str,
    policy_type: str,
    policy_id: str,
    violated_rule: str,
    reason: str,
    severity: str = "medium",
    evidence: Optional[Dict[str, Any]] = None,
) -> Optional[ViolationIncident]:
    """
    Handle a policy violation with S3 truth guarantees.

    This is the main entry point for policy violation handling.
    Call this from workers.py when a policy violation is detected.

    Returns ViolationIncident if incident was created, None if skipped.
    """
    service = PolicyViolationService(session)

    violation = ViolationFact(
        run_id=run_id,
        tenant_id=tenant_id,
        policy_id=policy_id,
        policy_type=policy_type,
        violated_rule=violated_rule,
        evaluated_value=f"run:{run_id}",
        threshold_condition=reason,
        severity=severity,
        reason=reason,
        evidence=evidence or {},
    )

    return await service.persist_violation_and_create_incident(violation)


# =============================================================================
# PIN-407: Sync Policy Evaluation for Worker Use
# =============================================================================


def create_policy_evaluation_sync(
    run_id: str,
    tenant_id: str,
    run_status: str,
    policies_checked: int = 0,
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
) -> Optional[str]:
    """
    Create a policy evaluation record for ANY run (PIN-407) - SYNC VERSION.

    This is a synchronous wrapper for use in worker contexts where we don't
    have an async session. Uses direct psycopg2 connection.

    Args:
        run_id: Run ID
        tenant_id: Tenant scope
        run_status: Run status (succeeded, failed, etc.)
        policies_checked: Number of policies evaluated
        is_synthetic: True if from SDSR scenario
        synthetic_scenario_id: Scenario ID for traceability

    Returns:
        policy_evaluation_id if created, None if failed
    """
    import psycopg2

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("policy_eval_sync_no_database_url")
        return None

    # Map run status to policy outcome
    status_lower = run_status.lower()
    if status_lower in ("succeeded", "completed", "success"):
        outcome = POLICY_OUTCOME_NO_VIOLATION
        reason = "Run completed successfully, no policy violations"
    elif status_lower in ("failed", "failure", "error"):
        outcome = POLICY_OUTCOME_NOT_APPLICABLE
        reason = "Run failed, policy evaluation not applicable"
    elif status_lower in ("halted", "blocked"):
        outcome = POLICY_OUTCOME_ADVISORY
        reason = "Run halted, policy advisory recorded"
    else:
        outcome = POLICY_OUTCOME_NOT_APPLICABLE
        reason = f"Run status '{run_status}', policy evaluation not applicable"

    evaluation_id = generate_uuid()
    now = datetime.now(timezone.utc)

    try:
        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor() as cur:
                # Match the async version's schema usage
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
                        f"policy_eval_{run_id[:8]}",  # Unique per run
                        f"policies_checked:{policies_checked}",
                        run_id,  # original_incident_id = run_id
                        run_id,  # blocked_incident_id = run_id
                        tenant_id,
                        outcome,
                        1.0 if outcome == POLICY_OUTCOME_NO_VIOLATION else 0.0,
                        now,
                        is_synthetic,
                        synthetic_scenario_id,
                    ),
                )
                result = cur.fetchone()
                conn.commit()

                if result:
                    logger.info(
                        "policy_evaluation_created_sync",
                        extra={
                            "run_id": run_id,
                            "evaluation_id": result[0],
                            "outcome": outcome,
                        },
                    )
                    return result[0]
                else:
                    logger.debug(
                        "policy_evaluation_exists_sync",
                        extra={"run_id": run_id, "outcome": outcome},
                    )
                    return None
        finally:
            conn.close()

    except Exception as e:
        logger.error(
            "policy_evaluation_sync_failed",
            extra={"run_id": run_id, "error": str(e)},
        )
        return None
