# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident, IncidentEvent, Policy, Run, AosTrace
#   Writes: Incident, IncidentEvent, PreventionRecord, PolicyProposal, Run, AosTrace
# Database:
#   Scope: domain (incidents)
#   Models: Incident, IncidentEvent, IncidentStatus
# Role: Data access for incident write operations
# Callers: incident engines (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-281, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for incident writes.
# NO business logic - only DB operations.
# Business logic (decisions, mappings) stays in L4 engine.
#
# EXTRACTION STATUS:
# - 2026-01-23: Initial extraction (state transitions, events)
# - 2026-01-23: Extended with incident creation, prevention records (PIN-468)
#
# ============================================================================
# L6 DRIVER INVENTORY — INCIDENT DOMAIN (CANONICAL)
# ============================================================================
# Method                      | Purpose
# --------------------------- | ------------------------------------------
# fetch_suppressing_policy    | Policy suppression lookup
# insert_prevention_record    | Prevention audit record
# insert_incident             | Incident creation
# update_run_incident_count   | Run stats (incident_count++)
# update_trace_incident_id    | Trace linking (aos_traces.incident_id)
# insert_policy_proposal      | Proposal persistence
# fetch_incidents_by_run_id   | Incident query by run
# update_incident_acknowledged| State transition: OPEN → ACKNOWLEDGED
# update_incident_resolved    | State transition: * → RESOLVED
# create_incident_event       | Timeline event creation
# refresh_incident            | Post-commit refresh
# commit                      | Transaction commit
# ============================================================================
# This is the SINGLE persistence authority for incident domain writes.
# Do NOT create competing drivers. Extend this file.
# ============================================================================

