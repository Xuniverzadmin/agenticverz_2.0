# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Customer integration data models
# Callers: cus_* services, cus_* APIs
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer Integrations Models

PURPOSE:
    SQLModel ORM classes for customer LLM integrations. These models represent
    the control plane (integrations) and data plane (usage telemetry) for
    customer-owned LLM providers.

MODELS:
    - CusIntegration: Customer LLM provider configuration with credentials and limits
    - CusLLMUsage: Individual LLM call telemetry record
    - CusUsageDaily: Pre-aggregated daily usage statistics

SEMANTIC:
    - CusIntegration: CONTROL PLANE - defines what integrations exist
    - CusLLMUsage: DATA PLANE - records what happened (append-only)
    - CusUsageDaily: DERIVED DATA - computed aggregates for performance
"""

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


# =============================================================================
# ENUMS
# =============================================================================


class CusProviderType(str, Enum):
    """Supported LLM provider types.

    SEMANTIC: Defines the universe of supported LLM providers.
    Adding a new provider requires SDK adapter implementation.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    CUSTOM = "custom"


class CusIntegrationStatus(str, Enum):
    """Integration lifecycle status.

    SEMANTIC: Controls whether the integration can be used.
    - created: Just created, not yet enabled
    - enabled: Active and usable
    - disabled: Manually paused by user
    - error: System-detected issue (e.g., credential failure)
    """

    CREATED = "created"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class CusHealthState(str, Enum):
    """Integration health state.

    SEMANTIC: Result of health checks against the LLM provider.
    - unknown: Never checked or check pending
    - healthy: Provider responding normally
    - degraded: Elevated latency or partial failures
    - failing: Provider unreachable or credentials invalid
    """

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"


class CusPolicyResult(str, Enum):
    """Policy enforcement result for LLM calls.

    SEMANTIC: Outcome of governance checks before/during LLM call.
    - allowed: Call proceeded normally
    - warned: Call proceeded but logged a warning (soft limit)
    - blocked: Call was prevented (hard limit)
    """

    ALLOWED = "allowed"
    WARNED = "warned"
    BLOCKED = "blocked"


# =============================================================================
# CUS_INTEGRATION MODEL
# =============================================================================


class CusIntegration(SQLModel, table=True):
    """Customer LLM Provider Integration.

    PURPOSE:
        Represents a customer's connection to an external LLM provider (OpenAI,
        Anthropic, etc.). Stores encrypted credentials, configuration, limits,
        and health state.

    SEMANTIC:
        CONTROL PLANE entity. Defines WHAT integrations exist and HOW they are
        configured. Changes here affect SDK behavior and enforcement.

    LIFECYCLE:
        created → enabled ↔ disabled
                    ↓
                  error (auto on health failure)

    INVARIANTS:
        - credential_ref is NEVER a raw API key (always encrypted/vault ref)
        - tenant_id is required for isolation
        - name is unique per tenant
    """

    __tablename__ = "cus_integrations"

    # Primary key
    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Tenant ownership (required for isolation)
    tenant_id: str = Field(max_length=100, index=True)

    # Integration identity
    name: str = Field(max_length=255)
    provider_type: CusProviderType = Field(max_length=50)

    # Credential storage (encrypted reference, NEVER raw key)
    credential_ref: str = Field(description="Encrypted credential or vault pointer")

    # Configuration (provider-specific settings as JSON)
    config: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Lifecycle status
    status: CusIntegrationStatus = Field(default=CusIntegrationStatus.CREATED, max_length=20)

    # Health monitoring
    health_state: CusHealthState = Field(default=CusHealthState.UNKNOWN, max_length=20)
    health_checked_at: Optional[datetime] = Field(default=None)
    health_message: Optional[str] = Field(default=None)

    # Default model for this integration
    default_model: Optional[str] = Field(default=None, max_length=100)

    # Governance limits (0 = unlimited)
    budget_limit_cents: int = Field(default=0, description="Monthly budget limit in cents")
    token_limit_month: int = Field(default=0, description="Monthly token limit")
    rate_limit_rpm: int = Field(default=0, description="Requests per minute limit")

    # Audit fields
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    created_by: Optional[str] = Field(default=None, max_length=100)

    # Soft delete
    deleted_at: Optional[datetime] = Field(default=None)

    # =========================================================================
    # LIFECYCLE METHODS
    # =========================================================================

    def enable(self) -> None:
        """Enable this integration for use.

        SEMANTIC: Transitions from created/disabled to enabled.
        Requires: credentials must be valid (health check passed).
        """
        if self.status == CusIntegrationStatus.ERROR:
            raise ValueError("Cannot enable integration in error state - fix credentials first")
        self.status = CusIntegrationStatus.ENABLED
        self.updated_at = utc_now()

    def disable(self) -> None:
        """Disable this integration (user-initiated pause).

        SEMANTIC: Temporarily stops SDK from using this integration.
        Can be re-enabled without re-validating credentials.
        """
        self.status = CusIntegrationStatus.DISABLED
        self.updated_at = utc_now()

    def mark_error(self, message: str) -> None:
        """Mark integration as errored (system-detected issue).

        SEMANTIC: Health check or credential validation failed.
        Requires manual intervention to fix and re-enable.
        """
        self.status = CusIntegrationStatus.ERROR
        self.health_state = CusHealthState.FAILING
        self.health_message = message
        self.health_checked_at = utc_now()
        self.updated_at = utc_now()

    def update_health(self, state: CusHealthState, message: Optional[str] = None) -> None:
        """Update health state from health check result.

        SEMANTIC: Records the outcome of a health check.
        Does NOT change status (use mark_error for that).
        """
        self.health_state = state
        self.health_message = message
        self.health_checked_at = utc_now()
        self.updated_at = utc_now()

    # =========================================================================
    # QUERY HELPERS
    # =========================================================================

    @property
    def is_usable(self) -> bool:
        """Check if integration can be used for LLM calls.

        SEMANTIC: SDK should check this before making calls.
        True only if enabled and not in error state.
        """
        return self.status == CusIntegrationStatus.ENABLED and self.deleted_at is None

    @property
    def is_deleted(self) -> bool:
        """Check if integration is soft-deleted."""
        return self.deleted_at is not None

    @property
    def has_budget_limit(self) -> bool:
        """Check if budget limit is configured."""
        return self.budget_limit_cents > 0

    @property
    def has_token_limit(self) -> bool:
        """Check if token limit is configured."""
        return self.token_limit_month > 0

    @property
    def has_rate_limit(self) -> bool:
        """Check if rate limit is configured."""
        return self.rate_limit_rpm > 0


