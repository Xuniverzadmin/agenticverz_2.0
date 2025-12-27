"""PB-S1: Proper Retry Mechanism with Run Immutability

This migration implements the correct retry model:
- Retry creates NEW execution (not mutation)
- Original runs are immutable after completion
- Parent linkage for audit trail

Revision ID: 053_pb_s1_retry
Revises: 052_s6_trace_immutability
Create Date: 2025-12-27

FROZEN: This migration enforces PB-S1 truth guarantees.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "053_pb_s1_retry"
down_revision = "052_s6_trace_immutability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add retry linkage columns and immutability triggers."""

    # ============================================================
    # STEP 1: Add parent_run_id to worker_runs for retry linkage
    # ============================================================
    op.add_column(
        "worker_runs",
        sa.Column(
            "parent_run_id",
            sa.String(36),
            sa.ForeignKey("worker_runs.id", ondelete="SET NULL"),
            nullable=True,
            comment="Original run ID if this is a retry",
        ),
    )

    # ============================================================
    # STEP 2: Add attempt counter to worker_runs
    # ============================================================
    op.add_column(
        "worker_runs",
        sa.Column(
            "attempt",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Attempt number (1 = original, 2+ = retry)",
        ),
    )

    # ============================================================
    # STEP 3: Add is_retry flag for fast filtering
    # ============================================================
    op.add_column(
        "worker_runs",
        sa.Column(
            "is_retry",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="True if this run is a retry of a failed run",
        ),
    )

    # ============================================================
    # STEP 4: Add index for parent_run_id lookups
    # ============================================================
    op.create_index("ix_worker_runs_parent_run_id", "worker_runs", ["parent_run_id"], unique=False)

    # ============================================================
    # STEP 5: Add index for retry chain lookups
    # ============================================================
    op.create_index("ix_worker_runs_is_retry", "worker_runs", ["is_retry"], unique=False)

    # ============================================================
    # STEP 6: Create immutability trigger (CRITICAL for PB-S1)
    # ============================================================
    # This trigger PREVENTS mutation of completed/failed runs
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_worker_run_mutation()
        RETURNS trigger AS $$
        BEGIN
            -- Only trigger on actual data changes (not just SELECT FOR UPDATE)
            IF OLD.status IN ('completed', 'failed') THEN
                -- Allow adding parent_run_id to existing runs (for backfill)
                -- But prevent any other changes
                IF (
                    NEW.status != OLD.status OR
                    NEW.success IS DISTINCT FROM OLD.success OR
                    NEW.error IS DISTINCT FROM OLD.error OR
                    NEW.output_json IS DISTINCT FROM OLD.output_json OR
                    NEW.total_tokens IS DISTINCT FROM OLD.total_tokens OR
                    NEW.cost_cents IS DISTINCT FROM OLD.cost_cents OR
                    NEW.started_at IS DISTINCT FROM OLD.started_at OR
                    NEW.completed_at IS DISTINCT FROM OLD.completed_at
                ) THEN
                    RAISE EXCEPTION 'PB-S1 VIOLATION: Cannot mutate completed/failed worker_run (id=%)', OLD.id
                        USING ERRCODE = 'restrict_violation';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS worker_runs_immutable_guard ON worker_runs;
        CREATE TRIGGER worker_runs_immutable_guard
        BEFORE UPDATE ON worker_runs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_worker_run_mutation();
    """
    )

    # ============================================================
    # STEP 7: Create retry_history view for audit queries
    # ============================================================
    op.execute(
        """
        CREATE OR REPLACE VIEW retry_history AS
        SELECT
            r.id as run_id,
            r.tenant_id,
            r.worker_id,
            r.status,
            r.success,
            r.attempt,
            r.is_retry,
            r.parent_run_id,
            r.created_at,
            r.completed_at,
            r.cost_cents,
            p.id as original_run_id,
            p.status as original_status,
            p.error as original_error,
            p.created_at as original_created_at
        FROM worker_runs r
        LEFT JOIN worker_runs p ON r.parent_run_id = p.id
        WHERE r.is_retry = true
        ORDER BY r.created_at DESC;
    """
    )

    # ============================================================
    # STEP 8: Add comment for documentation
    # ============================================================
    op.execute(
        """
        COMMENT ON TABLE worker_runs IS
        'Worker execution runs. IMMUTABLE after status becomes completed/failed. '
        'Retries create NEW rows with parent_run_id linking to original. '
        'PB-S1 truth guarantee enforced by trigger.';
    """
    )


def downgrade() -> None:
    """Remove retry linkage and immutability enforcement."""

    # Drop view first
    op.execute("DROP VIEW IF EXISTS retry_history;")

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS worker_runs_immutable_guard ON worker_runs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_worker_run_mutation();")

    # Drop indexes
    op.drop_index("ix_worker_runs_is_retry", table_name="worker_runs")
    op.drop_index("ix_worker_runs_parent_run_id", table_name="worker_runs")

    # Drop columns
    op.drop_column("worker_runs", "is_retry")
    op.drop_column("worker_runs", "attempt")
    op.drop_column("worker_runs", "parent_run_id")
