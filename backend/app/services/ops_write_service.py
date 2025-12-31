# Layer: L4 — Domain Engine
# Product: system-wide (Ops Console)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DB write delegation for Ops API (Phase 2B extraction)
# Callers: api/ops.py
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L2 (api), L3 (adapters)
# Reference: PIN-250 Phase 2B Batch 3

"""
Ops Write Service - DB write operations for Ops API.

Phase 2B Batch 3: Extracted from api/ops.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
"""

from typing import Optional

from sqlalchemy import text
from sqlmodel import Session


class OpsWriteService:
    """
    DB write operations for Ops background jobs.

    Write-only facade. No policy logic, no branching beyond DB operations.
    """

    def __init__(self, session: Session):
        self.session = session

    def update_silent_churn(self) -> int:
        """
        Update ops_customer_segments to mark silent churn.

        Silent churn = API active but investigation behavior stopped.

        Returns:
            Number of rows affected
        """
        stmt = text(
            """
            UPDATE ops_customer_segments
            SET
                is_silent_churn = true,
                risk_level = 'high',
                risk_reason = 'API active but no investigation in 7 days'
            WHERE tenant_id IN (
                SELECT tenant_id
                FROM ops_events
                GROUP BY tenant_id
                HAVING
                    MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') > now() - interval '48 hours'
                    AND
                    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED')) < now() - interval '7 days'
            )
        """
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount if hasattr(result, "rowcount") else 0

    def compute_stickiness_scores(self) -> int:
        """
        Compute and update stickiness scores for all tenants.

        Computes:
        - stickiness_7d: Recent 7-day engagement score
        - stickiness_30d: Full 30-day engagement score
        - stickiness_delta: Ratio of 7d/30d (trend indicator)
        - friction_score: Weighted friction events
        - last_friction_event: Most recent friction timestamp

        Returns:
            Number of rows affected
        """
        stmt = text(
            """
            WITH actions AS (
                SELECT
                    tenant_id,
                    -- 7-day stickiness (recent engagement)
                    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp > now() - interval '7 days') as views_7d,
                    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp > now() - interval '7 days') as replays_7d,
                    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp > now() - interval '7 days') as exports_7d,
                    -- 30-day stickiness (full window)
                    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp > now() - interval '30 days') as views_30d,
                    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp > now() - interval '30 days') as replays_30d,
                    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp > now() - interval '30 days') as exports_30d,
                    -- Friction events (weighted by severity)
                    COUNT(*) FILTER (WHERE event_type = 'REPLAY_ABORTED' AND timestamp > now() - interval '14 days') as aborts,
                    COUNT(*) FILTER (WHERE event_type = 'EXPORT_ABORTED' AND timestamp > now() - interval '14 days') as export_aborts,
                    COUNT(*) FILTER (WHERE event_type = 'POLICY_BLOCK_REPEAT' AND timestamp > now() - interval '14 days') as policy_blocks,
                    COUNT(*) FILTER (WHERE event_type = 'SESSION_IDLE_TIMEOUT' AND timestamp > now() - interval '14 days') as idle_timeouts,
                    MAX(timestamp) FILTER (WHERE event_type IN (
                        'REPLAY_ABORTED', 'EXPORT_ABORTED', 'POLICY_BLOCK_REPEAT',
                        'SESSION_IDLE_TIMEOUT', 'SESSION_STARTED', 'INVESTIGATION_NO_ACTION'
                    )) as last_friction,
                    -- Last activity timestamps
                    MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') as last_api,
                    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED')) as last_investigation,
                    -- First action
                    MIN(timestamp) as first_action_at
                FROM ops_events
                WHERE timestamp > now() - interval '30 days'
                GROUP BY tenant_id
            ),
            computed AS (
                SELECT
                    tenant_id,
                    -- 7-day stickiness
                    ROUND((views_7d * 0.2 + replays_7d * 0.3 + exports_7d * 0.5)::numeric, 2) as stickiness_7d,
                    -- 30-day stickiness (normalized to weekly equivalent)
                    ROUND(((views_30d * 0.2 + replays_30d * 0.3 + exports_30d * 0.5) / 4.28)::numeric, 2) as stickiness_30d,
                    -- Friction score (capped per Phase-2.1 rules)
                    ROUND(LEAST(
                        (aborts * 2.0 + export_aborts * 1.5 + policy_blocks * 3.0 + idle_timeouts * 1.0),
                        50.0  -- Global cap
                    )::numeric, 2) as friction_score,
                    last_friction,
                    last_api,
                    last_investigation,
                    first_action_at
                FROM actions
            )
            INSERT INTO ops_customer_segments (
                tenant_id, current_stickiness, stickiness_7d, stickiness_30d, stickiness_delta,
                friction_score, last_friction_event, last_api_call, last_investigation,
                first_action_at, computed_at
            )
            SELECT
                tenant_id,
                stickiness_7d as current_stickiness,
                stickiness_7d,
                stickiness_30d,
                CASE
                    WHEN stickiness_30d > 0 THEN ROUND((stickiness_7d / stickiness_30d)::numeric, 2)
                    WHEN stickiness_7d > 0 THEN 2.0  -- New active customer
                    ELSE 0.0
                END as stickiness_delta,
                friction_score,
                last_friction,
                last_api,
                last_investigation,
                first_action_at,
                now()
            FROM computed
            ON CONFLICT (tenant_id) DO UPDATE SET
                current_stickiness = EXCLUDED.current_stickiness,
                stickiness_7d = EXCLUDED.stickiness_7d,
                stickiness_30d = EXCLUDED.stickiness_30d,
                stickiness_delta = EXCLUDED.stickiness_delta,
                peak_stickiness = GREATEST(ops_customer_segments.peak_stickiness, EXCLUDED.current_stickiness),
                stickiness_trend = CASE
                    WHEN EXCLUDED.stickiness_delta > 1.1 THEN 'rising'
                    WHEN EXCLUDED.stickiness_delta < 0.9 THEN 'falling'
                    ELSE 'stable'
                END,
                friction_score = EXCLUDED.friction_score,
                last_friction_event = EXCLUDED.last_friction_event,
                last_api_call = EXCLUDED.last_api_call,
                last_investigation = EXCLUDED.last_investigation,
                first_action_at = COALESCE(ops_customer_segments.first_action_at, EXCLUDED.first_action_at),
                computed_at = now()
        """
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount if hasattr(result, "rowcount") else 0
