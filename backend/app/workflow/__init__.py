# Workflow Engine Module (M4 + Hardening)
# Deterministic multi-step workflow execution with checkpoints, resume, and replay

from .canonicalize import (
    DEFAULT_VOLATILE_FIELDS,
    SENSITIVE_FIELDS,
    canonical_hash,
    canonical_json,
    canonicalize_for_golden,
    compare_canonical,
    redact_sensitive_fields,
    strip_volatile_from_events,
)
from .checkpoint import (
    CheckpointData,
    CheckpointStore,
    CheckpointVersionConflictError,
    InMemoryCheckpointStore,
    WorkflowCheckpoint,
)
from .engine import StepContext, StepDescriptor, WorkflowEngine, WorkflowSpec
from .errors import (
    ERROR_METADATA,
    ErrorCategory,
    WorkflowError,
    WorkflowErrorCode,
    classify_exception,
    get_error_metadata,
)
from .external_guard import (
    ExternalCallBlockedError,
    ExternalCallsGuard,
    assert_no_external_calls_made,
    block_external_calls,
    check_external_call_allowed,
    is_external_calls_disabled,
    require_no_external_calls,
)
from .golden import GoldenEvent, GoldenRecorder, InMemoryGoldenRecorder
from .health import configure_health, record_checkpoint_activity
from .health import router as health_router
from .metrics import (
    record_checkpoint_operation,
    record_replay_verification,
    record_step_duration,
    record_step_failure,
    record_workflow_end,
    record_workflow_failure,
    record_workflow_start,
)
from .planner_sandbox import PlannerSandbox, SandboxReport
from .policies import BudgetExceededError, PolicyEnforcer, PolicyViolationError

__all__ = [
    # Engine
    "WorkflowEngine",
    "StepContext",
    "WorkflowSpec",
    "StepDescriptor",
    # Checkpoint
    "CheckpointStore",
    "WorkflowCheckpoint",
    "CheckpointVersionConflictError",
    "InMemoryCheckpointStore",
    "CheckpointData",
    # Policies
    "PolicyEnforcer",
    "BudgetExceededError",
    "PolicyViolationError",
    # Sandbox
    "PlannerSandbox",
    "SandboxReport",
    # Golden
    "GoldenRecorder",
    "InMemoryGoldenRecorder",
    "GoldenEvent",
    # Errors
    "ErrorCategory",
    "WorkflowErrorCode",
    "WorkflowError",
    "classify_exception",
    "get_error_metadata",
    "ERROR_METADATA",
    # Canonicalization
    "canonicalize_for_golden",
    "canonical_json",
    "canonical_hash",
    "redact_sensitive_fields",
    "compare_canonical",
    "strip_volatile_from_events",
    "DEFAULT_VOLATILE_FIELDS",
    "SENSITIVE_FIELDS",
    # External Guard
    "ExternalCallsGuard",
    "ExternalCallBlockedError",
    "block_external_calls",
    "require_no_external_calls",
    "is_external_calls_disabled",
    "check_external_call_allowed",
    "assert_no_external_calls_made",
    # Health
    "health_router",
    "configure_health",
    "record_checkpoint_activity",
    # Metrics
    "record_workflow_failure",
    "record_step_failure",
    "record_step_duration",
    "record_workflow_start",
    "record_workflow_end",
    "record_checkpoint_operation",
    "record_replay_verification",
]
