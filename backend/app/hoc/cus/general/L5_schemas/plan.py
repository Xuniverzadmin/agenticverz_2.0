# Layer: L5 — Domain Engine (Schema)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Plan API schemas (pure Pydantic DTOs)
# Callers: API routes, engines
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB), sqlalchemy
# Reference: PIN-470, API Schemas
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure Pydantic schemas, no boundary crossing

# Plan Schemas
# Pydantic models for Plan and PlanStep definitions

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.hoc.cus.general.L5_utils.time import utc_now as _utc_now


from .retry import RetryPolicy


class OnErrorPolicy(str, Enum):
    """What to do when a step fails."""

    ABORT = "abort"  # Stop plan execution immediately
    CONTINUE = "continue"  # Continue with next step
    RETRY = "retry"  # Retry according to retry policy
    FALLBACK = "fallback"  # Try fallback skill if specified


class StepStatus(str, Enum):
    """Execution status of a plan step."""

    PENDING = "pending"  # Not yet started
    RUNNING = "running"  # Currently executing
    SUCCEEDED = "succeeded"  # Completed successfully
    FAILED = "failed"  # Failed (terminal)
    SKIPPED = "skipped"  # Skipped due to condition
    RETRYING = "retrying"  # Failed, retrying


class ConditionOperator(str, Enum):
    """Operators for step conditions."""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    CONTAINS = "contains"
    MATCHES = "matches"  # regex match


class StepCondition(BaseModel):
    """Condition for conditional step execution.

    Allows steps to be skipped based on previous step outputs.
    """

    step_id: str = Field(description="Step ID to check output from")
    field: str = Field(description="Field path in step output (dot notation)")
    operator: ConditionOperator = Field(description="Comparison operator")
    value: Optional[Any] = Field(default=None, description="Value to compare against")


class PlanStep(BaseModel):
    """A single step in an execution plan.

    Defines what skill to run, with what parameters,
    dependencies, conditions, and error handling.
    """

    step_id: str = Field(
        description="Unique step identifier within plan",
        pattern=r"^[a-z0-9_-]+$",
        examples=["s1", "fetch_data", "step-01"],
    )
    skill: str = Field(description="Skill name to execute", examples=["http_call", "llm_invoke", "postgres_query"])
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to skill")
    description: Optional[str] = Field(default=None, description="Human-readable step description")

    # Dependencies and ordering
    depends_on: Optional[List[str]] = Field(default=None, description="Step IDs that must complete before this step")

    # Conditional execution
    condition: Optional[StepCondition] = Field(default=None, description="Condition for executing this step")

    # Error handling
    on_error: OnErrorPolicy = Field(default=OnErrorPolicy.ABORT, description="What to do if step fails")
    retry_policy: Optional[RetryPolicy] = Field(
        default=None, description="Retry policy (uses default if not specified)"
    )
    fallback_skill: Optional[str] = Field(
        default=None, description="Alternative skill if primary fails (requires on_error=fallback)"
    )
    fallback_params: Optional[Dict[str, Any]] = Field(default=None, description="Parameters for fallback skill")

    # Output handling
    output_key: Optional[str] = Field(
        default=None, description="Key to store output in context (for referencing in later steps)"
    )

    # Execution state (set during runtime)
    status: StepStatus = Field(default=StepStatus.PENDING, description="Current execution status")
    started_at: Optional[datetime] = Field(default=None, description="When step started")
    completed_at: Optional[datetime] = Field(default=None, description="When step completed")
    attempts: int = Field(default=0, ge=0, description="Number of execution attempts")
    output: Optional[Dict[str, Any]] = Field(default=None, description="Step output after execution")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "step_id": "fetch_page",
                "skill": "http_call",
                "params": {"url": "https://example.com", "method": "GET"},
                "description": "Fetch the example page",
                "on_error": "retry",
                "retry_policy": {"max_attempts": 3, "backoff_strategy": "exponential"},
            }
        }
    )

    @field_validator("fallback_skill")
    @classmethod
    def validate_fallback(cls, v, info):
        """Validate fallback_skill requires on_error=fallback."""
        if v is not None:
            on_error = info.data.get("on_error")
            if on_error != OnErrorPolicy.FALLBACK:
                raise ValueError("fallback_skill requires on_error='fallback'")
        return v


