"""M21: Tenant, Auth & Billing System

Creates tables for:
- tenants (organizations)
- users (user accounts linked to Clerk)
- tenant_memberships (user-tenant relationships)
- api_keys (programmatic access)
- subscriptions (billing plans)
- usage_records (metered billing)
- worker_configs (per-tenant worker settings)
- worker_runs (run tracking with tenant isolation)

Revision ID: 036_m21_tenant_auth
Revises: 035_m10_schema_repair
Create Date: 2024-12-16
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "036_m21_tenant_auth"
down_revision = "035_m10_schema_repair"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== TENANTS (Organizations) ==========
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("clerk_org_id", sa.String(100), nullable=True, unique=True),
        # Plan & Billing
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),  # free, pro, enterprise
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(100), nullable=True),
        # Quotas & Limits
        sa.Column("max_workers", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("max_runs_per_day", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_concurrent_runs", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_tokens_per_month", sa.BigInteger(), nullable=False, server_default="1000000"),
        sa.Column("max_api_keys", sa.Integer(), nullable=False, server_default="5"),
        # Usage Tracking
        sa.Column("runs_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("runs_this_month", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_this_month", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_run_reset_at", sa.DateTime(timezone=True), nullable=True),
        # Status
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),  # active, suspended, churned
        sa.Column("suspended_reason", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])
    op.create_index("ix_tenants_clerk_org_id", "tenants", ["clerk_org_id"])
    op.create_index("ix_tenants_plan", "tenants", ["plan"])

    # ========== USERS ==========
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("clerk_user_id", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        # Default tenant (for single-tenant users)
        sa.Column("default_tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=True),
        # Status
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),  # active, suspended, deleted
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_clerk_user_id", "users", ["clerk_user_id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ========== TENANT MEMBERSHIPS ==========
    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # Role within tenant
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),  # owner, admin, member, viewer
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("invited_by", sa.String(36), nullable=True),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
    )
    op.create_index("ix_tenant_memberships_tenant_id", "tenant_memberships", ["tenant_id"])
    op.create_index("ix_tenant_memberships_user_id", "tenant_memberships", ["user_id"])

    # ========== API KEYS ==========
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Key details
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),  # First 8 chars for display (aos_xxx...)
        sa.Column("key_hash", sa.String(128), nullable=False),  # SHA-256 hash of full key
        # Permissions & Scopes
        sa.Column("permissions_json", sa.Text(), nullable=True),  # JSON array of allowed permissions
        sa.Column("allowed_workers_json", sa.Text(), nullable=True),  # JSON array of worker IDs (null = all)
        # Rate Limits (per-key override)
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=True),  # null = use tenant default
        sa.Column("max_concurrent_runs", sa.Integer(), nullable=True),
        # Status & Lifecycle
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),  # active, revoked, expired
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(255), nullable=True),
        # Usage tracking
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_requests", sa.BigInteger(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])

    # ========== SUBSCRIPTIONS ==========
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        # Plan details
        sa.Column("plan", sa.String(50), nullable=False),  # free, pro, enterprise
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="active"
        ),  # active, canceled, past_due, trialing
        # Stripe integration
        sa.Column("stripe_subscription_id", sa.String(100), nullable=True),
        sa.Column("stripe_price_id", sa.String(100), nullable=True),
        # Billing period
        sa.Column("billing_period", sa.String(20), nullable=False, server_default="monthly"),  # monthly, annual
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        # Trial
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        # Cancellation
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default="false"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])

    # ========== USAGE RECORDS ==========
    op.create_table(
        "usage_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        # Usage details
        sa.Column("meter_name", sa.String(100), nullable=False),  # worker_runs, api_calls, tokens_used, etc.
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False, server_default="count"),  # count, tokens, seconds
        # Period
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        # Metadata
        sa.Column("worker_id", sa.String(100), nullable=True),
        sa.Column("api_key_id", sa.String(36), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_usage_records_tenant_id", "usage_records", ["tenant_id"])
    op.create_index("ix_usage_records_meter_name", "usage_records", ["meter_name"])
    op.create_index("ix_usage_records_period", "usage_records", ["period_start", "period_end"])

    # ========== WORKER REGISTRY ==========
    op.create_table(
        "worker_registry",
        sa.Column("id", sa.String(100), primary_key=True),  # e.g., 'business-builder'
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        # Status
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="available"
        ),  # available, beta, coming_soon, deprecated
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        # Configuration
        sa.Column("moats_json", sa.Text(), nullable=True),  # JSON array of moat IDs (M9, M10, etc.)
        sa.Column("default_config_json", sa.Text(), nullable=True),  # Default worker configuration
        sa.Column("input_schema_json", sa.Text(), nullable=True),  # JSON Schema for worker inputs
        sa.Column("output_schema_json", sa.Text(), nullable=True),  # JSON Schema for worker outputs
        # Pricing
        sa.Column("tokens_per_run_estimate", sa.Integer(), nullable=True),
        sa.Column("cost_per_run_cents", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_worker_registry_status", "worker_registry", ["status"])

    # ========== WORKER CONFIGS (Per-Tenant) ==========
    op.create_table(
        "worker_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("worker_id", sa.String(100), sa.ForeignKey("worker_registry.id", ondelete="CASCADE"), nullable=False),
        # Configuration overrides
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config_json", sa.Text(), nullable=True),  # Tenant-specific config overrides
        sa.Column("brand_json", sa.Text(), nullable=True),  # Default brand for this worker
        # Limits
        sa.Column("max_runs_per_day", sa.Integer(), nullable=True),  # Override tenant default
        sa.Column("max_tokens_per_run", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "worker_id", name="uq_tenant_worker"),
    )
    op.create_index("ix_worker_configs_tenant_id", "worker_configs", ["tenant_id"])
    op.create_index("ix_worker_configs_worker_id", "worker_configs", ["worker_id"])

    # ========== WORKER RUNS (With Tenant Isolation) ==========
    op.create_table(
        "worker_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("worker_id", sa.String(100), sa.ForeignKey("worker_registry.id"), nullable=False),
        sa.Column("api_key_id", sa.String(36), sa.ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Task details
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=True),  # Full input including brand
        # Status
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="queued"
        ),  # queued, running, completed, failed
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        # Results
        sa.Column("output_json", sa.Text(), nullable=True),  # Artifacts and results
        sa.Column("replay_token_json", sa.Text(), nullable=True),  # M4 Golden Replay token
        # Metrics
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("stages_completed", sa.Integer(), nullable=True),
        sa.Column("recoveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("policy_violations", sa.Integer(), nullable=False, server_default="0"),
        # Cost
        sa.Column("cost_cents", sa.Integer(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_worker_runs_tenant_id", "worker_runs", ["tenant_id"])
    op.create_index("ix_worker_runs_worker_id", "worker_runs", ["worker_id"])
    op.create_index("ix_worker_runs_status", "worker_runs", ["status"])
    op.create_index("ix_worker_runs_created_at", "worker_runs", ["created_at"])
    op.create_index("ix_worker_runs_tenant_created", "worker_runs", ["tenant_id", "created_at"])

    # ========== AUDIT LOG ==========
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("api_key_id", sa.String(36), nullable=True),
        # Action details
        sa.Column("action", sa.String(100), nullable=False),  # create_run, revoke_key, update_config, etc.
        sa.Column("resource_type", sa.String(50), nullable=False),  # run, api_key, worker_config, etc.
        sa.Column("resource_id", sa.String(100), nullable=True),
        # Request details
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        # Changes
        sa.Column("old_value_json", sa.Text(), nullable=True),
        sa.Column("new_value_json", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])

    # ========== INSERT DEFAULT WORKERS ==========
    op.execute(
        """
        INSERT INTO worker_registry (id, name, description, version, status, is_public, moats_json, tokens_per_run_estimate, cost_per_run_cents)
        VALUES
        ('business-builder', 'Business Builder', 'Generate complete landing pages, copy, positioning, and marketing assets from a brand strategy.', '0.2.0', 'available', true, '["M4","M9","M10","M15","M17","M18","M19","M20"]', 50000, 50),
        ('code-debugger', 'Code Debugger', 'Analyze codebases, identify bugs, and suggest fixes with full traceability.', '0.1.0', 'coming_soon', true, '["M9","M10","M17","M19"]', 30000, 30),
        ('repo-fixer', 'Repo Fixer', 'Automatically fix CI failures, dependency issues, and code quality problems.', '0.1.0', 'coming_soon', true, '["M9","M10","M17","M18","M19"]', 40000, 40),
        ('research-analyst', 'Research Analyst', 'Deep research on markets, competitors, and trends with structured output.', '0.1.0', 'coming_soon', true, '["M15","M17","M19"]', 25000, 25)
        ON CONFLICT (id) DO NOTHING;
    """
    )

    # ========== INSERT DEFAULT PLANS (for reference) ==========
    # Plans are codified in application logic, but we document them here:
    # free: 100 runs/day, 3 workers, 5 API keys, 1M tokens/month
    # pro: 1000 runs/day, 10 workers, 20 API keys, 10M tokens/month
    # enterprise: unlimited


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("worker_runs")
    op.drop_table("worker_configs")
    op.drop_table("worker_registry")
    op.drop_table("usage_records")
    op.drop_table("subscriptions")
    op.drop_table("api_keys")
    op.drop_table("tenant_memberships")
    op.drop_table("users")
    op.drop_table("tenants")
