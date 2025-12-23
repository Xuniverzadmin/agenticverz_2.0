"""M25: Graduation Hardening

Revision ID: 044_m25_hardening
Revises: 043_m25_learning
Create Date: 2025-12-23

Adds tables for DERIVED graduation (not manually declared):
- timeline_views: Track real user views of prevention timelines
- graduation_history: Audit trail of graduation status changes

Updates:
- prevention_records: Add is_simulated flag to exclude from real graduation
- regret_events: Add is_simulated flag

CRITICAL: Graduation is COMPUTED from evidence, never set manually.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "044_m25_hardening"
down_revision = "043_m25_learning"
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # TIMELINE VIEWS - Track real user views (for Gate 3)
    # =========================================================================
    op.create_table(
        "timeline_views",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("incident_id", sa.String(64), nullable=False),
        sa.Column("tenant_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64)),
        sa.Column("viewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("has_prevention", sa.Boolean, server_default="false"),
        sa.Column("has_rollback", sa.Boolean, server_default="false"),
        sa.Column("is_simulated", sa.Boolean, server_default="false"),  # Demo views excluded
        sa.Column("session_id", sa.String(64)),  # For deduplication
    )
    op.create_index("idx_timeline_views_tenant", "timeline_views", ["tenant_id", "viewed_at"])
    op.create_index(
        "idx_timeline_views_real",
        "timeline_views",
        ["viewed_at", "has_prevention"],
        postgresql_where=sa.text("is_simulated = false"),
    )

    # =========================================================================
    # GRADUATION HISTORY - Audit trail of status changes
    # =========================================================================
    op.create_table(
        "graduation_history",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("level", sa.String(32), nullable=False),  # alpha/beta/candidate/complete/degraded
        sa.Column("gates_json", JSONB),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_degraded", sa.Boolean, server_default="false"),
        sa.Column("degraded_from", sa.String(32)),
        sa.Column("degradation_reason", sa.Text),
        sa.Column("evidence_snapshot", JSONB),  # Full evidence at time of computation
    )
    op.create_index("idx_graduation_history_time", "graduation_history", ["computed_at"])
    op.create_index("idx_graduation_history_level", "graduation_history", ["level", "computed_at"])

    # =========================================================================
    # UPDATE EXISTING TABLES - Add simulation flags
    # =========================================================================

    # Add is_simulated to prevention_records (exclude from real graduation)
    op.execute(
        """
        ALTER TABLE prevention_records
        ADD COLUMN IF NOT EXISTS is_simulated BOOLEAN DEFAULT false
    """
    )

    # Add is_simulated to regret_events (exclude from real graduation)
    op.execute(
        """
        ALTER TABLE regret_events
        ADD COLUMN IF NOT EXISTS is_simulated BOOLEAN DEFAULT false
    """
    )

    # Mark existing simulated records (those created via simulate endpoints)
    op.execute(
        """
        UPDATE prevention_records
        SET is_simulated = true
        WHERE id LIKE 'prev_sim_%' OR id LIKE 'prev_%' AND created_at > '2025-12-23'
    """
    )

    op.execute(
        """
        UPDATE regret_events
        SET is_simulated = true
        WHERE id LIKE 'regret_sim_%' OR id LIKE 'regret_%' AND created_at > '2025-12-23'
    """
    )

    # =========================================================================
    # CAPABILITY LOCKOUTS - Track what's blocked until graduation
    # =========================================================================
    op.create_table(
        "capability_lockouts",
        sa.Column("capability", sa.String(64), primary_key=True),
        sa.Column("requires_gate", sa.String(32), nullable=False),  # prevention/rollback/timeline
        sa.Column("is_unlocked", sa.Boolean, server_default="false"),
        sa.Column("unlocked_at", sa.DateTime(timezone=True)),
        sa.Column("last_checked", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Insert default capability lockouts
    op.execute(
        """
        INSERT INTO capability_lockouts (capability, requires_gate, is_unlocked)
        VALUES
            ('auto_apply_recovery', 'prevention', false),
            ('auto_activate_policy', 'rollback', false),
            ('full_auto_routing', 'all', false)
        ON CONFLICT (capability) DO NOTHING
    """
    )

    # =========================================================================
    # MODIFY m25_graduation_status - Make it derived, not manual
    # =========================================================================

    # Add columns for derived status
    op.add_column("m25_graduation_status", sa.Column("is_derived", sa.Boolean, server_default="true"))
    op.add_column("m25_graduation_status", sa.Column("last_evidence_eval", sa.DateTime(timezone=True)))
    op.add_column("m25_graduation_status", sa.Column("degraded_from", sa.String(32)))
    op.add_column("m25_graduation_status", sa.Column("degradation_reason", sa.Text))

    # Clear any manually-set graduation (force re-evaluation)
    op.execute(
        """
        UPDATE m25_graduation_status
        SET gate1_passed = false,
            gate2_passed = false,
            gate3_passed = false,
            is_graduated = false,
            status_label = 'M25-ALPHA (0/3 gates) [re-evaluating]',
            is_derived = true,
            last_evidence_eval = NULL
        WHERE id = 1
    """
    )


def downgrade():
    # Drop new tables
    op.drop_table("capability_lockouts")
    op.drop_table("graduation_history")
    op.drop_table("timeline_views")

    # Remove added columns
    op.drop_column("m25_graduation_status", "degradation_reason")
    op.drop_column("m25_graduation_status", "degraded_from")
    op.drop_column("m25_graduation_status", "last_evidence_eval")
    op.drop_column("m25_graduation_status", "is_derived")

    # Remove is_simulated from existing tables
    op.execute("ALTER TABLE prevention_records DROP COLUMN IF EXISTS is_simulated")
    op.execute("ALTER TABLE regret_events DROP COLUMN IF EXISTS is_simulated")
