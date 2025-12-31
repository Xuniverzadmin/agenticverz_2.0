#!/usr/bin/env python3
"""Test Cost Snapshot Service

Tests the M27.1 Cost Snapshot Barrier with real Neon DB data.
"""
import asyncio
import os
import ssl
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.integrations.cost_snapshots import (
    SnapshotComputer,
    SnapshotAnomalyDetector,
    SnapshotStatus,
    SnapshotType,
)


async def get_db_session():
    """Create async database session."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    # Convert to async URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Remove sslmode from URL (asyncpg handles SSL differently)
    if "sslmode=" in database_url:
        import re

        database_url = re.sub(r"\?sslmode=[^&]*", "", database_url)
        database_url = re.sub(r"&sslmode=[^&]*", "", database_url)

    # Create SSL context for asyncpg
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"ssl": ssl_context},
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def test_snapshot_computation(tenant_id: str):
    """Test computing a snapshot for a tenant."""
    print(f"\n{'='*60}")
    print(f"Testing Snapshot Computation for: {tenant_id}")
    print(f"{'='*60}")

    session = await get_db_session()

    try:
        computer = SnapshotComputer(session)

        # Compute snapshot for today (we have today's data)
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Use a custom period for testing (today's data)
        snapshot = await computer._compute_snapshot(
            tenant_id=tenant_id,
            snapshot_type=SnapshotType.DAILY,
            period_start=today_start,
            period_end=now,
        )

        print("\n✅ Snapshot Created:")
        print(f"   ID: {snapshot.id}")
        print(f"   Status: {snapshot.status.value}")
        print(f"   Records Processed: {snapshot.records_processed}")
        print(f"   Computation Time: {snapshot.computation_ms}ms")
        print(f"   Period: {snapshot.period_start} to {snapshot.period_end}")

        # Verify aggregates were created
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT entity_type, entity_id, total_cost_cents, request_count
                FROM cost_snapshot_aggregates
                WHERE snapshot_id = :snapshot_id
                ORDER BY entity_type, total_cost_cents DESC
            """
            ),
            {"snapshot_id": snapshot.id},
        )

        print("\n📊 Aggregates Created:")
        for row in result.fetchall():
            entity = row.entity_id or "(tenant-level)"
            print(
                f"   {row.entity_type}: {entity} → ${row.total_cost_cents/100:.4f} ({row.request_count} requests)"
            )

        return snapshot

    finally:
        await session.close()


