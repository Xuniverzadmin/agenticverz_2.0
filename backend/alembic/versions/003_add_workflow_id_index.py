"""Add index on workflow_id for performance

Revision ID: 003_add_workflow_id_index
Revises: 002_fix_status_enum
Create Date: 2025-12-02

This migration adds an index on workflow_id for efficient queries
by workflow type. Common patterns:
- List all runs for a specific workflow
- Aggregate metrics by workflow
- Debug workflow-specific issues
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003_add_workflow_id_index"
down_revision: Union[str, None] = "002_fix_status_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on workflow_id
    op.create_index(
        "ix_workflow_checkpoints_workflow_id",
        "workflow_checkpoints",
        ["workflow_id"]
    )

    # Add composite index for workflow + status queries
    op.create_index(
        "ix_workflow_checkpoints_workflow_status",
        "workflow_checkpoints",
        ["workflow_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_checkpoints_workflow_status", table_name="workflow_checkpoints")
    op.drop_index("ix_workflow_checkpoints_workflow_id", table_name="workflow_checkpoints")
