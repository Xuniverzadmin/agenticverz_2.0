# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync (async session)
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: incidents, policy_breaches
#   Writes: incidents, policy_breaches
# Database:
#   Scope: cross-domain (policies, incidents)
#   Models: Incident, PolicyBreach
# Role: Cross-Domain Governance - Mandatory data integrity functions
# Callers: cost_anomaly_detector, budget services, worker runtime
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3
# Reference: PIN-470, design/CROSS_DOMAIN_GOVERNANCE.md

"""
Cross-Domain Governance Functions (Mandatory)

PIN: design/CROSS_DOMAIN_GOVERNANCE.md

These functions implement mandatory governance for customer-facing paths.
They MUST succeed or raise GovernanceError. Silent failures are forbidden.

DOCTRINE:
- Rule 1: Governance must throw
- Rule 2: No optional dependencies
- Rule 3: Learning is downstream only

DOMAINS:
- Analytics → Incidents: Cost anomalies MUST create incidents
- Policies ↔ Analytics: Limit breaches MUST be recorded

COROLLARY: GovernanceError must surface - never catch and ignore.
"""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from app.errors.governance import GovernanceError
from app.metrics import (
    governance_incidents_created_total,
    governance_limit_breaches_recorded_total,
)
from app.models.killswitch import Incident
from app.models.policy_control_plane import LimitBreach

logger = logging.getLogger("nova.services.governance.cross_domain")


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# Severity Mapping (Analytics → Incidents)
# =============================================================================

ANOMALY_SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}

ANOMALY_TRIGGER_TYPE_MAP = {
    "BUDGET_EXCEEDED": "budget_breach",
    "USER_SPIKE": "cost_spike",
    "TENANT_SPIKE": "cost_spike",
    "DRIFT": "cost_drift",
    "DEFAULT": "cost_anomaly",
}


# =============================================================================
# Analytics → Incidents: create_incident_from_cost_anomaly
# =============================================================================


