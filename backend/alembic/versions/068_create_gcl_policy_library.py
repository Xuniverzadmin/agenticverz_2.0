# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create GC_L Policy Library tables per PIN-340
# Reference: PIN-340, PIN-341, PIN-345

"""Create GC_L Policy Library tables

Revision ID: 068_create_gcl_policy_library
Revises: 067_phase_s_error_persistence
Create Date: 2026-01-07
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "068_create_gcl_policy_library"
down_revision = "067_phase_s_error_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create GC_L Policy Library tables per PIN-340:
    - policy_library: Core policy storage with lifecycle
    - policy_simulation_results: Simulation evidence
    - policy_activation_log: Activation audit trail
    """

    # =========================================================================
    # Table: policy_library
    # Purpose: Store policy definitions with lifecycle states
    # Reference: PIN-340 Section 1.2
    # =========================================================================
    op.create_table(
        "policy_library",
        sa.Column(
            "policy_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),  # NULL = org-scoped
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("policy_type", sa.Text(), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("policy_definition", postgresql.JSONB(), nullable=False),
        # DSL fields per PIN-341
        sa.Column("scope", sa.Text(), nullable=False, server_default="PROJECT"),  # ORG | PROJECT
        sa.Column("mode", sa.Text(), nullable=False, server_default="MONITOR"),  # MONITOR | ENFORCE
        sa.Column("dsl_source", sa.Text(), nullable=True),  # Original DSL text
        sa.Column("ast_hash", sa.Text(), nullable=True),  # Hash of compiled AST
        sa.Column("ir_bytecode", postgresql.JSONB(), nullable=True),  # Compiled IR per PIN-343
        # Metadata
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        # Primary key
        sa.PrimaryKeyConstraint("policy_id"),
        # Foreign key for versioning chain
        sa.ForeignKeyConstraint(["parent_policy_id"], ["policy_library.policy_id"], name="fk_policy_parent"),
        # Constraints per PIN-340
        sa.CheckConstraint(
            "policy_type IN ('RULE', 'LIMIT', 'SAFETY', 'COST', 'ACCESS')", name="ck_policy_library_valid_type"
        ),
        sa.CheckConstraint("origin IN ('HUMAN', 'LEARNED', 'IMPORTED')", name="ck_policy_library_valid_origin"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SIMULATED', 'ACTIVE', 'DISABLED', 'DEPRECATED')",
            name="ck_policy_library_valid_status",
        ),
        sa.CheckConstraint("scope IN ('ORG', 'PROJECT')", name="ck_policy_library_valid_scope"),
        sa.CheckConstraint("mode IN ('MONITOR', 'ENFORCE')", name="ck_policy_library_valid_mode"),
    )

    # Indexes for policy_library
    op.create_index("idx_policy_library_tenant", "policy_library", ["tenant_id"])
    op.create_index(
        "idx_policy_library_project",
        "policy_library",
        ["project_id"],
        postgresql_where=sa.text("project_id IS NOT NULL"),
    )
    op.create_index("idx_policy_library_status", "policy_library", ["status"])
    op.create_index("idx_policy_library_type", "policy_library", ["policy_type"])
    op.create_index("idx_policy_library_origin", "policy_library", ["origin"])
    op.create_index("idx_policy_library_mode", "policy_library", ["mode"])
    op.create_index(
        "idx_policy_library_active",
        "policy_library",
        ["tenant_id", "status"],
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # =========================================================================
    # Table: policy_simulation_results
    # Purpose: Store simulation evidence before activation
    # Reference: PIN-340 Section 1.2
    # =========================================================================
    op.create_table(
        "policy_simulation_results",
        sa.Column(
            "simulation_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("simulated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("lookback_window", sa.Interval(), nullable=False),
        sa.Column("affected_runs", sa.Integer(), nullable=False),
        sa.Column("would_block", sa.Integer(), nullable=False),
        sa.Column("would_warn", sa.Integer(), nullable=False),
        sa.Column("cost_impact_est", sa.Numeric(), nullable=True),
        sa.Column("risk_summary", postgresql.JSONB(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(), nullable=False),
        # Additional fields for simulation context
        sa.Column("simulated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        # Primary key
        sa.PrimaryKeyConstraint("simulation_id"),
        # Foreign key
        sa.ForeignKeyConstraint(["policy_id"], ["policy_library.policy_id"], name="fk_simulation_policy"),
    )

    # Indexes for simulation results
    op.create_index("idx_policy_sim_policy", "policy_simulation_results", ["policy_id"])
    op.create_index("idx_policy_sim_tenant", "policy_simulation_results", ["tenant_id"])
    op.create_index("idx_policy_sim_time", "policy_simulation_results", ["tenant_id", "simulated_at"])

    # =========================================================================
    # Table: policy_activation_log
    # Purpose: Audit trail for policy lifecycle transitions
    # Reference: PIN-340 Section 1.2
    # =========================================================================
    op.create_table(
        "policy_activation_log",
        sa.Column(
            "event_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("performed_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("justification", sa.Text(), nullable=True),
        # Extended fields for governance
        sa.Column("previous_status", sa.Text(), nullable=True),
        sa.Column("new_status", sa.Text(), nullable=False),
        sa.Column("previous_mode", sa.Text(), nullable=True),
        sa.Column("new_mode", sa.Text(), nullable=True),
        sa.Column("simulation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confirmation", sa.Boolean(), nullable=False, server_default="true"),
        # Primary key
        sa.PrimaryKeyConstraint("event_id"),
        # Foreign keys
        sa.ForeignKeyConstraint(["policy_id"], ["policy_library.policy_id"], name="fk_activation_policy"),
        sa.ForeignKeyConstraint(
            ["simulation_id"], ["policy_simulation_results.simulation_id"], name="fk_activation_simulation"
        ),
        # Constraint per PIN-340
        sa.CheckConstraint(
            "action IN ('ACTIVATE', 'DISABLE', 'DEPRECATE', 'SIMULATE', 'MODE_CHANGE')",
            name="ck_activation_log_valid_action",
        ),
    )

    # Indexes for activation log
    op.create_index("idx_policy_activation_policy", "policy_activation_log", ["policy_id"])
    op.create_index("idx_policy_activation_actor", "policy_activation_log", ["performed_by"])
    op.create_index("idx_policy_activation_time", "policy_activation_log", ["policy_id", "performed_at"])

    # =========================================================================
    # Trigger: Prevent DRAFT → ACTIVE transition (must go through SIMULATED)
    # Reference: PIN-340 Section 1.3 State Transition Matrix
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_policy_lifecycle()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Rule: DRAFT cannot directly become ACTIVE (PIN-340)
            IF OLD.status = 'DRAFT' AND NEW.status = 'ACTIVE' THEN
                RAISE EXCEPTION 'GCL-E001: Policy cannot transition directly from DRAFT to ACTIVE. Must simulate first.';
            END IF;

            -- Rule: LEARNED origin always starts as DRAFT (PIN-340)
            IF TG_OP = 'INSERT' AND NEW.origin = 'LEARNED' AND NEW.status != 'DRAFT' THEN
                RAISE EXCEPTION 'GCL-E002: LEARNED policies must start as DRAFT.';
            END IF;

            -- Rule: ENFORCE mode requires SIMULATED or ACTIVE status (PIN-341)
            IF NEW.mode = 'ENFORCE' AND NEW.status = 'DRAFT' THEN
                RAISE EXCEPTION 'GCL-E003: ENFORCE mode requires simulation before activation.';
            END IF;

            -- Update timestamp
            NEW.updated_at = NOW();

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER policy_lifecycle_check
        BEFORE INSERT OR UPDATE ON policy_library
        FOR EACH ROW EXECUTE FUNCTION enforce_policy_lifecycle();
    """)


def downgrade() -> None:
    """Remove GC_L Policy Library tables"""

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS policy_lifecycle_check ON policy_library;")
    op.execute("DROP FUNCTION IF EXISTS enforce_policy_lifecycle();")

    # Drop indexes
    op.drop_index("idx_policy_activation_time", "policy_activation_log")
    op.drop_index("idx_policy_activation_actor", "policy_activation_log")
    op.drop_index("idx_policy_activation_policy", "policy_activation_log")

    op.drop_index("idx_policy_sim_time", "policy_simulation_results")
    op.drop_index("idx_policy_sim_tenant", "policy_simulation_results")
    op.drop_index("idx_policy_sim_policy", "policy_simulation_results")

    op.drop_index("idx_policy_library_active", "policy_library")
    op.drop_index("idx_policy_library_mode", "policy_library")
    op.drop_index("idx_policy_library_origin", "policy_library")
    op.drop_index("idx_policy_library_type", "policy_library")
    op.drop_index("idx_policy_library_status", "policy_library")
    op.drop_index("idx_policy_library_project", "policy_library")
    op.drop_index("idx_policy_library_tenant", "policy_library")

    # Drop tables in reverse order
    op.drop_table("policy_activation_log")
    op.drop_table("policy_simulation_results")
    op.drop_table("policy_library")
