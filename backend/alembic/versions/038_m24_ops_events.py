"""M24 Ops Console - Event Stream for Founder Intelligence

Revision ID: 038_m24_ops_events
Revises: 037_m22_killswitch
Create Date: 2025-12-20

This migration adds:
- ops_events: Single event stream for all behavioral analytics
- ops_tenant_metrics: Materialized daily metrics per tenant (derived)
- ops_alert_thresholds: Configurable alert thresholds per metric

All Ops Console insights are derived from ops_events.
PIN-105 is the authoritative specification.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "038_m24_ops_events"
down_revision = "037_m22_killswitch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== OPS EVENTS (core event stream) ==============
    op.create_table(
        "ops_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),  # End-user (nullable)
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),  # Conversation session

        # Event classification
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),  # incident, replay, export, etc.
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Metrics
        sa.Column("severity", sa.Integer(), nullable=True),  # 1-5 scale
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),

        # Flexible payload
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )

    # Primary query indexes
    op.create_index(
        "ix_ops_events_tenant_time",
        "ops_events",
        ["tenant_id", sa.text("timestamp DESC")],
    )
    op.create_index(
        "ix_ops_events_type_time",
        "ops_events",
        ["event_type", sa.text("timestamp DESC")],
    )
    op.create_index(
        "ix_ops_events_tenant_type",
        "ops_events",
        ["tenant_id", "event_type"],
    )
    op.create_index(
        "ix_ops_events_entity",
        "ops_events",
        ["entity_type", "entity_id"],
    )

    # Session-based queries for customer intelligence
    op.create_index(
        "ix_ops_events_session",
        "ops_events",
        ["session_id", "timestamp"],
        postgresql_where=sa.text("session_id IS NOT NULL"),
    )

    # ============== OPS TENANT METRICS (daily rollup) ==============
    # Materialized view-like table for fast dashboard queries
    op.create_table(
        "ops_tenant_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),

        # Activity metrics
        sa.Column("api_calls", sa.Integer(), default=0),
        sa.Column("incidents_created", sa.Integer(), default=0),
        sa.Column("incidents_viewed", sa.Integer(), default=0),
        sa.Column("replays_executed", sa.Integer(), default=0),
        sa.Column("exports_generated", sa.Integer(), default=0),
        sa.Column("certs_verified", sa.Integer(), default=0),

        # Cost metrics
        sa.Column("total_cost_usd", sa.Numeric(12, 6), default=0),
        sa.Column("llm_calls", sa.Integer(), default=0),
        sa.Column("llm_failures", sa.Integer(), default=0),

        # Engagement metrics
        sa.Column("unique_users", sa.Integer(), default=0),
        sa.Column("unique_sessions", sa.Integer(), default=0),
        sa.Column("avg_session_duration_s", sa.Integer(), nullable=True),

        # Health metrics
        sa.Column("policy_blocks", sa.Integer(), default=0),
        sa.Column("infra_limit_hits", sa.Integer(), default=0),

        # Stickiness score (computed)
        sa.Column("stickiness_score", sa.Numeric(5, 2), nullable=True),

        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index(
        "ix_ops_tenant_metrics_tenant_date",
        "ops_tenant_metrics",
        ["tenant_id", sa.text("metric_date DESC")],
        unique=True,
    )

    # ============== OPS ALERT THRESHOLDS ==============
    op.create_table(
        "ops_alert_thresholds",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("metric_name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),

        # Threshold config
        sa.Column("threshold_type", sa.String(20), nullable=False),  # 'drop', 'spike', 'absolute'
        sa.Column("threshold_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("window_hours", sa.Integer(), default=24),

        # Alert routing
        sa.Column("severity", sa.String(20), default="warning"),  # 'info', 'warning', 'critical'
        sa.Column("notify_slack", sa.Boolean(), default=True),

        sa.Column("is_enabled", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Insert default thresholds (from PIN-105)
    op.execute("""
        INSERT INTO ops_alert_thresholds (id, metric_name, description, threshold_type, threshold_value, window_hours, severity, notify_slack, is_enabled)
        VALUES
        ('at-001', 'active_tenants', 'Active tenant count drop', 'drop', 20.00, 24, 'warning', true, true),
        ('at-002', 'incidents_created', 'Incident creation spike', 'spike', 50.00, 24, 'warning', true, true),
        ('at-003', 'replays_executed', 'Replay execution drop (stickiness signal)', 'drop', 30.00, 24, 'critical', true, true),
        ('at-004', 'exports_generated', 'Export generation drop (value signal)', 'drop', 40.00, 24, 'critical', true, true),
        ('at-005', 'llm_failure_rate', 'LLM failure rate exceeds threshold', 'absolute', 5.00, 24, 'critical', true, true),
        ('at-006', 'infra_saturation', 'Infrastructure resource saturation', 'absolute', 80.00, 1, 'critical', true, true)
    """)

    # ============== OPS CUSTOMER SEGMENTS ==============
    # Derived customer intelligence
    op.create_table(
        "ops_customer_segments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), primary_key=True),

        # Intent inference
        sa.Column("first_action", sa.String(50), nullable=True),  # First event type after signup
        sa.Column("first_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inferred_buyer_type", sa.String(50), nullable=True),  # 'legal', 'debugging', 'reliability'

        # Stickiness tracking
        sa.Column("current_stickiness", sa.Numeric(5, 2), default=0),
        sa.Column("peak_stickiness", sa.Numeric(5, 2), default=0),
        sa.Column("stickiness_trend", sa.String(20), nullable=True),  # 'rising', 'stable', 'falling', 'silent'

        # Engagement state
        sa.Column("last_api_call", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_investigation", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_silent_churn", sa.Boolean(), default=False),  # API active but no investigation

        # Revenue risk
        sa.Column("risk_level", sa.String(20), default="low"),  # 'low', 'medium', 'high', 'critical'
        sa.Column("risk_reason", sa.Text(), nullable=True),

        # Time-to-value
        sa.Column("first_replay_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_export_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_to_first_replay_m", sa.Integer(), nullable=True),  # Minutes
        sa.Column("time_to_first_export_m", sa.Integer(), nullable=True),

        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("ops_customer_segments")
    op.drop_table("ops_alert_thresholds")
    op.drop_table("ops_tenant_metrics")
    op.drop_table("ops_events")
