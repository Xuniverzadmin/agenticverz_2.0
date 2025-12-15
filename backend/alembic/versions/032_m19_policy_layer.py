"""M19: Policy Layer - Constitutional Governance for Multi-Agent Systems

Revision ID: 032_m19_policy
Revises: 031_m18_care_l_sba_evolution
Create Date: 2025-12-15

This migration creates the policy layer schema for M19:
- Policy definitions with versioning
- Policy evaluations audit log
- Policy violations tracking
- Risk ceilings and safety rules
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '032_m19_policy'
down_revision = '031_m18_care_l_sba_evolution'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create policy schema
    op.execute("CREATE SCHEMA IF NOT EXISTS policy")

    # ==========================================================================
    # Policy Definitions
    # ==========================================================================
    op.create_table(
        'policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('category', sa.String(50), nullable=False),  # compliance, ethical, risk, safety, business
        sa.Column('description', sa.Text, nullable=True),

        # Policy definition (rules in JSON)
        sa.Column('rules', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('constraints', postgresql.JSONB, nullable=False, server_default='{}'),

        # Versioning
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('supersedes_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Applicability
        sa.Column('applies_to', postgresql.ARRAY(sa.String), nullable=True),  # agent types
        sa.Column('tenant_id', sa.String(128), nullable=True),  # null = global policy
        sa.Column('priority', sa.Integer, nullable=False, server_default='100'),  # lower = higher priority

        # Tamper protection
        sa.Column('signature', sa.String(256), nullable=True),  # HMAC signature
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signed_by', sa.String(128), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),

        schema='policy'
    )

    # Policy indexes
    op.create_index('ix_policies_category', 'policies', ['category'], schema='policy')
    op.create_index('ix_policies_tenant_id', 'policies', ['tenant_id'], schema='policy')
    op.create_index('ix_policies_active', 'policies', ['is_active'], schema='policy')
    op.create_index('ix_policies_priority', 'policies', ['priority'], schema='policy')

    # ==========================================================================
    # Policy Evaluations (Audit Log)
    # ==========================================================================
    op.create_table(
        'evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_name', sa.String(128), nullable=True),

        # What was evaluated
        sa.Column('action_type', sa.String(50), nullable=False),  # route, execute, adapt, escalate, etc.
        sa.Column('agent_id', sa.String(128), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),
        sa.Column('request_context', postgresql.JSONB, nullable=False, server_default='{}'),

        # Decision
        sa.Column('decision', sa.String(20), nullable=False),  # ALLOW, BLOCK, MODIFY
        sa.Column('decision_reason', sa.Text, nullable=True),
        sa.Column('modifications', postgresql.JSONB, nullable=True),  # if MODIFY, what changed

        # Evaluation metadata
        sa.Column('evaluation_ms', sa.Float, nullable=True),
        sa.Column('policies_checked', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rules_matched', postgresql.ARRAY(sa.String), nullable=True),

        # Timestamp
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    # Evaluation indexes
    op.create_index('ix_evaluations_agent_id', 'evaluations', ['agent_id'], schema='policy')
    op.create_index('ix_evaluations_tenant_id', 'evaluations', ['tenant_id'], schema='policy')
    op.create_index('ix_evaluations_decision', 'evaluations', ['decision'], schema='policy')
    op.create_index('ix_evaluations_action_type', 'evaluations', ['action_type'], schema='policy')
    op.create_index('ix_evaluations_evaluated_at', 'evaluations', ['evaluated_at'], schema='policy')

    # Partition evaluations by month for performance
    # (Keeping as single table for now, can partition later)

    # ==========================================================================
    # Policy Violations
    # ==========================================================================
    op.create_table(
        'violations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('evaluation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_name', sa.String(128), nullable=True),

        # Violation details
        sa.Column('violation_type', sa.String(50), nullable=False),  # compliance, ethical, risk, safety, business
        sa.Column('severity', sa.Float, nullable=False, server_default='0.5'),  # 0.0-1.0
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('evidence', postgresql.JSONB, nullable=False, server_default='{}'),

        # What caused it
        sa.Column('agent_id', sa.String(128), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),
        sa.Column('action_attempted', sa.String(100), nullable=True),
        sa.Column('request_context', postgresql.JSONB, nullable=True),

        # Routing to Governor
        sa.Column('routed_to_governor', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('governor_action', sa.String(50), nullable=True),  # freeze, rollback, quarantine
        sa.Column('governor_action_at', sa.DateTime(timezone=True), nullable=True),

        # Resolution
        sa.Column('resolved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('resolved_by', sa.String(128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),

        # Acknowledgement (for review)
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(128), nullable=True),
        sa.Column('acknowledgement_notes', sa.Text, nullable=True),

        # Timestamps
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    # Violation indexes
    op.create_index('ix_violations_agent_id', 'violations', ['agent_id'], schema='policy')
    op.create_index('ix_violations_tenant_id', 'violations', ['tenant_id'], schema='policy')
    op.create_index('ix_violations_violation_type', 'violations', ['violation_type'], schema='policy')
    op.create_index('ix_violations_severity', 'violations', ['severity'], schema='policy')
    op.create_index('ix_violations_resolved', 'violations', ['resolved'], schema='policy')
    op.create_index('ix_violations_detected_at', 'violations', ['detected_at'], schema='policy')

    # ==========================================================================
    # Risk Ceilings
    # ==========================================================================
    op.create_table(
        'risk_ceilings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),

        # Ceiling definition
        sa.Column('metric', sa.String(100), nullable=False),  # cost_per_hour, retries_per_minute, etc.
        sa.Column('max_value', sa.Float, nullable=False),
        sa.Column('current_value', sa.Float, nullable=False, server_default='0'),
        sa.Column('window_seconds', sa.Integer, nullable=False, server_default='3600'),

        # Applicability
        sa.Column('applies_to', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),

        # Breach actions
        sa.Column('breach_action', sa.String(50), nullable=False, server_default="'block'"),  # block, throttle, alert
        sa.Column('breach_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_breach_at', sa.DateTime(timezone=True), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_risk_ceilings_metric', 'risk_ceilings', ['metric'], schema='policy')
    op.create_index('ix_risk_ceilings_tenant_id', 'risk_ceilings', ['tenant_id'], schema='policy')

    # ==========================================================================
    # Safety Rules (Hard Stops)
    # ==========================================================================
    op.create_table(
        'safety_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),

        # Rule definition
        sa.Column('rule_type', sa.String(50), nullable=False),  # action_block, pattern_block, escalation_required, hard_stop, cooldown
        sa.Column('condition', postgresql.JSONB, nullable=False),  # condition expression
        sa.Column('action', sa.String(50), nullable=False),  # block, escalate, alert, cooldown

        # Cooldown settings (if action=cooldown)
        sa.Column('cooldown_seconds', sa.Integer, nullable=True),

        # Applicability
        sa.Column('applies_to', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('tenant_id', sa.String(128), nullable=True),
        sa.Column('priority', sa.Integer, nullable=False, server_default='100'),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('triggered_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_safety_rules_rule_type', 'safety_rules', ['rule_type'], schema='policy')
    op.create_index('ix_safety_rules_tenant_id', 'safety_rules', ['tenant_id'], schema='policy')
    op.create_index('ix_safety_rules_priority', 'safety_rules', ['priority'], schema='policy')

    # ==========================================================================
    # Business Rules
    # ==========================================================================
    op.create_table(
        'business_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),

        # Rule definition
        sa.Column('rule_type', sa.String(50), nullable=False),  # pricing, tier_access, sla, budget, feature_gate
        sa.Column('condition', postgresql.JSONB, nullable=False),
        sa.Column('constraint', postgresql.JSONB, nullable=False),

        # Applicability
        sa.Column('tenant_id', sa.String(128), nullable=True),
        sa.Column('customer_tier', sa.String(50), nullable=True),  # free, pro, enterprise
        sa.Column('priority', sa.Integer, nullable=False, server_default='100'),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_business_rules_rule_type', 'business_rules', ['rule_type'], schema='policy')
    op.create_index('ix_business_rules_tenant_id', 'business_rules', ['tenant_id'], schema='policy')
    op.create_index('ix_business_rules_customer_tier', 'business_rules', ['customer_tier'], schema='policy')

    # ==========================================================================
    # Ethical Constraints (Codified Non-Negotiables)
    # ==========================================================================
    op.create_table(
        'ethical_constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=False),

        # Constraint definition
        sa.Column('constraint_type', sa.String(50), nullable=False),  # no_coercion, no_fabrication, no_manipulation, transparency
        sa.Column('forbidden_patterns', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('required_disclosures', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('transparency_threshold', sa.Float, nullable=True),  # 0.0-1.0, decisions must be explainable above this

        # Enforcement
        sa.Column('enforcement_level', sa.String(20), nullable=False, server_default="'strict'"),  # strict, warn, audit
        sa.Column('violation_action', sa.String(50), nullable=False, server_default="'block'"),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('violated_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_violated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),

        schema='policy'
    )

    op.create_index('ix_ethical_constraints_type', 'ethical_constraints', ['constraint_type'], schema='policy')

    # ==========================================================================
    # Insert Default Policies
    # ==========================================================================

    # Default ethical constraints
    op.execute("""
        INSERT INTO policy.ethical_constraints (name, description, constraint_type, forbidden_patterns, enforcement_level, violation_action)
        VALUES
        ('no_coercion', 'Agents must never use coercive tactics', 'no_coercion',
         ARRAY['threaten', 'force', 'blackmail', 'manipulate_emotion'], 'strict', 'block'),
        ('no_fabrication', 'Agents must never fabricate evidence or data', 'no_fabrication',
         ARRAY['fake_data', 'false_citation', 'invented_source'], 'strict', 'block'),
        ('no_manipulation', 'Agents must not strategically manipulate outcomes', 'no_manipulation',
         ARRAY['game_metrics', 'exploit_loophole', 'circumvent_control'], 'strict', 'block'),
        ('transparency', 'Decisions must be explainable', 'transparency',
         NULL, 'strict', 'block')
    """)

    # Default risk ceilings
    op.execute("""
        INSERT INTO policy.risk_ceilings (name, description, metric, max_value, window_seconds, breach_action)
        VALUES
        ('hourly_cost_ceiling', 'Maximum cost per hour across all agents', 'cost_per_hour', 100.0, 3600, 'throttle'),
        ('retry_rate_ceiling', 'Maximum retries per minute per agent', 'retries_per_minute', 30, 60, 'block'),
        ('cascade_depth_ceiling', 'Maximum depth of multi-agent cascades', 'cascade_depth', 5, 0, 'block'),
        ('concurrent_agents_ceiling', 'Maximum concurrent agents per tenant', 'concurrent_agents', 50, 0, 'throttle')
    """)

    # Default safety rules
    op.execute("""
        INSERT INTO policy.safety_rules (name, description, rule_type, condition, action, priority)
        VALUES
        ('block_system_commands', 'Block dangerous system commands', 'action_block',
         '{"actions": ["rm -rf", "shutdown", "format", "drop database"]}', 'block', 1),
        ('escalate_high_cost', 'Require human approval for high-cost operations', 'escalation_required',
         '{"cost_threshold": 50.0}', 'escalate', 10),
        ('cooldown_on_failure_spike', 'Enforce cooldown after failure spike', 'cooldown',
         '{"failure_count": 5, "window_seconds": 60}', 'cooldown', 20),
        ('block_external_pii', 'Block transmission of PII to external services', 'pattern_block',
         '{"patterns": ["ssn", "credit_card", "password"]}', 'block', 1)
    """)


def downgrade() -> None:
    # Drop all tables
    op.drop_table('ethical_constraints', schema='policy')
    op.drop_table('business_rules', schema='policy')
    op.drop_table('safety_rules', schema='policy')
    op.drop_table('risk_ceilings', schema='policy')
    op.drop_table('violations', schema='policy')
    op.drop_table('evaluations', schema='policy')
    op.drop_table('policies', schema='policy')

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS policy CASCADE")
