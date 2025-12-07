"""
Memory Audit Table Migration - M7 Enhancement

Creates system.memory_audit table for tracking memory operations.

Revision ID: 011_create_memory_audit
Revises: 010_create_rbac_audit
Create Date: 2025-12-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '011_create_memory_audit'
down_revision = '010_create_rbac_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create memory_audit table in system schema."""

    # Ensure system schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS system")

    # Create memory_audit table
    op.execute("""
        CREATE TABLE IF NOT EXISTS system.memory_audit (
            id BIGSERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            operation TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            key TEXT NOT NULL,
            agent_id TEXT,
            source TEXT,
            cache_hit BOOLEAN DEFAULT false,
            latency_ms DOUBLE PRECISION,
            success BOOLEAN NOT NULL DEFAULT true,
            error_message TEXT,
            old_value_hash TEXT,
            new_value_hash TEXT,
            extra JSONB DEFAULT '{}'::jsonb
        )
    """)

    # Create indexes for common queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_memory_audit_ts
        ON system.memory_audit(ts DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_memory_audit_tenant
        ON system.memory_audit(tenant_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_memory_audit_key
        ON system.memory_audit(key)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_memory_audit_operation
        ON system.memory_audit(operation)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_memory_audit_agent
        ON system.memory_audit(agent_id) WHERE agent_id IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_memory_audit_errors
        ON system.memory_audit(success) WHERE success = false
    """)

    # Create function for automated cleanup of old audit records
    op.execute("""
        CREATE OR REPLACE FUNCTION system.cleanup_memory_audit(retention_days INTEGER DEFAULT 30)
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM system.memory_audit
            WHERE ts < now() - (retention_days || ' days')::INTERVAL;
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Add comment
    op.execute("""
        COMMENT ON TABLE system.memory_audit IS
        'Audit log for memory operations (pins, retrieval, updates). M7 enhancement.'
    """)


def downgrade() -> None:
    """Drop memory_audit table."""
    op.execute("DROP FUNCTION IF EXISTS system.cleanup_memory_audit(INTEGER)")
    op.execute("DROP TABLE IF EXISTS system.memory_audit")
