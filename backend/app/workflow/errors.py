# Workflow Error Taxonomy (M4 Hardening)
"""
Canonical error codes and taxonomy for workflow execution.

Provides:
1. Structured error codes with categories
2. Retry policies per error type
3. HTTP status code mapping
4. Recovery suggestions

Design Principles:
- Deterministic: Same error conditions produce same codes
- Actionable: Each code has clear recovery path
- Auditable: Codes are logged and tracked in golden files
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCategory(str, Enum):
    """Error categories for classification and retry logic."""

    # Transient - retry might work
    TRANSIENT = "transient"

    # Permanent - don't retry
    PERMANENT = "permanent"

    # Resource - budget/rate limit exhausted
    RESOURCE = "resource"

    # Permission - not allowed
    PERMISSION = "permission"

    # Validation - bad input
    VALIDATION = "validation"

    # Infrastructure - system-level issues
    INFRASTRUCTURE = "infrastructure"

    # Planner - planner-related errors
    PLANNER = "planner"

    # Skill - skill execution errors
    SKILL = "skill"

    # Data - data-related errors
    DATA = "data"

    # Security - security violations
    SECURITY = "security"

    # Checkpoint - checkpoint/state errors
    CHECKPOINT = "checkpoint"

    def is_retryable(self) -> bool:
        """Check if errors in this category are retryable."""
        return self in (ErrorCategory.TRANSIENT, ErrorCategory.INFRASTRUCTURE)


class WorkflowErrorCode(str, Enum):
    """
    Canonical error codes for workflow execution.

    Format: {CATEGORY}_{SPECIFIC_ERROR}

    Each code maps to:
    - HTTP status code
    - Retry policy
    - Recovery suggestion
    """

    # === TRANSIENT ===
    TIMEOUT = "TIMEOUT"
    DNS_FAILURE = "DNS_FAILURE"
    CONNECTION_RESET = "CONNECTION_RESET"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"

    # === PERMANENT ===
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    INVALID_SKILL = "INVALID_SKILL"
    STEP_FAILED = "STEP_FAILED"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    WORKFLOW_ABORTED = "WORKFLOW_ABORTED"

    # === RESOURCE ===
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    STEP_CEILING_EXCEEDED = "STEP_CEILING_EXCEEDED"
    WORKFLOW_CEILING_EXCEEDED = "WORKFLOW_CEILING_EXCEEDED"
    AGENT_BUDGET_EXCEEDED = "AGENT_BUDGET_EXCEEDED"
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"

    # === PERMISSION ===
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN_SKILL = "FORBIDDEN_SKILL"
    TENANT_SUSPENDED = "TENANT_SUSPENDED"

    # === VALIDATION ===
    INVALID_INPUT = "INVALID_INPUT"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    INVALID_SPEC = "INVALID_SPEC"

    # === INFRASTRUCTURE ===
    DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    REDIS_CONNECTION_FAILED = "REDIS_CONNECTION_FAILED"
    CHECKPOINT_SAVE_FAILED = "CHECKPOINT_SAVE_FAILED"
    CHECKPOINT_LOAD_FAILED = "CHECKPOINT_LOAD_FAILED"
    GOLDEN_WRITE_FAILED = "GOLDEN_WRITE_FAILED"

    # === PLANNER ===
    PLANNER_TIMEOUT = "PLANNER_TIMEOUT"
    PLANNER_ERROR = "PLANNER_ERROR"
    INVALID_PLAN = "INVALID_PLAN"
    PLAN_TOO_EXPENSIVE = "PLAN_TOO_EXPENSIVE"

    # === SKILL ===
    HTTP_4XX = "HTTP_4XX"
    HTTP_5XX = "HTTP_5XX"
    LLM_ERROR = "LLM_ERROR"
    LLM_CONTEXT_EXCEEDED = "LLM_CONTEXT_EXCEEDED"
    TRANSFORM_ERROR = "TRANSFORM_ERROR"

    # === DATA ===
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_CORRUPT = "DATA_CORRUPT"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    DESERIALIZATION_ERROR = "DESERIALIZATION_ERROR"

    # === SECURITY ===
    INJECTION_DETECTED = "INJECTION_DETECTED"
    SANDBOX_REJECTION = "SANDBOX_REJECTION"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    TAMPER_DETECTED = "TAMPER_DETECTED"

    # === CHECKPOINT ===
    CHECKPOINT_VERSION_CONFLICT = "CHECKPOINT_VERSION_CONFLICT"
    CHECKPOINT_STALE = "CHECKPOINT_STALE"
    RESUME_FAILED = "RESUME_FAILED"

    # === POLICY ===
    POLICY_VIOLATION = "POLICY_VIOLATION"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    IDEMPOTENCY_REQUIRED = "IDEMPOTENCY_REQUIRED"


# Error metadata mapping
ERROR_METADATA: Dict[WorkflowErrorCode, Dict[str, Any]] = {
    # Transient errors
    WorkflowErrorCode.TIMEOUT: {
        "category": ErrorCategory.TRANSIENT,
        "http_status": 504,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 1000,
        "recovery": "Retry with exponential backoff",
    },
    WorkflowErrorCode.DNS_FAILURE: {
        "category": ErrorCategory.TRANSIENT,
        "http_status": 503,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 500,
        "recovery": "Check DNS resolution, retry after delay",
    },
    WorkflowErrorCode.CONNECTION_RESET: {
        "category": ErrorCategory.TRANSIENT,
        "http_status": 503,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 500,
        "recovery": "Retry connection",
    },
    WorkflowErrorCode.SERVICE_UNAVAILABLE: {
        "category": ErrorCategory.TRANSIENT,
        "http_status": 503,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 2000,
        "recovery": "Service temporarily unavailable, retry later",
    },
    WorkflowErrorCode.GATEWAY_TIMEOUT: {
        "category": ErrorCategory.TRANSIENT,
        "http_status": 504,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 3000,
        "recovery": "Gateway timeout, retry with longer timeout",
    },
    # Permanent errors
    WorkflowErrorCode.SKILL_NOT_FOUND: {
        "category": ErrorCategory.PERMANENT,
        "http_status": 404,
        "retryable": False,
        "recovery": "Register skill or check skill_id spelling",
    },
    WorkflowErrorCode.INVALID_SKILL: {
        "category": ErrorCategory.PERMANENT,
        "http_status": 500,
        "retryable": False,
        "recovery": "Fix skill implementation",
    },
    WorkflowErrorCode.STEP_FAILED: {
        "category": ErrorCategory.PERMANENT,
        "http_status": 500,
        "retryable": False,
        "recovery": "Check step inputs and skill behavior",
    },
    WorkflowErrorCode.EXECUTION_ERROR: {
        "category": ErrorCategory.PERMANENT,
        "http_status": 500,
        "retryable": False,
        "recovery": "Check execution logs for details",
    },
    WorkflowErrorCode.UNKNOWN_ERROR: {
        "category": ErrorCategory.PERMANENT,
        "http_status": 500,
        "retryable": False,
        "recovery": "Investigation required",
    },
    WorkflowErrorCode.WORKFLOW_ABORTED: {
        "category": ErrorCategory.PERMANENT,
        "http_status": 499,
        "retryable": False,
        "recovery": "Workflow was intentionally aborted",
    },
    # Resource errors
    WorkflowErrorCode.BUDGET_EXCEEDED: {
        "category": ErrorCategory.RESOURCE,
        "http_status": 402,
        "retryable": False,
        "recovery": "Increase budget or reduce step costs",
    },
    WorkflowErrorCode.STEP_CEILING_EXCEEDED: {
        "category": ErrorCategory.RESOURCE,
        "http_status": 402,
        "retryable": False,
        "recovery": "Reduce step cost or increase step ceiling",
    },
    WorkflowErrorCode.WORKFLOW_CEILING_EXCEEDED: {
        "category": ErrorCategory.RESOURCE,
        "http_status": 402,
        "retryable": False,
        "recovery": "Reduce workflow cost or increase workflow ceiling",
    },
    WorkflowErrorCode.AGENT_BUDGET_EXCEEDED: {
        "category": ErrorCategory.RESOURCE,
        "http_status": 402,
        "retryable": False,
        "recovery": "Request budget increase or wait for reset",
    },
    WorkflowErrorCode.RATE_LIMITED: {
        "category": ErrorCategory.RESOURCE,
        "http_status": 429,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 5000,
        "recovery": "Wait for rate limit reset",
    },
    WorkflowErrorCode.QUOTA_EXHAUSTED: {
        "category": ErrorCategory.RESOURCE,
        "http_status": 429,
        "retryable": False,
        "recovery": "Request quota increase",
    },
    # Permission errors
    WorkflowErrorCode.PERMISSION_DENIED: {
        "category": ErrorCategory.PERMISSION,
        "http_status": 403,
        "retryable": False,
        "recovery": "Request permission or use authorized credentials",
    },
    WorkflowErrorCode.UNAUTHORIZED: {
        "category": ErrorCategory.PERMISSION,
        "http_status": 401,
        "retryable": False,
        "recovery": "Provide valid authentication",
    },
    WorkflowErrorCode.FORBIDDEN_SKILL: {
        "category": ErrorCategory.PERMISSION,
        "http_status": 403,
        "retryable": False,
        "recovery": "Use allowed skills only",
    },
    WorkflowErrorCode.TENANT_SUSPENDED: {
        "category": ErrorCategory.PERMISSION,
        "http_status": 403,
        "retryable": False,
        "recovery": "Contact support to reactivate tenant",
    },
    # Validation errors
    WorkflowErrorCode.INVALID_INPUT: {
        "category": ErrorCategory.VALIDATION,
        "http_status": 400,
        "retryable": False,
        "recovery": "Fix input data format",
    },
    WorkflowErrorCode.SCHEMA_VALIDATION_FAILED: {
        "category": ErrorCategory.VALIDATION,
        "http_status": 400,
        "retryable": False,
        "recovery": "Match input to expected schema",
    },
    WorkflowErrorCode.MISSING_REQUIRED_FIELD: {
        "category": ErrorCategory.VALIDATION,
        "http_status": 400,
        "retryable": False,
        "recovery": "Provide all required fields",
    },
    WorkflowErrorCode.INVALID_REFERENCE: {
        "category": ErrorCategory.VALIDATION,
        "http_status": 400,
        "retryable": False,
        "recovery": "Fix step reference format",
    },
    WorkflowErrorCode.INVALID_SPEC: {
        "category": ErrorCategory.VALIDATION,
        "http_status": 400,
        "retryable": False,
        "recovery": "Fix workflow specification",
    },
    # Infrastructure errors
    WorkflowErrorCode.DB_CONNECTION_FAILED: {
        "category": ErrorCategory.INFRASTRUCTURE,
        "http_status": 503,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 1000,
        "recovery": "Check database connectivity",
    },
    WorkflowErrorCode.REDIS_CONNECTION_FAILED: {
        "category": ErrorCategory.INFRASTRUCTURE,
        "http_status": 503,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 1000,
        "recovery": "Check Redis connectivity",
    },
    WorkflowErrorCode.CHECKPOINT_SAVE_FAILED: {
        "category": ErrorCategory.CHECKPOINT,
        "http_status": 500,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 500,
        "recovery": "Retry checkpoint save",
    },
    WorkflowErrorCode.CHECKPOINT_LOAD_FAILED: {
        "category": ErrorCategory.CHECKPOINT,
        "http_status": 500,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 500,
        "recovery": "Retry checkpoint load",
    },
    WorkflowErrorCode.GOLDEN_WRITE_FAILED: {
        "category": ErrorCategory.INFRASTRUCTURE,
        "http_status": 500,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 500,
        "recovery": "Check golden file storage",
    },
    # Planner errors
    WorkflowErrorCode.PLANNER_TIMEOUT: {
        "category": ErrorCategory.PLANNER,
        "http_status": 504,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 2000,
        "recovery": "Retry planning with simpler prompt",
    },
    WorkflowErrorCode.PLANNER_ERROR: {
        "category": ErrorCategory.PLANNER,
        "http_status": 500,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 1000,
        "recovery": "Check planner configuration",
    },
    WorkflowErrorCode.INVALID_PLAN: {
        "category": ErrorCategory.PLANNER,
        "http_status": 400,
        "retryable": False,
        "recovery": "Fix planner output format",
    },
    WorkflowErrorCode.PLAN_TOO_EXPENSIVE: {
        "category": ErrorCategory.PLANNER,
        "http_status": 402,
        "retryable": False,
        "recovery": "Constrain planner to cheaper operations",
    },
    # Skill errors
    WorkflowErrorCode.HTTP_4XX: {
        "category": ErrorCategory.SKILL,
        "http_status": 400,
        "retryable": False,
        "recovery": "Fix request parameters",
    },
    WorkflowErrorCode.HTTP_5XX: {
        "category": ErrorCategory.SKILL,
        "http_status": 502,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 1000,
        "recovery": "Retry request",
    },
    WorkflowErrorCode.LLM_ERROR: {
        "category": ErrorCategory.SKILL,
        "http_status": 502,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 2000,
        "recovery": "Retry LLM call",
    },
    WorkflowErrorCode.LLM_CONTEXT_EXCEEDED: {
        "category": ErrorCategory.SKILL,
        "http_status": 400,
        "retryable": False,
        "recovery": "Reduce input context size",
    },
    WorkflowErrorCode.TRANSFORM_ERROR: {
        "category": ErrorCategory.SKILL,
        "http_status": 400,
        "retryable": False,
        "recovery": "Fix transformation expression",
    },
    # Data errors
    WorkflowErrorCode.DATA_NOT_FOUND: {
        "category": ErrorCategory.DATA,
        "http_status": 404,
        "retryable": False,
        "recovery": "Check data source",
    },
    WorkflowErrorCode.DATA_CORRUPT: {
        "category": ErrorCategory.DATA,
        "http_status": 500,
        "retryable": False,
        "recovery": "Restore from backup",
    },
    WorkflowErrorCode.SERIALIZATION_ERROR: {
        "category": ErrorCategory.DATA,
        "http_status": 500,
        "retryable": False,
        "recovery": "Fix data format for serialization",
    },
    WorkflowErrorCode.DESERIALIZATION_ERROR: {
        "category": ErrorCategory.DATA,
        "http_status": 500,
        "retryable": False,
        "recovery": "Fix stored data format",
    },
    # Security errors
    WorkflowErrorCode.INJECTION_DETECTED: {
        "category": ErrorCategory.SECURITY,
        "http_status": 400,
        "retryable": False,
        "recovery": "Remove malicious input",
    },
    WorkflowErrorCode.SANDBOX_REJECTION: {
        "category": ErrorCategory.SECURITY,
        "http_status": 403,
        "retryable": False,
        "recovery": "Remove forbidden operations from plan",
    },
    WorkflowErrorCode.SIGNATURE_INVALID: {
        "category": ErrorCategory.SECURITY,
        "http_status": 401,
        "retryable": False,
        "recovery": "Re-sign with correct key",
    },
    WorkflowErrorCode.TAMPER_DETECTED: {
        "category": ErrorCategory.SECURITY,
        "http_status": 403,
        "retryable": False,
        "recovery": "Restore from verified backup",
    },
    # Checkpoint errors
    WorkflowErrorCode.CHECKPOINT_VERSION_CONFLICT: {
        "category": ErrorCategory.CHECKPOINT,
        "http_status": 409,
        "retryable": True,
        "max_retries": 3,
        "backoff_base_ms": 100,
        "recovery": "Reload checkpoint and retry",
    },
    WorkflowErrorCode.CHECKPOINT_STALE: {
        "category": ErrorCategory.CHECKPOINT,
        "http_status": 409,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 500,
        "recovery": "Reload fresh checkpoint",
    },
    WorkflowErrorCode.RESUME_FAILED: {
        "category": ErrorCategory.CHECKPOINT,
        "http_status": 500,
        "retryable": True,
        "max_retries": 2,
        "backoff_base_ms": 1000,
        "recovery": "Check checkpoint integrity",
    },
    # Policy errors
    WorkflowErrorCode.POLICY_VIOLATION: {
        "category": ErrorCategory.PERMISSION,
        "http_status": 403,
        "retryable": False,
        "recovery": "Adjust operation to comply with policy",
    },
    WorkflowErrorCode.EMERGENCY_STOP: {
        "category": ErrorCategory.PERMISSION,
        "http_status": 503,
        "retryable": False,
        "recovery": "Wait for emergency stop to be lifted",
    },
    WorkflowErrorCode.IDEMPOTENCY_REQUIRED: {
        "category": ErrorCategory.VALIDATION,
        "http_status": 400,
        "retryable": False,
        "recovery": "Add idempotency_key to step",
    },
}


@dataclass
class WorkflowError:
    """
    Structured workflow error with full metadata.

    Used for:
    - Logging with structured fields
    - Golden file recording
    - API responses
    - Recovery suggestion display
    """

    code: WorkflowErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    step_id: Optional[str] = None
    run_id: Optional[str] = None

    @property
    def category(self) -> ErrorCategory:
        """Get error category."""
        meta = ERROR_METADATA.get(self.code, {})
        return meta.get("category", ErrorCategory.PERMANENT)

    @property
    def http_status(self) -> int:
        """Get HTTP status code."""
        meta = ERROR_METADATA.get(self.code, {})
        return meta.get("http_status", 500)

    @property
    def is_retryable(self) -> bool:
        """Check if error is retryable."""
        meta = ERROR_METADATA.get(self.code, {})
        return meta.get("retryable", False)

    @property
    def max_retries(self) -> int:
        """Get max retry count."""
        meta = ERROR_METADATA.get(self.code, {})
        return meta.get("max_retries", 0)

    @property
    def backoff_base_ms(self) -> int:
        """Get base backoff in milliseconds."""
        meta = ERROR_METADATA.get(self.code, {})
        return meta.get("backoff_base_ms", 1000)

    @property
    def recovery(self) -> str:
        """Get recovery suggestion."""
        meta = ERROR_METADATA.get(self.code, {})
        return meta.get("recovery", "Investigation required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code.value,
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
            "step_id": self.step_id,
            "run_id": self.run_id,
            "http_status": self.http_status,
            "retryable": self.is_retryable,
            "recovery": self.recovery,
        }

    def to_api_error(self) -> Dict[str, Any]:
        """Convert to API error response format."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            },
            "recovery": self.recovery,
        }


