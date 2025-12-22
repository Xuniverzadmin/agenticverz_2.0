#!/usr/bin/env python3
"""
Memory Embeddings Backfill Script

Rate-limited backfill for existing memory rows without embeddings.

Features:
- Configurable batch size and rate limiting
- Progress tracking with Prometheus metrics
- Retry logic with exponential backoff
- Graceful shutdown handling
- Resume from last position

Usage:
    # Dry run (count only)
    python scripts/backfill_memory_embeddings.py --dry-run

    # Backfill with defaults (100 rows/batch, 30s delay)
    python scripts/backfill_memory_embeddings.py

    # Custom batch size and rate
    python scripts/backfill_memory_embeddings.py --batch-size=50 --delay=60

    # Limit total rows
    python scripts/backfill_memory_embeddings.py --limit=1000
"""

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from typing import List, Optional, Tuple

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Graceful shutdown flag
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, requesting graceful shutdown...")
    _shutdown_requested = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


async def get_pending_count(session) -> Tuple[int, int]:
    """Get count of rows with and without embeddings."""
    from sqlalchemy import text as sql_text

    result = await session.execute(
        sql_text(
            """
        SELECT
            count(*) FILTER (WHERE embedding IS NULL) AS pending,
            count(*) FILTER (WHERE embedding IS NOT NULL) AS completed
        FROM memories
    """
        )
    )
    row = result.fetchone()
    return row.pending, row.completed


async def get_batch_without_embeddings(
    session,
    batch_size: int,
    offset: int = 0,
) -> List[dict]:
    """Get a batch of rows without embeddings."""
    from sqlalchemy import text as sql_text

    result = await session.execute(
        sql_text(
            """
            SELECT id, text
            FROM memories
            WHERE embedding IS NULL
            ORDER BY created_at ASC
            LIMIT :limit OFFSET :offset
        """
        ),
        {"limit": batch_size, "offset": offset},
    )

    return [{"id": row.id, "text": row.text} for row in result.fetchall()]


async def update_embedding(session, memory_id: str, embedding: List[float]) -> bool:
    """Update a single row with its embedding."""
    from sqlalchemy import text as sql_text

    try:
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"
        # Use CAST instead of :: to avoid asyncpg parameter parsing issues
        await session.execute(
            sql_text(
                """
                UPDATE memories
                SET embedding = CAST(:embedding AS vector)
                WHERE id = :id
            """
            ),
            {"id": memory_id, "embedding": embedding_str},
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update embedding for {memory_id}: {e}")
        return False


async def generate_embedding(text: str, provider: str = "openai") -> Optional[List[float]]:
    """Generate embedding for text using configured provider."""
    import httpx

    from app.memory.embedding_metrics import (
        EMBEDDING_API_CALLS,
        EMBEDDING_API_LATENCY,
        EMBEDDING_ERRORS,
    )

    start = time.perf_counter()

    if not text or not text.strip():
        logger.warning("Empty text, skipping embedding")
        return None

    # Truncate to avoid token limits
    text = text[:8000]

    try:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                        "input": text,
                    },
                )

                if response.status_code == 429:
                    EMBEDDING_ERRORS.labels(provider=provider, error_type="rate_limit").inc()
                    raise Exception("Rate limited")

                response.raise_for_status()
                data = response.json()
                embedding = data["data"][0]["embedding"]

                latency = time.perf_counter() - start
                EMBEDDING_API_CALLS.labels(provider=provider, status="success").inc()
                EMBEDDING_API_LATENCY.labels(provider=provider).observe(latency)

                return embedding
        else:
            raise ValueError(f"Unknown provider: {provider}")

    except Exception as e:
        latency = time.perf_counter() - start
        EMBEDDING_API_CALLS.labels(provider=provider, status="error").inc()
        EMBEDDING_API_LATENCY.labels(provider=provider).observe(latency)

        error_type = "rate_limit" if "rate" in str(e).lower() else "other"
        EMBEDDING_ERRORS.labels(provider=provider, error_type=error_type).inc()

        logger.error(f"Embedding generation failed: {e}")
        return None


