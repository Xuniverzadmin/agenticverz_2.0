"""M25: Pillar Integration Loop - Enhanced

Revision ID: 042_m25_integration
Revises: 041_fix_enqueue_work_constraint
Create Date: 2025-12-23

Enhanced with:
- Confidence bands (strong/weak/novel) for pattern matching
- Loop failure states for unhappy paths
- Policy shadow mode with confirmation requirements
- CARE routing guardrails (max delta, decay, rollback)
- Human checkpoint controls
- Narrative artifacts for console storytelling
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '042_m25_integration'
down_revision = '041_fix_enqueue_work_constraint'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # LOOP TRACES TABLE - Tracks full loop status
    # =========================================================================
    op.create_table(
        'loop_traces',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('incident_id', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('stages', JSONB, nullable=False, server_default='{}'),
        sa.Column('failure_state', sa.String(64)),  # LoopFailureState value
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('is_complete', sa.Boolean, server_default='false'),
        sa.Column('is_blocked', sa.Boolean, server_default='false'),
        sa.Column('pending_checkpoints', JSONB, server_default='[]'),
        sa.Column('narrative', JSONB),  # Narrative artifacts
    )
    op.create_index('idx_loop_trace_incident', 'loop_traces', ['incident_id'])
    op.create_index('idx_loop_trace_tenant', 'loop_traces', ['tenant_id', 'is_complete'])
    op.create_index('idx_loop_trace_blocked', 'loop_traces', ['tenant_id', 'is_blocked'])

    # =========================================================================
    # LOOP EVENTS TABLE - Individual stage events for durability
    # =========================================================================
    op.create_table(
        'loop_events',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('incident_id', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('stage', sa.String(32), nullable=False),
        sa.Column('details', JSONB),
        sa.Column('failure_state', sa.String(64)),  # If failed
        sa.Column('confidence_band', sa.String(32)),  # strong/weak/novel
        sa.Column('requires_human_review', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_loop_events_incident', 'loop_events', ['incident_id', 'created_at'])
    op.create_index('idx_loop_events_tenant_stage', 'loop_events', ['tenant_id', 'stage'])

    # =========================================================================
    # HUMAN CHECKPOINTS TABLE - Manual intervention points
    # =========================================================================
    op.create_table(
        'human_checkpoints',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('checkpoint_type', sa.String(32), nullable=False),  # approve_policy, simulate_routing, etc.
        sa.Column('incident_id', sa.String(64), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('stage', sa.String(32), nullable=False),
        sa.Column('target_id', sa.String(64), nullable=False),  # policy_id, recovery_id, etc.
        sa.Column('description', sa.Text),
        sa.Column('options', JSONB, server_default='[]'),  # Available actions
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', sa.String(64)),  # user_id
        sa.Column('resolution', sa.String(32)),  # approve, reject, etc.
    )
    op.create_index('idx_checkpoints_tenant', 'human_checkpoints', ['tenant_id', 'resolved_at'])
    op.create_index('idx_checkpoints_pending', 'human_checkpoints', ['tenant_id'],
                    postgresql_where=sa.text('resolved_at IS NULL'))

    # =========================================================================
    # ROUTING POLICY ADJUSTMENTS TABLE - With guardrails
    # =========================================================================
    op.create_table(
        'routing_policy_adjustments',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('agent_id', sa.String(64), nullable=False),
        sa.Column('capability', sa.String(128)),
        sa.Column('adjustment_type', sa.String(32), nullable=False),  # confidence_penalty, route_block, etc.
        sa.Column('magnitude', sa.Float, nullable=False),  # -1.0 to +1.0
        sa.Column('reason', sa.Text),
        sa.Column('source_policy_id', sa.String(64)),
        # Guardrails
        sa.Column('max_delta', sa.Float, server_default='0.2'),  # Never adjust more than 20%
        sa.Column('decay_days', sa.Integer, server_default='7'),  # Decay over 7 days
        sa.Column('rollback_threshold', sa.Float, server_default='0.1'),  # Rollback if KPI drops 10%
        # State
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('was_rolled_back', sa.Boolean, server_default='false'),
        sa.Column('rollback_reason', sa.Text),
        sa.Column('kpi_baseline', sa.Float),
        sa.Column('kpi_current', sa.Float),
    )
    op.create_index('idx_routing_adj_agent', 'routing_policy_adjustments', ['agent_id', 'is_active'])
    op.create_index('idx_routing_adj_policy', 'routing_policy_adjustments', ['source_policy_id'])

    # =========================================================================
    # ADD COLUMNS TO EXISTING TABLES (with existence checks for schema drift)
    # =========================================================================

    # Incidents - Add pattern matching and loop tracking
    op.execute("""
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS matched_pattern_id VARCHAR(64);
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS loop_trace_id VARCHAR(64);
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS match_confidence FLOAT;
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS match_confidence_band VARCHAR(32);
    """)

    # =========================================================================
    # CREATE FAILURE_PATTERNS TABLE (if it doesn't exist)
    # =========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS failure_patterns (
            id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            pattern_type VARCHAR(32) NOT NULL,
            signature JSONB NOT NULL DEFAULT '{}',
            first_incident_id VARCHAR(64),
            recovery_template JSONB,
            auto_apply_recovery BOOLEAN DEFAULT false,
            signature_hash VARCHAR(64),
            last_occurrence_at TIMESTAMP WITH TIME ZONE,
            occurrence_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Add columns if table already existed but columns don't
    op.execute("""
        ALTER TABLE failure_patterns ADD COLUMN IF NOT EXISTS first_incident_id VARCHAR(64);
        ALTER TABLE failure_patterns ADD COLUMN IF NOT EXISTS recovery_template JSONB;
        ALTER TABLE failure_patterns ADD COLUMN IF NOT EXISTS auto_apply_recovery BOOLEAN DEFAULT false;
        ALTER TABLE failure_patterns ADD COLUMN IF NOT EXISTS signature_hash VARCHAR(64);
        ALTER TABLE failure_patterns ADD COLUMN IF NOT EXISTS last_occurrence_at TIMESTAMP WITH TIME ZONE;
    """)

    # Create index on signature_hash for fast exact matching
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_pattern_signature_hash ON failure_patterns (signature_hash)
    """)

    # Recovery candidates - Add source tracking
    op.execute("""
        ALTER TABLE recovery_candidates ADD COLUMN IF NOT EXISTS source_pattern_id VARCHAR(64);
        ALTER TABLE recovery_candidates ADD COLUMN IF NOT EXISTS source_incident_id VARCHAR(64);
        ALTER TABLE recovery_candidates ADD COLUMN IF NOT EXISTS suggestion_type VARCHAR(32);
        ALTER TABLE recovery_candidates ADD COLUMN IF NOT EXISTS confidence_band VARCHAR(32);
        ALTER TABLE recovery_candidates ADD COLUMN IF NOT EXISTS requires_confirmation INTEGER DEFAULT 0;
        ALTER TABLE recovery_candidates ADD COLUMN IF NOT EXISTS confirmations_received INTEGER DEFAULT 0;
    """)

    # =========================================================================
    # CREATE POLICY_RULES TABLE (if it doesn't exist)
    # =========================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS policy_rules (
            id VARCHAR(64) PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            rule_type VARCHAR(32) NOT NULL,
            conditions JSONB DEFAULT '{}',
            actions JSONB DEFAULT '{}',
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            source_type VARCHAR(32),
            source_pattern_id VARCHAR(64),
            source_recovery_id VARCHAR(64),
            source_incident_id VARCHAR(64),
            generation_confidence FLOAT,
            mode VARCHAR(32) DEFAULT 'active',
            confirmations_required INTEGER DEFAULT 3,
            confirmations_received INTEGER DEFAULT 0,
            regret_count INTEGER DEFAULT 0,
            shadow_evaluations INTEGER DEFAULT 0,
            shadow_would_block INTEGER DEFAULT 0,
            activated_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Add columns if table already existed but columns don't
    op.execute("""
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS source_type VARCHAR(32);
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS source_pattern_id VARCHAR(64);
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS source_recovery_id VARCHAR(64);
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS generation_confidence FLOAT;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS mode VARCHAR(32) DEFAULT 'active';
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS confirmations_required INTEGER DEFAULT 3;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS confirmations_received INTEGER DEFAULT 0;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS regret_count INTEGER DEFAULT 0;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS shadow_evaluations INTEGER DEFAULT 0;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS shadow_would_block INTEGER DEFAULT 0;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP WITH TIME ZONE;
    """)


