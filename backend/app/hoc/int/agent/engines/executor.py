# Layer: L2 — API
# AUDIENCE: CUSTOMER
# Role: Skill execution with validation and evidence capture
# Product: system-wide
# Temporal:
#   Trigger: worker (via runner.py)
#   Execution: async
# Authority: Skill invocation, validation, evidence capture (NO step advancement)
# Callers: runner.py (passes cursor.context)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: Evidence Architecture v1.1
# capability_id: CAP-016


"""
Skill Executor - Validation wrapper for skill execution at the runner boundary.

Evidence Architecture v1.1:
- Receives ExecutionContext from runner (via cursor.context)
- Context is READ-ONLY - executor cannot advance steps
- Captures Activity (B) and Provider (G) evidence using context
- Step advancement is runner's responsibility via ExecutionCursor
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from pydantic import ValidationError

from app.observability.cost_tracker import (
    CostEnforcementResult,
    get_cost_tracker,
)
from app.schemas.plan import PlanStep, StepStatus
from .registry import get_skill_entry

# Evidence Architecture v1.1: Activity and Provider evidence capture
# ExecutionContext is received as read-only snapshot from runner's cursor.context
if TYPE_CHECKING:
    from app.core.execution_context import ExecutionContext

logger = logging.getLogger("nova.skills.executor")


class SkillExecutionError(Exception):
    """Error during skill execution."""

    def __init__(
        self,
        message: str,
        skill_name: str,
        step_id: Optional[str] = None,
        is_retryable: bool = True,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.skill_name = skill_name
        self.step_id = step_id
        self.is_retryable = is_retryable
        self.original_error = original_error


class SkillValidationError(SkillExecutionError):
    """Input/output validation failed."""

    def __init__(
        self,
        message: str,
        skill_name: str,
        validation_errors: list,
        is_input: bool = True,
    ):
        super().__init__(
            message=message,
            skill_name=skill_name,
            is_retryable=False,  # Validation errors are not retryable
        )
        self.validation_errors = validation_errors
        self.is_input = is_input


class BudgetExceededError(SkillExecutionError):
    """Budget limit exceeded - skill execution blocked.

    This is a HARD ceiling that cannot be bypassed. The request must be
    rejected to protect cost constraints.
    """

    def __init__(
        self,
        message: str,
        skill_name: str,
        enforcement_result: CostEnforcementResult,
        tenant_id: str,
        estimated_cost_cents: float,
        step_id: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            skill_name=skill_name,
            step_id=step_id,
            is_retryable=False,  # Budget errors are NOT retryable
        )
        self.enforcement_result = enforcement_result
        self.tenant_id = tenant_id
        self.estimated_cost_cents = estimated_cost_cents


class SkillExecutor:
    """Executes skills with input/output validation.

    This is the boundary layer between the runner and skills.
    It handles:
    - Cost enforcement (hard ceilings)
    - Input validation against skill schema
    - Skill instantiation via factory
    - Output validation
    - Error classification (retryable vs permanent)
    - Execution timing and logging
    """

    # Estimated cost per skill type (in cents)
    # Used for pre-execution budget checks
    SKILL_COST_ESTIMATES = {
        "llm_invoke": 5.0,  # ~5c per LLM call (varies by model)
        "http_call": 0.0,  # No cost
        "json_transform": 0.0,  # No cost
        "postgres_query": 0.0,  # No cost
        "calendar_write": 0.0,  # No cost
    }
    DEFAULT_COST_ESTIMATE = 1.0  # 1c default for unknown skills

    def __init__(
        self,
        validate_input: bool = True,
        validate_output: bool = True,
        strict_mode: bool = False,
        enforce_budget: bool = True,
    ):
        """Initialize executor.

        Args:
            validate_input: Whether to validate input params
            validate_output: Whether to validate output
            strict_mode: If True, validation errors are fatal
            enforce_budget: If True, check cost limits before execution
        """
        self.validate_input = validate_input
        self.validate_output = validate_output
        self.strict_mode = strict_mode
        self.enforce_budget = enforce_budget
        self._cost_tracker = get_cost_tracker()

    async def execute_step(
        self,
        step: PlanStep,
        context: Optional[Dict[str, Any]] = None,
        skill_config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], StepStatus]:
        """Execute a plan step.

        Args:
            step: The plan step to execute
            context: Execution context with outputs from previous steps
            skill_config: Configuration for skill instantiation

        Returns:
            Tuple of (result dict, step status)

        Raises:
            SkillExecutionError: If execution fails
            SkillValidationError: If validation fails
        """
        skill_name = step.skill
        params = self._interpolate_params(step.params, context or {})

        return await self.execute(
            skill_name=skill_name,
            params=params,
            step_id=step.step_id,
            skill_config=skill_config,
        )

    async def execute(
        self,
        skill_name: str,
        params: Dict[str, Any],
        step_id: Optional[str] = None,
        skill_config: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        execution_context: Optional["ExecutionContext"] = None,
    ) -> Tuple[Dict[str, Any], StepStatus]:
        """Execute a skill with validation.

        Args:
            skill_name: Name of skill to execute
            params: Parameters to pass to skill
            step_id: Optional step ID for logging
            skill_config: Configuration for skill
            tenant_id: Tenant ID for cost tracking (required if enforce_budget=True)
            workflow_id: Workflow ID for workflow-level budget limits
            execution_context: Read-only ExecutionContext from cursor.context (Evidence Architecture v1.1)
                              Used for Activity (B) and Provider (G) evidence capture.
                              Executor MUST NOT advance steps - that's runner's responsibility.

        Returns:
            Tuple of (result dict, step status)

        Raises:
            BudgetExceededError: If cost limits would be exceeded
            SkillExecutionError: If execution fails
            SkillValidationError: If validation fails
        """
        start_time = time.time()
        started_at = datetime.now(timezone.utc)

        # Estimate cost for this skill
        estimated_cost = self.SKILL_COST_ESTIMATES.get(skill_name, self.DEFAULT_COST_ESTIMATE)

        # HARD COST ENFORCEMENT - Check budget BEFORE execution
        if self.enforce_budget and tenant_id:
            result, reason = self._cost_tracker.check_can_spend(
                tenant_id=tenant_id,
                estimated_cost_cents=estimated_cost,
                workflow_id=workflow_id,
            )

            if result == CostEnforcementResult.BUDGET_EXCEEDED:
                logger.warning(
                    "skill_execution_blocked_budget",
                    extra={
                        "skill": skill_name,
                        "step_id": step_id,
                        "tenant_id": tenant_id,
                        "workflow_id": workflow_id,
                        "estimated_cost_cents": estimated_cost,
                        "reason": reason,
                    },
                )
                raise BudgetExceededError(
                    message=f"Budget exceeded: {reason}",
                    skill_name=skill_name,
                    enforcement_result=result,
                    tenant_id=tenant_id,
                    estimated_cost_cents=estimated_cost,
                    step_id=step_id,
                )

            if result == CostEnforcementResult.REQUEST_TOO_EXPENSIVE:
                logger.warning(
                    "skill_execution_blocked_too_expensive",
                    extra={
                        "skill": skill_name,
                        "step_id": step_id,
                        "tenant_id": tenant_id,
                        "estimated_cost_cents": estimated_cost,
                        "reason": reason,
                    },
                )
                raise BudgetExceededError(
                    message=f"Request too expensive: {reason}",
                    skill_name=skill_name,
                    enforcement_result=result,
                    tenant_id=tenant_id,
                    estimated_cost_cents=estimated_cost,
                    step_id=step_id,
                )

            if result == CostEnforcementResult.BUDGET_WARNING:
                logger.info(
                    "skill_execution_budget_warning",
                    extra={
                        "skill": skill_name,
                        "step_id": step_id,
                        "tenant_id": tenant_id,
                        "reason": reason,
                    },
                )

        logger.info(
            "skill_execution_start",
            extra={
                "skill": skill_name,
                "step_id": step_id,
                "params_keys": list(params.keys()),
            },
        )

        # Get skill entry from registry
        entry = get_skill_entry(skill_name)
        if not entry:
            raise SkillExecutionError(
                message=f"Skill not found: {skill_name}",
                skill_name=skill_name,
                step_id=step_id,
                is_retryable=False,
            )

        # Validate input
        validated_params = params
        if self.validate_input and entry.input_schema:
            validated_params = self._validate_input(skill_name, params, entry.input_schema)

        # Create skill instance
        try:
            instance = entry.create_instance(skill_config)
        except Exception as e:
            raise SkillExecutionError(
                message=f"Failed to instantiate skill: {e}",
                skill_name=skill_name,
                step_id=step_id,
                is_retryable=False,
                original_error=e,
            )

        # Evidence Architecture v1.1: Capture B (Activity) evidence before LLM/tool call
        # Context is read-only from cursor.context - we use it, we don't mutate it
        prompt_fingerprint = None
        prompt_token_estimate = 0
        if execution_context and skill_name == "llm_invoke":
            try:
                from app.hoc.cus.logs.L6_drivers.capture_driver import capture_activity_evidence

                # Compute prompt fingerprint for LLM calls
                prompt_text = str(validated_params.get("prompt", ""))
                prompt_fingerprint = hashlib.sha256(prompt_text.encode()).hexdigest()[:64]

                # Estimate token count (rough: ~4 chars per token)
                prompt_token_estimate = len(prompt_text) // 4

                # Extract model from config or params
                model_name = validated_params.get("model") or (skill_config.get("model", "unknown") if skill_config else "unknown")

                capture_activity_evidence(
                    execution_context,
                    skill_id=skill_name,
                    model_name=model_name,
                    prompt_fingerprint=prompt_fingerprint,
                    prompt_token_length=prompt_token_estimate,
                )
                logger.debug(
                    "activity_evidence_captured",
                    extra={"run_id": execution_context.run_id, "skill": skill_name},
                )
            except Exception as e:
                logger.warning(
                    "activity_evidence_capture_failed",
                    extra={"run_id": execution_context.run_id if execution_context else None, "error": str(e)},
                )

        # Execute skill
        try:
            result = await instance.execute(validated_params)
        except Exception as e:
            duration = time.time() - start_time
            logger.exception(
                "skill_execution_failed",
                extra={
                    "skill": skill_name,
                    "step_id": step_id,
                    "duration": round(duration, 3),
                    "error": str(e)[:200],
                },
            )
            raise SkillExecutionError(
                message=f"Skill execution failed: {e}",
                skill_name=skill_name,
                step_id=step_id,
                is_retryable=self._is_retryable_error(e),
                original_error=e,
            )

        # Validate output
        if self.validate_output and entry.output_schema:
            result = self._validate_output(skill_name, result, entry.output_schema)

        duration = time.time() - start_time
        completed_at = datetime.now(timezone.utc)

        # Determine status from result
        status = self._determine_status(result)

        logger.info(
            "skill_execution_complete",
            extra={
                "skill": skill_name,
                "step_id": step_id,
                "status": status.value,
                "duration": round(duration, 3),
            },
        )

        # Evidence Architecture v1.1: Capture G (Provider) evidence after LLM response
        # Context is read-only from cursor.context - we use it, we don't mutate it
        if execution_context and skill_name == "llm_invoke":
            try:
                from app.hoc.cus.logs.L6_drivers.capture_driver import capture_provider_evidence

                # Extract provider info from result
                input_tokens = result.get("input_tokens", 0)
                output_tokens = result.get("output_tokens", 0)
                model_name = result.get("model") or validated_params.get("model", "unknown")
                provider_latency_ms = result.get("latency_ms", int(duration * 1000))

                # Determine provider from model name
                provider_name = "anthropic" if "claude" in model_name.lower() else "openai"

                capture_provider_evidence(
                    execution_context,
                    provider_name=provider_name,
                    model_name=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    provider_latency_ms=provider_latency_ms,
                )
                logger.debug(
                    "provider_evidence_captured",
                    extra={
                        "run_id": execution_context.run_id,
                        "provider": provider_name,
                        "tokens": input_tokens + output_tokens,
                    },
                )
            except Exception as e:
                logger.warning(
                    "provider_evidence_capture_failed",
                    extra={"run_id": execution_context.run_id if execution_context else None, "error": str(e)},
                )

        # Add execution metadata to result
        result["_meta"] = {
            "skill": skill_name,
            "step_id": step_id,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": round(duration, 3),
        }

        return result, status

    def _validate_input(
        self,
        skill_name: str,
        params: Dict[str, Any],
        schema: type,
    ) -> Dict[str, Any]:
        """Validate input parameters against schema.

        Args:
            skill_name: Skill name for error context
            params: Input parameters
            schema: Pydantic model class

        Returns:
            Validated parameters dict

        Raises:
            SkillValidationError: If validation fails in strict mode
        """
        try:
            validated = schema(**params)
            return validated.model_dump()
        except ValidationError as e:
            errors = e.errors()
            error_summary = "; ".join(f"{err['loc']}: {err['msg']}" for err in errors[:3])

            if self.strict_mode:
                raise SkillValidationError(
                    message=f"Input validation failed: {error_summary}",
                    skill_name=skill_name,
                    validation_errors=errors,
                    is_input=True,
                )

            logger.warning(
                "skill_input_validation_warning",
                extra={
                    "skill": skill_name,
                    "errors": error_summary,
                    "error_count": len(errors),
                },
            )
            # Return original params if not strict
            return params

    def _validate_output(
        self,
        skill_name: str,
        result: Dict[str, Any],
        schema: type,
    ) -> Dict[str, Any]:
        """Validate output against schema.

        Args:
            skill_name: Skill name for error context
            result: Skill output
            schema: Pydantic model class

        Returns:
            Validated result dict

        Raises:
            SkillValidationError: If validation fails in strict mode
        """
        try:
            # Try to construct output model (may need to map fields)
            validated = schema(**result)
            return validated.model_dump()
        except ValidationError as e:
            errors = e.errors()
            error_summary = "; ".join(f"{err['loc']}: {err['msg']}" for err in errors[:3])

            if self.strict_mode:
                raise SkillValidationError(
                    message=f"Output validation failed: {error_summary}",
                    skill_name=skill_name,
                    validation_errors=errors,
                    is_input=False,
                )

            logger.warning(
                "skill_output_validation_warning",
                extra={
                    "skill": skill_name,
                    "errors": error_summary,
                    "error_count": len(errors),
                },
            )
            # Return original result if not strict
            return result

    def _interpolate_params(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Interpolate context values into parameters.

        Supports {{step_id.field}} syntax for referencing
        outputs from previous steps.

        Args:
            params: Original parameters
            context: Context with step outputs

        Returns:
            Interpolated parameters
        """
        import re

        def replace_var(match: re.Match) -> str:
            path = match.group(1)
            parts = path.split(".")
            value = context
            try:
                for part in parts:
                    if isinstance(value, dict):
                        value = value[part]
                    else:
                        return match.group(0)  # Can't resolve, keep original
                return str(value)
            except (KeyError, TypeError):
                return match.group(0)  # Can't resolve, keep original

        def interpolate_value(v: Any) -> Any:
            if isinstance(v, str):
                return re.sub(r"\{\{([^}]+)\}\}", replace_var, v)
            elif isinstance(v, dict):
                return {k: interpolate_value(vv) for k, vv in v.items()}
            elif isinstance(v, list):
                return [interpolate_value(item) for item in v]
            return v

        return interpolate_value(params)

    def _determine_status(self, result: Dict[str, Any]) -> StepStatus:
        """Determine step status from result.

        Args:
            result: Skill execution result

        Returns:
            StepStatus enum value
        """
        # Check for explicit status in result
        status_str = result.get("status") or result.get("result", {}).get("status")

        if status_str == "ok":
            return StepStatus.SUCCEEDED
        elif status_str == "error":
            return StepStatus.FAILED
        elif status_str == "stubbed":
            return StepStatus.SKIPPED

        # Default to succeeded if no error
        if "error" in result and result["error"]:
            return StepStatus.FAILED

        return StepStatus.SUCCEEDED

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable.

        Args:
            error: The exception that occurred

        Returns:
            True if error should be retried
        """
        # Non-retryable error types
        non_retryable = (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            SkillValidationError,
            BudgetExceededError,
        )

        if isinstance(error, non_retryable):
            return False

        # Check error message for non-retryable patterns
        error_msg = str(error).lower()
        non_retryable_patterns = [
            "invalid",
            "not found",
            "permission denied",
            "unauthorized",
            "forbidden",
            "bad request",
        ]

        for pattern in non_retryable_patterns:
            if pattern in error_msg:
                return False

        # Default to retryable
        return True


# Singleton executor instance with default settings
default_executor = SkillExecutor(
    validate_input=True,
    validate_output=False,  # Output validation optional for now
    strict_mode=False,
    enforce_budget=True,  # Cost enforcement enabled by default
)


async def execute_skill(
    skill_name: str,
    params: Dict[str, Any],
    step_id: Optional[str] = None,
    skill_config: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], StepStatus]:
    """Convenience function to execute a skill with default executor.

    Args:
        skill_name: Name of skill to execute
        params: Parameters to pass to skill
        step_id: Optional step ID for logging
        skill_config: Configuration for skill
        tenant_id: Tenant ID for cost tracking
        workflow_id: Workflow ID for workflow-level budget limits

    Returns:
        Tuple of (result dict, step status)

    Raises:
        BudgetExceededError: If cost limits would be exceeded
    """
    return await default_executor.execute(
        skill_name=skill_name,
        params=params,
        step_id=step_id,
        skill_config=skill_config,
        tenant_id=tenant_id,
        workflow_id=workflow_id,
    )