# =============================================================================
# CUS_LLM_USAGE MODEL
# =============================================================================


class CusLLMUsage(SQLModel, table=True):
    """Individual LLM Call Telemetry Record.

    PURPOSE:
        Records a single LLM API call made through the SDK. Captures tokens,
        cost, latency, and enforcement result. Used for analytics, billing,
        and governance.

    SEMANTIC:
        DATA PLANE entity. Records FACTS about what happened. Append-only by
        design - never update or delete usage records.

    INVARIANTS:
        - call_id is unique (idempotency key from SDK)
        - tokens_in and tokens_out are non-negative
        - cost_cents is calculated, not user-provided
    """

    __tablename__ = "cus_llm_usage"

    # Primary key
    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Ownership and context
    tenant_id: str = Field(max_length=100, index=True)
    integration_id: str = Field(description="Reference to cus_integrations")
    session_id: Optional[str] = Field(default=None, description="Optional session grouping")
    agent_id: Optional[str] = Field(default=None, max_length=100, description="Agent that made this call")

    # Idempotency key (SDK generates unique call_id per request)
    call_id: str = Field(max_length=100, unique=True, description="SDK-generated idempotency key")

    # LLM call details
    provider: str = Field(max_length=50)
    model: str = Field(max_length=100)
    tokens_in: int = Field(ge=0, description="Input/prompt tokens")
    tokens_out: int = Field(ge=0, description="Output/completion tokens")
    cost_cents: int = Field(ge=0, description="Calculated cost in cents")
    latency_ms: Optional[int] = Field(default=None, ge=0, description="Request latency in milliseconds")

    # Policy enforcement result
    policy_result: CusPolicyResult = Field(default=CusPolicyResult.ALLOWED, max_length=20)

    # Error tracking
    error_code: Optional[str] = Field(default=None, max_length=50)
    error_message: Optional[str] = Field(default=None)

    # Extensible metadata (named 'extra_data' to avoid SQLAlchemy reserved name 'metadata')
    extra_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamp
    created_at: datetime = Field(default_factory=utc_now)

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.tokens_in + self.tokens_out

    @property
    def is_error(self) -> bool:
        """Check if this call resulted in an error."""
        return self.error_code is not None

    @property
    def was_blocked(self) -> bool:
        """Check if this call was blocked by policy."""
        return self.policy_result == CusPolicyResult.BLOCKED


# =============================================================================
# CUS_USAGE_DAILY MODEL
# =============================================================================


class CusUsageDaily(SQLModel, table=True):
    """Pre-aggregated Daily Usage Statistics.

    PURPOSE:
        Stores rolled-up daily usage metrics for performance. Populated by a
        scheduled job that aggregates cus_llm_usage. Used for dashboards,
        billing, and limit enforcement.

    SEMANTIC:
        DERIVED DATA. Computed from cus_llm_usage for query performance.
        Can be regenerated from source if needed.

    INVARIANTS:
        - (tenant_id, integration_id, date) is unique
        - All counts are non-negative
        - updated_at reflects last aggregation run
    """

    __tablename__ = "cus_usage_daily"

    # Composite primary key (no separate id field)
    tenant_id: str = Field(max_length=100, primary_key=True)
    integration_id: str = Field(primary_key=True)
    usage_date: date = Field(primary_key=True)  # Renamed from 'date' to avoid shadowing the type

    # Aggregated metrics
    total_calls: int = Field(default=0, ge=0)
    total_tokens_in: int = Field(default=0, ge=0)
    total_tokens_out: int = Field(default=0, ge=0)
    total_cost_cents: int = Field(default=0, ge=0)
    avg_latency_ms: Optional[int] = Field(default=None, ge=0)
    error_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)

    # Audit
    updated_at: datetime = Field(default_factory=utc_now)

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.total_tokens_in + self.total_tokens_out

    @property
    def success_rate(self) -> float:
        """Percentage of successful calls (non-error, non-blocked)."""
        if self.total_calls == 0:
            return 1.0
        failed = self.error_count + self.blocked_count
        return (self.total_calls - failed) / self.total_calls

    @property
    def cost_dollars(self) -> float:
        """Total cost in dollars."""
        return self.total_cost_cents / 100.0