async def backfill_batch(
    session,
    batch: List[dict],
    provider: str,
    retry_count: int = 3,
) -> Tuple[int, int]:
    """
    Process a batch of rows.

    Returns:
        (success_count, failure_count)
    """
    from app.memory.embedding_metrics import BACKFILL_BATCH_DURATION

    start = time.perf_counter()
    success = 0
    failed = 0

    for row in batch:
        if _shutdown_requested:
            logger.info("Shutdown requested, stopping batch processing")
            break

        # Retry logic with exponential backoff
        for attempt in range(retry_count):
            embedding = await generate_embedding(row["text"], provider)

            if embedding:
                if await update_embedding(session, row["id"], embedding):
                    success += 1
                    break
                else:
                    failed += 1
                    break
            else:
                if attempt < retry_count - 1:
                    delay = 2**attempt  # Exponential backoff
                    logger.warning(f"Retrying {row['id']} in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                else:
                    failed += 1
                    logger.error(f"Failed to generate embedding for {row['id']} after {retry_count} attempts")

    await session.commit()

    duration = time.perf_counter() - start
    BACKFILL_BATCH_DURATION.observe(duration)

    return success, failed


async def run_backfill(
    batch_size: int = 100,
    delay_seconds: float = 30.0,
    limit: Optional[int] = None,
    dry_run: bool = False,
    provider: str = "openai",
):
    """
    Run the backfill process.

    Args:
        batch_size: Number of rows per batch
        delay_seconds: Delay between batches (rate limiting)
        limit: Max total rows to process (None = all)
        dry_run: If True, only count rows
        provider: Embedding provider (openai/anthropic)
    """
    from app.db_async import async_session_context
    from app.memory.embedding_metrics import update_backfill_progress, update_index_stats

    logger.info(f"Starting backfill: batch_size={batch_size}, delay={delay_seconds}s, limit={limit}, dry_run={dry_run}")

    async with async_session_context() as session:
        # Get initial counts
        pending, completed = await get_pending_count(session)
        update_index_stats(completed, pending)

        logger.info(f"Current status: {pending} pending, {completed} completed")

        if dry_run:
            logger.info("Dry run complete, no changes made")
            return

        if pending == 0:
            logger.info("No rows pending, nothing to do")
            return

        total_success = 0
        total_failed = 0
        batch_num = 0

        while not _shutdown_requested:
            # Get next batch
            batch = await get_batch_without_embeddings(session, batch_size)

            if not batch:
                logger.info("No more pending rows")
                break

            batch_num += 1
            logger.info(f"Processing batch {batch_num} ({len(batch)} rows)")

            # Process batch
            success, failed = await backfill_batch(session, batch, provider)

            total_success += success
            total_failed += failed

            # Update metrics
            pending, completed = await get_pending_count(session)
            update_backfill_progress(total_success, pending, total_failed)
            update_index_stats(completed, pending)

            logger.info(
                f"Batch {batch_num} complete: {success} success, {failed} failed. "
                f"Total: {total_success}/{total_success + total_failed}. Pending: {pending}"
            )

            # Check limit
            if limit and total_success + total_failed >= limit:
                logger.info(f"Reached limit of {limit} rows")
                break

            # Rate limiting delay
            if pending > 0 and not _shutdown_requested:
                logger.info(f"Waiting {delay_seconds}s before next batch...")
                await asyncio.sleep(delay_seconds)

        # Final summary
        logger.info(f"Backfill complete: {total_success} success, {total_failed} failed. " f"Pending: {pending}")


def main():
    parser = argparse.ArgumentParser(description="Backfill memory embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of rows per batch (default: 100)")
    parser.add_argument("--delay", type=float, default=30.0, help="Delay between batches in seconds (default: 30)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum rows to process (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Only count rows, don't process")
    parser.add_argument(
        "--provider", choices=["openai", "anthropic"], default="openai", help="Embedding provider (default: openai)"
    )

    args = parser.parse_args()

    asyncio.run(
        run_backfill(
            batch_size=args.batch_size,
            delay_seconds=args.delay,
            limit=args.limit,
            dry_run=args.dry_run,
            provider=args.provider,
        )
    )


if __name__ == "__main__":
    main()
