"""M26 Cost Intelligence Tables

Revision ID: 046_m26_cost_intelligence
Revises: 045_m25_policy_activation_audit
Create Date: 2025-12-23

M26 Core Objective:
Every token spent is attributable to tenant → user → feature → request.
Every anomaly must trigger an action, not a chart.

Tables:
- feature_tags: Registered feature namespaces (customer_support.chat, etc.)
- cost_records: High-volume raw metering (append-only)
- cost_anomalies: Detected cost issues
- cost_budgets: Per-tenant and per-feature budget limits
- cost_daily_aggregates: Pre-aggregated for fast dashboard reads
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers
revision = "046_m26_cost"
down_revision = "045_m25_policy_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create M26 cost intelligence tables."""

    # Drop old cost_records table if it exists (from costsim, empty table with different schema)
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'cost_records' AND column_name = 'execution_id'"
        )
    )
    old_schema_exists = result.fetchone() is not None
    if old_schema_exists:
        # This is the old costsim table with execution_id column
        # Drop indexes first
        conn.execute(sa.text("DROP INDEX IF EXISTS ix_cost_records_execution_id"))
        conn.execute(sa.text("DROP INDEX IF EXISTS ix_cost_records_skill_time"))
        op.drop_table("cost_records")

    # 1. feature_tags - Registered feature namespaces
    # This is the KEY UNLOCK for: feature ROI, kill-switch precision, product pricing
    op.create_table(
        "feature_tags",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("tag", sa.String(128), nullable=False),  # e.g., "customer_support.chat"
        sa.Column("display_name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("budget_cents", sa.Integer(), nullable=True),  # Per-feature budget
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "tag", name="uq_feature_tags_tenant_tag"),
    )
    op.create_index("ix_feature_tags_tag", "feature_tags", ["tag"])

    # 2. cost_records - High-volume raw metering (append-only)
    # Design rule: Raw writes fast, reads aggregated.
    op.create_table(
        "cost_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("user_id", sa.String(64), nullable=True, index=True),  # Who made the request
        sa.Column("feature_tag", sa.String(128), nullable=True, index=True),  # Which feature
        sa.Column("request_id", sa.String(64), nullable=True),  # Trace linkage
        sa.Column("workflow_id", sa.String(64), nullable=True),
        sa.Column("skill_id", sa.String(64), nullable=True),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_cents", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    # Composite index for time-series queries
    op.create_index("ix_cost_records_tenant_created", "cost_records", ["tenant_id", "created_at"])
    # Index for feature-level aggregation
    op.create_index("ix_cost_records_tenant_feature", "cost_records", ["tenant_id", "feature_tag"])
    # Index for user-level aggregation
    op.create_index("ix_cost_records_tenant_user", "cost_records", ["tenant_id", "user_id"])

    # 3. cost_anomalies - Detected cost issues
    # Four signals initially: USER_SPIKE, FEATURE_SPIKE, BUDGET_WARNING, BUDGET_EXCEEDED
    op.create_table(
        "cost_anomalies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column(
            "anomaly_type", sa.String(32), nullable=False
        ),  # USER_SPIKE, FEATURE_SPIKE, BUDGET_WARNING, BUDGET_EXCEEDED
        sa.Column("severity", sa.String(16), nullable=False),  # LOW, MEDIUM, HIGH, CRITICAL
        sa.Column("entity_type", sa.String(32), nullable=False),  # user, feature, model, tenant
        sa.Column("entity_id", sa.String(128), nullable=True),  # user_id, feature_tag, model name
        sa.Column("current_value_cents", sa.Float(), nullable=False),
        sa.Column("expected_value_cents", sa.Float(), nullable=False),
        sa.Column("deviation_pct", sa.Float(), nullable=False),
        sa.Column("threshold_pct", sa.Float(), nullable=False, server_default="200"),  # What deviation % triggered this
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("incident_id", sa.String(64), nullable=True),  # Link to M25 incident if escalated
        sa.Column("action_taken", sa.String(64), nullable=True),  # What action was taken
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_cost_anomalies_tenant_detected", "cost_anomalies", ["tenant_id", "detected_at"])
    op.create_index("ix_cost_anomalies_type", "cost_anomalies", ["anomaly_type"])
    op.create_index("ix_cost_anomalies_severity", "cost_anomalies", ["severity"])
    op.create_index("ix_cost_anomalies_incident", "cost_anomalies", ["incident_id"])

    # 4. cost_budgets - Per-tenant and per-feature budget limits
    op.create_table(
        "cost_budgets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("budget_type", sa.String(32), nullable=False),  # tenant, feature, user
        sa.Column(
            "entity_id", sa.String(128), nullable=True
        ),  # null for tenant-level, feature_tag or user_id for entity-level
        sa.Column("daily_limit_cents", sa.Integer(), nullable=True),
        sa.Column("monthly_limit_cents", sa.Integer(), nullable=True),
        sa.Column("warn_threshold_pct", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("hard_limit_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "budget_type", "entity_id", name="uq_cost_budgets_tenant_type_entity"),
    )

    # 5. cost_daily_aggregates - Pre-aggregated for fast dashboard reads
    # Never dashboard off raw rows.
    op.create_table(
        "cost_daily_aggregates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("feature_tag", sa.String(128), nullable=True),  # null for tenant-level
        sa.Column("user_id", sa.String(64), nullable=True),  # null for tenant/feature-level
        sa.Column("model", sa.String(64), nullable=True),  # null for higher-level aggregates
        sa.Column("total_cost_cents", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_input_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        # Composite unique constraint for upsert
        sa.UniqueConstraint("tenant_id", "date", "feature_tag", "user_id", "model", name="uq_cost_daily_agg_composite"),
    )
    op.create_index("ix_cost_daily_agg_tenant_date", "cost_daily_aggregates", ["tenant_id", "date"])
    op.create_index("ix_cost_daily_agg_feature", "cost_daily_aggregates", ["tenant_id", "feature_tag", "date"])


def downgrade() -> None:
    """Drop M26 cost intelligence tables."""
    op.drop_table("cost_daily_aggregates")
    op.drop_table("cost_budgets")
    op.drop_table("cost_anomalies")
    op.drop_table("cost_records")
    op.drop_table("feature_tags")
