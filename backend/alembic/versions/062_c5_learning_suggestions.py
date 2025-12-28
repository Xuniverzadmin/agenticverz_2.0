"""C5 Learning Suggestions Table.

Revision ID: 062_c5_learning_suggestions
Revises: 061_c2_prediction_hardening
Create Date: 2025-12-28

This migration creates the learning_suggestions table for C5 Learning.

IMMUTABILITY RULES (CI-C5-4, AC-S1-M1):
- Core fields (observation, suggestion_text, suggestion_confidence)
  CANNOT be updated after creation.
- Trigger enforces immutability.
- Only status-related fields can change.

Reference: C5_S1_LEARNING_SCENARIO.md, C5_S1_ACCEPTANCE_CRITERIA.md
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "062_c5_learning_suggestions"
down_revision = "061_c2_prediction_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create learning_suggestions table
    op.create_table(
        "learning_suggestions",
        # Identity
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        # Scenario identification
        sa.Column("scenario", sa.String(50), nullable=False),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # Observation window
        sa.Column("observation_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observation_window_end", sa.DateTime(timezone=True), nullable=False),
        # Observation data (IMMUTABLE - enforced by trigger)
        sa.Column("observation", postgresql.JSONB, nullable=False),
        # Suggestion details (IMMUTABLE - enforced by trigger)
        sa.Column("suggestion_type", sa.String(20), nullable=False, default="advisory"),
        sa.Column("suggestion_confidence", sa.String(10), nullable=False),
        sa.Column("suggestion_text", sa.Text(), nullable=False),
        # Status (MUTABLE via human action only)
        sa.Column("status", sa.String(30), nullable=False, default="pending_review"),
        # Human action tracking (MUTABLE)
        sa.Column("human_action", sa.String(30), nullable=True),
        sa.Column("human_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("human_actor_id", sa.String(100), nullable=True),
        # Applied flag (MUTABLE via human action only)
        sa.Column("applied", sa.Boolean(), nullable=False, default=False),
        # Constraints
        sa.CheckConstraint(
            "status IN ('pending_review', 'acknowledged', 'dismissed', 'applied_externally')",
            name="learning_suggestions_status_valid",
        ),
        sa.CheckConstraint(
            "suggestion_confidence IN ('low', 'medium', 'high')", name="learning_suggestions_confidence_valid"
        ),
        sa.CheckConstraint("suggestion_type = 'advisory'", name="learning_suggestions_type_advisory"),
    )

    # Create indexes for common queries
    op.create_index("ix_learning_suggestions_scenario", "learning_suggestions", ["scenario"])
    op.create_index("ix_learning_suggestions_status", "learning_suggestions", ["status"])
    op.create_index("ix_learning_suggestions_created_at", "learning_suggestions", ["created_at"])

    # Create immutability trigger function
    # This prevents modification of core fields after creation
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_suggestion_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Check if immutable fields are being modified
            IF OLD.observation IS DISTINCT FROM NEW.observation OR
               OLD.suggestion_text IS DISTINCT FROM NEW.suggestion_text OR
               OLD.suggestion_confidence IS DISTINCT FROM NEW.suggestion_confidence OR
               OLD.suggestion_type IS DISTINCT FROM NEW.suggestion_type OR
               OLD.observation_window_start IS DISTINCT FROM NEW.observation_window_start OR
               OLD.observation_window_end IS DISTINCT FROM NEW.observation_window_end THEN
                RAISE EXCEPTION 'Learning suggestions are immutable. Core fields cannot be modified after creation.';
            END IF;

            -- Allow status-related changes only
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Attach trigger to table
    op.execute(
        """
        CREATE TRIGGER learning_suggestion_immutable
            BEFORE UPDATE ON learning_suggestions
            FOR EACH ROW
            EXECUTE FUNCTION prevent_suggestion_mutation();
    """
    )

    # Add comment explaining the table
    op.execute(
        """
        COMMENT ON TABLE learning_suggestions IS
        'C5 Learning Suggestions - Advisory only. Core fields are immutable after creation.
         Reference: C5_S1_LEARNING_SCENARIO.md, CI-C5-4';
    """
    )


def downgrade() -> None:
    # Drop trigger first
    op.execute("DROP TRIGGER IF EXISTS learning_suggestion_immutable ON learning_suggestions")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS prevent_suggestion_mutation()")

    # Drop indexes
    op.drop_index("ix_learning_suggestions_created_at", "learning_suggestions")
    op.drop_index("ix_learning_suggestions_status", "learning_suggestions")
    op.drop_index("ix_learning_suggestions_scenario", "learning_suggestions")

    # Drop table
    op.drop_table("learning_suggestions")
