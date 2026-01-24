# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: none (QUARANTINED)
#   Execution: none
# Role: QUARANTINED - Cost anomaly decision logic (pending domain reassignment)
# Callers: tests, future background job
# Allowed Imports: none (QUARANTINED)
# Forbidden Imports: all (QUARANTINED)
# Reference: PIN-240, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# STATUS: QUARANTINED
# ORIGINAL LOCATION: logs/engines/cost_anomaly_detector.py
# REASON: Contains decision logic ("Was this anomalous?") which violates
#         Logs domain boundary. Logs is a FACT EMISSION domain, not a DECISION domain.
# ACTION: Reassign to analytics or activity domain, or archive.
#
# WARNING: If this logic is wrong, ALL products break.

"""
M29 Cost Anomaly Detector - Aligned Rules

Category 4 Anomaly Rules:
1. Absolute spike: daily_spend > baseline * 1.4 FOR 2 consecutive daily intervals
2. Sustained drift: 7d rolling avg > baseline_7d * 1.25 FOR >= 3 days
3. Severity: LOW +15-25%, MEDIUM +25-40%, HIGH >40%

THE INVARIANT: Every anomaly triggers an action, not a chart.

Detection Types:
- ABSOLUTE_SPIKE: Consecutive daily breaches (user, feature, tenant)
- SUSTAINED_DRIFT: Rolling average above baseline for multiple days
- BUDGET_WARNING: Projected overrun (warn threshold)
- BUDGET_EXCEEDED: Hard stop (budget exhausted)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional

from sqlalchemy import text
from sqlmodel import Session, select

from app.db import (
    CostAnomaly,
    CostBudget,
    utc_now,
)
from app.services.governance.cross_domain import create_incident_from_cost_anomaly_sync

logger = logging.getLogger("nova.cost_anomaly_detector")


# =============================================================================
# ENUMS
# =============================================================================


class AnomalyType(str, Enum):
    """Cost anomaly types - minimal set."""

    ABSOLUTE_SPIKE = "ABSOLUTE_SPIKE"  # 1.4x for 2 consecutive intervals
    SUSTAINED_DRIFT = "SUSTAINED_DRIFT"  # 1.25x for 3+ days
    BUDGET_WARNING = "BUDGET_WARNING"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


class AnomalySeverity(str, Enum):
    """Aligned severity bands per plan."""

    LOW = "LOW"  # +15% to +25%
    MEDIUM = "MEDIUM"  # +25% to +40%
    HIGH = "HIGH"  # >40%


class DerivedCause(str, Enum):
    """Deterministic cause derivation."""

    RETRY_LOOP = "RETRY_LOOP"  # retries/request increased
    PROMPT_GROWTH = "PROMPT_GROWTH"  # avg prompt tokens increased
    FEATURE_SURGE = "FEATURE_SURGE"  # cost concentrated in 1 feature
    TRAFFIC_GROWTH = "TRAFFIC_GROWTH"  # requests up without retries/prompt
    UNKNOWN = "UNKNOWN"  # fallback


# =============================================================================
# THRESHOLDS (PLAN-ALIGNED)
# =============================================================================


# Absolute spike: 1.4x baseline (40% increase)
ABSOLUTE_SPIKE_THRESHOLD = 1.40

# Consecutive intervals required for absolute spike
CONSECUTIVE_INTERVALS_REQUIRED = 2

# Sustained drift: 1.25x baseline (25% increase)
SUSTAINED_DRIFT_THRESHOLD = 1.25

# Days of drift required for sustained drift anomaly
DRIFT_DAYS_REQUIRED = 3

# Severity band thresholds (percentage deviation)
SEVERITY_BANDS = {
    "LOW": (15, 25),  # +15% to +25%
    "MEDIUM": (25, 40),  # +25% to +40%
    "HIGH": (40, float("inf")),  # >40%
}


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class DetectedAnomaly:
    """A detected cost anomaly."""

    anomaly_type: AnomalyType
    severity: AnomalySeverity
    entity_type: str  # "user", "feature", "tenant"
    entity_id: Optional[str]
    current_value_cents: float
    expected_value_cents: float
    deviation_pct: float
    message: str
    breach_count: int = 1
    derived_cause: DerivedCause = DerivedCause.UNKNOWN
    metadata: dict = field(default_factory=dict)


# =============================================================================
# SEVERITY CLASSIFIER
# =============================================================================


def classify_severity(deviation_pct: float) -> AnomalySeverity:
    """
    Classify severity based on percentage deviation.

    Plan alignment:
    - LOW: +15% to +25%
    - MEDIUM: +25% to +40%
    - HIGH: >40%

    Note: Below 15% is not an anomaly.
    """
    if deviation_pct >= 40:
        return AnomalySeverity.HIGH
    elif deviation_pct >= 25:
        return AnomalySeverity.MEDIUM
    elif deviation_pct >= 15:
        return AnomalySeverity.LOW
    else:
        # Below threshold - shouldn't be called, but return LOW as safe fallback
        return AnomalySeverity.LOW


# =============================================================================
# DETECTOR CLASS
# =============================================================================


class CostAnomalyDetector:
    """
    Detects cost anomalies with aligned rules.

    Rules:
    1. ABSOLUTE_SPIKE: daily > baseline * 1.4 for 2 consecutive intervals
    2. SUSTAINED_DRIFT: 7d rolling avg > baseline_7d * 1.25 for >= 3 days
    3. BUDGET_WARNING: spend > warn_threshold_pct of budget
    4. BUDGET_EXCEEDED: spend >= 100% of budget
    """

    def __init__(self, session: Session):
        self.session = session
        self.today = date.today()

    async def detect_all(self, tenant_id: str) -> List[DetectedAnomaly]:
        """Run all anomaly detection checks for a tenant."""
        anomalies = []

        # Detect absolute spikes (user, feature, tenant level)
        spike_anomalies = await self.detect_absolute_spikes(tenant_id)
        anomalies.extend(spike_anomalies)

        # Detect sustained drift
        drift_anomalies = await self.detect_sustained_drift(tenant_id)
        anomalies.extend(drift_anomalies)

        # Detect budget issues (unchanged logic, different thresholds)
        budget_anomalies = await self.detect_budget_issues(tenant_id)
        anomalies.extend(budget_anomalies)

        return anomalies

    # =========================================================================
    # ABSOLUTE SPIKE DETECTION
    # =========================================================================

    async def detect_absolute_spikes(
        self,
        tenant_id: str,
        lookback_days: int = 14,
    ) -> List[DetectedAnomaly]:
        """
        Detect absolute spikes with consecutive interval logic.

        Algorithm:
        1. Get 14-day baseline (excluding last 2 days)
        2. Get today's spend per entity
        3. If today > baseline * 1.4 → record breach
        4. If 2 consecutive breaches exist → fire anomaly
        """
        anomalies = []

        # Get user spikes
        user_anomalies = await self._detect_entity_spikes(tenant_id, "user", "user_id", lookback_days)
        anomalies.extend(user_anomalies)

        # Get feature spikes
        feature_anomalies = await self._detect_entity_spikes(tenant_id, "feature", "feature_tag", lookback_days)
        anomalies.extend(feature_anomalies)

        # Get tenant-level spikes
        tenant_anomalies = await self._detect_tenant_spike(tenant_id, lookback_days)
        anomalies.extend(tenant_anomalies)

        return anomalies

    async def _detect_entity_spikes(
        self,
        tenant_id: str,
        entity_type: str,
        column_name: str,
        lookback_days: int,
    ) -> List[DetectedAnomaly]:
        """Detect spikes for a specific entity type (user or feature)."""
        anomalies = []

        # Baseline: average daily spend over lookback period (excluding last 2 days)
        baseline_start = self.today - timedelta(days=lookback_days)
        baseline_end = self.today - timedelta(days=2)

        # Get entity baselines
        baseline_result = self.session.execute(
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
        ).all()

        entity_baselines = {row[0]: row[1] for row in baseline_result if row[1]}

        # Get today's spend
        today_start = datetime.combine(self.today, datetime.min.time())
        today_result = self.session.execute(
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
            {"tenant_id": tenant_id, "today_start": today_start},
        ).all()

        for row in today_result:
            entity_id = row[0]
            today_cost = row[1]
            baseline = entity_baselines.get(entity_id)

            if not baseline or baseline <= 0:
                continue

            ratio = today_cost / baseline
            deviation_pct = (ratio - 1) * 100

            # Check if breaching threshold (1.4x = 40% deviation)
            if ratio >= ABSOLUTE_SPIKE_THRESHOLD:
                # Record this breach
                breach_count = self._record_breach_and_get_consecutive_count(
                    tenant_id=tenant_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    breach_type="ABSOLUTE_SPIKE",
                    deviation_pct=deviation_pct,
                    current_value=today_cost,
                    baseline_value=baseline,
                )

                # Only fire anomaly if we have 2+ consecutive breaches
                if breach_count >= CONSECUTIVE_INTERVALS_REQUIRED:
                    severity = classify_severity(deviation_pct)
                    derived_cause = self._derive_cause(tenant_id, entity_type, entity_id)

                    anomalies.append(
                        DetectedAnomaly(
                            anomaly_type=AnomalyType.ABSOLUTE_SPIKE,
                            severity=severity,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            current_value_cents=today_cost,
                            expected_value_cents=baseline,
                            deviation_pct=deviation_pct,
                            message=self._format_spike_message(entity_type, entity_id, deviation_pct, breach_count),
                            breach_count=breach_count,
                            derived_cause=derived_cause,
                            metadata={
                                "lookback_days": lookback_days,
                                "baseline_daily_avg": baseline,
                                "consecutive_breaches": breach_count,
                            },
                        )
                    )
            else:
                # Not breaching - reset consecutive count
                self._reset_breach_history(tenant_id, entity_type, entity_id, "ABSOLUTE_SPIKE")

        return anomalies

    async def _detect_tenant_spike(
        self,
        tenant_id: str,
        lookback_days: int,
    ) -> List[DetectedAnomaly]:
        """Detect tenant-level absolute spikes."""
        anomalies = []

        baseline_start = self.today - timedelta(days=lookback_days)
        baseline_end = self.today - timedelta(days=2)

        # Get tenant baseline
        baseline_result = self.session.execute(
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
        ).first()

        baseline = baseline_result[0] if baseline_result and baseline_result[0] else 0

        if baseline <= 0:
            return anomalies

        # Get today's spend
        today_start = datetime.combine(self.today, datetime.min.time())
        today_result = self.session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND created_at >= :today_start
            """
            ),
            {"tenant_id": tenant_id, "today_start": today_start},
        ).first()

        today_cost = today_result[0] if today_result else 0
        ratio = today_cost / baseline if baseline > 0 else 0
        deviation_pct = (ratio - 1) * 100

        if ratio >= ABSOLUTE_SPIKE_THRESHOLD:
            breach_count = self._record_breach_and_get_consecutive_count(
                tenant_id=tenant_id,
                entity_type="tenant",
                entity_id=tenant_id,
                breach_type="ABSOLUTE_SPIKE",
                deviation_pct=deviation_pct,
                current_value=today_cost,
                baseline_value=baseline,
            )

            if breach_count >= CONSECUTIVE_INTERVALS_REQUIRED:
                severity = classify_severity(deviation_pct)
                derived_cause = self._derive_cause(tenant_id, "tenant", tenant_id)

                anomalies.append(
                    DetectedAnomaly(
                        anomaly_type=AnomalyType.ABSOLUTE_SPIKE,
                        severity=severity,
                        entity_type="tenant",
                        entity_id=tenant_id,
                        current_value_cents=today_cost,
                        expected_value_cents=baseline,
                        deviation_pct=deviation_pct,
                        message=self._format_spike_message("tenant", tenant_id, deviation_pct, breach_count),
                        breach_count=breach_count,
                        derived_cause=derived_cause,
                        metadata={
                            "lookback_days": lookback_days,
                            "baseline_daily_avg": baseline,
                            "consecutive_breaches": breach_count,
                        },
                    )
                )
        else:
            self._reset_breach_history(tenant_id, "tenant", tenant_id, "ABSOLUTE_SPIKE")

        return anomalies

    # =========================================================================
    # SUSTAINED DRIFT DETECTION
    # =========================================================================

    async def detect_sustained_drift(
        self,
        tenant_id: str,
    ) -> List[DetectedAnomaly]:
        """
        Detect sustained drift anomalies.

        Algorithm:
        1. Get 7-day rolling average
        2. Compare to 21-day baseline (days 8-28 ago)
        3. If rolling > baseline * 1.25 → increment drift counter
        4. If drift counter >= 3 days → fire anomaly
        """
        anomalies = []

        # Calculate date ranges
        rolling_end = self.today
        rolling_start = self.today - timedelta(days=6)  # Last 7 days including today
        baseline_start = self.today - timedelta(days=28)
        baseline_end = self.today - timedelta(days=8)  # Exclude recent 7 days

        # Get rolling 7-day average
        rolling_result = self.session.execute(
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
        ).first()

        rolling_avg = rolling_result[0] if rolling_result and rolling_result[0] else 0

        # Get baseline (21-day period before rolling window)
        baseline_result = self.session.execute(
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
        ).first()

        baseline_avg = baseline_result[0] if baseline_result and baseline_result[0] else 0

        if baseline_avg <= 0:
            return anomalies

        ratio = rolling_avg / baseline_avg
        drift_pct = (ratio - 1) * 100

        if ratio >= SUSTAINED_DRIFT_THRESHOLD:
            # Update drift tracking
            drift_days = self._update_drift_tracking(
                tenant_id=tenant_id,
                entity_type="tenant",
                entity_id=tenant_id,
                rolling_avg=rolling_avg,
                baseline_avg=baseline_avg,
                drift_pct=drift_pct,
            )

            if drift_days >= DRIFT_DAYS_REQUIRED:
                severity = classify_severity(drift_pct)
                derived_cause = self._derive_cause(tenant_id, "tenant", tenant_id)

                anomalies.append(
                    DetectedAnomaly(
                        anomaly_type=AnomalyType.SUSTAINED_DRIFT,
                        severity=severity,
                        entity_type="tenant",
                        entity_id=tenant_id,
                        current_value_cents=rolling_avg,
                        expected_value_cents=baseline_avg,
                        deviation_pct=drift_pct,
                        message=f"Sustained drift detected: {drift_pct:.1f}% above baseline for {drift_days} days",
                        breach_count=drift_days,
                        derived_cause=derived_cause,
                        metadata={
                            "rolling_7d_avg": rolling_avg,
                            "baseline_avg": baseline_avg,
                            "drift_days": drift_days,
                        },
                    )
                )
        else:
            # Reset drift tracking if no longer drifting
            self._reset_drift_tracking(tenant_id, "tenant", tenant_id)

        return anomalies

    # =========================================================================
    # BUDGET DETECTION (unchanged logic)
    # =========================================================================

    async def detect_budget_issues(self, tenant_id: str) -> List[DetectedAnomaly]:
        """Detect budget warnings and exceeded budgets."""
        anomalies = []

        today_start = datetime.combine(self.today, datetime.min.time())
        month_start = self.today.replace(day=1)

        budgets = self.session.exec(
            select(CostBudget).where(
                CostBudget.tenant_id == tenant_id,
                CostBudget.is_active == True,
            )
        ).all()

        for budget in budgets:
            where_clause = "tenant_id = :tenant_id"
            params: dict = {"tenant_id": tenant_id}

            if budget.budget_type == "feature" and budget.entity_id:
                where_clause += " AND feature_tag = :entity_id"
                params["entity_id"] = budget.entity_id
            elif budget.budget_type == "user" and budget.entity_id:
                where_clause += " AND user_id = :entity_id"
                params["entity_id"] = budget.entity_id

            # Check daily budget
            if budget.daily_limit_cents:
                params["today_start"] = today_start
                daily_spend = self.session.execute(
                    text(
                        f"""
                        SELECT COALESCE(SUM(cost_cents), 0)
                        FROM cost_records
                        WHERE {where_clause} AND created_at >= :today_start
                    """
                    ),
                    params,
                ).first()

                daily_cost = daily_spend[0] if daily_spend else 0
                anomaly = self._check_budget_threshold(
                    budget_type=budget.budget_type,
                    entity_id=budget.entity_id,
                    period="daily",
                    current_cents=daily_cost,
                    limit_cents=budget.daily_limit_cents,
                    warn_threshold_pct=budget.warn_threshold_pct,
                )
                if anomaly:
                    anomalies.append(anomaly)

            # Check monthly budget
            if budget.monthly_limit_cents:
                params["month_start"] = month_start
                monthly_spend = self.session.execute(
                    text(
                        f"""
                        SELECT COALESCE(SUM(cost_cents), 0)
                        FROM cost_records
                        WHERE {where_clause} AND DATE(created_at) >= :month_start
                    """
                    ),
                    params,
                ).first()

                monthly_cost = monthly_spend[0] if monthly_spend else 0
                anomaly = self._check_budget_threshold(
                    budget_type=budget.budget_type,
                    entity_id=budget.entity_id,
                    period="monthly",
                    current_cents=monthly_cost,
                    limit_cents=budget.monthly_limit_cents,
                    warn_threshold_pct=budget.warn_threshold_pct,
                )
                if anomaly:
                    anomalies.append(anomaly)

        return anomalies

    def _check_budget_threshold(
        self,
        budget_type: str,
        entity_id: Optional[str],
        period: str,
        current_cents: float,
        limit_cents: int,
        warn_threshold_pct: int,
    ) -> Optional[DetectedAnomaly]:
        """Check if budget threshold is breached."""
        if limit_cents <= 0:
            return None

        usage_pct = current_cents / limit_cents * 100
        deviation_pct = usage_pct - 100  # Deviation from 100%

        entity_desc = f"{budget_type}" if not entity_id else f"{budget_type} '{entity_id}'"

        if usage_pct >= 100:
            return DetectedAnomaly(
                anomaly_type=AnomalyType.BUDGET_EXCEEDED,
                severity=AnomalySeverity.HIGH,  # Budget exceeded is always HIGH
                entity_type=budget_type,
                entity_id=entity_id,
                current_value_cents=current_cents,
                expected_value_cents=float(limit_cents),
                deviation_pct=usage_pct,
                message=f"{period.title()} budget EXCEEDED for {entity_desc}: {usage_pct:.1f}%",
                derived_cause=DerivedCause.UNKNOWN,
                metadata={"period": period, "limit_cents": limit_cents},
            )
        elif usage_pct >= warn_threshold_pct:
            severity = AnomalySeverity.MEDIUM if usage_pct < 90 else AnomalySeverity.HIGH
            return DetectedAnomaly(
                anomaly_type=AnomalyType.BUDGET_WARNING,
                severity=severity,
                entity_type=budget_type,
                entity_id=entity_id,
                current_value_cents=current_cents,
                expected_value_cents=float(limit_cents),
                deviation_pct=usage_pct,
                message=f"{period.title()} budget WARNING for {entity_desc}: {usage_pct:.1f}%",
                derived_cause=DerivedCause.UNKNOWN,
                metadata={"period": period, "limit_cents": limit_cents, "warn_threshold_pct": warn_threshold_pct},
            )

        return None

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _record_breach_and_get_consecutive_count(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        breach_type: str,
        deviation_pct: float,
        current_value: float,
        baseline_value: float,
    ) -> int:
        """Record a breach and return the consecutive breach count."""
        # Check if breach already recorded for today
        existing = self.session.execute(
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
                "today": self.today,
            },
        ).first()

        if not existing:
            # Insert new breach record
            breach_id = f"bh_{uuid.uuid4().hex[:16]}"
            self.session.execute(
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
                    "breach_date": self.today,
                    "deviation_pct": deviation_pct,
                    "current_value": current_value,
                    "baseline_value": baseline_value,
                    "now": utc_now(),
                },
            )
            self.session.commit()

        # Count consecutive breaches (look at last N days)
        consecutive_count = self.session.execute(
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
                "today": self.today,
            },
        ).first()

        return consecutive_count[0] if consecutive_count and consecutive_count[0] else 1

    def _reset_breach_history(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        breach_type: str,
    ) -> None:
        """Reset breach history when entity is no longer breaching."""
        # We don't delete old records, just don't add today
        # The consecutive count logic handles gaps automatically
        pass

    def _update_drift_tracking(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        rolling_avg: float,
        baseline_avg: float,
        drift_pct: float,
    ) -> int:
        """Update drift tracking and return days count."""
        existing = self.session.execute(
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
        ).first()

        if existing:
            # Check if last_check_date was yesterday (continuous drift)
            last_check = existing[3]
            expected_prev = self.today - timedelta(days=1)

            if last_check == expected_prev:
                # Continuous drift - increment
                new_count = existing[1] + 1
            else:
                # Gap in drift - reset counter but keep tracking
                new_count = 1

            self.session.execute(
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
                    "id": existing[0],
                    "rolling_avg": rolling_avg,
                    "baseline_avg": baseline_avg,
                    "drift_pct": drift_pct,
                    "count": new_count,
                    "today": self.today,
                    "now": utc_now(),
                },
            )
            self.session.commit()
            return int(new_count)
        else:
            # New drift tracking
            drift_id = f"dt_{uuid.uuid4().hex[:16]}"
            self.session.execute(
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
                    "today": self.today,
                    "now": utc_now(),
                },
            )
            self.session.commit()
            return 1

    def _reset_drift_tracking(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
    ) -> None:
        """Mark drift tracking as inactive."""
        self.session.execute(
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
                "now": utc_now(),
            },
        )
        self.session.commit()

    def _derive_cause(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str,
    ) -> DerivedCause:
        """
        Derive the cause of a cost anomaly.

        Rules (deterministic, no ML):
        - RETRY_LOOP: retries/request increased > 50%
        - PROMPT_GROWTH: avg prompt tokens increased > 30%
        - FEATURE_SURGE: cost concentrated in 1 feature (>60%)
        - TRAFFIC_GROWTH: requests up without retry/prompt growth
        - UNKNOWN: fallback
        """
        today_start = datetime.combine(self.today, datetime.min.time())
        yesterday_start = datetime.combine(self.today - timedelta(days=1), datetime.min.time())

        # Compare today vs yesterday metrics
        where_clause = "tenant_id = :tenant_id"
        params: dict = {"tenant_id": tenant_id, "today_start": today_start, "yesterday_start": yesterday_start}

        if entity_type == "user":
            where_clause += " AND user_id = :entity_id"
            params["entity_id"] = entity_id
        elif entity_type == "feature":
            where_clause += " AND feature_tag = :entity_id"
            params["entity_id"] = entity_id

        # Get retry ratio comparison
        retry_result = self.session.execute(
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
        ).first()

        if retry_result and retry_result[0] and retry_result[1]:
            if retry_result[1] > 0 and retry_result[0] / retry_result[1] > 1.5:
                return DerivedCause.RETRY_LOOP

        # Get avg prompt tokens comparison
        prompt_result = self.session.execute(
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
        ).first()

        if prompt_result and prompt_result[0] and prompt_result[1]:
            if prompt_result[1] > 0 and prompt_result[0] / prompt_result[1] > 1.3:
                return DerivedCause.PROMPT_GROWTH

        # Check feature concentration (only for tenant-level)
        if entity_type == "tenant":
            feature_result = self.session.execute(
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
                params,
            ).first()

            if feature_result and feature_result[0] and feature_result[1]:
                if feature_result[1] / feature_result[0] > 0.6:
                    return DerivedCause.FEATURE_SURGE

        # Check request growth without other factors
        request_result = self.session.execute(
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
        ).first()

        if request_result and request_result[0] and request_result[1]:
            if request_result[1] > 0 and request_result[0] / request_result[1] > 1.3:
                return DerivedCause.TRAFFIC_GROWTH

        return DerivedCause.UNKNOWN

    def _format_spike_message(
        self,
        entity_type: str,
        entity_id: str,
        deviation_pct: float,
        breach_count: int,
    ) -> str:
        """Format human-readable spike message."""
        entity_desc = f"{entity_type.title()} {entity_id}"
        return (
            f"{entity_desc} spending {deviation_pct:.1f}% above baseline "
            f"for {breach_count} consecutive day{'s' if breach_count > 1 else ''}"
        )

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    async def persist_anomalies(
        self,
        tenant_id: str,
        anomalies: List[DetectedAnomaly],
    ) -> List[CostAnomaly]:
        """Persist detected anomalies to database."""
        created = []

        for anomaly in anomalies:
            today_start = datetime.combine(self.today, datetime.min.time())

            # Check for existing similar anomaly today
            existing = self.session.exec(
                select(CostAnomaly).where(
                    CostAnomaly.tenant_id == tenant_id,
                    CostAnomaly.anomaly_type == anomaly.anomaly_type.value,
                    CostAnomaly.entity_type == anomaly.entity_type,
                    CostAnomaly.entity_id == anomaly.entity_id,
                    CostAnomaly.detected_at >= today_start,
                    CostAnomaly.resolved == False,
                )
            ).first()

            if existing:
                # Update existing
                existing.current_value_cents = anomaly.current_value_cents
                existing.deviation_pct = anomaly.deviation_pct
                existing.severity = anomaly.severity.value
                existing.message = anomaly.message
                existing.breach_count = anomaly.breach_count
                existing.derived_cause = anomaly.derived_cause.value
                existing.metadata_json = anomaly.metadata
                self.session.add(existing)
                created.append(existing)
            else:
                # Create new
                cost_anomaly = CostAnomaly(
                    tenant_id=tenant_id,
                    anomaly_type=anomaly.anomaly_type.value,
                    severity=anomaly.severity.value,
                    entity_type=anomaly.entity_type,
                    entity_id=anomaly.entity_id,
                    current_value_cents=anomaly.current_value_cents,
                    expected_value_cents=anomaly.expected_value_cents,
                    deviation_pct=anomaly.deviation_pct,
                    threshold_pct=ABSOLUTE_SPIKE_THRESHOLD * 100
                    if anomaly.anomaly_type == AnomalyType.ABSOLUTE_SPIKE
                    else SUSTAINED_DRIFT_THRESHOLD * 100,
                    message=anomaly.message,
                    breach_count=anomaly.breach_count,
                    derived_cause=anomaly.derived_cause.value,
                    metadata_json=anomaly.metadata,
                )
                self.session.add(cost_anomaly)
                created.append(cost_anomaly)

        self.session.commit()

        for ca in created:
            self.session.refresh(ca)

        logger.info(f"Persisted {len(created)} anomalies for tenant {tenant_id}")
        return created


