"""
M26 Cost Anomaly Detector

Core Principle:
Every anomaly must trigger an action, not a chart.

This detector runs periodically to identify:
- USER_SPIKE: One user behaving abnormally
- FEATURE_SPIKE: Feature cost exploding
- BUDGET_WARNING: Projected overrun (warn threshold)
- BUDGET_EXCEEDED: Hard stop (budget exhausted)

When an anomaly is detected, it's:
1. Written to cost_anomalies table
2. Escalated to M25 loop as an incident (if HIGH/CRITICAL)
"""
from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, List
from enum import Enum

from sqlalchemy import text
from sqlmodel import Session, select

from app.db import (
    CostAnomaly,
    CostBudget,
    FeatureTag,
    utc_now,
)

logger = logging.getLogger("nova.cost_anomaly_detector")


class AnomalyType(str, Enum):
    """Cost anomaly types. Keep it small - anything more early = noise."""
    USER_SPIKE = "USER_SPIKE"
    FEATURE_SPIKE = "FEATURE_SPIKE"
    BUDGET_WARNING = "BUDGET_WARNING"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""
    LOW = "LOW"          # < 200% deviation
    MEDIUM = "MEDIUM"    # 200-300% deviation
    HIGH = "HIGH"        # 300-500% deviation
    CRITICAL = "CRITICAL"  # > 500% deviation or budget exceeded


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
    metadata: dict


