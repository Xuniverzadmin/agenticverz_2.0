# capability_id: CAP-001
# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide (ops visibility)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Translate OpsIncident domain models to Founder-facing views
# Callers: ops.py (L2)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-264 (Phase-S Adapter)

"""
Founder Ops Adapter (L2)

Translates L4 OpsIncident domain models to Founder-facing API views.

L4 (OpsIncidentService) → L2 (ops.py)

The adapter:
1. Receives OpsIncident domain models from L4
2. Selects/renames fields for Founder audience
3. Applies minimal redaction if needed
4. Returns FounderIncidentSummaryView for L2

HARD RULES (from PIN-264):
- NO infra queries (that's L4's job)
- NO aggregation (that's L4's job)
- NO permissions logic (that's L2's job)
- NO pagination (that's L2's job)
- ONLY field selection, redaction, light renaming
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.hoc.fdr.ops.schemas.ops_domain_models import OpsIncident

# =============================================================================
# View DTOs (Founder-facing, not domain models)
# =============================================================================


@dataclass(frozen=True)
class FounderIncidentSummaryView:
    """
    Founder-facing incident summary.

    This is what L2 returns to Founder Console.
    Distinct from OpsIncident (L4 domain model).
    """

    incident_id: str
    title: str
    severity: str  # INFO, ATTENTION, ACTION, URGENT
    component: str
    occurrence_count: int
    first_seen: str  # ISO8601 string for JSON
    last_seen: str  # ISO8601 string for JSON
    affected_runs: int
    affected_agents: int
    is_resolved: bool


@dataclass(frozen=True)
class FounderIncidentsSummaryResponse:
    """
    Response for GET /ops/incidents/summary.

    Aggregated incident counts plus recent incidents.
    """

    total_incidents: int
    by_severity: dict  # {"urgent": 2, "action": 5, ...}
    recent_incidents: List[FounderIncidentSummaryView]
    window_start: str  # ISO8601
    window_end: str  # ISO8601


# =============================================================================
# Adapter Class
# =============================================================================


class FounderOpsAdapter:
    """
    Boundary adapter for Founder Ops incident views.

    This class provides the ONLY interface that L2 (ops.py) may use
    to access OpsIncident data. It translates domain models to
    Founder-facing views.

    PIN-264 Adapter Rule: Translation only, no business logic.
    """

    def to_summary_view(self, incident: OpsIncident) -> FounderIncidentSummaryView:
        """
        Convert a single OpsIncident to Founder-facing view.

        Field selection and formatting only.
        """
        return FounderIncidentSummaryView(
            incident_id=incident.incident_id,
            title=incident.title,
            severity=incident.severity.value,
            component=incident.component,
            occurrence_count=incident.occurrence_count,
            first_seen=incident.first_seen.isoformat() if incident.first_seen else "",
            last_seen=incident.last_seen.isoformat() if incident.last_seen else "",
            affected_runs=incident.affected_runs,
            affected_agents=incident.affected_agents,
            is_resolved=incident.is_resolved,
        )

    def to_summary_response(
        self,
        incidents: List[OpsIncident],
        summary_counts: dict,
        window_start: datetime,
        window_end: datetime,
        max_recent: int = 10,
    ) -> FounderIncidentsSummaryResponse:
        """
        Convert incident list and summary to Founder-facing response.

        Args:
            incidents: List of OpsIncident from L4
            summary_counts: Dict from OpsIncidentService.get_incident_summary()
            window_start: Query window start
            window_end: Query window end
            max_recent: Max recent incidents to include (default 10)

        Returns:
            FounderIncidentsSummaryResponse for L2 to return
        """
        # Convert incidents to views (limit to max_recent)
        recent_views = [self.to_summary_view(inc) for inc in incidents[:max_recent]]

        return FounderIncidentsSummaryResponse(
            total_incidents=len(incidents),
            by_severity=summary_counts,
            recent_incidents=recent_views,
            window_start=window_start.isoformat(),
            window_end=window_end.isoformat(),
        )
