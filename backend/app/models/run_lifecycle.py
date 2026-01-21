# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Run lifecycle enums and models for governance
# Callers: worker/runner.py, services/*, api/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: BACKEND_REMEDIATION_PLAN.md GAP-002, GAP-007

"""
Run Lifecycle Models

Provides formal enums for run termination and status tracking.
Replaces string-based status/error codes with typed enums for:
- Better type safety
- Clear precedence rules
- SOC2-ready audit trails

Remediation: GAP-002 (Run stop on violation), GAP-007 (Termination enum)
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class RunTerminationReason(str, Enum):
    """
    Formal enum for why a run terminated.

    Precedence (highest to lowest):
    1. POLICY_BLOCK - Policy violation (immediate stop)
    2. BUDGET_EXCEEDED - Budget limit hit
    3. RATE_LIMITED - Rate limit reached
    4. TIMEOUT - Execution timeout
    5. SYSTEM_FAILURE - Internal error
    6. USER_ABORT - Manual cancellation
    7. COMPLETED - Normal completion
    """
    # Policy governance (highest priority)
    POLICY_BLOCK = "policy_block"

    # Resource limits
    BUDGET_EXCEEDED = "budget_exceeded"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"

    # System states
    SYSTEM_FAILURE = "system_failure"
    USER_ABORT = "user_abort"

    # Normal completion
    COMPLETED = "completed"


class RunStatus(str, Enum):
    """
    Run execution status.

    State transitions:
    QUEUED -> RUNNING -> SUCCEEDED | FAILED | FAILED_POLICY | CANCELLED
    """
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    FAILED_POLICY = "failed_policy"  # Stopped by policy violation
    CANCELLED = "cancelled"
    RETRY = "retry"


class RunLifecycleState(str, Enum):
    """
    High-level lifecycle state for UI purposes.

    LIVE: Run is in progress (queued, running, retry)
    COMPLETED: Run has finished (succeeded, failed, cancelled)
    """
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"


class PolicyViolationType(str, Enum):
    """Types of policy violations that can stop a run."""
    TOKEN_LIMIT = "token_limit"
    COST_LIMIT = "cost_limit"
    RATE_LIMIT = "rate_limit"
    CONTENT_POLICY = "content_policy"
    PII_DETECTED = "pii_detected"
    SAFETY_VIOLATION = "safety_violation"
    CUSTOM_RULE = "custom_rule"


class ViolationSeverity(str, Enum):
    """Severity levels for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Pydantic models for API/Service use

class RunViolationInfo(BaseModel):
    """Information about a policy violation that stopped a run."""
    policy_id: str
    policy_name: str
    violation_type: PolicyViolationType
    severity: ViolationSeverity
    step_index: int
    timestamp: datetime
    threshold_value: Optional[str] = None
    actual_value: Optional[str] = None
    reason: str


class RunTerminationInfo(BaseModel):
    """Complete termination information for a run."""
    termination_reason: RunTerminationReason
    terminated_at: datetime
    stopped_at_step: Optional[int] = None
    violation_info: Optional[RunViolationInfo] = None
    error_message: Optional[str] = None


# Mapping helpers

TERMINATION_TO_STATUS: dict[RunTerminationReason, RunStatus] = {
    RunTerminationReason.COMPLETED: RunStatus.SUCCEEDED,
    RunTerminationReason.POLICY_BLOCK: RunStatus.FAILED_POLICY,
    RunTerminationReason.BUDGET_EXCEEDED: RunStatus.FAILED,
    RunTerminationReason.RATE_LIMITED: RunStatus.FAILED,
    RunTerminationReason.TIMEOUT: RunStatus.FAILED,
    RunTerminationReason.SYSTEM_FAILURE: RunStatus.FAILED,
    RunTerminationReason.USER_ABORT: RunStatus.CANCELLED,
}


SEVERITY_PRIORITY: dict[ViolationSeverity, int] = {
    ViolationSeverity.CRITICAL: 4,
    ViolationSeverity.HIGH: 3,
    ViolationSeverity.MEDIUM: 2,
    ViolationSeverity.LOW: 1,
}


def get_lifecycle_state(status: RunStatus) -> RunLifecycleState:
    """Map run status to lifecycle state."""
    live_statuses = {RunStatus.QUEUED, RunStatus.RUNNING, RunStatus.RETRY}
    return RunLifecycleState.LIVE if status in live_statuses else RunLifecycleState.COMPLETED