class CostAnomalyDetector:
    """
    Detects cost anomalies across users, features, and budgets.

    Detection logic:
    1. USER_SPIKE: User spending > 2x their 7-day average
    2. FEATURE_SPIKE: Feature spending > 2x its 7-day average
    3. BUDGET_WARNING: Spend > warn_threshold_pct of budget
    4. BUDGET_EXCEEDED: Spend >= 100% of budget

    Severity classification:
    - LOW: 150-200% of expected
    - MEDIUM: 200-300% of expected
    - HIGH: 300-500% of expected
    - CRITICAL: >500% or budget exceeded
    """

    def __init__(self, session: Session):
        self.session = session

    async def detect_all(self, tenant_id: str) -> List[DetectedAnomaly]:
        """Run all anomaly detection checks for a tenant."""
        anomalies = []

        # Detect user spikes
        user_anomalies = await self.detect_user_spikes(tenant_id)
        anomalies.extend(user_anomalies)

        # Detect feature spikes
        feature_anomalies = await self.detect_feature_spikes(tenant_id)
        anomalies.extend(feature_anomalies)

        # Detect budget issues
        budget_anomalies = await self.detect_budget_issues(tenant_id)
        anomalies.extend(budget_anomalies)

        return anomalies

    async def detect_user_spikes(
        self,
        tenant_id: str,
        lookback_days: int = 7,
        deviation_threshold: float = 2.0,
    ) -> List[DetectedAnomaly]:
        """
        Detect users spending abnormally.

        Algorithm:
        1. Get each user's 7-day average daily spend
        2. Get today's spend
        3. If today > 2x average → spike detected
        """
        anomalies = []

        # Get historical user averages (7-day)
        lookback_start = utc_now() - timedelta(days=lookback_days)
        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get all users with spending in lookback period
        user_history = self.session.execute(
            text("""
                SELECT
                    user_id,
                    SUM(cost_cents) / :days as daily_avg
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND user_id IS NOT NULL
                  AND created_at >= :lookback_start
                  AND created_at < :today_start
                GROUP BY user_id
            """),
            {
                "tenant_id": tenant_id,
                "days": lookback_days,
                "lookback_start": lookback_start,
                "today_start": today_start,
            }
        ).all()

        user_avgs = {row[0]: row[1] for row in user_history}

        # Get today's spend per user
        today_spend = self.session.execute(
            text("""
                SELECT
                    user_id,
                    SUM(cost_cents) as today_cost
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND user_id IS NOT NULL
                  AND created_at >= :today_start
                GROUP BY user_id
            """),
            {"tenant_id": tenant_id, "today_start": today_start}
        ).all()

        for row in today_spend:
            user_id = row[0]
            today_cost = row[1]
            avg_cost = user_avgs.get(user_id, 0)

            # Skip if no history (new user)
            if avg_cost <= 0:
                continue

            deviation = today_cost / avg_cost

            if deviation >= deviation_threshold:
                severity = self._classify_severity(deviation * 100)

                anomalies.append(DetectedAnomaly(
                    anomaly_type=AnomalyType.USER_SPIKE,
                    severity=severity,
                    entity_type="user",
                    entity_id=user_id,
                    current_value_cents=today_cost,
                    expected_value_cents=avg_cost,
                    deviation_pct=deviation * 100,
                    message=f"User {user_id} spending {deviation:.1f}x their daily average (${today_cost/100:.2f} vs ${avg_cost/100:.2f})",
                    metadata={
                        "lookback_days": lookback_days,
                        "daily_avg_cents": avg_cost,
                        "today_cents": today_cost,
                    },
                ))

        return anomalies

    async def detect_feature_spikes(
        self,
        tenant_id: str,
        lookback_days: int = 7,
        deviation_threshold: float = 2.0,
    ) -> List[DetectedAnomaly]:
        """
        Detect features with exploding costs.

        Algorithm:
        1. Get each feature's 7-day average daily spend
        2. Get today's spend
        3. If today > 2x average → spike detected
        """
        anomalies = []

        lookback_start = utc_now() - timedelta(days=lookback_days)
        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get historical feature averages
        feature_history = self.session.execute(
            text("""
                SELECT
                    feature_tag,
                    SUM(cost_cents) / :days as daily_avg
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND feature_tag IS NOT NULL
                  AND created_at >= :lookback_start
                  AND created_at < :today_start
                GROUP BY feature_tag
            """),
            {
                "tenant_id": tenant_id,
                "days": lookback_days,
                "lookback_start": lookback_start,
                "today_start": today_start,
            }
        ).all()

        feature_avgs = {row[0]: row[1] for row in feature_history}

        # Get today's spend per feature
        today_spend = self.session.execute(
            text("""
                SELECT
                    feature_tag,
                    SUM(cost_cents) as today_cost
                FROM cost_records
                WHERE tenant_id = :tenant_id
                  AND feature_tag IS NOT NULL
                  AND created_at >= :today_start
                GROUP BY feature_tag
            """),
            {"tenant_id": tenant_id, "today_start": today_start}
        ).all()

        for row in today_spend:
            feature_tag = row[0]
            today_cost = row[1]
            avg_cost = feature_avgs.get(feature_tag, 0)

            if avg_cost <= 0:
                continue

            deviation = today_cost / avg_cost

            if deviation >= deviation_threshold:
                severity = self._classify_severity(deviation * 100)

                # Get feature display name
                feature = self.session.exec(
                    select(FeatureTag).where(
                        FeatureTag.tenant_id == tenant_id,
                        FeatureTag.tag == feature_tag,
                    )
                ).first()
                display_name = feature.display_name if feature else feature_tag

                anomalies.append(DetectedAnomaly(
                    anomaly_type=AnomalyType.FEATURE_SPIKE,
                    severity=severity,
                    entity_type="feature",
                    entity_id=feature_tag,
                    current_value_cents=today_cost,
                    expected_value_cents=avg_cost,
                    deviation_pct=deviation * 100,
                    message=f"Feature '{display_name}' spending {deviation:.1f}x its daily average (${today_cost/100:.2f} vs ${avg_cost/100:.2f})",
                    metadata={
                        "lookback_days": lookback_days,
                        "daily_avg_cents": avg_cost,
                        "today_cents": today_cost,
                        "feature_tag": feature_tag,
                    },
                ))

        return anomalies

    async def detect_budget_issues(self, tenant_id: str) -> List[DetectedAnomaly]:
        """
        Detect budget warnings and exceeded budgets.

        Checks:
        1. Tenant-level daily budget
        2. Tenant-level monthly budget
        3. Per-feature budgets
        """
        anomalies = []

        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get all active budgets for tenant
        budgets = self.session.exec(
            select(CostBudget).where(
                CostBudget.tenant_id == tenant_id,
                CostBudget.is_active == True,
            )
        ).all()

        for budget in budgets:
            # Build where clause based on budget type
            where_clause = "tenant_id = :tenant_id"
            params = {"tenant_id": tenant_id}

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
                    text(f"""
                        SELECT COALESCE(SUM(cost_cents), 0)
                        FROM cost_records
                        WHERE {where_clause} AND created_at >= :today_start
                    """),
                    params
                ).first()

                daily_cost = daily_spend[0] if daily_spend else 0
                daily_pct = (daily_cost / budget.daily_limit_cents * 100) if budget.daily_limit_cents > 0 else 0

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
                    text(f"""
                        SELECT COALESCE(SUM(cost_cents), 0)
                        FROM cost_records
                        WHERE {where_clause} AND created_at >= :month_start
                    """),
                    params
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

        if usage_pct >= 100:
            # Budget exceeded
            entity_desc = f"{budget_type}" if not entity_id else f"{budget_type} '{entity_id}'"
            return DetectedAnomaly(
                anomaly_type=AnomalyType.BUDGET_EXCEEDED,
                severity=AnomalySeverity.CRITICAL,
                entity_type=budget_type,
                entity_id=entity_id,
                current_value_cents=current_cents,
                expected_value_cents=float(limit_cents),
                deviation_pct=usage_pct,
                message=f"{period.title()} budget EXCEEDED for {entity_desc}: ${current_cents/100:.2f} / ${limit_cents/100:.2f} ({usage_pct:.1f}%)",
                metadata={
                    "period": period,
                    "limit_cents": limit_cents,
                    "usage_pct": usage_pct,
                },
            )
        elif usage_pct >= warn_threshold_pct:
            # Budget warning
            entity_desc = f"{budget_type}" if not entity_id else f"{budget_type} '{entity_id}'"
            severity = AnomalySeverity.HIGH if usage_pct >= 90 else AnomalySeverity.MEDIUM
            return DetectedAnomaly(
                anomaly_type=AnomalyType.BUDGET_WARNING,
                severity=severity,
                entity_type=budget_type,
                entity_id=entity_id,
                current_value_cents=current_cents,
                expected_value_cents=float(limit_cents),
                deviation_pct=usage_pct,
                message=f"{period.title()} budget WARNING for {entity_desc}: ${current_cents/100:.2f} / ${limit_cents/100:.2f} ({usage_pct:.1f}%)",
                metadata={
                    "period": period,
                    "limit_cents": limit_cents,
                    "usage_pct": usage_pct,
                    "warn_threshold_pct": warn_threshold_pct,
                },
            )

        return None

    def _classify_severity(self, deviation_pct: float) -> AnomalySeverity:
        """Classify anomaly severity based on deviation percentage."""
        if deviation_pct >= 500:
            return AnomalySeverity.CRITICAL
        elif deviation_pct >= 300:
            return AnomalySeverity.HIGH
        elif deviation_pct >= 200:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    async def persist_anomalies(
        self,
        tenant_id: str,
        anomalies: List[DetectedAnomaly],
    ) -> List[CostAnomaly]:
        """
        Persist detected anomalies to database.

        Returns the created CostAnomaly records.
        """
        created = []

        for anomaly in anomalies:
            # Check if similar anomaly already exists (same type, entity, today)
            today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
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
                # Update existing anomaly if values changed significantly
                if abs(existing.current_value_cents - anomaly.current_value_cents) > existing.current_value_cents * 0.1:
                    existing.current_value_cents = anomaly.current_value_cents
                    existing.deviation_pct = anomaly.deviation_pct
                    existing.message = anomaly.message
                    existing.severity = anomaly.severity.value
                    existing.metadata_json = anomaly.metadata
                    self.session.add(existing)
                    created.append(existing)
                continue

            # Create new anomaly
            cost_anomaly = CostAnomaly(
                tenant_id=tenant_id,
                anomaly_type=anomaly.anomaly_type.value,
                severity=anomaly.severity.value,
                entity_type=anomaly.entity_type,
                entity_id=anomaly.entity_id,
                current_value_cents=anomaly.current_value_cents,
                expected_value_cents=anomaly.expected_value_cents,
                deviation_pct=anomaly.deviation_pct,
                threshold_pct=200.0,  # Default threshold
                message=anomaly.message,
                metadata_json=anomaly.metadata,
            )

            self.session.add(cost_anomaly)
            created.append(cost_anomaly)

        self.session.commit()

        for ca in created:
            self.session.refresh(ca)

        logger.info(f"Persisted {len(created)} anomalies for tenant {tenant_id}")

        return created


