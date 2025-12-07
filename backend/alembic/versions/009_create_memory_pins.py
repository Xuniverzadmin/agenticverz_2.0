"""Create memory_pins table for M7

Revision ID: 009_mem_pins
Revises: 008_add_provenance_and_alert_queue
Create Date: 2025-12-04

Memory pins provide structured key-value storage with:
- Tenant isolation
- JSONB values for flexible schema
- TTL support for expiring entries
- Source tracking for audit
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_mem_pins'
down_revision = '008_provenance_alerts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create system schema if not exists
    op.execute("CREATE SCHEMA IF NOT EXISTS system")

    # Create memory_pins table
    op.create_table(
        'memory_pins',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('tenant_id', sa.Text(), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source', sa.Text(), nullable=False, server_default='api'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='system'
    )

    # Create unique index on (tenant_id, key)
    op.create_index(
        'ix_memory_pins_tenant_key',
        'memory_pins',
        ['tenant_id', 'key'],
        unique=True,
        schema='system'
    )

    # Create index for TTL cleanup queries
    op.create_index(
        'ix_memory_pins_expires_at',
        'memory_pins',
        ['expires_at'],
        schema='system',
        postgresql_where=sa.text('expires_at IS NOT NULL')
    )

    # Create index for listing by tenant
    op.create_index(
        'ix_memory_pins_tenant_created',
        'memory_pins',
        ['tenant_id', 'created_at'],
        schema='system'
    )

    # Create trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION system.update_memory_pins_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            -- Auto-compute expires_at from ttl_seconds
            IF NEW.ttl_seconds IS NOT NULL THEN
                NEW.expires_at = NEW.created_at + (NEW.ttl_seconds || ' seconds')::interval;
            ELSE
                NEW.expires_at = NULL;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger
    op.execute("""
        CREATE TRIGGER memory_pins_updated_at_trigger
        BEFORE UPDATE ON system.memory_pins
        FOR EACH ROW
        EXECUTE FUNCTION system.update_memory_pins_updated_at();
    """)

    # Create trigger for insert (to set expires_at on creation)
    op.execute("""
        CREATE OR REPLACE FUNCTION system.set_memory_pins_expires_at()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.ttl_seconds IS NOT NULL THEN
                NEW.expires_at = NEW.created_at + (NEW.ttl_seconds || ' seconds')::interval;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER memory_pins_insert_expires_trigger
        BEFORE INSERT ON system.memory_pins
        FOR EACH ROW
        EXECUTE FUNCTION system.set_memory_pins_expires_at();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS memory_pins_updated_at_trigger ON system.memory_pins")
    op.execute("DROP TRIGGER IF EXISTS memory_pins_insert_expires_trigger ON system.memory_pins")

    # Drop trigger functions
    op.execute("DROP FUNCTION IF EXISTS system.update_memory_pins_updated_at()")
    op.execute("DROP FUNCTION IF EXISTS system.set_memory_pins_expires_at()")

    # Drop indexes
    op.drop_index('ix_memory_pins_tenant_created', table_name='memory_pins', schema='system')
    op.drop_index('ix_memory_pins_expires_at', table_name='memory_pins', schema='system')
    op.drop_index('ix_memory_pins_tenant_key', table_name='memory_pins', schema='system')

    # Drop table
    op.drop_table('memory_pins', schema='system')
