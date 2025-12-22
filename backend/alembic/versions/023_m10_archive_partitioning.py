"""M10 Dead-Letter Archive Partitioning

Revision ID: 023_m10_archive_partitioning
Revises: 022_m10_production_hardening
Create Date: 2025-12-09

**STATUS: DEFERRED (PIN-058)**

This migration is DEFERRED until tables exceed 100K rows.
Current tables have <1K rows - partitioning is premature optimization.

DO NOT apply to production until:
1. dead_letter_archive table exceeds 100K rows
2. replay_log table exceeds 50K rows
3. Query performance degrades measurably

When ready to apply:
    alembic upgrade 023_m10_archive_partitioning

See PIN-058 for rationale on deferring this migration.

---

Original Description:
This migration converts dead_letter_archive to a partitioned table (by month)
for better retention management and query performance.

Features:
- Monthly partitions for dead_letter_archive
- Auto-creation of future partitions (3 months ahead)
- Retention function to drop old partitions
- Maintains all existing data
"""

from datetime import datetime, timedelta

from alembic import op

# revision identifiers
revision = "023_m10_archive_partitioning"
down_revision = "022_m10_production_hardening"
branch_labels = None
depends_on = None


def upgrade():
    # Create partitioned version of dead_letter_archive
    op.execute(
        """
    -- Step 1: Rename existing table
    ALTER TABLE IF EXISTS m10_recovery.dead_letter_archive
    RENAME TO dead_letter_archive_old;

    -- Step 2: Create new partitioned table
    CREATE TABLE m10_recovery.dead_letter_archive (
        id BIGSERIAL,
        original_msg_id TEXT NOT NULL,
        dl_msg_id TEXT NOT NULL,
        stream_key TEXT NOT NULL,
        payload JSONB NOT NULL,
        failure_reason TEXT,
        retry_count INT DEFAULT 0,
        archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        archived_by TEXT,
        PRIMARY KEY (id, archived_at)
    ) PARTITION BY RANGE (archived_at);

    -- Step 3: Create index on partitioned table
    CREATE INDEX idx_dla_original_msg_id ON m10_recovery.dead_letter_archive (original_msg_id);
    CREATE INDEX idx_dla_archived_at ON m10_recovery.dead_letter_archive (archived_at);
    CREATE INDEX idx_dla_stream_key ON m10_recovery.dead_letter_archive (stream_key);
    """
    )

    # Create partitions for current month and 3 months ahead
    now = datetime.utcnow()
    for i in range(-1, 4):  # Previous month, current, and 3 future months
        month_start = datetime(now.year, now.month, 1) + timedelta(days=32 * i)
        month_start = datetime(month_start.year, month_start.month, 1)
        month_end = datetime(month_start.year, month_start.month, 1) + timedelta(days=32)
        month_end = datetime(month_end.year, month_end.month, 1)

        partition_name = f"dead_letter_archive_{month_start.strftime('%Y_%m')}"

        op.execute(
            f"""
        CREATE TABLE IF NOT EXISTS m10_recovery.{partition_name}
        PARTITION OF m10_recovery.dead_letter_archive
        FOR VALUES FROM ('{month_start.strftime('%Y-%m-%d')}')
        TO ('{month_end.strftime('%Y-%m-%d')}');
        """
        )

    # Migrate existing data
    op.execute(
        """
    -- Step 4: Migrate existing data to partitioned table
    INSERT INTO m10_recovery.dead_letter_archive
        (id, original_msg_id, dl_msg_id, stream_key, payload, failure_reason,
         retry_count, archived_at, archived_by)
    SELECT
        id, original_msg_id, dl_msg_id, stream_key, payload, failure_reason,
        retry_count, archived_at, archived_by
    FROM m10_recovery.dead_letter_archive_old;

    -- Step 5: Drop old table
    DROP TABLE IF EXISTS m10_recovery.dead_letter_archive_old;

    -- Step 6: Reset sequence to max id
    SELECT setval(
        pg_get_serial_sequence('m10_recovery.dead_letter_archive', 'id'),
        COALESCE((SELECT MAX(id) FROM m10_recovery.dead_letter_archive), 1)
    );
    """
    )

    # Create partition management functions
    op.execute(
        """
    -- Function to create future partitions (run monthly via cron)
    CREATE OR REPLACE FUNCTION m10_recovery.create_archive_partition(
        p_month DATE DEFAULT date_trunc('month', now() + interval '1 month')
    )
    RETURNS TEXT
    LANGUAGE plpgsql
    AS $$
    DECLARE
        partition_name TEXT;
        start_date DATE;
        end_date DATE;
    BEGIN
        start_date := date_trunc('month', p_month);
        end_date := start_date + interval '1 month';
        partition_name := 'dead_letter_archive_' || to_char(start_date, 'YYYY_MM');

        -- Check if partition already exists
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'm10_recovery'
            AND c.relname = partition_name
        ) THEN
            RETURN 'Partition ' || partition_name || ' already exists';
        END IF;

        -- Create partition
        EXECUTE format(
            'CREATE TABLE m10_recovery.%I PARTITION OF m10_recovery.dead_letter_archive
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        RETURN 'Created partition ' || partition_name;
    END;
    $$;

    -- Function to drop old partitions (retention)
    CREATE OR REPLACE FUNCTION m10_recovery.drop_archive_partition(
        p_retention_months INT DEFAULT 6
    )
    RETURNS TABLE(partition_name TEXT, rows_deleted BIGINT, status TEXT)
    LANGUAGE plpgsql
    AS $$
    DECLARE
        cutoff_date DATE;
        part_name TEXT;
        part_count BIGINT;
    BEGIN
        cutoff_date := date_trunc('month', now() - (p_retention_months || ' months')::interval);

        FOR part_name IN
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_inherits i ON i.inhrelid = c.oid
            JOIN pg_class parent ON parent.oid = i.inhparent
            WHERE n.nspname = 'm10_recovery'
            AND parent.relname = 'dead_letter_archive'
            AND c.relname ~ '^dead_letter_archive_[0-9]{4}_[0-9]{2}$'
            AND to_date(substring(c.relname from '[0-9]{4}_[0-9]{2}$'), 'YYYY_MM') < cutoff_date
        LOOP
            -- Get row count before dropping
            EXECUTE format('SELECT COUNT(*) FROM m10_recovery.%I', part_name) INTO part_count;

            -- Drop the partition
            EXECUTE format('DROP TABLE m10_recovery.%I', part_name);

            partition_name := part_name;
            rows_deleted := part_count;
            status := 'dropped';
            RETURN NEXT;
        END LOOP;
    END;
    $$;

    -- Function to list partitions with stats
    CREATE OR REPLACE FUNCTION m10_recovery.list_archive_partitions()
    RETURNS TABLE(
        partition_name TEXT,
        row_count BIGINT,
        size_bytes BIGINT,
        min_archived_at TIMESTAMPTZ,
        max_archived_at TIMESTAMPTZ
    )
    LANGUAGE plpgsql
    AS $$
    DECLARE
        part_name TEXT;
    BEGIN
        FOR part_name IN
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_inherits i ON i.inhrelid = c.oid
            JOIN pg_class parent ON parent.oid = i.inhparent
            WHERE n.nspname = 'm10_recovery'
            AND parent.relname = 'dead_letter_archive'
            ORDER BY c.relname
        LOOP
            partition_name := part_name;

            EXECUTE format('SELECT COUNT(*) FROM m10_recovery.%I', part_name) INTO row_count;
            EXECUTE format('SELECT pg_relation_size(''m10_recovery.%I'')', part_name) INTO size_bytes;
            EXECUTE format('SELECT MIN(archived_at), MAX(archived_at) FROM m10_recovery.%I', part_name)
                INTO min_archived_at, max_archived_at;

            RETURN NEXT;
        END LOOP;
    END;
    $$;

    -- Create partitions for next 3 months automatically
    SELECT m10_recovery.create_archive_partition(date_trunc('month', now() + interval '1 month'));
    SELECT m10_recovery.create_archive_partition(date_trunc('month', now() + interval '2 months'));
    SELECT m10_recovery.create_archive_partition(date_trunc('month', now() + interval '3 months'));
    """
    )

    # Also partition replay_log for consistency
    op.execute(
        """
    -- Rename existing replay_log
    ALTER TABLE IF EXISTS m10_recovery.replay_log
    RENAME TO replay_log_old;

    -- Create partitioned replay_log
    CREATE TABLE m10_recovery.replay_log (
        id BIGSERIAL,
        original_msg_id TEXT NOT NULL,
        dl_msg_id TEXT,
        candidate_id UUID,
        recovery_id UUID,
        new_msg_id TEXT,
        replayed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        replayed_by TEXT,
        PRIMARY KEY (id, replayed_at),
        CONSTRAINT uq_replay_original_msg UNIQUE (original_msg_id, replayed_at)
    ) PARTITION BY RANGE (replayed_at);

    CREATE INDEX idx_replay_log_original ON m10_recovery.replay_log (original_msg_id);
    CREATE INDEX idx_replay_log_replayed_at ON m10_recovery.replay_log (replayed_at);
    """
    )

    # Create replay_log partitions
    now = datetime.utcnow()
    for i in range(-1, 4):
        month_start = datetime(now.year, now.month, 1) + timedelta(days=32 * i)
        month_start = datetime(month_start.year, month_start.month, 1)
        month_end = datetime(month_start.year, month_start.month, 1) + timedelta(days=32)
        month_end = datetime(month_end.year, month_end.month, 1)

        partition_name = f"replay_log_{month_start.strftime('%Y_%m')}"

        op.execute(
            f"""
        CREATE TABLE IF NOT EXISTS m10_recovery.{partition_name}
        PARTITION OF m10_recovery.replay_log
        FOR VALUES FROM ('{month_start.strftime('%Y-%m-%d')}')
        TO ('{month_end.strftime('%Y-%m-%d')}');
        """
        )

    # Migrate replay_log data
    op.execute(
        """
    INSERT INTO m10_recovery.replay_log
        (id, original_msg_id, dl_msg_id, candidate_id, recovery_id,
         new_msg_id, replayed_at, replayed_by)
    SELECT
        id, original_msg_id, dl_msg_id, candidate_id, recovery_id,
        new_msg_id, replayed_at, replayed_by
    FROM m10_recovery.replay_log_old;

    DROP TABLE IF EXISTS m10_recovery.replay_log_old;

    SELECT setval(
        pg_get_serial_sequence('m10_recovery.replay_log', 'id'),
        COALESCE((SELECT MAX(id) FROM m10_recovery.replay_log), 1)
    );
    """
    )

    # Update record_replay function for partitioned table
    op.execute(
        """
    -- Updated record_replay for partitioned table
    CREATE OR REPLACE FUNCTION m10_recovery.record_replay(
        p_original_msg_id TEXT,
        p_dl_msg_id TEXT DEFAULT NULL,
        p_candidate_id UUID DEFAULT NULL,
        p_recovery_id UUID DEFAULT NULL,
        p_new_msg_id TEXT DEFAULT NULL,
        p_replayed_by TEXT DEFAULT NULL
    )
    RETURNS TABLE(was_duplicate BOOLEAN, replay_id BIGINT)
    LANGUAGE plpgsql
    AS $$
    DECLARE
        existing_id BIGINT;
        new_id BIGINT;
    BEGIN
        -- Check for existing replay (idempotency)
        SELECT id INTO existing_id
        FROM m10_recovery.replay_log
        WHERE original_msg_id = p_original_msg_id
        LIMIT 1;

        IF existing_id IS NOT NULL THEN
            was_duplicate := TRUE;
            replay_id := existing_id;
            RETURN NEXT;
            RETURN;
        END IF;

        -- Insert new replay record
        INSERT INTO m10_recovery.replay_log (
            original_msg_id, dl_msg_id, candidate_id, recovery_id,
            new_msg_id, replayed_by
        ) VALUES (
            p_original_msg_id, p_dl_msg_id, p_candidate_id, p_recovery_id,
            p_new_msg_id, p_replayed_by
        )
        RETURNING id INTO new_id;

        was_duplicate := FALSE;
        replay_id := new_id;
        RETURN NEXT;
    END;
    $$;

    -- Function to create replay_log partitions
    CREATE OR REPLACE FUNCTION m10_recovery.create_replay_partition(
        p_month DATE DEFAULT date_trunc('month', now() + interval '1 month')
    )
    RETURNS TEXT
    LANGUAGE plpgsql
    AS $$
    DECLARE
        partition_name TEXT;
        start_date DATE;
        end_date DATE;
    BEGIN
        start_date := date_trunc('month', p_month);
        end_date := start_date + interval '1 month';
        partition_name := 'replay_log_' || to_char(start_date, 'YYYY_MM');

        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'm10_recovery'
            AND c.relname = partition_name
        ) THEN
            RETURN 'Partition ' || partition_name || ' already exists';
        END IF;

        EXECUTE format(
            'CREATE TABLE m10_recovery.%I PARTITION OF m10_recovery.replay_log
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );

        RETURN 'Created partition ' || partition_name;
    END;
    $$;

    -- Function to drop old replay_log partitions
    CREATE OR REPLACE FUNCTION m10_recovery.drop_replay_partition(
        p_retention_months INT DEFAULT 3
    )
    RETURNS TABLE(partition_name TEXT, rows_deleted BIGINT, status TEXT)
    LANGUAGE plpgsql
    AS $$
    DECLARE
        cutoff_date DATE;
        part_name TEXT;
        part_count BIGINT;
    BEGIN
        cutoff_date := date_trunc('month', now() - (p_retention_months || ' months')::interval);

        FOR part_name IN
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_inherits i ON i.inhrelid = c.oid
            JOIN pg_class parent ON parent.oid = i.inhparent
            WHERE n.nspname = 'm10_recovery'
            AND parent.relname = 'replay_log'
            AND c.relname ~ '^replay_log_[0-9]{4}_[0-9]{2}$'
            AND to_date(substring(c.relname from '[0-9]{4}_[0-9]{2}$'), 'YYYY_MM') < cutoff_date
        LOOP
            EXECUTE format('SELECT COUNT(*) FROM m10_recovery.%I', part_name) INTO part_count;
            EXECUTE format('DROP TABLE m10_recovery.%I', part_name);

            partition_name := part_name;
            rows_deleted := part_count;
            status := 'dropped';
            RETURN NEXT;
        END LOOP;
    END;
    $$;
    """
    )


