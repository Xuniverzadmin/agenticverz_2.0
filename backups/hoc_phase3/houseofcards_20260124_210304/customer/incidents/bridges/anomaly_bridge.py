# Layer: L4 — Domain Bridge
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker (called by analytics callers)
#   Execution: sync
# Role: Anomaly-to-Incident bridge (incidents-owned, not analytics)
# Callers: Orchestrators that process CostAnomalyFact from analytics
# Allowed Imports: L6 (incidents drivers), L4 (incident engines)
# Forbidden Imports: L1, L2, L3, analytics engines/drivers
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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.errors.governance import GovernanceError
from app.houseofcards.customer.incidents.drivers.incident_write_driver import (
    IncidentWriteDriver,
    get_incident_write_driver,
)
from app.metrics import governance_incidents_created_total

logger = logging.getLogger("nova.incidents.bridges.anomaly_bridge")


# =============================================================================
# COST ANOMALY FACT (Pure data from analytics — no DB, no side effects)
# =============================================================================


@dataclass
class CostAnomalyFact:
    """
    Pure fact emitted by analytics when a cost anomaly is detected.

    This dataclass contains NO database references, NO session objects,
    and NO imports from analytics. It is a pure data transfer object.

    Analytics engines emit this; the bridge decides what to do with it.
    """

    tenant_id: str
    anomaly_id: str
    anomaly_type: str  # BUDGET_EXCEEDED, ABSOLUTE_SPIKE, SUSTAINED_DRIFT, etc.
    severity: str  # LOW, MEDIUM, HIGH
    current_value_cents: int
    expected_value_cents: int
    entity_type: Optional[str] = None  # user, feature, tenant
    entity_id: Optional[str] = None
    deviation_pct: float = 0.0
    confidence: float = 1.0
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


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

    def __init__(self, session):
        """
        Initialize bridge with database session.

        Args:
            session: SQLModel Session for incident persistence
        """
        self._session = session
        self._driver = get_incident_write_driver(session)

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

            # Use driver to insert incident
            # Note: insert_incident expects source_run_id, we use anomaly_id
            # The driver's insert_incident is designed for run failures,
            # so we need to adapt slightly - using anomaly_id as source
            self._session.execute(
                self._build_incident_insert_sql(),
                {
                    "id": incident_id,
                    "tenant_id": fact.tenant_id,
                    "title": title,
                    "severity": incident_severity,
                    "status": "open",
                    "trigger_type": trigger_type,
                    "started_at": now,
                    "created_at": now,
                    "updated_at": now,
                    "source_type": "cost_anomaly",
                    "source_run_id": None,  # Cost anomalies don't come from runs
                    "category": "COST_ANOMALY",
                    "description": description,
                    "impact_scope": fact.entity_type or "tenant",
                    "affected_agent_id": fact.entity_id if fact.entity_type == "agent" else None,
                    "affected_count": 1,
                    "trigger_value": str(overage_cents),
                    "cost_delta_cents": Decimal(overage_cents),
                    "cost_impact": Decimal(overage_cents) / 100,
                    "cause_type": "SYSTEM",
                    "lifecycle_state": "ACTIVE",
                    "is_synthetic": False,
                    "synthetic_scenario_id": None,
                },
            )
            self._session.commit()

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

    def _build_incident_insert_sql(self):
        """Build SQL for incident insert."""
        from sqlalchemy import text
        return text("""
            INSERT INTO incidents (
                id, tenant_id, title, severity, status,
                trigger_type, started_at, created_at, updated_at,
                source_type, source_run_id, category, description,
                impact_scope, affected_agent_id, affected_count,
                trigger_value, cost_delta_cents, cost_impact,
                cause_type, lifecycle_state,
                is_synthetic, synthetic_scenario_id
            ) VALUES (
                :id, :tenant_id, :title, :severity, :status,
                :trigger_type, :started_at, :created_at, :updated_at,
                :source_type, :source_run_id, :category, :description,
                :impact_scope, :affected_agent_id, :affected_count,
                :trigger_value, :cost_delta_cents, :cost_impact,
                :cause_type, :lifecycle_state,
                :is_synthetic, :synthetic_scenario_id
            )
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        """)


def get_anomaly_incident_bridge(session) -> AnomalyIncidentBridge:
    """Factory function to get AnomalyIncidentBridge instance."""
    return AnomalyIncidentBridge(session)


__all__ = [
    "CostAnomalyFact",
    "AnomalyIncidentBridge",
    "get_anomaly_incident_bridge",
    "INCIDENT_SEVERITY_THRESHOLD",
]