class PlanMetadata(BaseModel):
    """Metadata about the plan and how it was created."""

    planner: str = Field(description="Planner that created this plan")
    planner_version: str = Field(description="Version of the planner")
    created_at: datetime = Field(default_factory=_utc_now, description="When plan was created")
    model: Optional[str] = Field(default=None, description="LLM model used for planning (if applicable)")
    reasoning: Optional[str] = Field(default=None, description="Planner's reasoning/explanation")
    estimated_duration_seconds: Optional[float] = Field(
        default=None, ge=0, description="Estimated total execution time"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class Plan(BaseModel):
    """Complete execution plan for achieving a goal.

    The plan is the contract between planner and executor.
    It defines what steps to run and in what order.
    """

    plan_id: str = Field(description="Unique plan identifier")
    goal: str = Field(description="The goal this plan achieves")
    steps: List[PlanStep] = Field(min_length=1, description="Ordered list of steps to execute")
    metadata: PlanMetadata = Field(description="Plan metadata")

    # Default policies (can be overridden per-step)
    default_retry_policy: RetryPolicy = Field(default_factory=RetryPolicy, description="Default retry policy for steps")
    default_on_error: OnErrorPolicy = Field(default=OnErrorPolicy.ABORT, description="Default error handling policy")

    # Context for step interpolation
    context: Dict[str, Any] = Field(default_factory=dict, description="Initial context variables")

    # Execution state
    status: StepStatus = Field(default=StepStatus.PENDING, description="Overall plan status")
    current_step_id: Optional[str] = Field(default=None, description="Currently executing step ID")
    started_at: Optional[datetime] = Field(default=None, description="When execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When execution completed")
    duration_seconds: Optional[float] = Field(default=None, ge=0, description="Total execution time")

    @field_validator("steps")
    @classmethod
    def validate_step_ids_unique(cls, v: List[PlanStep]) -> List[PlanStep]:
        """Ensure all step IDs are unique."""
        step_ids = [step.step_id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Step IDs must be unique within a plan")
        return v

    @field_validator("steps")
    @classmethod
    def validate_dependencies(cls, v: List[PlanStep]) -> List[PlanStep]:
        """Ensure dependencies reference valid step IDs."""
        step_ids = {step.step_id for step in v}
        for step in v:
            if step.depends_on:
                for dep in step.depends_on:
                    if dep not in step_ids:
                        raise ValueError(f"Step '{step.step_id}' depends on unknown step '{dep}'")
                    if dep == step.step_id:
                        raise ValueError(f"Step '{step.step_id}' cannot depend on itself")
        return v

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute (dependencies met)."""
        completed_ids = {
            step.step_id for step in self.steps if step.status in (StepStatus.SUCCEEDED, StepStatus.SKIPPED)
        }
        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            if step.depends_on:
                if all(dep in completed_ids for dep in step.depends_on):
                    ready.append(step)
            else:
                ready.append(step)
        return ready

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plan_id": "plan-abc123",
                "goal": "Fetch a webpage and summarize it",
                "steps": [
                    {
                        "step_id": "fetch",
                        "skill": "http_call",
                        "params": {"url": "https://example.com"},
                        "output_key": "page",
                    },
                    {
                        "step_id": "summarize",
                        "skill": "llm_invoke",
                        "params": {"messages": [{"role": "user", "content": "Summarize: {{page.body}}"}]},
                        "depends_on": ["fetch"],
                    },
                ],
                "metadata": {"planner": "anthropic", "planner_version": "1.0.0"},
            }
        }
    )
