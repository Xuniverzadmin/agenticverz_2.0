# capability_id: CAP-012
# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Consumers: logs, incidents
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Runtime Audit Contract (RAC) models - pure Pydantic/dataclass DTOs
# Callers: L4 drivers (transaction_coordinator), L5 engines (audit_store, reconciler)
# Allowed Imports: None (foundational schema)
# Forbidden Imports: L1, L2, L3, L4, L6, sqlalchemy
# Reference: PIN-470, PIN-454 (Cross-Domain Orchestration Audit)
# NOTE: Migrated from legacy audit models (2026-01-25)

"""
Runtime Audit Contract (RAC) Models

These models define the data structures for the audit system:

- AuditExpectation: Declares what action MUST happen for a run
- DomainAck: Reports that an action has completed
- ReconciliationResult: Result of comparing expectations vs acks

Design Principles:
1. Immutable after creation (expectations are contracts)
2. UUID-based for correlation across domains
3. Serializable for Redis storage
4. Type-safe with enums for domains and actions
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4


class AuditStatus(str, Enum):
    """Status of an audit expectation."""

    PENDING = "PENDING"  # Expectation created, not yet acked
    ACKED = "ACKED"  # Acknowledgment received
    MISSING = "MISSING"  # Deadline passed, no ack received
    FAILED = "FAILED"  # Ack received with error


class AuditDomain(str, Enum):
    """Domains that participate in the audit contract."""

    INCIDENTS = "incidents"  # Incident creation
    POLICIES = "policies"  # Policy evaluation
    LOGS = "logs"  # Trace/log recording
    ORCHESTRATOR = "orchestrator"  # ROK lifecycle (finalize_run)


class AuditAction(str, Enum):
    """Actions that can be expected/acked."""

    # Incident domain
    CREATE_INCIDENT = "create_incident"

    # Policy domain
    EVALUATE_POLICY = "evaluate_policy"

    # Logs domain
    START_TRACE = "start_trace"
    COMPLETE_TRACE = "complete_trace"

    # Orchestrator domain (meta-actions)
    FINALIZE_RUN = "finalize_run"


@dataclass
class AuditExpectation:
    """
    An expectation that an action MUST happen for a run.

    Created at run start (T0) by ROK, one per expected domain action.
    The finalize_run expectation is the liveness guarantee.

    Attributes:
        id: Unique expectation ID
        run_id: The run this expectation belongs to
        domain: Which domain should perform the action
        action: What action is expected
        status: Current status (PENDING -> ACKED | MISSING | FAILED)
        deadline_ms: Time allowed for ack (from creation)
        created_at: When this expectation was created
        acked_at: When the ack was received (if any)
        metadata: Additional context (e.g., expected result type)
    """

    run_id: UUID
    domain: AuditDomain
    action: AuditAction
    deadline_ms: int = 5000  # 5 seconds default
    id: UUID = field(default_factory=uuid4)
    status: AuditStatus = AuditStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acked_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "domain": self.domain.value,
            "action": self.action.value,
            "status": self.status.value,
            "deadline_ms": self.deadline_ms,
            "created_at": self.created_at.isoformat(),
            "acked_at": self.acked_at.isoformat() if self.acked_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditExpectation":
        """Deserialize from storage."""
        return cls(
            id=UUID(data["id"]),
            run_id=UUID(data["run_id"]),
            domain=AuditDomain(data["domain"]),
            action=AuditAction(data["action"]),
            status=AuditStatus(data["status"]),
            deadline_ms=data["deadline_ms"],
            created_at=datetime.fromisoformat(data["created_at"]),
            acked_at=datetime.fromisoformat(data["acked_at"]) if data.get("acked_at") else None,
            metadata=data.get("metadata", {}),
        )

    def key(self) -> Tuple[str, str]:
        """Return (domain, action) tuple for set operations."""
        return (self.domain.value, self.action.value)


class AckStatus(str, Enum):
    """Status of a domain acknowledgment."""

    SUCCESS = "SUCCESS"  # Action completed successfully
    FAILED = "FAILED"  # Action failed
    ROLLED_BACK = "ROLLED_BACK"  # Action was rolled back (for audit trail)


@dataclass
class DomainAck:
    """
    Acknowledgment that a domain action has completed.

    Emitted by facades after successful domain operations.
    Matched against expectations during reconciliation.

    Attributes:
        id: Unique ack ID
        run_id: The run this ack belongs to
        domain: Which domain performed the action
        action: What action was performed
        status: Status of the ack (SUCCESS, FAILED, ROLLED_BACK)
        result_id: ID of the created entity (e.g., incident_id)
        error: Error message if action failed
        rolled_back: True if this action was rolled back (audit trail)
        rollback_reason: Why the action was rolled back
        created_at: When this ack was created
        metadata: Additional context (e.g., execution time)
    """

    run_id: UUID
    domain: AuditDomain
    action: AuditAction
    id: UUID = field(default_factory=uuid4)
    status: AckStatus = AckStatus.SUCCESS
    result_id: Optional[str] = None
    error: Optional[str] = None
    rolled_back: bool = False
    rollback_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if this ack represents a successful action."""
        return self.status == AckStatus.SUCCESS and self.error is None

    @property
    def is_rolled_back(self) -> bool:
        """Check if this action was rolled back."""
        return self.rolled_back or self.status == AckStatus.ROLLED_BACK

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "domain": self.domain.value,
            "action": self.action.value,
            "status": self.status.value,
            "result_id": self.result_id,
            "error": self.error,
            "rolled_back": self.rolled_back,
            "rollback_reason": self.rollback_reason,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainAck":
        """Deserialize from storage."""
        return cls(
            id=UUID(data["id"]),
            run_id=UUID(data["run_id"]),
            domain=AuditDomain(data["domain"]),
            action=AuditAction(data["action"]),
            status=AckStatus(data.get("status", "SUCCESS")),
            result_id=data.get("result_id"),
            error=data.get("error"),
            rolled_back=data.get("rolled_back", False),
            rollback_reason=data.get("rollback_reason"),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )

    def key(self) -> Tuple[str, str]:
        """Return (domain, action) tuple for set operations."""
        return (self.domain.value, self.action.value)


