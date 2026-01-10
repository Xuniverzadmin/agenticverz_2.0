# Layer: L8 — Catalyst / Meta
# Product: system-wide (SDSR testing infrastructure)
# Temporal:
#   Trigger: worker (skill execution)
#   Execution: sync
# Role: SDSR failure trigger skill for controlled test failures
# Callers: Worker runtime (via plan execution)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-370 (Scenario-Driven System Realization), SDSR-E2E-003

"""
SDSR Failure Trigger Skill

PURPOSE:
    This skill enables SDSR scenarios to trigger controlled failures
    that the worker will recognize and process correctly.

    Instead of using non-existent fake skills, this skill:
    - Is registered in the real skill registry
    - Raises exceptions that map to specific failure codes
    - Enables IncidentEngine to receive the correct error_code

USAGE:
    Plan step:
    {
        "skill": "__sdsr_fail_trigger__",
        "params": {
            "error_code": "BUDGET_EXCEEDED",
            "error_message": "Test: Budget limit exceeded"
        }
    }

SUPPORTED ERROR CODES:
    - BUDGET_EXCEEDED → Raises BudgetExceededError
    - EXECUTION_TIMEOUT → Raises TimeoutError
    - STEP_FAILURE → Raises RuntimeError
    - SKILL_ERROR → Raises RuntimeError

CONTRACT:
    This skill ALWAYS fails. Success is a bug.
    The failure type is determined by error_code parameter.
"""

import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .executor import BudgetExceededError, SkillExecutionError
from .registry import skill

logger = logging.getLogger("nova.skills.sdsr_fail_trigger")


class SDSRFailTriggerInput(BaseModel):
    """Input schema for SDSR fail trigger skill."""

    error_code: str = Field(
        description="Failure code to trigger (BUDGET_EXCEEDED, EXECUTION_TIMEOUT, etc.)"
    )
    error_message: Optional[str] = Field(
        default=None, description="Custom error message (optional)"
    )
    delay_ms: Optional[int] = Field(
        default=0, description="Delay in milliseconds before failing (for timeout simulation)"
    )


class SDSRFailTriggerOutput(BaseModel):
    """Output schema - never used since this skill always fails."""

    status: str = Field(default="never_returned")


class SDSRFailError(SkillExecutionError):
    """SDSR controlled failure with specific error code."""

    def __init__(self, error_code: str, message: str, is_retryable: bool = False):
        super().__init__(
            message=message,
            skill_name="__sdsr_fail_trigger__",
            is_retryable=is_retryable,
        )
        self.error_code = error_code


@skill(
    name="__sdsr_fail_trigger__",
    input_schema=SDSRFailTriggerInput,
    output_schema=SDSRFailTriggerOutput,
    tags=["sdsr", "testing", "internal"],
)
class SDSRFailTriggerSkill:
    """SDSR Failure Trigger Skill.

    This skill exists ONLY for SDSR testing. It triggers controlled
    failures that the system will process as real failures.

    NEVER use this skill in production workflows.
    """

    VERSION = "1.0.0"
    DESCRIPTION = "SDSR testing skill that triggers controlled failures"

    def __init__(self, **_kwargs):
        # SDSR fail trigger skill requires no configuration
        pass

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the failure trigger.

        This method ALWAYS raises an exception. It never returns successfully.
        The exception type is determined by the error_code parameter.

        Args:
            params: Must contain 'error_code', optionally 'error_message' and 'delay_ms'

        Raises:
            Various exceptions based on error_code
        """
        error_code = params.get("error_code", "UNKNOWN")
        error_message = params.get("error_message") or f"SDSR triggered failure: {error_code}"
        delay_ms = params.get("delay_ms", 0)

        logger.info(
            f"SDSR fail trigger activated: error_code={error_code}, delay_ms={delay_ms}"
        )

        # Optional delay for timeout simulation
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        # Raise the appropriate exception based on error_code
        if error_code == "BUDGET_EXCEEDED":
            # Import here to avoid circular dependency
            from ..observability.cost_tracker import CostEnforcementResult

            # Use the enum value for budget exceeded
            raise BudgetExceededError(
                message=error_message,
                skill_name="__sdsr_fail_trigger__",
                enforcement_result=CostEnforcementResult.BUDGET_EXCEEDED,
                tenant_id="sdsr-tenant",
                estimated_cost_cents=1000,
            )

        elif error_code == "EXECUTION_TIMEOUT":
            # TimeoutError maps to EXECUTION_TIMEOUT in failure catalog
            raise TimeoutError(error_message)

        elif error_code == "STEP_FAILURE":
            # Generic step failure
            raise SDSRFailError(
                error_code="STEP_FAILURE",
                message=error_message,
                is_retryable=False,
            )

        elif error_code == "SKILL_ERROR":
            # Skill error
            raise SDSRFailError(
                error_code="SKILL_ERROR",
                message=error_message,
                is_retryable=True,
            )

        elif error_code == "RETRY_EXHAUSTED":
            # For testing retry behavior
            raise SDSRFailError(
                error_code="RETRY_EXHAUSTED",
                message=error_message,
                is_retryable=False,
            )

        else:
            # Default: raise as unknown error
            raise SDSRFailError(
                error_code=error_code,
                message=error_message,
                is_retryable=False,
            )


# SDSR test helper - verify the skill is registered
def verify_sdsr_skill_registered() -> bool:
    """Verify the SDSR fail trigger skill is registered."""
    from .registry import skill_exists

    return skill_exists("__sdsr_fail_trigger__")
