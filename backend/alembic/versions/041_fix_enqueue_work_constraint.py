"""041 Fix enqueue_work constraint reference

Revision ID: 041_fix_enqueue_work_constraint
Revises: 040_m24_onboarding
Create Date: 2025-12-22

Fixes: psycopg2.errors.UndefinedObject: constraint "uq_work_queue_candidate_pending" does not exist

Root cause: Migration 021 creates a partial UNIQUE INDEX (not a CONSTRAINT),
but enqueue_work function uses ON CONFLICT ON CONSTRAINT which requires
an actual named constraint.

Fix: Replace the function to use proper partial unique index conflict syntax.

See also: PIN-120 (RC-11: Migration Index vs Constraint Mismatch)
"""
from alembic import op
from sqlalchemy import text

revision = '041_fix_enqueue_work_constraint'
down_revision = '040_m24_onboarding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Drop and recreate the function with correct ON CONFLICT syntax
    # For partial unique indexes, specify the conflict target with WHERE clause
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION m10_recovery.enqueue_work(
            p_candidate_id INTEGER,
            p_idempotency_key UUID DEFAULT NULL,
            p_priority INTEGER DEFAULT 0,
            p_method TEXT DEFAULT 'db_fallback'
        )
        RETURNS INTEGER AS $$
        DECLARE
            v_id INTEGER;
        BEGIN
            -- Use ON CONFLICT with column list + WHERE for partial unique index
            -- (matches CREATE UNIQUE INDEX uq_work_queue_candidate_pending
            --  ON m10_recovery.work_queue(candidate_id) WHERE processed_at IS NULL)
            INSERT INTO m10_recovery.work_queue (
                candidate_id, idempotency_key, priority, method
            ) VALUES (
                p_candidate_id, p_idempotency_key, p_priority, p_method
            )
            ON CONFLICT (candidate_id) WHERE processed_at IS NULL
            DO UPDATE SET
                priority = GREATEST(m10_recovery.work_queue.priority, EXCLUDED.priority),
                retry_count = m10_recovery.work_queue.retry_count + 1
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.enqueue_work IS
            'Enqueue work item with upsert semantics for Redis fallback (fixed for partial unique index)';
    """))

    # Ensure the partial unique index exists (idempotent check)
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'm10_recovery'
                AND tablename = 'work_queue'
                AND indexname = 'uq_work_queue_candidate_pending'
            ) THEN
                CREATE UNIQUE INDEX uq_work_queue_candidate_pending
                    ON m10_recovery.work_queue(candidate_id)
                    WHERE processed_at IS NULL;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    conn = op.get_bind()

    # Restore original function with ON CONFLICT ON CONSTRAINT (will break)
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION m10_recovery.enqueue_work(
            p_candidate_id INTEGER,
            p_idempotency_key UUID DEFAULT NULL,
            p_priority INTEGER DEFAULT 0,
            p_method TEXT DEFAULT 'db_fallback'
        )
        RETURNS INTEGER AS $$
        DECLARE
            v_id INTEGER;
        BEGIN
            INSERT INTO m10_recovery.work_queue (
                candidate_id, idempotency_key, priority, method
            ) VALUES (
                p_candidate_id, p_idempotency_key, p_priority, p_method
            )
            ON CONFLICT ON CONSTRAINT uq_work_queue_candidate_pending
            DO UPDATE SET
                priority = GREATEST(m10_recovery.work_queue.priority, EXCLUDED.priority),
                retry_count = m10_recovery.work_queue.retry_count + 1
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
    """))
