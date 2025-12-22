"""M22 KillSwitch MVP - Proxy, Kill Switch, Incidents, Replay

Revision ID: 037_m22_killswitch
Revises: 036_m21_tenant_auth_billing
Create Date: 2025-12-19

This migration adds:
- killswitch_state: Tenant and API key freeze state
- proxy_calls: OpenAI proxy call log for replay
- incidents: Auto-grouped failure incidents
- default_guardrails: Read-only default policy pack
"""

import sqlalchemy as sa

from alembic import op

revision = "037_m22_killswitch"
down_revision = "036_m21_tenant_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============== KILLSWITCH STATE ==============
    op.create_table(
        "killswitch_state",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("entity_type", sa.String(20), nullable=False),  # 'tenant' or 'key'
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("is_frozen", sa.Boolean(), nullable=False, default=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("frozen_by", sa.String(100), nullable=True),
        sa.Column("freeze_reason", sa.Text(), nullable=True),
        sa.Column("unfrozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unfrozen_by", sa.String(100), nullable=True),
        sa.Column("auto_triggered", sa.Boolean(), default=False),
        sa.Column("trigger_type", sa.String(50), nullable=True),  # 'budget', 'failure_spike', 'manual'
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("ix_killswitch_state_entity", "killswitch_state", ["entity_type", "entity_id"], unique=True)
    op.create_index("ix_killswitch_state_frozen", "killswitch_state", ["is_frozen", "tenant_id"])

    # ============== PROXY CALLS (for replay) ==============
    op.create_table(
        "proxy_calls",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        sa.Column("api_key_id", sa.String(100), nullable=True, index=True),
        # Request
        sa.Column("endpoint", sa.String(100), nullable=False),  # '/v1/chat/completions', '/v1/embeddings'
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False, index=True),  # SHA256 of canonical request
        sa.Column("request_json", sa.Text(), nullable=False),  # Full request body
        # Response
        sa.Column("response_hash", sa.String(64), nullable=True),  # SHA256 of canonical response
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(50), nullable=True),  # 'budget_exceeded', 'killswitch', etc.
        # Tokens & Cost
        sa.Column("input_tokens", sa.Integer(), default=0),
        sa.Column("output_tokens", sa.Integer(), default=0),
        sa.Column("cost_cents", sa.Numeric(10, 4), default=0),
        # Policy decisions
        sa.Column("policy_decisions_json", sa.Text(), nullable=True),  # Which guardrails fired
        sa.Column("was_blocked", sa.Boolean(), default=False),
        sa.Column("block_reason", sa.String(100), nullable=True),
        # Timing
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("upstream_latency_ms", sa.Integer(), nullable=True),
        # Replay
        sa.Column("replay_eligible", sa.Boolean(), default=True),
        sa.Column("replayed_from_id", sa.String(100), nullable=True),  # If this is a replay
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    op.create_index("ix_proxy_calls_tenant_time", "proxy_calls", ["tenant_id", "created_at"])
    op.create_index("ix_proxy_calls_replay", "proxy_calls", ["tenant_id", "request_hash", "replay_eligible"])

    # ============== INCIDENTS (auto-grouped failures) ==============
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False, index=True),
        # Incident summary
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),  # 'critical', 'high', 'medium', 'low'
        sa.Column("status", sa.String(20), nullable=False, default="open"),  # 'open', 'acknowledged', 'resolved'
        # Root cause
        sa.Column("trigger_type", sa.String(50), nullable=False),  # 'failure_spike', 'budget_breach', 'rate_limit'
        sa.Column("trigger_value", sa.Text(), nullable=True),  # Threshold crossed
        # Impact
        sa.Column("calls_affected", sa.Integer(), default=0),
        sa.Column("cost_delta_cents", sa.Numeric(10, 4), default=0),
        sa.Column("error_rate", sa.Numeric(5, 4), nullable=True),  # e.g., 0.4500 = 45%
        # Actions taken
        sa.Column("auto_action", sa.String(50), nullable=True),  # 'freeze', 'throttle', 'none'
        sa.Column("action_details_json", sa.Text(), nullable=True),
        # Timeline
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        # Related entities
        sa.Column("related_call_ids_json", sa.Text(), nullable=True),  # Array of proxy_call IDs
        sa.Column("killswitch_id", sa.String(100), nullable=True),  # If freeze was triggered
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(100), nullable=True),
    )

    op.create_index("ix_incidents_tenant_status", "incidents", ["tenant_id", "status"])
    op.create_index("ix_incidents_tenant_time", "incidents", ["tenant_id", "created_at"])

    # ============== INCIDENT EVENTS (timeline) ==============
    op.create_table(
        "incident_events",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "incident_id", sa.String(100), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column(
            "event_type", sa.String(50), nullable=False
        ),  # 'call_failed', 'threshold_crossed', 'freeze_triggered', etc.
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=True),  # Event-specific data
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # ============== DEFAULT GUARDRAILS ==============
    op.create_table(
        "default_guardrails",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),  # 'cost', 'rate', 'safety', 'content'
        # Rule definition
        sa.Column("rule_type", sa.String(50), nullable=False),  # 'max_value', 'pattern_block', 'rate_limit'
        sa.Column("rule_config_json", sa.Text(), nullable=False),
        # Enforcement
        sa.Column("action", sa.String(50), nullable=False),  # 'block', 'warn', 'throttle', 'freeze'
        sa.Column("is_enabled", sa.Boolean(), default=True),
        sa.Column("is_default", sa.Boolean(), default=True),  # Part of default pack
        sa.Column("priority", sa.Integer(), default=100),  # Lower = higher priority
        # Version
        sa.Column("version", sa.String(20), default="v1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Insert default guardrails
    op.execute(
        """
        INSERT INTO default_guardrails (id, name, description, category, rule_type, rule_config_json, action, is_enabled, is_default, priority, version)
        VALUES
        ('dg-001', 'max_cost_per_request', 'Maximum cost per single request', 'cost', 'max_value', '{"field": "cost_cents", "max": 100, "unit": "cents"}', 'block', true, true, 10, 'v1'),
        ('dg-002', 'max_tokens_per_request', 'Maximum tokens per single request', 'cost', 'max_value', '{"field": "max_tokens", "max": 16000}', 'block', true, true, 20, 'v1'),
        ('dg-003', 'rate_limit_rpm', 'Rate limit requests per minute', 'rate', 'rate_limit', '{"window_seconds": 60, "max_requests": 100}', 'throttle', true, true, 30, 'v1'),
        ('dg-004', 'failure_spike_freeze', 'Auto-freeze on failure spike', 'safety', 'threshold', '{"metric": "error_rate", "threshold": 0.5, "window_seconds": 60, "min_samples": 10}', 'freeze', true, true, 5, 'v1'),
        ('dg-005', 'prompt_injection_block', 'Block known prompt injection patterns', 'content', 'pattern_block', '{"patterns": ["ignore previous instructions", "disregard above", "system prompt:", "\\\\n\\\\nHuman:", "\\\\n\\\\nAssistant:"]}', 'block', true, true, 1, 'v1')
    """
    )

    # ============== ADD COLUMNS TO EXISTING TABLES ==============

    # Add freeze fields to tenants
    op.add_column("tenants", sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenants", sa.Column("frozen_by", sa.String(100), nullable=True))
    op.add_column("tenants", sa.Column("freeze_reason", sa.Text(), nullable=True))

    # Add freeze fields to api_keys
    op.add_column("api_keys", sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("api_keys", sa.Column("frozen_by", sa.String(100), nullable=True))
    op.add_column("api_keys", sa.Column("freeze_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove columns from existing tables
    op.drop_column("api_keys", "freeze_reason")
    op.drop_column("api_keys", "frozen_by")
    op.drop_column("api_keys", "frozen_at")
    op.drop_column("tenants", "freeze_reason")
    op.drop_column("tenants", "frozen_by")
    op.drop_column("tenants", "frozen_at")

    # Drop tables
    op.drop_table("default_guardrails")
    op.drop_table("incident_events")
    op.drop_table("incidents")
    op.drop_table("proxy_calls")
    op.drop_table("killswitch_state")
