# Layer: L6 — Platform (Database Migration)
# Product: system-wide
"""Add run_id to prevention_records

Revision ID: 124_prevention_records_run_id
Revises: 123_incidents_source_run_fk
Create Date: 2026-02-09

NOTE: Creates prevention_records table if missing (local/staging DBs stamped
past migration 043 without running it). Includes all columns from 043/044/077/079.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "124_prevention_records_run_id"
down_revision = "123_incidents_source_run_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if "prevention_records" not in tables:
        # Table missing (local/staging DB stamped past 043). Create with ALL columns.
        op.create_table(
            "prevention_records",
            # Original columns (043)
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("policy_id", sa.String(64), nullable=False),
            sa.Column("pattern_id", sa.String(64), nullable=False),
            sa.Column("original_incident_id", sa.String(64), nullable=False),
            sa.Column("blocked_incident_id", sa.String(64), nullable=False),
            sa.Column("tenant_id", sa.String(64), nullable=False),
            sa.Column("outcome", sa.String(32), nullable=False),
            sa.Column("signature_match_confidence", sa.Float, nullable=False),
            sa.Column("policy_age_seconds", sa.Integer),
            sa.Column("calls_evaluated", sa.Integer, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            # Added by 044
            sa.Column("is_simulated", sa.Boolean, server_default="false"),
            # Added by 077
            sa.Column("synthetic_scenario_id", sa.String(64), nullable=True),
            # Added by 079
            sa.Column("is_synthetic", sa.Boolean, nullable=False, server_default=sa.text("false")),
            # This migration (124)
            sa.Column("run_id", sa.String(64), nullable=True),
        )
        # Indexes from 043
        op.create_index("idx_prevention_policy", "prevention_records", ["policy_id"])
        op.create_index("idx_prevention_pattern", "prevention_records", ["pattern_id"])
        op.create_index("idx_prevention_tenant", "prevention_records", ["tenant_id", "created_at"])
        # Index from 077
        op.create_index(
            "ix_prevention_records_scenario",
            "prevention_records",
            ["synthetic_scenario_id"],
            postgresql_where=sa.text("synthetic_scenario_id IS NOT NULL"),
        )
        # Index from 079
        op.create_index(
            "ix_prevention_records_sdsr",
            "prevention_records",
            ["is_synthetic", "synthetic_scenario_id"],
        )
    else:
        # Table exists — just add run_id column
        op.add_column("prevention_records", sa.Column("run_id", sa.String(64), nullable=True))

    # Index for run_id (always created)
    op.create_index("ix_prevention_records_run_id", "prevention_records", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_prevention_records_run_id", table_name="prevention_records")
    op.drop_column("prevention_records", "run_id")
