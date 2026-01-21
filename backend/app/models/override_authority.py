# Layer: L4 — Domain Engine
# Product: AI Console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Define emergency override rules for policies
# Callers: policy/prevention_engine.py, api/policy_overrides.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-010

"""
Override Authority Model

Defines emergency override rules for policies:
- Who can override (roles)
- Whether reason is required
- Maximum override duration
- Override audit trail

Overrides:
- Create audit entries
- Do not mutate the original policy snapshot
- Have time-limited effect
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel


class OverrideAuthority(SQLModel, table=True):
    """
    Override authority configuration for a policy.

    Defines who can override the policy during emergencies
    and the constraints on overrides.
    """

    __tablename__ = "policy_override_authority"

    id: Optional[int] = Field(default=None, primary_key=True)
    policy_id: str = Field(index=True, unique=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id

    # Override rules
    override_allowed: bool = Field(default=True)
    allowed_roles_json: str = Field(
        default='["OWNER", "SECURITY_ADMIN"]'
    )  # JSON array
    requires_reason: bool = Field(default=True)
    max_duration_seconds: int = Field(default=900)  # 15 minutes default
    max_overrides_per_day: int = Field(default=5)

    # Current override state
    currently_overridden: bool = Field(default=False)
    override_started_at: Optional[datetime] = Field(default=None)
    override_expires_at: Optional[datetime] = Field(default=None)
    override_by: Optional[str] = Field(default=None)
    override_reason: Optional[str] = Field(default=None)

    # Statistics
    total_overrides: int = Field(default=0)
    overrides_today: int = Field(default=0)
    last_override_date: Optional[datetime] = Field(default=None)

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def allowed_roles(self) -> list[str]:
        """Get allowed roles as list."""
        if self.allowed_roles_json:
            return json.loads(self.allowed_roles_json)
        return ["OWNER", "SECURITY_ADMIN"]

    @allowed_roles.setter
    def allowed_roles(self, value: list[str]) -> None:
        """Set allowed roles from list."""
        self.allowed_roles_json = json.dumps(value)

    def can_override(self, user_role: str) -> tuple[bool, str]:
        """
        Check if user with given role can override.

        Returns:
            Tuple of (can_override, reason)
        """
        if not self.override_allowed:
            return False, "Overrides are not allowed for this policy"

        if user_role not in self.allowed_roles:
            return False, f"Role {user_role} is not authorized to override"

        if self.overrides_today >= self.max_overrides_per_day:
            return False, "Maximum daily overrides exceeded"

        return True, "Override allowed"

    def is_override_active(self) -> bool:
        """Check if an override is currently active."""
        if not self.currently_overridden:
            return False
        if self.override_expires_at is None:
            return False
        return datetime.now(timezone.utc) < self.override_expires_at

    def apply_override(
        self,
        user_id: str,
        user_role: str,
        reason: str,
        duration_seconds: Optional[int] = None,
    ) -> tuple[bool, str]:
        """
        Apply an override to the policy.

        Returns:
            Tuple of (success, message)
        """
        can, msg = self.can_override(user_role)
        if not can:
            return False, msg

        if self.requires_reason and not reason:
            return False, "Reason is required for override"

        now = datetime.now(timezone.utc)
        duration = duration_seconds or self.max_duration_seconds

        self.currently_overridden = True
        self.override_started_at = now
        self.override_expires_at = now.replace(
            second=now.second + duration
        )  # Simplified
        self.override_by = user_id
        self.override_reason = reason
        self.total_overrides += 1
        self.overrides_today += 1
        self.last_override_date = now.date()
        self.updated_at = now

        return True, f"Override applied for {duration} seconds"

    def clear_override(self) -> None:
        """Clear the current override."""
        self.currently_overridden = False
        self.override_started_at = None
        self.override_expires_at = None
        self.override_by = None
        self.override_reason = None
        self.updated_at = datetime.now(timezone.utc)

    def reset_daily_count(self) -> None:
        """Reset the daily override count (called by scheduler)."""
        self.overrides_today = 0


class OverrideRecord(SQLModel, table=True):
    """
    Immutable record of a policy override.

    Every override creates an audit record that cannot be modified.
    """

    __tablename__ = "policy_override_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: str = Field(
        default_factory=lambda: f"OVRD-{uuid.uuid4().hex[:12]}",
        index=True,
        unique=True,
    )

    # References
    policy_id: str = Field(index=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id
    run_id: Optional[str] = Field(default=None, index=True)  # If override was for specific run

    # Override details
    override_by: str  # User ID
    override_role: str  # Role at time of override
    reason: str
    duration_seconds: int

    # Timestamps
    started_at: datetime
    expires_at: datetime
    ended_at: Optional[datetime] = Field(default=None)  # If manually ended

    # Outcome
    was_manually_ended: bool = Field(default=False)
    ended_by: Optional[str] = Field(default=None)

    @classmethod
    def create_record(
        cls,
        policy_id: str,
        tenant_id: str,
        override_by: str,
        override_role: str,
        reason: str,
        duration_seconds: int,
        run_id: Optional[str] = None,
    ) -> "OverrideRecord":
        """Create an override record."""
        now = datetime.now(timezone.utc)
        return cls(
            policy_id=policy_id,
            tenant_id=tenant_id,
            run_id=run_id,
            override_by=override_by,
            override_role=override_role,
            reason=reason,
            duration_seconds=duration_seconds,
            started_at=now,
            expires_at=now.replace(second=now.second + duration_seconds),
        )


class OverrideAuthorityCreate(BaseModel):
    """Request model for creating override authority."""

    policy_id: str
    override_allowed: bool = True
    allowed_roles: list[str] = PydanticField(default=["OWNER", "SECURITY_ADMIN"])
    requires_reason: bool = True
    max_duration_seconds: int = 900
    max_overrides_per_day: int = 5


class OverrideAuthorityUpdate(BaseModel):
    """Request model for updating override authority."""

    override_allowed: Optional[bool] = None
    allowed_roles: Optional[list[str]] = None
    requires_reason: Optional[bool] = None
    max_duration_seconds: Optional[int] = None
    max_overrides_per_day: Optional[int] = None


class ApplyOverrideRequest(BaseModel):
    """Request model for applying an override."""

    reason: str
    duration_seconds: Optional[int] = None
    run_id: Optional[str] = None


class OverrideAuthorityResponse(BaseModel):
    """Response model for override authority."""

    policy_id: str
    tenant_id: str
    override_allowed: bool
    allowed_roles: list[str]
    requires_reason: bool
    max_duration_seconds: int
    max_overrides_per_day: int
    currently_overridden: bool
    override_expires_at: Optional[datetime]
    override_by: Optional[str]
    total_overrides: int
    overrides_today: int


class OverrideRecordResponse(BaseModel):
    """Response model for override record."""

    record_id: str
    policy_id: str
    run_id: Optional[str]
    override_by: str
    override_role: str
    reason: str
    duration_seconds: int
    started_at: datetime
    expires_at: datetime
    ended_at: Optional[datetime]
    was_manually_ended: bool
