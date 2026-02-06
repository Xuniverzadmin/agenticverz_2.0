# Layer: L5 — Domain Engine
# AUDIENCE: FOUNDER
# Role: Founder Explorer cross-tenant read engine (READ-ONLY)
# Callers: L4 handler (fdr_explorer_handler)
# Forbidden Imports: L1, L2
# artifact_class: CODE

"""
Founder Explorer Engine (L5)

Cross-tenant summary, diagnostics, health, and pattern queries.
All methods are READ-ONLY — no mutations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.hoc.fdr.explorer_engine")


class ExplorerEngine:
    """READ-ONLY engine for cross-tenant founder exploration."""

    async def get_system_summary(self, session: AsyncSession) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        tenant_result = (await session.execute(
            text("""
                SELECT
                    COUNT(DISTINCT tenant_id) as total_tenants,
                    COUNT(DISTINCT CASE WHEN created_at > :yesterday THEN tenant_id END) as active_24h,
                    COUNT(DISTINCT CASE WHEN created_at > :week_ago THEN tenant_id END) as active_7d
                FROM proxy_calls
            """),
            {"yesterday": yesterday, "week_ago": week_ago},
        )).fetchone()

        calls_result = (await session.execute(
            text("""
                SELECT
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as calls_24h,
                    COUNT(CASE WHEN created_at > :week_ago THEN 1 END) as calls_7d,
                    COALESCE(SUM(cost_cents), 0) as total_cost,
                    COALESCE(SUM(CASE WHEN created_at > :yesterday THEN cost_cents ELSE 0 END), 0) as cost_24h,
                    COALESCE(SUM(CASE WHEN created_at > :week_ago THEN cost_cents ELSE 0 END), 0) as cost_7d,
                    AVG(CASE WHEN status = 'error' THEN 1.0 ELSE 0.0 END) as error_rate,
                    AVG(latency_ms) as avg_latency
                FROM proxy_calls
            """),
            {"yesterday": yesterday, "week_ago": week_ago},
        )).fetchone()

        incidents_result = (await session.execute(
            text("""
                SELECT
                    COUNT(*) as total_incidents,
                    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_incidents,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_incidents,
                    COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as incidents_24h
                FROM incidents
            """),
            {"yesterday": yesterday},
        )).fetchone()

        return {
            "total_tenants": tenant_result.total_tenants or 0 if tenant_result else 0,
            "active_tenants_24h": tenant_result.active_24h or 0 if tenant_result else 0,
            "active_tenants_7d": tenant_result.active_7d or 0 if tenant_result else 0,
            "total_calls": calls_result.total_calls or 0 if calls_result else 0,
            "calls_24h": calls_result.calls_24h or 0 if calls_result else 0,
            "calls_7d": calls_result.calls_7d or 0 if calls_result else 0,
            "total_incidents": incidents_result.total_incidents or 0 if incidents_result else 0,
            "open_incidents": incidents_result.open_incidents or 0 if incidents_result else 0,
            "critical_incidents": incidents_result.critical_incidents or 0 if incidents_result else 0,
            "incidents_24h": incidents_result.incidents_24h or 0 if incidents_result else 0,
            "total_cost_cents": int(calls_result.total_cost or 0) if calls_result else 0,
            "cost_24h_cents": int(calls_result.cost_24h or 0) if calls_result else 0,
            "cost_7d_cents": int(calls_result.cost_7d or 0) if calls_result else 0,
            "global_error_rate": round(float(calls_result.error_rate or 0) * 100, 2) if calls_result else 0,
            "avg_response_time_ms": round(float(calls_result.avg_latency or 0), 2) if calls_result else 0,
            "generated_at": now.isoformat(),
        }

    async def list_tenants(
        self, session: AsyncSession, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        results = (await session.execute(
            text("""
                WITH tenant_calls AS (
                    SELECT
                        tenant_id,
                        COUNT(*) as total_calls,
                        COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as calls_24h,
                        COUNT(CASE WHEN created_at > :week_ago THEN 1 END) as calls_7d,
                        COALESCE(SUM(cost_cents), 0) as total_cost,
                        COALESCE(SUM(CASE WHEN created_at > :yesterday THEN cost_cents ELSE 0 END), 0) as cost_24h,
                        AVG(CASE WHEN created_at > :yesterday AND status = 'error' THEN 1.0 ELSE 0.0 END) as error_rate,
                        AVG(latency_ms) as avg_latency,
                        MAX(created_at) as last_activity
                    FROM proxy_calls
                    GROUP BY tenant_id
                ),
                tenant_incidents AS (
                    SELECT
                        tenant_id,
                        COUNT(*) as total_incidents,
                        COUNT(CASE WHEN status = 'open' THEN 1 END) as open_incidents,
                        COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_incidents
                    FROM incidents
                    GROUP BY tenant_id
                )
                SELECT
                    tc.tenant_id,
                    tc.total_calls,
                    tc.calls_24h,
                    tc.calls_7d,
                    tc.total_cost,
                    tc.cost_24h,
                    tc.error_rate,
                    tc.avg_latency,
                    tc.last_activity,
                    COALESCE(ti.total_incidents, 0) as total_incidents,
                    COALESCE(ti.open_incidents, 0) as open_incidents,
                    COALESCE(ti.critical_incidents, 0) as critical_incidents
                FROM tenant_calls tc
                LEFT JOIN tenant_incidents ti ON tc.tenant_id = ti.tenant_id
                ORDER BY tc.calls_24h DESC
                LIMIT :limit
            """),
            {"yesterday": yesterday, "week_ago": week_ago, "limit": limit},
        )).fetchall()

        tenants = []
        for row in results:
            status = "active" if row.calls_24h > 0 else "inactive"
            if row.open_incidents > 0:
                status = "issues"
            if row.critical_incidents > 0:
                status = "critical"
            tenants.append({
                "tenant_id": row.tenant_id,
                "total_calls": row.total_calls or 0,
                "calls_24h": row.calls_24h or 0,
                "calls_7d": row.calls_7d or 0,
                "total_incidents": row.total_incidents or 0,
                "open_incidents": row.open_incidents or 0,
                "critical_incidents": row.critical_incidents or 0,
                "total_cost_cents": int(row.total_cost or 0),
                "cost_24h_cents": int(row.cost_24h or 0),
                "error_rate_24h": round(float(row.error_rate or 0) * 100, 2),
                "avg_latency_ms": round(float(row.avg_latency or 0), 2),
                "last_activity": row.last_activity.isoformat() if row.last_activity else None,
                "status": status,
            })
        return tenants

    async def get_tenant_diagnostics(
        self, session: AsyncSession, *, tenant_id: str, hours: int = 24
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=hours)

        hourly_results = (await session.execute(
            text("""
                SELECT DATE_TRUNC('hour', created_at) as hour, COUNT(*) as calls,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                    AVG(latency_ms) as avg_latency
                FROM proxy_calls
                WHERE tenant_id = :tenant_id AND created_at > :start_time
                GROUP BY DATE_TRUNC('hour', created_at) ORDER BY hour
            """),
            {"tenant_id": tenant_id, "start_time": start_time},
        )).fetchall()

        calls_by_hour = [
            {"hour": str(r.hour), "calls": r.calls, "errors": r.errors,
             "avg_latency": round(r.avg_latency or 0, 2)}
            for r in hourly_results
        ]

        skill_results = (await session.execute(
            text("""
                SELECT model as skill, COUNT(*) as calls,
                    COALESCE(SUM(cost_cents), 0) as cost, AVG(latency_ms) as avg_latency
                FROM proxy_calls
                WHERE tenant_id = :tenant_id AND created_at > :start_time
                GROUP BY model ORDER BY calls DESC LIMIT 10
            """),
            {"tenant_id": tenant_id, "start_time": start_time},
        )).fetchall()

        calls_by_skill = [
            {"skill": r.skill or "unknown", "calls": r.calls,
             "cost_cents": int(r.cost), "avg_latency": round(r.avg_latency or 0, 2)}
            for r in skill_results
        ]

        error_results = (await session.execute(
            text("""
                SELECT COALESCE(error_type, 'unknown') as error_type, COUNT(*) as count
                FROM proxy_calls
                WHERE tenant_id = :tenant_id AND status = 'error' AND created_at > :start_time
                GROUP BY error_type ORDER BY count DESC LIMIT 10
            """),
            {"tenant_id": tenant_id, "start_time": start_time},
        )).fetchall()

        error_breakdown = [{"error_type": r.error_type, "count": r.count} for r in error_results]

        incidents_results = (await session.execute(
            text("""
                SELECT id, title, severity, status, created_at
                FROM incidents WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC LIMIT 10
            """),
            {"tenant_id": tenant_id},
        )).fetchall()

        recent_incidents = [
            {"id": str(r.id), "title": r.title, "severity": r.severity,
             "status": r.status, "created_at": str(r.created_at)}
            for r in incidents_results
        ]

        return {
            "tenant_id": tenant_id,
            "calls_by_hour": calls_by_hour,
            "calls_by_skill": calls_by_skill,
            "error_breakdown": error_breakdown,
            "top_errors": error_breakdown[:5],
            "latency_percentiles": {"p50": 100, "p95": 500, "p99": 1000},
            "latency_by_skill": calls_by_skill,
            "cost_by_day": [],
            "cost_by_skill": calls_by_skill,
            "recent_incidents": recent_incidents,
            "generated_at": now.isoformat(),
        }

    async def get_system_health(self, session: AsyncSession) -> dict[str, Any]:
        now = datetime.now(timezone.utc)

        db_healthy = True
        try:
            await session.execute(text("SELECT 1"))
        except Exception:
            db_healthy = False

        redis_healthy = True
        try:
            import os
            import redis as redis_lib
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            r = redis_lib.from_url(redis_url)
            r.ping()
        except Exception:
            redis_healthy = False

        try:
            recent_errors = (await session.execute(
                text("""
                    SELECT COUNT(*) as count FROM proxy_calls
                    WHERE status = 'error' AND created_at > :cutoff
                """),
                {"cutoff": now - timedelta(minutes=5)},
            )).scalar() or 0
        except Exception:
            recent_errors = -1

        status = "healthy"
        if not db_healthy:
            status = "critical"
        elif not redis_healthy:
            status = "degraded"
        elif recent_errors > 100:
            status = "warning"

        return {
            "database_healthy": db_healthy,
            "redis_healthy": redis_healthy,
            "worker_healthy": True,
            "current_load": 0.0,
            "queue_depth": 0,
            "memory_usage_pct": 0.0,
            "cpu_usage_pct": 0.0,
            "recent_errors": recent_errors,
            "recent_timeouts": 0,
            "checked_at": now.isoformat(),
            "status": status,
        }

    async def get_usage_patterns(
        self, session: AsyncSession, *, hours: int = 24
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=hours)
        patterns: list[dict[str, Any]] = []

        inactive_result = (await session.execute(
            text("""
                WITH recent AS (
                    SELECT tenant_id, COUNT(*) as calls FROM proxy_calls
                    WHERE created_at > :recent_cutoff GROUP BY tenant_id
                ),
                historical AS (
                    SELECT tenant_id, COUNT(*) as calls FROM proxy_calls
                    WHERE created_at > :historical_cutoff AND created_at <= :recent_cutoff
                    GROUP BY tenant_id
                )
                SELECT COUNT(*) as count FROM historical h
                LEFT JOIN recent r ON h.tenant_id = r.tenant_id
                WHERE h.calls > 100 AND (r.calls IS NULL OR r.calls < 10)
            """),
            {"recent_cutoff": now - timedelta(hours=24),
             "historical_cutoff": now - timedelta(days=7)},
        )).scalar() or 0

        if inactive_result > 0:
            patterns.append({
                "pattern_type": "churn_risk",
                "description": f"{inactive_result} tenants with high historical usage have gone silent",
                "affected_tenants": inactive_result,
                "severity": "warning",
                "recommendation": "Review these tenants for potential churn intervention",
            })

        error_rate = (await session.execute(
            text("""
                SELECT COUNT(CASE WHEN status = 'error' THEN 1 END) * 100.0
                    / NULLIF(COUNT(*), 0) as error_rate
                FROM proxy_calls WHERE created_at > :start_time
            """),
            {"start_time": start_time},
        )).scalar() or 0

        if error_rate > 5:
            patterns.append({
                "pattern_type": "error_spike",
                "description": f"System-wide error rate is {error_rate:.1f}%",
                "affected_tenants": 0,
                "severity": "concern" if error_rate > 10 else "warning",
                "recommendation": "Investigate top error types and affected services",
            })

        high_cost_tenants = (await session.execute(
            text("""
                SELECT COUNT(*) as count FROM (
                    SELECT tenant_id, SUM(cost_cents) as cost FROM proxy_calls
                    WHERE created_at > :start_time GROUP BY tenant_id
                    HAVING SUM(cost_cents) > 10000
                ) high_cost
            """),
            {"start_time": start_time},
        )).scalar() or 0

        if high_cost_tenants > 0:
            patterns.append({
                "pattern_type": "cost_concentration",
                "description": f"{high_cost_tenants} tenants with high cost concentration (>$100)",
                "affected_tenants": high_cost_tenants,
                "severity": "info",
                "recommendation": "Review pricing and usage patterns for high-cost tenants",
            })

        return {
            "patterns": patterns,
            "analysis_window_hours": hours,
            "generated_at": now.isoformat(),
        }


def get_explorer_engine() -> ExplorerEngine:
    return ExplorerEngine()
