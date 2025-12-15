# app/tasks/m10_metrics_collector.py
"""
Periodic metrics collector for M10 Recovery System.

Updates Prometheus gauge metrics for:
- Redis stream stats (length, pending, consumers)
- DB fallback queue stats (depth, stalled)
- Materialized view freshness

Usage:
    # As async task
    await collect_m10_metrics()

    # As background loop
    await run_metrics_collector(interval=30)

    # One-time collection
    python -m app.tasks.m10_metrics_collector
"""

import asyncio
import logging
import os
import time
from typing import Optional

from sqlalchemy import text

from app.metrics import (
    recovery_stream_length,
    recovery_stream_pending,
    recovery_stream_consumers,
    recovery_db_queue_depth,
    recovery_db_queue_stalled,
    recovery_matview_age_seconds,
    recovery_matview_last_refresh_timestamp,
    recovery_candidates_pending,
    recovery_dead_letter_length,
)

logger = logging.getLogger("nova.tasks.m10_metrics_collector")

# Collection interval (seconds)
COLLECTION_INTERVAL = int(os.getenv("M10_METRICS_INTERVAL", "30"))


async def collect_redis_stream_metrics() -> dict:
    """
    Collect Redis stream metrics including dead-letter.

    Returns:
        Dict with stream_length, pending_count, consumers_count, dead_letter_count
    """
    try:
        from app.tasks.recovery_queue_stream import get_stream_info, get_dead_letter_count

        info = await get_stream_info()

        # Update Prometheus gauges
        recovery_stream_length.set(info.get("stream_length", 0))
        recovery_stream_pending.set(info.get("pending_count", 0))
        recovery_stream_consumers.set(info.get("consumers_count", 0))

        # Dead-letter count
        dl_count = await get_dead_letter_count()
        recovery_dead_letter_length.set(dl_count)
        info["dead_letter_count"] = dl_count

        logger.debug(
            f"Stream metrics: len={info.get('stream_length')}, "
            f"pending={info.get('pending_count')}, "
            f"consumers={info.get('consumers_count')}, "
            f"dead_letter={dl_count}"
        )

        return info

    except Exception as e:
        logger.warning(f"Failed to collect Redis stream metrics: {e}")
        # Set to 0 on error (Redis may be down)
        recovery_stream_length.set(0)
        recovery_stream_pending.set(0)
        recovery_stream_consumers.set(0)
        recovery_dead_letter_length.set(0)
        return {"error": str(e)}


async def collect_db_queue_metrics(session=None) -> dict:
    """
    Collect DB fallback queue metrics.

    Args:
        session: Optional SQLAlchemy async session

    Returns:
        Dict with queue_depth, stalled_count
    """
    close_session = False

    try:
        if session is None:
            from app.database import get_async_session
            session = await get_async_session()
            close_session = True

        # Queue depth (unprocessed items)
        depth_result = await session.execute(text("""
            SELECT COUNT(*) FROM m10_recovery.work_queue
            WHERE processed_at IS NULL
        """))
        queue_depth = depth_result.scalar() or 0

        # Stalled items (claimed but not processed for > 5 min)
        stalled_result = await session.execute(text("""
            SELECT COUNT(*) FROM m10_recovery.work_queue
            WHERE claimed_at IS NOT NULL
              AND processed_at IS NULL
              AND claimed_at < now() - interval '5 minutes'
        """))
        stalled_count = stalled_result.scalar() or 0

        # Update Prometheus gauges
        recovery_db_queue_depth.set(queue_depth)
        recovery_db_queue_stalled.set(stalled_count)

        logger.debug(f"DB queue metrics: depth={queue_depth}, stalled={stalled_count}")

        return {"queue_depth": queue_depth, "stalled_count": stalled_count}

    except Exception as e:
        logger.warning(f"Failed to collect DB queue metrics: {e}")
        # Don't set to 0 on error - DB might just not have the table yet
        return {"error": str(e)}

    finally:
        if close_session and session:
            await session.close()


async def collect_matview_freshness(session=None) -> dict:
    """
    Collect materialized view freshness metrics.

    Args:
        session: Optional SQLAlchemy async session

    Returns:
        Dict with view_name, age_seconds, last_refresh
    """
    close_session = False

    try:
        if session is None:
            from app.database import get_async_session
            session = await get_async_session()
            close_session = True

        # Get matview freshness from tracking table
        result = await session.execute(text("""
            SELECT view_name, last_refresh,
                   EXTRACT(EPOCH FROM (now() - last_refresh)) as age_seconds
            FROM m10_recovery.matview_freshness
        """))

        rows = result.fetchall()
        metrics = {}

        for row in rows:
            view_name = row[0]
            last_refresh = row[1]
            age_seconds = float(row[2]) if row[2] else 0

            # Update Prometheus gauges
            recovery_matview_age_seconds.labels(view_name=view_name).set(age_seconds)
            if last_refresh:
                recovery_matview_last_refresh_timestamp.labels(view_name=view_name).set(
                    last_refresh.timestamp()
                )

            metrics[view_name] = {
                "age_seconds": age_seconds,
                "last_refresh": str(last_refresh) if last_refresh else None,
            }

            logger.debug(f"Matview {view_name} age: {age_seconds:.1f}s")

        return metrics

    except Exception as e:
        logger.warning(f"Failed to collect matview freshness metrics: {e}")
        return {"error": str(e)}

    finally:
        if close_session and session:
            await session.close()


