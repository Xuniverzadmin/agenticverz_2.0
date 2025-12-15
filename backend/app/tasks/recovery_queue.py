# app/tasks/recovery_queue.py
"""
Redis-based task queue for M10 Recovery evaluation.

Provides async enqueue/dequeue functions for recovery candidate evaluation.

Usage:
    # Enqueue (from ingest endpoint)
    await enqueue_evaluation(candidate_id=123)

    # Dequeue (from worker)
    task = await dequeue_evaluation(timeout=5)
    if task:
        await process_task(task["candidate_id"])

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    RECOVERY_QUEUE_KEY: Queue key name (default: m10:evaluate)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.tasks.recovery_queue")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = os.getenv("RECOVERY_QUEUE_KEY", "m10:evaluate")
FAILED_QUEUE_KEY = f"{QUEUE_KEY}:failed"
PROCESSING_KEY = f"{QUEUE_KEY}:processing"

# Lazy-loaded Redis connection
_redis_client = None


async def get_redis():
    """Get or create async Redis client."""
    global _redis_client

    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            _redis_client = aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info(f"Connected to Redis at {REDIS_URL}")
        except ImportError:
            # Fallback to aioredis if redis.asyncio not available
            try:
                import aioredis
                _redis_client = await aioredis.from_url(
                    REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.error("Neither redis.asyncio nor aioredis available")
                raise

    return _redis_client


async def enqueue_evaluation(
    candidate_id: int,
    priority: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Enqueue a recovery candidate for evaluation.

    Args:
        candidate_id: ID of the recovery candidate
        priority: Priority level (0 = normal, higher = more urgent)
        metadata: Optional metadata to include with task

    Returns:
        True if enqueued successfully, False otherwise
    """
    try:
        redis = await get_redis()

        task = {
            "candidate_id": candidate_id,
            "priority": priority,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        payload = json.dumps(task)

        # Use LPUSH for FIFO with RPOP (or ZADD for priority queue)
        if priority > 0:
            # Priority queue using sorted set (higher score = higher priority)
            await redis.zadd(f"{QUEUE_KEY}:priority", {payload: priority})
        else:
            # Normal queue using list
            await redis.lpush(QUEUE_KEY, payload)

        logger.debug(f"Enqueued candidate {candidate_id} for evaluation")
        return True

    except Exception as e:
        logger.error(f"Failed to enqueue candidate {candidate_id}: {e}")
        return False


async def dequeue_evaluation(timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Dequeue a recovery candidate for evaluation.

    Checks priority queue first, then normal queue.

    Args:
        timeout: Blocking timeout in seconds (0 = non-blocking)

    Returns:
        Task dict with candidate_id, or None if queue empty
    """
    try:
        redis = await get_redis()

        # Check priority queue first (non-blocking)
        priority_items = await redis.zpopmax(f"{QUEUE_KEY}:priority", count=1)
        if priority_items:
            payload, _score = priority_items[0]
            task = json.loads(payload)
            # Mark as processing
            await redis.hset(PROCESSING_KEY, str(task["candidate_id"]), payload)
            return task

        # Check normal queue with blocking
        if timeout > 0:
            result = await redis.brpop(QUEUE_KEY, timeout=timeout)
            if result:
                _key, payload = result
                task = json.loads(payload)
                await redis.hset(PROCESSING_KEY, str(task["candidate_id"]), payload)
                return task
        else:
            payload = await redis.rpop(QUEUE_KEY)
            if payload:
                task = json.loads(payload)
                await redis.hset(PROCESSING_KEY, str(task["candidate_id"]), payload)
                return task

        return None

    except Exception as e:
        logger.error(f"Failed to dequeue task: {e}")
        return None


async def complete_evaluation(candidate_id: int, success: bool = True) -> bool:
    """
    Mark an evaluation task as complete.

    Args:
        candidate_id: ID of the candidate
        success: Whether evaluation succeeded

    Returns:
        True if marked successfully
    """
    try:
        redis = await get_redis()

        # Remove from processing set
        payload = await redis.hget(PROCESSING_KEY, str(candidate_id))
        await redis.hdel(PROCESSING_KEY, str(candidate_id))

        # If failed, move to failed queue for retry
        if not success and payload:
            task = json.loads(payload)
            task["failed_at"] = datetime.now(timezone.utc).isoformat()
            task["retry_count"] = task.get("retry_count", 0) + 1
            await redis.lpush(FAILED_QUEUE_KEY, json.dumps(task))

        return True

    except Exception as e:
        logger.error(f"Failed to complete task for candidate {candidate_id}: {e}")
        return False


async def requeue_failed(max_retries: int = 3) -> int:
    """
    Requeue failed tasks that haven't exceeded max retries.

    Args:
        max_retries: Maximum retry attempts

    Returns:
        Number of tasks requeued
    """
    try:
        redis = await get_redis()
        requeued = 0

        # Get all failed tasks
        while True:
            payload = await redis.rpop(FAILED_QUEUE_KEY)
            if not payload:
                break

            task = json.loads(payload)

            if task.get("retry_count", 0) < max_retries:
                # Requeue with lower priority
                task["priority"] = max(0, task.get("priority", 0) - 1)
                await redis.lpush(QUEUE_KEY, json.dumps(task))
                requeued += 1
                logger.info(f"Requeued candidate {task['candidate_id']} (retry {task['retry_count']})")
            else:
                logger.warning(f"Candidate {task['candidate_id']} exceeded max retries, dropping")

        return requeued

    except Exception as e:
        logger.error(f"Failed to requeue failed tasks: {e}")
        return 0


async def get_queue_stats() -> Dict[str, Any]:
    """
    Get queue statistics.

    Returns:
        Dict with queue lengths and processing count
    """
    try:
        redis = await get_redis()

        normal_len = await redis.llen(QUEUE_KEY)
        priority_len = await redis.zcard(f"{QUEUE_KEY}:priority")
        processing_len = await redis.hlen(PROCESSING_KEY)
        failed_len = await redis.llen(FAILED_QUEUE_KEY)

        return {
            "normal_queue": normal_len,
            "priority_queue": priority_len,
            "processing": processing_len,
            "failed": failed_len,
            "total_pending": normal_len + priority_len,
        }

    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {
            "error": str(e),
            "normal_queue": 0,
            "priority_queue": 0,
            "processing": 0,
            "failed": 0,
            "total_pending": 0,
        }


async def close():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


# Convenience exports
__all__ = [
    "enqueue_evaluation",
    "dequeue_evaluation",
    "complete_evaluation",
    "requeue_failed",
    "get_queue_stats",
    "get_redis",
    "close",
    "QUEUE_KEY",
]
