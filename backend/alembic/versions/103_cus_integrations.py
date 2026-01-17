"""Customer Integrations - LLM Provider Management and Telemetry

Revision ID: 103_cus_integrations
Revises: 102_lessons_source_run_id_varchar
Create Date: 2026-01-17

PURPOSE:
    Creates the customer integrations infrastructure for managing external LLM
    providers and capturing usage telemetry. This enables customers to bring
    their own LLM credentials while AOS provides governance, visibility, and
    cost control.

TABLES CREATED:
    - cus_integrations: Customer LLM provider configurations (credentials, limits)
    - cus_llm_usage: Individual LLM call telemetry (tokens, cost, latency)
    - cus_usage_daily: Aggregated daily usage for dashboards and billing

REFERENCE:
    - docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
    - Design Spec: Customer Integration Design Specification
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "103_cus_integrations"
down_revision = "102_lessons_source_run_id_varchar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # CUS_INTEGRATIONS TABLE
    # ==========================================================================
    # Customer LLM provider configurations. Each integration represents a
    # governed external LLM execution surface with credentials, limits, and
    # health state.
    #
    # SEMANTIC: Control plane authority - defines WHAT integrations exist
    # and HOW they are configured.

    op.create_table(
        "cus_integrations",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Tenant ownership (required for isolation)
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        # Integration identity
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "provider_type",
            sa.String(50),
            nullable=False,
            comment="LLM provider: openai, anthropic, azure_openai, bedrock, custom",
        ),
        # Credential storage (encrypted reference, never raw key)
        sa.Column(
            "credential_ref",
            sa.Text(),
            nullable=False,
            comment="Encrypted credential or vault pointer - NEVER store raw API keys",
        ),
        # Configuration (provider-specific settings)
        sa.Column(
            "config",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Provider-specific config: base_url, org_id, api_version, etc.",
        ),
        # Lifecycle status
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="created",
            comment="Lifecycle: created, enabled, disabled, error",
        ),
        # Health monitoring
        sa.Column(
            "health_state",
            sa.String(20),
            nullable=False,
            server_default="unknown",
            comment="Health: unknown, healthy, degraded, failing",
        ),
        sa.Column("health_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health_message", sa.Text(), nullable=True),
        # Default model for this integration
        sa.Column("default_model", sa.String(100), nullable=True),
        # Governance limits
        sa.Column(
            "budget_limit_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Monthly budget limit in cents (0 = unlimited)",
        ),
        sa.Column(
            "token_limit_month",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
            comment="Monthly token limit (0 = unlimited)",
        ),
        sa.Column(
            "rate_limit_rpm",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Requests per minute limit (0 = unlimited)",
        ),
        # Audit fields
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(100), nullable=True, comment="User ID who created this integration"),
        # Soft delete support
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Constraints
    op.create_check_constraint(
        "cus_integrations_provider_type_check",
        "cus_integrations",
        "provider_type IN ('openai', 'anthropic', 'azure_openai', 'bedrock', 'custom')",
    )
    op.create_check_constraint(
        "cus_integrations_status_check",
        "cus_integrations",
        "status IN ('created', 'enabled', 'disabled', 'error')",
    )
    op.create_check_constraint(
        "cus_integrations_health_state_check",
        "cus_integrations",
        "health_state IN ('unknown', 'healthy', 'degraded', 'failing')",
    )

    # Unique constraint: one integration name per tenant
    op.create_unique_constraint(
        "cus_integrations_tenant_name_unique",
        "cus_integrations",
        ["tenant_id", "name"],
    )

    # Indexes for common queries
    op.create_index("ix_cus_integrations_tenant_status", "cus_integrations", ["tenant_id", "status"])
    op.create_index("ix_cus_integrations_tenant_provider", "cus_integrations", ["tenant_id", "provider_type"])

    # ==========================================================================
    # CUS_LLM_USAGE TABLE
    # ==========================================================================
    # Individual LLM call telemetry. Each row represents one LLM API call made
    # by a customer through the SDK. Used for cost tracking, analytics, and
    # governance enforcement.
    #
    # SEMANTIC: Data plane truth - records FACTS about what happened.
    # Append-only by design. call_id provides idempotency.

    op.create_table(
        "cus_llm_usage",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Ownership and context
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column(
            "integration_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to cus_integrations (no FK for performance)",
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True, comment="Optional session grouping"),
        sa.Column("agent_id", sa.String(100), nullable=True, comment="Agent that made this call"),
        # Idempotency key (SDK generates unique call_id per request)
        sa.Column(
            "call_id",
            sa.String(100),
            nullable=False,
            unique=True,
            comment="SDK-generated idempotency key for deduplication",
        ),
        # LLM call details
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, comment="Input/prompt tokens"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, comment="Output/completion tokens"),
        sa.Column("cost_cents", sa.Integer(), nullable=False, comment="Calculated cost in cents"),
        sa.Column("latency_ms", sa.Integer(), nullable=True, comment="Request latency in milliseconds"),
        # Policy enforcement result
        sa.Column(
            "policy_result",
            sa.String(20),
            nullable=False,
            server_default="allowed",
            comment="Enforcement result: allowed, warned, blocked",
        ),
        # Error tracking
        sa.Column("error_code", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Extensible metadata
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Additional context: prompt_hash, tool_calls, etc.",
        ),
        # Timestamp (used for partitioning)
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # Constraints
    op.create_check_constraint(
        "cus_llm_usage_policy_result_check",
        "cus_llm_usage",
        "policy_result IN ('allowed', 'warned', 'blocked')",
    )
    op.create_check_constraint(
        "cus_llm_usage_tokens_positive",
        "cus_llm_usage",
        "tokens_in >= 0 AND tokens_out >= 0",
    )

    # Indexes for common queries
    op.create_index("ix_cus_llm_usage_tenant_created", "cus_llm_usage", ["tenant_id", "created_at"])
    op.create_index(
        "ix_cus_llm_usage_tenant_integration_created",
        "cus_llm_usage",
        ["tenant_id", "integration_id", "created_at"],
    )
    op.create_index("ix_cus_llm_usage_tenant_agent_created", "cus_llm_usage", ["tenant_id", "agent_id", "created_at"])
    op.create_index("ix_cus_llm_usage_call_id", "cus_llm_usage", ["call_id"])

    # ==========================================================================
    # CUS_USAGE_DAILY TABLE
    # ==========================================================================
    # Pre-aggregated daily usage statistics. Populated by a scheduled job that
    # rolls up cus_llm_usage. Used for dashboards, billing, and limit checks.
    #
    # SEMANTIC: Derived data - computed from cus_llm_usage for performance.
    # Can be regenerated from source if needed.

    op.create_table(
        "cus_usage_daily",
        # Composite primary key
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        # Aggregated metrics
        sa.Column("total_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens_in", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_tokens_out", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_cost_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_count", sa.Integer(), nullable=False, server_default="0"),
        # Audit
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        # Primary key constraint
        sa.PrimaryKeyConstraint("tenant_id", "integration_id", "date"),
    )

    # Index for date range queries
    op.create_index("ix_cus_usage_daily_tenant_date", "cus_usage_daily", ["tenant_id", "date"])

    # ==========================================================================
    # TRIGGER: Auto-update updated_at on cus_integrations
    # ==========================================================================

    op.execute(
        """
        CREATE OR REPLACE FUNCTION cus_integrations_update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER cus_integrations_updated_at
        BEFORE UPDATE ON cus_integrations
        FOR EACH ROW
        EXECUTE FUNCTION cus_integrations_update_timestamp();
    """
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS cus_integrations_updated_at ON cus_integrations")
    op.execute("DROP FUNCTION IF EXISTS cus_integrations_update_timestamp()")

    # Drop tables in reverse order
    op.drop_table("cus_usage_daily")
    op.drop_table("cus_llm_usage")
    op.drop_table("cus_integrations")
