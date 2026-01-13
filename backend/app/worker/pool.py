# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: scheduler (standalone process)
#   Execution: sync (dispatch loop) + ThreadPoolExecutor (worker threads)
# Role: Worker pool dispatch (polls DB, dispatches to RunRunner)
# Authority: Run claim (pending → running via ThreadPool dispatch)
# Callers: Standalone process (`python -m app.worker.pool`)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 3: At-Least-Once Worker Dispatch)
# Pattern: Sync dispatch loop with ThreadPoolExecutor for worker isolation

"""
Worker pool: polls runs table and dispatches runs to runner workers.
Designed to be launched as a separate process: `python -m app.worker.pool`

Supports graceful shutdown via SIGTERM/SIGINT - waits for running tasks to complete.
"""

import logging
import os
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, List, Optional, cast

from sqlmodel import Session, select

# Add parent to path for module imports when run directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.infra import FeatureIntent, RetryPolicy

from ..db import Run, engine
from ..events import get_publisher
from ..metrics import nova_worker_pool_size
from ..models.logs_records import (
    SystemCausedBy,
    SystemComponent,
    SystemEventType,
    SystemRecord,
    SystemSeverity,
)
from .runner import RunRunner

# Phase-2.3: Feature Intent Declaration
# Thread pool state tracking, no distributed locks needed
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

logger = logging.getLogger("nova.worker.pool")

# Global pool reference for signal handlers
_pool_instance: Optional["WorkerPool"] = None

POLL_INTERVAL = float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))
CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "4"))
MAX_BATCH = int(os.getenv("WORKER_BATCH_SIZE", "8"))


def _create_worker_system_record(
    event_type: str,
    severity: str,
    summary: str,
    details: Optional[dict] = None,
    caused_by: Optional[str] = None,
):
    """
    Create an immutable system record for worker events (PIN-413).

    Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger).
    """
    try:
        record = SystemRecord(
            tenant_id=None,  # Worker events are system-wide
            component=SystemComponent.WORKER.value,
            event_type=event_type,
            severity=severity,
            summary=summary,
            details=details,
            caused_by=caused_by,
        )

        with Session(engine) as session:
            session.add(record)
            session.commit()

        logger.info(
            "system_record_created",
            extra={
                "record_id": record.id,
                "component": SystemComponent.WORKER.value,
                "event_type": event_type,
                "severity": severity,
            },
        )
    except Exception as e:
        # System record creation failure should not crash the worker
        logger.error("system_record_creation_failed", extra={"error": str(e)})


