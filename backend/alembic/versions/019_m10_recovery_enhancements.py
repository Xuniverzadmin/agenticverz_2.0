"""019_m10_recovery_enhancements - pgcrypto, idempotency_key, materialized view, indexes

Revision ID: 019_m10_recovery_enhancements
Revises: 018_add_m10_recovery_enhancements
Create Date: 2025-12-09

M10 Recovery Enhancement Migration:
- Ensures pgcrypto extension for gen_random_uuid()
- Adds idempotency_key column to recovery_candidates for deduplication
- Creates materialized view mv_top_pending for dashboard performance
- Adds worker claim index for unevaluated inputs
- Adds partial index for executing candidates
- Creates retention_jobs metadata table for archival tracking
- Creates refresh function for materialized view

Safe, additive migration - does not alter existing table structures.
"""

from sqlalchemy import text

from alembic import op

# revision identifiers
revision = "019_m10_recovery_enhancements"
down_revision = "018_m10_recovery_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ==========================================================================
    # 1. Ensure pgcrypto extension for gen_random_uuid()
    # ==========================================================================
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

    # ==========================================================================
    # 2. Ensure m10_recovery schema exists (idempotent)
    # ==========================================================================
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS m10_recovery;"))

    # ==========================================================================
    # 3. Add idempotency_key to recovery_candidates for request deduplication
    # ==========================================================================
    conn.execute(
        text(
            """
        ALTER TABLE public.recovery_candidates
        ADD COLUMN IF NOT EXISTS idempotency_key UUID UNIQUE;

        COMMENT ON COLUMN public.recovery_candidates.idempotency_key IS
            'Optional client-provided idempotency key for deduplicating ingest requests';
    """
        )
    )

    # ==========================================================================
    # 4. Add recovery_candidate_id FK column to suggestion_input for linking
    # ==========================================================================
    conn.execute(
        text(
            """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'm10_recovery'
                  AND table_name = 'suggestion_input'
                  AND column_name = 'recovery_candidate_id'
            ) THEN
                ALTER TABLE m10_recovery.suggestion_input
                ADD COLUMN recovery_candidate_id INTEGER NULL;

                COMMENT ON COLUMN m10_recovery.suggestion_input.recovery_candidate_id IS
                    'Link to public.recovery_candidates.id for cross-reference';
            END IF;
        END$$;
    """
        )
    )

    # ==========================================================================
    # 5. Create materialized view for top pending candidates (dashboard perf)
    # ==========================================================================
    conn.execute(
        text(
            """
        DROP MATERIALIZED VIEW IF EXISTS m10_recovery.mv_top_pending;

        CREATE MATERIALIZED VIEW m10_recovery.mv_top_pending AS
        SELECT
            rc.id AS candidate_id,
            rc.failure_match_id,
            rc.suggestion AS suggestion_text,
            COALESCE(rc.confidence, 0.0) AS confidence,
            COALESCE(rc.occurrence_count, 1) AS occurrence_count,
            rc.created_at,
            rc.error_code,
            rc.source,
            sa.action_code,
            sa.action_type,
            sa.name AS action_name,
            COALESCE(sa.success_rate, 0.0) AS action_success_rate,
            (
                SELECT COUNT(*)
                FROM m10_recovery.suggestion_input si
                WHERE si.suggestion_id = rc.id
            ) AS input_count,
            (
                SELECT COUNT(*)
                FROM m10_recovery.suggestion_provenance sp
                WHERE sp.suggestion_id = rc.id
            ) AS provenance_count
        FROM public.recovery_candidates rc
        LEFT JOIN m10_recovery.suggestion_action sa ON rc.selected_action_id = sa.id
        WHERE rc.decision = 'pending'
        ORDER BY COALESCE(rc.confidence, 0.0) DESC, COALESCE(rc.occurrence_count, 1) DESC
        WITH DATA;

        -- Unique index for REFRESH CONCURRENTLY support
        CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_pending_candidate
            ON m10_recovery.mv_top_pending(candidate_id);

        COMMENT ON MATERIALIZED VIEW m10_recovery.mv_top_pending IS
            'Performance view: top pending recovery candidates for quick dashboard lookup. Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.mv_top_pending;';
    """
        )
    )

    # ==========================================================================
    # 6. Worker claim index on suggestion_input (unevaluated inputs)
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_si_unevaluated_created
            ON m10_recovery.suggestion_input(created_at)
            WHERE normalized_value IS NULL;

        COMMENT ON INDEX m10_recovery.idx_si_unevaluated_created IS
            'Worker claim index for polling unevaluated inputs';
    """
        )
    )

    # ==========================================================================
    # 7. Partial index for executing candidates
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_rc_executing
            ON public.recovery_candidates(executed_at)
            WHERE execution_status = 'executing';

        COMMENT ON INDEX public.idx_rc_executing IS
            'Partial index for tracking currently executing candidates';
    """
        )
    )

    # ==========================================================================
    # 8. Partial index for pending candidates with high confidence
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_rc_pending_high_confidence
            ON public.recovery_candidates(confidence DESC, created_at DESC)
            WHERE decision = 'pending' AND confidence >= 0.5;

        COMMENT ON INDEX public.idx_rc_pending_high_confidence IS
            'Index for high-confidence pending candidates for priority processing';
    """
        )
    )

    # ==========================================================================
    # 9. Create retention_jobs metadata table for archival tracking
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.retention_jobs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            last_run TIMESTAMPTZ NULL,
            rows_archived INTEGER DEFAULT 0,
            rows_deleted INTEGER DEFAULT 0,
            retention_days INTEGER DEFAULT 90,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        -- Seed default retention jobs
        INSERT INTO m10_recovery.retention_jobs (name, retention_days)
        VALUES
            ('provenance_archive', 90),
            ('candidates_archive', 180),
            ('inputs_archive', 90)
        ON CONFLICT (name) DO NOTHING;

        COMMENT ON TABLE m10_recovery.retention_jobs IS
            'Tracks data retention/archival job metadata for compliance';
    """
        )
    )

    # ==========================================================================
    # 10. Create archive tables for provenance and inputs
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS m10_recovery.suggestion_provenance_archive (
            LIKE m10_recovery.suggestion_provenance INCLUDING ALL,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS m10_recovery.suggestion_input_archive (
            LIKE m10_recovery.suggestion_input INCLUDING ALL,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        COMMENT ON TABLE m10_recovery.suggestion_provenance_archive IS
            'Archive table for aged-out provenance records (>90 days by default)';
        COMMENT ON TABLE m10_recovery.suggestion_input_archive IS
            'Archive table for aged-out input records (>90 days by default)';
    """
        )
    )

    # ==========================================================================
    # 11. Create function for refreshing materialized view (for cron/scheduler)
    # ==========================================================================
    conn.execute(
        text(
            """
        CREATE OR REPLACE FUNCTION m10_recovery.refresh_mv_top_pending()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.mv_top_pending;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION m10_recovery.refresh_mv_top_pending IS
            'Refresh mv_top_pending materialized view. Call from cron or scheduler.';
    """
        )
    )

    # ==========================================================================
    # 12. Grants for application role (safe - handles missing roles)
    # ==========================================================================
    conn.execute(
        text(
            """
        DO $$
        BEGIN
            -- Grant to 'nova' role if it exists
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nova') THEN
                GRANT USAGE ON SCHEMA m10_recovery TO nova;
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA m10_recovery TO nova;
                GRANT SELECT ON m10_recovery.mv_top_pending TO nova;
                GRANT EXECUTE ON FUNCTION m10_recovery.refresh_mv_top_pending() TO nova;
                RAISE NOTICE 'Granted permissions to nova role';
            END IF;

            -- Grant to 'mobiverz_app' role if it exists
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mobiverz_app') THEN
                GRANT USAGE ON SCHEMA m10_recovery TO mobiverz_app;
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA m10_recovery TO mobiverz_app;
                GRANT SELECT ON m10_recovery.mv_top_pending TO mobiverz_app;
                GRANT EXECUTE ON FUNCTION m10_recovery.refresh_mv_top_pending() TO mobiverz_app;
                RAISE NOTICE 'Granted permissions to mobiverz_app role';
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Grant failed (non-fatal): %', SQLERRM;
        END$$;
    """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Drop function
    conn.execute(text("DROP FUNCTION IF EXISTS m10_recovery.refresh_mv_top_pending();"))

    # Drop archive tables
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.suggestion_input_archive;"))
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.suggestion_provenance_archive;"))

    # Drop retention jobs table
    conn.execute(text("DROP TABLE IF EXISTS m10_recovery.retention_jobs;"))

    # Drop indexes
    conn.execute(text("DROP INDEX IF EXISTS public.idx_rc_pending_high_confidence;"))
    conn.execute(text("DROP INDEX IF EXISTS public.idx_rc_executing;"))
    conn.execute(text("DROP INDEX IF EXISTS m10_recovery.idx_si_unevaluated_created;"))

    # Drop materialized view
    conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS m10_recovery.mv_top_pending;"))

    # Note: Not dropping idempotency_key column or recovery_candidate_id to avoid data loss
    # If needed, operator can run:
    # ALTER TABLE public.recovery_candidates DROP COLUMN IF EXISTS idempotency_key;
    # ALTER TABLE m10_recovery.suggestion_input DROP COLUMN IF EXISTS recovery_candidate_id;
