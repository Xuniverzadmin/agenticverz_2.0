"""
PIN-412: Policy control-plane schema (Option B+ - Legacy Bridge)

Schema pivot with compatibility guarantees:
1. Rename existing policy_rules → policy_rules_legacy (READ-ONLY)
2. Create canonical policy_rules (PIN-412 Governance design)
3. Add explicit lineage bridge (legacy_rule_id)
4. Create policy_enforcements, limits, limit_breaches

Invariants (LOCKED):
- INV-GOV-001: policy_rules is the only executable governance source
- INV-GOV-002: policy_rules_legacy is immutable and non-executable
- INV-GOV-003: Lineage is explicit via legacy_rule_id, never inferred
- INV-GOV-004: No runtime joins between canonical and legacy tables

After this migration:
- Policies › Governance is eligible for O2 API design
- Policies › Limits is eligible for O2 API design
- Legacy rules preserved for audit/provenance

Revision ID: 088_policy_control_plane
Revises: 087_incidents_lifecycle_repair
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "088_policy_control_plane"
down_revision = "087_incidents_lifecycle_repair"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1 — Rename existing policy_rules → policy_rules_legacy
    # =========================================================================
    # This table is now WRITE-FROZEN and READ-ONLY.
    # Legacy rules do NOT execute. They are audit artifacts.

    op.rename_table("policy_rules", "policy_rules_legacy")

    # =========================================================================
    # STEP 2 — Create canonical policy_rules Table (PIN-412 Governance)
    # =========================================================================
    # This is the ONLY executable governance source.

    op.create_table(
        "policy_rules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        # Core rule definition
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "enforcement_mode",
            sa.String(length=16),
            nullable=False,
        ),  # BLOCK, WARN, AUDIT, DISABLED
        sa.Column(
            "scope",
            sa.String(length=16),
            nullable=False,
        ),  # GLOBAL, TENANT, PROJECT, AGENT
        sa.Column("scope_id", sa.String(), nullable=True),  # Specific ID for non-GLOBAL
        sa.Column("conditions", sa.JSON(), nullable=True),  # Rule condition definition
        # Status lifecycle
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="ACTIVE",
        ),  # ACTIVE, RETIRED
        # Provenance
        sa.Column("created_by", sa.String(), nullable=True),  # User or system ID
        sa.Column(
            "source",
            sa.String(length=16),
            nullable=False,
            server_default="MANUAL",
        ),  # MANUAL, SYSTEM, LEARNED
        sa.Column("source_proposal_id", sa.String(), nullable=True),  # Link to proposal
        sa.Column("parent_rule_id", sa.String(), nullable=True),  # For rule evolution
        # Explicit lineage bridge (INV-GOV-003)
        sa.Column("legacy_rule_id", sa.String(), nullable=True),  # FK to legacy
        # Retirement (for retired rules)
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_by", sa.String(), nullable=True),
        sa.Column("retirement_reason", sa.Text(), nullable=True),
        sa.Column("superseded_by", sa.String(), nullable=True),  # FK to new rule
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # CHECK constraints for enums
    op.create_check_constraint(
        "ck_policy_rules_enforcement_mode",
        "policy_rules",
        "enforcement_mode IN ('BLOCK','WARN','AUDIT','DISABLED')",
    )

    op.create_check_constraint(
        "ck_policy_rules_scope",
        "policy_rules",
        "scope IN ('GLOBAL','TENANT','PROJECT','AGENT')",
    )

    op.create_check_constraint(
        "ck_policy_rules_status",
        "policy_rules",
        "status IN ('ACTIVE','RETIRED')",
    )

    op.create_check_constraint(
        "ck_policy_rules_source",
        "policy_rules",
        "source IN ('MANUAL','SYSTEM','LEARNED')",
    )

    # FK for tenant
    op.create_foreign_key(
        "fk_policy_rules_tenant",
        "policy_rules",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Self-referential FK for rule evolution
    op.create_foreign_key(
        "fk_policy_rules_parent",
        "policy_rules",
        "policy_rules",
        ["parent_rule_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_policy_rules_superseded_by",
        "policy_rules",
        "policy_rules",
        ["superseded_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # FK to legacy table (explicit lineage bridge)
    op.create_foreign_key(
        "fk_policy_rules_legacy",
        "policy_rules",
        "policy_rules_legacy",
        ["legacy_rule_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Indexes for O2 list performance
    op.create_index(
        "idx_policy_rules_tenant_status",
        "policy_rules",
        ["tenant_id", "status"],
    )

    op.create_index(
        "idx_policy_rules_tenant_scope",
        "policy_rules",
        ["tenant_id", "scope"],
    )

    op.create_index(
        "idx_policy_rules_enforcement_mode",
        "policy_rules",
        ["enforcement_mode"],
    )

    op.create_index(
        "idx_policy_rules_created_at",
        "policy_rules",
        ["created_at"],
    )

    # =========================================================================
    # STEP 3 — Create policy_enforcements Table
    # =========================================================================
    # Records when rules were triggered (for trigger_count, last_triggered_at)

    op.create_table(
        "policy_enforcements",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=True),  # LLM Run that triggered
        sa.Column("incident_id", sa.String(), nullable=True),  # Resulting incident
        # Enforcement details
        sa.Column(
            "action_taken",
            sa.String(length=16),
            nullable=False,
        ),  # BLOCKED, WARNED, AUDITED
        sa.Column("details", sa.JSON(), nullable=True),  # Context of enforcement
        # Timestamps
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_check_constraint(
        "ck_policy_enforcements_action",
        "policy_enforcements",
        "action_taken IN ('BLOCKED','WARNED','AUDITED')",
    )

    # FKs
    op.create_foreign_key(
        "fk_policy_enforcements_tenant",
        "policy_enforcements",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_policy_enforcements_rule",
        "policy_enforcements",
        "policy_rules",
        ["rule_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_policy_enforcements_run",
        "policy_enforcements",
        "runs",
        ["run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_policy_enforcements_incident",
        "policy_enforcements",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Indexes for aggregation queries
    op.create_index(
        "idx_policy_enforcements_rule_id",
        "policy_enforcements",
        ["rule_id"],
    )

    op.create_index(
        "idx_policy_enforcements_tenant_triggered",
        "policy_enforcements",
        ["tenant_id", "triggered_at"],
    )

    op.create_index(
        "idx_policy_enforcements_run_id",
        "policy_enforcements",
        ["run_id"],
    )

    # =========================================================================
    # STEP 4 — Create limits Table
    # =========================================================================
    # Budget, rate, and threshold limits

    op.create_table(
        "limits",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        # Core limit definition
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "limit_category",
            sa.String(length=16),
            nullable=False,
        ),  # BUDGET, RATE, THRESHOLD
        sa.Column(
            "limit_type",
            sa.String(length=32),
            nullable=False,
        ),  # COST_USD, TOKENS_*, REQUESTS_*, LATENCY_MS, etc.
        sa.Column(
            "scope",
            sa.String(length=16),
            nullable=False,
        ),  # GLOBAL, TENANT, PROJECT, AGENT, PROVIDER
        sa.Column("scope_id", sa.String(), nullable=True),  # Specific ID for non-GLOBAL
        # Limit values
        sa.Column("max_value", sa.Numeric(precision=18, scale=4), nullable=False),
        # Budget-specific
        sa.Column(
            "reset_period",
            sa.String(length=16),
            nullable=True,
        ),  # DAILY, WEEKLY, MONTHLY, NONE
        sa.Column("next_reset_at", sa.DateTime(timezone=True), nullable=True),
        # Rate-specific
        sa.Column("window_seconds", sa.Integer(), nullable=True),
        # Threshold-specific
        sa.Column("measurement_window_seconds", sa.Integer(), nullable=True),
        # Enforcement behavior
        sa.Column(
            "enforcement",
            sa.String(length=16),
            nullable=False,
            server_default="BLOCK",
        ),  # BLOCK, WARN, REJECT, QUEUE, DEGRADE, ALERT
        sa.Column(
            "consequence",
            sa.String(length=16),
            nullable=True,
        ),  # ALERT, INCIDENT, ABORT (for thresholds)
        # Status
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="ACTIVE",
        ),  # ACTIVE, DISABLED
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # CHECK constraints
    op.create_check_constraint(
        "ck_limits_category",
        "limits",
        "limit_category IN ('BUDGET','RATE','THRESHOLD')",
    )

    op.create_check_constraint(
        "ck_limits_scope",
        "limits",
        "scope IN ('GLOBAL','TENANT','PROJECT','AGENT','PROVIDER')",
    )

    op.create_check_constraint(
        "ck_limits_reset_period",
        "limits",
        "reset_period IS NULL OR reset_period IN ('DAILY','WEEKLY','MONTHLY','NONE')",
    )

    op.create_check_constraint(
        "ck_limits_enforcement",
        "limits",
        "enforcement IN ('BLOCK','WARN','REJECT','QUEUE','DEGRADE','ALERT')",
    )

    op.create_check_constraint(
        "ck_limits_consequence",
        "limits",
        "consequence IS NULL OR consequence IN ('ALERT','INCIDENT','ABORT')",
    )

    op.create_check_constraint(
        "ck_limits_status",
        "limits",
        "status IN ('ACTIVE','DISABLED')",
    )

    # FK for tenant
    op.create_foreign_key(
        "fk_limits_tenant",
        "limits",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Indexes for O2 list performance
    op.create_index(
        "idx_limits_tenant_category",
        "limits",
        ["tenant_id", "limit_category"],
    )

    op.create_index(
        "idx_limits_tenant_scope",
        "limits",
        ["tenant_id", "scope"],
    )

    op.create_index(
        "idx_limits_tenant_status",
        "limits",
        ["tenant_id", "status"],
    )

    # =========================================================================
    # STEP 5 — Create limit_breaches Table
    # =========================================================================
    # Records when limits were breached (for breach_count, last_breach_at)

    op.create_table(
        "limit_breaches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("limit_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=True),  # LLM Run that caused breach
        sa.Column("incident_id", sa.String(), nullable=True),  # Resulting incident
        # Breach details
        sa.Column(
            "breach_type",
            sa.String(length=16),
            nullable=False,
        ),  # BREACHED, EXHAUSTED, THROTTLED, VIOLATED
        sa.Column("value_at_breach", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("limit_value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        # Timestamps
        sa.Column(
            "breached_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("recovered_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_check_constraint(
        "ck_limit_breaches_type",
        "limit_breaches",
        "breach_type IN ('BREACHED','EXHAUSTED','THROTTLED','VIOLATED')",
    )

    # FKs
    op.create_foreign_key(
        "fk_limit_breaches_tenant",
        "limit_breaches",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_limit_breaches_limit",
        "limit_breaches",
        "limits",
        ["limit_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "fk_limit_breaches_run",
        "limit_breaches",
        "runs",
        ["run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_limit_breaches_incident",
        "limit_breaches",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Indexes for aggregation
    op.create_index(
        "idx_limit_breaches_limit_id",
        "limit_breaches",
        ["limit_id"],
    )

    op.create_index(
        "idx_limit_breaches_tenant_breached",
        "limit_breaches",
        ["tenant_id", "breached_at"],
    )


def downgrade() -> None:
    # Drop new tables in reverse order (respecting FKs)
    op.drop_table("limit_breaches")
    op.drop_table("limits")
    op.drop_table("policy_enforcements")
    op.drop_table("policy_rules")

    # Restore legacy table name
    op.rename_table("policy_rules_legacy", "policy_rules")
