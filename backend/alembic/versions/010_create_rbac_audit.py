"""
RBAC Audit Table Migration - M7 Enhancement

Creates system.rbac_audit table for tracking authorization decisions.

Revision ID: 010_create_rbac_audit
Revises: 009_mem_pins
Create Date: 2025-12-04
"""


from alembic import op

# revision identifiers
revision = "010_create_rbac_audit"
down_revision = "009_mem_pins"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rbac_audit table in system schema."""

    # Ensure system schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS system")

    # Create rbac_audit table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system.rbac_audit (
            id BIGSERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            subject TEXT NOT NULL,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            allowed BOOLEAN NOT NULL,
            reason TEXT,
            roles TEXT[],
            path TEXT,
            method TEXT,
            tenant_id TEXT,
            request_id TEXT,
            latency_ms DOUBLE PRECISION,
            extra JSONB DEFAULT '{}'::jsonb
        )
    """
    )

    # Create indexes for common queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rbac_audit_ts
        ON system.rbac_audit(ts DESC)
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rbac_audit_subject
        ON system.rbac_audit(subject)
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rbac_audit_resource_action
        ON system.rbac_audit(resource, action)
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rbac_audit_allowed
        ON system.rbac_audit(allowed) WHERE allowed = false
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rbac_audit_tenant
        ON system.rbac_audit(tenant_id) WHERE tenant_id IS NOT NULL
    """
    )

    # Create function for automated cleanup of old audit records (retention policy)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION system.cleanup_rbac_audit(retention_days INTEGER DEFAULT 90)
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM system.rbac_audit
            WHERE ts < now() - (retention_days || ' days')::INTERVAL;
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql
    """
    )

    # Add comment
    op.execute(
        """
        COMMENT ON TABLE system.rbac_audit IS
        'Audit log for RBAC authorization decisions. M7 enhancement.'
    """
    )


def downgrade() -> None:
    """Drop rbac_audit table."""
    op.execute("DROP FUNCTION IF EXISTS system.cleanup_rbac_audit(INTEGER)")
    op.execute("DROP TABLE IF EXISTS system.rbac_audit")
