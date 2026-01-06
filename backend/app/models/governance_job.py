# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Governance Job database models
# Callers: governance/*, L4 domain services
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

"""
Governance Job Models (Part-2 CRM Workflow)

Models for persisting Governance Jobs - the execution tracking component
of the Part-2 governance workflow.

Job Properties:
- DERIVED FROM CONTRACT: Jobs are created only from activated contracts
- STEP-ORDERED: Jobs execute steps in sequence
- OBSERVABLE: State changes are recorded for audit
- NO AUTHORITY: Jobs track execution, they don't decide outcomes

Invariants:
- JOB-001: Jobs require contract_id (no orphan jobs)
- JOB-002: Job steps execute in order
- JOB-003: Terminal states are immutable
- JOB-004: Evidence is recorded per step
- JOB-005: Health snapshots are read-only (captured, not created)

Reference: PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# Import shared Base from costsim_cb to ensure single metadata
from app.models.costsim_cb import Base

# ==============================================================================
# JOB STATUS ENUM (Closed Set)
# ==============================================================================


class JobStatus(str, Enum):
    """
    Governance Job lifecycle states.

    Reference: PART2_CRM_WORKFLOW_CHARTER.md Step 7
    """

    PENDING = "PENDING"  # Job created, not yet started
    RUNNING = "RUNNING"  # Steps executing
    COMPLETED = "COMPLETED"  # All steps succeeded (terminal)
    FAILED = "FAILED"  # Step failed or timeout (terminal)
    CANCELLED = "CANCELLED"  # Manually cancelled (terminal)


# Terminal states - no further transitions allowed
JOB_TERMINAL_STATES = frozenset(
    {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }
)


# ==============================================================================
# STEP STATUS ENUM
# ==============================================================================


class StepStatus(str, Enum):
    """Status of a single job step."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ==============================================================================
# GOVERNANCE JOB DATABASE MODEL (L6)
# ==============================================================================


class GovernanceJob(Base):
    """
    Governance Job database model.

    A Governance Job is created when a contract is activated.
    It tracks execution progress and captures evidence.

    Reference: PART2_CRM_WORKFLOW_CHARTER.md Step 7
    """

    __tablename__ = "governance_jobs"

    # Primary key
    job_id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Origin (JOB-001: Jobs require contract_id)
    contract_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        unique=True,  # One job per contract
        index=True,
        comment="FK to system_contracts (one job per contract)",
    )

    # State
    status = Column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING.value,
        index=True,
        comment="Job lifecycle status",
    )
    status_reason = Column(
        Text,
        nullable=True,
        comment="Human-readable status reason",
    )

    # Execution plan (derived from contract)
    steps = Column(
        JSONB,
        nullable=False,
        default=[],
        comment="Ordered list of execution steps",
    )
    current_step_index = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Index of currently executing step",
    )
    total_steps = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of steps",
    )

    # Evidence (JOB-004: Evidence is recorded per step)
    step_results = Column(
        JSONB,
        nullable=False,
        default=[],
        comment="Results from each completed step",
    )
    execution_evidence = Column(
        JSONB,
        nullable=True,
        comment="Aggregated evidence for audit",
    )

    # Health snapshots (JOB-005: Read-only captures)
    health_snapshot_before = Column(
        JSONB,
        nullable=True,
        comment="Health state before execution",
    )
    health_snapshot_after = Column(
        JSONB,
        nullable=True,
        comment="Health state after execution",
    )

    # Timing
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    started_at = Column(
        DateTime,
        nullable=True,
        comment="When RUNNING began",
    )
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="When terminal state reached",
    )
    timeout_at = Column(
        DateTime,
        nullable=True,
        comment="When job should timeout",
    )

    # Metadata
    created_by = Column(
        String(100),
        nullable=False,
        default="system",
        comment="Who created this job",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_jobs_status_created", "status", "created_at"),
        Index("ix_jobs_timeout", "status", "timeout_at"),
        {"comment": "Part-2 Governance Jobs - contract execution tracking"},
    )


# ==============================================================================
# PYDANTIC MODELS FOR API/SERVICE USE
# ==============================================================================


class JobStep(BaseModel):
    """
    Single step in a governance job.

    Steps are derived from contract proposed_changes.
    """

    step_index: int
    step_type: str  # capability_enable, capability_disable, etc.
    target: str  # Capability name or scope
    parameters: dict[str, Any]
    timeout_seconds: int = Field(default=300)


class StepResult(BaseModel):
    """
    Result of executing a single step.

    Captured for audit trail.
    """

    step_index: int
    status: StepStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output: Optional[dict[str, Any]]
    error: Optional[str]
    health_after: Optional[dict[str, Any]]


class HealthSnapshot(BaseModel):
    """
    Point-in-time health state capture.

    JOB-005: These are read-only observations.
    """

    captured_at: datetime
    capabilities: dict[str, dict[str, Any]]  # capability_name -> health state
    system_health: dict[str, Any]


class JobCreate(BaseModel):
    """Input model for creating a job from activated contract."""

    contract_id: UUID
    steps: list[JobStep]
    timeout_minutes: int = Field(default=60, ge=1, le=1440)
    created_by: str = "system"


class JobResponse(BaseModel):
    """Output model for job data."""

    job_id: UUID
    contract_id: UUID
    status: str
    status_reason: Optional[str]
    steps: list[dict[str, Any]]
    current_step_index: int
    total_steps: int
    step_results: list[dict[str, Any]]
    execution_evidence: Optional[dict[str, Any]]
    health_snapshot_before: Optional[dict[str, Any]]
    health_snapshot_after: Optional[dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    timeout_at: Optional[datetime]
    created_by: str

    class Config:
        from_attributes = True


class JobTransitionRecord(BaseModel):
    """Record of a job state transition."""

    from_status: str
    to_status: str
    step_index: Optional[int]
    reason: str
    transitioned_by: str
    transitioned_at: datetime


# ==============================================================================
# JOB STATE TRANSITIONS
# ==============================================================================

# Valid state transitions (JOB-003: Terminal states are immutable)
JOB_VALID_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.PENDING: frozenset(
        {
            JobStatus.RUNNING,
            JobStatus.CANCELLED,
        }
    ),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }
    ),
    # Terminal states have no valid transitions
    JobStatus.COMPLETED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
}


# ==============================================================================
# JOB ERRORS
# ==============================================================================


class InvalidJobTransitionError(Exception):
    """Raised when an invalid job state transition is attempted."""

    def __init__(
        self,
        from_status: JobStatus,
        to_status: JobStatus,
        reason: str,
    ):
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        super().__init__(f"Invalid job transition from {from_status.value} to {to_status.value}: {reason}")


class JobImmutableError(Exception):
    """Raised when attempting to modify an immutable job."""

    def __init__(self, job_id: UUID, status: JobStatus):
        self.job_id = job_id
        self.status = status
        super().__init__(f"Job {job_id} is in terminal state {status.value} and cannot be modified")


class OrphanJobError(Exception):
    """Raised when attempting to create a job without a contract."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Cannot create orphan job: {reason}")