# =============================================================================
# ENTRY POINTS
# =============================================================================


async def run_anomaly_detection(session: Session, tenant_id: str) -> List[CostAnomaly]:
    """Run anomaly detection and persist results."""
    detector = CostAnomalyDetector(session)

    anomalies = await detector.detect_all(tenant_id)

    if not anomalies:
        logger.debug(f"No anomalies detected for tenant {tenant_id}")
        return []

    persisted = await detector.persist_anomalies(tenant_id, anomalies)
    logger.info(f"Detected and persisted {len(persisted)} anomalies for tenant {tenant_id}")

    return persisted


async def run_anomaly_detection_with_governance(
    session: Session,
    tenant_id: str,
) -> dict:
    """
    Run anomaly detection AND create incidents for HIGH anomalies.

    MANDATORY GOVERNANCE: Every HIGH+ anomaly creates an incident or crashes.
    There is no optional dispatcher. Governance is not negotiable.

    Returns:
        {
            "detected": [CostAnomaly, ...],
            "incidents_created": [{"anomaly_id": str, "incident_id": str}, ...],
        }

    Raises:
        GovernanceError: If incident creation fails (mandatory)
    """
    persisted = await run_anomaly_detection(session, tenant_id)

    if not persisted:
        return {"detected": [], "incidents_created": []}

    incidents_created = []

    # Only HIGH severity anomalies create incidents (no CRITICAL - severity bands changed)
    high_anomalies = [a for a in persisted if a.severity == "HIGH"]

    # MANDATORY: Every HIGH anomaly creates an incident or raises GovernanceError
    for cost_anomaly in high_anomalies:
        incident_id = create_incident_from_cost_anomaly_sync(
            session=session,
            tenant_id=tenant_id,
            anomaly_id=cost_anomaly.id,
            anomaly_type=cost_anomaly.anomaly_type,
            severity=cost_anomaly.severity,
            current_value_cents=int(cost_anomaly.current_value_cents),
            expected_value_cents=int(cost_anomaly.expected_value_cents),
            entity_type=cost_anomaly.entity_type,
            entity_id=cost_anomaly.entity_id,
        )

        incidents_created.append(
            {
                "anomaly_id": cost_anomaly.id,
                "incident_id": incident_id,
            }
        )

        logger.info(
            f"[GOVERNANCE] Created incident {incident_id} from cost anomaly {cost_anomaly.id}"
        )

    return {
        "detected": persisted,
        "incidents_created": incidents_created,
    }
