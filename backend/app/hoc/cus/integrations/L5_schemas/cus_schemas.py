# capability_id: CAP-018
# Layer: L6 — Platform Substrate (Schemas)
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Pydantic schemas for Customer Integration domain (LLM BYOK, SDK, RAG)
# Callers: aos_cus_integrations.py, cus_telemetry.py APIs
# Allowed Imports: cus_models.py (enums only)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Connectivity Domain - Customer Console v1 Constitution

"""Customer Integrations API Schemas

PURPOSE:
    Pydantic request/response models for the Customer Integrations API surface.
    These schemas define the contract between SDK/clients and the backend.

SCHEMAS:
    Request Schemas:
    - CusIntegrationCreate: Create a new integration
    - CusIntegrationUpdate: Update integration settings
    - CusLLMUsageIngest: Telemetry ingestion from SDK

    Response Schemas:
    - CusIntegrationResponse: Full integration details
    - CusIntegrationSummary: List view integration
    - CusUsageSummary: Aggregated usage statistics
    - CusLimitsStatus: Current usage vs limits

VALIDATION:
    - All credential_ref values are validated as non-raw (no bare API keys)
    - Provider types are constrained to supported enum values
    - Token/cost values must be non-negative
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.hoc.cus.integrations.L5_schemas.cus_enums import (
    CusHealthState,
    CusIntegrationStatus,
    CusPolicyResult,
    CusProviderType,
)


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class CusIntegrationCreate(BaseModel):
    """Request schema for creating a new integration.

    PURPOSE:
        Captures all required information to create a customer LLM integration.
        Credential handling is secure - we never accept raw API keys directly.

    VALIDATION:
        - name is required, 1-255 chars
        - provider_type must be a supported provider
        - credential_ref must not look like a raw API key
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name for this integration",
        examples=["Production OpenAI", "Dev Anthropic"],
    )
    provider_type: CusProviderType = Field(
        ...,
        description="LLM provider type",
        examples=["openai", "anthropic"],
    )
    credential_ref: str = Field(
        ...,
        description="Encrypted credential reference or vault pointer (NEVER raw API key)",
        examples=["vault://secrets/openai-prod", "encrypted:aes256:..."],
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific configuration (base_url, org_id, etc.)",
        examples=[{"organization_id": "org-123", "api_version": "2024-01"}],
    )
    default_model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Default model to use for this integration",
        examples=["gpt-4", "claude-sonnet-4-20250514"],
    )
    budget_limit_cents: int = Field(
        default=0,
        ge=0,
        description="Monthly budget limit in cents (0 = unlimited)",
        examples=[10000, 50000],
    )
    token_limit_month: int = Field(
        default=0,
        ge=0,
        description="Monthly token limit (0 = unlimited)",
        examples=[1000000, 10000000],
    )
    rate_limit_rpm: int = Field(
        default=0,
        ge=0,
        description="Requests per minute limit (0 = unlimited)",
        examples=[60, 100],
    )

    @field_validator("credential_ref")
    @classmethod
    def validate_not_raw_key(cls, v: str) -> str:
        """Ensure credential_ref is not a raw API key.

        SECURITY: Raw API keys (sk-..., anthropic-..., etc.) must never
        be stored directly. They must be encrypted or vault-referenced.
        """
        raw_prefixes = ["sk-", "anthropic-", "az-", "aws_"]
        for prefix in raw_prefixes:
            if v.startswith(prefix):
                raise ValueError(
                    f"credential_ref appears to be a raw API key (starts with '{prefix}'). "
                    "Please encrypt the key or use a vault reference."
                )
        return v


class CusIntegrationUpdate(BaseModel):
    """Request schema for updating an integration.

    PURPOSE:
        Partial update - only provided fields are changed.
        Status changes should use dedicated enable/disable endpoints.
    """

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Update integration name",
    )
    credential_ref: Optional[str] = Field(
        default=None,
        description="Update credential reference (must be encrypted/vault ref)",
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Update provider-specific configuration",
    )
    default_model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Update default model",
    )
    budget_limit_cents: Optional[int] = Field(
        default=None,
        ge=0,
        description="Update monthly budget limit",
    )
    token_limit_month: Optional[int] = Field(
        default=None,
        ge=0,
        description="Update monthly token limit",
    )
    rate_limit_rpm: Optional[int] = Field(
        default=None,
        ge=0,
        description="Update rate limit",
    )

    @field_validator("credential_ref")
    @classmethod
    def validate_not_raw_key(cls, v: Optional[str]) -> Optional[str]:
        """Ensure credential_ref is not a raw API key."""
        if v is None:
            return v
        raw_prefixes = ["sk-", "anthropic-", "az-", "aws_"]
        for prefix in raw_prefixes:
            if v.startswith(prefix):
                raise ValueError(
                    f"credential_ref appears to be a raw API key (starts with '{prefix}'). "
                    "Please encrypt the key or use a vault reference."
                )
        return v


