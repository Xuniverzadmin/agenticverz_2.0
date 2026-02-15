# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add controls_evaluation_evidence table for UC-MON-02 per-run control binding
# Reference: UC-MON (Monitoring), UC_MONITORING_IMPLEMENTATION_METHODS.md

"""Add controls_evaluation_evidence table for UC-MON-02

Revision ID: 130_monitoring_controls_binding_fields
Revises: 129_monitoring_incident_resolution_recurrence
Create Date: 2026-02-11

Purpose:
Persist per-run control evaluation evidence with version binding.
Supports UC-MON-02 control decision audit lineage.
Fields: control_set_version, override_ids_applied (JSONB), resolver_version, decision.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "130_monitoring_controls_binding_fields"
down_revision = "129_monitoring_incident_resolution_recurrence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "controls_evaluation_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("control_set_version", sa.String(length=64), nullable=False),
        sa.Column("override_ids_applied", postgresql.JSONB(), nullable=True),
        sa.Column("resolver_version", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_controls_eval_tenant_run",
        "controls_evaluation_evidence",
        ["tenant_id", "run_id"],
    )
    op.create_index(
        "ix_controls_eval_version",
        "controls_evaluation_evidence",
        ["control_set_version"],
    )


def downgrade() -> None:
    op.drop_index("ix_controls_eval_version", table_name="controls_evaluation_evidence")
    op.drop_index("ix_controls_eval_tenant_run", table_name="controls_evaluation_evidence")
    op.drop_table("controls_evaluation_evidence")
