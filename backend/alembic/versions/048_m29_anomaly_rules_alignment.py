"""M29 Category 4: Anomaly Rules Alignment

Adds:
1. cost_breach_history table for consecutive interval tracking
2. derived_cause column to cost_anomalies

The Plan:
- Absolute spike: 1.4x threshold + 2 consecutive daily intervals
- Sustained drift: 7d rolling > 1.25x baseline for >= 3 days
- Severity bands: LOW 15-25%, MED 25-40%, HIGH >40%

Revision ID: 048_m29_anomaly_rules
Revises: 047_m27_cost_snapshots
Create Date: 2025-12-24
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "048_m29_anomaly_rules"
down_revision = "047_m27_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create breach history table for consecutive interval tracking
    op.create_table(
        "cost_breach_history",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("entity_type", sa.String(32), nullable=False),  # user, feature, tenant, model
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("breach_type", sa.String(32), nullable=False),  # ABSOLUTE_SPIKE, SUSTAINED_DRIFT
        sa.Column("breach_date", sa.Date(), nullable=False),
        sa.Column("deviation_pct", sa.Float(), nullable=False),
        sa.Column("current_value_cents", sa.Float(), nullable=False),
        sa.Column("baseline_value_cents", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        # Unique constraint: one breach record per entity per day per breach_type
        sa.UniqueConstraint(
            "tenant_id", "entity_type", "entity_id", "breach_type", "breach_date", name="uq_breach_per_entity_day"
        ),
    )

    # Index for efficient consecutive interval queries
    op.create_index(
        "ix_breach_history_lookup",
        "cost_breach_history",
        ["tenant_id", "entity_type", "entity_id", "breach_type", "breach_date"],
    )

    # 2. Add derived_cause to cost_anomalies
    # Values: RETRY_LOOP, PROMPT_GROWTH, FEATURE_SURGE, TRAFFIC_GROWTH, UNKNOWN
    op.add_column(
        "cost_anomalies",
        sa.Column("derived_cause", sa.String(32), nullable=True),
    )

    # 3. Add breach_count to cost_anomalies (how many consecutive intervals)
    op.add_column(
        "cost_anomalies",
        sa.Column("breach_count", sa.Integer(), nullable=True, server_default="1"),
    )

    # 4. Create sustained drift tracking table
    op.create_table(
        "cost_drift_tracking",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("entity_type", sa.String(32), nullable=False),  # user, feature, tenant
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("rolling_7d_avg_cents", sa.Float(), nullable=False),
        sa.Column("baseline_7d_avg_cents", sa.Float(), nullable=False),
        sa.Column("drift_pct", sa.Float(), nullable=False),
        sa.Column("drift_days_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_drift_date", sa.Date(), nullable=False),
        sa.Column("last_check_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        # Unique constraint: one drift tracker per entity
        sa.UniqueConstraint("tenant_id", "entity_type", "entity_id", name="uq_drift_tracker_per_entity"),
    )


def downgrade() -> None:
    op.drop_table("cost_drift_tracking")
    op.drop_column("cost_anomalies", "breach_count")
    op.drop_column("cost_anomalies", "derived_cause")
    op.drop_index("ix_breach_history_lookup", "cost_breach_history")
    op.drop_table("cost_breach_history")
