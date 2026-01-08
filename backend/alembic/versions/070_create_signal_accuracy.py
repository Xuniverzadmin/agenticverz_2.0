# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create Signal Accuracy tables per PIN-343
# Reference: PIN-343, PIN-344, PIN-345

"""Create Signal Accuracy and Confidence Audit tables

Revision ID: 070_create_signal_accuracy
Revises: 069_create_gcl_audit_log
Create Date: 2026-01-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "070_create_signal_accuracy"
down_revision = "069_create_gcl_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create Signal Accuracy tables per PIN-343 Section 2.8:
    - signal_accuracy: Track historical accuracy per signal type per tenant
    - confidence_audit_log: Audit trail for confidence updates
    """

    # =========================================================================
    # Table: signal_accuracy
    # Purpose: Track historical accuracy of each signal type per tenant
    # Reference: PIN-343 Section 2.4, 2.8
    # Formula: calibrated_confidence = raw × historical_accuracy × temporal_decay
    # =========================================================================
    op.create_table(
        "signal_accuracy",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", sa.Text(), nullable=False),
        sa.Column("total_outcomes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "accuracy", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.5"
        ),  # Default 50% accuracy
        sa.Column("last_updated", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        # Extended fields for decay configuration per PIN-343 Section 2.5
        sa.Column("decay_lambda", sa.Numeric(precision=5, scale=4), nullable=False, server_default="0.1"),  # Default λ
        sa.Column(
            "suppression_threshold", sa.Numeric(precision=3, scale=2), nullable=False, server_default="0.2"
        ),  # Below this, suppress signal
        # Primary key
        sa.PrimaryKeyConstraint("tenant_id", "signal_type"),
        # Constraints
        sa.CheckConstraint("accuracy >= 0.0 AND accuracy <= 1.0", name="ck_signal_accuracy_range"),
        sa.CheckConstraint("decay_lambda >= 0.0", name="ck_signal_decay_positive"),
        sa.CheckConstraint(
            "suppression_threshold >= 0.0 AND suppression_threshold <= 1.0", name="ck_signal_suppression_range"
        ),
    )

    # Indexes
    op.create_index("idx_signal_accuracy_tenant", "signal_accuracy", ["tenant_id"])
    op.create_index("idx_signal_accuracy_type", "signal_accuracy", ["signal_type"])

    # =========================================================================
    # Table: confidence_audit_log
    # Purpose: Audit trail for all confidence updates (no silent tuning)
    # Reference: PIN-343 Section 2.7
    # =========================================================================
    op.create_table(
        "confidence_audit_log",
        sa.Column(
            "event_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("signal_id", sa.Text(), nullable=False),  # Instance of signal
        sa.Column("signal_type", sa.Text(), nullable=False),  # Signal catalog type
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("new_confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("components", postgresql.JSONB(), nullable=False),
        # {raw: 0.85, historical_accuracy: 0.72, temporal_decay: 0.90}
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        # Primary key
        sa.PrimaryKeyConstraint("event_id"),
    )

    # Indexes
    op.create_index("idx_confidence_audit_tenant", "confidence_audit_log", ["tenant_id", "timestamp"])
    op.create_index("idx_confidence_audit_signal", "confidence_audit_log", ["signal_type", "timestamp"])

    # =========================================================================
    # Immutability for confidence audit log
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_confidence_audit_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'CONFIDENCE-IMMUTABLE-001: Confidence audit log is immutable - no UPDATE or DELETE allowed. Reference: PIN-343 Section 2.7';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER confidence_audit_immutable_update
        BEFORE UPDATE ON confidence_audit_log
        FOR EACH ROW EXECUTE FUNCTION prevent_confidence_audit_mutation();
    """)

    op.execute("""
        CREATE TRIGGER confidence_audit_immutable_delete
        BEFORE DELETE ON confidence_audit_log
        FOR EACH ROW EXECUTE FUNCTION prevent_confidence_audit_mutation();
    """)

    # =========================================================================
    # Insert default accuracy records for core signals (per PIN-341 catalog)
    # =========================================================================
    op.execute("""
        -- This function can be called to initialize signal accuracy for a new tenant
        CREATE OR REPLACE FUNCTION initialize_tenant_signal_accuracy(p_tenant_id UUID)
        RETURNS void AS $$
        DECLARE
            signal_types TEXT[] := ARRAY[
                -- Execution signals (PIN-341 Section 2.2.A)
                'EXEC_ERROR_RATE_SPIKE',
                'EXEC_TIMEOUT_SURGE',
                'EXEC_RETRY_STORM',
                'EXEC_FAILURE_CLUSTER',
                'EXEC_LATENCY_DEGRADATION',
                'EXEC_THROUGHPUT_DROP',
                -- Cost signals (PIN-341 Section 2.2.B)
                'COST_RATE_SPIKE',
                'COST_BUDGET_RISK',
                'COST_BUDGET_BREACH',
                'UTIL_IDLE_WASTE',
                'UTIL_OVERCOMMIT',
                'UTIL_QUOTA_PRESSURE',
                -- Policy signals (PIN-341 Section 2.2.C)
                'POLICY_FREQUENT_WARN',
                'POLICY_BLOCK_RATE',
                'POLICY_CONFLICT',
                'POLICY_DORMANT',
                'POLICY_CASCADE',
                -- Integration signals (PIN-341 Section 2.2.D)
                'INTEG_FAILURE_LOOP',
                'INTEG_LATENCY_DRIFT',
                'INTEG_AUTH_ERROR',
                'INTEG_TIMEOUT_PATTERN',
                'INTEG_RATE_LIMIT_HIT',
                -- Safety signals (PIN-341 Section 2.2.E)
                'SAFETY_ANOMALOUS_BEHAVIOR',
                'SAFETY_THRESHOLD_BREACH',
                'SAFETY_KILLSWITCH_RECOMMENDED',
                'SAFETY_DRIFT_DETECTED'
            ];
            sig_type TEXT;
        BEGIN
            FOREACH sig_type IN ARRAY signal_types LOOP
                INSERT INTO signal_accuracy (tenant_id, signal_type, total_outcomes, accuracy)
                VALUES (p_tenant_id, sig_type, 0, 0.5)
                ON CONFLICT (tenant_id, signal_type) DO NOTHING;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Remove Signal Accuracy tables"""

    # Drop initialization function
    op.execute("DROP FUNCTION IF EXISTS initialize_tenant_signal_accuracy(UUID);")

    # Drop triggers and function
    op.execute("DROP TRIGGER IF EXISTS confidence_audit_immutable_delete ON confidence_audit_log;")
    op.execute("DROP TRIGGER IF EXISTS confidence_audit_immutable_update ON confidence_audit_log;")
    op.execute("DROP FUNCTION IF EXISTS prevent_confidence_audit_mutation();")

    # Drop indexes
    op.drop_index("idx_confidence_audit_signal", "confidence_audit_log")
    op.drop_index("idx_confidence_audit_tenant", "confidence_audit_log")

    op.drop_index("idx_signal_accuracy_type", "signal_accuracy")
    op.drop_index("idx_signal_accuracy_tenant", "signal_accuracy")

    # Drop tables
    op.drop_table("confidence_audit_log")
    op.drop_table("signal_accuracy")