class WorkerPool:
    """Worker pool that polls for queued runs and dispatches to runner threads."""

    def __init__(self, concurrency: int = CONCURRENCY):
        self.concurrency = concurrency
        self.executor = ThreadPoolExecutor(max_workers=self.concurrency)
        self._stop = threading.Event()
        self.publisher = get_publisher()
        self._active_runs = set()
        self._lock = threading.Lock()

    def poll_and_dispatch(self):
        """Main polling loop - runs until stopped."""
        logger.info("worker_pool_starting", extra={"concurrency": self.concurrency})
        self.publisher.publish("worker.pool.started", {"concurrency": self.concurrency})
        nova_worker_pool_size.set(self.concurrency)

        # PIN-413: Create immutable system record for worker startup
        _create_worker_system_record(
            event_type=SystemEventType.STARTUP.value,
            severity=SystemSeverity.INFO.value,
            summary="Worker pool started",
            details={
                "concurrency": self.concurrency,
                "poll_interval": POLL_INTERVAL,
                "max_batch": MAX_BATCH,
            },
            caused_by=SystemCausedBy.SYSTEM.value,
        )

        while not self._stop.is_set():
            try:
                runs = self._fetch_queued_runs()

                if not runs:
                    time.sleep(POLL_INTERVAL)
                    continue

                for run in runs:
                    # Skip if already being processed
                    with self._lock:
                        if run.id in self._active_runs:
                            continue
                        self._active_runs.add(run.id)

                    # Mark as running
                    self._mark_run_started(run.id)

                    # Submit to thread pool
                    future = self.executor.submit(self._execute_run, run.id)
                    future.add_done_callback(lambda f, rid=run.id: self._on_run_complete(rid, f))

                    logger.info("run_dispatched", extra={"run_id": run.id, "agent_id": run.agent_id})

            except Exception:
                logger.exception("worker_pool_poll_error")
                time.sleep(POLL_INTERVAL)

    def _fetch_queued_runs(self) -> List[Run]:
        """Fetch runs that are ready to be processed."""
        with Session(engine) as session:
            # Select queued or retry runs where next_attempt_at is NULL or <= now
            statement = (
                select(Run)
                .where(cast(Any, Run.status).in_(["queued", "retry"]))
                .where((Run.next_attempt_at == None) | (Run.next_attempt_at <= datetime.now(timezone.utc)))
                .order_by(cast(Any, Run.created_at).asc())
                .limit(MAX_BATCH)
            )
            runs = session.exec(statement).all()
            return list(runs)

    def _mark_run_started(self, run_id: str):
        """Mark run as running in database."""
        with Session(engine) as session:
            run = session.get(Run, run_id)
            if run:
                run.status = "running"
                run.started_at = datetime.now(timezone.utc)
                run.attempts = (run.attempts or 0) + 1
                session.add(run)
                session.commit()

    def _execute_run(self, run_id: str):
        """Execute run using runner (called in thread pool)."""
        runner = RunRunner(run_id=run_id, publisher=self.publisher)
        runner.run()

    def _on_run_complete(self, run_id: str, future):
        """Callback when run execution completes."""
        with self._lock:
            self._active_runs.discard(run_id)

        try:
            future.result()  # Raise any exception that occurred
        except Exception:
            logger.exception("runner_task_exception", extra={"run_id": run_id})

    def stop(self):
        """Stop the worker pool gracefully."""
        if self._stop.is_set():
            return  # Already stopping

        logger.info(
            "worker_pool_shutting_down",
            extra={"active_runs": len(self._active_runs), "reason": "waiting for running tasks to finish"},
        )
        self._stop.set()

        # Wait for executor to finish all running tasks
        self.executor.shutdown(wait=True)

        # PIN-413: Create immutable system record for worker shutdown
        _create_worker_system_record(
            event_type=SystemEventType.SHUTDOWN.value,
            severity=SystemSeverity.INFO.value,
            summary="Worker pool stopped",
            details={
                "graceful": True,
                "active_runs_at_shutdown": len(self._active_runs),
            },
            caused_by=SystemCausedBy.SYSTEM.value,
        )

        self.publisher.publish(
            "worker.pool.stopped", {"graceful": True, "active_runs_at_shutdown": len(self._active_runs)}
        )
        logger.info("worker_pool_stopped", extra={"graceful": True})


def _signal_handler(signum, _frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global _pool_instance
    sig_name = signal.Signals(signum).name
    logger.info("worker_pool_signal_received", extra={"signal": sig_name, "signum": signum})
    if _pool_instance:
        _pool_instance.stop()


def main():
    """Entry point for running worker pool as standalone process."""
    global _pool_instance

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    )

    # Verify database URL is set
    if not os.getenv("DATABASE_URL"):
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)

    # Initialize skills registry (required for skill execution)
    from ..skills import list_skills, load_all_skills

    load_all_skills()
    registered_skills = [s["name"] for s in list_skills()]
    logger.info("skills_initialized", extra={"count": len(registered_skills), "skills": registered_skills})

    pool = WorkerPool()
    _pool_instance = pool

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    logger.info("worker_pool_signal_handlers_registered", extra={"signals": ["SIGINT", "SIGTERM"]})

    try:
        pool.poll_and_dispatch()
    except KeyboardInterrupt:
        logger.info("worker_pool_interrupted")
    finally:
        pool.stop()


if __name__ == "__main__":
    main()
