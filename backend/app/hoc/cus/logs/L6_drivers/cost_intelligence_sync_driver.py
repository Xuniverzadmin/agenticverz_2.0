# capability_id: CAP-001
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: cost_records, feature_tags, cost_anomalies, cost_budgets
#   Writes: none (write ops via analytics L6 cost_write_driver)
# Database:
#   Scope: cross-domain (analytics/logs cost intelligence)
#   Models: FeatureTag, CostAnomaly, CostBudget, CostRecord
# Role: Sync data access for cost intelligence read operations (dashboard, breakdowns, projections)
# Callers: cost_intelligence_engine.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, L2 first-principles purity migration
# artifact_class: CODE

"""
Cost Intelligence Sync Driver (L6)

Pure synchronous database operations for cost intelligence reads.

All methods are pure DB operations — no business logic.
Business decisions (anomaly detection thresholds, trend analysis) stay in L5 engine.

Operations:
- Fetch cost summary for a period
- Fetch costs by feature, user, model
- Fetch cost anomalies
- Fetch cost projections (daily cost data)
- Fetch current spend for budget tracking
- Fetch feature tags for a tenant
- Fetch and manage budgets
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlmodel import Session


class CostIntelligenceSyncDriver:
    """
    L6 sync driver for cost intelligence read operations.

    Pure database access — no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    # =========================================================================
    # Feature Tag Operations
    # =========================================================================

    def check_feature_tag_exists(
        self,
        tenant_id: str,
        tag: str,
    ) -> bool:
        """Check if a feature tag exists for this tenant."""
        result = self._session.execute(
            text("SELECT id FROM feature_tags WHERE tenant_id = :tenant_id AND tag = :tag"),
            {"tenant_id": tenant_id, "tag": tag},
        )
        return result.first() is not None

    def fetch_feature_tags(
        self,
        tenant_id: str,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch feature tags for a tenant."""
        inactive_clause = "" if include_inactive else " AND is_active = true"
        result = self._session.execute(
            text(f"""
                SELECT id, tenant_id, tag, display_name, description,
                       budget_cents, is_active, created_at, updated_at
                FROM feature_tags
                WHERE tenant_id = :tenant_id{inactive_clause}
                ORDER BY tag
            """),
            {"tenant_id": tenant_id},
        )
        return [
            {
                "id": row[0],
                "tenant_id": row[1],
                "tag": row[2],
                "display_name": row[3],
                "description": row[4],
                "budget_cents": row[5],
                "is_active": row[6],
                "created_at": row[7],
                "updated_at": row[8],
            }
            for row in result.all()
        ]

    def fetch_feature_tag_by_tag(
        self,
        tenant_id: str,
        tag: str,
    ) -> Optional[dict[str, Any]]:
        """Fetch a specific feature tag by tag name."""
        result = self._session.execute(
            text("""
                SELECT id, tenant_id, tag, display_name, description,
                       budget_cents, is_active, created_at, updated_at
                FROM feature_tags
                WHERE tenant_id = :tenant_id AND tag = :tag
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "tag": tag},
        )
        row = result.first()
        if not row:
            return None
        return {
            "id": row[0],
            "tenant_id": row[1],
            "tag": row[2],
            "display_name": row[3],
            "description": row[4],
            "budget_cents": row[5],
            "is_active": row[6],
            "created_at": row[7],
            "updated_at": row[8],
        }

    def fetch_active_feature_tag(
        self,
        tenant_id: str,
        tag: str,
    ) -> Optional[dict[str, Any]]:
        """Fetch an active feature tag for validation."""
        result = self._session.execute(
            text("""
                SELECT id FROM feature_tags
                WHERE tenant_id = :tenant_id AND tag = :tag AND is_active = true
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "tag": tag},
        )
        row = result.first()
        return {"id": row[0]} if row else None

    def update_feature_tag(
        self,
        tenant_id: str,
        tag: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        budget_cents: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[dict[str, Any]]:
        """Update a feature tag and return updated values."""
        updates = ["updated_at = NOW()"]
        params: dict = {"tid": tenant_id, "tag": tag}
        if display_name is not None:
            updates.append("display_name = :display_name")
            params["display_name"] = display_name
        if description is not None:
            updates.append("description = :description")
            params["description"] = description
        if budget_cents is not None:
            updates.append("budget_cents = :budget_cents")
            params["budget_cents"] = budget_cents
        if is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = is_active

        set_clause = ", ".join(updates)
        result = self._session.execute(
            text(
                f"UPDATE feature_tags SET {set_clause} "
                "WHERE tenant_id = :tid AND tag = :tag "
                "RETURNING id, tenant_id, tag, display_name, description, "
                "budget_cents, is_active, created_at, updated_at"
            ),
            params,
        )
        row = result.mappings().first()
        if not row:
            return None
        return dict(row)

    # =========================================================================
    # Cost Summary
    # =========================================================================

    def fetch_cost_summary(
        self,
        tenant_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """Fetch aggregated cost metrics for a period."""
        result = self._session.execute(
            text("""
                SELECT
                    COALESCE(SUM(cost_cents), 0) as total_cost,
                    COALESCE(SUM(input_tokens), 0) as total_input,
                    COALESCE(SUM(output_tokens), 0) as total_output,
                    COUNT(*) as request_count
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND created_at >= :period_start
                  AND created_at <= :period_end
            """),
            {"tenant_id": tenant_id, "period_start": period_start, "period_end": period_end},
        )
        row = result.first()
        return {
            "total_cost": row[0] if row else 0,
            "total_input": row[1] if row else 0,
            "total_output": row[2] if row else 0,
            "request_count": row[3] if row else 0,
        }

    def fetch_tenant_budget(
        self,
        tenant_id: str,
    ) -> Optional[dict[str, Any]]:
        """Fetch tenant-level budget (budget_type='tenant', entity_id IS NULL)."""
        result = self._session.execute(
            text("""
                SELECT id, daily_limit_cents, monthly_limit_cents, warn_threshold_pct,
                       hard_limit_enabled, is_active
                FROM cost_budgets
                WHERE tenant_id = :tenant_id
                  AND budget_type = 'tenant'
                  AND entity_id IS NULL
                  AND is_active = true
                LIMIT 1
            """),
            {"tenant_id": tenant_id},
        )
        row = result.first()
        if not row:
            return None
        return {
            "id": row[0],
            "daily_limit_cents": row[1],
            "monthly_limit_cents": row[2],
            "warn_threshold_pct": row[3],
            "hard_limit_enabled": row[4],
            "is_active": row[5],
        }

    # =========================================================================
    # Cost Breakdowns
    # =========================================================================

    def fetch_total_cost(
        self,
        tenant_id: str,
        period_start: datetime,
    ) -> float:
        """Fetch total cost for a period (for percentage calculations)."""
        result = self._session.execute(
            text("""
                SELECT COALESCE(SUM(cost_cents), 0) as total
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :period_start
            """),
            {"tenant_id": tenant_id, "period_start": period_start},
        )
        row = result.first()
        return row[0] if row else 0

    def fetch_costs_by_feature(
        self,
        tenant_id: str,
        period_start: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch costs grouped by feature tag."""
        result = self._session.execute(
            text("""
                SELECT
                    COALESCE(cr.feature_tag, 'unclassified') as feature_tag,
                    ft.display_name,
                    ft.budget_cents,
                    COALESCE(SUM(cr.cost_cents), 0) as total_cost,
                    COUNT(*) as request_count
                FROM cost_records cr
                LEFT JOIN feature_tags ft ON cr.feature_tag = ft.tag AND cr.tenant_id = ft.tenant_id
                WHERE cr.tenant_id = :tenant_id AND cr.created_at >= :period_start
                GROUP BY cr.feature_tag, ft.display_name, ft.budget_cents
                ORDER BY total_cost DESC
            """),
            {"tenant_id": tenant_id, "period_start": period_start},
        )
        return [
            {
                "feature_tag": row[0],
                "display_name": row[1],
                "budget_cents": row[2],
                "total_cost": row[3],
                "request_count": row[4],
            }
            for row in result.all()
        ]

    def fetch_costs_by_user(
        self,
        tenant_id: str,
        period_start: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch costs grouped by user."""
        result = self._session.execute(
            text("""
                SELECT
                    COALESCE(user_id, 'anonymous') as user_id,
                    COALESCE(SUM(cost_cents), 0) as total_cost,
                    COUNT(*) as request_count
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :period_start
                GROUP BY user_id
                ORDER BY total_cost DESC
            """),
            {"tenant_id": tenant_id, "period_start": period_start},
        )
        return [
            {
                "user_id": row[0],
                "total_cost": row[1],
                "request_count": row[2],
            }
            for row in result.all()
        ]

    def fetch_costs_by_model(
        self,
        tenant_id: str,
        period_start: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch costs grouped by model."""
        result = self._session.execute(
            text("""
                SELECT
                    model,
                    COALESCE(SUM(cost_cents), 0) as total_cost,
                    COALESCE(SUM(input_tokens), 0) as total_input,
                    COALESCE(SUM(output_tokens), 0) as total_output,
                    COUNT(*) as request_count
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :period_start
                GROUP BY model
                ORDER BY total_cost DESC
            """),
            {"tenant_id": tenant_id, "period_start": period_start},
        )
        return [
            {
                "model": row[0],
                "total_cost": row[1],
                "total_input": row[2],
                "total_output": row[3],
                "request_count": row[4],
            }
            for row in result.all()
        ]

    # =========================================================================
    # Anomalies
    # =========================================================================

    def fetch_recent_anomalies(
        self,
        tenant_id: str,
        cutoff: datetime,
        include_resolved: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch recent cost anomalies."""
        params: dict[str, Any] = {"tenant_id": tenant_id, "cutoff": cutoff}

        resolved_clause = "" if include_resolved else " AND resolved = false"

        result = self._session.execute(
            text(f"""
                SELECT id, tenant_id, anomaly_type, severity, entity_type, entity_id,
                       current_value_cents, expected_value_cents, deviation_pct,
                       message, incident_id, action_taken, resolved, detected_at
                FROM cost_anomalies
                WHERE tenant_id = :tenant_id
                  AND detected_at >= :cutoff
                  {resolved_clause}
                ORDER BY detected_at DESC
            """),
            params,
        )
        return [
            {
                "id": row[0],
                "tenant_id": row[1],
                "anomaly_type": row[2],
                "severity": row[3],
                "entity_type": row[4],
                "entity_id": row[5],
                "current_value_cents": row[6],
                "expected_value_cents": row[7],
                "deviation_pct": row[8],
                "message": row[9],
                "incident_id": row[10],
                "action_taken": row[11],
                "resolved": row[12],
                "detected_at": row[13],
            }
            for row in result.all()
        ]

    # =========================================================================
    # Projections
    # =========================================================================

    def fetch_daily_costs(
        self,
        tenant_id: str,
        lookback_start: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch daily costs for projection calculation."""
        result = self._session.execute(
            text("""
                SELECT
                    DATE(created_at) as day,
                    COALESCE(SUM(cost_cents), 0) as daily_cost
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :lookback_start
                GROUP BY DATE(created_at)
                ORDER BY day
            """),
            {"tenant_id": tenant_id, "lookback_start": lookback_start},
        )
        return [{"day": row[0], "daily_cost": row[1]} for row in result.all()]

    def fetch_month_spend(
        self,
        tenant_id: str,
        month_start: datetime,
    ) -> float:
        """Fetch current month's total spend."""
        result = self._session.execute(
            text("""
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id AND created_at >= :month_start
            """),
            {"tenant_id": tenant_id, "month_start": month_start},
        )
        row = result.first()
        return row[0] if row else 0

    # =========================================================================
    # Budget Operations
    # =========================================================================

    def fetch_budgets(
        self,
        tenant_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch all active budgets for a tenant."""
        result = self._session.execute(
            text("""
                SELECT id, tenant_id, budget_type, entity_id,
                       daily_limit_cents, monthly_limit_cents,
                       warn_threshold_pct, hard_limit_enabled, is_active
                FROM cost_budgets
                WHERE tenant_id = :tenant_id AND is_active = true
            """),
            {"tenant_id": tenant_id},
        )
        return [
            {
                "id": row[0],
                "tenant_id": row[1],
                "budget_type": row[2],
                "entity_id": row[3],
                "daily_limit_cents": row[4],
                "monthly_limit_cents": row[5],
                "warn_threshold_pct": row[6],
                "hard_limit_enabled": row[7],
                "is_active": row[8],
            }
            for row in result.all()
        ]

    def fetch_budget_by_type(
        self,
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
    ) -> Optional[dict[str, Any]]:
        """Fetch a specific budget by type and entity."""
        if entity_id is None:
            result = self._session.execute(
                text("""
                    SELECT id, tenant_id, budget_type, entity_id,
                           daily_limit_cents, monthly_limit_cents,
                           warn_threshold_pct, hard_limit_enabled, is_active
                    FROM cost_budgets
                    WHERE tenant_id = :tenant_id
                      AND budget_type = :budget_type
                      AND entity_id IS NULL
                    LIMIT 1
                """),
                {"tenant_id": tenant_id, "budget_type": budget_type},
            )
        else:
            result = self._session.execute(
                text("""
                    SELECT id, tenant_id, budget_type, entity_id,
                           daily_limit_cents, monthly_limit_cents,
                           warn_threshold_pct, hard_limit_enabled, is_active
                    FROM cost_budgets
                    WHERE tenant_id = :tenant_id
                      AND budget_type = :budget_type
                      AND entity_id = :entity_id
                    LIMIT 1
                """),
                {"tenant_id": tenant_id, "budget_type": budget_type, "entity_id": entity_id},
            )
        row = result.first()
        if not row:
            return None
        return {
            "id": row[0],
            "tenant_id": row[1],
            "budget_type": row[2],
            "entity_id": row[3],
            "daily_limit_cents": row[4],
            "monthly_limit_cents": row[5],
            "warn_threshold_pct": row[6],
            "hard_limit_enabled": row[7],
            "is_active": row[8],
        }

    def create_budget(
        self,
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
        daily_limit_cents: Optional[int],
        monthly_limit_cents: Optional[int],
        warn_threshold_pct: int,
        hard_limit_enabled: bool,
    ) -> dict[str, Any]:
        """Create a new budget and return the created row."""
        result = self._session.execute(
            text("""
                INSERT INTO cost_budgets
                (tenant_id, budget_type, entity_id, daily_limit_cents,
                 monthly_limit_cents, warn_threshold_pct, hard_limit_enabled)
                VALUES (:tid, :bt, :eid, :dlc, :mlc, :wtp, :hle)
                RETURNING id, tenant_id, budget_type, entity_id,
                          daily_limit_cents, monthly_limit_cents,
                          warn_threshold_pct, hard_limit_enabled, is_active
            """),
            {
                "tid": tenant_id,
                "bt": budget_type,
                "eid": entity_id,
                "dlc": daily_limit_cents,
                "mlc": monthly_limit_cents,
                "wtp": warn_threshold_pct,
                "hle": hard_limit_enabled,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else {}

    def update_budget(
        self,
        budget_id: str,
        daily_limit_cents: Optional[int],
        monthly_limit_cents: Optional[int],
        warn_threshold_pct: int,
        hard_limit_enabled: bool,
    ) -> dict[str, Any]:
        """Update a budget and return the updated row."""
        result = self._session.execute(
            text("""
                UPDATE cost_budgets SET
                daily_limit_cents = :dlc, monthly_limit_cents = :mlc,
                warn_threshold_pct = :wtp, hard_limit_enabled = :hle,
                updated_at = NOW()
                WHERE id = :bid
                RETURNING id, tenant_id, budget_type, entity_id,
                          daily_limit_cents, monthly_limit_cents,
                          warn_threshold_pct, hard_limit_enabled, is_active
            """),
            {
                "bid": budget_id,
                "dlc": daily_limit_cents,
                "mlc": monthly_limit_cents,
                "wtp": warn_threshold_pct,
                "hle": hard_limit_enabled,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else {}

    # =========================================================================
    # Budget Current Spend
    # =========================================================================

    def fetch_current_spend(
        self,
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
        today_start: datetime,
        month_start: datetime,
    ) -> dict[str, float]:
        """Get current daily and monthly spend for a budget entity."""
        where_clause = "tenant_id = :tenant_id"
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "today_start": today_start,
            "month_start": month_start,
        }

        if budget_type == "feature":
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id
        elif budget_type == "user":
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id

        # Daily spend
        daily_result = self._session.execute(
            text(f"""
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE {where_clause} AND created_at >= :today_start
            """),
            params,
        )
        daily_row = daily_result.first()

        # Monthly spend
        monthly_result = self._session.execute(
            text(f"""
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE {where_clause} AND created_at >= :month_start
            """),
            params,
        )
        monthly_row = monthly_result.first()

        return {
            "daily": daily_row[0] if daily_row else 0,
            "monthly": monthly_row[0] if monthly_row else 0,
        }


def get_cost_intelligence_sync_driver(session: Session) -> CostIntelligenceSyncDriver:
    """Get cost intelligence sync driver instance."""
    return CostIntelligenceSyncDriver(session)


__all__ = [
    "CostIntelligenceSyncDriver",
    "get_cost_intelligence_sync_driver",
]
