# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create Signal Feedback table per PIN-344
# Reference: PIN-344 Section 2.5, PIN-345

"""Create Signal Feedback table

Revision ID: 071_create_signal_feedback
Revises: 070_create_signal_accuracy
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '071_create_signal_feedback'
down_revision = '070_create_signal_accuracy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create Signal Feedback table per PIN-344 Section 2.5:
    - Track human feedback on signal usefulness
    - Allowed inputs: USEFUL, NOT_USEFUL, IGNORED
    - One feedback per signal per actor per window
    """

    # =========================================================================
    # Table: signal_feedback
    # Purpose: Collect human feedback on signal usefulness
    # Reference: PIN-344 Section 2.5
    # Allowed feedback: USEFUL | NOT_USEFUL | IGNORED
    # =========================================================================
    op.create_table(
        'signal_feedback',
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('signal_id', sa.Text(), nullable=False),  # Instance of signal
        sa.Column('signal_type', sa.Text(), nullable=False),  # Signal catalog type
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False),  # USEFUL | NOT_USEFUL | IGNORED
        sa.Column('action_taken', sa.Text(), nullable=True),  # KILLSWITCH | POLICY_ACTIVATE | DISMISS | NONE
        sa.Column('time_to_decision_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('NOW()')),

        # Primary key
        sa.PrimaryKeyConstraint('feedback_id'),

        # Constraints per PIN-344 Section 2.5
        sa.CheckConstraint(
            "feedback IN ('USEFUL', 'NOT_USEFUL', 'IGNORED')",
            name='ck_signal_feedback_valid_feedback'
        ),

        # One feedback per signal per actor per recommendation (PIN-344 2.5)
        sa.UniqueConstraint('signal_id', 'recommendation_id', 'actor_id',
                            name='uq_signal_feedback_one_per_actor'),
    )

    # Indexes per PIN-344 Section 2.5
    op.create_index('idx_signal_feedback_tenant', 'signal_feedback',
                    ['tenant_id', 'created_at'])
    op.create_index('idx_signal_feedback_signal', 'signal_feedback',
                    ['signal_type'])
    op.create_index('idx_signal_feedback_actor', 'signal_feedback',
                    ['actor_id', 'created_at'])
    op.create_index('idx_signal_feedback_useful', 'signal_feedback',
                    ['tenant_id', 'signal_type', 'feedback'],
                    postgresql_where=sa.text("feedback = 'USEFUL'"))

    # =========================================================================
    # Trigger: Update signal_accuracy when feedback is received
    # Reference: PIN-344 Section 2.6 - Feedback updates confidence only
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION update_signal_accuracy_on_feedback()
        RETURNS TRIGGER AS $$
        DECLARE
            v_outcome_score NUMERIC;
            v_current_accuracy NUMERIC;
            v_current_outcomes INTEGER;
        BEGIN
            -- Only USEFUL and NOT_USEFUL update accuracy (PIN-344 Section 2.3)
            -- IGNORED is neutral and does not affect accuracy
            IF NEW.feedback = 'IGNORED' THEN
                RETURN NEW;
            END IF;

            -- Determine outcome score (PIN-343 Section 2.4)
            IF NEW.feedback = 'USEFUL' THEN
                v_outcome_score := 1.0;
            ELSE
                v_outcome_score := 0.0;
            END IF;

            -- Get current accuracy values
            SELECT accuracy, total_outcomes
            INTO v_current_accuracy, v_current_outcomes
            FROM signal_accuracy
            WHERE tenant_id = NEW.tenant_id
              AND signal_type = NEW.signal_type;

            -- If no record exists, create one with default values
            IF NOT FOUND THEN
                INSERT INTO signal_accuracy (tenant_id, signal_type, total_outcomes, accuracy)
                VALUES (NEW.tenant_id, NEW.signal_type, 1, v_outcome_score);
            ELSE
                -- Update accuracy using formula from PIN-343 Section 2.4:
                -- accuracy_new = (accuracy_old × N + outcome_score) / (N + 1)
                UPDATE signal_accuracy
                SET accuracy = (v_current_accuracy * v_current_outcomes + v_outcome_score) / (v_current_outcomes + 1),
                    total_outcomes = v_current_outcomes + 1,
                    last_updated = NOW()
                WHERE tenant_id = NEW.tenant_id
                  AND signal_type = NEW.signal_type;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER signal_feedback_update_accuracy
        AFTER INSERT ON signal_feedback
        FOR EACH ROW EXECUTE FUNCTION update_signal_accuracy_on_feedback();
    """)

    # =========================================================================
    # Table: signal_recommendations
    # Purpose: Track FACILITATION recommendations shown to users
    # Reference: PIN-344 Section 2.2
    # =========================================================================
    op.create_table(
        'signal_recommendations',
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('signal_id', sa.Text(), nullable=False),
        sa.Column('signal_type', sa.Text(), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('suggested_action', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('severity', sa.Text(), nullable=False),  # LOW | MEDIUM | HIGH | CRITICAL
        sa.Column('shown_to', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False,
                  server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),

        # Primary key
        sa.PrimaryKeyConstraint('recommendation_id'),

        # Constraints
        sa.CheckConstraint(
            "severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name='ck_recommendation_valid_severity'
        ),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name='ck_recommendation_confidence_range'
        ),
    )

    # Indexes
    op.create_index('idx_recommendations_tenant', 'signal_recommendations',
                    ['tenant_id', 'created_at'])
    op.create_index('idx_recommendations_signal', 'signal_recommendations',
                    ['signal_type', 'created_at'])
    # Note: Cannot use NOW() in partial index as it's not IMMUTABLE
    # Query active recommendations with: WHERE expires_at IS NULL OR expires_at > NOW()
    op.create_index('idx_recommendations_expires', 'signal_recommendations',
                    ['tenant_id', 'expires_at'])


def downgrade() -> None:
    """Remove Signal Feedback tables"""

    # Drop indexes
    op.drop_index('idx_recommendations_expires', 'signal_recommendations')
    op.drop_index('idx_recommendations_signal', 'signal_recommendations')
    op.drop_index('idx_recommendations_tenant', 'signal_recommendations')

    # Drop recommendations table
    op.drop_table('signal_recommendations')

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS signal_feedback_update_accuracy ON signal_feedback;")
    op.execute("DROP FUNCTION IF EXISTS update_signal_accuracy_on_feedback();")

    # Drop indexes
    op.drop_index('idx_signal_feedback_useful', 'signal_feedback')
    op.drop_index('idx_signal_feedback_actor', 'signal_feedback')
    op.drop_index('idx_signal_feedback_signal', 'signal_feedback')
    op.drop_index('idx_signal_feedback_tenant', 'signal_feedback')

    # Drop table
    op.drop_table('signal_feedback')