def downgrade():
    # Drop columns from existing tables (with IF EXISTS for safety)
    op.execute("""
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS activated_at;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS shadow_would_block;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS shadow_evaluations;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS regret_count;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS confirmations_received;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS confirmations_required;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS mode;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS generation_confidence;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS source_recovery_id;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS source_pattern_id;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS source_type;

        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS confirmations_received;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS requires_confirmation;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS confidence_band;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS suggestion_type;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS source_incident_id;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS source_pattern_id;

        DROP INDEX IF EXISTS idx_pattern_signature_hash;
        ALTER TABLE failure_patterns DROP COLUMN IF EXISTS last_occurrence_at;
        ALTER TABLE failure_patterns DROP COLUMN IF EXISTS signature_hash;
        ALTER TABLE failure_patterns DROP COLUMN IF EXISTS auto_apply_recovery;
        ALTER TABLE failure_patterns DROP COLUMN IF EXISTS recovery_template;
        ALTER TABLE failure_patterns DROP COLUMN IF EXISTS first_incident_id;

        ALTER TABLE incidents DROP COLUMN IF EXISTS match_confidence_band;
        ALTER TABLE incidents DROP COLUMN IF EXISTS match_confidence;
        ALTER TABLE incidents DROP COLUMN IF EXISTS loop_trace_id;
        ALTER TABLE incidents DROP COLUMN IF EXISTS matched_pattern_id;
    """)

    # Drop new tables
    op.execute("DROP TABLE IF EXISTS routing_policy_adjustments")
    op.execute("DROP TABLE IF EXISTS human_checkpoints")
    op.execute("DROP TABLE IF EXISTS loop_events")
    op.execute("DROP TABLE IF EXISTS loop_traces")
    op.execute("DROP TABLE IF EXISTS policy_rules")
    op.execute("DROP TABLE IF EXISTS failure_patterns")
