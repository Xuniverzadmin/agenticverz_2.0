"""034 Fix outbox constraint reference

Revision ID: 034_fix_outbox_constraint
Revises: 033_m19_1_policy_gaps
Create Date: 2025-12-15

Fixes: psycopg2.errors.UndefinedObject: constraint "uq_outbox_pending" does not exist

Root cause: Migration 022 creates a partial UNIQUE INDEX (not a CONSTRAINT),
but publish_outbox function uses ON CONFLICT ON CONSTRAINT which requires
an actual named constraint.

Fix: Replace the function to use proper partial unique index conflict syntax.
"""

from sqlalchemy import text

from alembic import op

revision = "034_fix_outbox_constraint"
down_revision = "033_m19_1_gaps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Drop and recreate the function with correct ON CONFLICT syntax
    # For partial unique indexes, specify the conflict target with WHERE clause
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.publish_outbox(
            p_aggregate_type TEXT,
            p_aggregate_id TEXT,
            p_event_type TEXT,
            p_payload JSONB
        )
        RETURNS BIGINT AS $$
        DECLARE
            v_id BIGINT;
        BEGIN
            -- Use ON CONFLICT with column list + WHERE for partial unique index
            INSERT INTO m10_recovery.outbox (
                aggregate_type, aggregate_id, event_type, payload
            ) VALUES (
                p_aggregate_type, p_aggregate_id, p_event_type, p_payload
            )
            ON CONFLICT (aggregate_type, aggregate_id, event_type)
                WHERE processed_at IS NULL
            DO UPDATE
            SET payload = EXCLUDED.payload,
                retry_count = m10_recovery.outbox.retry_count + 1
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.publish_outbox IS
            'Publish event to outbox for external delivery (fixed for partial unique index)';
    """
        )
    )

    # Also ensure the partial unique index exists (idempotent)
    conn.execute(
        text(
            """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'm10_recovery'
                AND tablename = 'outbox'
                AND indexname = 'uq_outbox_pending'
            ) THEN
                CREATE UNIQUE INDEX uq_outbox_pending
                    ON m10_recovery.outbox(aggregate_type, aggregate_id, event_type)
                    WHERE processed_at IS NULL;
            END IF;
        END $$;
    """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Restore original function with ON CONFLICT ON CONSTRAINT
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.publish_outbox(
            p_aggregate_type TEXT,
            p_aggregate_id TEXT,
            p_event_type TEXT,
            p_payload JSONB
        )
        RETURNS BIGINT AS $$
        DECLARE
            v_id BIGINT;
        BEGIN
            INSERT INTO m10_recovery.outbox (
                aggregate_type, aggregate_id, event_type, payload
            ) VALUES (
                p_aggregate_type, p_aggregate_id, p_event_type, p_payload
            )
            ON CONFLICT ON CONSTRAINT uq_outbox_pending DO UPDATE
            SET payload = EXCLUDED.payload,
                retry_count = m10_recovery.outbox.retry_count + 1
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
    """
        )
    )
