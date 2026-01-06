"""Add approval_requests table for policy workflow

Revision ID: 005_add_approval_requests
Revises: 004_add_feature_flags_and_policy_approval
Create Date: 2025-12-03

This migration adds the approval_requests table for:
1. Persistent storage of policy approval requests
2. Transactional state machine for approval workflow
3. Webhook retry tracking
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_approval_requests"
down_revision: Union[str, None] = "004_add_feature_flags_and_policy_approval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create approval_requests table
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        # Correlation ID for webhook idempotency
        sa.Column("correlation_id", sa.String(32), nullable=True, unique=True),
        # Request metadata
        sa.Column("policy_type", sa.String(50), nullable=False, index=True),
        sa.Column("skill_id", sa.String(255), nullable=True, index=True),
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("agent_id", sa.String(255), nullable=True),
        # Request details
        sa.Column("requested_by", sa.String(255), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),  # JSON of execution payload
        # Status state machine: pending -> approved/rejected/escalated/expired
        sa.Column("status", sa.String(50), nullable=False, default="pending", index=True),
        sa.Column("status_history_json", sa.Text(), nullable=True),
        # Approval tracking
        sa.Column("required_level", sa.SmallInteger(), nullable=False, default=3),
        sa.Column("current_level", sa.SmallInteger(), nullable=False, default=0),
        sa.Column("approvals_json", sa.Text(), nullable=True),  # JSON array of approvals
        # Escalation config
        sa.Column("escalate_to", sa.String(255), nullable=True),
        sa.Column("escalation_timeout_seconds", sa.Integer(), nullable=False, default=300),
        # Webhook tracking
        sa.Column("webhook_url", sa.String(2048), nullable=True),
        sa.Column("webhook_secret_hash", sa.String(64), nullable=True),  # Store hash, not secret
        sa.Column("webhook_attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("last_webhook_status", sa.String(50), nullable=True),
        sa.Column("last_webhook_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for common queries
    op.create_index("ix_approval_requests_status_tenant", "approval_requests", ["status", "tenant_id"])

    op.create_index("ix_approval_requests_expires_status", "approval_requests", ["expires_at", "status"])

    op.create_index("ix_approval_requests_created_status", "approval_requests", ["created_at", "status"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_approval_requests_created_status", table_name="approval_requests")
    op.drop_index("ix_approval_requests_expires_status", table_name="approval_requests")
    op.drop_index("ix_approval_requests_status_tenant", table_name="approval_requests")

    # Drop table
    op.drop_table("approval_requests")
