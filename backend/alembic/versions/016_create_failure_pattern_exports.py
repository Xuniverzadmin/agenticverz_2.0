"""Create failure_pattern_exports table for R2 upload audit

Revision ID: 016_failure_pattern_exports
Revises: 015b_harden_failure_matches
Create Date: 2025-12-08

Tracks all failure pattern exports to R2 storage:
- Successful uploads
- Local fallback files (pending retry)
- Retry history
"""

from alembic import op

# revision identifiers
revision = "016_failure_pattern_exports"
down_revision = "015b_harden_failure_matches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the failure_pattern_exports table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS failure_pattern_exports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            s3_key TEXT NOT NULL,
            uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            uploader TEXT,
            size_bytes BIGINT,
            sha256 TEXT,
            status TEXT NOT NULL,
            notes TEXT,
            retry_count INTEGER DEFAULT 0,
            last_retry_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        -- Index for querying by status (pending retries)
        CREATE INDEX IF NOT EXISTS idx_fpe_status
        ON failure_pattern_exports(status);

        -- Index for listing exports by date
        CREATE INDEX IF NOT EXISTS idx_fpe_uploaded_at
        ON failure_pattern_exports(uploaded_at DESC);

        -- Index for SHA lookup (deduplication)
        CREATE INDEX IF NOT EXISTS idx_fpe_sha256
        ON failure_pattern_exports(sha256);

        -- Comment on table
        COMMENT ON TABLE failure_pattern_exports IS
            'Audit trail for failure pattern exports to R2 storage';

        -- Comments on columns
        COMMENT ON COLUMN failure_pattern_exports.s3_key IS
            'R2 object key or local fallback path';
        COMMENT ON COLUMN failure_pattern_exports.status IS
            'uploaded | fallback_local | retrying | failed';
        COMMENT ON COLUMN failure_pattern_exports.retry_count IS
            'Number of retry attempts for fallback files';
    """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS idx_fpe_sha256;
        DROP INDEX IF EXISTS idx_fpe_uploaded_at;
        DROP INDEX IF EXISTS idx_fpe_status;
        DROP TABLE IF EXISTS failure_pattern_exports;
    """
    )
