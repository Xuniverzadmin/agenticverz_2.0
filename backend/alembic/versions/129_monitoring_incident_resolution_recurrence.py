# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add resolution and recurrence fields to incidents table for UC-MON-05
# Reference: UC-MON (Monitoring), UC_MONITORING_IMPLEMENTATION_METHODS.md

"""Add incident resolution and recurrence fields for UC-MON-05

Revision ID: 129_monitoring_incident_resolution_recurrence
Revises: 128_monitoring_activity_feedback_contracts
Create Date: 2026-02-11

Purpose:
Extend incidents table with resolution lifecycle and recurrence grouping fields.
Supports UC-MON-05 incident lifecycle closure invariants.
Fields: resolution_type, resolution_summary, postmortem_artifact_id,
        recurrence_signature, signature_version.
"""

from alembic import op
import sqlalchemy as sa

revision = "129_monitoring_incident_resolution_recurrence"
down_revision = "128_monitoring_activity_feedback_contracts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("resolution_type", sa.String(length=50), nullable=True))
    op.add_column("incidents", sa.Column("resolution_summary", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("postmortem_artifact_id", sa.String(length=64), nullable=True))
    op.add_column("incidents", sa.Column("recurrence_signature", sa.String(length=128), nullable=True))
    op.add_column("incidents", sa.Column("signature_version", sa.String(length=20), nullable=True))
    op.create_index(
        "ix_incidents_recurrence_signature",
        "incidents",
        ["recurrence_signature"],
    )


def downgrade() -> None:
    op.drop_index("ix_incidents_recurrence_signature", table_name="incidents")
    op.drop_column("incidents", "signature_version")
    op.drop_column("incidents", "recurrence_signature")
    op.drop_column("incidents", "postmortem_artifact_id")
    op.drop_column("incidents", "resolution_summary")
    op.drop_column("incidents", "resolution_type")
