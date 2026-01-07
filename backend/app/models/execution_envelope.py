# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Execution envelope models for implicit authority hardening
# Callers: auth/execution_envelope.py, worker/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-330

"""
Execution Envelope Database Models - PIN-330 Implicit Authority Hardening

Provides append-only storage for execution envelopes.

CONSTRAINTS:
- Records are immutable once created
- No UPDATE or DELETE operations allowed
- Failure to write MUST NOT block execution
"""

from typing import Any, Dict

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Float,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.models.costsim_cb import Base


class ExecutionEnvelopeModel(Base):
    """
    Execution envelope for implicit authority hardening.

    INVARIANTS:
    - Records are immutable (no UPDATE/DELETE)
    - Append-only storage
    - Failure to write does NOT block execution
    """

    __tablename__ = "execution_envelopes"

    # Primary key (auto-increment for ordering)
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Core identity
    envelope_id = Column(Text, nullable=False, unique=True, index=True)
    capability_id = Column(Text, nullable=False, index=True)  # CAP-020, CAP-021, SUB-019
    execution_vector = Column(Text, nullable=False, index=True)  # CLI, SDK, AUTO_EXEC

    # Caller identity
    caller_type = Column(Text, nullable=False)  # human, service, system
    caller_subject = Column(Text, nullable=False, index=True)
    impersonated_subject = Column(Text, nullable=True)
    impersonation_declared = Column(Boolean, nullable=False, default=False)

    # Tenant context
    tenant_id = Column(Text, nullable=False, index=True)
    account_id = Column(Text, nullable=True)
    project_id = Column(Text, nullable=True)

    # Invocation tracking
    invocation_id = Column(Text, nullable=False, index=True)
    invocation_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    sequence_number = Column(Integer, nullable=True)

    # Plan integrity
    input_hash = Column(Text, nullable=False)
    resolved_plan_hash = Column(Text, nullable=False)
    plan_mutation_detected = Column(Boolean, nullable=False, default=False)
    original_invocation_id = Column(Text, nullable=True)

    # Confidence (for SUB-019)
    confidence_score = Column(Float, nullable=True)
    confidence_threshold = Column(Float, nullable=True)
    auto_execute_triggered = Column(Boolean, nullable=True)

    # Attribution
    attribution_origin = Column(Text, nullable=False, default="PIN-330")
    reason_code = Column(Text, nullable=True)
    source_command = Column(Text, nullable=True)
    sdk_version = Column(Text, nullable=True)
    cli_version = Column(Text, nullable=True)

    # Evidence metadata
    emitted_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    emission_success = Column(Boolean, nullable=False, default=True)

    # Full envelope JSON (for future-proofing)
    envelope_json = Column(JSONB, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_exec_envelope_capability_tenant", "capability_id", "tenant_id"),
        Index("ix_exec_envelope_vector_tenant", "execution_vector", "tenant_id"),
        Index("ix_exec_envelope_emitted_at", "emitted_at"),
        Index("ix_exec_envelope_mutation", "plan_mutation_detected", "tenant_id"),
        Index("ix_exec_envelope_auto_exec", "auto_execute_triggered", "tenant_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "envelope_id": self.envelope_id,
            "capability_id": self.capability_id,
            "execution_vector": self.execution_vector,
            "caller_identity": {
                "type": self.caller_type,
                "subject": self.caller_subject,
                "impersonated_subject": self.impersonated_subject,
                "impersonation_declared": self.impersonation_declared,
            },
            "tenant_context": {
                "tenant_id": self.tenant_id,
                "account_id": self.account_id,
                "project_id": self.project_id,
            },
            "invocation": {
                "invocation_id": self.invocation_id,
                "timestamp": (
                    self.invocation_timestamp.isoformat()
                    if self.invocation_timestamp
                    else None
                ),
                "sequence_number": self.sequence_number,
            },
            "plan": {
                "input_hash": self.input_hash,
                "resolved_plan_hash": self.resolved_plan_hash,
                "plan_mutation_detected": self.plan_mutation_detected,
                "original_invocation_id": self.original_invocation_id,
            },
            "confidence": (
                {
                    "score": self.confidence_score,
                    "threshold_used": self.confidence_threshold,
                    "auto_execute_triggered": self.auto_execute_triggered,
                }
                if self.confidence_score is not None
                else None
            ),
            "attribution": {
                "origin": self.attribution_origin,
                "reason_code": self.reason_code,
                "source_command": self.source_command,
                "sdk_version": self.sdk_version,
                "cli_version": self.cli_version,
            },
            "evidence": {
                "emitted_at": (
                    self.emitted_at.isoformat() if self.emitted_at else None
                ),
                "emission_success": self.emission_success,
            },
        }


# =============================================================================
# SUMMARY STATISTICS MODEL (OPTIONAL)
# =============================================================================


class ExecutionEnvelopeStats(Base):
    """
    Aggregate statistics for execution envelopes.

    Used for quick dashboards without scanning full table.
    Updated asynchronously (eventual consistency acceptable).
    """

    __tablename__ = "execution_envelope_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    capability_id = Column(Text, nullable=False, index=True)
    execution_vector = Column(Text, nullable=False)
    tenant_id = Column(Text, nullable=False, index=True)
    period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False)

    # Counts
    total_envelopes = Column(Integer, nullable=False, default=0)
    impersonation_count = Column(Integer, nullable=False, default=0)
    mutation_count = Column(Integer, nullable=False, default=0)
    auto_execute_count = Column(Integer, nullable=False, default=0)

    # Updated timestamp
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_exec_stats_cap_tenant_period",
            "capability_id",
            "tenant_id",
            "period_start",
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "capability_id": self.capability_id,
            "execution_vector": self.execution_vector,
            "tenant_id": self.tenant_id,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_envelopes": self.total_envelopes,
            "impersonation_count": self.impersonation_count,
            "mutation_count": self.mutation_count,
            "auto_execute_count": self.auto_execute_count,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
