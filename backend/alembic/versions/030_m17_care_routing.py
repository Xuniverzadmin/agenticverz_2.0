"""M17 CARE Routing

Revision ID: 030_m17_care_routing
Revises: 029_m15_sba_validator
Create Date: 2025-12-14

Adds:
- routing.routing_decisions: Audit log of all CARE routing decisions
- routing.capability_probes: Cached probe results
- Index for fast routing decision lookups
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "030_m17_care_routing"
down_revision = "029_m15_sba_validator"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create routing schema
    op.execute("CREATE SCHEMA IF NOT EXISTS routing")

    # Routing decisions audit table
    op.create_table(
        "routing_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("request_id", sa.String(32), nullable=False, index=True),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("task_domain", sa.String(100), nullable=True),
        sa.Column("selected_agent_id", sa.String(100), nullable=True),
        sa.Column("success_metric", sa.String(20), nullable=False, server_default="balanced"),
        sa.Column("orchestrator_mode", sa.String(20), nullable=False, server_default="sequential"),
        sa.Column("risk_policy", sa.String(20), nullable=False, server_default="balanced"),
        sa.Column("eligible_agents", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("fallback_agents", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("degraded_reason", sa.Text(), nullable=True),
        sa.Column("evaluated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("routed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("actionable_fix", sa.Text(), nullable=True),
        sa.Column("total_latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("stage_latencies", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("decision_details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("tenant_id", sa.String(100), nullable=False, server_default="default"),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="routing",
    )

    # Index for time-based queries
    op.create_index("ix_routing_decisions_decided_at", "routing_decisions", ["decided_at"], schema="routing")

    # Index for agent-based queries
    op.create_index("ix_routing_decisions_agent", "routing_decisions", ["selected_agent_id"], schema="routing")

    # Index for tenant queries
    op.create_index("ix_routing_decisions_tenant", "routing_decisions", ["tenant_id", "decided_at"], schema="routing")

    # Capability probe cache table (for persistence across restarts)
    op.create_table(
        "capability_probes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("probe_type", sa.String(20), nullable=False),
        sa.Column("probe_name", sa.String(200), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("fix_instruction", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema="routing",
    )

    # Unique index for probe lookup
    op.create_index(
        "ix_capability_probes_lookup", "capability_probes", ["probe_type", "probe_name"], unique=True, schema="routing"
    )

    # Agent routing stats view (for quick routing decisions)
    op.execute(
        """
        CREATE OR REPLACE VIEW routing.agent_routing_stats AS
        SELECT
            selected_agent_id as agent_id,
            COUNT(*) as total_routes,
            COUNT(*) FILTER (WHERE routed = true) as successful_routes,
            AVG(total_latency_ms) as avg_latency_ms,
            MAX(decided_at) as last_routed_at
        FROM routing.routing_decisions
        WHERE selected_agent_id IS NOT NULL
        GROUP BY selected_agent_id
    """
    )

    # Add routing_config column to agent_registry (for M17 extensions)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'agents'
                AND table_name = 'agent_registry'
                AND column_name = 'routing_config'
            ) THEN
                ALTER TABLE agents.agent_registry
                ADD COLUMN routing_config JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    # Drop view
    op.execute("DROP VIEW IF EXISTS routing.agent_routing_stats")

    # Drop tables
    op.drop_table("capability_probes", schema="routing")
    op.drop_table("routing_decisions", schema="routing")

    # Drop schema (only if empty)
    op.execute("DROP SCHEMA IF EXISTS routing")

    # Remove routing_config column
    op.execute(
        """
        ALTER TABLE agents.agent_registry
        DROP COLUMN IF EXISTS routing_config
    """
    )
