# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Policy limits request/response schemas
# Callers: api/policies.py, services/limits/policy_limits_service.py
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-LIM-01

"""
Policy Limits Schemas (PIN-LIM-01)

Request and response models for policy limit CRUD operations.
Enforces schema contract between API and service layer.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LimitCategoryEnum(str, Enum):
    """Limit categories."""
    BUDGET = "BUDGET"
    RATE = "RATE"
    THRESHOLD = "THRESHOLD"


class LimitScopeEnum(str, Enum):
    """Limit scope levels."""
    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    PROJECT = "PROJECT"
    AGENT = "AGENT"
    PROVIDER = "PROVIDER"


class LimitEnforcementEnum(str, Enum):
    """Limit enforcement behaviors."""
    BLOCK = "BLOCK"
    WARN = "WARN"
    REJECT = "REJECT"
    QUEUE = "QUEUE"
    DEGRADE = "DEGRADE"
    ALERT = "ALERT"


class ResetPeriodEnum(str, Enum):
    """Budget limit reset periods."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    NONE = "NONE"


class CreatePolicyLimitRequest(BaseModel):
    """Request model for creating a policy limit."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Human-readable limit name",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Optional description",
    )
    limit_category: LimitCategoryEnum = Field(
        ...,
        description="Limit category: BUDGET, RATE, or THRESHOLD",
    )
    limit_type: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Limit type: COST_USD, TOKENS_PER_RUN, REQUESTS_PER_MINUTE, etc.",
    )
    scope: LimitScopeEnum = Field(
        default=LimitScopeEnum.TENANT,
        description="Scope level: GLOBAL, TENANT, PROJECT, AGENT, PROVIDER",
    )
    scope_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Specific entity ID for non-GLOBAL scope",
    )
    max_value: Decimal = Field(
        ...,
        gt=0,
        description="Maximum allowed value (must be positive)",
    )
    enforcement: LimitEnforcementEnum = Field(
        default=LimitEnforcementEnum.BLOCK,
        description="Enforcement behavior when limit is breached",
    )
    # Budget-specific fields
    reset_period: Optional[ResetPeriodEnum] = Field(
        default=None,
        description="Reset period for BUDGET limits: DAILY, WEEKLY, MONTHLY, NONE",
    )
    # Rate-specific fields
    window_seconds: Optional[int] = Field(
        default=None,
        gt=0,
        description="Time window in seconds for RATE limits",
    )

    @field_validator("reset_period")
    @classmethod
    def validate_reset_period(cls, v: Optional[ResetPeriodEnum], info) -> Optional[ResetPeriodEnum]:
        """Reset period required for BUDGET limits."""
        # Note: Can't easily access other fields in Pydantic v2 field_validator
        # Validation happens at service layer
        return v

    @field_validator("window_seconds")
    @classmethod
    def validate_window_seconds(cls, v: Optional[int], info) -> Optional[int]:
        """Window seconds required for RATE limits."""
        return v


class UpdatePolicyLimitRequest(BaseModel):
    """Request model for updating a policy limit."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Updated name",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Updated description",
    )
    max_value: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Updated max value (must be positive)",
    )
    enforcement: Optional[LimitEnforcementEnum] = Field(
        default=None,
        description="Updated enforcement behavior",
    )
    reset_period: Optional[ResetPeriodEnum] = Field(
        default=None,
        description="Updated reset period (BUDGET only)",
    )
    window_seconds: Optional[int] = Field(
        default=None,
        gt=0,
        description="Updated time window (RATE only)",
    )
    status: Optional[str] = Field(
        default=None,
        pattern="^(ACTIVE|DISABLED)$",
        description="Updated status: ACTIVE or DISABLED",
    )


class PolicyLimitResponse(BaseModel):
    """Response model for policy limit operations."""

    limit_id: str = Field(description="Unique limit identifier")
    tenant_id: str = Field(description="Owning tenant ID")
    name: str = Field(description="Limit name")
    description: Optional[str] = Field(default=None, description="Limit description")
    limit_category: str = Field(description="Limit category")
    limit_type: str = Field(description="Limit type")
    scope: str = Field(description="Scope level")
    scope_id: Optional[str] = Field(default=None, description="Scope entity ID")
    max_value: Decimal = Field(description="Maximum allowed value")
    enforcement: str = Field(description="Enforcement behavior")
    status: str = Field(description="Limit status")
    reset_period: Optional[str] = Field(default=None, description="Reset period")
    window_seconds: Optional[int] = Field(default=None, description="Time window")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        from_attributes = True
