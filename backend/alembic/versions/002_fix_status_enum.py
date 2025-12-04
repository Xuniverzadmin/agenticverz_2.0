"""Fix status enum to include all workflow engine statuses

Revision ID: 002_fix_status_enum
Revises: 001_workflow_checkpoints
Create Date: 2025-12-02

This migration fixes the status constraint to include all statuses
used by the workflow engine:
- running: Workflow is currently executing
- completed: Workflow finished successfully
- failed: Workflow failed due to step failure
- aborted: Workflow was manually aborted
- paused: Workflow is paused (for future use)
- timeout: Workflow exceeded timeout limit
- budget_exceeded: Workflow stopped due to budget limits
- emergency_stopped: Workflow stopped via emergency stop
- policy_violation: Workflow stopped due to policy violation
- sandbox_rejected: Workflow rejected by planner sandbox
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_fix_status_enum"
down_revision: Union[str, None] = "001_workflow_checkpoints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old constraint
    op.execute("ALTER TABLE workflow_checkpoints DROP CONSTRAINT IF EXISTS ck_valid_status")

    # Add new constraint with all valid statuses
    op.execute("""
        ALTER TABLE workflow_checkpoints
        ADD CONSTRAINT ck_valid_status
        CHECK (status IN (
            'running',
            'completed',
            'failed',
            'aborted',
            'paused',
            'timeout',
            'budget_exceeded',
            'emergency_stopped',
            'policy_violation',
            'sandbox_rejected'
        ))
    """)


def downgrade() -> None:
    # Drop new constraint
    op.execute("ALTER TABLE workflow_checkpoints DROP CONSTRAINT IF EXISTS ck_valid_status")

    # Restore old constraint
    op.execute("""
        ALTER TABLE workflow_checkpoints
        ADD CONSTRAINT ck_valid_status
        CHECK (status IN ('running', 'completed', 'failed', 'aborted', 'paused', 'timeout'))
    """)