async def collect_candidate_stats(session=None) -> dict:
    """
    Collect recovery candidate statistics.

    Args:
        session: Optional SQLAlchemy async session

    Returns:
        Dict with pending count and decision breakdown
    """
    close_session = False

    try:
        if session is None:
            from app.database import get_async_session
            session = await get_async_session()
            close_session = True

        # Pending candidates count
        pending_result = await session.execute(text("""
            SELECT COUNT(*) FROM recovery_candidates
            WHERE decision = 'pending'
        """))
        pending_count = pending_result.scalar() or 0

        # Update Prometheus gauge
        recovery_candidates_pending.set(pending_count)

        logger.debug(f"Candidates pending: {pending_count}")

        return {"pending": pending_count}

    except Exception as e:
        logger.warning(f"Failed to collect candidate stats: {e}")
        return {"error": str(e)}

    finally:
        if close_session and session:
            await session.close()


async def collect_m10_metrics(session=None) -> dict:
    """
    Collect all M10 recovery system metrics.

    This is the main entry point for metrics collection.

    Args:
        session: Optional SQLAlchemy async session

    Returns:
        Dict with all collected metrics
    """
    start = time.time()

    # Collect all metrics concurrently where possible
    redis_task = asyncio.create_task(collect_redis_stream_metrics())

    # DB metrics need to share session if provided
    db_queue = await collect_db_queue_metrics(session)
    matview = await collect_matview_freshness(session)
    candidates = await collect_candidate_stats(session)

    redis = await redis_task

    elapsed = time.time() - start

    result = {
        "redis_stream": redis,
        "db_queue": db_queue,
        "matview_freshness": matview,
        "candidates": candidates,
        "collection_time_ms": round(elapsed * 1000, 2),
    }

    logger.info(f"M10 metrics collected in {elapsed*1000:.1f}ms")

    return result


async def run_metrics_collector(
    interval: int = COLLECTION_INTERVAL,
    stop_event: Optional[asyncio.Event] = None,
) -> None:
    """
    Run metrics collector as a background loop.

    Args:
        interval: Collection interval in seconds
        stop_event: Optional event to signal shutdown
    """
    logger.info(f"Starting M10 metrics collector (interval={interval}s)")

    while True:
        try:
            await collect_m10_metrics()
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")

        # Check for shutdown signal
        if stop_event and stop_event.is_set():
            logger.info("Metrics collector shutdown requested")
            break

        await asyncio.sleep(interval)


async def main():
    """CLI entry point for one-time collection."""
    import json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    result = await collect_m10_metrics()
    print(json.dumps(result, indent=2, default=str))


async def daemon_main():
    """
    Daemon entry point with signal handling and systemd watchdog.

    Usage:
        python -m app.tasks.m10_metrics_collector --daemon
    """
    import signal

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    stop_event = asyncio.Event()

    def handle_shutdown(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        stop_event.set()

    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Systemd watchdog support (optional)
    try:
        import sdnotify
        notify = sdnotify.SystemdNotifier()
        notify.notify("READY=1")
        logger.info("Systemd notification: READY")

        async def watchdog_ping():
            while not stop_event.is_set():
                notify.notify("WATCHDOG=1")
                await asyncio.sleep(30)  # Ping every 30s (watchdog is 120s)

        watchdog_task = asyncio.create_task(watchdog_ping())
    except ImportError:
        notify = None
        watchdog_task = None
        logger.info("sdnotify not available, running without systemd integration")

    logger.info("M10 Metrics Collector daemon starting...")

    try:
        await run_metrics_collector(
            interval=COLLECTION_INTERVAL,
            stop_event=stop_event,
        )
    finally:
        if watchdog_task:
            watchdog_task.cancel()
        if notify:
            notify.notify("STOPPING=1")
        logger.info("M10 Metrics Collector daemon stopped")


if __name__ == "__main__":
    import sys

    if "--daemon" in sys.argv:
        asyncio.run(daemon_main())
    else:
        asyncio.run(main())
