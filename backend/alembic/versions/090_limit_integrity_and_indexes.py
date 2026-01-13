"""limit integrity + limits indexes

Revision ID: 090_limit_integrity
Revises: 089_policy_rule_integrity
Create Date: 2026-01-13

PIN-412: Adds limit_integrity table and missing limits/breaches indexes.
Enforces invariant: every ACTIVE limit must have exactly one integrity row.
Mirrors the pattern from policy_rule_integrity (Option C - explicit, not polymorphic).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "090_limit_integrity"
down_revision = "089_policy_rule_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1 — Create limit_integrity table
    # =========================================================================
    # Note: limit_id is VARCHAR to match limits.id schema
    # UNIQUE(limit_id) enforces exactly one integrity row per limit
    op.create_table(
        "limit_integrity",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "limit_id",
            sa.String(),
            sa.ForeignKey("limits.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,  # exactly one integrity row per limit
        ),
        sa.Column(
            "integrity_status",
            sa.String(16),
            nullable=False,
        ),
        sa.Column(
            "integrity_score",
            sa.Numeric(5, 4),
            nullable=False,
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Check constraints
        sa.CheckConstraint(
            "integrity_status IN ('VERIFIED', 'DEGRADED', 'FAILED')",
            name="ck_limit_integrity_status",
        ),
        sa.CheckConstraint(
            "integrity_score >= 0 AND integrity_score <= 1",
            name="ck_limit_integrity_score_range",
        ),
    )

    # =========================================================================
    # STEP 2 — Indexes for limit_integrity
    # =========================================================================
    op.create_index(
        "idx_limit_integrity_status",
        "limit_integrity",
        ["integrity_status"],
    )

    op.create_index(
        "idx_limit_integrity_computed_at",
        "limit_integrity",
        ["computed_at"],
    )

    # =========================================================================
    # STEP 3 — Limits indexes (verify/create)
    # =========================================================================
    # idx_limits_tenant_status
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_limits_tenant_status
        ON limits (tenant_id, status);
        """
    )

    # idx_limits_category
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_limits_category
        ON limits (limit_category);
        """
    )

    # idx_limits_scope
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_limits_scope
        ON limits (scope);
        """
    )

    # =========================================================================
    # STEP 4 — Limit breaches aggregation index (O2 critical)
    # =========================================================================
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_limit_breaches_limit_breached
        ON limit_breaches (limit_id, breached_at);
        """
    )

    # =========================================================================
    # STEP 5 — Invariant Enforcement Trigger
    # Invariant: Every ACTIVE limit must have exactly one integrity row
    # =========================================================================

    # Trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_limit_integrity()
        RETURNS trigger AS $$
        BEGIN
            IF NEW.status = 'ACTIVE' THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM limit_integrity
                    WHERE limit_id = NEW.id
                ) THEN
                    RAISE EXCEPTION
                        'ACTIVE limit % must have exactly one integrity row',
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
        CREATE TRIGGER trg_enforce_limit_integrity
        AFTER INSERT OR UPDATE OF status
        ON limits
        FOR EACH ROW
        EXECUTE FUNCTION enforce_limit_integrity();
        """
    )


def downgrade() -> None:
    # =========================================================================
    # STEP 1 — Drop trigger + function
    # =========================================================================
    op.execute(
        "DROP TRIGGER IF EXISTS trg_enforce_limit_integrity ON limits;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS enforce_limit_integrity;"
    )

    # =========================================================================
    # STEP 2 — Drop indexes (only the ones we explicitly created)
    # =========================================================================
    op.execute("DROP INDEX IF EXISTS idx_limit_breaches_limit_breached;")
    op.execute("DROP INDEX IF EXISTS idx_limits_scope;")
    op.execute("DROP INDEX IF EXISTS idx_limits_category;")
    op.execute("DROP INDEX IF EXISTS idx_limits_tenant_status;")

    op.drop_index(
        "idx_limit_integrity_computed_at",
        table_name="limit_integrity",
    )

    op.drop_index(
        "idx_limit_integrity_status",
        table_name="limit_integrity",
    )

    # =========================================================================
    # STEP 3 — Drop table
    # =========================================================================
    op.drop_table("limit_integrity")
