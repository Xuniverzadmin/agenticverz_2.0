"""M23 AI Incident Console - User Tracking

Revision ID: 039_m23_user_tracking
Revises: 038_m24_ops_events
Create Date: 2025-12-20

This migration adds:
- user_id column to proxy_calls for end-user tracking (OpenAI standard `user` field)

The `user` field is an OpenAI standard parameter that allows customers to
identify end-users making requests. This enables:
- Per-user incident analysis
- End-user behavior tracking
- Compliance and audit trails

PIN-100 is the authoritative specification for M23.
"""

import sqlalchemy as sa

from alembic import op

revision = "039_m23_user_tracking"
down_revision = "038_m24_ops_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to proxy_calls for M23 end-user tracking
    op.add_column(
        "proxy_calls",
        sa.Column("user_id", sa.String(255), nullable=True),
    )

    # Create index for user_id queries (e.g., "all calls by this user")
    op.create_index(
        "ix_proxy_calls_user_id",
        "proxy_calls",
        ["user_id"],
        unique=False,
    )

    # Create composite index for tenant + user queries
    op.create_index(
        "ix_proxy_calls_tenant_user",
        "proxy_calls",
        ["tenant_id", "user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_proxy_calls_tenant_user", table_name="proxy_calls")
    op.drop_index("ix_proxy_calls_user_id", table_name="proxy_calls")
    op.drop_column("proxy_calls", "user_id")
