"""
Phase E FIX-03: Governance Signals Table.

Adds governance_signals table for explicit L7 → L6 governance persistence.
L4/L5 can query governance state before proceeding.

Reference: PIN-256, PHASE_E_FIX_DESIGN.md
Violations Resolved: VIOLATION-004, VIOLATION-005
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "064_phase_e_governance_signals"
down_revision = "063_c4_coordination_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create governance_signals table
    op.create_table(
        "governance_signals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Signal type: what kind of governance decision
        sa.Column(
            "signal_type",
            sa.String(50),
            nullable=False,
            comment="Type: BLCA_STATUS, CI_STATUS, DEPLOYMENT_GATE, SESSION_BLOCK",
        ),
        # Scope: what this signal applies to
        sa.Column(
            "scope",
            sa.String(500),
            nullable=False,
            comment="Scope identifier: file path, PR number, commit SHA, session ID",
        ),
        # Decision: the governance verdict
        sa.Column(
            "decision",
            sa.String(20),
            nullable=False,
            comment="Decision: CLEAN, BLOCKED, WARN, PENDING",
        ),
        # Reason: human-readable explanation
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
            comment="Why this decision was made",
        ),
        # Constraints: structured details about what's blocked
        sa.Column(
            "constraints",
            postgresql.JSONB(),
            nullable=True,
            comment="Structured constraints: {blocked_files: [...], blocked_actions: [...]}",
        ),
        # Source: who/what generated this signal
        sa.Column(
            "recorded_by",
            sa.String(100),
            nullable=False,
            comment="Source: BLCA, CI, OPS, MANUAL",
        ),
        # Timestamps
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When this signal was recorded",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Optional expiration for temporary blocks",
        ),
        # Superseded tracking
        sa.Column(
            "superseded_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="ID of signal that superseded this one",
        ),
        sa.Column(
            "superseded_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When this signal was superseded",
        ),
        # Constraints
        sa.CheckConstraint(
            "signal_type IN ('BLCA_STATUS', 'CI_STATUS', 'DEPLOYMENT_GATE', 'SESSION_BLOCK', 'MANUAL_OVERRIDE')",
            name="gov_signal_type_valid",
        ),
        sa.CheckConstraint(
            "decision IN ('CLEAN', 'BLOCKED', 'WARN', 'PENDING')",
            name="gov_decision_valid",
        ),
        comment="Phase E FIX-03: Explicit governance signals from L7 to L6",
    )

    # 2. Create indexes for efficient queries
    op.create_index(
        "ix_gov_signals_scope",
        "governance_signals",
        ["scope"],
    )
    op.create_index(
        "ix_gov_signals_type",
        "governance_signals",
        ["signal_type"],
    )
    op.create_index(
        "ix_gov_signals_decision",
        "governance_signals",
        ["decision"],
    )
    op.create_index(
        "ix_gov_signals_recorded_at",
        "governance_signals",
        ["recorded_at"],
    )
    # Composite index for active signal lookup
    op.create_index(
        "ix_gov_signals_scope_type_active",
        "governance_signals",
        ["scope", "signal_type", "decision"],
    )
    # Partial index for finding active (non-superseded) signals
    op.create_index(
        "ix_gov_signals_active",
        "governance_signals",
        ["scope", "signal_type"],
        postgresql_where=sa.text("superseded_at IS NULL"),
    )


def downgrade() -> None:
    # 1. Drop indexes
    op.drop_index("ix_gov_signals_active", table_name="governance_signals")
    op.drop_index("ix_gov_signals_scope_type_active", table_name="governance_signals")
    op.drop_index("ix_gov_signals_recorded_at", table_name="governance_signals")
    op.drop_index("ix_gov_signals_decision", table_name="governance_signals")
    op.drop_index("ix_gov_signals_type", table_name="governance_signals")
    op.drop_index("ix_gov_signals_scope", table_name="governance_signals")

    # 2. Drop table
    op.drop_table("governance_signals")