"""
Incident Write Driver (L6)

Pure database write operations for incidents.
All business logic stays in L4 engine.

Operations:
- Create incidents from run failures/successes
- Create prevention records (policy suppression)
- Create policy proposals
- Update incident state (acknowledge, resolve)
- Update related tables (runs.incident_count, aos_traces.incident_id)
- Create incident events (timeline)

NO business logic:
- NO severity/category mapping (L4)
- NO policy suppression decisions (L4)
- NO proposal creation decisions (L4)

Reference: PIN-281, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session

# L6 imports (allowed)
from app.models.killswitch import Incident, IncidentEvent, IncidentStatus


class IncidentWriteDriver:
    """
    L6 driver for incident write operations.

    Pure database access - no business logic.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    def update_incident_acknowledged(
        self,
        incident: Incident,
        acknowledged_at: datetime,
        acknowledged_by: str,
    ) -> None:
        """
        Update incident to acknowledged status.

        Args:
            incident: Incident to update
            acknowledged_at: Timestamp of acknowledgment
            acknowledged_by: Who acknowledged
        """
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = acknowledged_at
        incident.acknowledged_by = acknowledged_by
        self._session.add(incident)

    def update_incident_resolved(
        self,
        incident: Incident,
        resolved_at: datetime,
        resolved_by: str,
        resolution_method: str | None = None,
    ) -> None:
        """
        Update incident to resolved status.

        Args:
            incident: Incident to update
            resolved_at: Timestamp of resolution
            resolved_by: Who resolved
            resolution_method: How it was resolved (optional)
        """
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = resolved_at
        incident.resolved_by = resolved_by
        if resolution_method:
            incident.resolution_method = resolution_method
        self._session.add(incident)

    def create_incident_event(
        self,
        incident_id: str,
        event_type: str,
        description: str,
    ) -> IncidentEvent:
        """
        Create a new incident timeline event.

        Args:
            incident_id: Parent incident ID
            event_type: Type of event (acknowledged, resolved, etc.)
            description: Event description

        Returns:
            Created IncidentEvent (not yet committed)
        """
        event = IncidentEvent(
            incident_id=incident_id,
            event_type=event_type,
            description=description,
        )
        self._session.add(event)
        return event

    def refresh_incident(self, incident: Incident) -> Incident:
        """
        Refresh incident from database after commit.

        Args:
            incident: Incident to refresh

        Returns:
            Refreshed Incident
        """
        self._session.refresh(incident)
        return incident


    # =========================================================================
    # INCIDENT CREATION (PIN-468 extraction from incident_engine.py)
    # =========================================================================

    def insert_incident(
        self,
        incident_id: str,
        tenant_id: str,
        title: str,
        severity: str,
        status: str,
        trigger_type: str,
        category: str,
        description: str,
        source_run_id: str,
        source_type: str,
        now: datetime,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        agent_id: Optional[str] = None,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> bool:
        """
        Insert a new incident record.

        Args:
            incident_id: Generated incident ID
            tenant_id: Tenant scope
            title: Incident title
            severity: Severity (CRITICAL, HIGH, MEDIUM, LOW, NONE)
            status: Status (OPEN, CLOSED)
            trigger_type: Trigger type (run_failure, run_completion)
            category: Category (EXECUTION_FAILURE, BUDGET_EXCEEDED, etc.)
            description: Incident description
            source_run_id: Source run ID
            source_type: Source type (run)
            now: Timestamp
            error_code: Error code (optional)
            error_message: Error message (optional)
            agent_id: Agent ID (optional)
            is_synthetic: Synthetic flag for SDSR
            synthetic_scenario_id: Scenario ID for SDSR

        Returns:
            True if inserted, False if conflict (already exists)
        """
        result = self._session.execute(
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
                RETURNING id
            """),
            {
                "id": incident_id,
                "tenant_id": tenant_id,
                "title": title,
                "severity": severity,
                "status": status,
                "trigger_type": trigger_type,
                "started_at": now,
                "created_at": now,
                "updated_at": now,
                "source_run_id": source_run_id,
                "source_type": source_type,
                "category": category,
                "description": description,
                "error_code": error_code,
                "error_message": error_message,
                "impact_scope": "single_run",
                "affected_agent_id": agent_id,
                "affected_count": 1,
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
            },
        )
        row = result.fetchone()
        return row is not None

    def update_run_incident_count(self, run_id: str) -> bool:
        """
        Increment incident_count on the runs table.

        Args:
            run_id: Run ID to update

        Returns:
            True if updated, False if run not found
        """
        result = self._session.execute(
            text("""
                UPDATE runs
                SET incident_count = incident_count + 1
                WHERE id = :run_id
                RETURNING id
            """),
            {"run_id": run_id},
        )
        row = result.fetchone()
        return row is not None

    def update_trace_incident_id(self, run_id: str, incident_id: str) -> int:
        """
        Propagate incident_id to aos_traces for cross-domain correlation.

        Args:
            run_id: Run ID to match traces
            incident_id: Incident ID to set

        Returns:
            Number of traces updated
        """
        result = self._session.execute(
            text("""
                UPDATE aos_traces
                SET incident_id = :incident_id
                WHERE run_id = :run_id
            """),
            {"incident_id": incident_id, "run_id": run_id},
        )
        return result.rowcount

    # =========================================================================
    # PREVENTION RECORDS (PIN-468 extraction)
    # =========================================================================

    def insert_prevention_record(
        self,
        prevention_id: str,
        policy_id: str,
        pattern_id: str,
        original_incident_id: str,
        blocked_incident_id: str,
        tenant_id: str,
        now: datetime,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> bool:
        """
        Insert a prevention record when policy suppresses an incident.

        Args:
            prevention_id: Generated prevention ID
            policy_id: Policy rule that caused suppression
            pattern_id: Error pattern matched
            original_incident_id: Original incident that created the policy
            blocked_incident_id: Run ID that was blocked (not the incident)
            tenant_id: Tenant scope
            now: Timestamp
            is_synthetic: Synthetic flag for SDSR
            synthetic_scenario_id: Scenario ID for SDSR

        Returns:
            True if inserted
        """
        self._session.execute(
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
                "pattern_id": pattern_id,
                "original_incident_id": original_incident_id,
                "blocked_incident_id": blocked_incident_id,
                "tenant_id": tenant_id,
                "outcome": "prevented",
                "signature_match_confidence": 1.0,
                "created_at": now,
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
            },
        )
        return True

    # =========================================================================
    # POLICY PROPOSALS (PIN-468 extraction)
    # =========================================================================

    def insert_policy_proposal(
        self,
        proposal_id: str,
        tenant_id: str,
        proposal_name: str,
        proposal_type: str,
        rationale: str,
        proposed_rule: Dict[str, Any],
        triggering_feedback_ids: List[str],
        now: datetime,
        is_synthetic: bool = False,
        synthetic_scenario_id: Optional[str] = None,
    ) -> bool:
        """
        Insert a policy proposal for high-severity incidents.

        Args:
            proposal_id: Generated proposal ID
            tenant_id: Tenant scope
            proposal_name: Proposal display name
            proposal_type: Type (timeout_policy, crash_recovery_policy, etc.)
            rationale: Human-readable rationale
            proposed_rule: JSON rule definition
            triggering_feedback_ids: List of incident IDs
            now: Timestamp
            is_synthetic: Synthetic flag for SDSR
            synthetic_scenario_id: Scenario ID for SDSR

        Returns:
            True if inserted
        """
        self._session.execute(
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
                "proposal_name": proposal_name,
                "proposal_type": proposal_type,
                "rationale": rationale,
                "proposed_rule": json.dumps(proposed_rule),
                "triggering_feedback_ids": json.dumps(triggering_feedback_ids),
                "status": "draft",
                "created_at": now,
                "is_synthetic": is_synthetic,
                "synthetic_scenario_id": synthetic_scenario_id,
            },
        )
        return True

    # =========================================================================
    # POLICY SUPPRESSION CHECK (PIN-468 extraction)
    # =========================================================================

    def fetch_suppressing_policy(
        self,
        tenant_id: str,
        error_code: str,
        category: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an active policy_rule suppresses this incident pattern.

        Args:
            tenant_id: Tenant scope
            error_code: Error code to match
            category: Error category to match

        Returns:
            Dict with policy info if suppressed, None if not
        """
        result = self._session.execute(
            text("""
                SELECT id, name, conditions, source_incident_id
                FROM policy_rules
                WHERE tenant_id = :tenant_id
                  AND is_active = true
                  AND mode = 'active'
                  AND (
                    conditions::text LIKE :error_pattern
                    OR conditions::text LIKE :category_pattern
                  )
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {
                "tenant_id": tenant_id,
                "error_pattern": f"%{error_code}%",
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

    # =========================================================================
    # INCIDENT QUERIES (PIN-468 extraction)
    # =========================================================================

    def fetch_incidents_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all incidents linked to a run.

        Args:
            run_id: Run ID to check

        Returns:
            List of incident dicts
        """
        result = self._session.execute(
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
            incidents.append({
                "id": row[0],
                "category": row[1],
                "severity": row[2],
                "status": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "is_synthetic": row[5],
            })
        return incidents

    # REMOVED: commit() helper — L6 DOES NOT COMMIT (L4 coordinator owns transaction boundary)


def get_incident_write_driver(session: Session) -> IncidentWriteDriver:
    """Factory function to get IncidentWriteDriver instance."""
    return IncidentWriteDriver(session)


__all__ = [
    "IncidentWriteDriver",
    "get_incident_write_driver",
]
