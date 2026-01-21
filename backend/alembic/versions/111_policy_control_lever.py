"""Add policy control lever tables

Revision ID: 111_policy_control_lever
Revises: 110_governance_fields
Create Date: 2026-01-20

Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md

This migration implements the policy control lever system:
1. policy_scopes - Scope selectors (PCL-001)
2. policy_precedence - Precedence and conflict resolution (PCL-003)
3. policy_monitor_configs - Monitor configuration (PCL-005)
4. threshold_signals - Threshold events (PCL-006)
5. policy_alert_configs - Alert configuration (PCL-007)
6. policy_override_authority - Override rules (PCL-010)
7. policy_override_records - Override audit trail (PCL-010)
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "111_policy_control_lever"
down_revision = "110_governance_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create policy_scopes table (PCL-001)
    # =========================================================================
    op.create_table(
        "policy_scopes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scope_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("policy_id", sa.String(64), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Scope definition
        sa.Column("scope_type", sa.String(32), nullable=False, server_default="all_runs"),
        sa.Column("agent_ids_json", sa.Text(), nullable=True),
        sa.Column("api_key_ids_json", sa.Text(), nullable=True),
        sa.Column("human_actor_ids_json", sa.Text(), nullable=True),
        # Metadata
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Check constraint for scope_type
    op.create_check_constraint(
        "ck_policy_scopes_scope_type",
        "policy_scopes",
        """scope_type IN ('all_runs', 'agent', 'api_key', 'human_actor')""",
    )

    # Index for policy scope lookups
    op.create_index(
        "idx_policy_scopes_tenant_policy",
        "policy_scopes",
        ["tenant_id", "policy_id"],
    )

    # =========================================================================
    # 2. Create policy_precedence table (PCL-003)
    # =========================================================================
    op.create_table(
        "policy_precedence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Precedence (lower = higher priority)
        sa.Column("precedence", sa.Integer(), nullable=False, server_default="100"),
        # Conflict resolution strategy
        sa.Column("conflict_strategy", sa.String(32), nullable=False, server_default="most_restrictive"),
        # Binding moment
        sa.Column("bind_at", sa.String(32), nullable=False, server_default="run_start"),
        # Failure semantics
        sa.Column("failure_mode", sa.String(32), nullable=False, server_default="fail_closed"),
        # Metadata
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Check constraint for conflict_strategy
    op.create_check_constraint(
        "ck_policy_precedence_strategy",
        "policy_precedence",
        """conflict_strategy IN ('most_restrictive', 'explicit_priority', 'fail_closed')""",
    )

    # Check constraint for bind_at
    op.create_check_constraint(
        "ck_policy_precedence_bind_at",
        "policy_precedence",
        """bind_at IN ('run_start', 'first_token', 'each_step')""",
    )

    # =========================================================================
    # 3. Create policy_monitor_configs table (PCL-005)
    # =========================================================================
    op.create_table(
        "policy_monitor_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("config_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("policy_id", sa.String(64), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Token monitoring
        sa.Column("monitor_token_usage", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("monitor_token_per_step", sa.Boolean(), nullable=False, server_default="false"),
        # Cost monitoring
        sa.Column("monitor_cost", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("monitor_burn_rate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("burn_rate_window_seconds", sa.Integer(), nullable=False, server_default="60"),
        # RAG monitoring
        sa.Column("monitor_rag_access", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("allowed_rag_sources_json", sa.Text(), nullable=True),
        # Latency and step monitoring
        sa.Column("monitor_latency", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("monitor_step_count", sa.Boolean(), nullable=False, server_default="false"),
        # Inspection constraints (negative capabilities)
        sa.Column("allow_prompt_logging", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("allow_response_logging", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("allow_pii_capture", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("allow_secret_access", sa.Boolean(), nullable=False, server_default="false"),
        # Metadata
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # =========================================================================
    # 4. Create threshold_signals table (PCL-006)
    # =========================================================================
    op.create_table(
        "threshold_signals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String(64), nullable=False, unique=True, index=True),
        # References
        sa.Column("run_id", sa.String(64), nullable=False, index=True),
        sa.Column("policy_id", sa.String(64), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("step_index", sa.Integer(), nullable=True),
        # Signal data
        sa.Column("signal_type", sa.String(16), nullable=False),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=True),
        # Action taken (for BREACH signals)
        sa.Column("action_taken", sa.String(16), nullable=True),
        # Timestamp
        sa.Column(
            "timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Acknowledgement
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("acknowledged_by", sa.String(64), nullable=True),
        sa.Column("acknowledged_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # Alert status
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("alert_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("alert_channels", sa.Text(), nullable=True),
    )

    # Check constraint for signal_type
    op.create_check_constraint(
        "ck_threshold_signals_type",
        "threshold_signals",
        """signal_type IN ('near', 'breach')""",
    )

    # Index for finding signals by run
    op.create_index(
        "idx_threshold_signals_run",
        "threshold_signals",
        ["run_id", "timestamp"],
    )

    # Index for finding breach signals
    op.create_index(
        "idx_threshold_signals_breach",
        "threshold_signals",
        ["tenant_id", "signal_type"],
        postgresql_where=sa.text("signal_type = 'breach'"),
    )

    # =========================================================================
    # 5. Create policy_alert_configs table (PCL-007)
    # =========================================================================
    op.create_table(
        "policy_alert_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Near-threshold alerting
        sa.Column("near_threshold_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("near_threshold_percentage", sa.Integer(), nullable=False, server_default="80"),
        # Breach alerting
        sa.Column("breach_alert_enabled", sa.Boolean(), nullable=False, server_default="true"),
        # Notification channels
        sa.Column("enabled_channels_json", sa.Text(), nullable=False, server_default='["ui"]'),
        # Webhook configuration
        sa.Column("webhook_url", sa.Text(), nullable=True),
        sa.Column("webhook_secret", sa.Text(), nullable=True),
        # Email configuration
        sa.Column("email_recipients_json", sa.Text(), nullable=True),
        # Slack configuration
        sa.Column("slack_webhook_url", sa.Text(), nullable=True),
        sa.Column("slack_channel", sa.String(128), nullable=True),
        # Alert throttling
        sa.Column("min_alert_interval_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_alerts_per_run", sa.Integer(), nullable=False, server_default="10"),
        # Last alert tracking
        sa.Column("last_alert_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("alerts_sent_count", sa.Integer(), nullable=False, server_default="0"),
        # Metadata
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # =========================================================================
    # 6. Create policy_override_authority table (PCL-010)
    # =========================================================================
    op.create_table(
        "policy_override_authority",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        # Override rules
        sa.Column("override_allowed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allowed_roles_json", sa.Text(), nullable=False, server_default='["OWNER", "SECURITY_ADMIN"]'),
        sa.Column("requires_reason", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_duration_seconds", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("max_overrides_per_day", sa.Integer(), nullable=False, server_default="5"),
        # Current override state
        sa.Column("currently_overridden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("override_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("override_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("override_by", sa.String(64), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        # Statistics
        sa.Column("total_overrides", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overrides_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_override_date", sa.TIMESTAMP(timezone=True), nullable=True),
        # Metadata
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # =========================================================================
    # 7. Create policy_override_records table (audit trail)
    # =========================================================================
    op.create_table(
        "policy_override_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("record_id", sa.String(64), nullable=False, unique=True, index=True),
        # References
        sa.Column("policy_id", sa.String(64), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("run_id", sa.String(64), nullable=True, index=True),
        # Override details
        sa.Column("override_by", sa.String(64), nullable=False),
        sa.Column("override_role", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        # Timestamps
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # Outcome
        sa.Column("was_manually_ended", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ended_by", sa.String(64), nullable=True),
    )

    # Index for override history
    op.create_index(
        "idx_policy_override_records_policy",
        "policy_override_records",
        ["policy_id", "started_at"],
    )

    # Immutability trigger for threshold_signals
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_threshold_signal_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Allow updates only to acknowledgement and alert fields
            IF OLD.signal_type != NEW.signal_type OR
               OLD.metric != NEW.metric OR
               OLD.current_value != NEW.current_value OR
               OLD.threshold_value != NEW.threshold_value OR
               OLD.run_id != NEW.run_id OR
               OLD.policy_id != NEW.policy_id THEN
                RAISE EXCEPTION 'threshold_signals core fields are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS threshold_signals_immutable ON threshold_signals;
        CREATE TRIGGER threshold_signals_immutable
        BEFORE UPDATE ON threshold_signals
        FOR EACH ROW
        EXECUTE FUNCTION reject_threshold_signal_mutation();
    """)

    # Immutability trigger for policy_override_records
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_override_record_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Allow updates only to ended_at, was_manually_ended, ended_by
            IF OLD.policy_id != NEW.policy_id OR
               OLD.override_by != NEW.override_by OR
               OLD.reason != NEW.reason OR
               OLD.started_at != NEW.started_at THEN
                RAISE EXCEPTION 'policy_override_records core fields are immutable';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS override_records_immutable ON policy_override_records;
        CREATE TRIGGER override_records_immutable
        BEFORE UPDATE ON policy_override_records
        FOR EACH ROW
        EXECUTE FUNCTION reject_override_record_mutation();
    """)


def downgrade() -> None:
    # Remove triggers
    op.execute("DROP TRIGGER IF EXISTS override_records_immutable ON policy_override_records")
    op.execute("DROP FUNCTION IF EXISTS reject_override_record_mutation()")
    op.execute("DROP TRIGGER IF EXISTS threshold_signals_immutable ON threshold_signals")
    op.execute("DROP FUNCTION IF EXISTS reject_threshold_signal_mutation()")

    # Remove tables in reverse order
    op.drop_index("idx_policy_override_records_policy", table_name="policy_override_records")
    op.drop_table("policy_override_records")

    op.drop_table("policy_override_authority")

    op.drop_table("policy_alert_configs")

    op.drop_index("idx_threshold_signals_breach", table_name="threshold_signals")
    op.drop_index("idx_threshold_signals_run", table_name="threshold_signals")
    op.drop_constraint("ck_threshold_signals_type", "threshold_signals", type_="check")
    op.drop_table("threshold_signals")

    op.drop_table("policy_monitor_configs")

    op.drop_constraint("ck_policy_precedence_bind_at", "policy_precedence", type_="check")
    op.drop_constraint("ck_policy_precedence_strategy", "policy_precedence", type_="check")
    op.drop_table("policy_precedence")

    op.drop_index("idx_policy_scopes_tenant_policy", table_name="policy_scopes")
    op.drop_constraint("ck_policy_scopes_scope_type", "policy_scopes", type_="check")
    op.drop_table("policy_scopes")
