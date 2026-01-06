# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: System Contract database models
# Callers: governance/*, L4 domain services
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1

"""
System Contract Models (Part-2 CRM Workflow)

Models for persisting System Contracts - the first stateful component
of the Part-2 governance workflow.

Contract Properties:
- STATE MACHINE: Explicit state transitions with invariants
- IMMUTABLE POST-APPROVED: Terminal and approved states cannot revert
- AUDIT ANCHORED: Every transition is traceable
- GOVERNANCE BOUND: Created only via validated proposals

Invariants:
- CONTRACT-001: Status transitions must follow state machine
- CONTRACT-002: APPROVED requires approved_by
- CONTRACT-003: ACTIVE requires job exists
- CONTRACT-004: COMPLETED requires audit_verdict = PASS
- CONTRACT-005: Terminal states are immutable
- CONTRACT-006: proposed_changes must validate schema
- CONTRACT-007: confidence_score range [0,1]

Reference: SYSTEM_CONTRACT_OBJECT.md, PIN-291, part2-design-v1
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    DECIMAL,
    Column,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# Import shared Base from costsim_cb to ensure single metadata
from app.models.costsim_cb import Base

# ==============================================================================
# CONTRACT STATUS ENUM (Closed Set)
# ==============================================================================


class ContractStatus(str, Enum):
    """
    System Contract lifecycle states.

    Reference: SYSTEM_CONTRACT_OBJECT.md Contract Lifecycle States
    """

    DRAFT = "DRAFT"  # Initial: Issue passes filter
    VALIDATED = "VALIDATED"  # Validator verdict recorded
    ELIGIBLE = "ELIGIBLE"  # Eligibility verdict = MAY
    APPROVED = "APPROVED"  # Founder approved
    ACTIVE = "ACTIVE"  # Activation window started
    COMPLETED = "COMPLETED"  # Job succeeded + audit passed (terminal)
    FAILED = "FAILED"  # Job failed OR audit failed (terminal)
    REJECTED = "REJECTED"  # Any gate rejected (terminal)
    EXPIRED = "EXPIRED"  # TTL exceeded (terminal)


# Terminal states - no further transitions allowed
TERMINAL_STATES = frozenset(
    {
        ContractStatus.COMPLETED,
        ContractStatus.FAILED,
        ContractStatus.REJECTED,
        ContractStatus.EXPIRED,
    }
)


# ==============================================================================
# AUDIT VERDICT ENUM
# ==============================================================================


class AuditVerdict(str, Enum):
    """Audit verification verdict."""

    PENDING = "PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


# ==============================================================================
# RISK LEVEL ENUM
# ==============================================================================


class RiskLevel(str, Enum):
    """Risk level classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ==============================================================================
# PROPOSED CHANGE TYPE ENUM
# ==============================================================================


class ProposedChangeType(str, Enum):
    """Types of proposed changes in a contract."""

    CAPABILITY_ENABLE = "capability_enable"
    CAPABILITY_DISABLE = "capability_disable"
    CONFIGURATION_UPDATE = "configuration_update"
    PARAMETER_CHANGE = "parameter_change"


# ==============================================================================
# SOURCE ENUM
# ==============================================================================


class ContractSource(str, Enum):
    """Issue source classification."""

    CRM_FEEDBACK = "crm_feedback"
    SUPPORT_TICKET = "support_ticket"
    OPS_ALERT = "ops_alert"
    MANUAL = "manual"


# ==============================================================================
# STATE TRANSITION DEFINITIONS
# ==============================================================================

# Valid state transitions
# CONTRACT-001: Status transitions must follow state machine
VALID_TRANSITIONS: dict[ContractStatus, frozenset[ContractStatus]] = {
    ContractStatus.DRAFT: frozenset(
        {
            ContractStatus.VALIDATED,
            ContractStatus.EXPIRED,
            ContractStatus.REJECTED,
        }
    ),
    ContractStatus.VALIDATED: frozenset(
        {
            ContractStatus.ELIGIBLE,
            ContractStatus.REJECTED,
            ContractStatus.EXPIRED,
        }
    ),
    ContractStatus.ELIGIBLE: frozenset(
        {
            ContractStatus.APPROVED,
            ContractStatus.REJECTED,
            ContractStatus.EXPIRED,
        }
    ),
    ContractStatus.APPROVED: frozenset(
        {
            ContractStatus.ACTIVE,
            ContractStatus.FAILED,
        }
    ),
    ContractStatus.ACTIVE: frozenset(
        {
            ContractStatus.COMPLETED,
            ContractStatus.FAILED,
        }
    ),
    # Terminal states have no valid transitions
    ContractStatus.COMPLETED: frozenset(),
    ContractStatus.FAILED: frozenset(),
    ContractStatus.REJECTED: frozenset(),
    ContractStatus.EXPIRED: frozenset(),
}


