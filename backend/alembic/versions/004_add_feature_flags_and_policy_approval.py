"""Add feature_flags and policy_approval_levels tables

Revision ID: 004_add_feature_flags_and_policy_approval
Revises: 003_add_workflow_id_index
Create Date: 2025-12-03

This migration adds:
1. feature_flags table - DB-backed feature flags for multi-node deployments
2. policy_approval_levels table - Hierarchical policy approval configuration

These tables support M5 capability enforcement and policy-driven autonomy.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_feature_flags_and_policy_approval"
down_revision: Union[str, None] = "003_add_workflow_id_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create feature_flags table
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=False),
        sa.Column("environment", sa.String(50), nullable=False, default="staging", index=True),
        # Flag metadata
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(100), nullable=False, default="platform"),
        sa.Column("requires_signoff", sa.Boolean(), nullable=False, default=False),
        # Rollout configuration
        sa.Column("rollout_percentage", sa.Integer(), nullable=False, default=100),
        sa.Column("rollout_tenant_ids_json", sa.Text(), nullable=True),
        # Audit trail
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column("git_sha", sa.String(40), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
        sa.Column("rollback_to", sa.Text(), nullable=True),  # JSON of previous state
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create policy_approval_levels table
    op.create_table(
        "policy_approval_levels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_type", sa.String(50), nullable=False, index=True),
        # budget, rate_limit, capability, permission
        sa.Column("approval_level", sa.String(50), nullable=False, default="auto_approve"),
        # auto_approve, pre_approved, agent_approve, manual_approve, owner_override
        # Scope
        sa.Column("tenant_id", sa.String(255), nullable=True, index=True),
        sa.Column("agent_id", sa.String(255), nullable=True, index=True),
        sa.Column("skill_id", sa.String(255), nullable=True),
        # Thresholds for auto-approval
        sa.Column("auto_approve_max_cost_cents", sa.BigInteger(), nullable=True),
        sa.Column("auto_approve_max_tokens", sa.Integer(), nullable=True),
        # Escalation config
        sa.Column("escalate_to", sa.String(50), nullable=True),
        sa.Column("escalation_timeout_seconds", sa.Integer(), nullable=False, default=300),
        # Audit
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create cost_records table for CostSim V2 drift tracking
    op.create_table(
        "cost_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_id", sa.String(255), nullable=False, index=True),
        sa.Column("skill_id", sa.String(255), nullable=False, index=True),
        sa.Column("tenant_hash", sa.String(16), nullable=True),
        sa.Column("simulated_cents", sa.Integer(), nullable=False),
        sa.Column("actual_cents", sa.Integer(), nullable=False),
        sa.Column("drift_cents", sa.Integer(), nullable=False),  # actual - simulated
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # Create composite indexes for common queries
    op.create_index("ix_feature_flags_name_env", "feature_flags", ["name", "environment"])

    op.create_index("ix_policy_approval_scope", "policy_approval_levels", ["tenant_id", "agent_id", "policy_type"])

    op.create_index("ix_cost_records_skill_time", "cost_records", ["skill_id", "recorded_at"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_cost_records_skill_time", table_name="cost_records")
    op.drop_index("ix_policy_approval_scope", table_name="policy_approval_levels")
    op.drop_index("ix_feature_flags_name_env", table_name="feature_flags")

    # Drop tables
    op.drop_table("cost_records")
    op.drop_table("policy_approval_levels")
    op.drop_table("feature_flags")
