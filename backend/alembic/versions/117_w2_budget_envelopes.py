# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: GAP-168 (T3 Budget Migration)
"""Add budget_envelopes table for T3 governance

Revision ID: 117_w2_budget_envelopes
Revises: 116_w2_audit_events
Create Date: 2026-01-21

Reference: GAP-168 (T3 Budget Migration), GAP_IMPLEMENTATION_PLAN_V2.md

This migration creates the budget_envelopes table for T3 (Governance & Policy) tier.
Budget envelopes define cost and resource limits that are enforced during execution.

Purpose:
- Define cost budgets per tenant/project/run
- Track budget consumption in real-time
- Enable budget-based policy enforcement
- Support multi-currency and multi-resource budgets
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers
revision = "117_w2_budget_envelopes"
down_revision = "116_w2_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Create budget_envelopes table (GAP-168)
    # =========================================================================
    op.create_table(
        "budget_envelopes",
        # Primary key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("envelope_id", sa.String(64), nullable=False, unique=True, index=True),
        # Identity
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Scope
        sa.Column(
            "scope_type",
            sa.String(32),
            nullable=False,
            comment="Scope: tenant, project, user, run, agent",
        ),
        sa.Column(
            "scope_id",
            sa.String(100),
            nullable=True,
            comment="ID of the scoped entity (null for tenant scope)",
        ),
        # Budget limits
        sa.Column(
            "limit_type",
            sa.String(32),
            nullable=False,
            comment="Type: cost, tokens, requests, time",
        ),
        sa.Column(
            "limit_value",
            sa.BigInteger(),
            nullable=False,
            comment="Budget limit in smallest unit (cents, tokens, etc.)",
        ),
        sa.Column(
            "limit_unit",
            sa.String(16),
            nullable=False,
            server_default="cents",
            comment="Unit: cents, tokens, requests, seconds",
        ),
        # Time window
        sa.Column(
            "period_type",
            sa.String(32),
            nullable=False,
            server_default="monthly",
            comment="Period: hourly, daily, weekly, monthly, total",
        ),
        sa.Column(
            "period_start",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Start of current period (null for total)",
        ),
        sa.Column(
            "period_end",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="End of current period (null for total)",
        ),
        # Current usage
        sa.Column(
            "current_usage",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
            comment="Current usage in this period",
        ),
        sa.Column(
            "last_usage_update",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="When usage was last updated",
        ),
        # Alert thresholds (percentages)
        sa.Column(
            "warn_threshold_pct",
            sa.Integer(),
            nullable=False,
            server_default="80",
            comment="Warning threshold percentage (0-100)",
        ),
        sa.Column(
            "block_threshold_pct",
            sa.Integer(),
            nullable=False,
            server_default="100",
            comment="Blocking threshold percentage (0-100)",
        ),
        # Status
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="active",
            comment="Status: active, warned, blocked, suspended, archived",
        ),
        sa.Column(
            "last_alert_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="When the last alert was sent",
        ),
        sa.Column(
            "alert_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        # Policy reference
        sa.Column(
            "enforcement_policy_id",
            sa.String(64),
            nullable=True,
            comment="Policy to invoke when threshold exceeded",
        ),
        # Rollover settings
        sa.Column(
            "rollover_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether unused budget rolls over",
        ),
        sa.Column(
            "max_rollover_pct",
            sa.Integer(),
            nullable=True,
            comment="Maximum rollover percentage (0-100)",
        ),
        # Metadata
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("tags", JSONB, nullable=True, server_default="[]"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create indexes for common query patterns
    op.create_index(
        "ix_budget_envelopes_tenant_scope",
        "budget_envelopes",
        ["tenant_id", "scope_type", "scope_id"],
    )
    op.create_index(
        "ix_budget_envelopes_status",
        "budget_envelopes",
        ["status"],
        postgresql_where=sa.text("status IN ('warned', 'blocked')"),
    )
    op.create_index(
        "ix_budget_envelopes_period_end",
        "budget_envelopes",
        ["period_end"],
        postgresql_where=sa.text("period_end IS NOT NULL"),
    )

    # Create check constraints
    op.create_check_constraint(
        "ck_budget_envelopes_scope_type",
        "budget_envelopes",
        "scope_type IN ('tenant', 'project', 'user', 'run', 'agent')",
    )
    op.create_check_constraint(
        "ck_budget_envelopes_limit_type",
        "budget_envelopes",
        "limit_type IN ('cost', 'tokens', 'requests', 'time', 'storage')",
    )
    op.create_check_constraint(
        "ck_budget_envelopes_period_type",
        "budget_envelopes",
        "period_type IN ('hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'total')",
    )
    op.create_check_constraint(
        "ck_budget_envelopes_status",
        "budget_envelopes",
        "status IN ('active', 'warned', 'blocked', 'suspended', 'archived')",
    )
    op.create_check_constraint(
        "ck_budget_envelopes_limit_positive",
        "budget_envelopes",
        "limit_value > 0",
    )
    op.create_check_constraint(
        "ck_budget_envelopes_usage_non_negative",
        "budget_envelopes",
        "current_usage >= 0",
    )
    op.create_check_constraint(
        "ck_budget_envelopes_thresholds",
        "budget_envelopes",
        "warn_threshold_pct >= 0 AND warn_threshold_pct <= 100 AND "
        "block_threshold_pct >= 0 AND block_threshold_pct <= 100 AND "
        "warn_threshold_pct <= block_threshold_pct",
    )

    # Unique constraint on tenant + scope + limit_type
    op.create_unique_constraint(
        "uq_budget_envelopes_scope",
        "budget_envelopes",
        ["tenant_id", "scope_type", "scope_id", "limit_type"],
    )

    # Add comment to table
    op.execute("""
        COMMENT ON TABLE budget_envelopes IS
        'T3 budget envelopes for cost and resource governance (GAP-168). Defines limits, tracks usage, and triggers enforcement policies.';
    """)

    # =========================================================================
    # Create budget_usage_history table for tracking historical usage
    # =========================================================================
    op.create_table(
        "budget_usage_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "envelope_id",
            sa.String(64),
            sa.ForeignKey("budget_envelopes.envelope_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Usage record
        sa.Column("run_id", sa.String(100), nullable=True, index=True),
        sa.Column("step_index", sa.Integer(), nullable=True),
        sa.Column("usage_amount", sa.BigInteger(), nullable=False),
        sa.Column("usage_type", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Running totals
        sa.Column("envelope_usage_before", sa.BigInteger(), nullable=False),
        sa.Column("envelope_usage_after", sa.BigInteger(), nullable=False),
        # Timestamp
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_budget_usage_history_envelope_recorded",
        "budget_usage_history",
        ["envelope_id", sa.text("recorded_at DESC")],
    )

    # Add comment
    op.execute("""
        COMMENT ON TABLE budget_usage_history IS
        'Historical usage records for budget envelopes (GAP-168). Supports audit and trend analysis.';
    """)


def downgrade() -> None:
    # Drop budget_usage_history table
    op.drop_index("ix_budget_usage_history_envelope_recorded", table_name="budget_usage_history")
    op.drop_table("budget_usage_history")

    # Drop budget_envelopes constraints
    op.drop_constraint("uq_budget_envelopes_scope", "budget_envelopes", type_="unique")
    op.drop_constraint("ck_budget_envelopes_thresholds", "budget_envelopes", type_="check")
    op.drop_constraint("ck_budget_envelopes_usage_non_negative", "budget_envelopes", type_="check")
    op.drop_constraint("ck_budget_envelopes_limit_positive", "budget_envelopes", type_="check")
    op.drop_constraint("ck_budget_envelopes_status", "budget_envelopes", type_="check")
    op.drop_constraint("ck_budget_envelopes_period_type", "budget_envelopes", type_="check")
    op.drop_constraint("ck_budget_envelopes_limit_type", "budget_envelopes", type_="check")
    op.drop_constraint("ck_budget_envelopes_scope_type", "budget_envelopes", type_="check")

    # Drop indexes
    op.drop_index("ix_budget_envelopes_period_end", table_name="budget_envelopes")
    op.drop_index("ix_budget_envelopes_status", table_name="budget_envelopes")
    op.drop_index("ix_budget_envelopes_tenant_scope", table_name="budget_envelopes")

    # Drop the table
    op.drop_table("budget_envelopes")
