"""Add trace retention lifecycle stored procedure

Revision ID: 013_add_trace_retention
Revises: 012_add_aos_traces
Create Date: 2025-12-06

M8 Deliverable: Trace retention policy with automatic archival and deletion
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '013_add_trace_retention'
down_revision = '012_add_aos_traces'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create retention lifecycle stored procedure
    op.execute("""
        CREATE OR REPLACE FUNCTION aos_traces_retention(
            archive_days INTEGER DEFAULT 90,
            delete_days INTEGER DEFAULT 365
        )
        RETURNS TABLE(archived_count INTEGER, deleted_count INTEGER) AS $$
        DECLARE
            _archived INTEGER := 0;
            _deleted INTEGER := 0;
        BEGIN
            -- Archive traces older than archive_days to aos_traces_archive
            WITH archived AS (
                INSERT INTO aos_traces_archive
                SELECT * FROM aos_traces
                WHERE created_at < now() - (archive_days || ' days')::INTERVAL
                ON CONFLICT (trace_id) DO NOTHING
                RETURNING 1
            )
            SELECT COUNT(*) INTO _archived FROM archived;

            -- Delete archived traces from main table
            DELETE FROM aos_traces
            WHERE created_at < now() - (archive_days || ' days')::INTERVAL;

            -- Hard delete from archive older than delete_days
            WITH deleted AS (
                DELETE FROM aos_traces_archive
                WHERE created_at < now() - (delete_days || ' days')::INTERVAL
                RETURNING 1
            )
            SELECT COUNT(*) INTO _deleted FROM deleted;

            archived_count := _archived;
            deleted_count := _deleted;

            RETURN NEXT;
        END;
        $$ LANGUAGE plpgsql;

        -- Create a simple wrapper for cron job
        CREATE OR REPLACE FUNCTION aos_run_trace_retention()
        RETURNS void AS $$
        BEGIN
            PERFORM * FROM aos_traces_retention(90, 365);
        END;
        $$ LANGUAGE plpgsql;

        -- Add comment for documentation
        COMMENT ON FUNCTION aos_traces_retention IS
            'Archive traces older than archive_days, delete from archive older than delete_days.
             Default: archive after 90 days, delete after 365 days.
             Schedule with pg_cron: SELECT cron.schedule(''0 4 * * *'', ''SELECT aos_run_trace_retention()'');';
    """)

    # Create retention audit log table
    op.create_table(
        'aos_traces_retention_log',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('run_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('archived_count', sa.Integer(), nullable=False, default=0),
        sa.Column('deleted_count', sa.Integer(), nullable=False, default=0),
        sa.Column('archive_days', sa.Integer(), nullable=False, default=90),
        sa.Column('delete_days', sa.Integer(), nullable=False, default=365),
        sa.Column('duration_ms', sa.Float(), nullable=True),
    )

    # Create a logging version of the retention function
    op.execute("""
        CREATE OR REPLACE FUNCTION aos_run_trace_retention_with_log()
        RETURNS void AS $$
        DECLARE
            _start TIMESTAMP := clock_timestamp();
            _result RECORD;
        BEGIN
            SELECT * INTO _result FROM aos_traces_retention(90, 365);

            INSERT INTO aos_traces_retention_log (archived_count, deleted_count, duration_ms)
            VALUES (
                _result.archived_count,
                _result.deleted_count,
                EXTRACT(MILLISECONDS FROM clock_timestamp() - _start)
            );
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS aos_run_trace_retention_with_log();")
    op.execute("DROP FUNCTION IF EXISTS aos_run_trace_retention();")
    op.execute("DROP FUNCTION IF EXISTS aos_traces_retention(INTEGER, INTEGER);")
    op.drop_table('aos_traces_retention_log')