def classify_exception(exc: Exception, context: Optional[Dict[str, Any]] = None) -> WorkflowError:
    """
    Classify an exception into a structured WorkflowError.

    Args:
        exc: The exception to classify
        context: Optional context (step_id, run_id, etc.)

    Returns:
        WorkflowError with appropriate code
    """
    context = context or {}
    message = str(exc)
    exc_type = type(exc).__name__

    # Import here to avoid circular imports
    from .policies import BudgetExceededError, PolicyViolationError

    # Budget errors
    if isinstance(exc, BudgetExceededError):
        if "step" in exc.breach_type.lower():
            code = WorkflowErrorCode.STEP_CEILING_EXCEEDED
        elif "workflow" in exc.breach_type.lower():
            code = WorkflowErrorCode.WORKFLOW_CEILING_EXCEEDED
        elif "agent" in exc.breach_type.lower():
            code = WorkflowErrorCode.AGENT_BUDGET_EXCEEDED
        else:
            code = WorkflowErrorCode.BUDGET_EXCEEDED
        return WorkflowError(
            code=code,
            message=message,
            details={"breach_type": exc.breach_type, "limit": exc.limit_cents, "current": exc.current_cents},
            **context,
        )

    # Policy errors
    if isinstance(exc, PolicyViolationError):
        if "emergency" in exc.policy.lower():
            code = WorkflowErrorCode.EMERGENCY_STOP
        elif "idempotency" in exc.policy.lower():
            code = WorkflowErrorCode.IDEMPOTENCY_REQUIRED
        else:
            code = WorkflowErrorCode.POLICY_VIOLATION
        return WorkflowError(
            code=code,
            message=message,
            details=exc.details,
            **context,
        )

    # Connection errors
    if "timeout" in message.lower() or "timed out" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.TIMEOUT, message=message, **context)

    if "connection" in message.lower():
        if "reset" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.CONNECTION_RESET, message=message, **context)
        if "refused" in message.lower() or "failed" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.DB_CONNECTION_FAILED, message=message, **context)

    if "dns" in message.lower() or "resolve" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.DNS_FAILURE, message=message, **context)

    # Rate limiting
    if "rate" in message.lower() and "limit" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.RATE_LIMITED, message=message, **context)

    # Permission errors
    if "permission" in message.lower() or "forbidden" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.PERMISSION_DENIED, message=message, **context)

    if "unauthorized" in message.lower() or "authentication" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.UNAUTHORIZED, message=message, **context)

    # Validation errors
    if "validation" in message.lower() or "invalid" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.INVALID_INPUT, message=message, **context)

    # HTTP status codes from httpx/aiohttp/requests
    if "status" in message.lower() or exc_type in ("HTTPStatusError", "ClientResponseError"):
        # Try to extract status code
        import re

        status_match = re.search(r"(\d{3})", message)
        if status_match:
            status = int(status_match.group(1))
            if 400 <= status < 500:
                if status == 401:
                    return WorkflowError(code=WorkflowErrorCode.UNAUTHORIZED, message=message, **context)
                elif status == 403:
                    return WorkflowError(code=WorkflowErrorCode.PERMISSION_DENIED, message=message, **context)
                elif status == 404:
                    return WorkflowError(code=WorkflowErrorCode.DATA_NOT_FOUND, message=message, **context)
                elif status == 429:
                    return WorkflowError(code=WorkflowErrorCode.RATE_LIMITED, message=message, **context)
                else:
                    return WorkflowError(
                        code=WorkflowErrorCode.HTTP_4XX, message=message, details={"status_code": status}, **context
                    )
            elif 500 <= status < 600:
                if status == 502 or status == 503:
                    return WorkflowError(code=WorkflowErrorCode.SERVICE_UNAVAILABLE, message=message, **context)
                elif status == 504:
                    return WorkflowError(code=WorkflowErrorCode.GATEWAY_TIMEOUT, message=message, **context)
                else:
                    return WorkflowError(
                        code=WorkflowErrorCode.HTTP_5XX, message=message, details={"status_code": status}, **context
                    )

    # Database errors (psycopg2, asyncpg, sqlalchemy)
    db_error_types = ("OperationalError", "InterfaceError", "DatabaseError", "PostgresError", "IntegrityError")
    if exc_type in db_error_types:
        if "constraint" in message.lower() or "unique" in message.lower() or "duplicate" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.CHECKPOINT_VERSION_CONFLICT, message=message, **context)
        if "deadlock" in message.lower():
            return WorkflowError(
                code=WorkflowErrorCode.DB_CONNECTION_FAILED,
                message=message,
                details={"db_error": "deadlock"},
                **context,
            )
        return WorkflowError(code=WorkflowErrorCode.DB_CONNECTION_FAILED, message=message, **context)

    # Redis errors
    redis_error_types = ("RedisError", "ConnectionError", "TimeoutError", "ResponseError")
    if exc_type in redis_error_types or "redis" in message.lower():
        return WorkflowError(code=WorkflowErrorCode.REDIS_CONNECTION_FAILED, message=message, **context)

    # LLM/Anthropic errors
    if "anthropic" in message.lower() or "claude" in message.lower() or "llm" in message.lower():
        if "context" in message.lower() or "token" in message.lower() or "length" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.LLM_CONTEXT_EXCEEDED, message=message, **context)
        if "overloaded" in message.lower() or "capacity" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.SERVICE_UNAVAILABLE, message=message, **context)
        return WorkflowError(code=WorkflowErrorCode.LLM_ERROR, message=message, **context)

    # JSON/serialization errors
    if exc_type in ("JSONDecodeError", "SerializationError") or "json" in message.lower():
        if "decode" in message.lower() or "parse" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.DESERIALIZATION_ERROR, message=message, **context)
        return WorkflowError(code=WorkflowErrorCode.SERIALIZATION_ERROR, message=message, **context)

    # File/IO errors
    if exc_type in ("FileNotFoundError", "IOError", "OSError"):
        if "golden" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.GOLDEN_WRITE_FAILED, message=message, **context)
        if "permission" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.PERMISSION_DENIED, message=message, **context)
        return WorkflowError(code=WorkflowErrorCode.DATA_NOT_FOUND, message=message, **context)

    # Value/Type errors that indicate validation issues
    if exc_type in ("ValueError", "TypeError", "KeyError", "AttributeError"):
        if "required" in message.lower() or "missing" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.MISSING_REQUIRED_FIELD, message=message, **context)
        if "schema" in message.lower():
            return WorkflowError(code=WorkflowErrorCode.SCHEMA_VALIDATION_FAILED, message=message, **context)
        return WorkflowError(
            code=WorkflowErrorCode.INVALID_INPUT, message=message, details={"exception_type": exc_type}, **context
        )

    # Default to execution error
    return WorkflowError(
        code=WorkflowErrorCode.EXECUTION_ERROR,
        message=message,
        details={"exception_type": exc_type},
        **context,
    )


def get_error_metadata(code: WorkflowErrorCode) -> Dict[str, Any]:
    """Get full metadata for an error code."""
    return ERROR_METADATA.get(
        code,
        {
            "category": ErrorCategory.PERMANENT,
            "http_status": 500,
            "retryable": False,
            "recovery": "Investigation required",
        },
    )
