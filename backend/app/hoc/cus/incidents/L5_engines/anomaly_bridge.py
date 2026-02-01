# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker (called by analytics callers)
#   Execution: sync
# Role: Anomaly-to-Incident bridge (incidents-owned, not analytics)
# Callers: Orchestrators that process CostAnomalyFact from analytics
# Allowed Imports: L6 (incidents drivers), L4 (incident engines)
# Forbidden Imports: L1, L2, analytics engines/drivers
# Forbidden: session.commit(), session.rollback() — Adapter DOES NOT COMMIT (L4 coordinator owns)
# Reference: R1 Resolution — Analytics Authority Boundary
#
# GOVERNANCE NOTE:
# This bridge is OWNED BY INCIDENTS, not by analytics.
# Analytics emits pure CostAnomalyFact. This bridge decides if → incident.
#
# Authority model:
# - Analytics: Detect anomalies, compute severity/confidence
# - Incidents: Decide if anomaly warrants incident creation
# - Bridge: Translation boundary (owned by incidents)

"""
Anomaly-to-Incident Bridge

Accepts pure CostAnomalyFact from analytics and decides if an incident
should be created. This is NOT a general service - it applies incident
creation rules specific to cost anomalies.

Responsibilities:
- Accept CostAnomalyFact (pure data, no DB, no imports from analytics)
- Apply severity/confidence thresholds
- Apply deduplication window
- Apply suppression rules
- Map anomaly data to incident schema
- Delegate persistence to IncidentWriteDriver

This bridge ensures analytics never writes to incidents directly.
"""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.errors.governance import GovernanceError
from app.hoc.cus.incidents.L6_drivers.incident_write_driver import (
    IncidentWriteDriver,
    get_incident_write_driver,
)
from app.metrics import governance_incidents_created_total

logger = logging.getLogger("nova.incidents.adapters.anomaly_bridge")


# =============================================================================
# COST ANOMALY FACT (Pure data from analytics — no DB, no side effects)
# =============================================================================


# PIN-510 Phase 1C: CostAnomalyFact moved to hoc_spine/schemas/anomaly_types.py
# Backward-compat re-export (TOMBSTONE — remove when zero dependents confirmed)
from app.hoc.cus.hoc_spine.schemas.anomaly_types import CostAnomalyFact  # noqa: F401


# =============================================================================
# BRIDGE CONFIGURATION (Incident creation rules)
# =============================================================================

# Minimum severity to create incident (only HIGH creates incidents)
INCIDENT_SEVERITY_THRESHOLD = "HIGH"

# Severity mapping: Analytics severity → Incident severity
ANOMALY_SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}

# Trigger type mapping: Anomaly type → Incident trigger type
ANOMALY_TRIGGER_TYPE_MAP = {
    "BUDGET_EXCEEDED": "budget_breach",
    "ABSOLUTE_SPIKE": "cost_spike",
    "SUSTAINED_DRIFT": "cost_drift",
    "BUDGET_WARNING": "budget_warning",
    "USER_SPIKE": "cost_spike",  # Legacy compatibility
    "TENANT_SPIKE": "cost_spike",  # Legacy compatibility
    "DRIFT": "cost_drift",  # Legacy compatibility
}


# =============================================================================
# ANOMALY INCIDENT BRIDGE
# =============================================================================


