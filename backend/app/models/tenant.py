"""Tenant, User, and Multi-Tenancy Models (M21)

Provides:
- Tenant (organization) management
- User accounts linked to Clerk
- Tenant memberships with roles
- API key generation and validation
- Subscription/billing support
- TenantTier integration (M32)
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from ..auth.tier_gating import TenantTier


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ============== TENANT (Organization) ==============


class Tenant(SQLModel, table=True):
    """Organization/Tenant model for multi-tenancy."""

    __tablename__ = "tenants"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=100, unique=True, index=True)
    clerk_org_id: Optional[str] = Field(default=None, max_length=100, unique=True)

    # Plan & Billing
    plan: str = Field(default="free", max_length=50)  # free, pro, enterprise
    billing_email: Optional[str] = Field(default=None, max_length=255)
    stripe_customer_id: Optional[str] = Field(default=None, max_length=100)

    # Quotas & Limits
    max_workers: int = Field(default=3)
    max_runs_per_day: int = Field(default=100)
    max_concurrent_runs: int = Field(default=5)
    max_tokens_per_month: int = Field(default=1_000_000)
    max_api_keys: int = Field(default=5)

    # Usage Tracking
    runs_today: int = Field(default=0)
    runs_this_month: int = Field(default=0)
    tokens_this_month: int = Field(default=0)
    last_run_reset_at: Optional[datetime] = None

    # Status
    status: str = Field(default="active", max_length=50)  # active, suspended, churned
    suspended_reason: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def can_create_run(self) -> tuple[bool, str]:
        """Check if tenant can create a new run."""
        if self.status != "active":
            return False, f"Tenant is {self.status}"
        if self.runs_today >= self.max_runs_per_day:
            return False, f"Daily run limit ({self.max_runs_per_day}) exceeded"
        return True, ""

    def can_use_tokens(self, tokens: int) -> tuple[bool, str]:
        """Check if tenant can use given tokens."""
        if self.tokens_this_month + tokens > self.max_tokens_per_month:
            return False, f"Monthly token limit ({self.max_tokens_per_month:,}) would be exceeded"
        return True, ""

    def increment_usage(self, tokens: int = 0):
        """Increment usage counters."""
        self.runs_today += 1
        self.runs_this_month += 1
        self.tokens_this_month += tokens
        self.updated_at = utc_now()

    @property
    def tier(self) -> "TenantTier":
        """
        Get the tenant's tier from their plan.

        Resolves legacy plan names (free, pro, enterprise) and new tier names
        (observe, react, prevent, assist, govern) to TenantTier enum.
        """
        from ..auth.tier_gating import resolve_tier

        return resolve_tier(self.plan)

    @property
    def tier_marketing_name(self) -> str:
        """Get the marketing name for the tenant's tier."""
        from ..auth.tier_gating import PRICE_ANCHORS

        return PRICE_ANCHORS.get(self.tier, {}).get("marketing_name", self.plan)

    @property
    def retention_days(self) -> int:
        """Get log retention days based on tier."""
        from ..auth.tier_gating import PRICE_ANCHORS

        return PRICE_ANCHORS.get(self.tier, {}).get("retention_days", 7)

    def has_feature(self, feature: str) -> bool:
        """
        Check if tenant has access to a feature based on their tier.

        Uses CURRENT_PHASE to determine soft/hard gating.
        """
        from ..auth.tier_gating import check_tier_access

        result = check_tier_access(feature, self.tier)
        return result.allowed

    def get_available_features(self) -> list[str]:
        """Get list of all features available to this tenant."""
        from ..auth.tier_gating import get_tier_features

        return get_tier_features(self.tier)


# Plan quotas reference
PLAN_QUOTAS = {
    "free": {
        "max_workers": 3,
        "max_runs_per_day": 100,
        "max_concurrent_runs": 5,
        "max_tokens_per_month": 1_000_000,
        "max_api_keys": 5,
    },
    "pro": {
        "max_workers": 10,
        "max_runs_per_day": 1000,
        "max_concurrent_runs": 20,
        "max_tokens_per_month": 10_000_000,
        "max_api_keys": 20,
    },
    "enterprise": {
        "max_workers": 100,
        "max_runs_per_day": 100000,
        "max_concurrent_runs": 100,
        "max_tokens_per_month": 1_000_000_000,
        "max_api_keys": 100,
    },
}


# ============== USER ==============


