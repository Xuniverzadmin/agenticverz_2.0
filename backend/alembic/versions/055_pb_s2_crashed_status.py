"""PB-S2: Add 'crashed' status to immutability protection

This migration:
1. Updates the immutability trigger to protect 'crashed' runs
2. Documents 'crashed' as a valid terminal status

PB-S2 Guarantee: Orphaned runs are never silently lost.
- On startup, detect runs stuck in "queued" or "running"
- Mark them as "crashed" (factual status, not mutation)
- Once crashed, the run becomes immutable

Revision ID: 055_pb_s2_crashed_status
Revises: 054_merge_heads
Create Date: 2025-12-27

FROZEN: This migration extends PB-S1 truth guarantees to include PB-S2 crash recovery.
"""

from alembic import op

# revision identifiers
revision = "055_pb_s2_crashed_status"
down_revision = "054_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update trigger to also protect 'crashed' runs."""

    # ============================================================
    # STEP 1: Update immutability trigger to include 'crashed'
    # ============================================================
    # Replace the function to now protect completed, failed, AND crashed
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_worker_run_mutation()
        RETURNS trigger AS $$
        BEGIN
            -- PB-S1 + PB-S2: Protect completed, failed, AND crashed runs
            -- "crashed" is a terminal status for orphaned runs (PB-S2)
            IF OLD.status IN ('completed', 'failed', 'crashed') THEN
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
                    RAISE EXCEPTION 'TRUTH_VIOLATION: Cannot mutate completed/failed/crashed worker_run (id=%, status=%)', OLD.id, OLD.status
                        USING ERRCODE = 'restrict_violation';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # ============================================================
    # STEP 2: Update table comment to document crashed status
    # ============================================================
    op.execute(
        """
        COMMENT ON TABLE worker_runs IS
        'Worker execution runs. IMMUTABLE after status becomes completed/failed/crashed. '
        'Retries create NEW rows with parent_run_id linking to original. '
        'Crashed status indicates orphaned runs detected at startup (PB-S2). '
        'Truth guarantees enforced by trigger (PB-S1 + PB-S2).';
    """
    )


def downgrade() -> None:
    """Restore original trigger that only protects completed/failed."""

    # Restore original function without 'crashed' protection
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_worker_run_mutation()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.status IN ('completed', 'failed') THEN
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

    # Restore original table comment
    op.execute(
        """
        COMMENT ON TABLE worker_runs IS
        'Worker execution runs. IMMUTABLE after status becomes completed/failed. '
        'Retries create NEW rows with parent_run_id linking to original. '
        'PB-S1 truth guarantee enforced by trigger.';
    """
    )
