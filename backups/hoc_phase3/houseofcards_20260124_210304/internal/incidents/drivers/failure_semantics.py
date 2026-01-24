# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api | sdk | worker
#   Execution: sync
# Role: Customer-visible failure semantics with category classification
# Callers: SDK facades, L2 API routes, lifecycle handlers
# Allowed Imports: None (pure value object)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: INV-W0-004

"""
Module: failure_semantics
Purpose: Provide structured failure semantics for customer-visible errors.

INV-W0-004: All customer-visible failures MUST be categorized.

Customers cannot distinguish between "try again later" and "this will never work"
without explicit failure categories. This module provides the standard structure.

Categories:
    TRANSIENT: Retry may succeed (network, rate limit, temporary outage)
    PERMANENT: Retry will not succeed (invalid input, missing resource)
    POLICY: Governance blocked (policy violation, budget exceeded)

Acceptance Criteria:
    - FS-001: All SDK methods return SDKResult with CustomerFailure
    - FS-002: All failures have explicit category
    - FS-003: TRANSIENT failures include retry_after
    - FS-004: POLICY failures include policy context
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class FailureCategory(str, Enum):
    """
    Customer-visible failure categories.

    These categories help clients understand what action to take:
    - TRANSIENT: Retry may succeed (wait and retry)
    - PERMANENT: Retry will not succeed (fix request)
    - POLICY: Governance blocked (contact admin or adjust policy)
    """

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    POLICY = "policy"


@dataclass
class CustomerFailure:
    """
    Structured failure for customer-visible errors.

    SDK and API responses MUST use this structure for all errors.
    This ensures consistent error handling across all clients.

    Attributes:
        category: The failure category (transient, permanent, policy)
        code: Machine-readable error code (e.g., "rate_limited")
        message: Human-readable error message
        retry_after_seconds: Seconds to wait before retry (TRANSIENT only)
        details: Additional context (e.g., policy_id for POLICY failures)
    """

    category: FailureCategory
    code: str
    message: str
    retry_after_seconds: Optional[int] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate failure structure."""
        if not self.code:
            raise ValueError("CustomerFailure requires a code")
        if not self.message:
            raise ValueError("CustomerFailure requires a message")

        # Initialize details to empty dict if None
        if self.details is None:
            self.details = {}

    def to_sdk_response(self) -> Dict[str, Any]:
        """
        Convert to SDK response format.

        Returns standardized error response that SDKs can parse:
        {
            "success": false,
            "error": {
                "category": "transient|permanent|policy",
                "code": "error_code",
                "message": "Human readable message",
                "retry_after_seconds": 60,  # Only for transient
                "details": {}  # Additional context
            }
        }
        """
        error: Dict[str, Any] = {
            "category": self.category.value,
            "code": self.code,
            "message": self.message,
        }

        if self.category == FailureCategory.TRANSIENT and self.retry_after_seconds:
            error["retry_after_seconds"] = self.retry_after_seconds

        if self.details:
            error["details"] = self.details

        return {
            "success": False,
            "error": error,
        }

    def to_api_response(self) -> Dict[str, Any]:
        """
        Convert to API response format for FastAPI.

        This format is suitable for HTTP error responses.
        """
        return self.to_sdk_response()

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for logging/serialization."""
        return {
            "category": self.category.value,
            "code": self.code,
            "message": self.message,
            "retry_after_seconds": self.retry_after_seconds,
            "details": self.details,
        }

    # =========================
    # Factory Methods
    # =========================

    @classmethod
    def transient(
        cls,
        code: str,
        message: str,
        retry_after: int = 60,
        details: Optional[Dict[str, Any]] = None,
    ) -> "CustomerFailure":
        """
        Create a transient failure (retry may help).

        Args:
            code: Error code (e.g., ErrorCodes.RATE_LIMITED)
            message: Human-readable message
            retry_after: Seconds to wait before retry (default 60)
            details: Additional context

        Returns:
            CustomerFailure with TRANSIENT category
        """
        return cls(
            category=FailureCategory.TRANSIENT,
            code=code,
            message=message,
            retry_after_seconds=retry_after,
            details=details or {},
        )

    @classmethod
    def permanent(
        cls,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "CustomerFailure":
        """
        Create a permanent failure (retry will not help).

        Args:
            code: Error code (e.g., ErrorCodes.INVALID_INPUT)
            message: Human-readable message
            details: Additional context (e.g., validation errors)

        Returns:
            CustomerFailure with PERMANENT category
        """
        return cls(
            category=FailureCategory.PERMANENT,
            code=code,
            message=message,
            details=details or {},
        )

    @classmethod
    def policy(
        cls,
        code: str,
        message: str,
        policy_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> "CustomerFailure":
        """
        Create a policy failure (governance blocked).

        Args:
            code: Error code (e.g., ErrorCodes.POLICY_VIOLATION)
            message: Human-readable message
            policy_id: The policy that blocked the action
            details: Additional context

        Returns:
            CustomerFailure with POLICY category
        """
        failure_details = details or {}
        if policy_id:
            failure_details["policy_id"] = policy_id

        return cls(
            category=FailureCategory.POLICY,
            code=code,
            message=message,
            details=failure_details,
        )


class ErrorCodes:
    """
    Standard error codes for customer-visible failures.

    These codes are machine-readable and allow clients to programmatically
    handle different error types.
    """

    # =========================
    # Transient Errors (retry may help)
    # =========================

    RATE_LIMITED = "rate_limited"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    TEMPORARY_FAILURE = "temporary_failure"
    RESOURCE_BUSY = "resource_busy"

    # =========================
    # Permanent Errors (retry will not help)
    # =========================

    INVALID_INPUT = "invalid_input"
    RESOURCE_NOT_FOUND = "resource_not_found"
    INVALID_STATE = "invalid_state"
    UNSUPPORTED_OPERATION = "unsupported_operation"
    INVALID_CONFIGURATION = "invalid_configuration"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_FAILED = "authorization_failed"
    CONFLICT = "conflict"
    PRECONDITION_FAILED = "precondition_failed"

    # =========================
    # Policy Errors (governance blocked)
    # =========================

    POLICY_VIOLATION = "policy_violation"
    BUDGET_EXCEEDED = "budget_exceeded"
    CAPABILITY_DISABLED = "capability_disabled"
    TENANT_SUSPENDED = "tenant_suspended"
    RATE_LIMIT_POLICY = "rate_limit_policy"
    CONTENT_POLICY = "content_policy"
    TOOL_BLOCKED = "tool_blocked"
    ACTION_BLOCKED = "action_blocked"


@dataclass
class SDKResult:
    """
    Standard result wrapper for SDK responses.

    All SDK methods MUST return SDKResult, never raw exceptions.

    Attributes:
        success: True if operation succeeded
        data: Result data (only if success=True)
        failure: CustomerFailure (only if success=False)
    """

    success: bool
    data: Optional[Dict[str, Any]] = None
    failure: Optional[CustomerFailure] = None

    def __post_init__(self):
        """Validate result structure."""
        if self.success and self.failure is not None:
            raise ValueError("Successful result cannot have a failure")
        if not self.success and self.failure is None:
            raise ValueError("Failed result must have a failure")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for SDK responses."""
        if self.success:
            return {
                "success": True,
                "data": self.data,
            }
        else:
            return self.failure.to_sdk_response()

    @classmethod
    def ok(cls, data: Optional[Dict[str, Any]] = None) -> "SDKResult":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, failure: CustomerFailure) -> "SDKResult":
        """Create a failed result."""
        return cls(success=False, failure=failure)

    @classmethod
    def fail_transient(
        cls,
        code: str,
        message: str,
        retry_after: int = 60,
    ) -> "SDKResult":
        """Create a transient failure result."""
        return cls.fail(
            CustomerFailure.transient(code, message, retry_after)
        )

    @classmethod
    def fail_permanent(
        cls,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "SDKResult":
        """Create a permanent failure result."""
        return cls.fail(
            CustomerFailure.permanent(code, message, details)
        )

    @classmethod
    def fail_policy(
        cls,
        code: str,
        message: str,
        policy_id: Optional[str] = None,
    ) -> "SDKResult":
        """Create a policy failure result."""
        return cls.fail(
            CustomerFailure.policy(code, message, policy_id)
        )


# =========================
# Exception to CustomerFailure Mapping
# =========================

def classify_exception(exc: Exception) -> CustomerFailure:
    """
    Classify an exception into a CustomerFailure.

    This is a fallback for exceptions that escape structured handling.
    Production code should catch and convert exceptions explicitly.

    Args:
        exc: The exception to classify

    Returns:
        CustomerFailure with appropriate category
    """
    import logging

    logger = logging.getLogger("nova.core.failure_semantics")

    exc_type = type(exc).__name__
    exc_message = str(exc)

    # Known transient exceptions
    transient_types = {
        "TimeoutError",
        "ConnectionError",
        "ConnectionRefusedError",
        "ConnectionResetError",
        "BrokenPipeError",
        "TemporaryError",
        "RetryableError",
    }

    # Known policy exceptions (by convention)
    policy_keywords = [
        "policy",
        "budget",
        "limit exceeded",
        "blocked",
        "forbidden",
        "not allowed",
    ]

    if exc_type in transient_types:
        return CustomerFailure.transient(
            code=ErrorCodes.TEMPORARY_FAILURE,
            message=f"Temporary error: {exc_message}",
            retry_after=60,
        )

    if any(kw in exc_message.lower() for kw in policy_keywords):
        return CustomerFailure.policy(
            code=ErrorCodes.POLICY_VIOLATION,
            message=exc_message,
        )

    # Log unclassified exceptions
    logger.warning(
        "failure_semantics.unclassified_exception",
        extra={"type": exc_type, "message": exc_message},
    )

    # Default to permanent (fail-safe)
    return CustomerFailure.permanent(
        code=ErrorCodes.INVALID_STATE,
        message=f"Unexpected error: {exc_message}",
    )