async def test_anomaly_evaluation(snapshot_id: str, tenant_id: str):
    """Test evaluating a snapshot for anomalies."""
    print(f"\n{'='*60}")
    print(f"Testing Anomaly Evaluation for Snapshot: {snapshot_id}")
    print(f"{'='*60}")

    session = await get_db_session()

    try:
        # First, create a synthetic baseline for testing
        # (We don't have historical data, so we'll create one manually)
        print("\n📈 Creating synthetic baseline for testing...")

        # Get tenant-level aggregate
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT total_cost_cents FROM cost_snapshot_aggregates
                WHERE snapshot_id = :snapshot_id AND entity_type = 'tenant'
            """
            ),
            {"snapshot_id": snapshot_id},
        )
        row = result.fetchone()
        if row:
            current_cost = row.total_cost_cents
            # Create a baseline that's 1/5 of current (to trigger HIGH anomaly)
            baseline_cost = current_cost / 5

            # Insert synthetic baseline
            import hashlib

            baseline_id = f"base_{hashlib.sha256(f'{tenant_id}:tenant:None:7:test'.encode()).hexdigest()[:16]}"

            await session.execute(
                __import__("sqlalchemy").text(
                    """
                    INSERT INTO cost_snapshot_baselines (
                        id, tenant_id, entity_type, entity_id,
                        avg_daily_cost_cents, avg_daily_requests,
                        window_days, samples_count, computed_at, valid_until, is_current
                    ) VALUES (
                        :id, :tenant_id, 'tenant', NULL,
                        :avg_cost, 10,
                        7, 7, NOW(), NOW() + INTERVAL '1 day', true
                    )
                    ON CONFLICT (tenant_id, entity_type, entity_id, window_days, is_current)
                    DO UPDATE SET avg_daily_cost_cents = :avg_cost
                """
                ),
                {
                    "id": baseline_id,
                    "tenant_id": tenant_id,
                    "avg_cost": baseline_cost,
                },
            )
            await session.commit()
            print(f"   Baseline: ${baseline_cost/100:.4f}/day")
            print(f"   Current: ${current_cost/100:.4f} (today)")
            print(f"   Expected deviation: {(current_cost/baseline_cost - 1)*100:.0f}%")

            # Update aggregate with baseline
            await session.execute(
                __import__("sqlalchemy").text(
                    """
                    UPDATE cost_snapshot_aggregates SET
                        baseline_7d_avg_cents = :baseline,
                        deviation_from_7d_pct = (total_cost_cents - :baseline) / :baseline * 100
                    WHERE snapshot_id = :snapshot_id AND entity_type = 'tenant'
                """
                ),
                {
                    "snapshot_id": snapshot_id,
                    "baseline": baseline_cost,
                },
            )
            await session.commit()

        # Now run anomaly detection
        detector = SnapshotAnomalyDetector(session)
        evaluations = await detector.evaluate_snapshot(snapshot_id, threshold_pct=200)

        print("\n🔍 Anomaly Evaluations:")
        for eval in evaluations:
            status = "🚨 TRIGGERED" if eval.triggered else "✅ OK"
            print(f"   {eval.entity_type.value}: {eval.entity_id or '(tenant)'}")
            print(
                f"      {status} - {eval.deviation_pct:.1f}% deviation (threshold: {eval.threshold_pct}%)"
            )
            if eval.triggered:
                print(f"      Severity: {eval.severity_computed}")
                print(f"      Anomaly ID: {eval.anomaly_id}")

        return evaluations

    finally:
        await session.close()


async def verify_db_state(tenant_id: str):
    """Verify the final database state."""
    print(f"\n{'='*60}")
    print("Verifying Database State")
    print(f"{'='*60}")

    session = await get_db_session()

    try:
        # Check snapshots
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT id, status, records_processed, computation_ms
                FROM cost_snapshots WHERE tenant_id = :tenant_id
            """
            ),
            {"tenant_id": tenant_id},
        )
        print("\n📸 Snapshots:")
        for row in result.fetchall():
            print(
                f"   {row.id}: {row.status} ({row.records_processed} records, {row.computation_ms}ms)"
            )

        # Check aggregates count
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT COUNT(*) as count FROM cost_snapshot_aggregates
                WHERE tenant_id = :tenant_id
            """
            ),
            {"tenant_id": tenant_id},
        )
        row = result.fetchone()
        print(f"\n📊 Aggregates: {row.count} total")

        # Check baselines
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT COUNT(*) as count FROM cost_snapshot_baselines
                WHERE tenant_id = :tenant_id AND is_current = true
            """
            ),
            {"tenant_id": tenant_id},
        )
        row = result.fetchone()
        print(f"📈 Active Baselines: {row.count}")

        # Check evaluations
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT COUNT(*) as total, SUM(CASE WHEN triggered THEN 1 ELSE 0 END) as triggered
                FROM cost_anomaly_evaluations
                WHERE tenant_id = :tenant_id
            """
            ),
            {"tenant_id": tenant_id},
        )
        row = result.fetchone()
        print(f"🔍 Evaluations: {row.total} total, {row.triggered} triggered")

        # Check anomalies with snapshot_id
        result = await session.execute(
            __import__("sqlalchemy").text(
                """
                SELECT id, severity, snapshot_id FROM cost_anomalies
                WHERE tenant_id = :tenant_id AND snapshot_id IS NOT NULL
                ORDER BY detected_at DESC LIMIT 3
            """
            ),
            {"tenant_id": tenant_id},
        )
        print("\n🚨 Anomalies (from snapshots):")
        for row in result.fetchall():
            print(f"   {row.id}: {row.severity} (snapshot: {row.snapshot_id[:20]}...)")

    finally:
        await session.close()


async def main():
    """Run all tests."""
    tenant_id = "tenant_m27_test"  # Has the most data

    print("=" * 60)
    print("M27.1 Cost Snapshot Barrier Test")
    print("=" * 60)
    print(f"Tenant: {tenant_id}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")

    # Test 1: Compute snapshot
    snapshot = await test_snapshot_computation(tenant_id)

    if snapshot and snapshot.status == SnapshotStatus.COMPLETE:
        # Test 2: Evaluate for anomalies
        await test_anomaly_evaluation(snapshot.id, tenant_id)

    # Test 3: Verify final state
    await verify_db_state(tenant_id)

    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
