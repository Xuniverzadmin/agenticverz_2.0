#!/usr/bin/env python3
"""Cost Snapshot Job Runner

Runs hourly or daily cost snapshot jobs for all active tenants.

Usage:
    python cost_snapshot_job.py hourly
    python cost_snapshot_job.py daily

Environment:
    DATABASE_URL - PostgreSQL connection string (required)
"""
import asyncio
import os
import ssl
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def get_db_session():
    """Create async database session."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    # Convert to async URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    # Remove sslmode from URL (asyncpg handles SSL differently)
    if 'sslmode=' in database_url:
        import re
        database_url = re.sub(r'\?sslmode=[^&]*', '', database_url)
        database_url = re.sub(r'&sslmode=[^&]*', '', database_url)

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


async def get_active_tenants(session: AsyncSession) -> list[str]:
    """Get list of active tenants with cost records."""
    result = await session.execute(
        text("""
            SELECT DISTINCT tenant_id
            FROM cost_records
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY tenant_id
        """)
    )
    return [row[0] for row in result.fetchall()]


async def run_hourly(session: AsyncSession, tenant_ids: list[str]) -> dict:
    """Run hourly snapshot job."""
    from app.integrations.cost_snapshots import run_hourly_snapshot_job
    return await run_hourly_snapshot_job(session, tenant_ids)


async def run_daily(session: AsyncSession, tenant_ids: list[str]) -> dict:
    """Run daily snapshot + baseline job."""
    from app.integrations.cost_snapshots import run_daily_snapshot_and_baseline_job
    return await run_daily_snapshot_and_baseline_job(session, tenant_ids)


async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('hourly', 'daily'):
        print("Usage: python cost_snapshot_job.py [hourly|daily]")
        sys.exit(1)

    job_type = sys.argv[1]
    now = datetime.now(timezone.utc)

    print(f"[{now.isoformat()}] Starting {job_type} snapshot job...")

    session = await get_db_session()

    try:
        # Get active tenants
        tenant_ids = await get_active_tenants(session)

        if not tenant_ids:
            print(f"[{now.isoformat()}] No active tenants found (no cost records in last 7 days)")
            print(f"[{now.isoformat()}] Job complete: 0 tenants processed")
            return

        print(f"[{now.isoformat()}] Found {len(tenant_ids)} active tenant(s): {tenant_ids}")

        # Run appropriate job
        if job_type == 'hourly':
            results = await run_hourly(session, tenant_ids)
            # Hourly returns {"success": [...], "failed": [...]}
            success = len(results.get('success', []))
            failed_list = results.get('failed', [])
            total = success + len(failed_list)
            print(f"[{now.isoformat()}] Job complete: {success}/{total} succeeded")
            if failed_list:
                print(f"[{now.isoformat()}] Failures:")
                for err in failed_list:
                    print(f"  - {err}")
                sys.exit(1)
        else:
            results = await run_daily(session, tenant_ids)
            # Daily returns {"snapshots": [...], "baselines": [...], "anomalies": [...]}
            snapshots = results.get('snapshots', [])
            baselines = results.get('baselines', [])
            anomalies = results.get('anomalies', [])

            success = len([s for s in snapshots if s.get('status') == 'complete'])
            total = len(snapshots)
            baseline_count = sum(b.get('count', 0) for b in baselines)
            anomaly_triggered = sum(a.get('triggered', 0) for a in anomalies)

            print(f"[{now.isoformat()}] Job complete: {success}/{total} snapshots, {baseline_count} baselines, {anomaly_triggered} anomalies triggered")

    except Exception as e:
        print(f"[{now.isoformat()}] FATAL ERROR: {e}")
        sys.exit(1)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
