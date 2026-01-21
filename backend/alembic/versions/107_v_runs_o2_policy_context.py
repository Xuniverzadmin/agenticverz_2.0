"""Extend v_runs_o2 view with policy context projection

Revision ID: 107_v_runs_o2_policy_context
Revises: 106_threshold_params
Create Date: 2026-01-19

PURPOSE:
    Extends v_runs_o2 view to include policy context as advisory metadata.
    This enables Activity V2 endpoints to show "why" a run is at-risk.

POLICY CONTEXT FIELDS ADDED:
    - policy_id: The governing limit ID (or 'SYSTEM_DEFAULT')
    - policy_name: Human-readable limit name
    - policy_scope: TENANT | PROJECT | AGENT | PROVIDER | GLOBAL
    - limit_type: COST_USD | TOKENS_* | TIME_MS | REQUESTS_*
    - threshold_value: The configured threshold
    - threshold_unit: USD | tokens | ms | requests
    - threshold_source: SYSTEM_DEFAULT | TENANT_OVERRIDE
    - evaluation_outcome: OK | NEAR_THRESHOLD | BREACH | OVERRIDDEN | ADVISORY
    - actual_value: The run's actual value for comparison
    - risk_type: Simplified COST | TIME | TOKENS | RATE (for panels)

DESIGN DECISIONS:
    1. Policy context is ADVISORY - derived at query time, not authoritative
    2. Uses LEFT JOIN to limits - runs without limits get SYSTEM_DEFAULT
    3. Phase 1 uses query-time evaluation (not limit_breaches)
    4. Most severe limit wins when multiple apply

REFERENCE:
    - docs/architecture/activity/ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md
    - docs/architecture/activity/ACTIVITY_DOMAIN_CONTRACT.md (V2 sections)
"""

from alembic import op

