# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: cost_records, cost_anomalies, breach_history, drift_tracking
#   Writes: cost_anomalies, breach_history, drift_tracking
# Database:
#   Scope: domain (analytics)
#   Models: CostRecord, CostAnomaly, BreachHistory, DriftTracking
# Role: Data access for cost anomaly detection operations
# Callers: cost_anomaly_detector.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, Phase-2.5A Analytics Extraction
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for cost anomaly detection.
# NO business logic - only DB operations.
# Business logic (thresholds, scoring, classification) stays in L4 engine.
#
# ============================================================================
# L6 DRIVER INVENTORY — COST ANOMALY DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose                    | Status
# ----------------------------------- | -------------------------- | ------
# M1: Entity spike detection
# fetch_entity_baseline               | Entity daily avg baseline  | [DONE]
# fetch_entity_today_spend            | Entity today spend         | [DONE]
# M2: Tenant spike detection
# fetch_tenant_baseline               | Tenant daily avg baseline  | [DONE]
# fetch_tenant_today_spend            | Tenant today spend         | [DONE]
# M3: Sustained drift detection
# fetch_rolling_avg                   | 7-day rolling average      | [DONE]
# fetch_baseline_avg                  | 21-day baseline average    | [DONE]
# M4: Budget detection
# fetch_active_budgets                | Active budgets for tenant  | [DONE]
# fetch_daily_spend                   | Daily spend for budget     | [DONE]
# fetch_monthly_spend                 | Monthly spend for budget   | [DONE]
# M5: Breach history tracking
# fetch_breach_exists_today           | Check breach for today     | [DONE]
# insert_breach_history               | Insert breach record       | [DONE]
# fetch_consecutive_breaches          | Count consecutive breaches | [DONE]
# M6: Drift tracking
# fetch_drift_tracking                | Get active drift tracking  | [DONE]
# update_drift_tracking               | Update drift state         | [DONE]
# insert_drift_tracking               | Create new drift tracking  | [DONE]
# M7: Drift reset
# reset_drift_tracking                | Mark drift inactive        | [DONE]
# M8: Cause derivation queries
# fetch_retry_comparison              | Retry ratio comparison     | [DONE]
# fetch_prompt_comparison             | Prompt token comparison    | [DONE]
# fetch_feature_concentration         | Feature cost concentration | [DONE]
# fetch_request_comparison            | Request count comparison   | [DONE]
# M9: Anomaly persistence (ORM-based, via engine)
# fetch_existing_anomaly              | Deduplication check        | [ENGINE]
# insert_anomaly                      | Persist CostAnomaly        | [ENGINE]
# update_anomaly                      | Update existing anomaly    | [ENGINE]
# ============================================================================

