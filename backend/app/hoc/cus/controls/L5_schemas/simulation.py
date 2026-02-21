# capability_id: CAP-009
# Layer: L5 — Domain Schema
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Limit simulation request/response schemas
# Callers: api/limits/simulate.py, services/limits/simulation_service.py
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-LIM-04

"""
Limit Simulation Schemas (PIN-LIM-04)

Request and response models for pre-execution limit checks.
The simulation endpoint allows dry-run verification against all limits
before actually executing a run.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SimulationDecision(str, Enum):
    """Simulation outcome decision."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"


class MessageCode(str, Enum):
    """Standardized message codes (no free-text messages)."""
    # Quota limits
    DAILY_RUN_LIMIT_EXCEEDED = "DAILY_RUN_LIMIT_EXCEEDED"
    MONTHLY_TOKEN_LIMIT_EXCEEDED = "MONTHLY_TOKEN_LIMIT_EXCEEDED"
    CONCURRENT_RUN_LIMIT_EXCEEDED = "CONCURRENT_RUN_LIMIT_EXCEEDED"
    # Cost budgets
    DAILY_COST_BUDGET_EXCEEDED = "DAILY_COST_BUDGET_EXCEEDED"
    MONTHLY_COST_BUDGET_EXCEEDED = "MONTHLY_COST_BUDGET_EXCEEDED"
    FEATURE_COST_BUDGET_EXCEEDED = "FEATURE_COST_BUDGET_EXCEEDED"
    USER_COST_BUDGET_EXCEEDED = "USER_COST_BUDGET_EXCEEDED"
    # Policy limits
    POLICY_LIMIT_BREACHED = "POLICY_LIMIT_BREACHED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    THRESHOLD_LIMIT_EXCEEDED = "THRESHOLD_LIMIT_EXCEEDED"
    # Worker limits
    WORKER_DAILY_LIMIT_EXCEEDED = "WORKER_DAILY_LIMIT_EXCEEDED"
    WORKER_TOKEN_LIMIT_EXCEEDED = "WORKER_TOKEN_LIMIT_EXCEEDED"
    # Override-related
    OVERRIDE_APPLIED = "OVERRIDE_APPLIED"
    OVERRIDE_EXPIRED = "OVERRIDE_EXPIRED"
    # General
    LIMIT_APPROACHING = "LIMIT_APPROACHING"


class LimitSimulationRequest(BaseModel):
    """Request model for limit simulation (pre-execution check)."""

    # Required context
    tenant_id: Optional[str] = Field(
        default=None,
        description="Tenant ID (extracted from auth if not provided)",
    )
    worker_id: Optional[str] = Field(
        default=None,
        description="Worker ID for worker-specific limits",
    )
    # Execution intent
    estimated_tokens: int = Field(
        ...,
        ge=0,
        description="Estimated token usage for this run",
    )
    estimated_cost_cents: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated cost in cents (optional - computed if not provided)",
    )
    run_count: int = Field(
        default=1,
        ge=1,
        description="Number of runs being requested",
    )
    concurrency_delta: int = Field(
        default=1,
        ge=0,
        description="Additional concurrent runs being requested",
    )
    # Optional context
    feature_id: Optional[str] = Field(
        default=None,
        description="Feature ID for feature-scoped limits",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for user-scoped limits",
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID for project-scoped limits",
    )


class LimitCheckResult(BaseModel):
    """Result of a single limit check."""

    limit_id: Optional[str] = Field(
        default=None,
        description="Limit ID (if policy limit)",
    )
    limit_type: str = Field(
        description="Type of limit checked",
    )
    limit_name: str = Field(
        description="Human-readable limit name",
    )
    current_value: Decimal = Field(
        description="Current usage value",
    )
    limit_value: Decimal = Field(
        description="Maximum allowed value",
    )
    projected_value: Decimal = Field(
        description="Projected value after execution",
    )
    enforcement: str = Field(
        description="Enforcement behavior: BLOCK, WARN, etc.",
    )
    decision: SimulationDecision = Field(
        description="Decision for this limit: ALLOW, BLOCK, WARN",
    )
    message_code: MessageCode = Field(
        description="Standardized message code",
    )


class HeadroomInfo(BaseModel):
    """Remaining headroom before hitting limits."""

    tokens: int = Field(
        description="Remaining tokens before limit",
    )
    cost_cents: int = Field(
        description="Remaining cost budget in cents",
    )
    runs: int = Field(
        description="Remaining runs before limit",
    )
    concurrent_runs: int = Field(
        description="Remaining concurrent run slots",
    )


class LimitWarning(BaseModel):
    """Warning for soft limit approaching."""

    limit_id: Optional[str] = Field(
        default=None,
        description="Limit ID if applicable",
    )
    limit_type: str = Field(
        description="Type of limit",
    )
    message_code: MessageCode = Field(
        description="Standardized warning code",
    )
    current_percent: float = Field(
        description="Current usage as percentage of limit",
    )


class LimitSimulationResponse(BaseModel):
    """Response model for limit simulation."""

    # Overall decision
    decision: SimulationDecision = Field(
        description="Overall decision: ALLOW, BLOCK, or WARN",
    )
    # Blocking limit (if BLOCK)
    blocking_limit_id: Optional[str] = Field(
        default=None,
        description="ID of the limit that caused BLOCK (if any)",
    )
    blocking_limit_type: Optional[str] = Field(
        default=None,
        description="Type of blocking limit",
    )
    blocking_message_code: Optional[MessageCode] = Field(
        default=None,
        description="Message code for blocking limit",
    )
    # Warnings
    warnings: list[LimitWarning] = Field(
        default_factory=list,
        description="List of soft limit warnings",
    )
    # Headroom
    headroom: HeadroomInfo = Field(
        description="Remaining capacity before hitting limits",
    )
    # Detailed results
    checks: list[LimitCheckResult] = Field(
        default_factory=list,
        description="Detailed results for each limit checked",
    )
    # Override info
    overrides_applied: list[str] = Field(
        default_factory=list,
        description="List of override IDs that were applied",
    )

    class Config:
        from_attributes = True
