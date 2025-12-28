"""PB-S5: Prediction Events Table

This migration creates the prediction_events table for storing
predictions WITHOUT affecting execution behavior.

PB-S5 Guarantee: Advise → Observe → Do Nothing
- Predictions are advisory only
- Predictions have zero side-effects
- Predictions never modify execution, scheduling, or history
- Predictions are clearly labeled as estimates, not facts

Revision ID: 058_pb_s5_prediction_events
Revises: 057_pb_s4_policy_proposals
Create Date: 2025-12-27

CRITICAL: Predictions are INERT. They cannot influence execution.
No execution data is ever modified by predictions.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers
revision = "058_pb_s5_prediction_events"
down_revision = "057_pb_s4_policy_proposals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create prediction_events table for PB-S5."""

    # ============================================================
    # STEP 1: Create prediction_events table
    # ============================================================
    # Note: tenant_id is VARCHAR to match existing tenants table schema
    # Note: subject_id is VARCHAR (reference only, NOT FK to preserve independence)
    op.create_table(
        "prediction_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
        # Prediction identification
        sa.Column("prediction_type", sa.String(50), nullable=False, index=True),  # failure_likelihood, cost_overrun
        sa.Column("subject_type", sa.String(50), nullable=False),  # worker, run, tenant
        sa.Column("subject_id", sa.String(255), nullable=False),  # Reference only, NOT FK
        # Prediction content
        sa.Column("confidence_score", sa.Float, nullable=False),  # 0.0 - 1.0
        sa.Column("prediction_value", JSONB, nullable=False),  # Projected outcome
        sa.Column("contributing_factors", JSONB, nullable=False, default=[]),  # Features used
        # Validity window
        sa.Column("valid_until", sa.DateTime, nullable=True),  # Prediction expiry
        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        # Advisory flag - ALWAYS TRUE (enforced by design)
        sa.Column("is_advisory", sa.Boolean, nullable=False, default=True),
        # Optional notes for context
        sa.Column("notes", sa.Text, nullable=True),
    )

    # ============================================================
    # STEP 2: Add indexes for common queries
    # ============================================================
    op.create_index(
        "ix_prediction_events_tenant_type",
        "prediction_events",
        ["tenant_id", "prediction_type"],
    )
    op.create_index(
        "ix_prediction_events_subject",
        "prediction_events",
        ["subject_type", "subject_id"],
    )
    op.create_index(
        "ix_prediction_events_created_at",
        "prediction_events",
        ["created_at"],
    )
    # Note: Partial index with NOW() not supported (non-immutable function)
    # Using a regular index instead; filtering done at query time
    op.create_index(
        "ix_prediction_events_valid",
        "prediction_events",
        ["tenant_id", "valid_until"],
    )

    # ============================================================
    # STEP 3: Add table comment documenting PB-S5 contract
    # ============================================================
    op.execute(
        """
        COMMENT ON TABLE prediction_events IS
        'PB-S5 Prediction Events: Advisory predictions about future outcomes. '
        'This table is SEPARATE from execution tables. '
        'Predictions are INERT - they cannot modify execution behavior. '
        'No execution data (worker_runs, traces, costs) may be modified by predictions. '
        'Predictions are estimates, NOT facts. '
        'Rule: Advise → Observe → Do Nothing.';
    """
    )


def downgrade() -> None:
    """Remove prediction_events table."""
    op.drop_index("ix_prediction_events_valid", table_name="prediction_events")
    op.drop_index("ix_prediction_events_created_at", table_name="prediction_events")
    op.drop_index("ix_prediction_events_subject", table_name="prediction_events")
    op.drop_index("ix_prediction_events_tenant_type", table_name="prediction_events")
    op.drop_table("prediction_events")
