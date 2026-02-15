# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create sdk_attestations table for UC-002 SDK handshake persistence
# Reference: UC-002 (Customer Onboarding), DOMAIN_REPAIR_PLAN_UC001_UC002_v2

"""Create sdk_attestations table

Revision ID: 127_create_sdk_attestations
Revises: 126_s6_trace_completion_allowed
Create Date: 2026-02-11

Purpose:
SDK attestation persistence for UC-002 Customer Onboarding.
Tracks SDK handshake records per tenant for onboarding activation predicate.
"""

from alembic import op
import sqlalchemy as sa

revision = "127_create_sdk_attestations"
down_revision = "126_s6_trace_completion_allowed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sdk_attestations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("sdk_version", sa.String(length=100), nullable=False),
        sa.Column("sdk_language", sa.String(length=50), nullable=False),
        sa.Column("client_id", sa.String(length=200), nullable=True),
        sa.Column("attested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attestation_hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "attestation_hash", name="uq_sdk_attestations_tenant_hash"),
    )
    op.create_index(
        "ix_sdk_attestations_tenant_id",
        "sdk_attestations",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sdk_attestations_tenant_id", table_name="sdk_attestations")
    op.drop_table("sdk_attestations")
