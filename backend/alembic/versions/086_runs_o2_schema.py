"""
PIN-411: Add O2 schema columns to runs table

Adds Aurora runtime projection columns for Activity domain:
- state (LIVE/COMPLETED lifecycle)
- risk_level, latency_bucket, evidence_health, integrity_status (derived)
- source, provider_type (origin)
- incident_count, policy_violation (impact signals)
- project_id, last_seen_at (scope and heartbeat)
- input_tokens, output_tokens, estimated_cost_usd (cost tracking)

Creates v_runs_o2 view for read-only O2 queries.
Creates required indexes for /runs endpoint performance.

Revision ID: 086_runs_o2_schema
Revises: 085_evidence_failure_resolution
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "086_runs_o2_schema"
down_revision = "085_evidence_failure_resolution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Step 1: Add O2 columns to runs table
    # =========================================================================

    # State column (LIVE/COMPLETED lifecycle, different from status)
    op.add_column(
        "runs",
        sa.Column(
            "state",
            sa.String(20),
            nullable=False,
            server_default="LIVE",
            comment="Run lifecycle state: LIVE or COMPLETED"
        )
    )

    # Project scope
    op.add_column(
        "runs",
        sa.Column(
            "project_id",
            sa.String(36),
            nullable=True,
            comment="Project scope (UUID)"
        )
    )

    # Heartbeat for LIVE runs
    op.add_column(
        "runs",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last heartbeat timestamp for LIVE runs"
        )
    )

    # Source and provider
    op.add_column(
        "runs",
        sa.Column(
            "source",
            sa.String(20),
            nullable=False,
            server_default="agent",
            comment="Run initiator: agent, human, sdk"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "provider_type",
            sa.String(30),
            nullable=False,
            server_default="anthropic",
            comment="LLM provider: openai, anthropic, internal"
        )
    )

    # Risk and health columns (computed upstream, stored here)
    op.add_column(
        "runs",
        sa.Column(
            "risk_level",
            sa.String(20),
            nullable=False,
            server_default="NORMAL",
            comment="Risk classification: NORMAL, NEAR_THRESHOLD, AT_RISK, VIOLATED"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "latency_bucket",
            sa.String(20),
            nullable=False,
            server_default="OK",
            comment="Latency classification: OK, SLOW, STALLED"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "evidence_health",
            sa.String(20),
            nullable=False,
            server_default="FLOWING",
            comment="Evidence capture health: FLOWING, DEGRADED, MISSING"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "integrity_status",
            sa.String(20),
            nullable=False,
            server_default="UNKNOWN",
            comment="Integrity verification: UNKNOWN, VERIFIED, DEGRADED, FAILED"
        )
    )

    # Impact signals
    op.add_column(
        "runs",
        sa.Column(
            "incident_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Count of incidents caused by this run"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "policy_draft_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Count of policy drafts generated"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "policy_violation",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether run violated any policy"
        )
    )

    # Cost tracking
    op.add_column(
        "runs",
        sa.Column(
            "input_tokens",
            sa.Integer(),
            nullable=True,
            comment="Input token count"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "output_tokens",
            sa.Integer(),
            nullable=True,
            comment="Output token count"
        )
    )

    op.add_column(
        "runs",
        sa.Column(
            "estimated_cost_usd",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Estimated cost in USD"
        )
    )

    # Expected latency for latency_bucket computation
    op.add_column(
        "runs",
        sa.Column(
            "expected_latency_ms",
            sa.Integer(),
            nullable=True,
            comment="Expected latency in ms (from policy/intent)"
        )
    )

    # =========================================================================
    # Step 2: Create indexes for /runs endpoint performance
    # =========================================================================

    # Primary query pattern: tenant + state + time
    op.create_index(
        "idx_runs_tenant_state_started",
        "runs",
        ["tenant_id", "state", "started_at"],
        postgresql_using="btree"
    )

    # Risk filtering
    op.create_index(
        "idx_runs_tenant_risk",
        "runs",
        ["tenant_id", "risk_level"],
        postgresql_using="btree"
    )

    # Status filtering
    op.create_index(
        "idx_runs_tenant_status",
        "runs",
        ["tenant_id", "status"],
        postgresql_using="btree"
    )

    # Completed time range queries
    op.create_index(
        "idx_runs_tenant_completed",
        "runs",
        ["tenant_id", "completed_at"],
        postgresql_using="btree"
    )

    # Latency bucket filtering
    op.create_index(
        "idx_runs_tenant_latency",
        "runs",
        ["tenant_id", "latency_bucket"],
        postgresql_using="btree"
    )

    # Last seen for LIVE run queries
    op.create_index(
        "idx_runs_tenant_lastseen",
        "runs",
        ["tenant_id", "last_seen_at"],
        postgresql_using="btree"
    )

    # Project scope
    op.create_index(
        "idx_runs_tenant_project",
        "runs",
        ["tenant_id", "project_id"],
        postgresql_using="btree"
    )

    # =========================================================================
    # Step 3: Create v_runs_o2 view for read-only O2 queries
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW v_runs_o2 AS
        SELECT
            id AS run_id,
            tenant_id,
            project_id,
            is_synthetic,
            source,
            provider_type,
            state,
            status,
            started_at,
            last_seen_at,
            completed_at,
            duration_ms,
            risk_level,
            latency_bucket,
            evidence_health,
            integrity_status,
            incident_count,
            policy_draft_count,
            policy_violation,
            input_tokens,
            output_tokens,
            estimated_cost_usd,
            expected_latency_ms,
            synthetic_scenario_id
        FROM runs
    """)


def downgrade() -> None:
    # Drop view first
    op.execute("DROP VIEW IF EXISTS v_runs_o2")

    # Drop indexes
    op.drop_index("idx_runs_tenant_project", table_name="runs")
    op.drop_index("idx_runs_tenant_lastseen", table_name="runs")
    op.drop_index("idx_runs_tenant_latency", table_name="runs")
    op.drop_index("idx_runs_tenant_completed", table_name="runs")
    op.drop_index("idx_runs_tenant_status", table_name="runs")
    op.drop_index("idx_runs_tenant_risk", table_name="runs")
    op.drop_index("idx_runs_tenant_state_started", table_name="runs")

    # Drop columns
    op.drop_column("runs", "expected_latency_ms")
    op.drop_column("runs", "estimated_cost_usd")
    op.drop_column("runs", "output_tokens")
    op.drop_column("runs", "input_tokens")
    op.drop_column("runs", "policy_violation")
    op.drop_column("runs", "policy_draft_count")
    op.drop_column("runs", "incident_count")
    op.drop_column("runs", "integrity_status")
    op.drop_column("runs", "evidence_health")
    op.drop_column("runs", "latency_bucket")
    op.drop_column("runs", "risk_level")
    op.drop_column("runs", "provider_type")
    op.drop_column("runs", "source")
    op.drop_column("runs", "last_seen_at")
    op.drop_column("runs", "project_id")
    op.drop_column("runs", "state")
