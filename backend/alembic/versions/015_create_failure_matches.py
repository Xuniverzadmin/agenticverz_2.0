"""Create failure_matches table for M9 failure persistence

Revision ID: 015_failure_matches
Revises: 014_trace_mismatches
Create Date: 2025-12-07

Tracks all failure catalog matches for:
- Learning from runtime errors
- Recovery suggestion engine (M10)
- Failure analytics dashboards
- Pattern aggregation for unknown errors
"""

from alembic import op

# revision identifiers
revision = "015_failure_matches"
down_revision = "014_trace_mismatches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create failure_matches table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS failure_matches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id TEXT NOT NULL,
            tenant_id TEXT,
            error_code TEXT NOT NULL,
            error_message TEXT,
            catalog_entry_id TEXT,
            match_type TEXT NOT NULL DEFAULT 'unknown',
            confidence_score FLOAT NOT NULL DEFAULT 0.0,
            category TEXT,
            severity TEXT,
            is_retryable BOOLEAN DEFAULT FALSE,
            recovery_mode TEXT,
            recovery_suggestion TEXT,
            recovery_attempted BOOLEAN DEFAULT FALSE,
            recovery_succeeded BOOLEAN DEFAULT FALSE,
            skill_id TEXT,
            step_index INTEGER,
            context_json JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
        );

        -- Indexes for common query patterns
        CREATE INDEX IF NOT EXISTS idx_fm_run_id ON failure_matches(run_id);
        CREATE INDEX IF NOT EXISTS idx_fm_tenant_id ON failure_matches(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_fm_error_code ON failure_matches(error_code);
        CREATE INDEX IF NOT EXISTS idx_fm_catalog_entry ON failure_matches(catalog_entry_id);
        CREATE INDEX IF NOT EXISTS idx_fm_created_at ON failure_matches(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_fm_category ON failure_matches(category);
        CREATE INDEX IF NOT EXISTS idx_fm_unmatched ON failure_matches(created_at DESC)
            WHERE catalog_entry_id IS NULL;
        CREATE INDEX IF NOT EXISTS idx_fm_recovery_pending ON failure_matches(created_at DESC)
            WHERE recovery_attempted = FALSE AND is_retryable = TRUE;

        -- Comment
        COMMENT ON TABLE failure_matches IS 'M9: Persistent storage for failure catalog matches';
    """
    )

    # Create aggregation helper view for candidate pattern detection
    op.execute(
        """
        CREATE OR REPLACE VIEW failure_pattern_candidates AS
        SELECT
            error_code,
            error_message,
            COUNT(*) AS occurrence_count,
            MAX(created_at) AS last_seen,
            MIN(created_at) AS first_seen,
            array_agg(DISTINCT skill_id) FILTER (WHERE skill_id IS NOT NULL) AS affected_skills,
            array_agg(DISTINCT tenant_id) FILTER (WHERE tenant_id IS NOT NULL) AS affected_tenants
        FROM failure_matches
        WHERE catalog_entry_id IS NULL
          AND created_at > now() - interval '7 days'
        GROUP BY error_code, error_message
        HAVING COUNT(*) >= 3
        ORDER BY occurrence_count DESC;

        COMMENT ON VIEW failure_pattern_candidates IS 'Unmatched failures aggregated for catalog expansion';
    """
    )

    # Create metrics view for Prometheus scraping
    op.execute(
        """
        CREATE OR REPLACE VIEW failure_match_metrics AS
        SELECT
            COALESCE(tenant_id, 'global') AS tenant_id,
            COUNT(*) FILTER (WHERE catalog_entry_id IS NOT NULL) AS hits_total,
            COUNT(*) FILTER (WHERE catalog_entry_id IS NULL) AS misses_total,
            COUNT(*) FILTER (WHERE recovery_succeeded = TRUE) AS recovery_success_total,
            COUNT(*) FILTER (WHERE recovery_attempted = TRUE AND recovery_succeeded = FALSE) AS recovery_failure_total,
            COUNT(*) FILTER (WHERE created_at > now() - interval '1 hour') AS matches_1h,
            COUNT(*) FILTER (WHERE created_at > now() - interval '24 hours') AS matches_24h,
            COUNT(*) FILTER (WHERE is_retryable = TRUE) AS retryable_total,
            COUNT(*) FILTER (WHERE category = 'TRANSIENT') AS transient_total,
            COUNT(*) FILTER (WHERE category = 'PERMANENT') AS permanent_total
        FROM failure_matches
        GROUP BY ROLLUP(tenant_id);

        COMMENT ON VIEW failure_match_metrics IS 'Aggregated failure metrics for Prometheus';
    """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS failure_match_metrics;")
    op.execute("DROP VIEW IF EXISTS failure_pattern_candidates;")
    op.execute("DROP TABLE IF EXISTS failure_matches;")
