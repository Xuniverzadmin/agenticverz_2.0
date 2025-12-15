"""M15.1 Strategy-Bound Agent (SBA) Schema

Revision ID: 028_m15_1_sba_schema
Revises: 027_m15_llm_governance
Create Date: 2025-12-14

Adds agent_registry table with JSONB SBA storage for Strategy Cascade compliance.

Key Design:
- agent_registry: Agent definitions with SBA metadata
- JSONB sba column: Stores the 5-element Strategy Cascade
- sba_version: For schema evolution and compatibility
- Validation function: Check SBA at spawn time

Based on: M15.1 SBA Foundations (Hard Enforcement Layer)
"""

revision = '028_m15_1_sba_schema'
down_revision = '027_m15_llm_governance'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def upgrade():
    # 1. Create agent_registry table for agent definitions
    op.create_table(
        'agent_registry',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.String(128), nullable=False, unique=True),  # Unique agent identifier
        sa.Column('agent_name', sa.String(256), nullable=True),  # Human-readable name
        sa.Column('description', sa.Text(), nullable=True),  # Agent description
        sa.Column('agent_type', sa.String(64), nullable=False, server_default='worker'),  # worker, orchestrator, aggregator

        # SBA Schema (Strategy Cascade) - JSONB for flexibility
        sa.Column('sba', JSONB, nullable=True),  # The 5-element Strategy Cascade
        sa.Column('sba_version', sa.String(16), nullable=True),  # SBA schema version
        sa.Column('sba_validated', sa.Boolean(), nullable=False, server_default='false'),  # Has SBA been validated
        sa.Column('sba_validated_at', sa.DateTime(timezone=True), nullable=True),  # When SBA was validated

        # Capabilities and config
        sa.Column('capabilities', JSONB, server_default='{}', nullable=False),  # Skills, rate limits
        sa.Column('config', JSONB, server_default='{}', nullable=False),  # Default configuration

        # Status and lifecycle
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),  # active, deprecated, disabled
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),

        # Tenant isolation
        sa.Column('tenant_id', sa.String(128), nullable=False, server_default='default', index=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        schema='agents'
    )

    # Index for agent lookups by type
    op.create_index(
        'idx_agent_registry_type',
        'agent_registry',
        ['agent_type', 'enabled'],
        schema='agents'
    )

    # Index for SBA validation status
    op.create_index(
        'idx_agent_registry_sba_validated',
        'agent_registry',
        ['sba_validated'],
        schema='agents'
    )

    # 2. Add agent_name column to instances table (for better tracking)
    op.add_column(
        'instances',
        sa.Column('agent_name', sa.String(256), nullable=True),
        schema='agents'
    )

    # 3. Create validation function for SBA at spawn time
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.validate_agent_sba(
            p_agent_id TEXT
        ) RETURNS TABLE(
            valid BOOLEAN,
            error_code TEXT,
            error_message TEXT
        ) AS $$
        DECLARE
            v_sba JSONB;
            v_sba_version TEXT;
            v_validated BOOLEAN;
        BEGIN
            -- Get agent SBA from registry
            SELECT sba, sba_version, sba_validated
            INTO v_sba, v_sba_version, v_validated
            FROM agents.agent_registry
            WHERE agent_id = p_agent_id AND enabled = true;

            -- Agent not found
            IF NOT FOUND THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'AGENT_NOT_FOUND'::TEXT,
                    ('Agent not found in registry: ' || p_agent_id)::TEXT;
                RETURN;
            END IF;

            -- No SBA defined
            IF v_sba IS NULL THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_SBA'::TEXT,
                    ('Agent has no SBA schema: ' || p_agent_id)::TEXT;
                RETURN;
            END IF;

            -- Check required SBA fields
            IF NOT (v_sba ? 'winning_aspiration') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing winning_aspiration in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'where_to_play') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing where_to_play in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'how_to_win') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing how_to_win in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'capabilities_capacity') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing capabilities_capacity in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'enabling_management_systems') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing enabling_management_systems in SBA'::TEXT;
                RETURN;
            END IF;

            -- Check governance is BudgetLLM
            IF (v_sba->'enabling_management_systems'->>'governance') != 'BudgetLLM' THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'GOVERNANCE_REQUIRED'::TEXT,
                    'BudgetLLM governance is required'::TEXT;
                RETURN;
            END IF;

            -- Check tasks not empty
            IF jsonb_array_length(v_sba->'how_to_win'->'tasks') = 0 THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'EMPTY_TASKS'::TEXT,
                    'how_to_win.tasks cannot be empty'::TEXT;
                RETURN;
            END IF;

            -- All checks passed
            RETURN QUERY SELECT
                true::BOOLEAN,
                NULL::TEXT,
                NULL::TEXT;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 4. Create function to get or register agent
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.get_or_create_agent(
            p_agent_id TEXT,
            p_agent_type TEXT DEFAULT 'worker',
            p_tenant_id TEXT DEFAULT 'default'
        ) RETURNS UUID AS $$
        DECLARE
            v_id UUID;
        BEGIN
            -- Try to get existing
            SELECT id INTO v_id
            FROM agents.agent_registry
            WHERE agent_id = p_agent_id;

            IF FOUND THEN
                RETURN v_id;
            END IF;

            -- Create new entry
            INSERT INTO agents.agent_registry (
                agent_id, agent_type, tenant_id,
                capabilities, config
            ) VALUES (
                p_agent_id, p_agent_type, p_tenant_id,
                '{}', '{}'
            )
            RETURNING id INTO v_id;

            RETURN v_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 5. Create trigger to update updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.update_agent_registry_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER agent_registry_updated_at
        BEFORE UPDATE ON agents.agent_registry
        FOR EACH ROW
        EXECUTE FUNCTION agents.update_agent_registry_timestamp();
    """)

    # 6. Update job_progress view to include SBA info
    # Must drop and recreate because we're changing column types
    op.execute("DROP VIEW IF EXISTS agents.job_progress CASCADE")
    op.execute("""
        CREATE VIEW agents.job_progress AS
        SELECT
            j.id,
            j.task,
            j.status,
            j.total_items,
            j.completed_items,
            j.failed_items,
            j.total_items - j.completed_items - j.failed_items AS pending_items,
            CASE
                WHEN j.total_items > 0
                THEN ROUND((j.completed_items::NUMERIC / j.total_items) * 100, 2)
                ELSE 0
            END AS progress_pct,
            j.credits_reserved,
            j.credits_spent,
            j.credits_refunded,
            -- M15: LLM governance
            j.llm_budget_cents,
            j.llm_budget_used,
            j.llm_budget_cents - j.llm_budget_used AS llm_budget_remaining,
            j.llm_risk_violations,
            (SELECT COUNT(*) FROM agents.job_items ji WHERE ji.job_id = j.id AND ji.blocked = true) AS blocked_items,
            (SELECT COALESCE(AVG(ji.risk_score), 0) FROM agents.job_items ji WHERE ji.job_id = j.id AND ji.risk_score IS NOT NULL) AS avg_risk_score,
            j.created_at,
            j.started_at,
            j.completed_at,
            EXTRACT(EPOCH FROM (COALESCE(j.completed_at, now()) - j.started_at)) AS duration_seconds
        FROM agents.jobs j;
    """)


def downgrade():
    # Drop updated view
    op.execute("""
        CREATE OR REPLACE VIEW agents.job_progress AS
        SELECT
            j.id,
            j.task,
            j.status,
            j.total_items,
            j.completed_items,
            j.failed_items,
            j.total_items - j.completed_items - j.failed_items AS pending_items,
            CASE
                WHEN j.total_items > 0
                THEN ROUND((j.completed_items::NUMERIC / j.total_items) * 100, 2)
                ELSE 0
            END AS progress_pct,
            j.credits_reserved,
            j.credits_spent,
            j.credits_refunded,
            j.created_at,
            j.started_at,
            j.completed_at,
            EXTRACT(EPOCH FROM (COALESCE(j.completed_at, now()) - j.started_at)) AS duration_seconds
        FROM agents.jobs j;
    """)

    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS agent_registry_updated_at ON agents.agent_registry")
    op.execute("DROP FUNCTION IF EXISTS agents.update_agent_registry_timestamp()")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS agents.get_or_create_agent(TEXT, TEXT, TEXT)")
    op.execute("DROP FUNCTION IF EXISTS agents.validate_agent_sba(TEXT)")

    # Drop column from instances
    op.drop_column('instances', 'agent_name', schema='agents')

    # Drop indexes
    op.drop_index('idx_agent_registry_sba_validated', table_name='agent_registry', schema='agents')
    op.drop_index('idx_agent_registry_type', table_name='agent_registry', schema='agents')

    # Drop table
    op.drop_table('agent_registry', schema='agents')