class User(SQLModel, table=True):
    """User account - supports OAuth (Google/Azure) and email signup."""

    __tablename__ = "users"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    clerk_user_id: str = Field(max_length=100, unique=True, index=True)
    email: str = Field(max_length=255, index=True)
    name: Optional[str] = Field(default=None, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    # OAuth provider info (M24 Customer Onboarding)
    oauth_provider: Optional[str] = Field(default=None, max_length=50)  # google, azure, email
    oauth_provider_id: Optional[str] = Field(default=None, max_length=255)

    # Email verification (M24)
    email_verified: bool = Field(default=False)
    email_verified_at: Optional[datetime] = None

    # Default tenant
    default_tenant_id: Optional[str] = Field(default=None, foreign_key="tenants.id")

    # Status
    status: str = Field(default="active", max_length=50)  # active, suspended, deleted

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_login_at: Optional[datetime] = None


# ============== TENANT MEMBERSHIP ==============


class TenantMembership(SQLModel, table=True):
    """User membership in a tenant with role."""

    __tablename__ = "tenant_memberships"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)

    # Role: owner, admin, member, viewer
    role: str = Field(default="member", max_length=50)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    invited_by: Optional[str] = None

    def can_manage_keys(self) -> bool:
        return self.role in ("owner", "admin")

    def can_run_workers(self) -> bool:
        return self.role in ("owner", "admin", "member")

    def can_view_runs(self) -> bool:
        return True  # All roles can view


# ============== API KEY ==============


