# MIGRATION_CONTRACT:
#   parent: 094_limit_overrides
#   description: Add indexes for Activity signal endpoints
#   authority: neon

"""
Activity Domain Signal Indexes

Supports:
- COMP-O3: Summary by status (uses existing index)
- LIVE-O5: Runs by dimension (new provider/source indexes)
- SIG-O3: Pattern detection (step analysis indexes)
- SIG-O4: Cost analysis (agent cost index)
- SIG-O5: Attention queue (composite, uses existing indexes)

Reference: docs/architecture/activity/ACTIVITY_DOMAIN_SQL.md

Revision ID: 095_activity_signal_indexes
Revises: 094_limit_overrides
Create Date: 2026-01-17
"""

from alembic import op

revision = "095_activity_signal_indexes"
down_revision = "094_limit_overrides"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # LIVE-O5: Dimension grouping indexes
    # =========================================================================

    # Provider type grouping for /runs/by-dimension?dim=provider_type
    op.create_index(
        "idx_runs_tenant_provider",
        "runs",
        ["tenant_id", "provider_type"],
        postgresql_using="btree"
    )

    # Source grouping for /runs/by-dimension?dim=source
    op.create_index(
        "idx_runs_tenant_source",
        "runs",
        ["tenant_id", "source"],
        postgresql_using="btree"
    )

    # Agent grouping for /runs/by-dimension?dim=agent_id
    op.create_index(
        "idx_runs_tenant_agent",
        "runs",
        ["tenant_id", "agent_id"],
        postgresql_using="btree"
    )

    # =========================================================================
    # SIG-O3: Pattern detection indexes on aos_trace_steps
    # =========================================================================

    # Retry pattern detection
    op.create_index(
        "idx_aos_trace_steps_skill_retry",
        "aos_trace_steps",
        ["trace_id", "skill_id", "retry_count"],
        postgresql_using="btree"
    )

    # Duration analysis for timeout cascades
    op.create_index(
        "idx_aos_trace_steps_duration",
        "aos_trace_steps",
        ["trace_id", "duration_ms"],
        postgresql_using="btree"
    )

    # Step sequence analysis
    op.create_index(
        "idx_aos_trace_steps_sequence",
        "aos_trace_steps",
        ["trace_id", "step_index", "skill_id"],
        postgresql_using="btree"
    )

    # =========================================================================
    # SIG-O4: Cost analysis index
    # =========================================================================

    # Partial index for cost analysis (only rows with cost data)
    op.execute("""
        CREATE INDEX idx_runs_tenant_agent_cost
        ON runs (tenant_id, agent_id, estimated_cost_usd, completed_at)
        WHERE estimated_cost_usd IS NOT NULL
    """)

    # =========================================================================
    # SIG-O5: Attention queue (uses existing risk/status indexes)
    # Composite index for attention scoring
    # =========================================================================

    op.create_index(
        "idx_runs_attention_scoring",
        "runs",
        ["tenant_id", "risk_level", "policy_violation", "incident_count"],
        postgresql_using="btree"
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("idx_runs_attention_scoring", table_name="runs")
    op.drop_index("idx_runs_tenant_agent_cost", table_name="runs")
    op.drop_index("idx_aos_trace_steps_sequence", table_name="aos_trace_steps")
    op.drop_index("idx_aos_trace_steps_duration", table_name="aos_trace_steps")
    op.drop_index("idx_aos_trace_steps_skill_retry", table_name="aos_trace_steps")
    op.drop_index("idx_runs_tenant_agent", table_name="runs")
    op.drop_index("idx_runs_tenant_source", table_name="runs")
    op.drop_index("idx_runs_tenant_provider", table_name="runs")
