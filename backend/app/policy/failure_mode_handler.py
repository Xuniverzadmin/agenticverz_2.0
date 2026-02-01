# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api (during policy evaluation)
#   Execution: sync
# Role: Handle failure modes - default to fail-closed
# Callers: prevention_engine.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-035

"""
Module: failure_mode_handler
Purpose: Handles failure modes when policy evaluation fails or is uncertain.

Key Principle: FAIL-CLOSED by default.
If policy evaluation fails, the system MUST block the action, not allow it.

Imports (Dependencies):
    - app.services.governance.profile: get_governance_config

Exports (Provides):
    - handle_policy_failure(error, context) -> FailureDecision
    - FailureMode: Enum of failure modes
    - FailureDecision: Decision when failure occurs

Wiring Points:
    - Called from: prevention_engine.py when evaluation fails
    - Logs: All failures for audit

Acceptance Criteria:
    - [x] AC-035-01: Default is fail-closed
    - [x] AC-035-02: Missing policy = blocked
    - [x] AC-035-03: Evaluation error = blocked
    - [x] AC-035-04: All failures logged
    - [x] AC-035-05: No hardcoded fail-open
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict
from datetime import datetime, timezone
import logging

logger = logging.getLogger("nova.policy.failure_mode_handler")


class FailureMode(str, Enum):
    """Failure mode for policy evaluation."""
    FAIL_CLOSED = "fail_closed"  # Block on failure (DEFAULT)
    FAIL_OPEN = "fail_open"      # Allow on failure (DANGEROUS - requires explicit config)
    FAIL_WARN = "fail_warn"      # Allow with warning (audit trail required)


class FailureType(str, Enum):
    """Type of failure encountered."""
    MISSING_POLICY = "missing_policy"
    EVALUATION_ERROR = "evaluation_error"
    TIMEOUT = "timeout"
    INVALID_CONTEXT = "invalid_context"
    ENGINE_UNAVAILABLE = "engine_unavailable"
    UNKNOWN = "unknown"


@dataclass
class FailureDecision:
    """Decision made when failure occurs."""
    action: str  # STOP, WARN, CONTINUE
    failure_type: FailureType
    failure_mode: FailureMode
    reason: str
    should_block: bool
    audit_required: bool
    timestamp: str


# Default failure mode - MUST be fail-closed
DEFAULT_FAILURE_MODE = FailureMode.FAIL_CLOSED


def get_failure_mode() -> FailureMode:
    """
    Get configured failure mode.

    Returns:
        FailureMode from governance config, defaulting to FAIL_CLOSED
    """
    try:
        from app.hoc.cus.hoc_spine.authority.profile_policy_mode import get_governance_config

        config = get_governance_config()

        # Check if custom failure mode is configured
        if hasattr(config, 'default_failure_mode'):
            mode_str = config.default_failure_mode
            if mode_str:
                try:
                    return FailureMode(mode_str.lower())
                except ValueError:
                    logger.warning("failure_mode.invalid_config", extra={
                        "configured": mode_str,
                        "defaulting_to": DEFAULT_FAILURE_MODE.value,
                    })

    except Exception as e:
        logger.warning("failure_mode.config_error", extra={
            "error": str(e),
            "defaulting_to": DEFAULT_FAILURE_MODE.value,
        })

    return DEFAULT_FAILURE_MODE


def handle_policy_failure(
    error: Optional[Exception],
    context: Dict[str, Any],
    failure_type: FailureType = FailureType.UNKNOWN,
) -> FailureDecision:
    """
    Handle a policy evaluation failure.

    This function determines what action to take when policy evaluation
    fails. The default is FAIL-CLOSED (block the action).

    Args:
        error: The exception that occurred, if any
        context: Evaluation context (run_id, tenant_id, etc.)
        failure_type: Type of failure

    Returns:
        FailureDecision with action to take
    """
    failure_mode = get_failure_mode()
    timestamp = datetime.now(timezone.utc).isoformat()

    error_msg = str(error) if error else "Unknown error"
    run_id = context.get('run_id', 'unknown')
    tenant_id = context.get('tenant_id', 'unknown')

    # Log the failure
    logger.error("policy_failure.occurred", extra={
        "run_id": run_id,
        "tenant_id": tenant_id,
        "failure_type": failure_type.value,
        "failure_mode": failure_mode.value,
        "error": error_msg,
    })

    # Determine action based on failure mode
    if failure_mode == FailureMode.FAIL_CLOSED:
        decision = FailureDecision(
            action="STOP",
            failure_type=failure_type,
            failure_mode=failure_mode,
            reason=f"Fail-closed: {failure_type.value} - {error_msg}",
            should_block=True,
            audit_required=True,
            timestamp=timestamp,
        )

    elif failure_mode == FailureMode.FAIL_WARN:
        decision = FailureDecision(
            action="WARN",
            failure_type=failure_type,
            failure_mode=failure_mode,
            reason=f"Fail-warn: {failure_type.value} - {error_msg}",
            should_block=False,
            audit_required=True,  # MUST audit when allowing despite failure
            timestamp=timestamp,
        )

    elif failure_mode == FailureMode.FAIL_OPEN:
        # DANGEROUS: Only use if explicitly configured
        logger.warning("policy_failure.fail_open_used", extra={
            "run_id": run_id,
            "tenant_id": tenant_id,
            "failure_type": failure_type.value,
            "warning": "FAIL_OPEN is dangerous - action allowed despite failure",
        })
        decision = FailureDecision(
            action="CONTINUE",
            failure_type=failure_type,
            failure_mode=failure_mode,
            reason=f"Fail-open (DANGEROUS): {failure_type.value} - {error_msg}",
            should_block=False,
            audit_required=True,  # MUST audit when using fail-open
            timestamp=timestamp,
        )

    else:
        # Unknown mode - default to fail-closed
        decision = FailureDecision(
            action="STOP",
            failure_type=failure_type,
            failure_mode=FailureMode.FAIL_CLOSED,
            reason=f"Unknown failure mode, defaulting to fail-closed: {error_msg}",
            should_block=True,
            audit_required=True,
            timestamp=timestamp,
        )

    # Log the decision
    logger.info("policy_failure.decision", extra={
        "run_id": run_id,
        "action": decision.action,
        "should_block": decision.should_block,
        "failure_mode": decision.failure_mode.value,
    })

    return decision


def handle_missing_policy(context: Dict[str, Any]) -> FailureDecision:
    """
    Handle case where no policy exists for the action.

    By default, missing policy = BLOCK (fail-closed).

    Args:
        context: Evaluation context

    Returns:
        FailureDecision
    """
    return handle_policy_failure(
        error=None,
        context=context,
        failure_type=FailureType.MISSING_POLICY,
    )


def handle_evaluation_error(error: Exception, context: Dict[str, Any]) -> FailureDecision:
    """
    Handle policy evaluation error.

    Args:
        error: The exception that occurred
        context: Evaluation context

    Returns:
        FailureDecision
    """
    return handle_policy_failure(
        error=error,
        context=context,
        failure_type=FailureType.EVALUATION_ERROR,
    )


def handle_timeout(context: Dict[str, Any], timeout_seconds: float) -> FailureDecision:
    """
    Handle policy evaluation timeout.

    Args:
        context: Evaluation context
        timeout_seconds: How long before timeout

    Returns:
        FailureDecision
    """
    return handle_policy_failure(
        error=Exception(f"Policy evaluation timed out after {timeout_seconds}s"),
        context=context,
        failure_type=FailureType.TIMEOUT,
    )