class CusLLMUsageIngest(BaseModel):
    """Request schema for SDK telemetry ingestion.

    PURPOSE:
        SDK sends telemetry for each LLM call. This schema validates
        the payload before persisting to cus_llm_usage.

    SEMANTIC:
        This is DATA PLANE ingestion - append-only facts about what happened.
        call_id provides idempotency for at-least-once delivery.
    """

    integration_id: str = Field(
        ...,
        description="Integration ID this call was made through",
    )
    call_id: str = Field(
        ...,
        max_length=100,
        description="SDK-generated unique call ID for idempotency",
        examples=["call-abc123-def456"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session grouping for related calls",
    )
    agent_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Agent that made this call",
    )
    provider: str = Field(
        ...,
        max_length=50,
        description="Provider used (e.g., 'openai', 'anthropic')",
    )
    model: str = Field(
        ...,
        max_length=100,
        description="Model used for this call",
        examples=["gpt-4", "claude-sonnet-4-20250514"],
    )
    tokens_in: int = Field(
        ...,
        ge=0,
        description="Input/prompt tokens",
    )
    tokens_out: int = Field(
        ...,
        ge=0,
        description="Output/completion tokens",
    )
    cost_cents: int = Field(
        ...,
        ge=0,
        description="Calculated cost in cents",
    )
    latency_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Request latency in milliseconds",
    )
    policy_result: CusPolicyResult = Field(
        default=CusPolicyResult.ALLOWED,
        description="Policy enforcement result",
    )
    error_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Error code if call failed",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if call failed",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (prompt_hash, tool_calls, etc.)",
    )


class CusLLMUsageBatchIngest(BaseModel):
    """Request schema for batch telemetry ingestion.

    PURPOSE:
        SDK may buffer and send multiple telemetry records at once
        for efficiency. Max batch size is 100.
    """

    records: List[CusLLMUsageIngest] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Batch of telemetry records (max 100)",
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class CusIntegrationResponse(BaseModel):
    """Full integration details response.

    PURPOSE:
        Complete integration information including health state
        and current limits. Used for detail view.
    """

    id: str = Field(..., description="Integration ID")
    tenant_id: str = Field(..., description="Owning tenant")
    name: str = Field(..., description="Integration name")
    provider_type: CusProviderType = Field(..., description="Provider type")
    status: CusIntegrationStatus = Field(..., description="Current status")
    health_state: CusHealthState = Field(..., description="Health state")
    health_checked_at: Optional[datetime] = Field(
        default=None,
        description="Last health check timestamp",
    )
    health_message: Optional[str] = Field(
        default=None,
        description="Health check message",
    )
    default_model: Optional[str] = Field(default=None, description="Default model")
    budget_limit_cents: int = Field(..., description="Monthly budget limit (cents)")
    token_limit_month: int = Field(..., description="Monthly token limit")
    rate_limit_rpm: int = Field(..., description="Rate limit (RPM)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")

    # Note: credential_ref and config are NOT exposed in response for security

    class Config:
        from_attributes = True


