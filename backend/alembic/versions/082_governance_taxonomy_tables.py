# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add governance taxonomy tables (PIN-405)
# Reference: PIN-405 (AOS LLM Governance Data Taxonomy v1.0)

"""Add governance taxonomy tables

Revision ID: 082_governance_taxonomy_tables
Revises: 081_tenant_onboarding_state
Create Date: 2026-01-12

PIN-405: AOS LLM Governance Data Taxonomy v1.0 - Full Capture

This migration adds tables required by the LLM Governance Data Taxonomy:
- activity_evidence (Class B) - Governed I/O fingerprints
- policy_decisions (Class D) - Decision evidence
- provider_evidence (Class G) - Provider behavior tracking
- environment_evidence (Class H) - Trust boundary context
- integrity_evidence (Class J) - Evidence about evidence

Also extends the runs table with:
- execution_mode
- execution_environment

Design Invariants (from taxonomy):
- INV-001: No data without run identity
- INV-002: No decision without decision evidence
- INV-005: Absence must be explicit
- INV-006: Integrity must be computable
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

# Revision identifiers
revision = "082_governance_taxonomy_tables"
down_revision = "081_tenant_onboarding_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # CLASS A ENHANCEMENT: Extend runs table
    # ==========================================================================
    op.add_column(
        "runs",
        sa.Column(
            "execution_mode",
            sa.String(20),
            nullable=True,
            comment="SDK invocation mode: direct, api, async_worker, replay",
        ),
    )
    op.add_column(
        "runs",
        sa.Column(
            "execution_environment",
            sa.String(20),
            nullable=True,
            comment="Execution context: prod, staging, dev, sandbox",
        ),
    )

    # ==========================================================================
    # CLASS B: Activity Evidence
    # ==========================================================================
    # Cryptographic proof of prompt/response activity (governed representation)
    op.create_table(
        "activity_evidence",
        # Identity
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        # Input evidence (governed - no raw content)
        sa.Column("prompt_fingerprint", sa.String(64), nullable=False, comment="SHA256 of canonical prompt"),
        sa.Column("prompt_token_length", sa.Integer(), nullable=False),
        sa.Column("prompt_template_id", sa.Text(), nullable=True),
        sa.Column("prompt_template_version", sa.String(20), nullable=True),
        # Output evidence (governed - no raw content)
        sa.Column("response_fingerprint", sa.String(64), nullable=True, comment="SHA256 of canonical response"),
        sa.Column("response_token_length", sa.Integer(), nullable=True),
        sa.Column("completion_type", sa.String(20), nullable=True, comment="final, partial, streaming, refused"),
        # Sensitivity classification
        sa.Column("sensitivity_class", sa.String(20), nullable=True, comment="public, internal, pii, regulated, code"),
        sa.Column("redaction_status", sa.String(20), nullable=True, comment="raw, redacted, hashed"),
        sa.Column("provider_safety_flags", JSONB, nullable=True),
        # Evidence metadata
        sa.Column("evidence_source", sa.String(20), nullable=False, server_default="execution"),
        # SDSR columns
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_activity_evidence_run_id", "activity_evidence", ["run_id"])
    op.create_index("idx_activity_evidence_prompt_fp", "activity_evidence", ["prompt_fingerprint"])
    op.create_index("idx_activity_evidence_skill", "activity_evidence", ["skill_id"])
    op.create_unique_constraint("uq_activity_evidence_run_step", "activity_evidence", ["run_id", "step_index"])

    # ==========================================================================
    # CLASS D: Policy Decisions
    # ==========================================================================
    # Granular decision record per policy evaluation
    op.create_table(
        "policy_decisions",
        # Identity
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        # Decision context
        sa.Column("policy_type", sa.String(50), nullable=False, comment="budget, rate_limit, capability, permission"),
        sa.Column("policy_rule_id", sa.Text(), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=True),
        # Decision outcome
        sa.Column("decision", sa.String(20), nullable=False, comment="GRANTED, DENIED, PENDING_APPROVAL"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decision_confidence", sa.Float(), nullable=True),
        # Policy evaluation details
        sa.Column("policies_evaluated", ARRAY(sa.Text()), nullable=True),
        sa.Column("policy_results", sa.String(20), nullable=True, comment="pass, warn, fail, skip"),
        sa.Column("evaluation_order", ARRAY(sa.Text()), nullable=True),
        sa.Column("thresholds_used", JSONB, nullable=True),
        # Guardrail decisions
        sa.Column("customer_guardrail_result", JSONB, nullable=True),
        sa.Column("provider_moderation_result", JSONB, nullable=True),
        sa.Column("decision_reason_codes", ARRAY(sa.Text()), nullable=True),
        # Approval info
        sa.Column("approval_request_id", sa.Text(), sa.ForeignKey("approval_requests.id"), nullable=True),
        sa.Column("required_approval_level", sa.Integer(), nullable=True),
        sa.Column("current_approval_level", sa.Integer(), nullable=True),
        # Metadata
        sa.Column("evaluated_by", sa.String(50), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # SDSR columns
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_policy_decisions_run_id", "policy_decisions", ["run_id"])
    op.create_index("idx_policy_decisions_type", "policy_decisions", ["policy_type"])
    op.create_index("idx_policy_decisions_decision", "policy_decisions", ["decision"])

    # ==========================================================================
    # CLASS G: Provider Evidence
    # ==========================================================================
    # Track LLM provider requests/responses, token usage, model metadata
    op.create_table(
        "provider_evidence",
        # Identity
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        # Provider identification
        sa.Column("provider_name", sa.String(50), nullable=False, comment="anthropic, openai, etc."),
        sa.Column("provider_request_id", sa.Text(), nullable=True, comment="Provider's own request ID"),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        # Token tracking
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        # Provider metadata
        sa.Column("api_version", sa.String(20), nullable=True),
        sa.Column("endpoint", sa.String(255), nullable=True),
        # Performance metrics
        sa.Column("provider_latency_ms", sa.Integer(), nullable=True),
        sa.Column("provider_http_status", sa.Integer(), nullable=True),
        sa.Column("provider_error_code", sa.String(50), nullable=True),
        sa.Column("provider_retry_count", sa.Integer(), nullable=True, server_default="0"),
        # Safety signals
        sa.Column("provider_safety_signals", JSONB, nullable=True),
        # Timestamps
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        # SDSR columns
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True),
        # Created
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_provider_evidence_run_id", "provider_evidence", ["run_id"])
    op.create_index("idx_provider_evidence_provider", "provider_evidence", ["provider_name"])
    op.create_index("idx_provider_evidence_model", "provider_evidence", ["model_name"])
    op.create_index("idx_provider_evidence_request_id", "provider_evidence", ["provider_request_id"])
    op.create_unique_constraint("uq_provider_evidence_run_step", "provider_evidence", ["run_id", "step_index"])

    # ==========================================================================
    # CLASS H: Environment Evidence
    # ==========================================================================
    # Track SDK mode, telemetry settings, environment configuration
    op.create_table(
        "environment_evidence",
        # Identity
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        # Execution environment
        sa.Column("sdk_mode", sa.String(20), nullable=False, comment="inline, async, degraded, offline"),
        sa.Column("sdk_version", sa.String(20), nullable=True),
        sa.Column("environment", sa.String(20), nullable=True, comment="prod, staging, dev, sandbox"),
        # Telemetry configuration
        sa.Column("telemetry_enabled", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("telemetry_delivery_status", sa.String(20), nullable=True, comment="sent, dropped, buffered, unknown"),
        sa.Column("trace_sampling_rate", sa.Float(), nullable=True, server_default="1.0"),
        sa.Column("metrics_enabled", sa.Boolean(), nullable=True, server_default="true"),
        # Client context
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.Column("client_user_agent", sa.Text(), nullable=True),
        sa.Column("client_origin", sa.String(255), nullable=True),
        # Feature flags
        sa.Column("active_feature_flags", ARRAY(sa.Text()), nullable=True),
        # Debug settings
        sa.Column("debug_mode", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("dry_run", sa.Boolean(), nullable=True, server_default="false"),
        # Capture confidence
        sa.Column("capture_confidence_score", sa.Float(), nullable=True),
        sa.Column("firewall_proxy_detected", sa.Boolean(), nullable=True),
        # SDSR columns
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_environment_evidence_run_id", "environment_evidence", ["run_id"])
    op.create_index("idx_environment_evidence_sdk_mode", "environment_evidence", ["sdk_mode"])
    op.create_index("idx_environment_evidence_env", "environment_evidence", ["environment"])
    op.create_unique_constraint("uq_environment_evidence_run", "environment_evidence", ["run_id"])

    # ==========================================================================
    # CLASS J: Integrity Evidence
    # ==========================================================================
    # Evidence about the evidence - expected vs observed artifacts
    op.create_table(
        "integrity_evidence",
        # Identity
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.Text(), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        # Integrity expectations
        sa.Column("expected_artifacts", ARRAY(sa.Text()), nullable=False),
        sa.Column("expected_artifact_schema", JSONB, nullable=True),
        # Observed artifacts
        sa.Column("observed_artifacts", ARRAY(sa.Text()), nullable=False),
        sa.Column("missing_artifacts", ARRAY(sa.Text()), nullable=True),
        sa.Column("missing_reasons", JSONB, nullable=True),
        # Integrity computation
        sa.Column("integrity_score", sa.Float(), nullable=False, comment="0.0-1.0 ratio of observed/expected"),
        sa.Column("integrity_status", sa.String(20), nullable=False, comment="VALID, DEGRADED, FAILED"),
        # Verification
        sa.Column("verification_method", sa.String(30), nullable=True, comment="hash_match, schema_validation, semantic_check"),
        sa.Column("verification_timestamp", sa.DateTime(timezone=True), nullable=True),
        # Recovery (if failed)
        sa.Column("divergence_details", sa.Text(), nullable=True),
        sa.Column("recovery_action", sa.Text(), nullable=True),
        # Coverage metrics
        sa.Column("coverage_metrics", JSONB, nullable=True),
        # SDSR columns
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_integrity_evidence_run_id", "integrity_evidence", ["run_id"])
    op.create_index("idx_integrity_evidence_status", "integrity_evidence", ["integrity_status"])
    op.create_index("idx_integrity_evidence_score", "integrity_evidence", ["integrity_score"])
    op.create_unique_constraint("uq_integrity_evidence_run", "integrity_evidence", ["run_id"])


def downgrade() -> None:
    # Drop integrity_evidence
    op.drop_constraint("uq_integrity_evidence_run", "integrity_evidence")
    op.drop_index("idx_integrity_evidence_score", "integrity_evidence")
    op.drop_index("idx_integrity_evidence_status", "integrity_evidence")
    op.drop_index("idx_integrity_evidence_run_id", "integrity_evidence")
    op.drop_table("integrity_evidence")

    # Drop environment_evidence
    op.drop_constraint("uq_environment_evidence_run", "environment_evidence")
    op.drop_index("idx_environment_evidence_env", "environment_evidence")
    op.drop_index("idx_environment_evidence_sdk_mode", "environment_evidence")
    op.drop_index("idx_environment_evidence_run_id", "environment_evidence")
    op.drop_table("environment_evidence")

    # Drop provider_evidence
    op.drop_constraint("uq_provider_evidence_run_step", "provider_evidence")
    op.drop_index("idx_provider_evidence_request_id", "provider_evidence")
    op.drop_index("idx_provider_evidence_model", "provider_evidence")
    op.drop_index("idx_provider_evidence_provider", "provider_evidence")
    op.drop_index("idx_provider_evidence_run_id", "provider_evidence")
    op.drop_table("provider_evidence")

    # Drop policy_decisions
    op.drop_index("idx_policy_decisions_decision", "policy_decisions")
    op.drop_index("idx_policy_decisions_type", "policy_decisions")
    op.drop_index("idx_policy_decisions_run_id", "policy_decisions")
    op.drop_table("policy_decisions")

    # Drop activity_evidence
    op.drop_constraint("uq_activity_evidence_run_step", "activity_evidence")
    op.drop_index("idx_activity_evidence_skill", "activity_evidence")
    op.drop_index("idx_activity_evidence_prompt_fp", "activity_evidence")
    op.drop_index("idx_activity_evidence_run_id", "activity_evidence")
    op.drop_table("activity_evidence")

    # Remove runs columns
    op.drop_column("runs", "execution_environment")
    op.drop_column("runs", "execution_mode")
