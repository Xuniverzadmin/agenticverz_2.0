"""Merge migration heads: decision_records + pb_s1_retry

This migration merges the two independent branches:
- 050_dr_causal_binding (decision records feature)
- 053_pb_s1_retry (truth guarantee enforcement)

Both branches are independent features that can coexist.

Revision ID: 054_merge_heads
Revises: 050_dr_causal_binding, 053_pb_s1_retry
Create Date: 2025-12-27

LESSON: Migration 051 skipped 049/050 creating a fork.
        This merge repairs the lineage.
        Future migrations MUST verify single head before creation.
"""

# revision identifiers
revision = "054_merge_heads"
down_revision = ("050_dr_causal_binding", "053_pb_s1_retry")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Merge migration - no schema changes needed.

    Both branches are independent:
    - 050: Decision records tables
    - 053: worker_runs immutability columns + trigger

    This merge simply unifies the revision history.
    """
    pass


def downgrade() -> None:
    """
    Downgrade not supported for merge migrations.

    To undo, downgrade each branch separately:
    - alembic downgrade 050_dr_causal_binding
    - alembic downgrade 053_pb_s1_retry
    """
    pass
