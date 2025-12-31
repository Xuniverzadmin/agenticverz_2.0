# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: CostSim circuit breaker models
# Callers: costsim/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: CostSim

# CostSim Circuit Breaker Models (Async SQLAlchemy)
"""
Pure SQLAlchemy models for async database access.

These models are used with AsyncSession for non-blocking DB operations.
They mirror the SQLModel definitions in db.py but are designed for
async use with SQLAlchemy 2.0+.
"""

import json
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
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CostSimCBStateModel(Base):
    """
    Circuit breaker state for CostSim V2.

    Single row per circuit breaker (name is unique key).
    Uses SELECT FOR UPDATE for atomic state transitions.
    """

    __tablename__ = "costsim_cb_state"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    disabled = Column(Boolean, nullable=False, default=False)
    disabled_by = Column(Text, nullable=True)
    disabled_reason = Column(Text, nullable=True)
    disabled_until = Column(TIMESTAMP(timezone=True), nullable=True)
    incident_id = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    last_failure_at = Column(TIMESTAMP(timezone=True), nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "disabled": self.disabled,
            "disabled_by": self.disabled_by,
            "disabled_reason": self.disabled_reason,
            "disabled_until": self.disabled_until.isoformat() if self.disabled_until else None,
            "incident_id": self.incident_id,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CostSimCBIncidentModel(Base):
    """
    Incident records for circuit breaker trips.

    Provides audit trail for all circuit breaker events.
    """

    __tablename__ = "costsim_cb_incidents"

    id = Column(Text, primary_key=True)
    circuit_breaker_name = Column(Text, nullable=False, index=True)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    reason = Column(Text, nullable=False)
    severity = Column(Text, nullable=False)  # P1, P2, P3
    drift_score = Column(Float, nullable=True)
    sample_count = Column(Integer, nullable=True)
    details_json = Column(Text, nullable=True)

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    resolved_by = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Alert tracking
    alert_sent = Column(Boolean, nullable=False, default=False)
    alert_sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    alert_response = Column(Text, nullable=True)

    def get_details(self) -> Dict[str, Any]:
        """Parse details JSON."""
        if self.details_json:
            return json.loads(self.details_json)
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "circuit_breaker_name": self.circuit_breaker_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "reason": self.reason,
            "severity": self.severity,
            "drift_score": self.drift_score,
            "sample_count": self.sample_count,
            "details": self.get_details(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "alert_sent": self.alert_sent,
            "alert_sent_at": self.alert_sent_at.isoformat() if self.alert_sent_at else None,
        }


class CostSimProvenanceModel(Base):
    """
    Provenance records for CostSim simulations.

    Stores V1 and V2 costs for divergence analysis.
    """

    __tablename__ = "costsim_provenance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(Text, nullable=True, index=True)
    tenant_id = Column(Text, nullable=True, index=True)
    variant_slug = Column(Text, nullable=True, index=True)  # v1, v2, canary
    source = Column(Text, nullable=True)  # sandbox, canary, manual

    # Version tracking
    model_version = Column(Text, nullable=True)
    adapter_version = Column(Text, nullable=True)
    commit_sha = Column(Text, nullable=True)

    # Hashes for deduplication
    input_hash = Column(Text, nullable=True, index=True)
    output_hash = Column(Text, nullable=True)

    # Cost data (nullable for error cases)
    v1_cost = Column(Float, nullable=True)
    v2_cost = Column(Float, nullable=True)
    cost_delta = Column(Float, nullable=True)

    # Full payload (compressed JSON)
    payload = Column(JSONB, nullable=True)

    # Timing
    runtime_ms = Column(Integer, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    __table_args__ = (
        Index("idx_costsim_prov_run", "run_id"),
        Index("idx_costsim_prov_variant", "variant_slug"),
        Index("idx_costsim_prov_input_hash", "input_hash"),
        Index("idx_costsim_prov_tenant_created", "tenant_id", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "variant_slug": self.variant_slug,
            "source": self.source,
            "model_version": self.model_version,
            "adapter_version": self.adapter_version,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "v1_cost": self.v1_cost,
            "v2_cost": self.v2_cost,
            "cost_delta": self.cost_delta,
            "runtime_ms": self.runtime_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CostSimCanaryReportModel(Base):
    """
    Canary run reports for CostSim V2 validation.

    Stores results from daily canary runs for audit and trend analysis.
    """

    __tablename__ = "costsim_canary_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(Text, nullable=False, unique=True, index=True)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    status = Column(Text, nullable=False)  # pass, fail, error, skipped

    # Sample stats
    total_samples = Column(Integer, nullable=False, default=0)
    matching_samples = Column(Integer, nullable=False, default=0)
    minor_drift_samples = Column(Integer, nullable=False, default=0)
    major_drift_samples = Column(Integer, nullable=False, default=0)

    # Metrics
    median_cost_diff = Column(Float, nullable=True)
    p90_cost_diff = Column(Float, nullable=True)
    kl_divergence = Column(Float, nullable=True)
    outlier_count = Column(Integer, nullable=True)

    # Verdict
    passed = Column(Boolean, nullable=False, default=True)
    failure_reasons_json = Column(Text, nullable=True)

    # Artifacts and golden comparison
    artifact_paths_json = Column(Text, nullable=True)
    golden_comparison_json = Column(Text, nullable=True)

    # Metadata
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_costsim_canary_status", "status"),
        Index("idx_costsim_canary_passed", "passed"),
    )

    def get_failure_reasons(self) -> list:
        """Parse failure reasons JSON."""
        if self.failure_reasons_json:
            return json.loads(self.failure_reasons_json)
        return []

    def get_artifact_paths(self) -> list:
        """Parse artifact paths JSON."""
        if self.artifact_paths_json:
            return json.loads(self.artifact_paths_json)
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "status": self.status,
            "total_samples": self.total_samples,
            "matching_samples": self.matching_samples,
            "minor_drift_samples": self.minor_drift_samples,
            "major_drift_samples": self.major_drift_samples,
            "median_cost_diff": self.median_cost_diff,
            "p90_cost_diff": self.p90_cost_diff,
            "kl_divergence": self.kl_divergence,
            "outlier_count": self.outlier_count,
            "passed": self.passed,
            "failure_reasons": self.get_failure_reasons(),
            "artifact_paths": self.get_artifact_paths(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CostSimAlertQueueModel(Base):
    """
    Alert queue for reliable alert delivery.

    Failed alerts are retried with exponential backoff.
    """

    __tablename__ = "costsim_alert_queue"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payload = Column(JSONB, nullable=False)
    alert_type = Column(Text, nullable=True)  # disable, enable, canary_fail
    circuit_breaker_name = Column(Text, nullable=True)
    incident_id = Column(Text, nullable=True)

    # Retry tracking
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=10)
    last_attempt_at = Column(TIMESTAMP(timezone=True), nullable=True)
    next_attempt_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    last_error = Column(Text, nullable=True)

    # Status
    status = Column(Text, nullable=False, default="pending")  # pending, sent, failed

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_costsim_alert_queue_next", "next_attempt_at"),
        Index("idx_costsim_alert_queue_status", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "circuit_breaker_name": self.circuit_breaker_name,
            "incident_id": self.incident_id,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "last_error": self.last_error,
            "next_attempt_at": self.next_attempt_at.isoformat() if self.next_attempt_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