class CusIntegrationSummary(BaseModel):
    """Integration summary for list views.

    PURPOSE:
        Lightweight representation for list endpoints.
        Excludes detailed config and health messages.
    """

    id: str = Field(..., description="Integration ID")
    name: str = Field(..., description="Integration name")
    provider_type: CusProviderType = Field(..., description="Provider type")
    status: CusIntegrationStatus = Field(..., description="Current status")
    health_state: CusHealthState = Field(..., description="Health state")
    default_model: Optional[str] = Field(default=None, description="Default model")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CusLimitsStatus(BaseModel):
    """Current usage vs configured limits.

    PURPOSE:
        Dashboard view showing how much of each limit has been used.
        Enables proactive budget and capacity management.
    """

    integration_id: str = Field(..., description="Integration ID")
    integration_name: str = Field(..., description="Integration name")

    # Budget
    budget_limit_cents: int = Field(..., description="Monthly budget limit (cents)")
    budget_used_cents: int = Field(..., description="Budget used this month (cents)")
    budget_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Budget usage percentage",
    )

    # Tokens
    token_limit_month: int = Field(..., description="Monthly token limit")
    tokens_used_month: int = Field(..., description="Tokens used this month")
    token_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Token usage percentage",
    )

    # Rate
    rate_limit_rpm: int = Field(..., description="Rate limit (RPM)")
    current_rpm: int = Field(..., description="Current requests per minute")
    rate_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Rate usage percentage",
    )

    # Period
    period_start: date = Field(..., description="Current billing period start")
    period_end: date = Field(..., description="Current billing period end")


class CusUsageSummary(BaseModel):
    """Aggregated usage statistics.

    PURPOSE:
        Summary view of usage across integrations.
        Used for dashboard totals and reports.
    """

    tenant_id: str = Field(..., description="Tenant ID")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")

    # Aggregates
    total_calls: int = Field(default=0, ge=0, description="Total LLM calls")
    total_tokens_in: int = Field(default=0, ge=0, description="Total input tokens")
    total_tokens_out: int = Field(default=0, ge=0, description="Total output tokens")
    total_cost_cents: int = Field(default=0, ge=0, description="Total cost (cents)")
    avg_latency_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Average latency (ms)",
    )
    error_count: int = Field(default=0, ge=0, description="Total errors")
    blocked_count: int = Field(default=0, ge=0, description="Policy-blocked calls")

    # Per-integration breakdown (optional)
    by_integration: Optional[List["CusIntegrationUsage"]] = Field(
        default=None,
        description="Breakdown by integration",
    )


class CusIntegrationUsage(BaseModel):
    """Usage for a single integration within a period.

    PURPOSE:
        Per-integration breakdown within CusUsageSummary.
    """

    integration_id: str = Field(..., description="Integration ID")
    integration_name: str = Field(..., description="Integration name")
    provider_type: CusProviderType = Field(..., description="Provider type")

    total_calls: int = Field(default=0, ge=0, description="Total calls")
    total_tokens: int = Field(default=0, ge=0, description="Total tokens")
    total_cost_cents: int = Field(default=0, ge=0, description="Total cost (cents)")
    error_count: int = Field(default=0, ge=0, description="Error count")


class CusLLMUsageResponse(BaseModel):
    """Individual usage record response.

    PURPOSE:
        Detailed view of a single LLM call for audit/debugging.
    """

    id: str = Field(..., description="Record ID")
    integration_id: str = Field(..., description="Integration ID")
    call_id: str = Field(..., description="SDK call ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    agent_id: Optional[str] = Field(default=None, description="Agent ID")

    provider: str = Field(..., description="Provider")
    model: str = Field(..., description="Model")
    tokens_in: int = Field(..., description="Input tokens")
    tokens_out: int = Field(..., description="Output tokens")
    cost_cents: int = Field(..., description="Cost (cents)")
    latency_ms: Optional[int] = Field(default=None, description="Latency (ms)")

    policy_result: CusPolicyResult = Field(..., description="Policy result")
    error_code: Optional[str] = Field(default=None, description="Error code")
    error_message: Optional[str] = Field(default=None, description="Error message")

    created_at: datetime = Field(..., description="Timestamp")

    class Config:
        from_attributes = True


# =============================================================================
# HEALTH CHECK RESPONSE
# =============================================================================


class CusHealthCheckResponse(BaseModel):
    """Response from integration health check.

    PURPOSE:
        Result of testing integration connectivity and credentials.
    """

    integration_id: str = Field(..., description="Integration ID")
    health_state: CusHealthState = Field(..., description="New health state")
    message: Optional[str] = Field(default=None, description="Health message")
    latency_ms: Optional[int] = Field(
        default=None,
        description="Health check latency (ms)",
    )
    checked_at: datetime = Field(..., description="Check timestamp")


# Update forward reference
CusUsageSummary.model_rebuild()
