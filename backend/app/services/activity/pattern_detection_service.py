# Layer: L4 — Domain Engines
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Detect instability patterns in trace steps
# Callers: Activity API (L2)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/architecture/activity/ACTIVITY_DOMAIN_SQL.md#4-sig-o3

"""
Pattern Detection Service

Detects instability patterns in aos_trace_steps:
- retry_loop: Repeated retries (>3 in same run)
- step_oscillation: Same skill called non-consecutively
- tool_call_loop: Repeated skill within sliding window
- timeout_cascade: Multiple slow steps

Design Rules:
- Rule-based only (no ML)
- Read-only (no writes)
- No cross-service calls
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PatternMatch:
    """A detected pattern."""
    pattern_type: str
    run_id: str
    confidence: float
    details: dict


@dataclass
class PatternResult:
    """Result of pattern detection."""
    patterns: list[PatternMatch]
    window_start: datetime
    window_end: datetime
    runs_analyzed: int


class PatternDetectionService:
    """
    Detect instability patterns in trace steps.

    RESPONSIBILITIES:
    - Detect retry_loop, step_oscillation, tool_call_loop, timeout_cascade
    - Rule-based analysis only (no ML)
    - Return pattern type + confidence

    FORBIDDEN:
    - Write to any table
    - Call other services
    - Use machine learning
    """

    # Pattern thresholds (frozen constants)
    RETRY_THRESHOLD = 3  # Min retries to flag retry_loop
    OSCILLATION_THRESHOLD = 3  # Min oscillations to flag
    LOOP_WINDOW_SIZE = 5  # Steps to look back for tool_call_loop
    LOOP_THRESHOLD = 3  # Min calls in window to flag
    SLOW_THRESHOLD_MS = 5000  # Duration to consider "slow"
    CASCADE_THRESHOLD = 2  # Min slow steps for cascade

    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_patterns(
        self,
        tenant_id: str,
        window_hours: int = 24,
        limit: int = 10,
    ) -> PatternResult:
        """
        Detect all patterns within the time window.

        Args:
            tenant_id: Tenant scope
            window_hours: Hours to look back (max 168 = 7 days)
            limit: Max patterns per type

        Returns:
            PatternResult with all detected patterns
        """
        window_hours = min(window_hours, 168)  # Cap at 7 days
        window_start = datetime.utcnow() - timedelta(hours=window_hours)
        window_end = datetime.utcnow()

        all_patterns: list[PatternMatch] = []
        runs_analyzed = 0

        # Detect each pattern type
        retry_patterns = await self._detect_retry_loops(tenant_id, window_start, limit)
        all_patterns.extend(retry_patterns)

        oscillation_patterns = await self._detect_step_oscillation(tenant_id, window_start, limit)
        all_patterns.extend(oscillation_patterns)

        loop_patterns = await self._detect_tool_call_loops(tenant_id, window_start, limit)
        all_patterns.extend(loop_patterns)

        cascade_patterns = await self._detect_timeout_cascades(tenant_id, window_start, limit)
        all_patterns.extend(cascade_patterns)

        # Get runs analyzed count
        count_sql = text("""
            SELECT COUNT(DISTINCT t.run_id)
            FROM aos_traces t
            WHERE t.tenant_id = :tenant_id
              AND t.started_at >= :window_start
        """)
        result = await self.session.execute(count_sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
        })
        runs_analyzed = result.scalar() or 0

        return PatternResult(
            patterns=all_patterns,
            window_start=window_start,
            window_end=window_end,
            runs_analyzed=runs_analyzed,
        )

    async def _detect_retry_loops(
        self,
        tenant_id: str,
        window_start: datetime,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect runs with excessive retries."""
        sql = text("""
            SELECT
                t.run_id,
                SUM(s.retry_count) as total_retries,
                MAX(s.retry_count) as max_step_retries,
                COUNT(*) as step_count
            FROM aos_traces t
            JOIN aos_trace_steps s ON s.trace_id = t.trace_id
            WHERE t.tenant_id = :tenant_id
              AND t.started_at >= :window_start
              AND s.retry_count > 0
            GROUP BY t.run_id
            HAVING SUM(s.retry_count) >= :threshold
            ORDER BY total_retries DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
            "threshold": self.RETRY_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            # Confidence based on retry severity
            total_retries = row["total_retries"]
            confidence = min(0.5 + (total_retries - self.RETRY_THRESHOLD) * 0.1, 0.99)

            patterns.append(PatternMatch(
                pattern_type="retry_loop",
                run_id=row["run_id"],
                confidence=round(confidence, 2),
                details={
                    "total_retries": total_retries,
                    "max_step_retries": row["max_step_retries"],
                    "step_count": row["step_count"],
                },
            ))

        return patterns

    async def _detect_step_oscillation(
        self,
        tenant_id: str,
        window_start: datetime,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect skills called repeatedly in non-consecutive steps."""
        sql = text("""
            WITH step_sequences AS (
                SELECT
                    t.run_id,
                    s.trace_id,
                    s.skill_id,
                    s.step_index,
                    LAG(s.skill_id) OVER (
                        PARTITION BY s.trace_id ORDER BY s.step_index
                    ) as prev_skill
                FROM aos_traces t
                JOIN aos_trace_steps s ON s.trace_id = t.trace_id
                WHERE t.tenant_id = :tenant_id
                  AND t.started_at >= :window_start
            )
            SELECT
                run_id,
                skill_id,
                COUNT(*) as oscillation_count
            FROM step_sequences
            WHERE skill_id != prev_skill  -- Non-consecutive
              AND prev_skill IS NOT NULL
            GROUP BY run_id, skill_id
            HAVING COUNT(*) >= :threshold
            ORDER BY oscillation_count DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
            "threshold": self.OSCILLATION_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            count = row["oscillation_count"]
            confidence = min(0.6 + (count - self.OSCILLATION_THRESHOLD) * 0.1, 0.95)

            patterns.append(PatternMatch(
                pattern_type="step_oscillation",
                run_id=row["run_id"],
                confidence=round(confidence, 2),
                details={
                    "skill_id": row["skill_id"],
                    "oscillation_count": count,
                },
            ))

        return patterns

    async def _detect_tool_call_loops(
        self,
        tenant_id: str,
        window_start: datetime,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect skills called repeatedly within a sliding window."""
        sql = text("""
            WITH windowed_skills AS (
                SELECT
                    t.run_id,
                    s.trace_id,
                    s.skill_id,
                    s.step_index,
                    COUNT(*) OVER (
                        PARTITION BY s.trace_id, s.skill_id
                        ORDER BY s.step_index
                        ROWS BETWEEN :window_size PRECEDING AND CURRENT ROW
                    ) as recent_calls
                FROM aos_traces t
                JOIN aos_trace_steps s ON s.trace_id = t.trace_id
                WHERE t.tenant_id = :tenant_id
                  AND t.started_at >= :window_start
            )
            SELECT
                run_id,
                skill_id,
                MAX(recent_calls) as loop_depth
            FROM windowed_skills
            WHERE recent_calls >= :threshold
            GROUP BY run_id, skill_id
            ORDER BY loop_depth DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
            "window_size": self.LOOP_WINDOW_SIZE - 1,  # ROWS BETWEEN is 0-indexed
            "threshold": self.LOOP_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            depth = row["loop_depth"]
            confidence = min(0.7 + (depth - self.LOOP_THRESHOLD) * 0.1, 0.98)

            patterns.append(PatternMatch(
                pattern_type="tool_call_loop",
                run_id=row["run_id"],
                confidence=round(confidence, 2),
                details={
                    "skill_id": row["skill_id"],
                    "loop_depth": depth,
                },
            ))

        return patterns

    async def _detect_timeout_cascades(
        self,
        tenant_id: str,
        window_start: datetime,
        limit: int,
    ) -> list[PatternMatch]:
        """Detect runs with multiple slow steps."""
        sql = text("""
            SELECT
                t.run_id,
                COUNT(*) as slow_step_count,
                AVG(s.duration_ms) as avg_duration_ms,
                MAX(s.duration_ms) as max_duration_ms
            FROM aos_traces t
            JOIN aos_trace_steps s ON s.trace_id = t.trace_id
            WHERE t.tenant_id = :tenant_id
              AND t.started_at >= :window_start
              AND s.duration_ms > :slow_threshold
            GROUP BY t.run_id
            HAVING COUNT(*) >= :cascade_threshold
            ORDER BY slow_step_count DESC
            LIMIT :limit
        """)

        result = await self.session.execute(sql, {
            "tenant_id": tenant_id,
            "window_start": window_start,
            "slow_threshold": self.SLOW_THRESHOLD_MS,
            "cascade_threshold": self.CASCADE_THRESHOLD,
            "limit": limit,
        })

        patterns = []
        for row in result.mappings():
            count = row["slow_step_count"]
            confidence = min(0.6 + (count - self.CASCADE_THRESHOLD) * 0.15, 0.95)

            patterns.append(PatternMatch(
                pattern_type="timeout_cascade",
                run_id=row["run_id"],
                confidence=round(confidence, 2),
                details={
                    "slow_step_count": count,
                    "avg_duration_ms": round(row["avg_duration_ms"], 2),
                    "max_duration_ms": round(row["max_duration_ms"], 2),
                },
            ))

        return patterns