# ==============================================================================
# SYSTEM CONTRACT DATABASE MODEL (L6)
# ==============================================================================


class SystemContract(Base):
    """
    System Contract database model.

    A System Contract is a formal, machine-enforced agreement between
    human intent and governance authority.

    Reference: SYSTEM_CONTRACT_OBJECT.md Contract Schema
    """

    __tablename__ = "system_contracts"

    # Primary key with optimistic locking
    contract_id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    version = Column(
        DECIMAL(precision=10, scale=0),
        nullable=False,
        default=1,
        comment="Optimistic lock version",
    )

    # Origin
    issue_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK to issue_events",
    )
    source = Column(
        String(50),
        nullable=False,
        index=True,
        comment="crm_feedback, support_ticket, ops_alert, manual",
    )

    # State
    status = Column(
        String(20),
        nullable=False,
        default=ContractStatus.DRAFT.value,
        index=True,
        comment="Contract lifecycle status",
    )
    status_reason = Column(
        Text,
        nullable=True,
        comment="Human-readable status reason",
    )

    # Content
    title = Column(
        String(200),
        nullable=False,
        comment="Contract title (max 200 chars)",
    )
    description = Column(
        String(4000),
        nullable=True,
        comment="Contract description (max 4000 chars)",
    )
    proposed_changes = Column(
        JSONB,
        nullable=False,
        comment="Schema-validated proposed changes",
    )
    affected_capabilities = Column(
        ARRAY(String),
        nullable=False,
        default=[],
        comment="List of affected capability names",
    )
    risk_level = Column(
        String(20),
        nullable=False,
        default=RiskLevel.LOW.value,
        comment="critical, high, medium, low",
    )

    # Validation
    validator_verdict = Column(
        JSONB,
        nullable=True,
        comment="Validator verdict (nullable until validated)",
    )
    eligibility_verdict = Column(
        JSONB,
        nullable=True,
        comment="Eligibility verdict (nullable until eligible)",
    )
    confidence_score = Column(
        DECIMAL(precision=3, scale=2),
        nullable=True,
        comment="Confidence score 0.00-1.00 (CONTRACT-007)",
    )

    # Authorization
    created_by = Column(
        String(100),
        nullable=False,
        comment="system or user_id",
    )
    approved_by = Column(
        String(100),
        nullable=True,
        comment="Approver ID (nullable until approved)",
    )
    approved_at = Column(
        DateTime,
        nullable=True,
        comment="Approval timestamp",
    )

    # Execution
    activation_window_start = Column(
        DateTime,
        nullable=True,
        comment="When activation window begins",
    )
    activation_window_end = Column(
        DateTime,
        nullable=True,
        comment="When activation window ends",
    )
    execution_constraints = Column(
        JSONB,
        nullable=True,
        comment="Rate limits, scope limits, etc.",
    )
    job_id = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="FK to governance_jobs",
    )

    # Audit
    audit_verdict = Column(
        String(20),
        nullable=False,
        default=AuditVerdict.PENDING.value,
        comment="PENDING, PASS, FAIL, INCONCLUSIVE",
    )
    audit_reason = Column(
        Text,
        nullable=True,
        comment="Audit verdict reason",
    )
    audit_completed_at = Column(
        DateTime,
        nullable=True,
        comment="When audit completed",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="TTL for DRAFT contracts",
    )

    # State transition history (for audit)
    transition_history = Column(
        JSONB,
        nullable=False,
        default=[],
        comment="Array of state transitions",
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_contracts_status_expires", "status", "expires_at"),
        Index("ix_contracts_capabilities", affected_capabilities, postgresql_using="gin"),
        Index("ix_contracts_approved", "approved_by", "approved_at"),
        Index("ix_contracts_audit", "audit_verdict", "audit_completed_at"),
        {"comment": "Part-2 System Contracts - governed change requests"},
    )


# ==============================================================================
# PYDANTIC MODELS FOR API/SERVICE USE
# ==============================================================================


class ProposedChangeBase(BaseModel):
    """Base schema for proposed changes."""

    type: ProposedChangeType


