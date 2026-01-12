# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Incidents domain API - incidents list, details, and propagation trigger
# Callers: Customer Console Incidents page
# Reference: PIN-370 (SDSR), Customer Console v1 Constitution

"""
Incidents API - Incidents List for Customer Console

Queries the `incidents` table for SDSR pipeline validation.
Returns data compatible with IncidentsPage component.

SDSR Contract (PIN-370):
- Incidents are created by the Incident Engine, not by direct writes
- This API observes incidents, never creates them directly
- POST /trigger endpoint invokes Incident Engine for a failed run
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlmodel import Session

from app.models.killswitch import Incident
from app.db import Run, get_session as get_db_session
from app.services.incident_engine import get_incident_engine

router = APIRouter(prefix="/incidents", tags=["Incidents"])


# =============================================================================
# Response Models
# =============================================================================


class IncidentSummary(BaseModel):
    """Incident summary for list view."""
    id: str
    source_run_id: Optional[str]
    source_type: str
    category: str
    severity: str
    status: str
    title: str
    description: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    tenant_id: str
    affected_agent_id: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    is_synthetic: bool
    synthetic_scenario_id: Optional[str]


class IncidentsResponse(BaseModel):
    """Incidents list response."""
    incidents: List[IncidentSummary]
    total: int
    page: int
    per_page: int


class IncidentCountBySeverity(BaseModel):
    """Count of incidents by severity."""
    critical: int
    high: int
    medium: int
    low: int


class IncidentsMetricsResponse(BaseModel):
    """Incidents metrics/summary response."""
    total_open: int
    total_resolved: int
    by_severity: IncidentCountBySeverity


class TriggerIncidentRequest(BaseModel):
    """Request to trigger incident creation for a run."""
    run_id: str


class TriggerIncidentResponse(BaseModel):
    """Response from incident trigger."""
    incident_id: Optional[str]
    created: bool
    message: str


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=IncidentsResponse)
def list_incidents(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    include_synthetic: bool = Query(default=True, description="Include synthetic SDSR data"),
    session: Session = Depends(get_db_session),
):
    """
    List incidents for Incidents domain.

    Returns incidents from the `incidents` table for SDSR validation.
    By default includes synthetic data for preflight testing.

    Note: Auth bypassed for SDSR preflight validation (PIN-370)
    Route is public in gateway_config.py and rbac_middleware.py
    """
    # Build query
    query = select(Incident).order_by(Incident.created_at.desc())

    # Filter by status if provided
    if status:
        query = query.where(Incident.status == status)

    # Filter by severity if provided
    if severity:
        query = query.where(Incident.severity == severity)

    # Filter by category if provided
    if category:
        query = query.where(Incident.category == category)

    # Optionally exclude synthetic data
    if not include_synthetic:
        query = query.where((Incident.is_synthetic == False) | (Incident.is_synthetic.is_(None)))

    # Get total count (with same filters)
    count_query = select(Incident)
    if status:
        count_query = count_query.where(Incident.status == status)
    if severity:
        count_query = count_query.where(Incident.severity == severity)
    if category:
        count_query = count_query.where(Incident.category == category)
    if not include_synthetic:
        count_query = count_query.where((Incident.is_synthetic == False) | (Incident.is_synthetic.is_(None)))

    count_result = session.execute(count_query)
    total = len(count_result.scalars().all())

    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = session.execute(query)
    incidents = result.scalars().all()

    return IncidentsResponse(
        incidents=[
            IncidentSummary(
                id=i.id,
                source_run_id=i.source_run_id,
                source_type=i.source_type or "killswitch",
                category=i.category or "UNKNOWN",
                severity=i.severity.upper() if i.severity else "MEDIUM",
                status=i.status.upper() if i.status else "OPEN",
                title=i.title,
                description=i.description,
                error_code=i.error_code,
                error_message=i.error_message,
                tenant_id=i.tenant_id,
                affected_agent_id=i.affected_agent_id,
                created_at=i.created_at.isoformat() if i.created_at else "",
                updated_at=i.updated_at.isoformat() if i.updated_at else "",
                resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
                is_synthetic=i.is_synthetic or False,
                synthetic_scenario_id=i.synthetic_scenario_id,
            )
            for i in incidents
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/metrics", response_model=IncidentsMetricsResponse)
def get_incidents_metrics(
    include_synthetic: bool = Query(default=True, description="Include synthetic SDSR data"),
    session: Session = Depends(get_db_session),
):
    """
    Get summary metrics for incidents dashboard.

    Returns counts by status and severity.
    """
    base_filter = ""
    if not include_synthetic:
        base_filter = " AND (is_synthetic = false OR is_synthetic IS NULL)"

    # Count open incidents (from canonical incidents table - PIN-370 consolidation)
    open_result = session.execute(
        text(f"SELECT COUNT(*) FROM incidents WHERE UPPER(status) NOT IN ('RESOLVED', 'CLOSED'){base_filter}")
    )
    total_open = open_result.scalar() or 0

    # Count resolved incidents (from canonical incidents table)
    resolved_result = session.execute(
        text(f"SELECT COUNT(*) FROM incidents WHERE UPPER(status) IN ('RESOLVED', 'CLOSED'){base_filter}")
    )
    total_resolved = resolved_result.scalar() or 0

    # Count by severity (for open incidents) - handle case-insensitive
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        result = session.execute(
            text(f"SELECT COUNT(*) FROM incidents WHERE UPPER(severity) = :sev AND UPPER(status) NOT IN ('RESOLVED', 'CLOSED'){base_filter}"),
            {"sev": sev}
        )
        severity_counts[sev.lower()] = result.scalar() or 0

    return IncidentsMetricsResponse(
        total_open=total_open,
        total_resolved=total_resolved,
        by_severity=IncidentCountBySeverity(**severity_counts),
    )


@router.get("/{incident_id}", response_model=IncidentSummary)
def get_incident_detail(
    incident_id: str,
    session: Session = Depends(get_db_session),
):
    """
    Get details of a specific incident.

    Note: Auth bypassed for SDSR preflight validation (PIN-370)
    """
    result = session.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return IncidentSummary(
        id=incident.id,
        source_run_id=incident.source_run_id,
        source_type=incident.source_type or "killswitch",
        category=incident.category or "UNKNOWN",
        severity=incident.severity.upper() if incident.severity else "MEDIUM",
        status=incident.status.upper() if incident.status else "OPEN",
        title=incident.title,
        description=incident.description,
        error_code=incident.error_code,
        error_message=incident.error_message,
        tenant_id=incident.tenant_id,
        affected_agent_id=incident.affected_agent_id,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        is_synthetic=incident.is_synthetic or False,
        synthetic_scenario_id=incident.synthetic_scenario_id,
    )


@router.get("/by-run/{run_id}")
def get_incidents_for_run(
    run_id: str,
    session: Session = Depends(get_db_session),
):
    """
    Get all incidents linked to a specific run.

    Used by SDSR expectations validator and UI to show linked incidents.
    """
    result = session.execute(
        select(Incident).where(Incident.source_run_id == run_id).order_by(Incident.created_at.desc())
    )
    incidents = result.scalars().all()

    return {
        "run_id": run_id,
        "incidents": [
            IncidentSummary(
                id=i.id,
                source_run_id=i.source_run_id,
                source_type=i.source_type or "killswitch",
                category=i.category or "UNKNOWN",
                severity=i.severity.upper() if i.severity else "MEDIUM",
                status=i.status.upper() if i.status else "OPEN",
                title=i.title,
                description=i.description,
                error_code=i.error_code,
                error_message=i.error_message,
                tenant_id=i.tenant_id,
                affected_agent_id=i.affected_agent_id,
                created_at=i.created_at.isoformat() if i.created_at else "",
                updated_at=i.updated_at.isoformat() if i.updated_at else "",
                resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
                is_synthetic=i.is_synthetic or False,
                synthetic_scenario_id=i.synthetic_scenario_id,
            )
            for i in incidents
        ],
        "total": len(incidents),
    }


@router.post("/trigger", response_model=TriggerIncidentResponse, deprecated=True)
def trigger_incident_for_run(
    request: TriggerIncidentRequest,
    session: Session = Depends(get_db_session),
):
    """
    [DEPRECATED] Trigger incident creation for a failed run.

    ⚠️ DEPRECATION NOTICE (PIN-370):
    This endpoint is deprecated. Incidents are now created AUTOMATICALLY
    by the worker via Incident Engine when a run fails. Do not rely on
    this endpoint for new integrations.

    This endpoint remains for backward compatibility only and will be
    removed in a future release. It delegates to the Incident Engine
    internally (same as automatic creation).

    Migration path:
    - Remove calls to this endpoint
    - Incidents are auto-created on run failure
    - Use GET /incidents/by-run/{run_id} to check for incidents
    """
    import logging
    logger = logging.getLogger("nova.api.incidents")
    logger.warning(
        f"DEPRECATED: /api/v1/incidents/trigger called for run_id={request.run_id}. "
        "Incidents are now auto-created by worker. This endpoint will be removed."
    )

    # Fetch the run
    result = session.execute(
        select(Run).where(Run.id == request.run_id)
    )
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Check if run is failed
    if run.status != "failed":
        return TriggerIncidentResponse(
            incident_id=None,
            created=False,
            message=f"Run status is '{run.status}', not 'failed'. No incident created.",
        )

    # Check if incident already exists for this run
    existing = session.execute(
        select(Incident).where(Incident.source_run_id == request.run_id)
    )
    if existing.scalar_one_or_none():
        return TriggerIncidentResponse(
            incident_id=None,
            created=False,
            message="Incident already exists for this run",
        )

    # Trigger incident creation via Incident Engine
    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not run.tenant_id:
        raise HTTPException(status_code=400, detail="Run has no tenant_id. Cannot create incident.")
    engine = get_incident_engine()
    incident_id = engine.create_incident_for_failed_run(
        run_id=run.id,
        tenant_id=run.tenant_id,
        error_code=_extract_error_code(run.error_message),
        error_message=run.error_message,
        agent_id=run.agent_id,
        is_synthetic=run.is_synthetic,
        synthetic_scenario_id=run.synthetic_scenario_id,
    )

    if incident_id:
        return TriggerIncidentResponse(
            incident_id=incident_id,
            created=True,
            message=f"Incident {incident_id} created for run {run.id}",
        )
    else:
        return TriggerIncidentResponse(
            incident_id=None,
            created=False,
            message="Failed to create incident",
        )


def _extract_error_code(error_message: Optional[str]) -> str:
    """Extract error code from error message."""
    if not error_message:
        return "UNKNOWN"

    # Check for known error codes
    known_codes = [
        "EXECUTION_TIMEOUT", "AGENT_CRASH", "STEP_FAILURE", "SKILL_ERROR",
        "BUDGET_EXCEEDED", "RATE_LIMIT_EXCEEDED", "RESOURCE_EXHAUSTION",
        "CANCELLED", "MANUAL_STOP", "RETRY_EXHAUSTED"
    ]

    for code in known_codes:
        if code in error_message.upper():
            return code

    return "UNKNOWN"
