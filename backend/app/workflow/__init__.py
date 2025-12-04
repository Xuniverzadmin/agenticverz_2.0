# Workflow Engine Module (M4 + Hardening)
# Deterministic multi-step workflow execution with checkpoints, resume, and replay

from .engine import WorkflowEngine, StepContext, WorkflowSpec, StepDescriptor
from .checkpoint import (
    CheckpointStore,
    WorkflowCheckpoint,
    CheckpointVersionConflictError,
    InMemoryCheckpointStore,
    CheckpointData,
)
from .policies import PolicyEnforcer, BudgetExceededError, PolicyViolationError
from .planner_sandbox import PlannerSandbox, SandboxReport
from .golden import GoldenRecorder, InMemoryGoldenRecorder, GoldenEvent
from .errors import (
    ErrorCategory,
    WorkflowErrorCode,
    WorkflowError,
    classify_exception,
    get_error_metadata,
    ERROR_METADATA,
)
from .canonicalize import (
    canonicalize_for_golden,
    canonical_json,
    canonical_hash,
    redact_sensitive_fields,
    compare_canonical,
    strip_volatile_from_events,
    DEFAULT_VOLATILE_FIELDS,
    SENSITIVE_FIELDS,
)
from .external_guard import (
    ExternalCallsGuard,
    ExternalCallBlockedError,
    block_external_calls,
    require_no_external_calls,
    is_external_calls_disabled,
    check_external_call_allowed,
    assert_no_external_calls_made,
)
from .health import router as health_router, configure_health, record_checkpoint_activity
from .metrics import (
    record_workflow_failure,
    record_step_failure,
    record_step_duration,
    record_workflow_start,
    record_workflow_end,
    record_checkpoint_operation,
    record_replay_verification,
)

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