async def run_anomaly_detection(session: Session, tenant_id: str) -> List[CostAnomaly]:
    """
    Run anomaly detection and persist results.

    This is the main entry point for periodic detection.
    """
    detector = CostAnomalyDetector(session)

    # Detect anomalies
    anomalies = await detector.detect_all(tenant_id)

    if not anomalies:
        logger.debug(f"No anomalies detected for tenant {tenant_id}")
        return []

    # Persist to database
    persisted = await detector.persist_anomalies(tenant_id, anomalies)

    logger.info(f"Detected and persisted {len(persisted)} anomalies for tenant {tenant_id}")

    return persisted


async def run_anomaly_detection_with_m25(
    session: Session,
    tenant_id: str,
    dispatcher=None,
) -> dict:
    """
    Run anomaly detection AND escalate HIGH/CRITICAL anomalies to M25 loop.

    This is the enhanced entry point that integrates with M25 incident loop.

    Returns:
        {
            "detected": [CostAnomaly, ...],
            "escalated_to_m25": [{"anomaly_id": str, "incident_id": str, "loop_result": dict}, ...],
        }
    """
    # First, run normal detection
    persisted = await run_anomaly_detection(session, tenant_id)

    if not persisted:
        return {"detected": [], "escalated_to_m25": []}

    # Escalate HIGH/CRITICAL to M25 loop
    escalated = []

    # Only process HIGH and CRITICAL anomalies through M25 loop
    high_critical = [a for a in persisted if a.severity in ["HIGH", "CRITICAL"]]

    if high_critical and dispatcher:
        try:
            from app.integrations.cost_bridges import (
                CostAnomaly as CostAnomalyBridge,
                AnomalyType as BridgeAnomalyType,
                AnomalySeverity as BridgeAnomalySeverity,
                CostLoopOrchestrator,
            )

            orchestrator = CostLoopOrchestrator(dispatcher=dispatcher, db_session=session)

            for cost_anomaly in high_critical:
                # Convert DB model to bridge dataclass
                bridge_anomaly = CostAnomalyBridge.create(
                    tenant_id=cost_anomaly.tenant_id,
                    anomaly_type=BridgeAnomalyType(cost_anomaly.anomaly_type.lower()),
                    entity_type=cost_anomaly.entity_type,
                    entity_id=cost_anomaly.entity_id or "",
                    current_value_cents=int(cost_anomaly.current_value_cents),
                    expected_value_cents=int(cost_anomaly.expected_value_cents),
                    metadata=cost_anomaly.metadata_json or {},
                )
                # Override ID and severity to match DB record
                bridge_anomaly.id = cost_anomaly.id
                bridge_anomaly.severity = (
                    BridgeAnomalySeverity.CRITICAL if cost_anomaly.severity == "CRITICAL"
                    else BridgeAnomalySeverity.HIGH
                )

                # Process through M25 loop
                loop_result = await orchestrator.process_anomaly(bridge_anomaly)

                escalated.append({
                    "anomaly_id": cost_anomaly.id,
                    "incident_id": loop_result.get("incident_id"),
                    "loop_result": loop_result,
                })

                logger.info(
                    f"Escalated cost anomaly {cost_anomaly.id} to M25 loop: "
                    f"incident={loop_result.get('incident_id')}, "
                    f"status={loop_result.get('status')}"
                )

        except ImportError as e:
            logger.warning(f"M25 cost bridges not available: {e}")
        except Exception as e:
            logger.error(f"Failed to escalate anomalies to M25 loop: {e}")

    elif high_critical:
        logger.info(
            f"Found {len(high_critical)} HIGH/CRITICAL anomalies but no dispatcher configured. "
            f"Anomalies will NOT be processed through M25 loop."
        )

    return {
        "detected": persisted,
        "escalated_to_m25": escalated,
    }
