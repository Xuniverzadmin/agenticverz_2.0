# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Governance signal data models (DB tables)
# Callers: governance/*, L4 orchestrators, L5 executors
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-256 Phase E FIX-03

"""
Governance Signal Models (Phase E FIX-03)

Models for persisting governance decisions from L7 (BLCA, CI) to L6,
making governance influence explicit and queryable by L4/L5.

Phase E Contract:
- L7 writes governance signals to L6
- L4 reads signals before domain decisions
- L5 reads signals before execution
- No implicit governance influence

Violations Resolved: VIOLATION-004, VIOLATION-005
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

# Import shared Base from costsim_cb to ensure single metadata
from app.models.costsim_cb import Base


class GovernanceSignal(Base):
    """
    Governance signal record - explicit persistence of L7 decisions.

    Phase E: Governance influence must be visible data, not invisible pressure.
    L7 (BLCA, CI) writes signals here. L4/L5 reads before proceeding.
    """

    __tablename__ = "governance_signals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Signal type: what kind of governance decision
    signal_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: BLCA_STATUS, CI_STATUS, DEPLOYMENT_GATE, SESSION_BLOCK"
    )

    # Scope: what this signal applies to
    scope = Column(
        String(500),
        nullable=False,
        index=True,
        comment="Scope identifier: file path, PR number, commit SHA, session ID, etc."
    )

    # Decision: the governance verdict
    decision = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Decision: CLEAN, BLOCKED, WARN, PENDING"
    )

    # Reason: human-readable explanation
    reason = Column(
        Text,
        nullable=True,
        comment="Why this decision was made"
    )

    # Constraints: structured details about what's blocked
    constraints = Column(
        JSONB,
        nullable=True,
        comment="Structured constraints: {blocked_files: [...], blocked_actions: [...]}"
    )

    # Source: who/what generated this signal
    recorded_by = Column(
        String(100),
        nullable=False,
        comment="Source: BLCA, CI, OPS, MANUAL"
    )

    # Timestamps
    recorded_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="When this signal was recorded"
    )

    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Optional expiration (for temporary blocks)"
    )

    # Superseded tracking: when a newer signal replaces this one
    superseded_by = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="ID of signal that superseded this one"
    )

    superseded_at = Column(
        DateTime,
        nullable=True,
        comment="When this signal was superseded"
    )

    # Phase E FIX-04: Semantic ownership
    semantic_owner = Column(
        String(100),
        nullable=True,
        comment="L4 engine with interpretation authority (FIX-04)"
    )

    # Composite index for efficient lookups
    __table_args__ = (
        Index('ix_governance_signals_scope_type_active', 'scope', 'signal_type', 'decision'),
        {"comment": "Phase E FIX-03: Explicit governance signals from L7 to L6"}
    )


# Pydantic models for API/Service use

class GovernanceSignalCreate(BaseModel):
    """Input model for creating governance signals."""

    signal_type: str  # BLCA_STATUS, CI_STATUS, DEPLOYMENT_GATE
    scope: str  # file path, PR number, session ID
    decision: str  # CLEAN, BLOCKED, WARN, PENDING
    reason: Optional[str] = None
    constraints: Optional[dict] = None
    recorded_by: str  # BLCA, CI, OPS
    expires_at: Optional[datetime] = None


class GovernanceSignalResponse(BaseModel):
    """Output model for governance signals."""

    id: UUID
    signal_type: str
    scope: str
    decision: str
    reason: Optional[str]
    constraints: Optional[dict]
    recorded_by: str
    recorded_at: datetime
    expires_at: Optional[datetime]
    superseded_by: Optional[UUID]
    superseded_at: Optional[datetime]

    class Config:
        from_attributes = True


class GovernanceSignalQuery(BaseModel):
    """Query model for checking governance status."""

    scope: str
    signal_type: Optional[str] = None


class GovernanceCheckResult(BaseModel):
    """Result of checking governance status for a scope."""

    scope: str
    is_blocked: bool
    blocking_signals: list[GovernanceSignalResponse]
    warning_signals: list[GovernanceSignalResponse]
    last_checked: datetime
