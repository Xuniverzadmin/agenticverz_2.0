# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add pre-computed authorization fields to runs table
# Callers: alembic upgrade
# Allowed Imports: L6 (alembic, sqlalchemy)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-256 Phase E FIX-02

"""
Phase E FIX-02: Pre-Computed Authorization Fields.

Adds authorization fields to runs table so L5 (runner) can read
authorization decisions from L6 without importing L4 (rbac_engine).

Authorization is computed at submission time (L2 → L4) and persisted in L6.

Reference: PIN-256, PHASE_E_FIX_DESIGN.md
Violations Resolved: VIOLATION-002 (remaining), VIOLATION-003
"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "065_precomputed_auth"
down_revision = "064_phase_e_governance_signals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add authorization fields to runs table
    # These enable L5 (runner) to read auth decisions without calling L4

    # Authorization decision: the verdict
    op.add_column(
        "runs",
        sa.Column(
            "authorization_decision",
            sa.String(30),
            nullable=True,
            server_default="GRANTED",
            comment="Auth decision: GRANTED, DENIED, PENDING_APPROVAL (FIX-02)",
        ),
    )

    # Which L4 engine evaluated this
    op.add_column(
        "runs",
        sa.Column(
            "authorization_engine",
            sa.String(100),
            nullable=True,
            comment="L4 engine that evaluated: rbac_engine, approvals_engine, etc.",
        ),
    )

    # Structured context: roles, permissions, reason
    op.add_column(
        "runs",
        sa.Column(
            "authorization_context",
            sa.Text(),
            nullable=True,
            comment="JSON: {roles, permissions, resource, action, decision_reason}",
        ),
    )

    # When authorization was computed
    op.add_column(
        "runs",
        sa.Column(
            "authorized_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When authorization decision was computed (submission time)",
        ),
    )

    # Who authorized (user_id, api_key_id, system)
    op.add_column(
        "runs",
        sa.Column(
            "authorized_by",
            sa.String(100),
            nullable=True,
            comment="Principal that authorized: user_id, api_key_id, system",
        ),
    )

    # 2. Create index for efficient authorization queries
    op.create_index(
        "ix_runs_authorization_decision",
        "runs",
        ["authorization_decision"],
    )

    # 3. Add check constraint for valid authorization decisions
    op.create_check_constraint(
        "runs_auth_decision_valid",
        "runs",
        "authorization_decision IS NULL OR authorization_decision IN ('GRANTED', 'DENIED', 'PENDING_APPROVAL')",
    )


def downgrade() -> None:
    # 1. Drop constraint
    op.drop_constraint("runs_auth_decision_valid", "runs", type_="check")

    # 2. Drop index
    op.drop_index("ix_runs_authorization_decision", table_name="runs")

    # 3. Drop columns
    op.drop_column("runs", "authorized_by")
    op.drop_column("runs", "authorized_at")
    op.drop_column("runs", "authorization_context")
    op.drop_column("runs", "authorization_engine")
    op.drop_column("runs", "authorization_decision")
