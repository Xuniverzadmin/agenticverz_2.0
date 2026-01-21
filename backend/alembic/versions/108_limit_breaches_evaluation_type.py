"""Phase 2 placeholder: Extend limit_breaches with evaluation_type

Revision ID: 108_limit_breaches_evaluation_type
Revises: 107_v_runs_o2_policy_context
Create Date: 2026-01-19

STATUS: PLACEHOLDER — DO NOT IMPLEMENT YET

PURPOSE:
    This migration is a placeholder signaling architectural intent for Phase 2.
    The moment customers rely on:
    - Near-threshold trends
    - Historical comparisons
    - Audit exports

    ...this migration must be implemented to persist evaluation outcomes.

PHASE 1 (Current):
    - Query-time evaluation is acceptable (temporary)
    - Documented as GAP-PHASE2
    - Not marked "final"

PHASE 2 (Future):
    - Persist evaluation outcomes in limit_breaches
    - Enable historical trend analysis
    - Support compliance/audit requirements

PLANNED SCHEMA CHANGE:
    ALTER TABLE limit_breaches
    ADD COLUMN evaluation_type VARCHAR(16)
    CHECK (evaluation_type IN ('OK', 'NEAR_THRESHOLD', 'BREACH', 'OVERRIDDEN'));

REFERENCE:
    - ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md (GAP-PHASE2)
    - ACTIVITY_DOMAIN_CONTRACT.md (Section 17 - Evaluation Time Semantics)

IMPLEMENTATION TRIGGER:
    Remove this placeholder and implement when ANY of these occur:
    1. Customer requests historical threshold trend analysis
    2. Compliance requirement for audit trail
    3. Performance issues with query-time evaluation
    4. Phase 3 shadow validation requires historical accuracy
"""

from alembic import op

# revision identifiers
revision = "108_limit_breaches_evaluation_type"
down_revision = "107_v_runs_o2_policy_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PLACEHOLDER — This migration intentionally does nothing.
    # It exists to signal architectural intent and prevent "forgotten debt".
    #
    # When Phase 2 is approved, replace this with:
    #
    # op.add_column(
    #     "limit_breaches",
    #     sa.Column(
    #         "evaluation_type",
    #         sa.String(16),
    #         nullable=True,
    #     )
    # )
    # op.create_check_constraint(
    #     "ck_limit_breaches_evaluation_type",
    #     "limit_breaches",
    #     "evaluation_type IN ('OK', 'NEAR_THRESHOLD', 'BREACH', 'OVERRIDDEN')"
    # )
    pass


def downgrade() -> None:
    # PLACEHOLDER — No changes to revert
    pass
