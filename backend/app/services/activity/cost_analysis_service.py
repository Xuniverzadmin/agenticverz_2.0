# Layer: L4 — Domain Engines
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Analyze cost anomalies via Z-score
# Callers: Activity API (L2)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/activity/ACTIVITY_DOMAIN_SQL.md#5-sig-o4

"""
Cost Analysis Service

Analyzes cost anomalies in worker runs:
- Calculates baseline statistics per agent (configurable window)
- Detects anomalies via Z-score threshold
- Returns anomaly details for attention

Design Rules:
- Read-only (no writes)
- Statistical comparison only
- No cross-service calls
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AgentCostAnalysis:
    """Cost analysis for a single agent."""
    agent_id: str
    current_cost_usd: float
    run_count: int
    baseline_avg_usd: Optional[float]
    baseline_p95_usd: Optional[float]
    z_score: float
    is_anomaly: bool


@dataclass
class CostAnalysisResult:
    """Result of cost analysis."""
    agents: list[AgentCostAnalysis]
    total_anomalies: int
    total_cost_usd: float
    window_current: str
    window_baseline: str


class CostAnalysisService:
    """
    Analyze cost anomalies via Z-score.

    RESPONSIBILITIES:
    - Calculate baseline cost statistics
    - Detect cost anomalies via Z-score
    - Return anomaly + details

    FORBIDDEN:
    - Write to any table
    - Modify cost fields
    - Label runs as failed
    """

    # Default thresholds (can be overridden)
    DEFAULT_BASELINE_DAYS = 7
    DEFAULT_ANOMALY_THRESHOLD = 2.0  # Z-score

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze_costs(
        self,
        tenant_id: str,
        baseline_days: int = DEFAULT_BASELINE_DAYS,
        anomaly_threshold: float = DEFAULT_ANOMALY_THRESHOLD,
    ) -> CostAnalysisResult:
        """
        Analyze costs and detect anomalies.

        Args:
            tenant_id: Tenant scope
            baseline_days: Days to use for baseline (max 30)
            anomaly_threshold: Z-score threshold for anomaly detection

        Returns:
            CostAnalysisResult with per-agent analysis
        """
        baseline_days = min(baseline_days, 30)  # Cap at 30 days
        anomaly_threshold = min(anomaly_threshold, 5.0)  # Cap Z-score

        sql = text("""
            WITH baseline AS (
                SELECT
                    COALESCE(agent_id, 'unknown') as agent_id,
                    AVG(estimated_cost_usd) as avg_cost,
                    STDDEV(estimated_cost_usd) as stddev_cost,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY estimated_cost_usd) as p95_cost,
                    COUNT(*) as baseline_run_count
                FROM runs
                WHERE tenant_id = :tenant_id
                  AND completed_at >= NOW() - INTERVAL '1 day' * :baseline_days
                  AND completed_at < NOW() - INTERVAL '1 day'
                  AND estimated_cost_usd IS NOT NULL
                GROUP BY agent_id
            ),
            current_window AS (
                SELECT
                    COALESCE(agent_id, 'unknown') as agent_id,
                    AVG(estimated_cost_usd) as current_avg_cost,
                    SUM(estimated_cost_usd) as total_cost,
                    COUNT(*) as run_count
                FROM runs
                WHERE tenant_id = :tenant_id
                  AND started_at >= NOW() - INTERVAL '1 day'
                  AND estimated_cost_usd IS NOT NULL
                GROUP BY agent_id
            )
            SELECT
                c.agent_id,
                c.current_avg_cost,
                c.total_cost,
                c.run_count,
                b.avg_cost as baseline_avg,
                b.p95_cost as baseline_p95,
                b.stddev_cost,
                CASE
                    WHEN b.stddev_cost > 0 AND b.stddev_cost IS NOT NULL THEN
                        (c.current_avg_cost - b.avg_cost) / b.stddev_cost
                    ELSE 0
                END as z_score
            FROM current_window c
            LEFT JOIN baseline b ON b.agent_id = c.agent_id
            ORDER BY z_score DESC
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "baseline_days": baseline_days,
        })

        agents: list[AgentCostAnalysis] = []
        total_cost = 0.0
        anomaly_count = 0

        for row in result.mappings():
            z_score = float(row["z_score"] or 0)
            current_cost = float(row["current_avg_cost"] or 0)
            baseline_avg = float(row["baseline_avg"]) if row["baseline_avg"] else None
            baseline_p95 = float(row["baseline_p95"]) if row["baseline_p95"] else None

            # Determine if anomaly
            is_anomaly = False
            if z_score > anomaly_threshold:
                is_anomaly = True
            elif baseline_p95 and current_cost > baseline_p95:
                is_anomaly = True

            if is_anomaly:
                anomaly_count += 1

            total_cost += float(row["total_cost"] or 0)

            agents.append(AgentCostAnalysis(
                agent_id=row["agent_id"],
                current_cost_usd=round(current_cost, 4),
                run_count=row["run_count"],
                baseline_avg_usd=round(baseline_avg, 4) if baseline_avg else None,
                baseline_p95_usd=round(baseline_p95, 4) if baseline_p95 else None,
                z_score=round(z_score, 2),
                is_anomaly=is_anomaly,
            ))

        return CostAnalysisResult(
            agents=agents,
            total_anomalies=anomaly_count,
            total_cost_usd=round(total_cost, 4),
            window_current="last_24h",
            window_baseline=f"{baseline_days}_day_average",
        )
