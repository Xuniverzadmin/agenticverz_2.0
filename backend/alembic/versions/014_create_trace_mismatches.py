"""Create trace mismatches table for replay-mismatch tracking

Revision ID: 014_trace_mismatches
Revises: 013_add_trace_retention
Create Date: 2025-12-06

Tracks replay mismatches for operator review and automated ticketing.
"""

from alembic import op

# revision identifiers
revision = "014_trace_mismatches"
down_revision = "013_add_trace_retention"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trace mismatches table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS aos_trace_mismatches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            trace_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            reported_by TEXT,
            step_index INTEGER,
            reason TEXT NOT NULL,
            expected_hash TEXT,
            actual_hash TEXT,
            details JSONB DEFAULT '{}',
            notification_sent BOOLEAN DEFAULT FALSE,
            issue_url TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMPTZ,
            resolved_by TEXT,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_mismatch_trace ON aos_trace_mismatches(trace_id);
        CREATE INDEX IF NOT EXISTS idx_mismatch_tenant ON aos_trace_mismatches(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_mismatch_created ON aos_trace_mismatches(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_mismatch_unresolved ON aos_trace_mismatches(resolved, created_at DESC)
            WHERE resolved = FALSE;

        -- Comment
        COMMENT ON TABLE aos_trace_mismatches IS 'Tracks replay mismatches for operator review';
    """
    )

    # Create metrics view for Prometheus scraping
    op.execute(
        """
        CREATE OR REPLACE VIEW aos_mismatch_metrics AS
        SELECT
            tenant_id,
            COUNT(*) FILTER (WHERE created_at > now() - interval '1 hour') AS mismatches_1h,
            COUNT(*) FILTER (WHERE created_at > now() - interval '24 hours') AS mismatches_24h,
            COUNT(*) FILTER (WHERE resolved = FALSE) AS unresolved_count,
            COUNT(*) FILTER (WHERE notification_sent = FALSE AND resolved = FALSE) AS pending_notification_count
        FROM aos_trace_mismatches
        GROUP BY tenant_id;
    """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS aos_mismatch_metrics;")
    op.execute("DROP TABLE IF EXISTS aos_trace_mismatches;")
