# Layer: L6 — Platform Substrate
# AUDIENCE: INTERNAL
# Role: Alembic migration to add is_frozen column to api_keys table
# Reference: INT-APIKEYS-BUG-001

"""Add is_frozen column to api_keys table.

Migration 037 added frozen_at, frozen_by, freeze_reason to api_keys,
but the is_frozen boolean field was missing, causing code-schema mismatch.

Revision ID: 120_is_frozen_api_keys
Revises: c8213cda2be4
Create Date: 2026-01-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '120_is_frozen_api_keys'
down_revision: Union[str, None] = 'c8213cda2be4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_frozen column to api_keys table."""
    op.add_column(
        "api_keys",
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    # Create index for efficient frozen key lookups
    op.create_index(
        "ix_api_keys_is_frozen",
        "api_keys",
        ["is_frozen", "tenant_id"]
    )


def downgrade() -> None:
    """Remove is_frozen column from api_keys table."""
    op.drop_index("ix_api_keys_is_frozen", table_name="api_keys")
    op.drop_column("api_keys", "is_frozen")