async def create_incident_from_cost_anomaly(
    session: AsyncSession,
    tenant_id: str,
    anomaly_id: str,
    anomaly_type: str,
    severity: str,
    current_value_cents: int,
    expected_value_cents: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Create an incident from a cost anomaly. MANDATORY.

    This function MUST succeed or raise GovernanceError.
    It cannot be skipped based on optional configuration.

    Args:
        session: Database session
        tenant_id: Tenant scope
        anomaly_id: ID of the cost anomaly
        anomaly_type: Type of anomaly (BUDGET_EXCEEDED, USER_SPIKE, etc.)
        severity: Anomaly severity (CRITICAL, HIGH, MEDIUM, LOW)
        current_value_cents: Actual cost in cents
        expected_value_cents: Expected cost in cents
        entity_type: Optional entity type (user, tenant, etc.)
        entity_id: Optional entity ID
        description: Optional description

    Returns:
        incident_id

    Raises:
        GovernanceError: If incident cannot be created

    Example:
        incident_id = await create_incident_from_cost_anomaly(
            session=session,
            tenant_id="tenant-123",
            anomaly_id="anomaly-456",
            anomaly_type="BUDGET_EXCEEDED",
            severity="HIGH",
            current_value_cents=15000,
            expected_value_cents=10000,
        )
    """
    try:
        incident_id = generate_uuid()
        now = utc_now()

        # Map severity
        incident_severity = ANOMALY_SEVERITY_MAP.get(severity.upper(), "medium")

        # Map trigger type
        trigger_type = ANOMALY_TRIGGER_TYPE_MAP.get(anomaly_type, "cost_anomaly")

        # Build title
        overage_cents = current_value_cents - expected_value_cents
        overage_usd = Decimal(overage_cents) / 100
        title = f"Cost anomaly: {anomaly_type} (+${overage_usd:.2f})"

        # Build description if not provided
        if not description:
            description = (
                f"Detected {anomaly_type} anomaly. "
                f"Current: ${current_value_cents / 100:.2f}, "
                f"Expected: ${expected_value_cents / 100:.2f}."
            )
            if entity_type and entity_id:
                description += f" Entity: {entity_type}/{entity_id}"

        incident = Incident(
            id=incident_id,
            tenant_id=tenant_id,
            title=title,
            severity=incident_severity,
            status="open",
            trigger_type=trigger_type,
            trigger_value=str(overage_cents),
            cost_delta_cents=Decimal(overage_cents),
            started_at=now,
            created_at=now,
            updated_at=now,
            source_type="cost_anomaly",
            category="COST_ANOMALY",
            description=description,
            impact_scope=entity_type or "tenant",
            affected_agent_id=entity_id if entity_type == "agent" else None,
            affected_count=1,
            cause_type="SYSTEM",
            lifecycle_state="ACTIVE",
            cost_impact=Decimal(overage_cents) / 100,
        )

        session.add(incident)
        await session.flush()

        # METRIC: Track successful incident creation
        governance_incidents_created_total.labels(
            domain="Analytics",
            source_type="cost_anomaly",
        ).inc()

        logger.info(
            f"[GOVERNANCE] Created incident {incident_id} from cost anomaly {anomaly_id} "
            f"(severity={severity}, type={anomaly_type})"
        )

        return incident_id

    except Exception as e:
        raise GovernanceError(
            message=str(e),
            domain="Analytics",
            operation="create_incident_from_cost_anomaly",
            entity_id=anomaly_id,
        ) from e


# =============================================================================
# Policies ↔ Analytics: record_limit_breach
# =============================================================================


async def record_limit_breach(
    session: AsyncSession,
    tenant_id: str,
    limit_id: str,
    breach_type: str,
    value_at_breach: Decimal,
    limit_value: Decimal,
    run_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> str:
    """
    Record a limit breach. MANDATORY.

    This function MUST succeed or raise GovernanceError.
    Every budget/rate/threshold breach MUST be recorded.

    Args:
        session: Database session
        tenant_id: Tenant scope
        limit_id: ID of the limit that was breached
        breach_type: Type of breach (BREACHED, EXHAUSTED, THROTTLED, VIOLATED)
        value_at_breach: The value that caused the breach
        limit_value: The limit value that was exceeded
        run_id: Optional ID of the run that caused the breach
        incident_id: Optional ID of resulting incident
        details: Optional additional context

    Returns:
        breach_id

    Raises:
        GovernanceError: If breach cannot be recorded

    Example:
        breach_id = await record_limit_breach(
            session=session,
            tenant_id="tenant-123",
            limit_id="limit-456",
            breach_type="BREACHED",
            value_at_breach=Decimal("150.00"),
            limit_value=Decimal("100.00"),
            run_id="run-789",
        )
    """
    try:
        breach_id = generate_uuid()
        now = utc_now()

        breach = LimitBreach(
            id=breach_id,
            tenant_id=tenant_id,
            limit_id=limit_id,
            run_id=run_id,
            incident_id=incident_id,
            breach_type=breach_type,
            value_at_breach=value_at_breach,
            limit_value=limit_value,
            details=details,
            breached_at=now,
        )

        session.add(breach)
        await session.flush()

        # METRIC: Track successful limit breach recording
        governance_limit_breaches_recorded_total.labels(
            breach_type=breach_type,
        ).inc()

        logger.info(
            f"[GOVERNANCE] Recorded limit breach {breach_id} for limit {limit_id} "
            f"(type={breach_type}, value={value_at_breach}, limit={limit_value})"
        )

        return breach_id

    except Exception as e:
        raise GovernanceError(
            message=str(e),
            domain="Policies",
            operation="record_limit_breach",
            entity_id=limit_id,
        ) from e


# =============================================================================
# Helper: Check if table exists (for defensive Overview queries)
# =============================================================================


async def table_exists(session: AsyncSession, table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Used by Overview for defensive queries that should degrade gracefully.

    Args:
        session: Database session
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise
    """
    try:
        from sqlalchemy import text

        result = await session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = :table_name
                )
                """
            ),
            {"table_name": table_name},
        )
        return result.scalar() or False
    except Exception as e:
        logger.warning(f"Failed to check if table {table_name} exists: {e}")
        return False


# =============================================================================
# SYNC VERSIONS (for code using sync SQLModel Session)
# =============================================================================
# Some legacy code uses sync sessions. These functions provide the same
# governance guarantees but work with sync Session instead of AsyncSession.


def create_incident_from_cost_anomaly_sync(
    session: Session,
    tenant_id: str,
    anomaly_id: str,
    anomaly_type: str,
    severity: str,
    current_value_cents: int,
    expected_value_cents: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """
    Create an incident from a cost anomaly (SYNC version). MANDATORY.

    Same as create_incident_from_cost_anomaly but for sync sessions.
    See async version for full documentation.

    Raises:
        GovernanceError: If incident cannot be created
    """
    try:
        incident_id = generate_uuid()
        now = utc_now()

        # Map severity
        incident_severity = ANOMALY_SEVERITY_MAP.get(severity.upper(), "medium")

        # Map trigger type
        trigger_type = ANOMALY_TRIGGER_TYPE_MAP.get(anomaly_type, "cost_anomaly")

        # Build title
        overage_cents = current_value_cents - expected_value_cents
        overage_usd = Decimal(overage_cents) / 100
        title = f"Cost anomaly: {anomaly_type} (+${overage_usd:.2f})"

        # Build description if not provided
        if not description:
            description = (
                f"Detected {anomaly_type} anomaly. "
                f"Current: ${current_value_cents / 100:.2f}, "
                f"Expected: ${expected_value_cents / 100:.2f}."
            )
            if entity_type and entity_id:
                description += f" Entity: {entity_type}/{entity_id}"

        incident = Incident(
            id=incident_id,
            tenant_id=tenant_id,
            title=title,
            severity=incident_severity,
            status="open",
            trigger_type=trigger_type,
            trigger_value=str(overage_cents),
            cost_delta_cents=Decimal(overage_cents),
            started_at=now,
            created_at=now,
            updated_at=now,
            source_type="cost_anomaly",
            category="COST_ANOMALY",
            description=description,
            impact_scope=entity_type or "tenant",
            affected_agent_id=entity_id if entity_type == "agent" else None,
            affected_count=1,
            cause_type="SYSTEM",
            lifecycle_state="ACTIVE",
            cost_impact=Decimal(overage_cents) / 100,
        )

        session.add(incident)
        session.flush()

        # METRIC: Track successful incident creation
        governance_incidents_created_total.labels(
            domain="Analytics",
            source_type="cost_anomaly",
        ).inc()

        logger.info(
            f"[GOVERNANCE] Created incident {incident_id} from cost anomaly {anomaly_id} "
            f"(severity={severity}, type={anomaly_type})"
        )

        return incident_id

    except Exception as e:
        raise GovernanceError(
            message=str(e),
            domain="Analytics",
            operation="create_incident_from_cost_anomaly_sync",
            entity_id=anomaly_id,
        ) from e


def record_limit_breach_sync(
    session: Session,
    tenant_id: str,
    limit_id: str,
    breach_type: str,
    value_at_breach: Decimal,
    limit_value: Decimal,
    run_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> str:
    """
    Record a limit breach (SYNC version). MANDATORY.

    Same as record_limit_breach but for sync sessions.
    See async version for full documentation.

    Raises:
        GovernanceError: If breach cannot be recorded
    """
    try:
        breach_id = generate_uuid()
        now = utc_now()

        breach = LimitBreach(
            id=breach_id,
            tenant_id=tenant_id,
            limit_id=limit_id,
            run_id=run_id,
            incident_id=incident_id,
            breach_type=breach_type,
            value_at_breach=value_at_breach,
            limit_value=limit_value,
            details=details,
            breached_at=now,
        )

        session.add(breach)
        session.flush()

        # METRIC: Track successful limit breach recording
        governance_limit_breaches_recorded_total.labels(
            breach_type=breach_type,
        ).inc()

        logger.info(
            f"[GOVERNANCE] Recorded limit breach {breach_id} for limit {limit_id} "
            f"(type={breach_type}, value={value_at_breach}, limit={limit_value})"
        )

        return breach_id

    except Exception as e:
        raise GovernanceError(
            message=str(e),
            domain="Policies",
            operation="record_limit_breach_sync",
            entity_id=limit_id,
        ) from e
