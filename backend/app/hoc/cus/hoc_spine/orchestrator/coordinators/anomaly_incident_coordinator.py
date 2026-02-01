# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — analytics anomaly detection → incidents bridge
# Callers: analytics_handler.py (L4), legacy run_anomaly_detection_with_governance
# Allowed Imports: hoc_spine, hoc.cus.* (lazy — L4 can import L5/L6)
# Forbidden Imports: L1, L2
# Reference: PIN-510 Phase 1C, PIN-513 Wiring Plan #4 (coordination_audit_driver injection)
# artifact_class: CODE

"""
Anomaly Incident Coordinator (PIN-510 Phase 1C)

L4 coordinator that owns the cross-domain sequencing:
  analytics (detect) → incidents (ingest)

This coordinator replaces the direct cross-domain imports in
cost_anomaly_detector_engine.py (lines 976, 982, 1048).

Responsibilities:
- Call analytics detection (returns pure CostAnomalyFact list)
- Pass facts to incidents bridge for incident creation
- Return combined results

Rules:
- No retry logic (L4 coordinators are pass-through)
- No business logic (that belongs in L5 engines)
- Cross-domain sequencing ONLY
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger("nova.hoc_spine.coordinators.anomaly_incident")


class AnomalyIncidentCoordinator:
    """L4 coordinator: analytics anomaly detection → incidents bridge.

    Owns the cross-domain sequencing that previously lived in
    run_anomaly_detection_with_governance() (deprecated).
    """

    async def detect_and_ingest(self, session: Any, tenant_id: str) -> dict:
        """Run analytics detection, then pass facts to incidents bridge.

        Args:
            session: Database session (passed to both domains)
            tenant_id: Tenant to detect anomalies for

        Returns:
            {
                "detected": [CostAnomaly, ...],
                "incidents_created": [{"anomaly_id": str, "incident_id": str}, ...],
            }
        """
        # Step 1: Analytics detects (returns pure facts)
        from app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine import (
            _run_anomaly_detection_with_facts,
        )

        result = await _run_anomaly_detection_with_facts(session, tenant_id)

        if not result["facts"]:
            return {"detected": result["detected"], "incidents_created": []}

        # Step 2: Incidents bridge ingests facts
        from app.hoc.cus.incidents.L5_engines.anomaly_bridge import (
            get_anomaly_incident_bridge,
        )

        bridge = get_anomaly_incident_bridge(session)
        incidents_created = []

        for fact in result["facts"]:
            incident_id = bridge.ingest(fact)
            if incident_id:
                incidents_created.append({
                    "anomaly_id": fact.anomaly_id,
                    "incident_id": incident_id,
                })
                logger.info(
                    f"Anomaly {fact.anomaly_id} → incident {incident_id} "
                    f"(tenant={tenant_id})"
                )

        return {
            "detected": result["detected"],
            "incidents_created": incidents_created,
        }

    def persist_coordination_audit(
        self,
        session: Any,
        envelope_id: str,
        envelope_class: str,
        decision: str,
        reason: str,
        conflicting_envelope_id: Optional[str] = None,
        preempting_envelope_id: Optional[str] = None,
        active_envelopes_count: int = 0,
        tenant_id: Optional[str] = None,
        emit_traces: bool = True,
    ) -> bool:
        """Persist a coordination audit record via L6 driver.

        L4 coordinator owns transaction boundary — driver does session.add()
        but does NOT commit.

        Args:
            session: Database session
            envelope_id: Envelope being coordinated
            envelope_class: SAFETY, RELIABILITY, COST, or PERFORMANCE
            decision: APPLIED, REJECTED, or PREEMPTED
            reason: Human-readable reason
            conflicting_envelope_id: For REJECTED decisions
            preempting_envelope_id: For PREEMPTED decisions
            active_envelopes_count: Active envelopes at decision time
            tenant_id: Tenant identifier
            emit_traces: If False, skip persistence (replay mode)

        Returns:
            True if persisted, False on failure (non-blocking)
        """
        from app.hoc.cus.analytics.L6_drivers.coordination_audit_driver import (
            persist_audit_record,
        )

        return persist_audit_record(
            db=session,
            audit_id=str(uuid4()),
            envelope_id=envelope_id,
            envelope_class=envelope_class,
            decision=decision,
            reason=reason,
            decision_timestamp=datetime.now(timezone.utc),
            conflicting_envelope_id=conflicting_envelope_id,
            preempting_envelope_id=preempting_envelope_id,
            active_envelopes_count=active_envelopes_count,
            tenant_id=tenant_id,
            emit_traces=emit_traces,
        )


# Singleton
_instance = None


def get_anomaly_incident_coordinator() -> AnomalyIncidentCoordinator:
    """Get the singleton AnomalyIncidentCoordinator instance."""
    global _instance
    if _instance is None:
        _instance = AnomalyIncidentCoordinator()
    return _instance


__all__ = [
    "AnomalyIncidentCoordinator",
    "get_anomaly_incident_coordinator",
]
