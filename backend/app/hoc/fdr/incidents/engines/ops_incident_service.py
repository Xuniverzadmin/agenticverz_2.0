# Layer: L4 — Domain Engines
# Product: system-wide (ops visibility)
# Temporal:
#   Trigger: api|scheduler
#   Execution: sync
# Role: Translate infra errors into operator-facing incidents
# Callers: L3 adapters (FounderOpsAdapter, PreflightOpsAdapter)
# Allowed Imports: L6 (infra stores), L4 (ops domain models)
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-264 (Phase-S L4 Aggregation)

"""
Ops Incident Service — L4 Aggregation Layer

Translates infra truth (ErrorEnvelope) into operator understanding (OpsIncident).

This service answers: "What incidents are happening?"

Design Principles:
- INPUT: Time window, severity threshold, optional component scope
- OUTPUT: List[OpsIncident] (domain models only)
- NO: UI shaping, pagination, sorting for display, auth, filtering by role

HARD RULES:
1. Never return infra artifacts (ErrorEnvelope, raw DB rows)
2. Never know about consoles (fops, preflight)
3. Never paginate (that's L3's job)
4. Must be unit-testable with fake infra data

Aggregation Logic:
- Group errors by (component, error_class) within time window
- Collapse repeated errors into single incident
- Compute severity based on occurrence count and error severity
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from app.hoc.fdr.ops.schemas.ops_domain_models import (
    OpsIncident,
    OpsIncidentCategory,
    OpsSeverity,
)

# =============================================================================
# Protocol for Dependency Injection (enables unit testing)
# =============================================================================


class ErrorStoreProtocol(Protocol):
    """
    Protocol for error store dependency.

    Allows injection of fake store for unit testing.
    """

    def get_errors_by_component(
        self,
        component: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]: ...

    def get_error_counts_by_class(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]: ...

    def get_error_counts_by_component(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]: ...


# =============================================================================
# Service Configuration (no UI concepts)
# =============================================================================


@dataclass(frozen=True)
class IncidentAggregationConfig:
    """
    Configuration for incident aggregation.

    These are domain thresholds, not UI preferences.
    """

    # Minimum errors to form an incident
    min_occurrence_count: int = 2

    # Severity escalation thresholds
    attention_threshold: int = 3  # >= 3 errors = ATTENTION
    action_threshold: int = 10  # >= 10 errors = ACTION
    urgent_threshold: int = 50  # >= 50 errors = URGENT

    # Time window for grouping (default: 1 hour)
    grouping_window_minutes: int = 60


# =============================================================================
# Ops Incident Service
# =============================================================================


class OpsIncidentService:
    """
    L4 Aggregation Service for incidents.

    Queries infra persistence and returns OpsIncident domain models.

    Usage:
        service = OpsIncidentService(error_store)
        incidents = service.get_active_incidents(
            since=datetime.now(timezone.utc) - timedelta(hours=24)
        )
    """

    def __init__(
        self,
        error_store: ErrorStoreProtocol,
        config: Optional[IncidentAggregationConfig] = None,
    ):
        """
        Initialize with error store dependency.

        Args:
            error_store: Error store (real or fake for testing)
            config: Optional aggregation configuration
        """
        self._store = error_store
        self._config = config or IncidentAggregationConfig()

    def get_active_incidents(
        self,
        since: datetime,
        until: Optional[datetime] = None,
        component: Optional[str] = None,
        min_severity: Optional[OpsSeverity] = None,
    ) -> List[OpsIncident]:
        """
        Get active incidents within a time window.

        This is the primary method for incident aggregation.

        Args:
            since: Start of time window
            until: End of time window (default: now)
            component: Optional component filter
            min_severity: Optional minimum severity filter

        Returns:
            List of OpsIncident domain models (not infra artifacts)
        """
        if until is None:
            until = datetime.now(timezone.utc)

        # Query raw error data from infra store
        raw_errors = self._query_errors(since, until, component)

        # Aggregate into incidents
        incidents = self._aggregate_to_incidents(raw_errors, since, until)

        # Filter by severity if requested
        if min_severity is not None:
            severity_order = [
                OpsSeverity.INFO,
                OpsSeverity.ATTENTION,
                OpsSeverity.ACTION,
                OpsSeverity.URGENT,
            ]
            min_index = severity_order.index(min_severity)
            incidents = [inc for inc in incidents if severity_order.index(inc.severity) >= min_index]

        # Sort by severity (descending) then occurrence count
        incidents.sort(
            key=lambda i: (
                -[OpsSeverity.INFO, OpsSeverity.ATTENTION, OpsSeverity.ACTION, OpsSeverity.URGENT].index(i.severity),
                -i.occurrence_count,
            )
        )

        return incidents

    def get_incident_by_component(
        self,
        component: str,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Optional[OpsIncident]:
        """
        Get the aggregated incident for a specific component.

        Returns None if no errors found for the component.
        """
        incidents = self.get_active_incidents(
            since=since,
            until=until,
            component=component,
        )

        if not incidents:
            return None

        # Return the most severe incident for this component
        return incidents[0]

    def get_incident_summary(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get summary counts by severity level.

        Returns dict like: {"urgent": 2, "action": 5, "attention": 10, "info": 3}
        """
        incidents = self.get_active_incidents(since=since, until=until)

        summary = {
            "urgent": 0,
            "action": 0,
            "attention": 0,
            "info": 0,
        }

        for inc in incidents:
            summary[inc.severity.value] += 1

        return summary

    # =========================================================================
    # Private Methods (Aggregation Logic)
    # =========================================================================

    def _query_errors(
        self,
        since: datetime,
        until: datetime,
        component: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Query raw errors from infra store.

        This is the ONLY place that touches infra data.
        Everything after this works with domain concepts.
        """
        # Use raw SQL for aggregation query
        from sqlalchemy import text
        from sqlmodel import Session

        from app.db import engine

        with Session(engine) as session:
            if component:
                # Query specific component
                stmt = text(
                    """
                    SELECT
                        component,
                        error_class,
                        severity,
                        COUNT(*) as occurrence_count,
                        MIN(timestamp) as first_seen,
                        MAX(timestamp) as last_seen,
                        COUNT(DISTINCT run_id) as affected_runs,
                        COUNT(DISTINCT agent_id) as affected_agents,
                        (array_agg(correlation_id))[1] as sample_correlation_id,
                        (array_agg(message))[1] as sample_message
                    FROM infra_error_events
                    WHERE component = :component
                      AND timestamp >= :since
                      AND timestamp < :until
                    GROUP BY component, error_class, severity
                    HAVING COUNT(*) >= :min_count
                """
                )
                result = session.execute(
                    stmt,
                    {
                        "component": component,
                        "since": since,
                        "until": until,
                        "min_count": self._config.min_occurrence_count,
                    },
                )
            else:
                # Query all components
                stmt = text(
                    """
                    SELECT
                        component,
                        error_class,
                        severity,
                        COUNT(*) as occurrence_count,
                        MIN(timestamp) as first_seen,
                        MAX(timestamp) as last_seen,
                        COUNT(DISTINCT run_id) as affected_runs,
                        COUNT(DISTINCT agent_id) as affected_agents,
                        (array_agg(correlation_id))[1] as sample_correlation_id,
                        (array_agg(message))[1] as sample_message
                    FROM infra_error_events
                    WHERE timestamp >= :since
                      AND timestamp < :until
                    GROUP BY component, error_class, severity
                    HAVING COUNT(*) >= :min_count
                """
                )
                result = session.execute(
                    stmt,
                    {
                        "since": since,
                        "until": until,
                        "min_count": self._config.min_occurrence_count,
                    },
                )

            return [dict(row._mapping) for row in result.fetchall()]

    def _aggregate_to_incidents(
        self,
        raw_errors: List[Dict[str, Any]],
        since: datetime,
        until: datetime,
    ) -> List[OpsIncident]:
        """
        Convert raw error aggregates to OpsIncident domain models.

        This is where infra → domain translation happens.
        """
        incidents = []

        for row in raw_errors:
            # Map error_class to incident category
            category = self._classify_incident(row["error_class"])

            # Compute severity based on occurrence count
            severity = self._compute_severity(row["occurrence_count"])

            # Build human-readable title and description
            title = self._build_title(
                category,
                row["component"],
                row["occurrence_count"],
            )
            description = self._build_description(
                row["error_class"],
                row.get("sample_message", ""),
                row["occurrence_count"],
            )

            # Create domain model (no infra artifacts)
            incident = OpsIncident(
                incident_id=f"ops_inc_{row['component'][:20]}_{row['error_class'][:20]}",
                category=category,
                severity=severity,
                title=title,
                description=description,
                component=row["component"],
                affected_runs=row.get("affected_runs") or 0,
                affected_agents=row.get("affected_agents") or 0,
                first_seen=row["first_seen"],
                last_seen=row["last_seen"],
                occurrence_count=row["occurrence_count"],
                sample_correlation_id=row.get("sample_correlation_id"),
                is_resolved=False,
                context={
                    "error_class": row["error_class"],
                    "infra_severity": row["severity"],
                },
            )

            incidents.append(incident)

        return incidents

    def _classify_incident(self, error_class: str) -> OpsIncidentCategory:
        """
        Map infra error_class to operator-facing incident category.

        This is domain interpretation, not data mapping.
        """
        # Parse error class prefix
        if error_class.startswith("domain.budget"):
            return OpsIncidentCategory.BUDGET_EXHAUSTION
        elif error_class.startswith("domain.policy"):
            return OpsIncidentCategory.POLICY_VIOLATION
        elif error_class.startswith("domain.rate"):
            return OpsIncidentCategory.RATE_LIMIT
        elif error_class.startswith("infra.external"):
            return OpsIncidentCategory.EXTERNAL_DEPENDENCY
        elif error_class.startswith("infra."):
            return OpsIncidentCategory.EXECUTION_FAILURE
        elif error_class.startswith("system.recovery"):
            return OpsIncidentCategory.RECOVERY_FAILURE
        elif error_class.startswith("system.config"):
            return OpsIncidentCategory.CONFIGURATION
        elif error_class.startswith("system."):
            return OpsIncidentCategory.EXECUTION_FAILURE
        else:
            return OpsIncidentCategory.UNKNOWN

    def _compute_severity(self, occurrence_count: int) -> OpsSeverity:
        """
        Compute operator severity based on occurrence count.

        This reflects operational urgency, not technical severity.
        """
        if occurrence_count >= self._config.urgent_threshold:
            return OpsSeverity.URGENT
        elif occurrence_count >= self._config.action_threshold:
            return OpsSeverity.ACTION
        elif occurrence_count >= self._config.attention_threshold:
            return OpsSeverity.ATTENTION
        else:
            return OpsSeverity.INFO

    def _build_title(
        self,
        category: OpsIncidentCategory,
        component: str,
        count: int,
    ) -> str:
        """
        Build human-readable incident title.
        """
        # Extract short component name
        short_component = component.split(".")[-1] if "." in component else component

        category_labels = {
            OpsIncidentCategory.EXECUTION_FAILURE: "Execution failures",
            OpsIncidentCategory.BUDGET_EXHAUSTION: "Budget exhaustion",
            OpsIncidentCategory.POLICY_VIOLATION: "Policy violations",
            OpsIncidentCategory.RECOVERY_FAILURE: "Recovery failures",
            OpsIncidentCategory.EXTERNAL_DEPENDENCY: "External service issues",
            OpsIncidentCategory.CONFIGURATION: "Configuration errors",
            OpsIncidentCategory.RATE_LIMIT: "Rate limiting",
            OpsIncidentCategory.UNKNOWN: "Errors",
        }

        label = category_labels.get(category, "Issues")
        return f"{label} in {short_component} ({count}x)"

    def _build_description(
        self,
        error_class: str,
        sample_message: str,
        count: int,
    ) -> str:
        """
        Build human-readable incident description.
        """
        # Truncate message if too long
        if sample_message and len(sample_message) > 200:
            sample_message = sample_message[:197] + "..."

        if sample_message:
            return f"{count} occurrences of {error_class}. Example: {sample_message}"
        else:
            return f"{count} occurrences of {error_class}"