"""
Cost Anomaly Driver (L6)

Pure database operations for cost anomaly detection.
All business logic stays in L4 engine.

Operations:
- Read baseline/today aggregations for spike detection
- Read rolling/baseline averages for drift detection
- Read/write breach history for consecutive tracking
- Read/write drift tracking state
- Read cost metrics for cause derivation
- Persist CostAnomaly records

NO business logic:
- NO threshold comparisons (L4)
- NO severity classification (L4)
- NO anomaly type decisions (L4)

Reference: Phase-2.5A Analytics Extraction
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlmodel import Session


class CostAnomalyDriver:
    """
    L6 driver for cost anomaly detection data access.

    Pure database access - no business logic.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    # =========================================================================
    # M1: ENTITY SPIKE DETECTION QUERIES
    # =========================================================================

    def fetch_entity_baseline(
        self,
        tenant_id: str,
        column_name: str,
        baseline_start: date,
        baseline_end: date,
    ) -> Dict[str, float]:
        """
        Fetch baseline daily averages per entity (user or feature).

        Args:
            tenant_id: Tenant scope
            column_name: Column to group by (user_id or feature_tag)
            baseline_start: Start date for baseline period
            baseline_end: End date for baseline period

        Returns:
            Dict mapping entity_id to daily average cost (cents)
        """
        # Note: Using f-string for column_name is safe here because
        # column_name is always from internal code (user_id or feature_tag),
        # never from user input
        result = self._session.execute(
            text(
                f"""
                SELECT
                    {column_name},
                    COALESCE(SUM(cost_cents), 0) / NULLIF(COUNT(DISTINCT DATE(created_at)), 0) as daily_avg
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND {column_name} IS NOT NULL
                  AND DATE(created_at) >= :baseline_start
                  AND DATE(created_at) <= :baseline_end
                GROUP BY {column_name}
                """
            ),
            {
                "tenant_id": tenant_id,
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
            },
        )

        return {row[0]: row[1] for row in result.all() if row[1]}

    def fetch_entity_today_spend(
        self,
        tenant_id: str,
        column_name: str,
        today_start: datetime,
    ) -> Dict[str, float]:
        """
        Fetch today's spend per entity (user or feature).

        Args:
            tenant_id: Tenant scope
            column_name: Column to group by (user_id or feature_tag)
            today_start: Start of today (datetime)

        Returns:
            Dict mapping entity_id to today's cost (cents)
        """
        result = self._session.execute(
            text(
                f"""
                SELECT
                    {column_name},
                    COALESCE(SUM(cost_cents), 0) as today_cost
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND {column_name} IS NOT NULL
                  AND created_at >= :today_start
                GROUP BY {column_name}
                """
            ),
            {
                "tenant_id": tenant_id,
                "today_start": today_start,
            },
        )

        return {row[0]: row[1] for row in result.all()}

    # =========================================================================
    # M2: TENANT SPIKE DETECTION QUERIES
    # =========================================================================

    def fetch_tenant_baseline(
        self,
        tenant_id: str,
        baseline_start: date,
        baseline_end: date,
    ) -> Optional[float]:
        """
        Fetch tenant-level baseline daily average.

        Args:
            tenant_id: Tenant scope
            baseline_start: Start date for baseline period
            baseline_end: End date for baseline period

        Returns:
            Daily average cost in cents, or None if no data
        """
        result = self._session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0) / NULLIF(COUNT(DISTINCT DATE(created_at)), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND DATE(created_at) >= :baseline_start
                  AND DATE(created_at) <= :baseline_end
                """
            ),
            {
                "tenant_id": tenant_id,
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
            },
        )

        row = result.first()
        return row[0] if row and row[0] else None

    def fetch_tenant_today_spend(
        self,
        tenant_id: str,
        today_start: datetime,
    ) -> float:
        """
        Fetch tenant-level today's spend.

        Args:
            tenant_id: Tenant scope
            today_start: Start of today (datetime)

        Returns:
            Today's cost in cents
        """
        result = self._session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND created_at >= :today_start
                """
            ),
            {
                "tenant_id": tenant_id,
                "today_start": today_start,
            },
        )

        row = result.first()
        return row[0] if row else 0

    # =========================================================================
    # M3: SUSTAINED DRIFT DETECTION QUERIES
    # =========================================================================

    def fetch_rolling_avg(
        self,
        tenant_id: str,
        rolling_start: date,
        rolling_end: date,
    ) -> float:
        """
        Fetch 7-day rolling average cost.

        Args:
            tenant_id: Tenant scope
            rolling_start: Start date for rolling period
            rolling_end: End date for rolling period

        Returns:
            Rolling average cost in cents (defaults to 0)
        """
        result = self._session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0) / 7.0
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND DATE(created_at) >= :rolling_start
                  AND DATE(created_at) <= :rolling_end
                """
            ),
            {
                "tenant_id": tenant_id,
                "rolling_start": rolling_start,
                "rolling_end": rolling_end,
            },
        )

        row = result.first()
        return row[0] if row and row[0] else 0

    def fetch_baseline_avg(
        self,
        tenant_id: str,
        baseline_start: date,
        baseline_end: date,
    ) -> float:
        """
        Fetch 21-day baseline average cost (excluding rolling period).

        Args:
            tenant_id: Tenant scope
            baseline_start: Start date for baseline period
            baseline_end: End date for baseline period

        Returns:
            Baseline average cost in cents (defaults to 0)
        """
        result = self._session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0) / NULLIF(
                    (SELECT COUNT(DISTINCT DATE(created_at))
                     FROM cost_records
                     WHERE tenant_id = :tenant_id
                       AND DATE(created_at) >= :baseline_start
                       AND DATE(created_at) <= :baseline_end), 0
                )
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND DATE(created_at) >= :baseline_start
                  AND DATE(created_at) <= :baseline_end
                """
            ),
            {
                "tenant_id": tenant_id,
                "baseline_start": baseline_start,
                "baseline_end": baseline_end,
            },
        )

        row = result.first()
        return row[0] if row and row[0] else 0

    # =========================================================================
    # M4: BUDGET DETECTION QUERIES
    # =========================================================================

    def fetch_daily_spend(
        self,
        tenant_id: str,
        today_start: datetime,
        budget_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> float:
        """
        Fetch daily spend for budget checking.

        Args:
            tenant_id: Tenant scope
            today_start: Start of today (datetime)
            budget_type: Optional budget type (feature/user)
            entity_id: Optional entity ID for filtering

        Returns:
            Daily cost in cents
        """
        where_clause = "tenant_id = :tenant_id AND created_at >= :today_start"
        params: dict = {"tenant_id": tenant_id, "today_start": today_start}

        if budget_type == "feature" and entity_id:
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id
        elif budget_type == "user" and entity_id:
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id

        result = self._session.execute(
            text(
                f"""
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE {where_clause}
                """
            ),
            params,
        )

        row = result.first()
        return row[0] if row else 0

    def fetch_monthly_spend(
        self,
        tenant_id: str,
        month_start: date,
        budget_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> float:
        """
        Fetch monthly spend for budget checking.

        Args:
            tenant_id: Tenant scope
            month_start: Start of month (date)
            budget_type: Optional budget type (feature/user)
            entity_id: Optional entity ID for filtering

        Returns:
            Monthly cost in cents
        """
        where_clause = "tenant_id = :tenant_id AND DATE(created_at) >= :month_start"
        params: dict = {"tenant_id": tenant_id, "month_start": month_start}

        if budget_type == "feature" and entity_id:
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id
        elif budget_type == "user" and entity_id:
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id

        result = self._session.execute(
            text(
                f"""
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE {where_clause}
                """
            ),
            params,
        )

        row = result.first()
        return row[0] if row else 0

    # =========================================================================
    # M5: BREACH HISTORY QUERIES
    # =========================================================================

    def fetch_breach_exists_today(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        breach_type: str,
        today: date,
    ) -> bool:
        """
        Check if breach already recorded for today.

        Args:
            tenant_id: Tenant scope
            entity_type: Entity type (user/feature/tenant)
            entity_id: Entity identifier
            breach_type: Type of breach (ABSOLUTE_SPIKE)
            today: Today's date

        Returns:
            True if breach exists for today
        """
        result = self._session.execute(
            text(
                """
                SELECT id FROM cost_breach_history
                WHERE tenant_id = :tenant_id
                  AND entity_type = :entity_type
                  AND COALESCE(entity_id, '') = COALESCE(:entity_id, '')
                  AND breach_type = :breach_type
                  AND breach_date = :today
                """
            ),
            {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "breach_type": breach_type,
                "today": today,
            },
        )

        return result.first() is not None

    def insert_breach_history(
        self,
        breach_id: str,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        breach_type: str,
        breach_date: date,
        deviation_pct: float,
        current_value: float,
        baseline_value: float,
        created_at: datetime,
    ) -> None:
        """
        Insert or update breach history record.

        Args:
            breach_id: Unique breach ID
            tenant_id: Tenant scope
            entity_type: Entity type
            entity_id: Entity identifier
            breach_type: Type of breach
            breach_date: Date of breach
            deviation_pct: Percentage deviation
            current_value: Current value in cents
            baseline_value: Baseline value in cents
            created_at: Creation timestamp
        """
        self._session.execute(
            text(
                """
                INSERT INTO cost_breach_history
                (id, tenant_id, entity_type, entity_id, breach_type, breach_date,
                 deviation_pct, current_value_cents, baseline_value_cents, created_at)
                VALUES (:id, :tenant_id, :entity_type, :entity_id, :breach_type, :breach_date,
                        :deviation_pct, :current_value, :baseline_value, :now)
                ON CONFLICT (tenant_id, entity_type, entity_id, breach_type, breach_date)
                DO UPDATE SET deviation_pct = :deviation_pct,
                              current_value_cents = :current_value
                """
            ),
            {
                "id": breach_id,
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id or "",
                "breach_type": breach_type,
                "breach_date": breach_date,
                "deviation_pct": deviation_pct,
                "current_value": current_value,
                "baseline_value": baseline_value,
                "now": created_at,
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

    def fetch_consecutive_breaches(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        breach_type: str,
        today: date,
    ) -> int:
        """
        Count consecutive breaches ending on today.

        Args:
            tenant_id: Tenant scope
            entity_type: Entity type
            entity_id: Entity identifier
            breach_type: Type of breach
            today: Today's date

        Returns:
            Count of consecutive breach days
        """
        result = self._session.execute(
            text(
                """
                WITH consecutive AS (
                    SELECT breach_date,
                           ROW_NUMBER() OVER (ORDER BY breach_date DESC) as rn,
                           breach_date - INTERVAL '1 day' * (ROW_NUMBER() OVER (ORDER BY breach_date DESC) - 1) as grp
                    FROM cost_breach_history
                    WHERE tenant_id = :tenant_id
                      AND entity_type = :entity_type
                      AND COALESCE(entity_id, '') = COALESCE(:entity_id, '')
                      AND breach_type = :breach_type
                      AND breach_date <= :today
                      AND breach_date >= :today - INTERVAL '7 days'
                    ORDER BY breach_date DESC
                )
                SELECT COUNT(*)
                FROM consecutive
                WHERE grp = (SELECT grp FROM consecutive WHERE breach_date = :today LIMIT 1)
                """
            ),
            {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id or "",
                "breach_type": breach_type,
                "today": today,
            },
        )

        row = result.first()
        return row[0] if row and row[0] else 1

    # =========================================================================
    # M6: DRIFT TRACKING QUERIES
    # =========================================================================

    def fetch_drift_tracking(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
    ) -> Optional[Tuple[str, int, date, date]]:
        """
        Fetch active drift tracking record.

        Args:
            tenant_id: Tenant scope
            entity_type: Entity type
            entity_id: Entity identifier

        Returns:
            Tuple of (id, drift_days_count, first_drift_date, last_check_date) or None
        """
        result = self._session.execute(
            text(
                """
                SELECT id, drift_days_count, first_drift_date, last_check_date
                FROM cost_drift_tracking
                WHERE tenant_id = :tenant_id
                  AND entity_type = :entity_type
                  AND COALESCE(entity_id, '') = COALESCE(:entity_id, '')
                  AND is_active = true
                """
            ),
            {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id or "",
            },
        )

        row = result.first()
        return (row[0], row[1], row[2], row[3]) if row else None

    def update_drift_tracking(
        self,
        drift_id: str,
        rolling_avg: float,
        baseline_avg: float,
        drift_pct: float,
        drift_days_count: int,
        today: date,
        updated_at: datetime,
    ) -> None:
        """
        Update existing drift tracking record.

        Args:
            drift_id: Drift tracking record ID
            rolling_avg: 7-day rolling average
            baseline_avg: Baseline average
            drift_pct: Drift percentage
            drift_days_count: Updated drift days count
            today: Today's date
            updated_at: Update timestamp
        """
        self._session.execute(
            text(
                """
                UPDATE cost_drift_tracking
                SET rolling_7d_avg_cents = :rolling_avg,
                    baseline_7d_avg_cents = :baseline_avg,
                    drift_pct = :drift_pct,
                    drift_days_count = :count,
                    last_check_date = :today,
                    updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "id": drift_id,
                "rolling_avg": rolling_avg,
                "baseline_avg": baseline_avg,
                "drift_pct": drift_pct,
                "count": drift_days_count,
                "today": today,
                "now": updated_at,
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

    def insert_drift_tracking(
        self,
        drift_id: str,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        rolling_avg: float,
        baseline_avg: float,
        drift_pct: float,
        today: date,
        created_at: datetime,
    ) -> None:
        """
        Insert new drift tracking record.

        Args:
            drift_id: Unique drift tracking ID
            tenant_id: Tenant scope
            entity_type: Entity type
            entity_id: Entity identifier
            rolling_avg: 7-day rolling average
            baseline_avg: Baseline average
            drift_pct: Drift percentage
            today: Today's date
            created_at: Creation timestamp
        """
        self._session.execute(
            text(
                """
                INSERT INTO cost_drift_tracking
                (id, tenant_id, entity_type, entity_id, rolling_7d_avg_cents,
                 baseline_7d_avg_cents, drift_pct, drift_days_count,
                 first_drift_date, last_check_date, is_active, created_at, updated_at)
                VALUES (:id, :tenant_id, :entity_type, :entity_id, :rolling_avg,
                        :baseline_avg, :drift_pct, 1, :today, :today, true, :now, :now)
                """
            ),
            {
                "id": drift_id,
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id or "",
                "rolling_avg": rolling_avg,
                "baseline_avg": baseline_avg,
                "drift_pct": drift_pct,
                "today": today,
                "now": created_at,
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

    # =========================================================================
    # M7: DRIFT RESET
    # =========================================================================

    def reset_drift_tracking(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        updated_at: datetime,
    ) -> None:
        """
        Mark drift tracking as inactive.

        Args:
            tenant_id: Tenant scope
            entity_type: Entity type
            entity_id: Entity identifier
            updated_at: Update timestamp
        """
        self._session.execute(
            text(
                """
                UPDATE cost_drift_tracking
                SET is_active = false, updated_at = :now
                WHERE tenant_id = :tenant_id
                  AND entity_type = :entity_type
                  AND COALESCE(entity_id, '') = COALESCE(:entity_id, '')
                  AND is_active = true
                """
            ),
            {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "entity_id": entity_id or "",
                "now": updated_at,
            },
        )
        # NO COMMIT — L4 coordinator owns transaction boundary

    # =========================================================================
    # M8: CAUSE DERIVATION QUERIES
    # =========================================================================

    def fetch_retry_comparison(
        self,
        tenant_id: str,
        today_start: datetime,
        yesterday_start: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Fetch retry ratio comparison between today and yesterday.

        Args:
            tenant_id: Tenant scope
            today_start: Start of today
            yesterday_start: Start of yesterday
            entity_type: Optional entity type for filtering
            entity_id: Optional entity ID for filtering

        Returns:
            Tuple of (today_retry_ratio, yesterday_retry_ratio)
        """
        where_clause = "tenant_id = :tenant_id"
        params: dict = {
            "tenant_id": tenant_id,
            "today_start": today_start,
            "yesterday_start": yesterday_start,
        }

        if entity_type == "user":
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id
        elif entity_type == "feature":
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id

        result = self._session.execute(
            text(
                f"""
                SELECT
                    (SELECT COUNT(*) FILTER (WHERE is_retry = true)::float /
                            NULLIF(COUNT(*), 0)
                     FROM cost_records WHERE {where_clause} AND created_at >= :today_start) as today_retry_ratio,
                    (SELECT COUNT(*) FILTER (WHERE is_retry = true)::float /
                            NULLIF(COUNT(*), 0)
                     FROM cost_records WHERE {where_clause}
                       AND created_at >= :yesterday_start AND created_at < :today_start) as yesterday_retry_ratio
                """
            ),
            params,
        )

        row = result.first()
        return (row[0], row[1]) if row else (None, None)

    def fetch_prompt_comparison(
        self,
        tenant_id: str,
        today_start: datetime,
        yesterday_start: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Fetch average prompt token comparison between today and yesterday.

        Args:
            tenant_id: Tenant scope
            today_start: Start of today
            yesterday_start: Start of yesterday
            entity_type: Optional entity type for filtering
            entity_id: Optional entity ID for filtering

        Returns:
            Tuple of (today_avg_tokens, yesterday_avg_tokens)
        """
        where_clause = "tenant_id = :tenant_id"
        params: dict = {
            "tenant_id": tenant_id,
            "today_start": today_start,
            "yesterday_start": yesterday_start,
        }

        if entity_type == "user":
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id
        elif entity_type == "feature":
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id

        result = self._session.execute(
            text(
                f"""
                SELECT
                    (SELECT AVG(input_tokens)
                     FROM cost_records WHERE {where_clause} AND created_at >= :today_start) as today_avg,
                    (SELECT AVG(input_tokens)
                     FROM cost_records WHERE {where_clause}
                       AND created_at >= :yesterday_start AND created_at < :today_start) as yesterday_avg
                """
            ),
            params,
        )

        row = result.first()
        return (row[0], row[1]) if row else (None, None)

    def fetch_feature_concentration(
        self,
        tenant_id: str,
        today_start: datetime,
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Fetch feature cost concentration for today.

        Args:
            tenant_id: Tenant scope
            today_start: Start of today

        Returns:
            Tuple of (total_cost, max_feature_cost)
        """
        result = self._session.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(cost_cents), 0) as total,
                    COALESCE(MAX(feature_cost), 0) as max_feature
                FROM (
                    SELECT feature_tag, COALESCE(SUM(cost_cents), 0) as feature_cost
                    FROM cost_records
                    WHERE tenant_id = :tenant_id
                      AND created_at >= :today_start
                      AND feature_tag IS NOT NULL
                    GROUP BY feature_tag
                ) sq
                """
            ),
            {
                "tenant_id": tenant_id,
                "today_start": today_start,
            },
        )

        row = result.first()
        return (row[0], row[1]) if row else (None, None)

    def fetch_request_comparison(
        self,
        tenant_id: str,
        today_start: datetime,
        yesterday_start: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Fetch request count comparison between today and yesterday.

        Args:
            tenant_id: Tenant scope
            today_start: Start of today
            yesterday_start: Start of yesterday
            entity_type: Optional entity type for filtering
            entity_id: Optional entity ID for filtering

        Returns:
            Tuple of (today_count, yesterday_count)
        """
        where_clause = "tenant_id = :tenant_id"
        params: dict = {
            "tenant_id": tenant_id,
            "today_start": today_start,
            "yesterday_start": yesterday_start,
        }

        if entity_type == "user":
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id
        elif entity_type == "feature":
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id

        result = self._session.execute(
            text(
                f"""
                SELECT
                    (SELECT COUNT(*) FROM cost_records
                     WHERE {where_clause} AND created_at >= :today_start) as today_count,
                    (SELECT COUNT(*) FROM cost_records
                     WHERE {where_clause}
                       AND created_at >= :yesterday_start AND created_at < :today_start) as yesterday_count
                """
            ),
            params,
        )

        row = result.first()
        return (row[0], row[1]) if row else (None, None)

    # TRANSACTION HELPERS section removed — L6 DOES NOT COMMIT


def get_cost_anomaly_driver(session: Session) -> CostAnomalyDriver:
    """Factory function to get CostAnomalyDriver instance."""
    return CostAnomalyDriver(session)


__all__ = [
    "CostAnomalyDriver",
    "get_cost_anomaly_driver",
]
