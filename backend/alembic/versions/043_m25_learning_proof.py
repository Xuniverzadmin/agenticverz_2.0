"""M25: Learning Proof Tables

Revision ID: 043_m25_learning
Revises: 042_m25_integration
Create Date: 2025-12-23

Adds tables for proving that M25 actually LEARNS:
- prevention_records: Track when policies prevent incidents (Gate 1)
- regret_events: Track when policies cause harm (Gate 2)
- pattern_calibrations: Adaptive confidence thresholds
- checkpoint_configs: Per-tenant checkpoint configuration
- graduation_checkpoints: M25 graduation gate tracking
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "043_m25_learning"
down_revision = "042_m25_integration"
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # PREVENTION RECORDS - Gate 1: Proof that policies prevent incidents
    # =========================================================================
    op.create_table(
        "prevention_records",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("pattern_id", sa.String(64), nullable=False),
        sa.Column("original_incident_id", sa.String(64), nullable=False),
        sa.Column("blocked_incident_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),  # prevented/mitigated/failed
        sa.Column("signature_match_confidence", sa.Float, nullable=False),
        sa.Column("policy_age_seconds", sa.Integer),  # Time policy was active
        sa.Column("calls_evaluated", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_prevention_policy", "prevention_records", ["policy_id"])
    op.create_index("idx_prevention_pattern", "prevention_records", ["pattern_id"])
    op.create_index("idx_prevention_tenant", "prevention_records", ["tenant_id", "created_at"])

    # =========================================================================
    # REGRET EVENTS - Gate 2: Track when policies cause harm
    # =========================================================================
    op.create_table(
        "regret_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("regret_type", sa.String(32), nullable=False),  # false_positive/perf/escalation/cascade
        sa.Column("description", sa.Text),
        sa.Column("severity", sa.Integer, nullable=False),  # 1-10
        sa.Column("affected_calls", sa.Integer, server_default="0"),
        sa.Column("affected_users", sa.Integer, server_default="0"),
        sa.Column("impact_duration_seconds", sa.Integer),
        sa.Column("was_auto_rolled_back", sa.Boolean, server_default="false"),
        sa.Column("manual_override_by", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_regret_policy", "regret_events", ["policy_id", "created_at"])
    op.create_index("idx_regret_tenant", "regret_events", ["tenant_id", "created_at"])

    # =========================================================================
    # POLICY REGRET SUMMARY - Aggregated regret per policy
    # =========================================================================
    op.create_table(
        "policy_regret_summary",
        sa.Column("policy_id", sa.String(64), primary_key=True),
        sa.Column("regret_score", sa.Float, server_default="0"),
        sa.Column("regret_event_count", sa.Integer, server_default="0"),
        sa.Column("demoted_at", sa.DateTime(timezone=True)),
        sa.Column("demoted_reason", sa.Text),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # =========================================================================
    # PATTERN CALIBRATIONS - Adaptive confidence thresholds
    # =========================================================================
    op.create_table(
        "pattern_calibrations",
        sa.Column("pattern_id", sa.String(64), primary_key=True),
        sa.Column("total_matches", sa.Integer, server_default="0"),
        sa.Column("correct_matches", sa.Integer, server_default="0"),
        sa.Column("false_positives", sa.Integer, server_default="0"),
        sa.Column("false_negatives", sa.Integer, server_default="0"),
        sa.Column("empirical_strong_threshold", sa.Float, server_default="0.85"),
        sa.Column("empirical_weak_threshold", sa.Float, server_default="0.60"),
        sa.Column("predictions", JSONB, server_default="[]"),  # [(confidence, was_correct), ...]
        sa.Column("last_calibrated_at", sa.DateTime(timezone=True)),
        sa.Column("is_calibrated", sa.Boolean, server_default="false"),
    )

    # =========================================================================
    # CHECKPOINT CONFIGS - Per-tenant checkpoint configuration
    # =========================================================================
    op.create_table(
        "checkpoint_configs",
        sa.Column("tenant_id", sa.String(64), primary_key=True),
        sa.Column(
            "enabled_types",
            JSONB,
            server_default='["approve_policy", "approve_recovery", "simulate_routing", "revert_loop", "override_guardrail"]',
        ),
        sa.Column("priority_overrides", JSONB, server_default="{}"),
        sa.Column("blocking_checkpoints", JSONB, server_default='["approve_policy", "override_guardrail"]'),
        sa.Column("auto_approve_confidence", sa.Float, server_default="0.95"),
        sa.Column("auto_dismiss_after_hours", sa.Integer, server_default="48"),
        sa.Column("max_pending_checkpoints", sa.Integer, server_default="10"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # =========================================================================
    # GRADUATION GATES - M25 graduation tracking
    # =========================================================================
    op.create_table(
        "m25_graduation_status",
        sa.Column("id", sa.Integer, primary_key=True),  # Singleton row
        sa.Column("gate1_passed", sa.Boolean, server_default="false"),
        sa.Column("gate1_passed_at", sa.DateTime(timezone=True)),
        sa.Column("gate1_evidence", JSONB),
        sa.Column("gate2_passed", sa.Boolean, server_default="false"),
        sa.Column("gate2_passed_at", sa.DateTime(timezone=True)),
        sa.Column("gate2_evidence", JSONB),
        sa.Column("gate3_passed", sa.Boolean, server_default="false"),
        sa.Column("gate3_passed_at", sa.DateTime(timezone=True)),
        sa.Column("gate3_evidence", JSONB),
        sa.Column("is_graduated", sa.Boolean, server_default="false"),
        sa.Column("graduated_at", sa.DateTime(timezone=True)),
        sa.Column("status_label", sa.String(64), server_default="'M25-ALPHA (0/3 gates)'"),
        sa.Column("last_checked", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Insert singleton row
    op.execute(
        """
        INSERT INTO m25_graduation_status (id, status_label)
        VALUES (1, 'M25-ALPHA (0/3 gates)')
        ON CONFLICT (id) DO NOTHING
    """
    )

    # =========================================================================
    # ADD COLUMNS TO EXISTING TABLES (with IF NOT EXISTS for schema drift)
    # =========================================================================

    # Add prevention tracking to policies
    op.execute(
        """
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS prevention_count INTEGER DEFAULT 0;
        ALTER TABLE policy_rules ADD COLUMN IF NOT EXISTS last_prevention_at TIMESTAMP WITH TIME ZONE;
    """
    )

    # Add calibration reference to incidents
    op.execute(
        """
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS prediction_was_correct BOOLEAN;
        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS calibration_recorded BOOLEAN DEFAULT false;
    """
    )

    # Add priority to human_checkpoints
    op.execute(
        """
        ALTER TABLE human_checkpoints ADD COLUMN IF NOT EXISTS priority VARCHAR(32) DEFAULT 'normal';
        ALTER TABLE human_checkpoints ADD COLUMN IF NOT EXISTS is_blocking BOOLEAN DEFAULT true;
        ALTER TABLE human_checkpoints ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;
        ALTER TABLE human_checkpoints ADD COLUMN IF NOT EXISTS auto_dismissed BOOLEAN DEFAULT false;
    """
    )


def downgrade():
    # Remove columns (with IF EXISTS for safety)
    op.execute(
        """
        ALTER TABLE human_checkpoints DROP COLUMN IF EXISTS auto_dismissed;
        ALTER TABLE human_checkpoints DROP COLUMN IF EXISTS expires_at;
        ALTER TABLE human_checkpoints DROP COLUMN IF EXISTS is_blocking;
        ALTER TABLE human_checkpoints DROP COLUMN IF EXISTS priority;
        ALTER TABLE incidents DROP COLUMN IF EXISTS calibration_recorded;
        ALTER TABLE incidents DROP COLUMN IF EXISTS prediction_was_correct;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS last_prevention_at;
        ALTER TABLE policy_rules DROP COLUMN IF EXISTS prevention_count;
    """
    )

    # Drop tables
    op.execute("DROP TABLE IF EXISTS m25_graduation_status")
    op.execute("DROP TABLE IF EXISTS checkpoint_configs")
    op.execute("DROP TABLE IF EXISTS pattern_calibrations")
    op.execute("DROP TABLE IF EXISTS policy_regret_summary")
    op.execute("DROP TABLE IF EXISTS regret_events")
    op.execute("DROP TABLE IF EXISTS prevention_records")
