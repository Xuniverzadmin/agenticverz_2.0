"""Create workflow_checkpoints table with M4 hardening columns

Revision ID: 001_workflow_checkpoints
Revises: None
Create Date: 2025-12-01

This migration creates the workflow_checkpoints table with:
- Primary key: run_id
- Optimistic locking: version column
- Multi-tenant support: tenant_id with index
- Debugging fields: started_at, ended_at
- Size guard: max_step_outputs_bytes constraint
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_workflow_checkpoints"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflow_checkpoints table
    op.create_table(
        "workflow_checkpoints",
        sa.Column("run_id", sa.String(255), primary_key=True),
        sa.Column("workflow_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("tenant_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("next_step_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_result_hash", sa.String(64), nullable=True),
        sa.Column("step_outputs_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on run_id (already primary key, but explicit for queries)
    op.create_index("ix_workflow_checkpoints_run_id", "workflow_checkpoints", ["run_id"])

    # Create index on tenant_id for multi-tenant queries
    op.create_index("ix_workflow_checkpoints_tenant_id", "workflow_checkpoints", ["tenant_id"])

    # Create index on status for list_running queries
    op.create_index("ix_workflow_checkpoints_status", "workflow_checkpoints", ["status"])

    # Create composite index for common query pattern
    op.create_index("ix_workflow_checkpoints_tenant_status", "workflow_checkpoints", ["tenant_id", "status"])

    # Add check constraint for step_outputs_json size (10MB max)
    op.execute(
        """
        ALTER TABLE workflow_checkpoints
        ADD CONSTRAINT ck_step_outputs_size
        CHECK (step_outputs_json IS NULL OR length(step_outputs_json) <= 10485760)
    """
    )

    # Add check constraint for valid status values
    op.execute(
        """
        ALTER TABLE workflow_checkpoints
        ADD CONSTRAINT ck_valid_status
        CHECK (status IN ('running', 'completed', 'failed', 'aborted', 'paused', 'timeout'))
    """
    )


def downgrade() -> None:
    # Drop constraints
    op.execute("ALTER TABLE workflow_checkpoints DROP CONSTRAINT IF EXISTS ck_step_outputs_size")
    op.execute("ALTER TABLE workflow_checkpoints DROP CONSTRAINT IF EXISTS ck_valid_status")

    # Drop indexes
    op.drop_index("ix_workflow_checkpoints_tenant_status", table_name="workflow_checkpoints")
    op.drop_index("ix_workflow_checkpoints_status", table_name="workflow_checkpoints")
    op.drop_index("ix_workflow_checkpoints_tenant_id", table_name="workflow_checkpoints")
    op.drop_index("ix_workflow_checkpoints_run_id", table_name="workflow_checkpoints")

    # Drop table
    op.drop_table("workflow_checkpoints")