class CapabilityEnableChange(ProposedChangeBase):
    """Enable a capability."""

    type: ProposedChangeType = ProposedChangeType.CAPABILITY_ENABLE
    capability_name: str
    target_lifecycle: str  # PREVIEW, LAUNCHED, DEPRECATED


class CapabilityDisableChange(ProposedChangeBase):
    """Disable a capability."""

    type: ProposedChangeType = ProposedChangeType.CAPABILITY_DISABLE
    capability_name: str
    reason: str


class ConfigurationUpdateChange(ProposedChangeBase):
    """Update configuration."""

    type: ProposedChangeType = ProposedChangeType.CONFIGURATION_UPDATE
    scope: str  # SYSTEM or capability_name
    key: str
    old_value: Any
    new_value: Any


class ParameterChangeChange(ProposedChangeBase):
    """Change parameters."""

    type: ProposedChangeType = ProposedChangeType.PARAMETER_CHANGE
    scope: str  # SYSTEM or capability_name
    parameters: dict[str, Any]


class ValidatorVerdictData(BaseModel):
    """Stored validator verdict data."""

    issue_type: str
    severity: str
    affected_capabilities: list[str]
    recommended_action: str
    confidence_score: Decimal
    reason: str
    analyzed_at: datetime
    validator_version: str


class EligibilityVerdictData(BaseModel):
    """Stored eligibility verdict data."""

    decision: str  # MAY or MAY_NOT
    reason: str
    blocking_signals: list[str]
    missing_prerequisites: list[str]
    evaluated_at: datetime
    rules_version: str


class TransitionRecord(BaseModel):
    """Record of a state transition."""

    from_status: str
    to_status: str
    reason: str
    transitioned_by: str
    transitioned_at: datetime


class ContractCreate(BaseModel):
    """Input model for creating a contract from validated proposal."""

    issue_id: UUID
    source: ContractSource
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    proposed_changes: dict[str, Any]
    affected_capabilities: list[str]
    risk_level: RiskLevel
    validator_verdict: ValidatorVerdictData
    eligibility_verdict: EligibilityVerdictData
    confidence_score: Decimal
    created_by: str
    expires_at: Optional[datetime] = None

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: Decimal) -> Decimal:
        """CONTRACT-007: confidence_score range [0,1]."""
        if v < 0 or v > 1:
            raise ValueError("confidence_score must be between 0 and 1")
        return v


class ContractResponse(BaseModel):
    """Output model for contract data."""

    contract_id: UUID
    version: int
    issue_id: UUID
    source: str
    status: str
    status_reason: Optional[str]
    title: str
    description: Optional[str]
    proposed_changes: dict[str, Any]
    affected_capabilities: list[str]
    risk_level: str
    validator_verdict: Optional[dict[str, Any]]
    eligibility_verdict: Optional[dict[str, Any]]
    confidence_score: Optional[Decimal]
    created_by: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    activation_window_start: Optional[datetime]
    activation_window_end: Optional[datetime]
    execution_constraints: Optional[dict[str, Any]]
    job_id: Optional[UUID]
    audit_verdict: str
    audit_reason: Optional[str]
    audit_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    transition_history: list[dict[str, Any]]

    class Config:
        from_attributes = True


class ContractApproval(BaseModel):
    """Input model for founder approval."""

    approved_by: str
    activation_window_hours: int = Field(default=24, ge=1, le=168)
    execution_constraints: Optional[dict[str, Any]] = None


class ContractRejection(BaseModel):
    """Input model for rejection."""

    rejected_by: str
    reason: str


# ==============================================================================
# STATE TRANSITION ERROR
# ==============================================================================


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        from_status: ContractStatus,
        to_status: ContractStatus,
        reason: str,
    ):
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        super().__init__(f"Invalid transition from {from_status.value} to {to_status.value}: {reason}")


class ContractImmutableError(Exception):
    """Raised when attempting to modify an immutable contract."""

    def __init__(self, contract_id: UUID, status: ContractStatus):
        self.contract_id = contract_id
        self.status = status
        super().__init__(f"Contract {contract_id} is in terminal state {status.value} and cannot be modified")


class MayNotVerdictError(Exception):
    """
    Raised when attempting to create a contract with MAY_NOT verdict.

    This error is mechanically un-overridable per governance rule.
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Cannot create contract: eligibility verdict is MAY_NOT. Reason: {reason}")
