# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Limit override request/response schemas
# Callers: api/limits/override.py, services/limits/override_service.py
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-LIM-05

"""
Limit Override Schemas (PIN-LIM-05)

Request and response models for temporary limit increases.
Overrides allow customers to request and apply temporary limit increases
with proper audit trail.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OverrideStatus(str, Enum):
    """Override lifecycle status."""
    PENDING = "PENDING"           # Awaiting approval
    APPROVED = "APPROVED"         # Approved, waiting to start
    ACTIVE = "ACTIVE"             # Currently in effect
    EXPIRED = "EXPIRED"           # Past expiry time
    REJECTED = "REJECTED"         # Denied by admin
    CANCELLED = "CANCELLED"       # Cancelled by requester


class LimitOverrideRequest(BaseModel):
    """Request model for requesting a temporary limit override."""

    limit_id: str = Field(
        ...,
        description="ID of the limit to override",
    )
    override_value: Decimal = Field(
        ...,
        gt=0,
        description="Requested override value (must be positive)",
    )
    duration_hours: int = Field(
        ...,
        ge=1,
        le=168,  # Max 1 week
        description="Override duration in hours (1-168)",
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Business justification for the override",
    )
    start_immediately: bool = Field(
        default=True,
        description="Start override immediately upon approval",
    )
    scheduled_start: Optional[datetime] = Field(
        default=None,
        description="Scheduled start time (if not starting immediately)",
    )

    @field_validator("override_value")
    @classmethod
    def validate_override_value(cls, v: Decimal) -> Decimal:
        """Override value must be positive."""
        if v <= 0:
            raise ValueError("Override value must be positive")
        return v


class LimitOverrideResponse(BaseModel):
    """Response model for limit override operations."""

    override_id: str = Field(
        description="Unique override identifier",
    )
    limit_id: str = Field(
        description="ID of the limit being overridden",
    )
    limit_name: str = Field(
        description="Name of the limit being overridden",
    )
    tenant_id: str = Field(
        description="Owning tenant ID",
    )
    # Override details
    original_value: Decimal = Field(
        description="Original limit value",
    )
    override_value: Decimal = Field(
        description="Approved override value",
    )
    effective_value: Decimal = Field(
        description="Currently effective value",
    )
    # Status
    status: OverrideStatus = Field(
        description="Current override status",
    )
    # Timing
    requested_at: datetime = Field(
        description="When the override was requested",
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        description="When the override was approved",
    )
    starts_at: Optional[datetime] = Field(
        default=None,
        description="When the override starts/started",
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the override expires",
    )
    # Audit
    requested_by: str = Field(
        description="User who requested the override",
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="User who approved the override",
    )
    reason: str = Field(
        description="Business justification",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Reason for rejection (if rejected)",
    )

    class Config:
        from_attributes = True


class OverrideApprovalRequest(BaseModel):
    """Request model for approving/rejecting an override."""

    approved: bool = Field(
        description="Whether to approve (true) or reject (false)",
    )
    adjusted_value: Optional[Decimal] = Field(
        default=None,
        description="Optionally adjust the override value",
    )
    adjusted_duration_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=168,
        description="Optionally adjust the duration",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for rejection (required if rejecting)",
    )

    @field_validator("rejection_reason")
    @classmethod
    def validate_rejection_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Rejection reason required when rejecting."""
        # Note: Cross-field validation happens at service layer
        return v


class OverrideListResponse(BaseModel):
    """Response model for listing overrides."""

    items: list[LimitOverrideResponse] = Field(
        default_factory=list,
        description="List of overrides",
    )
    total: int = Field(
        description="Total count of matching overrides",
    )
    has_more: bool = Field(
        description="Whether more results are available",
    )