def downgrade():
    # Convert back to non-partitioned tables
    op.execute(
        """
    -- Backup partitioned data
    CREATE TABLE m10_recovery.dead_letter_archive_backup AS
    SELECT * FROM m10_recovery.dead_letter_archive;

    CREATE TABLE m10_recovery.replay_log_backup AS
    SELECT * FROM m10_recovery.replay_log;

    -- Drop partitioned tables (cascades to partitions)
    DROP TABLE IF EXISTS m10_recovery.dead_letter_archive CASCADE;
    DROP TABLE IF EXISTS m10_recovery.replay_log CASCADE;

    -- Recreate non-partitioned dead_letter_archive
    CREATE TABLE m10_recovery.dead_letter_archive (
        id BIGSERIAL PRIMARY KEY,
        original_msg_id TEXT NOT NULL,
        dl_msg_id TEXT NOT NULL,
        stream_key TEXT NOT NULL,
        payload JSONB NOT NULL,
        failure_reason TEXT,
        retry_count INT DEFAULT 0,
        archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        archived_by TEXT
    );

    CREATE INDEX idx_dla_original_msg_id ON m10_recovery.dead_letter_archive (original_msg_id);
    CREATE INDEX idx_dla_archived_at ON m10_recovery.dead_letter_archive (archived_at);

    -- Restore data
    INSERT INTO m10_recovery.dead_letter_archive SELECT * FROM m10_recovery.dead_letter_archive_backup;
    DROP TABLE m10_recovery.dead_letter_archive_backup;

    -- Recreate non-partitioned replay_log
    CREATE TABLE m10_recovery.replay_log (
        id BIGSERIAL PRIMARY KEY,
        original_msg_id TEXT NOT NULL UNIQUE,
        dl_msg_id TEXT,
        candidate_id UUID,
        recovery_id UUID,
        new_msg_id TEXT,
        replayed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        replayed_by TEXT
    );

    CREATE INDEX idx_replay_log_original ON m10_recovery.replay_log (original_msg_id);

    INSERT INTO m10_recovery.replay_log SELECT * FROM m10_recovery.replay_log_backup;
    DROP TABLE m10_recovery.replay_log_backup;

    -- Restore original record_replay function
    CREATE OR REPLACE FUNCTION m10_recovery.record_replay(
        p_original_msg_id TEXT,
        p_dl_msg_id TEXT DEFAULT NULL,
        p_candidate_id UUID DEFAULT NULL,
        p_recovery_id UUID DEFAULT NULL,
        p_new_msg_id TEXT DEFAULT NULL,
        p_replayed_by TEXT DEFAULT NULL
    )
    RETURNS TABLE(was_duplicate BOOLEAN, replay_id BIGINT)
    LANGUAGE plpgsql
    AS $$
    DECLARE
        existing_id BIGINT;
        new_id BIGINT;
    BEGIN
        SELECT id INTO existing_id
        FROM m10_recovery.replay_log
        WHERE original_msg_id = p_original_msg_id;

        IF existing_id IS NOT NULL THEN
            was_duplicate := TRUE;
            replay_id := existing_id;
            RETURN NEXT;
            RETURN;
        END IF;

        INSERT INTO m10_recovery.replay_log (
            original_msg_id, dl_msg_id, candidate_id, recovery_id,
            new_msg_id, replayed_by
        ) VALUES (
            p_original_msg_id, p_dl_msg_id, p_candidate_id, p_recovery_id,
            p_new_msg_id, p_replayed_by
        )
        RETURNING id INTO new_id;

        was_duplicate := FALSE;
        replay_id := new_id;
        RETURN NEXT;
    END;
    $$;

    -- Drop partition management functions
    DROP FUNCTION IF EXISTS m10_recovery.create_archive_partition(DATE);
    DROP FUNCTION IF EXISTS m10_recovery.drop_archive_partition(INT);
    DROP FUNCTION IF EXISTS m10_recovery.list_archive_partitions();
    DROP FUNCTION IF EXISTS m10_recovery.create_replay_partition(DATE);
    DROP FUNCTION IF EXISTS m10_recovery.drop_replay_partition(INT);
    """
    )
