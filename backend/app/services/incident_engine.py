# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: worker (run failure events)
#   Execution: sync
# Role: Incident creation decision-making (domain logic)
# Authority: Incident generation from run failures (SDSR pattern)
# Callers: Worker runtime, API endpoints
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Contract: SDSR (PIN-370)
# Reference: PIN-370 (Scenario-Driven System Realization)
#
# GOVERNANCE NOTE: This L4 engine owns INCIDENT CREATION logic.
# Scenarios inject causes (failed runs), this engine creates incidents.
# UI observes incidents, never writes them.

"""
Incident Engine (L4 Domain Logic)

This engine implements the SDSR cross-domain propagation contract:
- Run failure (Activity domain) → Incident creation (Incidents domain)

Per PIN-370 Rule 6 (Scenarios Inject Causes, Not Consequences):
- Scenarios inject a failed run
- This engine AUTOMATICALLY creates incidents
- If incident doesn't appear, the ENGINE is broken, not the scenario

Reference: PIN-370, INCIDENTS-EXEC-FAILURE-001
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, text

logger = logging.getLogger("nova.services.incident_engine")


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# Incident Engine (L4 Domain Logic)
# =============================================================================

# =============================================================================
# NORMALIZATION CONTRACT (PIN-370)
# =============================================================================
# This engine is the SINGLE source of truth for incident field normalization.
# All incidents created by this engine use:
#   - severity: UPPERCASE (CRITICAL, HIGH, MEDIUM, LOW)
#   - status: UPPERCASE (OPEN, ACKNOWLEDGED, RESOLVED, CLOSED)
#   - category: UPPERCASE (EXECUTION_FAILURE, BUDGET_EXCEEDED, etc.)
#
# API response mappers may still normalize for backward compatibility with
# legacy data, but NEW incidents created here are always uppercase.
# =============================================================================

# =============================================================================
# PIN-407: Incident Outcome Model (SUCCESS as First-Class Data)
# =============================================================================
# Every run produces ONE incident record with an explicit outcome.
# Outcome values: SUCCESS, FAILURE, BLOCKED, ABORTED
# Severity values: NONE (for success), or existing severity for failures
# =============================================================================

# Incident outcomes (PIN-407)
INCIDENT_OUTCOME_SUCCESS = "SUCCESS"
INCIDENT_OUTCOME_FAILURE = "FAILURE"
INCIDENT_OUTCOME_BLOCKED = "BLOCKED"
INCIDENT_OUTCOME_ABORTED = "ABORTED"

# Severity for success incidents
SEVERITY_NONE = "NONE"

# Severity mapping based on failure codes
FAILURE_SEVERITY_MAP = {
    # High severity - execution failures
    "EXECUTION_TIMEOUT": "HIGH",
    "AGENT_CRASH": "CRITICAL",
    "STEP_FAILURE": "HIGH",
    "SKILL_ERROR": "HIGH",
    # Medium severity - resource issues
    "BUDGET_EXCEEDED": "MEDIUM",
    "RATE_LIMIT_EXCEEDED": "MEDIUM",
    "RESOURCE_EXHAUSTION": "MEDIUM",
    # Low severity - expected failures
    "CANCELLED": "LOW",
    "MANUAL_STOP": "LOW",
    "RETRY_EXHAUSTED": "MEDIUM",
    # Default
    "UNKNOWN": "MEDIUM",
}

# Category mapping based on failure codes
FAILURE_CATEGORY_MAP = {
    "EXECUTION_TIMEOUT": "EXECUTION_FAILURE",
    "AGENT_CRASH": "EXECUTION_FAILURE",
    "STEP_FAILURE": "EXECUTION_FAILURE",
    "SKILL_ERROR": "EXECUTION_FAILURE",
    "BUDGET_EXCEEDED": "BUDGET_EXCEEDED",
    "RATE_LIMIT_EXCEEDED": "RATE_LIMIT",
    "RESOURCE_EXHAUSTION": "RESOURCE_EXHAUSTION",
    "CANCELLED": "MANUAL",
    "MANUAL_STOP": "MANUAL",
    "RETRY_EXHAUSTED": "EXECUTION_FAILURE",
    "UNKNOWN": "EXECUTION_FAILURE",
}


class IncidentEngine:
    """
    L4 Domain Engine for incident creation.

    This engine implements the SDSR cross-domain propagation:
    Activity (cause) → Incidents (reactive)

    SDSR Contract (PIN-370):
    - This engine is called when a run fails
    - It creates an incident record automatically
    - Incidents are NEVER created by scenarios directly
    - If incidents don't appear for failed runs, THIS ENGINE is broken

    Callers:
    - Worker runtime (on run failure)
    - inject_synthetic.py expectations validator
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize the incident engine."""
        self._db_url = db_url or os.environ.get("DATABASE_URL")

    def _get_engine(self):
        """Get SQLAlchemy engine."""
        if not self._db_url:
            raise RuntimeError("DATABASE_URL not configured")
        return create_engine(self._db_url)

    def _check_policy_suppression(
        self,
        tenant_id: str,
        error_code: Optional[str],
        category: str,
    ) -> Optional[dict]:
        """
        Check if an active policy_rule suppresses this incident pattern.

        POLICY ENFORCEMENT (Keystone):
        - Called BEFORE incident creation (read-before-write)
        - Returns matching policy_rule if suppression applies
        - Returns None if no suppression (proceed with incident)

        Matching criteria:
        - Same tenant_id
        - is_active = true
        - mode = 'active'
        - conditions match error_code pattern

        This is NOT SDSR-specific logic. It applies to ALL runs,
        both real and synthetic. The policy_rule itself may be
        synthetic (for testing) but the enforcement logic is identical.

        Args:
            tenant_id: Tenant scope
            error_code: Error code to match against policy conditions
            category: Error category

        Returns:
            dict with policy_rule info if suppressed, None otherwise
        """
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                # Find active policy_rules for this tenant that match the error pattern
                # The conditions JSONB contains trigger.error_code or similar
                result = conn.execute(
                    text("""
                        SELECT id, name, conditions, source_incident_id
                        FROM policy_rules
                        WHERE tenant_id = :tenant_id
                          AND is_active = true
                          AND mode = 'active'
                          AND (
                            -- Match if conditions contain the error_code
                            conditions::text LIKE :error_pattern
                            OR conditions::text LIKE :category_pattern
                          )
                        ORDER BY created_at DESC
                        LIMIT 1
                    """),
                    {
                        "tenant_id": tenant_id,
                        "error_pattern": f"%{error_code or 'UNKNOWN'}%",
                        "category_pattern": f"%{category}%",
                    },
                )
                row = result.fetchone()

                if row:
                    return {
                        "policy_id": row[0],
                        "policy_name": row[1],
                        "conditions": row[2],
                        "source_incident_id": row[3],
                    }
                return None

        except Exception as e:
            logger.warning(f"Error checking policy suppression: {e}")
            # On error, default to NOT suppressing (fail open for incident creation)
            return None

    def _write_prevention_record(
        self,
        policy_id: str,
        run_id: str,
        tenant_id: str,
        error_code: Optional[str],
        source_incident_id: Optional[str],
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> str:
        """
        Write a prevention_record when a run is suppressed by an active policy.

        EXACTLY ONE SIDE EFFECT:
        - Either an incident is created (in create_incident_for_failed_run)
        - OR a prevention_record is created (here)
        - NEVER both

        Args:
            policy_id: The policy_rule that caused suppression
            run_id: The run that was suppressed (blocked_incident_id)
            tenant_id: Tenant scope
            error_code: The error pattern that was matched
            source_incident_id: The original incident that created this policy
            is_synthetic: Synthetic flag for SDSR traceability
            synthetic_scenario_id: Scenario ID for SDSR traceability

        Returns:
            prevention_record ID
        """
        import uuid

        prevention_id = f"prev_{uuid.uuid4().hex[:16]}"
        now = utc_now()

        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO prevention_records (
                        id, policy_id, pattern_id, original_incident_id,
                        blocked_incident_id, tenant_id, outcome,
                        signature_match_confidence, created_at,
                        is_synthetic, synthetic_scenario_id
                    ) VALUES (
                        :id, :policy_id, :pattern_id, :original_incident_id,
                        :blocked_incident_id, :tenant_id, :outcome,
                        :signature_match_confidence, :created_at,
                        :is_synthetic, :synthetic_scenario_id
                    )
                """),
                {
                    "id": prevention_id,
                    "policy_id": policy_id,
                    "pattern_id": error_code or "UNKNOWN",
                    "original_incident_id": source_incident_id or policy_id,
                    "blocked_incident_id": run_id,
                    "tenant_id": tenant_id,
                    "outcome": "prevented",
                    "signature_match_confidence": 1.0,
                    "created_at": now,
                    "is_synthetic": is_synthetic,
                    "synthetic_scenario_id": synthetic_scenario_id,
                },
            )
            conn.commit()

        logger.info(
            f"Prevention record {prevention_id}: run {run_id} suppressed by policy {policy_id}"
        )
        return prevention_id

    # =========================================================================
    # PIN-407: Create incident for ANY run (SUCCESS or FAILURE)
    # =========================================================================
    def create_incident_for_run(
        self,
        run_id: str,
        tenant_id: str,
        run_status: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create an incident for ANY run (PIN-407: Success as First-Class Data).

        Every run MUST produce exactly one incident record with an explicit outcome.
        This is NOT limited to failures - successful runs also get incident records.

        PIN-407 Correction:
        - Success is data, not silence
        - Every run produces an incident record
        - Outcome is explicit: SUCCESS, FAILURE, BLOCKED, ABORTED

        Args:
            run_id: ID of the run
            tenant_id: Tenant scope
            run_status: Run status (succeeded, failed, halted, aborted, etc.)
            error_code: Error code (for failures)
            error_message: Error message (for failures)
            agent_id: Agent that was running
            is_synthetic: True if from SDSR scenario
            synthetic_scenario_id: Scenario ID for traceability

        Returns:
            incident_id if created, None if failed to create
        """
        try:
            # Map run_status to incident outcome
            status_to_outcome = {
                "succeeded": INCIDENT_OUTCOME_SUCCESS,
                "completed": INCIDENT_OUTCOME_SUCCESS,
                "success": INCIDENT_OUTCOME_SUCCESS,
                "failed": INCIDENT_OUTCOME_FAILURE,
                "failure": INCIDENT_OUTCOME_FAILURE,
                "error": INCIDENT_OUTCOME_FAILURE,
                "halted": INCIDENT_OUTCOME_BLOCKED,
                "blocked": INCIDENT_OUTCOME_BLOCKED,
                "aborted": INCIDENT_OUTCOME_ABORTED,
                "cancelled": INCIDENT_OUTCOME_ABORTED,
            }
            outcome = status_to_outcome.get(run_status.lower(), INCIDENT_OUTCOME_FAILURE)

            # Determine severity based on outcome
            if outcome == INCIDENT_OUTCOME_SUCCESS:
                severity = SEVERITY_NONE
                category = "EXECUTION_SUCCESS"
                title = f"Execution Complete: Run {run_id[:8]}..."
                description = f"Run {run_id} completed successfully"
                status = "CLOSED"  # Success incidents are immediately closed
            else:
                # Use existing failure logic
                severity = FAILURE_SEVERITY_MAP.get(error_code or "UNKNOWN", "MEDIUM")
                category = FAILURE_CATEGORY_MAP.get(error_code or "UNKNOWN", "EXECUTION_FAILURE")
                title = self._generate_title(error_code, run_id)
                description = f"Run {run_id} failed with error: {error_code or 'UNKNOWN'}"
                status = "OPEN"

            # For failures, check policy suppression (existing logic)
            if outcome != INCIDENT_OUTCOME_SUCCESS:
                suppressing_policy = self._check_policy_suppression(
                    tenant_id=tenant_id,
                    error_code=error_code,
                    category=category,
                )

                if suppressing_policy:
                    logger.info(
                        f"Run {run_id} suppressed by policy {suppressing_policy['policy_id']} "
                        f"(pattern: {error_code})"
                    )
                    self._write_prevention_record(
                        policy_id=suppressing_policy["policy_id"],
                        run_id=run_id,
                        tenant_id=tenant_id,
                        error_code=error_code,
                        source_incident_id=suppressing_policy.get("source_incident_id"),
                        is_synthetic=is_synthetic,
                        synthetic_scenario_id=synthetic_scenario_id,
                    )
                    return None

            # Generate incident ID
            import uuid
            incident_id = f"inc_{uuid.uuid4().hex[:16]}"

            # Insert incident
            engine = self._get_engine()
            now = utc_now()

            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO incidents (
                            id, tenant_id, title, severity, status,
                            trigger_type, started_at, created_at, updated_at,
                            source_run_id, source_type, category, description,
                            error_code, error_message, impact_scope,
                            affected_agent_id, affected_count,
                            is_synthetic, synthetic_scenario_id
                        ) VALUES (
                            :id, :tenant_id, :title, :severity, :status,
                            :trigger_type, :started_at, :created_at, :updated_at,
                            :source_run_id, :source_type, :category, :description,
                            :error_code, :error_message, :impact_scope,
                            :affected_agent_id, :affected_count,
                            :is_synthetic, :synthetic_scenario_id
                        )
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": incident_id,
                        "tenant_id": tenant_id,
                        "title": title,
                        "severity": severity.upper(),
                        "status": status,
                        "trigger_type": "run_completion",  # Not just failure
                        "started_at": now,
                        "created_at": now,
                        "updated_at": now,
                        "source_run_id": run_id,
                        "source_type": "run",
                        "category": category,
                        "description": description,
                        "error_code": error_code if outcome != INCIDENT_OUTCOME_SUCCESS else None,
                        "error_message": error_message if outcome != INCIDENT_OUTCOME_SUCCESS else None,
                        "impact_scope": "single_run",
                        "affected_agent_id": agent_id,
                        "affected_count": 1,
                        "is_synthetic": is_synthetic,
                        "synthetic_scenario_id": synthetic_scenario_id,
                    },
                )
                conn.commit()

            logger.info(
                f"Created incident {incident_id} for run {run_id} "
                f"(outcome={outcome}, category={category}, severity={severity}, synthetic={is_synthetic})"
            )

            # For failures, propagate to traces and maybe create policy proposal
            if outcome != INCIDENT_OUTCOME_SUCCESS:
                # GAP-PROP-001 FIX: Propagate incident_id to aos_traces
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text("""
                                UPDATE aos_traces
                                SET incident_id = :incident_id
                                WHERE run_id = :run_id
                            """),
                            {"incident_id": incident_id, "run_id": run_id},
                        )
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to propagate incident_id to trace: {e}")

                # Create policy proposal for high-severity failures
                if severity.upper() in ("HIGH", "CRITICAL"):
                    self._maybe_create_policy_proposal(
                        incident_id=incident_id,
                        tenant_id=tenant_id,
                        severity=severity,
                        category=category,
                        error_code=error_code,
                        run_id=run_id,
                        is_synthetic=is_synthetic,
                        synthetic_scenario_id=synthetic_scenario_id,
                    )

            return incident_id

        except Exception as e:
            logger.error(f"Failed to create incident for run {run_id}: {e}")
            return None

    def create_incident_for_failed_run(
        self,
        run_id: str,
        tenant_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create an incident for a failed run.

        This is the primary entry point for run → incident propagation.

        POLICY ENFORCEMENT (added for E2E-004):
        - BEFORE creating an incident, check if an active policy_rule suppresses it
        - If suppressed: write prevention_record, return None
        - If not suppressed: create incident normally

        Per SDSR Rule 6:
        - This method is called when a run fails
        - It creates an incident AUTOMATICALLY (unless suppressed by policy)
        - The incident links back to the source run

        Args:
            run_id: ID of the failed run
            tenant_id: Tenant scope
            error_code: Error code (e.g., EXECUTION_TIMEOUT)
            error_message: Full error message
            agent_id: Agent that was running
            is_synthetic: True if from SDSR scenario
            synthetic_scenario_id: Scenario ID for traceability

        Returns:
            incident_id if created, None if suppressed or failed
        """
        try:
            # Determine severity and category from error code
            severity = FAILURE_SEVERITY_MAP.get(error_code or "UNKNOWN", "MEDIUM")
            category = FAILURE_CATEGORY_MAP.get(error_code or "UNKNOWN", "EXECUTION_FAILURE")

            # =====================================================================
            # POLICY ENFORCEMENT CHECK (read-before-write)
            # =====================================================================
            # Check if an active policy_rule suppresses this incident pattern.
            # This is NOT SDSR-specific - it applies to ALL runs.
            # =====================================================================
            suppressing_policy = self._check_policy_suppression(
                tenant_id=tenant_id,
                error_code=error_code,
                category=category,
            )

            if suppressing_policy:
                # Policy suppresses this incident - write prevention_record instead
                logger.info(
                    f"Run {run_id} suppressed by policy {suppressing_policy['policy_id']} "
                    f"(pattern: {error_code})"
                )
                self._write_prevention_record(
                    policy_id=suppressing_policy["policy_id"],
                    run_id=run_id,
                    tenant_id=tenant_id,
                    error_code=error_code,
                    source_incident_id=suppressing_policy.get("source_incident_id"),
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )
                # Return None to indicate no incident was created
                return None

            # Generate incident title
            title = self._generate_title(error_code, run_id)

            # Generate incident ID
            import uuid

            incident_id = f"inc_{uuid.uuid4().hex[:16]}"

            # Insert incident into canonical incidents table (PIN-370 consolidation)
            engine = self._get_engine()
            now = utc_now()

            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO incidents (
                            id, tenant_id, title, severity, status,
                            trigger_type, started_at, created_at, updated_at,
                            source_run_id, source_type, category, description,
                            error_code, error_message, impact_scope,
                            affected_agent_id, affected_count,
                            is_synthetic, synthetic_scenario_id
                        ) VALUES (
                            :id, :tenant_id, :title, :severity, :status,
                            :trigger_type, :started_at, :created_at, :updated_at,
                            :source_run_id, :source_type, :category, :description,
                            :error_code, :error_message, :impact_scope,
                            :affected_agent_id, :affected_count,
                            :is_synthetic, :synthetic_scenario_id
                        )
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": incident_id,
                        "tenant_id": tenant_id,
                        "title": title,
                        "severity": severity.upper(),  # NORMALIZED: always uppercase (CRITICAL, HIGH, MEDIUM, LOW)
                        "status": "OPEN",  # NORMALIZED: always uppercase (OPEN, ACKNOWLEDGED, RESOLVED, CLOSED)
                        "trigger_type": "run_failure",
                        "started_at": now,
                        "created_at": now,
                        "updated_at": now,
                        "source_run_id": run_id,
                        "source_type": "run",
                        "category": category,
                        "description": f"Run {run_id} failed with error: {error_code or 'UNKNOWN'}",
                        "error_code": error_code,
                        "error_message": error_message,
                        "impact_scope": "single_run",
                        "affected_agent_id": agent_id,
                        "affected_count": 1,
                        "is_synthetic": is_synthetic,
                        "synthetic_scenario_id": synthetic_scenario_id,
                    },
                )
                conn.commit()

            logger.info(
                f"Created incident {incident_id} for failed run {run_id} "
                f"(category={category}, severity={severity}, synthetic={is_synthetic})"
            )

            # GAP-PROP-001 FIX: Propagate incident_id to aos_traces (PIN-378 cross-domain correlation)
            # This enables Logs → Incidents deep linking in UI
            try:
                engine_conn = self._get_engine()
                with engine_conn.connect() as conn:
                    conn.execute(
                        text("""
                            UPDATE aos_traces
                            SET incident_id = :incident_id
                            WHERE run_id = :run_id
                        """),
                        {"incident_id": incident_id, "run_id": run_id},
                    )
                    conn.commit()
                logger.debug(f"Propagated incident_id {incident_id} to trace for run {run_id}")
            except Exception as e:
                # Don't fail incident creation if trace update fails
                logger.warning(f"Failed to propagate incident_id to trace: {e}")

            # PIN-373: Consider creating policy proposal for high-severity incidents
            if severity.upper() in ("HIGH", "CRITICAL"):
                self._maybe_create_policy_proposal(
                    incident_id=incident_id,
                    tenant_id=tenant_id,
                    severity=severity,
                    category=category,
                    error_code=error_code,
                    run_id=run_id,
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )

            return incident_id

        except Exception as e:
            logger.error(f"Failed to create incident for run {run_id}: {e}")
            return None

    def _maybe_create_policy_proposal(
        self,
        incident_id: str,
        tenant_id: str,
        severity: str,
        category: str,
        error_code: Optional[str],
        run_id: str,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a policy proposal for high-severity incidents.

        PIN-373: Incidents MAY create policy proposals (draft).
        - System proposes, human approves
        - Only for HIGH/CRITICAL severity
        - Creates DRAFT proposal, never auto-enforces

        Returns:
            proposal_id if created, None otherwise
        """
        try:
            import json
            import uuid

            proposal_id = str(uuid.uuid4())

            # Determine proposal type based on error pattern
            proposal_type_map = {
                "EXECUTION_TIMEOUT": "timeout_policy",
                "AGENT_CRASH": "crash_recovery_policy",
                "BUDGET_EXCEEDED": "cost_cap_policy",
                "RATE_LIMIT_EXCEEDED": "rate_limit_policy",
                "STEP_FAILURE": "retry_policy",
            }
            proposal_type = proposal_type_map.get(error_code or "", "failure_pattern_policy")

            # Generate rationale
            rationale = (
                f"Auto-generated proposal based on {severity} severity incident.\n"
                f"Category: {category}\n"
                f"Error: {error_code or 'Unknown'}\n"
                f"Source run: {run_id}\n\n"
                f"This proposal requires human review and approval before activation."
            )

            # Generate proposed rule (simple template)
            proposed_rule = {
                "type": proposal_type,
                "trigger": {
                    "error_code": error_code,
                    "severity_threshold": severity,
                },
                "action": {
                    "type": "alert" if severity == "HIGH" else "block",
                    "description": f"Proposed action for {error_code or 'unknown'} failures",
                },
                "auto_generated": True,
                "source_incident_id": incident_id,
            }

            # Insert into policy_proposals
            engine = self._get_engine()
            now = utc_now()

            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO policy_proposals (
                            id, tenant_id, proposal_name, proposal_type,
                            rationale, proposed_rule, triggering_feedback_ids,
                            status, created_at, is_synthetic, synthetic_scenario_id
                        ) VALUES (
                            :id, :tenant_id, :proposal_name, :proposal_type,
                            :rationale, :proposed_rule, :triggering_feedback_ids,
                            :status, :created_at, :is_synthetic, :synthetic_scenario_id
                        )
                    """),
                    {
                        "id": proposal_id,
                        "tenant_id": tenant_id,
                        "proposal_name": f"Auto: {proposal_type.replace('_', ' ').title()} ({incident_id[:12]})",
                        "proposal_type": proposal_type,
                        "rationale": rationale,
                        "proposed_rule": json.dumps(proposed_rule),  # Proper JSON
                        "triggering_feedback_ids": json.dumps([incident_id]),  # Proper JSON array
                        "status": "draft",  # Always draft - human approval required
                        "created_at": now,
                        "is_synthetic": is_synthetic,  # SDSR traceability
                        "synthetic_scenario_id": synthetic_scenario_id,  # SDSR traceability
                    },
                )
                conn.commit()

            logger.info(
                f"Created policy proposal {proposal_id} for incident {incident_id} "
                f"(type={proposal_type}, synthetic={is_synthetic})"
            )
            return proposal_id

        except Exception as e:
            # Don't fail incident creation if proposal fails
            logger.warning(f"Failed to create policy proposal for incident {incident_id}: {e}")
            return None

    def _generate_title(self, error_code: Optional[str], run_id: str) -> str:
        """Generate human-readable incident title."""
        if error_code == "EXECUTION_TIMEOUT":
            return f"Execution Timeout: Run {run_id[:8]}..."
        elif error_code == "AGENT_CRASH":
            return f"Agent Crash: Run {run_id[:8]}..."
        elif error_code == "BUDGET_EXCEEDED":
            return f"Budget Exceeded: Run {run_id[:8]}..."
        elif error_code == "RATE_LIMIT_EXCEEDED":
            return f"Rate Limit Hit: Run {run_id[:8]}..."
        elif error_code == "STEP_FAILURE":
            return f"Step Failure: Run {run_id[:8]}..."
        elif error_code == "SKILL_ERROR":
            return f"Skill Error: Run {run_id[:8]}..."
        else:
            return f"Run Failed: {run_id[:8]}..."

    def check_and_create_incident(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Check if a run status warrants an incident and create one if so.

        DEPRECATED: Use create_incident_for_all_runs() for PIN-407 compliance.

        This legacy method only creates incidents for failed runs.
        For backward compatibility with existing callers.

        Args:
            run_id: Run ID
            status: Run status
            error_message: Error message (may contain error code)
            tenant_id: Tenant scope
            agent_id: Agent ID
            is_synthetic: SDSR synthetic flag
            synthetic_scenario_id: SDSR scenario ID

        Returns:
            incident_id if created, None otherwise
        """
        # Only create incidents for failed runs (legacy behavior)
        if status != "failed":
            return None

        # Extract error code from error message
        error_code = self._extract_error_code(error_message)

        # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant.
        # Skip incident creation for runs without tenant_id (legacy data).
        if not tenant_id:
            logger.warning("Cannot create incident for run without tenant_id", extra={"run_id": run_id})
            return None
        return self.create_incident_for_failed_run(
            run_id=run_id,
            tenant_id=tenant_id,
            error_code=error_code,
            error_message=error_message,
            agent_id=agent_id,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def create_incident_for_all_runs(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create an incident for ANY run (PIN-407: Success as First-Class Data).

        This is the NEW preferred entry point for run → incident propagation.
        Every run creates exactly one incident record with explicit outcome.

        Args:
            run_id: Run ID
            status: Run status (succeeded, failed, halted, etc.)
            error_message: Error message (for failures)
            tenant_id: Tenant scope
            agent_id: Agent ID
            is_synthetic: SDSR synthetic flag
            synthetic_scenario_id: SDSR scenario ID

        Returns:
            incident_id if created, None otherwise
        """
        # Extract error code from error message (for failures)
        error_code = self._extract_error_code(error_message) if status == "failed" else None

        # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant.
        if not tenant_id:
            logger.warning("Cannot create incident for run without tenant_id", extra={"run_id": run_id})
            return None

        return self.create_incident_for_run(
            run_id=run_id,
            tenant_id=tenant_id,
            run_status=status,
            error_code=error_code,
            error_message=error_message,
            agent_id=agent_id,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

    def _extract_error_code(self, error_message: Optional[str]) -> str:
        """Extract error code from error message."""
        if not error_message:
            return "UNKNOWN"

        # Check for known error codes in the message
        for code in FAILURE_SEVERITY_MAP.keys():
            if code in error_message.upper():
                return code

        return "UNKNOWN"

    def get_incidents_for_run(self, run_id: str) -> list:
        """
        Get all incidents linked to a run.

        Used by SDSR expectations validator to check if incidents were created.

        Args:
            run_id: Run ID to check

        Returns:
            List of incident dicts
        """
        try:
            engine = self._get_engine()

            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, category, severity, status, created_at, is_synthetic
                        FROM incidents
                        WHERE source_run_id = :run_id
                        ORDER BY created_at DESC
                    """),
                    {"run_id": run_id},
                )

                incidents = []
                for row in result:
                    incidents.append(
                        {
                            "id": row[0],
                            "category": row[1],
                            "severity": row[2],
                            "status": row[3],
                            "created_at": row[4].isoformat() if row[4] else None,
                            "is_synthetic": row[5],
                        }
                    )

                return incidents

        except Exception as e:
            logger.error(f"Failed to get incidents for run {run_id}: {e}")
            return []


# Singleton instance for convenience
_incident_engine: Optional[IncidentEngine] = None


def get_incident_engine() -> IncidentEngine:
    """Get or create singleton incident engine instance."""
    global _incident_engine
    if _incident_engine is None:
        _incident_engine = IncidentEngine()
    return _incident_engine
