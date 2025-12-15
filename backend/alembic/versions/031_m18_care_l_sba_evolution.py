"""M18 CARE-L + SBA Evolution

Creates tables for:
- Agent reputation tracking
- Boundary violations
- Drift signals
- Strategy adjustments
- Learning parameters

Revision ID: 031_m18_care_l_sba_evolution
Revises: 030_m17_care_routing
Create Date: 2025-12-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '031_m18_care_l_sba_evolution'
down_revision = '030_m17_care_routing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Agent Reputation Table
    # Use DO block to handle concurrent migration execution gracefully
    # =========================================================================
    op.execute("""
        DO $$
        BEGIN
            CREATE TABLE IF NOT EXISTS routing.agent_reputation (
                agent_id VARCHAR(128) PRIMARY KEY,
                reputation_score FLOAT NOT NULL DEFAULT 1.0,
                success_rate FLOAT NOT NULL DEFAULT 1.0,
                latency_percentile FLOAT NOT NULL DEFAULT 0.5,
                violation_count INT NOT NULL DEFAULT 0,
                quarantine_count INT NOT NULL DEFAULT 0,
                quarantine_state VARCHAR(20) NOT NULL DEFAULT 'active',
                quarantine_until TIMESTAMPTZ,
                quarantine_reason TEXT,
                total_routes INT NOT NULL DEFAULT 0,
                successful_routes INT NOT NULL DEFAULT 0,
                recent_failures INT NOT NULL DEFAULT 0,
                consecutive_successes INT NOT NULL DEFAULT 0,
                last_success_at TIMESTAMPTZ,
                last_failure_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            -- Table or type already exists (concurrent migration), skip
            NULL;
        END $$
    """)

    # Index for reputation queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reputation_score
        ON routing.agent_reputation (reputation_score DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reputation_state
        ON routing.agent_reputation (quarantine_state)
    """)

    # =========================================================================
    # Boundary Violations Table
    # =========================================================================
    op.execute("""
        DO $$
        BEGIN
            CREATE TABLE IF NOT EXISTS agents.boundary_violations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(128) NOT NULL,
                violation_type VARCHAR(50) NOT NULL,
                description TEXT,
                task_description TEXT,
                task_domain VARCHAR(100),
                severity FLOAT NOT NULL DEFAULT 0.5,
                auto_reported BOOLEAN NOT NULL DEFAULT false,
                detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            NULL;
        END $$
    """)

    # Index for violation queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_violations_agent
        ON agents.boundary_violations (agent_id, detected_at DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_violations_type
        ON agents.boundary_violations (violation_type, detected_at DESC)
    """)

    # =========================================================================
    # Drift Signals Table
    # =========================================================================
    op.execute("""
        DO $$
        BEGIN
            CREATE TABLE IF NOT EXISTS agents.drift_signals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(128) NOT NULL,
                drift_type VARCHAR(50) NOT NULL,
                severity FLOAT NOT NULL,
                evidence JSONB NOT NULL DEFAULT '{}',
                recommendation TEXT,
                acknowledged BOOLEAN NOT NULL DEFAULT false,
                auto_adjusted BOOLEAN NOT NULL DEFAULT false,
                detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            NULL;
        END $$
    """)

    # Index for drift queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_drift_agent
        ON agents.drift_signals (agent_id, detected_at DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_drift_unacknowledged
        ON agents.drift_signals (acknowledged, detected_at DESC)
        WHERE acknowledged = false
    """)

    # =========================================================================
    # Strategy Adjustments Table
    # =========================================================================
    op.execute("""
        DO $$
        BEGIN
            CREATE TABLE IF NOT EXISTS agents.strategy_adjustments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(128) NOT NULL,
                trigger VARCHAR(200) NOT NULL,
                adjustment_type VARCHAR(50) NOT NULL,
                old_strategy JSONB NOT NULL,
                new_strategy JSONB NOT NULL,
                success_rate_before FLOAT,
                success_rate_after FLOAT,
                adjusted_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            NULL;
        END $$
    """)

    # Index for adjustment queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_adjustments_agent
        ON agents.strategy_adjustments (agent_id, adjusted_at DESC)
    """)

    # =========================================================================
    # Learning Parameters Table
    # =========================================================================
    op.execute("""
        DO $$
        BEGIN
            CREATE TABLE IF NOT EXISTS routing.learning_parameters (
                id SERIAL PRIMARY KEY,
                parameter_name VARCHAR(100) NOT NULL UNIQUE,
                current_value FLOAT NOT NULL,
                min_value FLOAT NOT NULL,
                max_value FLOAT NOT NULL,
                adaptation_rate FLOAT NOT NULL DEFAULT 0.01,
                last_adjusted_at TIMESTAMPTZ,
                adjustment_reason TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        EXCEPTION WHEN duplicate_object OR unique_violation THEN
            NULL;
        END $$
    """)

    # Insert default learning parameters
    op.execute("""
        INSERT INTO routing.learning_parameters (
            parameter_name, current_value, min_value, max_value, adaptation_rate
        ) VALUES
            ('confidence_block', 0.35, 0.1, 0.5, 0.01),
            ('confidence_fallback', 0.55, 0.3, 0.8, 0.01),
            ('quarantine_failure_threshold', 5, 2, 10, 0.01),
            ('probation_failure_threshold', 3, 1, 7, 0.01),
            ('success_weight', 0.40, 0.2, 0.6, 0.01),
            ('latency_weight', 0.20, 0.1, 0.4, 0.01),
            ('violation_weight', 0.25, 0.1, 0.4, 0.01),
            ('hysteresis_threshold', 0.15, 0.05, 0.30, 0.01)
        ON CONFLICT (parameter_name) DO NOTHING
    """)

    # =========================================================================
    # Add reputation columns to routing_decisions for tracking
    # =========================================================================
    op.execute("""
        ALTER TABLE routing.routing_decisions
        ADD COLUMN IF NOT EXISTS agent_reputation_at_route FLOAT,
        ADD COLUMN IF NOT EXISTS quarantine_state_at_route VARCHAR(20)
    """)


def downgrade() -> None:
    # Drop columns from routing_decisions
    op.execute("""
        ALTER TABLE routing.routing_decisions
        DROP COLUMN IF EXISTS agent_reputation_at_route,
        DROP COLUMN IF EXISTS quarantine_state_at_route
    """)

    # Drop tables in reverse order
    op.execute("DROP TABLE IF EXISTS routing.learning_parameters")
    op.execute("DROP TABLE IF EXISTS agents.strategy_adjustments")
    op.execute("DROP TABLE IF EXISTS agents.drift_signals")
    op.execute("DROP TABLE IF EXISTS agents.boundary_violations")
    op.execute("DROP TABLE IF EXISTS routing.agent_reputation")
