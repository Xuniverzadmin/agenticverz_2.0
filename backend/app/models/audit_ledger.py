# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Audit Ledger model for Logs domain (PIN-413)
# Callers: runtime_projections/logs/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-413 Domain Design — Overview & Logs (CORRECTED)

"""
Audit Ledger Model (PIN-413 CORRECTED)

SCOPE: Logs domain ONLY. Not Overview.

AuditLedger is the immutable governance action log:
- Records governance-relevant actions taken by actors
- APPEND-ONLY (enforced by DB trigger)
- Only canonical events create rows

ARCHITECTURAL RULE:
- Overview is PROJECTION-ONLY (no owned tables)
- AuditLedger belongs to Logs domain
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time (PIN-413)."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string (PIN-413)."""
    return str(uuid.uuid4())


# =============================================================================
# Enums (Canonical Values - PIN-413)
# =============================================================================


class ActorType(str, Enum):
    """Types of actors performing actions."""
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"


class AuditEntityType(str, Enum):
    """Entity types tracked in audit ledger."""
    POLICY_RULE = "POLICY_RULE"
    POLICY_PROPOSAL = "POLICY_PROPOSAL"
    LIMIT = "LIMIT"
    INCIDENT = "INCIDENT"
    SIGNAL = "SIGNAL"


class AuditEventType(str, Enum):
    """Canonical audit events - only these create audit rows."""
    # Policies › Governance
    POLICY_RULE_CREATED = "PolicyRuleCreated"
    POLICY_RULE_MODIFIED = "PolicyRuleModified"
    POLICY_RULE_RETIRED = "PolicyRuleRetired"
    POLICY_PROPOSAL_APPROVED = "PolicyProposalApproved"
    POLICY_PROPOSAL_REJECTED = "PolicyProposalRejected"
    # Policies › Limits
    LIMIT_CREATED = "LimitCreated"
    LIMIT_UPDATED = "LimitUpdated"
    LIMIT_BREACHED = "LimitBreached"
    LIMIT_OVERRIDE_GRANTED = "LimitOverrideGranted"
    LIMIT_OVERRIDE_REVOKED = "LimitOverrideRevoked"
    # Incidents
    INCIDENT_ACKNOWLEDGED = "IncidentAcknowledged"
    INCIDENT_RESOLVED = "IncidentResolved"
    INCIDENT_MANUALLY_CLOSED = "IncidentManuallyClosed"
    # System / Control
    EMERGENCY_OVERRIDE_ACTIVATED = "EmergencyOverrideActivated"
    EMERGENCY_OVERRIDE_DEACTIVATED = "EmergencyOverrideDeactivated"
    # Signal Feedback
    SIGNAL_ACKNOWLEDGED = "SignalAcknowledged"
    SIGNAL_SUPPRESSED = "SignalSuppressed"
    SIGNAL_ESCALATED = "SignalEscalated"


# =============================================================================
# AuditLedger Model — Logs Domain (APPEND-ONLY)
# =============================================================================


class AuditLedger(SQLModel, table=True):
    """
    Immutable governance action log (Logs domain).

    Records governance-relevant actions taken by actors.
    APPEND-ONLY: No UPDATE, no DELETE (enforced by DB trigger).

    Invariants:
    - Only canonical events from AuditEventType create rows
    - Time-ordered within tenant
    - No joins required to read meaning
    """
    __tablename__ = "audit_ledger"

    id: str = Field(default_factory=generate_uuid, primary_key=True, max_length=64)
    tenant_id: str = Field(foreign_key="tenants.id", max_length=64)

    # Event classification
    event_type: str = Field(max_length=64)  # AuditEventType enum
    entity_type: str = Field(max_length=32)  # AuditEntityType enum
    entity_id: str = Field(max_length=64)

    # Actor information
    actor_type: str = Field(max_length=16)  # ActorType enum
    actor_id: Optional[str] = Field(default=None, max_length=64)

    # Reason / justification
    action_reason: Optional[str] = Field(default=None)

    # State snapshots (for MODIFY events)
    before_state: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    after_state: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamp (immutable once written)
    created_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# Export all
# =============================================================================

__all__ = [
    "ActorType",
    "AuditEntityType",
    "AuditEventType",
    "AuditLedger",
]
