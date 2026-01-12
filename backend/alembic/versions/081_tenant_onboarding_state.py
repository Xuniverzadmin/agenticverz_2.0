# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add onboarding_state column to tenants table
# Reference: PIN-399 (Onboarding State Machine v1)

"""Add onboarding_state column to tenants table

Revision ID: 081_tenant_onboarding_state
Revises: 080_trace_archival_columns
Create Date: 2026-01-12

PIN-399: Onboarding State Machine v1

This migration adds the `onboarding_state` column to the tenants table.
The column is the sole authority for bootstrap permissions.

States (as integers for comparison):
    0 = CREATED
    1 = IDENTITY_VERIFIED
    2 = API_KEY_CREATED
    3 = SDK_CONNECTED
    4 = COMPLETE

Design Invariants:
- ONBOARD-001: State is the sole authority for bootstrap permissions
- ONBOARD-002: Roles and plans do not apply before COMPLETE
- ONBOARD-003: Founders and customers follow identical state transitions
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "081_tenant_onboarding_state"
# NOTE: Skipping 079-080 as they reference non-existent tables (prevention_records)
# Database is currently at 078_aos_traces_sdsr_columns
down_revision = "078_aos_traces_sdsr_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add onboarding_state column to tenants table.

    - Type: Integer (for enum comparison)
    - Default: 0 (CREATED)
    - Non-nullable
    - Indexed (for query performance)
    """
    op.add_column(
        "tenants",
        sa.Column(
            "onboarding_state",
            sa.Integer(),
            nullable=False,
            server_default="0",  # CREATED
            comment="PIN-399: Onboarding state (0=CREATED, 1=IDENTITY_VERIFIED, 2=API_KEY_CREATED, 3=SDK_CONNECTED, 4=COMPLETE)",
        ),
    )

    # Index for filtering by onboarding state
    op.create_index(
        "idx_tenants_onboarding_state",
        "tenants",
        ["onboarding_state"],
    )


def downgrade() -> None:
    """Remove onboarding_state column from tenants table."""
    op.drop_index("idx_tenants_onboarding_state", "tenants")
    op.drop_column("tenants", "onboarding_state")