class APIKey(SQLModel, table=True):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")

    # Key details
    name: str = Field(max_length=100)
    key_prefix: str = Field(max_length=10, index=True)  # aos_xxxxxxxx
    key_hash: str = Field(max_length=128, index=True)  # SHA-256 hash

    # Permissions & Scopes (JSON strings)
    permissions_json: Optional[str] = None  # ["run:*", "read:*"]
    allowed_workers_json: Optional[str] = None  # ["business-builder"]

    # Rate Limits (per-key override)
    rate_limit_rpm: Optional[int] = None
    max_concurrent_runs: Optional[int] = None

    # Status
    status: str = Field(default="active", max_length=50)  # active, revoked, expired
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = Field(default=None, max_length=255)

    # Usage
    last_used_at: Optional[datetime] = None
    total_requests: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate a new API key. Returns (full_key, prefix, hash)."""
        # Generate 32-byte random key
        raw_key = secrets.token_urlsafe(32)
        full_key = f"aos_{raw_key}"
        prefix = full_key[:12]  # aos_xxxxxxxx
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        return full_key, prefix, key_hash

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash a key for comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    def is_valid(self) -> bool:
        """Check if key is valid (not revoked, not expired)."""
        if self.status != "active":
            return False
        if self.expires_at and self.expires_at < utc_now():
            return False
        return True

    def record_usage(self):
        """Record that this key was used."""
        self.last_used_at = utc_now()
        self.total_requests += 1


# ============== SUBSCRIPTION ==============


class Subscription(SQLModel, table=True):
    """Billing subscription for a tenant."""

    __tablename__ = "subscriptions"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)

    # Plan
    plan: str = Field(max_length=50)  # free, pro, enterprise
    status: str = Field(default="active", max_length=50)  # active, canceled, past_due, trialing

    # Stripe
    stripe_subscription_id: Optional[str] = Field(default=None, max_length=100, index=True)
    stripe_price_id: Optional[str] = Field(default=None, max_length=100)

    # Billing period
    billing_period: str = Field(default="monthly", max_length=20)  # monthly, annual
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

    # Trial
    trial_ends_at: Optional[datetime] = None

    # Cancellation
    canceled_at: Optional[datetime] = None
    cancel_at_period_end: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# ============== USAGE RECORD ==============


class UsageRecord(SQLModel, table=True):
    """Usage metering for billing."""

    __tablename__ = "usage_records"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)

    # Usage
    meter_name: str = Field(max_length=100, index=True)  # worker_runs, tokens_used, etc.
    amount: int
    unit: str = Field(default="count", max_length=50)  # count, tokens, seconds

    # Period
    period_start: datetime
    period_end: datetime

    # Metadata
    worker_id: Optional[str] = Field(default=None, max_length=100)
    api_key_id: Optional[str] = None
    metadata_json: Optional[str] = None

    # Timestamps
    recorded_at: datetime = Field(default_factory=utc_now)


# ============== WORKER REGISTRY ==============


class WorkerRegistry(SQLModel, table=True):
    """Registry of available workers."""

    __tablename__ = "worker_registry"

    id: str = Field(primary_key=True, max_length=100)  # e.g., 'business-builder'
    name: str = Field(max_length=255)
    description: Optional[str] = None
    version: str = Field(default="1.0.0", max_length=50)

    # Status
    status: str = Field(default="available", max_length=50, index=True)  # available, beta, coming_soon, deprecated
    is_public: bool = Field(default=True)

    # Configuration (JSON)
    moats_json: Optional[str] = None  # ["M9", "M10", "M17"]
    default_config_json: Optional[str] = None
    input_schema_json: Optional[str] = None
    output_schema_json: Optional[str] = None

    # Pricing
    tokens_per_run_estimate: Optional[int] = None
    cost_per_run_cents: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# ============== WORKER CONFIG (Per-Tenant) ==============


class WorkerConfig(SQLModel, table=True):
    """Per-tenant worker configuration."""

    __tablename__ = "worker_configs"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    worker_id: str = Field(foreign_key="worker_registry.id", index=True)

    # Config
    enabled: bool = Field(default=True)
    config_json: Optional[str] = None  # Tenant overrides
    brand_json: Optional[str] = None  # Default brand

    # Limits
    max_runs_per_day: Optional[int] = None
    max_tokens_per_run: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# ============== WORKER RUN (With Tenant Isolation) ==============


class WorkerRun(SQLModel, table=True):
    """Worker execution run with tenant isolation."""

    __tablename__ = "worker_runs"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.id", index=True)
    worker_id: str = Field(foreign_key="worker_registry.id", index=True)
    api_key_id: Optional[str] = Field(default=None, foreign_key="api_keys.id")
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")

    # Task
    task: str
    input_json: Optional[str] = None

    # Status
    status: str = Field(default="queued", max_length=50, index=True)  # queued, running, completed, failed
    success: Optional[bool] = None
    error: Optional[str] = None

    # Results
    output_json: Optional[str] = None
    replay_token_json: Optional[str] = None

    # Metrics
    total_tokens: Optional[int] = None
    total_latency_ms: Optional[int] = None
    stages_completed: Optional[int] = None
    recoveries: int = Field(default=0)
    policy_violations: int = Field(default=0)

    # Cost
    cost_cents: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============== AUDIT LOG ==============


class AuditLog(SQLModel, table=True):
    """Comprehensive audit log for compliance."""

    __tablename__ = "audit_log"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    api_key_id: Optional[str] = None

    # Action
    action: str = Field(max_length=100)  # create_run, revoke_key, etc.
    resource_type: str = Field(max_length=50)  # run, api_key, worker_config
    resource_id: Optional[str] = Field(default=None, max_length=100)

    # Request
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    request_id: Optional[str] = Field(default=None, max_length=100)

    # Changes
    old_value_json: Optional[str] = None
    new_value_json: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)


# ============== FOUNDER ACTIONS (M29 Category 6) ==============


class FounderAction(SQLModel, table=True):
    """
    Immutable record of founder actions on tenants/keys/incidents.

    M29 Category 6: Founder Action Paths

    Invariants:
    - Every action MUST have an audit record (no audit → API fails)
    - Actions are immutable (only reversed_at/reversed_by can be updated)
    - OVERRIDE_INCIDENT is not reversible
    - FREEZE_TENANT and THROTTLE_TENANT are mutually exclusive
    """

    __tablename__ = "founder_actions"

    # Primary key
    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Action type
    action_type: str = Field(
        max_length=50,
        description="FREEZE_TENANT, THROTTLE_TENANT, FREEZE_API_KEY, OVERRIDE_INCIDENT, UNFREEZE_TENANT, UNTHROTTLE_TENANT, UNFREEZE_API_KEY",
    )

    # Target
    target_type: str = Field(max_length=20, description="TENANT, API_KEY, INCIDENT")
    target_id: str = Field(max_length=100, description="ID of target")
    target_name: Optional[str] = Field(
        default=None, max_length=200, description="Display name of target at time of action"
    )

    # Reason (required for audit)
    reason_code: str = Field(
        max_length=50, description="COST_ANOMALY, POLICY_VIOLATION, RETRY_LOOP, ABUSE_SUSPECTED, FALSE_POSITIVE, OTHER"
    )
    reason_note: Optional[str] = Field(default=None, max_length=500, description="Optional free-text explanation")

    # Source incident (if action was triggered from incident view)
    source_incident_id: Optional[str] = Field(
        default=None, max_length=100, description="Incident ID that triggered this action"
    )

    # Founder who took action (required)
    founder_id: str = Field(max_length=100, description="ID of founder")
    founder_email: str = Field(max_length=200, description="Email of founder")
    mfa_verified: bool = Field(default=False, description="Whether MFA was verified")

    # Timestamps
    applied_at: datetime = Field(default_factory=utc_now, description="When action was applied")
    reversed_at: Optional[datetime] = Field(default=None, description="When action was reversed (null if still active)")
    reversed_by_action_id: Optional[str] = Field(default=None, max_length=100, description="ID of the reversal action")

    # Status tracking
    is_active: bool = Field(default=True, description="Whether action is currently in effect")
    is_reversible: bool = Field(default=True, description="Whether action can be reversed (OVERRIDE_INCIDENT = False)")

    @property
    def is_reversal(self) -> bool:
        """Check if this action is a reversal action."""
        return self.action_type in ("UNFREEZE_TENANT", "UNTHROTTLE_TENANT", "UNFREEZE_API_KEY")
