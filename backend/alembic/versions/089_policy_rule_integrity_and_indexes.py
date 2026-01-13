"""policy rule integrity + governance indexes

Revision ID: 089_policy_rule_integrity
Revises: 088_policy_control_plane
Create Date: 2026-01-13

PIN-412: Adds policy_rule_integrity table and missing governance indexes.
Enforces invariant: every ACTIVE policy_rule must have exactly one integrity row.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "089_policy_rule_integrity"
down_revision = "088_policy_control_plane"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1 — Create policy_rule_integrity table
    # =========================================================================
    # Note: rule_id is VARCHAR to match policy_rules.id schema
    op.create_table(
        "policy_rule_integrity",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "rule_id",
            sa.String(),
            sa.ForeignKey("policy_rules.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,  # exactly one integrity row per rule
        ),
        sa.Column(
            "integrity_status",
            sa.String(16),
            nullable=False,
        ),
        sa.Column(
            "integrity_score",
            sa.Numeric(4, 3),
            nullable=False,
        ),
        sa.Column(
            "hash_root",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Check constraint for integrity_status values
        sa.CheckConstraint(
            "integrity_status IN ('VERIFIED', 'DEGRADED', 'FAILED')",
            name="ck_policy_rule_integrity_status",
        ),
    )

    # =========================================================================
    # STEP 2 — Indexes for policy_rule_integrity
    # =========================================================================
    op.create_index(
        "idx_policy_rule_integrity_status",
        "policy_rule_integrity",
        ["integrity_status"],
    )

    op.create_index(
        "idx_policy_rule_integrity_computed_at",
        "policy_rule_integrity",
        ["computed_at"],
    )

    # =========================================================================
    # STEP 3 — Missing index: policy_rules(source)
    # =========================================================================
    op.create_index(
        "idx_policy_rules_source",
        "policy_rules",
        ["source"],
    )

    # =========================================================================
    # STEP 4 — Missing compound index: policy_enforcements(rule_id, triggered_at)
    # Note: Column is triggered_at, not created_at per actual schema
    # =========================================================================
    op.create_index(
        "idx_policy_enforcements_rule_triggered",
        "policy_enforcements",
        ["rule_id", "triggered_at"],
    )

    # =========================================================================
    # STEP 5 — Invariant Enforcement Trigger
    # Invariant: Every ACTIVE policy_rule must have exactly one integrity row
    # =========================================================================

    # Trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_policy_rule_integrity()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.status = 'ACTIVE' THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM policy_rule_integrity pri
                    WHERE pri.rule_id = NEW.id
                ) THEN
                    RAISE EXCEPTION
                        'ACTIVE policy_rule % must have integrity row',
                        NEW.id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Attach trigger
    op.execute(
        """
        CREATE TRIGGER trg_policy_rule_integrity_required
        AFTER INSERT OR UPDATE OF status
        ON policy_rules
        FOR EACH ROW
        EXECUTE FUNCTION enforce_policy_rule_integrity();
        """
    )


def downgrade() -> None:
    # =========================================================================
    # STEP 1 — Drop trigger + function
    # =========================================================================
    op.execute(
        "DROP TRIGGER IF EXISTS trg_policy_rule_integrity_required ON policy_rules;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS enforce_policy_rule_integrity;"
    )

    # =========================================================================
    # STEP 2 — Drop indexes
    # =========================================================================
    op.drop_index(
        "idx_policy_enforcements_rule_triggered",
        table_name="policy_enforcements",
    )

    op.drop_index(
        "idx_policy_rules_source",
        table_name="policy_rules",
    )

    op.drop_index(
        "idx_policy_rule_integrity_computed_at",
        table_name="policy_rule_integrity",
    )

    op.drop_index(
        "idx_policy_rule_integrity_status",
        table_name="policy_rule_integrity",
    )

    # =========================================================================
    # STEP 3 — Drop table
    # =========================================================================
    op.drop_table("policy_rule_integrity")
