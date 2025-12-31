# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: scheduler (standalone process)
#   Execution: async
# Role: Recovery claim processing orchestration (L5 execution wrapper)
# Authority: Recovery candidate state mutation (unevaluated → claimed → processed)
# Callers: Standalone process
# Allowed Imports: L4, L6
# Domain Engine: claim_decision_engine.py (L4)
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md (L5 Worker Rules)
# Reference: PIN-257 Phase E-4 Extraction #4
#
# GOVERNANCE NOTE: L5 owns all DB operations.
# L4 claim_decision_engine.py provides pure domain logic:
#   - is_candidate_claimable() - claim eligibility threshold
#   - determine_claim_status() - status from evaluation result
#   - get_result_confidence() - confidence extraction
# This L5 file:
#   - Orchestrates batch claim processing
#   - Calls L4 for domain decisions
#   - Persists results TO database (L6)

# app/worker/recovery_claim_worker.py
"""
M10 Recovery Claim Worker - Concurrent-safe batch processor

Background worker that:
1. Claims unevaluated recovery candidates using FOR UPDATE SKIP LOCKED
2. Processes claims in batches for efficiency
3. Handles graceful shutdown and unclaimed row release

Features:
- Concurrent-safe: Multiple workers can run without duplicating work
- Atomic claims: Uses SELECT ... FOR UPDATE SKIP LOCKED
- Fault-tolerant: Unclaimed rows are picked up on next poll
- Graceful shutdown: Releases claimed rows on SIGTERM/SIGINT

Usage:
    python -m app.worker.recovery_claim_worker --batch-size 50 --poll-interval 10

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- RECOVERY_WORKER_BATCH_SIZE: Candidates per batch (default: 50)
- RECOVERY_WORKER_POLL_INTERVAL: Seconds between polls (default: 10)
"""

import argparse
import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session, create_engine

logger = logging.getLogger("nova.worker.recovery_claim")

# Configuration
DEFAULT_BATCH_SIZE = int(os.getenv("RECOVERY_WORKER_BATCH_SIZE", "50"))
DEFAULT_POLL_INTERVAL = int(os.getenv("RECOVERY_WORKER_POLL_INTERVAL", "10"))

# Shutdown flag
_shutdown_requested = False


