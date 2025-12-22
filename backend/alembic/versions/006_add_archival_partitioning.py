"""Add archival partitioning for approval_requests

Revision ID: 006_add_archival_partitioning
Revises: 005_add_approval_requests
Create Date: 2025-12-03

This migration:
1. Creates an archived_approval_requests table for resolved records >90 days
2. Adds indexes optimized for archival queries
3. Does NOT convert to native partitioning (would require table recreation)

For native partitioning, see docs/ops/partition-migration.md
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "006_add_archival_partitioning"
down_revision = "005_add_approval_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create archive table with same structure
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS archived_approval_requests (
            id VARCHAR PRIMARY KEY,
            correlation_id VARCHAR,
            policy_type VARCHAR NOT NULL,
            skill_id VARCHAR,
            tenant_id VARCHAR,
            agent_id VARCHAR,
            requested_by VARCHAR NOT NULL,
            justification VARCHAR,
            payload_json VARCHAR,
            status VARCHAR NOT NULL,
            status_history_json VARCHAR,
            required_level INTEGER NOT NULL,
            current_level INTEGER NOT NULL,
            approvals_json VARCHAR,
            escalate_to VARCHAR,
            escalation_timeout_seconds INTEGER NOT NULL,
            webhook_url VARCHAR,
            webhook_secret_hash VARCHAR,
            webhook_attempts INTEGER NOT NULL DEFAULT 0,
            last_webhook_status VARCHAR,
            last_webhook_at TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            resolved_at TIMESTAMP,
            archived_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """
    )

    # Add indexes on archive table
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_archived_approval_requests_tenant_id
        ON archived_approval_requests (tenant_id);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_archived_approval_requests_created_at
        ON archived_approval_requests (created_at);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_archived_approval_requests_archived_at
        ON archived_approval_requests (archived_at);
    """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_archived_approval_requests_status
        ON archived_approval_requests (status);
    """
    )

    # Create archival function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION archive_old_approval_requests(
            retention_days INTEGER DEFAULT 90
        ) RETURNS INTEGER AS $$
        DECLARE
            archived_count INTEGER;
        BEGIN
            -- Move resolved requests older than retention period
            WITH moved AS (
                DELETE FROM approval_requests
                WHERE status IN ('approved', 'rejected', 'expired')
                  AND resolved_at IS NOT NULL
                  AND resolved_at < NOW() - (retention_days || ' days')::INTERVAL
                RETURNING *
            )
            INSERT INTO archived_approval_requests
            SELECT *, NOW() as archived_at FROM moved;

            GET DIAGNOSTICS archived_count = ROW_COUNT;

            -- Log the archival
            RAISE NOTICE 'Archived % approval requests older than % days',
                archived_count, retention_days;

            RETURN archived_count;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Create view for unified access
    op.execute(
        """
        CREATE OR REPLACE VIEW all_approval_requests AS
        SELECT
            id, correlation_id, policy_type, skill_id, tenant_id, agent_id,
            requested_by, justification, payload_json, status, status_history_json,
            required_level, current_level, approvals_json, escalate_to,
            escalation_timeout_seconds, webhook_url, webhook_secret_hash,
            webhook_attempts, last_webhook_status, last_webhook_at,
            expires_at, created_at, updated_at, resolved_at,
            NULL::TIMESTAMP as archived_at,
            'active' as source
        FROM approval_requests
        UNION ALL
        SELECT
            id, correlation_id, policy_type, skill_id, tenant_id, agent_id,
            requested_by, justification, payload_json, status, status_history_json,
            required_level, current_level, approvals_json, escalate_to,
            escalation_timeout_seconds, webhook_url, webhook_secret_hash,
            webhook_attempts, last_webhook_status, last_webhook_at,
            expires_at, created_at, updated_at, resolved_at,
            archived_at,
            'archived' as source
        FROM archived_approval_requests;
    """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS all_approval_requests;")
    op.execute("DROP FUNCTION IF EXISTS archive_old_approval_requests;")
    op.execute("DROP TABLE IF EXISTS archived_approval_requests;")
