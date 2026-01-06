"""PC: Discovery Ledger - Phase C observational signal log

Revision ID: 059_pc_discovery_ledger
Revises: 058_pb_s5_prediction_events
Create Date: 2025-12-27

Phase C introduces the Discovery Ledger - a passive, append-only system that:
- Records interesting signals the system notices
- Does NOT enforce visibility
- Does NOT require approval
- Does NOT block progress

This is internal development tooling, not customer governance.

Reference: Phase C Discovery Ledger design
Truth anchor: "Discovery Ledger records curiosity, not decisions."
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "059_pc_discovery_ledger"
down_revision = "058_pb_s5_prediction_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Discovery Ledger - append-only observation log
    # No foreign keys to execution tables (no coupling)
    # Can be dropped later with zero blast radius
    op.create_table(
        "discovery_ledger",
        # Primary key
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        # What was noticed
        sa.Column("artifact", sa.Text(), nullable=False),  # e.g. prediction_events
        sa.Column("field", sa.Text(), nullable=True),  # e.g. confidence (nullable)
        sa.Column("signal_type", sa.Text(), nullable=False),  # enum-like string
        # Why it was noticed
        sa.Column("evidence", postgresql.JSONB(), nullable=False),  # counts, queries, references
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),  # optional 0.00-1.00
        # Context
        sa.Column("detected_by", sa.Text(), nullable=False),  # subsystem name
        sa.Column("phase", sa.Text(), nullable=False),  # B / C / D
        sa.Column("environment", sa.Text(), nullable=False),  # local / staging / prod
        # Lifecycle (passive)
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("seen_count", sa.Integer(), server_default="1", nullable=False),
        # Explicitly non-enforcing
        # 'observed' = just noticed
        # 'ignored' = human decided not interesting
        # 'promoted' = human decided to make visible (manually)
        sa.Column("status", sa.Text(), server_default="observed", nullable=False),
        # Metadata
        sa.Column("notes", sa.Text(), nullable=True),
        # Constraint: status must be one of the allowed values
        sa.CheckConstraint("status IN ('observed', 'ignored', 'promoted')", name="ck_discovery_ledger_status"),
    )

    # Indexes for common queries
    op.create_index("ix_discovery_ledger_artifact", "discovery_ledger", ["artifact"])
    op.create_index("ix_discovery_ledger_signal_type", "discovery_ledger", ["signal_type"])
    op.create_index("ix_discovery_ledger_status", "discovery_ledger", ["status"])
    op.create_index("ix_discovery_ledger_last_seen", "discovery_ledger", ["last_seen_at"])

    # Unique constraint on (artifact, field, signal_type) for upsert pattern
    # This allows aggregating signals instead of spamming rows
    op.create_index(
        "ix_discovery_ledger_unique_signal",
        "discovery_ledger",
        ["artifact", "field", "signal_type"],
        unique=True,
        postgresql_where=sa.text("field IS NOT NULL"),
    )

    # For artifact-level signals (no field)
    op.create_index(
        "ix_discovery_ledger_unique_signal_no_field",
        "discovery_ledger",
        ["artifact", "signal_type"],
        unique=True,
        postgresql_where=sa.text("field IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_discovery_ledger_unique_signal_no_field")
    op.drop_index("ix_discovery_ledger_unique_signal")
    op.drop_index("ix_discovery_ledger_last_seen")
    op.drop_index("ix_discovery_ledger_status")
    op.drop_index("ix_discovery_ledger_signal_type")
    op.drop_index("ix_discovery_ledger_artifact")
    op.drop_table("discovery_ledger")
