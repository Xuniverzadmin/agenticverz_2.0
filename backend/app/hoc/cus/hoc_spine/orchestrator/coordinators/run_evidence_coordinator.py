# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — run evidence aggregation
# Callers: ActivityFacade (L5)
# Allowed Imports: hoc_spine, bridges (lazy)
# Forbidden Imports: L1, L2, L5 engines directly
# Reference: PIN-519 System Run Introspection
# artifact_class: CODE

"""
Run Evidence Coordinator (PIN-519)

L4 coordinator that composes cross-domain impact for a run.

Aggregates:
- Incidents caused by the run
- Policies evaluated during the run
- Limits breached by the run
- Decisions made during the run
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
    DecisionSummary,
    IncidentSummary,
    LimitHitSummary,
    PolicyEvaluationSummary,
    RunEvidenceResult,
)

logger = logging.getLogger("nova.hoc_spine.coordinators.run_evidence")


class RunEvidenceCoordinator:
    """L4 coordinator: Compose run impact from multiple domains.

    Aggregates evidence from incidents, policies, and controls domains
    to provide a complete picture of a run's cross-domain impact.
    """

    async def get_run_evidence(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> RunEvidenceResult:
        """
        Derive cross-domain impact for a run.

        Args:
            session: Database session
            tenant_id: Tenant ID for isolation
            run_id: Run ID to fetch evidence for

        Returns:
            RunEvidenceResult with cross-domain impact
        """
        # Get bridges (lazy imports to avoid circular dependencies)
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge import (
            get_incidents_bridge,
        )
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.policies_bridge import (
            get_policies_bridge,
        )
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge import (
            get_controls_bridge,
        )

        incidents_bridge = get_incidents_bridge()
        policies_bridge = get_policies_bridge()
        controls_bridge = get_controls_bridge()

        # Gather incidents caused by this run
        incidents_caused = await self._get_incidents_for_run(
            incidents_bridge, session, tenant_id, run_id
        )

        # Gather policy evaluations for this run
        policies_evaluated = await self._get_policy_evaluations_for_run(
            policies_bridge, session, tenant_id, run_id
        )

        # Gather limit breaches for this run
        limits_hit = await self._get_limit_breaches_for_run(
            controls_bridge, session, tenant_id, run_id
        )

        # Decisions are derived from policy evaluations
        decisions_made = self._derive_decisions(policies_evaluated)

        logger.info(
            "run_evidence_composed",
            extra={
                "tenant_id": tenant_id,
                "run_id": run_id,
                "incidents_count": len(incidents_caused),
                "policies_count": len(policies_evaluated),
                "limits_count": len(limits_hit),
                "decisions_count": len(decisions_made),
            },
        )

        return RunEvidenceResult(
            run_id=run_id,
            incidents_caused=incidents_caused,
            policies_evaluated=policies_evaluated,
            limits_hit=limits_hit,
            decisions_made=decisions_made,
            computed_at=datetime.now(timezone.utc),
        )

    async def _get_incidents_for_run(
        self,
        bridge: Any,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> list[IncidentSummary]:
        """Get incidents caused by this run via IncidentsBridge."""
        try:
            reader = bridge.incidents_for_run_capability(session)
            incidents, _ = reader.list_incidents(
                tenant_id=tenant_id,
                limit=100,
            )

            # Filter to incidents related to this run
            # (incidents have run_id in their context)
            return [
                IncidentSummary(
                    incident_id=str(inc.id),
                    severity=inc.severity if hasattr(inc, "severity") else "UNKNOWN",
                    title=inc.title if hasattr(inc, "title") else "Untitled",
                    created_at=inc.created_at if hasattr(inc, "created_at") else datetime.now(timezone.utc),
                )
                for inc in incidents
                if hasattr(inc, "run_id") and inc.run_id == run_id
            ]
        except Exception as e:
            logger.warning(f"Failed to get incidents for run {run_id}: {e}")
            return []

    async def _get_policy_evaluations_for_run(
        self,
        bridge: Any,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> list[PolicyEvaluationSummary]:
        """Get policy evaluations for this run via PoliciesBridge."""
        try:
            reader = bridge.policy_evaluations_capability(session)
            evaluations = await reader.fetch_policy_evaluations_for_run(
                tenant_id=tenant_id,
                run_id=run_id,
            )

            return [
                PolicyEvaluationSummary(
                    policy_id=ev["rule_id"],
                    policy_name=ev.get("rule_name", "Unknown"),
                    outcome=ev.get("action_taken", "UNKNOWN"),
                    evaluated_at=ev.get("triggered_at", datetime.now(timezone.utc)),
                )
                for ev in evaluations
            ]
        except Exception as e:
            logger.warning(f"Failed to get policy evaluations for run {run_id}: {e}")
            return []

    async def _get_limit_breaches_for_run(
        self,
        bridge: Any,
        session: Any,
        tenant_id: str,
        run_id: str,
    ) -> list[LimitHitSummary]:
        """Get limit breaches for this run via ControlsBridge."""
        try:
            reader = bridge.limit_breaches_capability(session)
            breaches = await reader.fetch_limit_breaches_for_run(
                tenant_id=tenant_id,
                run_id=run_id,
            )

            return [
                LimitHitSummary(
                    limit_id=br["limit_id"],
                    limit_name=br.get("limit_name", "Unknown"),
                    breached_value=float(br.get("value_at_breach") or 0),
                    threshold_value=float(br.get("threshold_value") or 0),
                    breached_at=br.get("breached_at", datetime.now(timezone.utc)),
                )
                for br in breaches
            ]
        except Exception as e:
            logger.warning(f"Failed to get limit breaches for run {run_id}: {e}")
            return []

    def _derive_decisions(
        self,
        evaluations: list[PolicyEvaluationSummary],
    ) -> list[DecisionSummary]:
        """Derive decisions from policy evaluations."""
        return [
            DecisionSummary(
                decision_id=f"dec-{ev.policy_id[:8]}",
                decision_type="POLICY_EVALUATION",
                outcome=ev.outcome,
                decided_at=ev.evaluated_at,
            )
            for ev in evaluations
            if ev.outcome in ("BLOCKED", "WARNED")
        ]


# =============================================================================
# Singleton
# =============================================================================

_instance = None


def get_run_evidence_coordinator() -> RunEvidenceCoordinator:
    """Get the singleton RunEvidenceCoordinator instance."""
    global _instance
    if _instance is None:
        _instance = RunEvidenceCoordinator()
    return _instance


__all__ = [
    "RunEvidenceCoordinator",
    "get_run_evidence_coordinator",
]