@dataclass
class ReconciliationResult:
    """
    Result of reconciling expectations against acknowledgments.

    Produced by AuditReconciler after comparing what was expected
    vs what actually happened.

    Attributes:
        run_id: The run that was reconciled
        status: Overall status (COMPLETE, INCOMPLETE, STALE)
        missing_actions: Actions expected but not acked
        drift_actions: Actions acked but not expected
        failed_actions: Actions acked with errors
        stale_run: True if finalize_run was never acked
        reconciled_at: When reconciliation was performed
        expectations_count: Total expectations
        acks_count: Total acks received
    """

    run_id: UUID
    status: str  # COMPLETE, INCOMPLETE, STALE
    missing_actions: List[Tuple[str, str]] = field(default_factory=list)
    drift_actions: List[Tuple[str, str]] = field(default_factory=list)
    failed_actions: List[Tuple[str, str]] = field(default_factory=list)
    stale_run: bool = False
    reconciled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expectations_count: int = 0
    acks_count: int = 0

    @property
    def is_clean(self) -> bool:
        """Check if reconciliation found no issues."""
        return (
            self.status == "COMPLETE"
            and not self.missing_actions
            and not self.drift_actions
            and not self.failed_actions
            and not self.stale_run
        )

    @property
    def has_missing(self) -> bool:
        """Check if there are missing actions."""
        return len(self.missing_actions) > 0

    @property
    def has_drift(self) -> bool:
        """Check if there are unexpected actions."""
        return len(self.drift_actions) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "run_id": str(self.run_id),
            "status": self.status,
            "missing_actions": self.missing_actions,
            "drift_actions": self.drift_actions,
            "failed_actions": self.failed_actions,
            "stale_run": self.stale_run,
            "reconciled_at": self.reconciled_at.isoformat(),
            "expectations_count": self.expectations_count,
            "acks_count": self.acks_count,
            "is_clean": self.is_clean,
        }


# =============================================================================
# Factory Functions for Common Expectations
# =============================================================================


def create_run_expectations(
    run_id: UUID,
    run_timeout_ms: int = 30000,
    grace_period_ms: int = 5000,
) -> List[AuditExpectation]:
    """
    Create the standard set of expectations for a run.

    This is called by ROK at T0 (run creation) to declare
    what MUST happen during run execution.

    Args:
        run_id: The run ID
        run_timeout_ms: Expected run duration
        grace_period_ms: Grace period after run timeout

    Returns:
        List of AuditExpectation objects
    """
    expectations = [
        # Incident creation (all runs create incidents per PIN-407)
        AuditExpectation(
            run_id=run_id,
            domain=AuditDomain.INCIDENTS,
            action=AuditAction.CREATE_INCIDENT,
            deadline_ms=5000,
        ),
        # Policy evaluation (all runs get policy evaluation)
        AuditExpectation(
            run_id=run_id,
            domain=AuditDomain.POLICIES,
            action=AuditAction.EVALUATE_POLICY,
            deadline_ms=5000,
        ),
        # Trace start (observability)
        AuditExpectation(
            run_id=run_id,
            domain=AuditDomain.LOGS,
            action=AuditAction.START_TRACE,
            deadline_ms=5000,
        ),
        # Meta-expectation: Run must finalize (liveness guarantee)
        AuditExpectation(
            run_id=run_id,
            domain=AuditDomain.ORCHESTRATOR,
            action=AuditAction.FINALIZE_RUN,
            deadline_ms=run_timeout_ms + grace_period_ms,
            metadata={"is_liveness_check": True},
        ),
    ]
    return expectations


def create_domain_ack(
    run_id: UUID,
    domain: AuditDomain,
    action: AuditAction,
    result_id: Optional[str] = None,
    error: Optional[str] = None,
    **metadata: Any,
) -> DomainAck:
    """
    Create a domain acknowledgment.

    This is called by facades after completing domain operations.

    Args:
        run_id: The run ID
        domain: Which domain performed the action
        action: What action was performed
        result_id: ID of created entity (e.g., incident_id)
        error: Error message if action failed
        **metadata: Additional context

    Returns:
        DomainAck object
    """
    return DomainAck(
        run_id=run_id,
        domain=domain,
        action=action,
        result_id=result_id,
        error=error,
        metadata=dict(metadata),
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "AckStatus",
    "AuditAction",
    "AuditDomain",
    "AuditStatus",
    # Dataclasses
    "AuditExpectation",
    "DomainAck",
    "ReconciliationResult",
    # Factory functions
    "create_domain_ack",
    "create_run_expectations",
]
