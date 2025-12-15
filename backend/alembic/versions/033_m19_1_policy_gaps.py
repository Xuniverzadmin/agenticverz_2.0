"""M19.1: Policy Layer Gap Fixes

Revision ID: 033_m19_1_gaps
Revises: 032_m19_policy
Create Date: 2025-12-15

This migration addresses critical gaps in M19 Policy Layer:
- GAP 1: Policy Versioning & Provenance
- GAP 2: Policy Dependency Graph & Conflict Resolution
- GAP 3: Temporal Policies (Sliding Windows)
- GAP 4: Policy Context Object (tracking tables)
- GAP 5: Enhanced Violation Classifications
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '033_m19_1_gaps'
down_revision = '032_m19_policy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # GAP 1: Policy Versioning & Provenance
    # ==========================================================================

    # Policy versions table - snapshots of policy sets
    op.create_table(
        'policy_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('version', sa.String(50), nullable=False),  # Semantic version
        sa.Column('policy_hash', sa.String(64), nullable=False),  # SHA256
        sa.Column('signature', sa.String(512), nullable=True),  # HMAC signature

        # Provenance
        sa.Column('created_by', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('description', sa.Text, nullable=True),

        # Content snapshots (JSONB for efficiency)
        sa.Column('policies_snapshot', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('risk_ceilings_snapshot', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('safety_rules_snapshot', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('ethical_constraints_snapshot', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('business_rules_snapshot', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('temporal_policies_snapshot', postgresql.JSONB, nullable=False, server_default='{}'),

        # Rollback info
        sa.Column('parent_version', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rolled_back_by', sa.String(128), nullable=True),

        schema='policy'
    )

    op.create_index('ix_policy_versions_version', 'policy_versions', ['version'], schema='policy')
    op.create_index('ix_policy_versions_active', 'policy_versions', ['is_active'], schema='policy')
    op.create_index('ix_policy_versions_created_at', 'policy_versions', ['created_at'], schema='policy')

    # Policy provenance table - audit trail
    op.create_table(
        'policy_provenance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_type', sa.String(50), nullable=False),

        # Change details
        sa.Column('action', sa.String(50), nullable=False),  # create, update, delete, activate
        sa.Column('changed_by', sa.String(128), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        # Before/after
        sa.Column('previous_value', postgresql.JSONB, nullable=True),
        sa.Column('new_value', postgresql.JSONB, nullable=True),

        # Version context
        sa.Column('policy_version', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text, nullable=True),

        schema='policy'
    )

    op.create_index('ix_provenance_policy_id', 'policy_provenance', ['policy_id'], schema='policy')
    op.create_index('ix_provenance_changed_at', 'policy_provenance', ['changed_at'], schema='policy')
    op.create_index('ix_provenance_action', 'policy_provenance', ['action'], schema='policy')

    # ==========================================================================
    # GAP 2: Policy Dependency Graph & Conflict Resolution
    # ==========================================================================

    # Policy dependencies table
    op.create_table(
        'policy_dependencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_policy', sa.String(128), nullable=False),  # Policy name/ID
        sa.Column('target_policy', sa.String(128), nullable=False),
        sa.Column('dependency_type', sa.String(50), nullable=False),  # requires, conflicts_with, overrides

        # Conflict resolution
        sa.Column('resolution_strategy', sa.String(50), nullable=False, server_default="'source_wins'"),
        sa.Column('priority', sa.Integer, nullable=False, server_default='100'),

        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_dependencies_source', 'policy_dependencies', ['source_policy'], schema='policy')
    op.create_index('ix_dependencies_target', 'policy_dependencies', ['target_policy'], schema='policy')
    op.create_index('ix_dependencies_type', 'policy_dependencies', ['dependency_type'], schema='policy')

    # Policy conflicts table
    op.create_table(
        'policy_conflicts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_a', sa.String(128), nullable=False),
        sa.Column('policy_b', sa.String(128), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.Float, nullable=False, server_default='0.5'),

        # Details
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('affected_action_types', postgresql.ARRAY(sa.String), nullable=True),

        # Resolution
        sa.Column('resolved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('resolution', sa.Text, nullable=True),
        sa.Column('resolved_by', sa.String(128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_conflicts_resolved', 'policy_conflicts', ['resolved'], schema='policy')
    op.create_index('ix_conflicts_severity', 'policy_conflicts', ['severity'], schema='policy')

    # ==========================================================================
    # GAP 3: Temporal Policies (Sliding Windows)
    # ==========================================================================

    # Temporal policies table
    op.create_table(
        'temporal_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),

        # Temporal definition
        sa.Column('temporal_type', sa.String(50), nullable=False),  # sliding_window, cumulative_daily, etc.
        sa.Column('metric', sa.String(100), nullable=False),  # retries, cost, adaptations
        sa.Column('max_value', sa.Float, nullable=False),
        sa.Column('window_seconds', sa.Integer, nullable=False),

        # Scope
        sa.Column('applies_to', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),
        sa.Column('agent_id', sa.String(128), nullable=True),

        # Breach handling
        sa.Column('breach_action', sa.String(50), nullable=False, server_default="'block'"),
        sa.Column('cooldown_on_breach', sa.Integer, nullable=False, server_default='0'),

        # State
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('breach_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_breach_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_temporal_metric', 'temporal_policies', ['metric'], schema='policy')
    op.create_index('ix_temporal_type', 'temporal_policies', ['temporal_type'], schema='policy')
    op.create_index('ix_temporal_agent', 'temporal_policies', ['agent_id'], schema='policy')

    # Temporal metric windows table (for tracking sliding window values)
    op.create_table(
        'temporal_metric_windows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(128), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),

        # Window key (for partitioning)
        sa.Column('window_key', sa.String(255), nullable=False),  # policy_id:agent_id:tenant_id

        # Current aggregates
        sa.Column('current_sum', sa.Float, nullable=False, server_default='0'),
        sa.Column('current_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('current_max', sa.Float, nullable=False, server_default='0'),

        # Window bounds
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),

        # Last update
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_metric_windows_key', 'temporal_metric_windows', ['window_key'], schema='policy', unique=True)
    op.create_index('ix_metric_windows_policy', 'temporal_metric_windows', ['policy_id'], schema='policy')

    # Temporal metric events table (individual events for sliding window computation)
    op.create_table(
        'temporal_metric_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(128), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),

        # Event data
        sa.Column('metric', sa.String(100), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        # Context
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('request_id', sa.String(128), nullable=True),

        schema='policy'
    )

    op.create_index('ix_metric_events_policy', 'temporal_metric_events', ['policy_id'], schema='policy')
    op.create_index('ix_metric_events_occurred', 'temporal_metric_events', ['occurred_at'], schema='policy')
    op.create_index('ix_metric_events_agent', 'temporal_metric_events', ['agent_id'], schema='policy')

    # ==========================================================================
    # GAP 4 & 5: Enhanced Violations Table
    # ==========================================================================

    # Add new columns to violations table for enhanced severity
    op.add_column('violations',
        sa.Column('severity_class', sa.String(50), nullable=True),
        schema='policy'
    )
    op.add_column('violations',
        sa.Column('recoverability', sa.String(50), nullable=True),
        schema='policy'
    )
    op.add_column('violations',
        sa.Column('action_chain_depth', sa.Integer, nullable=True, server_default='0'),
        schema='policy'
    )
    op.add_column('violations',
        sa.Column('is_temporal_violation', sa.Boolean, nullable=True, server_default='false'),
        schema='policy'
    )
    op.add_column('violations',
        sa.Column('temporal_window_seconds', sa.Integer, nullable=True),
        schema='policy'
    )
    op.add_column('violations',
        sa.Column('temporal_metric_value', sa.Float, nullable=True),
        schema='policy'
    )
    op.add_column('violations',
        sa.Column('recommended_action', sa.String(50), nullable=True),
        schema='policy'
    )

    # Add policy version tracking to evaluations
    op.add_column('evaluations',
        sa.Column('policy_version', sa.String(50), nullable=True),
        schema='policy'
    )
    op.add_column('evaluations',
        sa.Column('policy_hash', sa.String(64), nullable=True),
        schema='policy'
    )
    op.add_column('evaluations',
        sa.Column('temporal_policies_checked', sa.Integer, nullable=True, server_default='0'),
        schema='policy'
    )
    op.add_column('evaluations',
        sa.Column('dependencies_checked', sa.Integer, nullable=True, server_default='0'),
        schema='policy'
    )
    op.add_column('evaluations',
        sa.Column('conflicts_detected', sa.Integer, nullable=True, server_default='0'),
        schema='policy'
    )

    # ==========================================================================
    # Insert Default Temporal Policies
    # ==========================================================================

    op.execute("""
        INSERT INTO policy.temporal_policies
            (name, description, temporal_type, metric, max_value, window_seconds, breach_action)
        VALUES
        ('retry_total_per_24h', 'Maximum total retries per agent per day', 'cumulative_daily',
         'retries', 300, 86400, 'block'),
        ('adaptations_per_agent_per_day', 'Maximum strategy adaptations per agent per day', 'cumulative_daily',
         'adaptations', 10, 86400, 'throttle'),
        ('escalations_per_hour', 'Maximum escalations to humans per hour', 'sliding_window',
         'escalations', 20, 3600, 'throttle'),
        ('cost_burst_5min', 'Short-term cost spike protection', 'burst_limit',
         'cost', 10.0, 300, 'block'),
        ('external_calls_per_minute', 'External API call rate limit', 'sliding_window',
         'external_calls', 60, 60, 'throttle')
    """)

    # ==========================================================================
    # Insert Default Policy Dependencies
    # ==========================================================================

    op.execute("""
        INSERT INTO policy.policy_dependencies
            (source_policy, target_policy, dependency_type, resolution_strategy, description)
        VALUES
        ('ethical.no_manipulation', 'business.personalization', 'conflicts_with', 'source_wins',
         'Ethical no-manipulation overrides aggressive personalization'),
        ('risk.cascade_depth', 'routing.parallelization', 'modifies', 'source_wins',
         'Cascade depth limits affect routing parallelization'),
        ('safety.block_system_commands', 'business.automation', 'overrides', 'source_wins',
         'Safety rules always override automation business rules'),
        ('compliance.gdpr', 'business.data_sharing', 'conflicts_with', 'source_wins',
         'GDPR compliance overrides data sharing business rules'),
        ('ethical.transparency', 'risk.cost_optimization', 'modifies', 'merge',
         'Transparency requirements may increase costs')
    """)

    # Create initial policy version
    op.execute("""
        INSERT INTO policy.policy_versions
            (version, policy_hash, created_by, description, is_active)
        VALUES
        ('1.0.0', 'initial', 'system', 'Initial M19.1 policy set with gap fixes', true)
    """)


def downgrade() -> None:
    # Remove new columns from evaluations
    op.drop_column('evaluations', 'conflicts_detected', schema='policy')
    op.drop_column('evaluations', 'dependencies_checked', schema='policy')
    op.drop_column('evaluations', 'temporal_policies_checked', schema='policy')
    op.drop_column('evaluations', 'policy_hash', schema='policy')
    op.drop_column('evaluations', 'policy_version', schema='policy')

    # Remove new columns from violations
    op.drop_column('violations', 'recommended_action', schema='policy')
    op.drop_column('violations', 'temporal_metric_value', schema='policy')
    op.drop_column('violations', 'temporal_window_seconds', schema='policy')
    op.drop_column('violations', 'is_temporal_violation', schema='policy')
    op.drop_column('violations', 'action_chain_depth', schema='policy')
    op.drop_column('violations', 'recoverability', schema='policy')
    op.drop_column('violations', 'severity_class', schema='policy')

    # Drop new tables
    op.drop_table('temporal_metric_events', schema='policy')
    op.drop_table('temporal_metric_windows', schema='policy')
    op.drop_table('temporal_policies', schema='policy')
    op.drop_table('policy_conflicts', schema='policy')
    op.drop_table('policy_dependencies', schema='policy')
    op.drop_table('policy_provenance', schema='policy')
    op.drop_table('policy_versions', schema='policy')
