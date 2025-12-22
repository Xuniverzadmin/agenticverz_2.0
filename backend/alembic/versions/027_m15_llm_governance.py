"""M15 LLM Governance Schema Extensions

Revision ID: 027_m15_llm_governance
Revises: 026_m12_credit_tables_fix
Create Date: 2025-12-14

Adds BudgetLLM governance columns to M12 agent tables:
- jobs: LLM budget tracking at job level
- job_items: Risk scoring and blocking per item
- instances: Per-worker budget and risk tracking

Key Design:
- Per-job budget envelopes (llm_budget_cents)
- Per-worker budget allocation
- Risk scoring on every LLM call
- Blocked items tracked for retry/exclusion

Based on: PIN-070-budgetllm-safety-governance.md
"""

revision = "027_m15_llm_governance"
down_revision = "026_m12_credit_tables_fix"
branch_labels = None
depends_on = None

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


def upgrade():
    # 1. Add LLM governance columns to jobs table
    op.add_column("jobs", sa.Column("llm_budget_cents", sa.Integer(), nullable=True), schema="agents")
    op.add_column(
        "jobs", sa.Column("llm_budget_used", sa.Integer(), server_default="0", nullable=False), schema="agents"
    )
    op.add_column(
        "jobs", sa.Column("llm_risk_violations", sa.Integer(), server_default="0", nullable=False), schema="agents"
    )
    op.add_column("jobs", sa.Column("llm_config", JSONB, server_default="{}", nullable=False), schema="agents")

    # 2. Add LLM governance columns to job_items table
    op.add_column("job_items", sa.Column("risk_score", sa.Float(), nullable=True), schema="agents")
    op.add_column("job_items", sa.Column("risk_factors", JSONB, server_default="{}", nullable=False), schema="agents")
    op.add_column(
        "job_items", sa.Column("blocked", sa.Boolean(), server_default="false", nullable=False), schema="agents"
    )
    op.add_column("job_items", sa.Column("blocked_reason", sa.Text(), nullable=True), schema="agents")
    op.add_column("job_items", sa.Column("params_clamped", JSONB, server_default="{}", nullable=False), schema="agents")
    op.add_column(
        "job_items", sa.Column("llm_cost_cents", sa.Float(), server_default="0", nullable=False), schema="agents"
    )
    op.add_column(
        "job_items", sa.Column("llm_tokens_used", sa.Integer(), server_default="0", nullable=False), schema="agents"
    )

    # 3. Add LLM governance columns to instances table
    op.add_column("instances", sa.Column("llm_budget_cents", sa.Integer(), nullable=True), schema="agents")
    op.add_column(
        "instances", sa.Column("llm_budget_used", sa.Integer(), server_default="0", nullable=False), schema="agents"
    )
    op.add_column(
        "instances", sa.Column("llm_risk_violations", sa.Integer(), server_default="0", nullable=False), schema="agents"
    )
    op.add_column("instances", sa.Column("llm_config", JSONB, server_default="{}", nullable=False), schema="agents")

    # 4. Create index for blocked items (for aggregation filtering)
    op.execute(
        """
        CREATE INDEX idx_job_items_blocked
        ON agents.job_items(job_id, blocked)
        WHERE blocked = true
    """
    )

    # 5. Create index for high-risk items (for monitoring)
    op.execute(
        """
        CREATE INDEX idx_job_items_high_risk
        ON agents.job_items(job_id, risk_score)
        WHERE risk_score > 0.5
    """
    )

    # 6. Update job_progress view to include LLM governance metrics
    op.execute("DROP VIEW IF EXISTS agents.job_progress")
    op.execute(
        """
        CREATE OR REPLACE VIEW agents.job_progress AS
        SELECT
            j.id,
            j.task,
            j.status,
            j.total_items,
            j.completed_items,
            j.failed_items,
            j.total_items - j.completed_items - j.failed_items AS pending_items,
            CASE
                WHEN j.total_items > 0
                THEN ROUND((j.completed_items::NUMERIC / j.total_items) * 100, 2)
                ELSE 0
            END AS progress_pct,
            j.credits_reserved,
            j.credits_spent,
            j.credits_refunded,
            -- LLM governance metrics
            j.llm_budget_cents,
            j.llm_budget_used,
            CASE
                WHEN j.llm_budget_cents > 0
                THEN j.llm_budget_cents - j.llm_budget_used
                ELSE NULL
            END AS llm_budget_remaining,
            j.llm_risk_violations,
            (SELECT COUNT(*) FROM agents.job_items ji WHERE ji.job_id = j.id AND ji.blocked = true) AS blocked_items,
            (SELECT ROUND(AVG(ji.risk_score)::NUMERIC, 3) FROM agents.job_items ji WHERE ji.job_id = j.id AND ji.risk_score IS NOT NULL) AS avg_risk_score,
            j.created_at,
            j.started_at,
            j.completed_at,
            EXTRACT(EPOCH FROM (COALESCE(j.completed_at, now()) - j.started_at)) AS duration_seconds
        FROM agents.jobs j
    """
    )

    # 7. Update active_workers view to include LLM governance metrics
    op.execute("DROP VIEW IF EXISTS agents.active_workers")
    op.execute(
        """
        CREATE OR REPLACE VIEW agents.active_workers AS
        SELECT
            i.id,
            i.agent_id,
            i.instance_id,
            i.job_id,
            i.status,
            i.heartbeat_at,
            now() - i.heartbeat_at AS heartbeat_age,
            -- LLM governance metrics
            i.llm_budget_cents,
            i.llm_budget_used,
            CASE
                WHEN i.llm_budget_cents > 0
                THEN i.llm_budget_cents - i.llm_budget_used
                ELSE NULL
            END AS llm_budget_remaining,
            i.llm_risk_violations,
            i.created_at,
            (SELECT COUNT(*) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.status = 'completed') AS items_completed,
            (SELECT COUNT(*) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.status IN ('claimed', 'running')) AS items_in_progress,
            (SELECT ROUND(AVG(ji.risk_score)::NUMERIC, 3) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.risk_score IS NOT NULL) AS avg_risk_score
        FROM agents.instances i
        WHERE i.status IN ('running', 'idle')
    """
    )

    # 8. Function to check worker budget before LLM call
    op.execute(
        """
        CREATE OR REPLACE FUNCTION agents.check_worker_budget(
            p_instance_id TEXT,
            p_estimated_cost INTEGER
        ) RETURNS TABLE(
            can_proceed BOOLEAN,
            budget_remaining INTEGER,
            reason TEXT
        ) AS $$
        DECLARE
            v_budget_cents INTEGER;
            v_budget_used INTEGER;
            v_remaining INTEGER;
        BEGIN
            SELECT llm_budget_cents, llm_budget_used
            INTO v_budget_cents, v_budget_used
            FROM agents.instances
            WHERE instance_id = p_instance_id;

            IF v_budget_cents IS NULL THEN
                -- No budget limit set
                RETURN QUERY SELECT TRUE, NULL::INTEGER, 'no_limit'::TEXT;
                RETURN;
            END IF;

            v_remaining := v_budget_cents - v_budget_used;

            IF v_remaining < p_estimated_cost THEN
                RETURN QUERY SELECT FALSE, v_remaining, 'budget_exceeded'::TEXT;
            ELSE
                RETURN QUERY SELECT TRUE, v_remaining, 'ok'::TEXT;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # 9. Function to record LLM usage
    op.execute(
        """
        CREATE OR REPLACE FUNCTION agents.record_llm_usage(
            p_item_id UUID,
            p_cost_cents FLOAT,
            p_tokens INTEGER,
            p_risk_score FLOAT,
            p_risk_factors JSONB,
            p_blocked BOOLEAN,
            p_blocked_reason TEXT,
            p_params_clamped JSONB
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_job_id UUID;
            v_worker_instance_id TEXT;
            v_cost_int INTEGER;
        BEGIN
            v_cost_int := CEIL(p_cost_cents);

            -- Get job_id and worker from item
            SELECT job_id, worker_instance_id
            INTO v_job_id, v_worker_instance_id
            FROM agents.job_items
            WHERE id = p_item_id;

            IF v_job_id IS NULL THEN
                RETURN FALSE;
            END IF;

            -- Update job_item
            UPDATE agents.job_items
            SET llm_cost_cents = p_cost_cents,
                llm_tokens_used = p_tokens,
                risk_score = p_risk_score,
                risk_factors = COALESCE(p_risk_factors, '{}'),
                blocked = p_blocked,
                blocked_reason = p_blocked_reason,
                params_clamped = COALESCE(p_params_clamped, '{}')
            WHERE id = p_item_id;

            -- Update job totals
            UPDATE agents.jobs
            SET llm_budget_used = llm_budget_used + v_cost_int,
                llm_risk_violations = llm_risk_violations + CASE WHEN p_blocked THEN 1 ELSE 0 END
            WHERE id = v_job_id;

            -- Update instance totals
            IF v_worker_instance_id IS NOT NULL THEN
                UPDATE agents.instances
                SET llm_budget_used = llm_budget_used + v_cost_int,
                    llm_risk_violations = llm_risk_violations + CASE WHEN p_blocked THEN 1 ELSE 0 END
                WHERE instance_id = v_worker_instance_id;
            END IF;

            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def downgrade():
    # Drop functions
    op.execute(
        "DROP FUNCTION IF EXISTS agents.record_llm_usage(UUID, FLOAT, INTEGER, FLOAT, JSONB, BOOLEAN, TEXT, JSONB)"
    )
    op.execute("DROP FUNCTION IF EXISTS agents.check_worker_budget(TEXT, INTEGER)")

    # Restore original views
    op.execute("DROP VIEW IF EXISTS agents.active_workers")
    op.execute(
        """
        CREATE OR REPLACE VIEW agents.active_workers AS
        SELECT
            i.id,
            i.agent_id,
            i.instance_id,
            i.job_id,
            i.status,
            i.heartbeat_at,
            now() - i.heartbeat_at AS heartbeat_age,
            i.created_at,
            (SELECT COUNT(*) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.status = 'completed') AS items_completed,
            (SELECT COUNT(*) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.status IN ('claimed', 'running')) AS items_in_progress
        FROM agents.instances i
        WHERE i.status IN ('running', 'idle')
    """
    )

    op.execute("DROP VIEW IF EXISTS agents.job_progress")
    op.execute(
        """
        CREATE OR REPLACE VIEW agents.job_progress AS
        SELECT
            j.id,
            j.task,
            j.status,
            j.total_items,
            j.completed_items,
            j.failed_items,
            j.total_items - j.completed_items - j.failed_items AS pending_items,
            CASE
                WHEN j.total_items > 0
                THEN ROUND((j.completed_items::NUMERIC / j.total_items) * 100, 2)
                ELSE 0
            END AS progress_pct,
            j.credits_reserved,
            j.credits_spent,
            j.credits_refunded,
            j.created_at,
            j.started_at,
            j.completed_at,
            EXTRACT(EPOCH FROM (COALESCE(j.completed_at, now()) - j.started_at)) AS duration_seconds
        FROM agents.jobs j
    """
    )

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS agents.idx_job_items_high_risk")
    op.execute("DROP INDEX IF EXISTS agents.idx_job_items_blocked")

    # Drop columns from instances
    op.drop_column("instances", "llm_config", schema="agents")
    op.drop_column("instances", "llm_risk_violations", schema="agents")
    op.drop_column("instances", "llm_budget_used", schema="agents")
    op.drop_column("instances", "llm_budget_cents", schema="agents")

    # Drop columns from job_items
    op.drop_column("job_items", "llm_tokens_used", schema="agents")
    op.drop_column("job_items", "llm_cost_cents", schema="agents")
    op.drop_column("job_items", "params_clamped", schema="agents")
    op.drop_column("job_items", "blocked_reason", schema="agents")
    op.drop_column("job_items", "blocked", schema="agents")
    op.drop_column("job_items", "risk_factors", schema="agents")
    op.drop_column("job_items", "risk_score", schema="agents")

    # Drop columns from jobs
    op.drop_column("jobs", "llm_config", schema="agents")
    op.drop_column("jobs", "llm_risk_violations", schema="agents")
    op.drop_column("jobs", "llm_budget_used", schema="agents")
    op.drop_column("jobs", "llm_budget_cents", schema="agents")