class AnomalyIncidentBridge:
    """
    Bridge that accepts cost anomaly facts and creates incidents.

    OWNED BY INCIDENTS DOMAIN, not by analytics.

    This bridge applies incident creation rules:
    - Only HIGH severity anomalies create incidents
    - Deduplication prevents duplicate incidents
    - Suppression rules may block incident creation

    Usage:
        bridge = AnomalyIncidentBridge(session)
        incident_id = bridge.ingest(fact)  # Returns None if not created
    """

    def __init__(self, driver: IncidentWriteDriver):
        """
        Initialize bridge with incident write driver.

        PIN-508 Phase 1B: Accepts driver, not session.
        L5 must not receive session at all (Gap 2).

        Args:
            driver: IncidentWriteDriver instance for incident persistence
        """
        self._driver = driver

    def ingest(self, fact: CostAnomalyFact) -> Optional[str]:
        """
        Process a cost anomaly fact and create an incident if warranted.

        Decision rules (applied in order):
        1. Severity check: Only HIGH creates incidents
        2. Suppression check: Active policy may suppress
        3. Deduplication: Same anomaly today → update, not create

        Args:
            fact: Pure CostAnomalyFact from analytics

        Returns:
            incident_id if created, None if not created (suppressed, low severity, etc.)

        Raises:
            GovernanceError: If incident creation fails after passing all checks
        """
        # Rule 1: Only HIGH severity creates incidents
        if not self._meets_severity_threshold(fact.severity):
            logger.debug(
                f"Anomaly {fact.anomaly_id} below severity threshold "
                f"({fact.severity} < {INCIDENT_SEVERITY_THRESHOLD})"
            )
            return None

        # Rule 2: Check for active suppression policy
        if self._is_suppressed(fact):
            logger.info(
                f"Anomaly {fact.anomaly_id} suppressed by active policy"
            )
            return None

        # Rule 3: Check for existing incident (deduplication)
        existing = self._check_existing_incident(fact)
        if existing:
            logger.debug(
                f"Anomaly {fact.anomaly_id} already has incident {existing}"
            )
            return existing

        # All checks passed - create incident
        return self._create_incident(fact)

    def _meets_severity_threshold(self, severity: str) -> bool:
        """Check if severity meets threshold for incident creation."""
        # Only HIGH (and CRITICAL if it exists) creates incidents
        return severity.upper() in ("HIGH", "CRITICAL")

    def _is_suppressed(self, fact: CostAnomalyFact) -> bool:
        """
        Check if an active policy suppresses this anomaly type.

        Uses the incidents domain driver to check policy_rules.
        """
        # Anomaly code for matching
        error_code = f"COST_ANOMALY_{fact.anomaly_type}"
        category = "COST_ANOMALY"

        suppressing = self._driver.fetch_suppressing_policy(
            tenant_id=fact.tenant_id,
            error_code=error_code,
            category=category,
        )
        return suppressing is not None

    def _check_existing_incident(self, fact: CostAnomalyFact) -> Optional[str]:
        """
        Check for existing unresolved incident for this anomaly.

        Deduplication window: same anomaly_id on same day.
        """
        # Cost anomalies don't have source_run_id, so we check by anomaly metadata
        # For now, we don't have a direct lookup - return None
        # TODO: Add deduplication query to driver if needed
        return None

    def _create_incident(self, fact: CostAnomalyFact) -> str:
        """
        Create an incident from the cost anomaly fact.

        Applies incident schema mapping and delegates to driver.

        Raises:
            GovernanceError: If creation fails
        """
        try:
            incident_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            # Map severity
            incident_severity = ANOMALY_SEVERITY_MAP.get(
                fact.severity.upper(), "medium"
            )

            # Map trigger type
            trigger_type = ANOMALY_TRIGGER_TYPE_MAP.get(
                fact.anomaly_type, "cost_anomaly"
            )

            # Build title
            overage_cents = fact.current_value_cents - fact.expected_value_cents
            overage_usd = Decimal(overage_cents) / 100
            title = f"Cost anomaly: {fact.anomaly_type} (+${overage_usd:.2f})"

            # Build description
            description = (
                f"Detected {fact.anomaly_type} anomaly. "
                f"Current: ${fact.current_value_cents / 100:.2f}, "
                f"Expected: ${fact.expected_value_cents / 100:.2f}."
            )
            if fact.entity_type and fact.entity_id:
                description += f" Entity: {fact.entity_type}/{fact.entity_id}"

            # PIN-508 Phase 1B: Use driver method, not session.execute()
            self._driver.insert_incident_from_anomaly(
                incident_id=incident_id,
                tenant_id=fact.tenant_id,
                title=title,
                severity=incident_severity,
                trigger_type=trigger_type,
                category="COST_ANOMALY",
                description=description,
                impact_scope=fact.entity_type or "tenant",
                affected_agent_id=fact.entity_id if fact.entity_type == "agent" else None,
                cost_delta_cents=Decimal(overage_cents),
                now=now,
            )
            # NO COMMIT — L4 coordinator owns transaction boundary

            # Emit metric
            governance_incidents_created_total.labels(
                domain="Analytics",
                source_type="cost_anomaly",
            ).inc()

            logger.info(
                f"[BRIDGE] Created incident {incident_id} from cost anomaly "
                f"{fact.anomaly_id} (severity={fact.severity}, type={fact.anomaly_type})"
            )

            return incident_id

        except Exception as e:
            raise GovernanceError(
                message=str(e),
                domain="Incidents",
                operation="ingest_cost_anomaly",
                entity_id=fact.anomaly_id,
            ) from e

    # _build_incident_insert_sql removed — PIN-508 Phase 1B:
    # SQL moved to IncidentWriteDriver.insert_incident_from_anomaly()


def get_anomaly_incident_bridge(session) -> AnomalyIncidentBridge:
    """Factory function to get AnomalyIncidentBridge instance.

    PIN-508 Phase 1B: Creates driver from session, passes driver to bridge.
    Bridge no longer receives session directly.
    """
    driver = get_incident_write_driver(session)
    return AnomalyIncidentBridge(driver)


__all__ = [
    "CostAnomalyFact",
    "AnomalyIncidentBridge",
    "get_anomaly_incident_bridge",
    "INCIDENT_SEVERITY_THRESHOLD",
]