# revision identifiers
revision = "107_v_runs_o2_policy_context"
down_revision = "106_threshold_params"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop and recreate v_runs_o2 view with policy context
    op.execute("DROP VIEW IF EXISTS v_runs_o2")

    op.execute("""
        CREATE OR REPLACE VIEW v_runs_o2 AS
        WITH run_limits AS (
            -- Find the most relevant limit for each run (by scope priority)
            SELECT DISTINCT ON (r.id)
                r.id AS run_id,
                l.id AS policy_id,
                l.name AS policy_name,
                l.scope AS policy_scope,
                l.limit_type,
                l.max_value AS threshold_value,
                CASE l.limit_type
                    WHEN 'COST_USD' THEN 'USD'
                    WHEN 'COST_CENTS' THEN 'cents'
                    WHEN 'TOKENS_INPUT' THEN 'tokens'
                    WHEN 'TOKENS_OUTPUT' THEN 'tokens'
                    WHEN 'TOKENS_TOTAL' THEN 'tokens'
                    WHEN 'TIME_MS' THEN 'ms'
                    WHEN 'REQUESTS_PM' THEN 'requests/min'
                    WHEN 'REQUESTS_PH' THEN 'requests/hour'
                    ELSE 'units'
                END AS threshold_unit,
                CASE l.scope
                    WHEN 'GLOBAL' THEN 'SYSTEM_DEFAULT'
                    ELSE 'TENANT_OVERRIDE'
                END AS threshold_source,
                -- Determine risk_type for panel grouping
                CASE
                    WHEN l.limit_type LIKE 'COST%' THEN 'COST'
                    WHEN l.limit_type LIKE 'TOKEN%' THEN 'TOKENS'
                    WHEN l.limit_type LIKE 'TIME%' THEN 'TIME'
                    WHEN l.limit_type LIKE 'REQUEST%' THEN 'RATE'
                    ELSE 'OTHER'
                END AS risk_type
            FROM runs r
            LEFT JOIN limits l ON (
                l.tenant_id = r.tenant_id
                AND l.status = 'ACTIVE'
                AND l.limit_category = 'THRESHOLD'
            )
            ORDER BY r.id,
                CASE l.scope
                    WHEN 'TENANT' THEN 1
                    WHEN 'PROJECT' THEN 2
                    WHEN 'AGENT' THEN 3
                    WHEN 'PROVIDER' THEN 4
                    WHEN 'GLOBAL' THEN 5
                    ELSE 6
                END
        ),
        run_evaluations AS (
            -- Evaluate runs against their limits
            SELECT
                r.id AS run_id,
                rl.policy_id,
                rl.policy_name,
                rl.policy_scope,
                rl.limit_type,
                rl.threshold_value,
                rl.threshold_unit,
                rl.threshold_source,
                rl.risk_type,
                -- Determine actual value based on limit type
                CASE
                    WHEN rl.limit_type LIKE 'COST%' THEN r.estimated_cost_usd
                    WHEN rl.limit_type LIKE 'TOKEN%' THEN (COALESCE(r.input_tokens, 0) + COALESCE(r.output_tokens, 0))::numeric
                    WHEN rl.limit_type LIKE 'TIME%' THEN r.duration_ms::numeric
                    ELSE NULL
                END AS actual_value,
                -- Check for existing breach
                lb.breach_type AS breach_type
            FROM runs r
            LEFT JOIN run_limits rl ON r.id = rl.run_id
            LEFT JOIN limit_breaches lb ON r.id = lb.run_id AND rl.policy_id = lb.limit_id
        )
        SELECT
            r.id AS run_id,
            r.tenant_id,
            r.project_id,
            r.is_synthetic,
            r.source,
            r.provider_type,
            r.state,
            r.status,
            r.started_at,
            r.last_seen_at,
            r.completed_at,
            r.duration_ms,
            r.risk_level,
            r.latency_bucket,
            r.evidence_health,
            r.integrity_status,
            r.incident_count,
            r.policy_draft_count,
            r.policy_violation,
            r.input_tokens,
            r.output_tokens,
            r.estimated_cost_usd,
            r.expected_latency_ms,
            r.synthetic_scenario_id,
            -- Policy context fields (advisory)
            COALESCE(re.policy_id, 'SYSTEM_DEFAULT') AS policy_id,
            COALESCE(re.policy_name, 'Default Safety Thresholds') AS policy_name,
            COALESCE(re.policy_scope, 'GLOBAL') AS policy_scope,
            re.limit_type,
            re.threshold_value,
            re.threshold_unit,
            COALESCE(re.threshold_source, 'SYSTEM_DEFAULT') AS threshold_source,
            re.risk_type,
            re.actual_value,
            -- Evaluation outcome (computed)
            CASE
                WHEN re.breach_type IS NOT NULL THEN
                    CASE re.breach_type
                        WHEN 'OVERRIDDEN' THEN 'OVERRIDDEN'
                        ELSE 'BREACH'
                    END
                WHEN re.threshold_value IS NULL THEN 'ADVISORY'
                WHEN re.actual_value IS NULL THEN 'ADVISORY'
                WHEN re.actual_value >= re.threshold_value THEN 'BREACH'
                WHEN re.actual_value >= re.threshold_value * 0.8 THEN 'NEAR_THRESHOLD'
                ELSE 'OK'
            END AS evaluation_outcome,
            -- Proximity percentage for NEAR_THRESHOLD panels
            CASE
                WHEN re.threshold_value IS NOT NULL AND re.threshold_value > 0 AND re.actual_value IS NOT NULL
                THEN ROUND((re.actual_value / re.threshold_value * 100)::numeric, 1)
                ELSE NULL
            END AS proximity_pct
        FROM runs r
        LEFT JOIN run_evaluations re ON r.id = re.run_id
    """)

    # Add index for policy-aware queries
    op.create_index(
        "idx_runs_tenant_risk_type",
        "runs",
        ["tenant_id", "risk_level"],
        postgresql_where="risk_level != 'NORMAL'"
    )


def downgrade() -> None:
    # Drop the index
    op.execute("DROP INDEX IF EXISTS idx_runs_tenant_risk_type")

    # Restore original v_runs_o2 view without policy context
    op.execute("DROP VIEW IF EXISTS v_runs_o2")

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