def signal_handler(signum, _frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    _shutdown_requested = True


class RecoveryClaimWorker:
    """
    Worker that claims and processes recovery candidates using FOR UPDATE SKIP LOCKED.

    This pattern ensures:
    - Multiple workers can run simultaneously without conflicts
    - Each worker claims distinct rows
    - Locked rows are skipped, preventing duplicate processing
    - Unclaimed rows are released on shutdown
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise RuntimeError("DATABASE_URL environment variable is required")

        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.engine = create_engine(
            self.db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self._stats = {
            "claimed": 0,
            "evaluated": 0,
            "errors": 0,
            "started_at": datetime.now(timezone.utc),
        }
        self._pending_ids: List[int] = []

    def _get_session(self) -> Session:
        """Create new database session."""
        return Session(self.engine)

    def claim_batch(self) -> List[Dict[str, Any]]:
        """
        Claim a batch of unevaluated candidates using FOR UPDATE SKIP LOCKED.

        Uses L4 CLAIM_ELIGIBILITY_THRESHOLD to determine which candidates need evaluation.
        Reference: PIN-257 Phase E-4 Extraction #4

        SQL Pattern:
        ```sql
        WITH claimed AS (
            SELECT id FROM recovery_candidates
            WHERE decision = 'pending' AND confidence <= :threshold
            ORDER BY created_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT :batch_size
        )
        UPDATE recovery_candidates rc
        SET execution_status = 'executing', updated_at = now()
        FROM claimed
        WHERE rc.id = claimed.id
        RETURNING rc.*;
        ```

        Returns:
            List of claimed candidate dicts
        """
        # L4 domain decision: claim eligibility threshold
        # Reference: PIN-257 Phase E-4 Extraction #4
        from app.services.claim_decision_engine import CLAIM_ELIGIBILITY_THRESHOLD

        session = self._get_session()
        try:
            result = session.execute(
                text(
                    """
                    WITH claimed AS (
                        SELECT id
                        FROM recovery_candidates
                        WHERE decision = 'pending'
                          AND (confidence IS NULL OR confidence <= :threshold)
                          AND (execution_status IS NULL OR execution_status = 'pending')
                        ORDER BY created_at ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT :batch_size
                    )
                    UPDATE recovery_candidates rc
                    SET
                        execution_status = 'executing',
                        updated_at = now()
                    FROM claimed
                    WHERE rc.id = claimed.id
                    RETURNING
                        rc.id,
                        rc.failure_match_id,
                        rc.suggestion,
                        rc.confidence,
                        rc.error_code,
                        rc.error_signature,
                        rc.occurrence_count,
                        rc.source,
                        rc.explain
                """
                ),
                {"batch_size": self.batch_size, "threshold": CLAIM_ELIGIBILITY_THRESHOLD},
            )

            rows = result.fetchall()
            session.commit()

            candidates = []
            for row in rows:
                candidate = {
                    "id": row[0],
                    "failure_match_id": str(row[1]) if row[1] else None,
                    "suggestion": row[2],
                    "confidence": float(row[3]) if row[3] else 0.0,
                    "error_code": row[4],
                    "error_signature": row[5],
                    "occurrence_count": row[6] or 1,
                    "source": row[7],
                    "explain": json.loads(row[8]) if isinstance(row[8], str) else (row[8] or {}),
                }
                candidates.append(candidate)
                self._pending_ids.append(candidate["id"])

            if candidates:
                logger.info(f"Claimed {len(candidates)} candidates for evaluation")
                self._stats["claimed"] += len(candidates)

            return candidates

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to claim batch: {e}")
            return []
        finally:
            session.close()

    async def evaluate_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single candidate using the recovery evaluator.

        Args:
            candidate: Candidate dict from claim_batch

        Returns:
            Evaluation result dict
        """
        from app.worker.recovery_evaluator import (
            FailureEvent,
            RecoveryEvaluator,
        )

        event = FailureEvent(
            failure_match_id=candidate["failure_match_id"] or str(candidate["id"]),
            error_code=candidate.get("error_code", "UNKNOWN"),
            error_message=candidate.get("suggestion", ""),
            metadata={
                "occurrence_count": candidate.get("occurrence_count", 1),
                "source": candidate.get("source"),
            },
        )

        evaluator = RecoveryEvaluator(db_url=self.db_url)
        outcome = await evaluator.evaluate(event)

        return {
            "candidate_id": candidate["id"],
            "confidence": outcome.confidence,
            "suggested_action": outcome.suggested_action,
            "auto_executed": outcome.auto_executed,
            "error": outcome.error,
            "duration_ms": outcome.duration_ms,
        }

    def update_candidate(
        self,
        candidate_id: int,
        result: Dict[str, Any],
    ) -> None:
        """
        Update candidate with evaluation results.

        Args:
            candidate_id: ID of candidate to update
            result: Evaluation result dict
        """
        # L4 domain decisions: status and confidence extraction
        # Reference: PIN-257 Phase E-4 Extraction #4
        from app.services.claim_decision_engine import (
            determine_claim_status,
            get_result_confidence,
        )

        status = determine_claim_status(result)
        confidence = get_result_confidence(result)

        session = self._get_session()
        try:
            session.execute(
                text(
                    """
                    UPDATE recovery_candidates
                    SET
                        confidence = :confidence,
                        execution_status = :status,
                        updated_at = now()
                    WHERE id = :id
                """
                ),
                {
                    "id": candidate_id,
                    "confidence": confidence,
                    "status": status,
                },
            )
            session.commit()

            # Remove from pending list
            if candidate_id in self._pending_ids:
                self._pending_ids.remove(candidate_id)

            self._stats["evaluated"] += 1

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update candidate {candidate_id}: {e}")
            self._stats["errors"] += 1
        finally:
            session.close()

    def release_pending(self) -> None:
        """
        Release all pending claimed candidates back to 'pending' status.

        Called on shutdown to ensure claimed rows aren't stuck.
        """
        if not self._pending_ids:
            return

        session = self._get_session()
        try:
            session.execute(
                text(
                    """
                    UPDATE recovery_candidates
                    SET
                        execution_status = 'pending',
                        updated_at = now()
                    WHERE id = ANY(:ids)
                      AND execution_status = 'executing'
                """
                ),
                {"ids": self._pending_ids},
            )
            session.commit()
            logger.info(f"Released {len(self._pending_ids)} pending candidates")
            self._pending_ids.clear()

        except Exception as e:
            session.rollback()
            logger.warning(f"Failed to release pending candidates: {e}")
        finally:
            session.close()

    async def process_batch(self, candidates: List[Dict[str, Any]]) -> int:
        """
        Process a batch of claimed candidates.

        Args:
            candidates: List of candidate dicts

        Returns:
            Number of successfully processed candidates
        """
        processed = 0

        for candidate in candidates:
            if _shutdown_requested:
                logger.info("Shutdown requested, stopping batch processing")
                break

            candidate_id = candidate["id"]

            try:
                result = await self.evaluate_candidate(candidate)
                self.update_candidate(candidate_id, result)
                processed += 1

                logger.debug(
                    f"Evaluated candidate {candidate_id}: "
                    f"confidence={result.get('confidence', 0):.2f}, "
                    f"action={result.get('suggested_action')}"
                )

            except Exception as e:
                logger.error(f"Failed to process candidate {candidate_id}: {e}")
                self.update_candidate(candidate_id, {"error": str(e), "confidence": 0.1})

        return processed

    async def run(self) -> None:
        """
        Main worker loop.

        Polls for unevaluated candidates and processes them.
        Runs until shutdown signal received.
        """
        logger.info(
            f"Starting recovery claim worker: batch_size={self.batch_size}, poll_interval={self.poll_interval}s"
        )

        try:
            while not _shutdown_requested:
                try:
                    # Claim batch
                    candidates = self.claim_batch()

                    if candidates:
                        # Process batch
                        processed = await self.process_batch(candidates)
                        logger.info(
                            f"Processed {processed}/{len(candidates)} candidates. "
                            f"Total: claimed={self._stats['claimed']}, "
                            f"evaluated={self._stats['evaluated']}, "
                            f"errors={self._stats['errors']}"
                        )
                    else:
                        # No work, sleep
                        logger.debug(f"No candidates to evaluate, sleeping {self.poll_interval}s")
                        await asyncio.sleep(self.poll_interval)

                except asyncio.CancelledError:
                    logger.info("Worker cancelled")
                    break
                except Exception as e:
                    logger.error(f"Worker error: {e}", exc_info=True)
                    await asyncio.sleep(self.poll_interval)

        finally:
            # Release any pending claimed candidates
            self.release_pending()

            # Log final stats
            runtime = (datetime.now(timezone.utc) - self._stats["started_at"]).total_seconds()
            logger.info(
                f"Worker shutdown. Runtime: {runtime:.1f}s, "
                f"Claimed: {self._stats['claimed']}, "
                f"Evaluated: {self._stats['evaluated']}, "
                f"Errors: {self._stats['errors']}"
            )


async def main_async(args):
    """Async main entry point."""
    worker = RecoveryClaimWorker(
        batch_size=args.batch_size,
        poll_interval=args.poll_interval,
    )
    await worker.run()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="M10 Recovery Claim Worker")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of candidates to claim per batch (default: {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Seconds between polls when no work (default: {DEFAULT_POLL_INTERVAL})",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Run async worker
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
