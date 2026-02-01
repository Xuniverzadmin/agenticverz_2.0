# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — run governance (policy evaluation + violation handling)
# Callers: Run lifecycle (worker completion), L2 APIs
# Allowed Imports: hoc_spine, hoc.cus.incidents.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 1B Wiring, PIN-407 (Success as First-Class Data)
# artifact_class: CODE

"""
Run Governance Handler (PIN-513 Batch 1B Wiring)

L4 handler that owns run-lifecycle policy side effects.

Wires three previously orphaned symbols from
incidents/L5_engines/policy_violation_engine.py:

- handle_policy_evaluation_for_run  (async run → evaluation record)
- handle_policy_violation           (async violation → incident flow)
- create_policy_evaluation_record   (async raw evaluation creation)

These are run-lifecycle side effects that must be owned by L4.
The L5 engine provides the business logic; L4 owns session and
invocation authority.

Flow:
  Run completed
    → RunGovernanceHandler.evaluate_run(session, run_id, tenant_id, run_status)
        → handle_policy_evaluation_for_run(session, ...)

  Policy violation detected
    → RunGovernanceHandler.report_violation(session, ...)
        → handle_policy_violation(session, ...)
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.hoc_spine.handlers.run_governance")


class RunGovernanceHandler:
    """L4 handler: run governance policy evaluation and violation handling.

    Owns invocation authority for policy evaluation side effects.
    L5 engine provides business logic and driver delegation.
    """

    async def evaluate_run(
        self,
        session: Any,
        run_id: str,
        tenant_id: str,
        run_status: str,
        policies_checked: int = 0,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> str:
        """Create policy evaluation record for a completed run (PIN-407).

        Every run MUST produce exactly one evaluation record.

        Args:
            session: AsyncSession for database operations
            run_id: Run ID
            tenant_id: Tenant scope
            run_status: Run outcome (succeeded/failed/halted/etc.)
            policies_checked: Number of policies evaluated
            is_synthetic: True if from SDSR scenario
            synthetic_scenario_id: Scenario ID for traceability

        Returns:
            policy_evaluation_id
        """
        from app.hoc.cus.incidents.L5_engines.policy_violation_engine import (
            handle_policy_evaluation_for_run,
        )

        evaluation_id = await handle_policy_evaluation_for_run(
            session=session,
            run_id=run_id,
            tenant_id=tenant_id,
            run_status=run_status,
            policies_checked=policies_checked,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )

        logger.info(
            "run_governance_evaluation_created",
            extra={
                "run_id": run_id,
                "tenant_id": tenant_id,
                "evaluation_id": evaluation_id,
                "run_status": run_status,
            },
        )

        return evaluation_id

    async def report_violation(
        self,
        session: Any,
        run_id: str,
        tenant_id: str,
        policy_type: str,
        policy_id: str,
        violated_rule: str,
        reason: str,
        severity: str = "medium",
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Handle a policy violation with S3 truth guarantees.

        Args:
            session: AsyncSession for database operations
            run_id: Run that triggered the violation
            tenant_id: Tenant scope
            policy_type: Policy category (CONTENT_ACCURACY, SAFETY, PII, etc.)
            policy_id: Specific policy violated
            violated_rule: Rule ID (e.g., CA001, PII_SSN)
            reason: Human-readable violation reason
            severity: Severity level (critical/high/medium/low)
            evidence: Optional evidence dictionary

        Returns:
            Dict with incident_id, violation_id, evidence_id if created;
            None if skipped
        """
        from app.hoc.cus.incidents.L5_engines.policy_violation_engine import (
            handle_policy_violation,
        )

        result = await handle_policy_violation(
            session=session,
            run_id=run_id,
            tenant_id=tenant_id,
            policy_type=policy_type,
            policy_id=policy_id,
            violated_rule=violated_rule,
            reason=reason,
            severity=severity,
            evidence=evidence,
        )

        if result:
            logger.info(
                "run_governance_violation_reported",
                extra={
                    "run_id": run_id,
                    "tenant_id": tenant_id,
                    "incident_id": result.incident_id,
                    "violation_id": result.violation_id,
                },
            )
            return {
                "incident_id": result.incident_id,
                "violation_id": result.violation_id,
                "evidence_id": result.evidence_id,
                "persisted": result.persisted,
            }

        return None

    async def create_evaluation(
        self,
        session: Any,
        run_id: str,
        tenant_id: str,
        outcome: str,
        policies_checked: int = 0,
        reason: str = "",
        draft_candidate: bool = False,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> str:
        """Create a raw policy evaluation record (low-level).

        Prefer evaluate_run() which maps run_status → outcome automatically.

        Args:
            session: AsyncSession
            run_id: Run ID
            tenant_id: Tenant scope
            outcome: Explicit outcome (no_violation/violation_incident/advisory/not_applicable)
            policies_checked: Number of policies evaluated
            reason: Human-readable reason
            draft_candidate: Policy learning flag
            is_synthetic: SDSR flag
            synthetic_scenario_id: Scenario ID

        Returns:
            policy_evaluation_id
        """
        from app.hoc.cus.incidents.L5_engines.policy_violation_engine import (
            create_policy_evaluation_record,
        )

        return await create_policy_evaluation_record(
            session=session,
            run_id=run_id,
            tenant_id=tenant_id,
            outcome=outcome,
            policies_checked=policies_checked,
            reason=reason,
            draft_candidate=draft_candidate,
            is_synthetic=is_synthetic,
            synthetic_scenario_id=synthetic_scenario_id,
        )
