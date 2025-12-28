"""PB-S4: Policy Proposals Table

This migration creates the policy_proposals and policy_versions tables
for storing proposed policy changes WITHOUT auto-enforcement.

PB-S4 Guarantee: Propose → Review → Decide (Human)
- Policies are proposed based on observed feedback
- Human approval is mandatory
- No policy auto-enforces
- No policy affects past executions

Revision ID: 057_pb_s4_policy_proposals
Revises: 056_pb_s3_pattern_feedback
Create Date: 2025-12-27

CRITICAL: Policy proposals are INERT until human approval.
No execution data is ever modified by policy proposals.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers
revision = "057_pb_s4_policy_proposals"
down_revision = "056_pb_s3_pattern_feedback"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create policy_proposals and policy_versions tables for PB-S4."""

    # ============================================================
    # STEP 1: Create policy_proposals table
    # ============================================================
    # Note: tenant_id is VARCHAR to match existing tenants table schema
    op.create_table(
        "policy_proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.String(255), nullable=False, index=True),
        # Proposal identification
        sa.Column("proposal_name", sa.String(255), nullable=False),
        sa.Column("proposal_type", sa.String(50), nullable=False, index=True),  # rate_limit, cost_cap, retry_policy
        # Proposal content
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("proposed_rule", JSONB, nullable=False),  # The actual policy rule
        # Provenance - READ-ONLY references to triggering feedback
        # This links back to pattern_feedback records (no FK for independence)
        sa.Column("triggering_feedback_ids", JSONB, nullable=False, default=[]),
        # Status workflow: draft → approved/rejected
        sa.Column("status", sa.String(20), nullable=False, default="draft"),  # draft, approved, rejected
        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        # Review tracking (nullable until reviewed)
        sa.Column("reviewed_at", sa.DateTime, nullable=True),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        # Effective date (only set if approved, future-dated)
        sa.Column("effective_from", sa.DateTime, nullable=True),
    )

    # ============================================================
    # STEP 2: Create policy_versions table (append-only history)
    # ============================================================
    op.create_table(
        "policy_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposal_id", UUID(as_uuid=True), sa.ForeignKey("policy_proposals.id"), nullable=False),
        # Version tracking
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("rule_snapshot", JSONB, nullable=False),  # Snapshot of the rule at this version
        # Audit trail
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("change_reason", sa.Text, nullable=True),
    )

    # ============================================================
    # STEP 3: Add indexes for common queries
    # ============================================================
    op.create_index(
        "ix_policy_proposals_tenant_status",
        "policy_proposals",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_policy_proposals_type",
        "policy_proposals",
        ["proposal_type"],
    )
    op.create_index(
        "ix_policy_proposals_created_at",
        "policy_proposals",
        ["created_at"],
    )
    op.create_index(
        "ix_policy_proposals_draft",
        "policy_proposals",
        ["tenant_id", "status"],
        postgresql_where=sa.text("status = 'draft'"),
    )
    op.create_index(
        "ix_policy_versions_proposal",
        "policy_versions",
        ["proposal_id", "version"],
    )

    # ============================================================
    # STEP 4: Add table comments documenting PB-S4 contract
    # ============================================================
    op.execute(
        """
        COMMENT ON TABLE policy_proposals IS
        'PB-S4 Policy Proposals: Recommended policy changes based on feedback. '
        'This table is SEPARATE from execution tables. '
        'Proposals are INERT until human approval. '
        'No execution data (worker_runs, traces, costs) may be modified by proposals. '
        'Human approval is MANDATORY before any policy becomes effective. '
        'Rule: Propose → Review → Decide (Human).';
    """
    )

    op.execute(
        """
        COMMENT ON TABLE policy_versions IS
        'PB-S4 Policy Versions: Append-only history of policy changes. '
        'Versions are never deleted or modified. '
        'Each approval creates a new version snapshot.';
    """
    )


def downgrade() -> None:
    """Remove policy_proposals and policy_versions tables."""
    op.drop_index("ix_policy_versions_proposal", table_name="policy_versions")
    op.drop_index("ix_policy_proposals_draft", table_name="policy_proposals")
    op.drop_index("ix_policy_proposals_created_at", table_name="policy_proposals")
    op.drop_index("ix_policy_proposals_type", table_name="policy_proposals")
    op.drop_index("ix_policy_proposals_tenant_status", table_name="policy_proposals")
    op.drop_table("policy_versions")
    op.drop_table("policy_proposals")
