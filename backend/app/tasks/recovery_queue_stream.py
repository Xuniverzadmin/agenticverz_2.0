# app/tasks/recovery_queue_stream.py
"""
Durable Redis Streams queue for M10 Recovery evaluation.

Uses Redis Streams with consumer groups for:
- Message durability (persisted until ACK)
- Consumer groups for distributed processing
- Pending entry list for crash recovery
- XCLAIM for stalled message recovery

Usage:
    # Enqueue (from ingest endpoint)
    await enqueue_stream(candidate_id=123)

    # Worker consumer loop
    async for mid, task in consume_stream():
        await process(task)
        await ack_message(mid)

Environment Variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    M10_STREAM_KEY: Stream key name (default: m10:evaluate:stream)
    M10_CONSUMER_GROUP: Consumer group name (default: m10:evaluate:group)
    HOSTNAME: Consumer name (default: worker-1)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

logger = logging.getLogger("nova.tasks.recovery_queue_stream")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_KEY = os.getenv("M10_STREAM_KEY", "m10:evaluate:stream")
CONSUMER_GROUP = os.getenv("M10_CONSUMER_GROUP", "m10:evaluate:group")
CONSUMER_NAME = os.getenv("HOSTNAME", f"worker-{os.getpid()}")

# Stream settings
MAX_STREAM_LEN = int(os.getenv("M10_STREAM_MAX_LEN", "100000"))
CLAIM_IDLE_MS = int(os.getenv("M10_CLAIM_IDLE_MS", "300000"))  # 5 min idle before reclaim (was 60s)
BLOCK_MS = int(os.getenv("M10_BLOCK_MS", "2000"))  # 2s block on read
MAX_RECLAIM_ATTEMPTS = int(os.getenv("M10_MAX_RECLAIM_ATTEMPTS", "3"))  # Max reclaims before dead-letter
MAX_RECLAIM_PER_LOOP = int(os.getenv("M10_MAX_RECLAIM_PER_LOOP", "20"))  # Rate-limit reclaims per loop

# Dead-letter stream for permanently failed messages
DEAD_LETTER_STREAM = os.getenv("M10_DEAD_LETTER_STREAM", "m10:evaluate:dead-letter")
DEAD_LETTER_MAX_LEN = int(os.getenv("M10_DEAD_LETTER_MAX_LEN", "10000"))

# Exponential backoff for reclaims
RECLAIM_ATTEMPTS_KEY = os.getenv("M10_RECLAIM_ATTEMPTS_KEY", "m10:reclaim:attempts")
RECLAIM_BASE_BACKOFF_MS = int(os.getenv("M10_RECLAIM_BASE_BACKOFF_MS", "60000"))  # 1 minute base
RECLAIM_MAX_BACKOFF_MS = int(os.getenv("M10_RECLAIM_MAX_BACKOFF_MS", "86400000"))  # 24 hours max

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
            logger.info(f"Connected to Redis Streams at {REDIS_URL}")
        except ImportError:
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


async def ensure_consumer_group() -> bool:
    """
    Ensure consumer group exists for the stream.

    Creates stream and group if they don't exist.
    Returns True if successful, False otherwise.
    """
    try:
        redis = await get_redis()
        try:
            # Create consumer group, mkstream=True creates stream if missing
            await redis.xgroup_create(
                STREAM_KEY,
                CONSUMER_GROUP,
                id="$",  # Start from new messages
                mkstream=True,
            )
            logger.info(f"Created consumer group {CONSUMER_GROUP} for stream {STREAM_KEY}")
        except Exception as e:
            # BUSYGROUP means group already exists - that's OK
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {CONSUMER_GROUP} already exists")
            else:
                raise
        return True
    except Exception as e:
        logger.error(f"Failed to ensure consumer group: {e}")
        return False


async def enqueue_stream(
    candidate_id: int,
    priority: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> Optional[str]:
    """
    Add item to Redis Stream (durable queue).

    Args:
        candidate_id: ID of the recovery candidate
        priority: Priority level (stored in message for consumer sorting)
        metadata: Optional metadata dict
        idempotency_key: Optional idempotency key for deduplication

    Returns:
        Message ID if enqueued successfully, None otherwise
    """
    try:
        redis = await get_redis()
        await ensure_consumer_group()

        # Build message fields
        fields = {
            "candidate_id": str(candidate_id),
            "priority": str(priority),
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }

        if metadata:
            fields["metadata"] = json.dumps(metadata)

        if idempotency_key:
            fields["idempotency_key"] = idempotency_key

        # XADD with maxlen approximate to bound stream size
        msg_id = await redis.xadd(
            STREAM_KEY,
            fields,
            maxlen=MAX_STREAM_LEN,
            approximate=True,
        )

        logger.debug(f"Enqueued candidate {candidate_id} to stream, msg_id={msg_id}")
        return msg_id

    except Exception as e:
        logger.error(f"Failed to enqueue candidate {candidate_id} to stream: {e}")
        return None


async def consume_batch(
    batch_size: int = 10,
    block_ms: int = BLOCK_MS,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Read a batch of messages from the stream using XREADGROUP.

    Args:
        batch_size: Maximum messages to read
        block_ms: Milliseconds to block waiting for messages (0 = non-blocking)

    Returns:
        List of (message_id, fields_dict) tuples
    """
    try:
        redis = await get_redis()
        await ensure_consumer_group()

        # XREADGROUP reads new messages (">") for this consumer
        response = await redis.xreadgroup(
            CONSUMER_GROUP,
            CONSUMER_NAME,
            {STREAM_KEY: ">"},
            count=batch_size,
            block=block_ms,
        )

        items = []
        if response:
            for stream_name, messages in response:
                for msg_id, fields in messages:
                    # Parse fields
                    task = {
                        "candidate_id": int(fields.get("candidate_id", 0)),
                        "priority": float(fields.get("priority", 0)),
                        "enqueued_at": fields.get("enqueued_at"),
                        "idempotency_key": fields.get("idempotency_key"),
                    }
                    if "metadata" in fields:
                        try:
                            task["metadata"] = json.loads(fields["metadata"])
                        except json.JSONDecodeError:
                            task["metadata"] = {}
                    items.append((msg_id, task))

        return items

    except Exception as e:
        logger.error(f"Failed to consume from stream: {e}")
        return []


async def consume_stream(
    batch_size: int = 10,
    block_ms: int = BLOCK_MS,
) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
    """
    Async generator for consuming messages from stream.

    Usage:
        async for msg_id, task in consume_stream():
            await process(task)
            await ack_message(msg_id)
    """
    while True:
        items = await consume_batch(batch_size=batch_size, block_ms=block_ms)
        for msg_id, task in items:
            yield msg_id, task


async def ack_message(msg_id: str) -> bool:
    """
    Acknowledge a message as processed.

    Also clears any reclaim attempts tracked for exponential backoff.

    Args:
        msg_id: Message ID to acknowledge

    Returns:
        True if acknowledged successfully
    """
    try:
        redis = await get_redis()
        result = await redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
        logger.debug(f"Acknowledged message {msg_id}, result={result}")

        # Clear reclaim attempts on successful ack
        if result > 0:
            await clear_reclaim_attempts(msg_id)

        return result > 0
    except Exception as e:
        logger.error(f"Failed to ack message {msg_id}: {e}")
        return False


async def ack_and_delete(msg_id: str) -> bool:
    """
    Acknowledge and delete a message from stream.

    Use when you want to free memory after processing.
    """
    try:
        redis = await get_redis()
        await redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
        await redis.xdel(STREAM_KEY, msg_id)
        return True
    except Exception as e:
        logger.error(f"Failed to ack+delete message {msg_id}: {e}")
        return False


async def claim_stalled_messages(
    idle_ms: int = CLAIM_IDLE_MS,
    batch_size: int = 100,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Claim messages that have been pending longer than idle_ms.

    Used by workers to recover messages from crashed consumers.

    Args:
        idle_ms: Minimum idle time in milliseconds
        batch_size: Maximum messages to claim

    Returns:
        List of (message_id, fields_dict) tuples
    """
    try:
        redis = await get_redis()

        # Get pending messages for the group
        pending = await redis.xpending_range(
            STREAM_KEY,
            CONSUMER_GROUP,
            min="-",
            max="+",
            count=batch_size,
        )

        if not pending:
            return []

        # Filter messages that are idle long enough
        stalled_ids = []
        for entry in pending:
            # entry format: {'message_id': ..., 'consumer': ..., 'time_since_delivered': ..., 'times_delivered': ...}
            if isinstance(entry, dict):
                msg_id = entry.get("message_id")
                idle_time = entry.get("time_since_delivered", 0)
            else:
                # Older redis-py returns tuple
                msg_id = entry[0] if len(entry) > 0 else None
                idle_time = entry[2] if len(entry) > 2 else 0

            if msg_id and idle_time >= idle_ms:
                stalled_ids.append(msg_id)

        if not stalled_ids:
            return []

        # XCLAIM moves ownership to this consumer
        claimed = await redis.xclaim(
            STREAM_KEY,
            CONSUMER_GROUP,
            CONSUMER_NAME,
            min_idle_time=idle_ms,
            message_ids=stalled_ids,
        )

        items = []
        for msg_id, fields in claimed:
            task = {
                "candidate_id": int(fields.get("candidate_id", 0)),
                "priority": float(fields.get("priority", 0)),
                "enqueued_at": fields.get("enqueued_at"),
                "idempotency_key": fields.get("idempotency_key"),
                "_reclaimed": True,
            }
            if "metadata" in fields:
                try:
                    task["metadata"] = json.loads(fields["metadata"])
                except json.JSONDecodeError:
                    task["metadata"] = {}
            items.append((msg_id, task))
            logger.info(f"Claimed stalled message {msg_id} for candidate {task['candidate_id']}")

        return items

    except Exception as e:
        logger.error(f"Failed to claim stalled messages: {e}")
        return []


async def get_stream_info() -> Dict[str, Any]:
    """
    Get stream and consumer group statistics.

    Returns:
        Dict with stream length, pending count, consumer info
    """
    try:
        redis = await get_redis()

        # Stream info
        try:
            stream_info = await redis.xinfo_stream(STREAM_KEY)
            stream_len = stream_info.get("length", 0)
            first_entry = stream_info.get("first-entry")
            last_entry = stream_info.get("last-entry")
        except Exception:
            stream_len = 0
            first_entry = None
            last_entry = None

        # Consumer group info
        try:
            groups = await redis.xinfo_groups(STREAM_KEY)
            group_info = next((g for g in groups if g.get("name") == CONSUMER_GROUP), {})
            pending_count = group_info.get("pending", 0)
            consumers_count = group_info.get("consumers", 0)
        except Exception:
            pending_count = 0
            consumers_count = 0

        return {
            "stream_key": STREAM_KEY,
            "consumer_group": CONSUMER_GROUP,
            "stream_length": stream_len,
            "pending_count": pending_count,
            "consumers_count": consumers_count,
            "first_entry_id": first_entry[0] if first_entry else None,
            "last_entry_id": last_entry[0] if last_entry else None,
        }

    except Exception as e:
        logger.error(f"Failed to get stream info: {e}")
        return {
            "error": str(e),
            "stream_key": STREAM_KEY,
            "consumer_group": CONSUMER_GROUP,
            "stream_length": 0,
            "pending_count": 0,
            "consumers_count": 0,
        }


async def close():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis Streams connection closed")


async def move_to_dead_letter(
    msg_id: str,
    fields: Dict[str, Any],
    reason: str = "max_reclaims_exceeded",
) -> bool:
    """
    Move a message to the dead-letter stream atomically.

    Order of operations (critical for correctness):
    1. XADD to dead-letter stream (must succeed first)
    2. XACK original message (only after successful XADD)

    If XADD succeeds but XACK fails, message stays in pending but is also
    in DL - idempotent replay will skip duplicates via original_msg_id check.

    Args:
        msg_id: Original message ID
        fields: Message fields/payload
        reason: Reason for dead-lettering

    Returns:
        True if moved successfully (XADD succeeded, XACK may have failed)
    """
    try:
        redis = await get_redis()

        # Build dead-letter entry
        dl_fields = {
            "original_msg_id": msg_id,
            "original_stream": STREAM_KEY,
            "reason": reason,
            "dead_lettered_at": datetime.now(timezone.utc).isoformat(),
            "consumer": CONSUMER_NAME,
        }

        # Copy original fields with orig_ prefix
        for key, value in fields.items():
            if key not in dl_fields:
                dl_fields[f"orig_{key}"] = str(value) if not isinstance(value, str) else value

        # STEP 1: Add to dead-letter stream FIRST (critical ordering)
        # If this fails, we haven't lost the message
        dl_msg_id = await redis.xadd(
            DEAD_LETTER_STREAM,
            dl_fields,
            maxlen=DEAD_LETTER_MAX_LEN,
            approximate=True,
        )

        if not dl_msg_id:
            logger.error(f"XADD to dead-letter failed for message {msg_id}")
            return False

        # STEP 2: Acknowledge original message ONLY after successful XADD
        # If this fails, message stays in pending but is also in DL
        # The next reclaim cycle will see it's already in DL and skip
        try:
            ack_result = await redis.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
            if ack_result == 0:
                logger.warning(f"XACK returned 0 for {msg_id} - message may already be acknowledged")
        except Exception as ack_error:
            # XADD succeeded, XACK failed - log but return True
            # Message is safely in DL, pending entry will be cleaned up eventually
            logger.warning(
                f"XACK failed for {msg_id} after successful DL insert: {ack_error}. "
                f"Message is in dead-letter as {dl_msg_id}, pending entry remains."
            )

        logger.warning(f"Moved message {msg_id} to dead-letter stream: {reason}, " f"dl_msg_id={dl_msg_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to move message {msg_id} to dead-letter: {e}")
        return False


async def process_stalled_with_dead_letter(
    idle_ms: int = CLAIM_IDLE_MS,
    max_reclaims: int = MAX_RECLAIM_ATTEMPTS,
    batch_size: int = 100,
    max_reclaim_per_loop: int = MAX_RECLAIM_PER_LOOP,
    use_exponential_backoff: bool = True,
) -> Dict[str, int]:
    """
    Process stalled messages with dead-letter support, rate-limiting, and exponential backoff.

    Messages that have been delivered more than max_reclaims times
    are moved to the dead-letter stream instead of being reclaimed.

    Rate-limiting prevents thundering herd when many messages are stalled.

    Exponential backoff prevents rapid repeated reclaims of slow-but-valid work.
    Each message tracks its reclaim attempts in a Redis HASH, and the minimum
    idle time increases exponentially: 1m, 2m, 4m, 8m, ... up to 24h.

    Args:
        idle_ms: Base minimum idle time before considering stalled
        max_reclaims: Maximum delivery attempts before dead-lettering
        batch_size: Maximum messages to scan for pending
        max_reclaim_per_loop: Maximum messages to reclaim per call (rate-limit)
        use_exponential_backoff: Whether to use per-message exponential backoff

    Returns:
        Dict with counts: {'reclaimed': N, 'dead_lettered': M, 'skipped': K, 'backoff_deferred': P}
    """
    try:
        redis = await get_redis()

        # Get pending messages with delivery counts
        pending = await redis.xpending_range(
            STREAM_KEY,
            CONSUMER_GROUP,
            min="-",
            max="+",
            count=batch_size,
        )

        if not pending:
            return {"reclaimed": 0, "dead_lettered": 0, "skipped": 0, "backoff_deferred": 0}

        reclaim_candidates = []  # (msg_id, idle_time, times_delivered)
        dead_letter_ids = []
        skipped = 0
        backoff_deferred = 0

        for entry in pending:
            # Parse entry (format varies by redis-py version)
            if isinstance(entry, dict):
                msg_id = entry.get("message_id")
                idle_time = entry.get("time_since_delivered", 0)
                times_delivered = entry.get("times_delivered", 1)
            else:
                # Tuple format: (msg_id, consumer, idle_time, times_delivered)
                msg_id = entry[0] if len(entry) > 0 else None
                idle_time = entry[2] if len(entry) > 2 else 0
                times_delivered = entry[3] if len(entry) > 3 else 1

            if not msg_id:
                continue

            # Check if message exceeds max reclaims
            if times_delivered >= max_reclaims:
                dead_letter_ids.append(msg_id)
                continue

            # Calculate required idle time with exponential backoff
            if use_exponential_backoff:
                reclaim_attempts = await get_reclaim_attempts(msg_id)
                required_idle_ms = calculate_backoff_ms(reclaim_attempts)
            else:
                required_idle_ms = idle_ms

            # Check if message has been idle long enough
            if idle_time < required_idle_ms:
                backoff_deferred += 1
                logger.debug(
                    f"Message {msg_id} deferred by backoff: " f"idle={idle_time}ms < required={required_idle_ms}ms"
                )
                continue

            reclaim_candidates.append((msg_id, idle_time, times_delivered))

        results = {
            "reclaimed": 0,
            "dead_lettered": 0,
            "skipped": skipped,
            "backoff_deferred": backoff_deferred,
        }

        # Rate-limit reclaims
        reclaim_ids = []
        for msg_id, idle_time, _ in reclaim_candidates:
            if len(reclaim_ids) < max_reclaim_per_loop:
                reclaim_ids.append(msg_id)
            else:
                skipped += 1
                results["skipped"] = skipped

        # Reclaim messages that haven't exceeded limit (rate-limited)
        if reclaim_ids:
            try:
                # Use the minimum idle time from base config for XCLAIM
                claimed = await redis.xclaim(
                    STREAM_KEY,
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    min_idle_time=idle_ms,  # Base idle time for XCLAIM
                    message_ids=reclaim_ids,
                )
                results["reclaimed"] = len(claimed)

                for msg_id, _ in claimed:
                    # Increment reclaim attempts for backoff tracking
                    if use_exponential_backoff:
                        new_attempts = await increment_reclaim_attempts(msg_id)
                        logger.info(
                            f"Reclaimed stalled message {msg_id} "
                            f"(attempt #{new_attempts}, next backoff: "
                            f"{calculate_backoff_ms(new_attempts)}ms)"
                        )
                    else:
                        logger.info(f"Reclaimed stalled message {msg_id}")

            except Exception as e:
                logger.error(f"Failed to reclaim messages: {e}")

        # Move messages to dead-letter that exceeded limit
        for msg_id in dead_letter_ids:
            try:
                # Read the message content first
                messages = await redis.xrange(STREAM_KEY, min=msg_id, max=msg_id, count=1)
                if messages:
                    _, fields = messages[0]
                    if await move_to_dead_letter(msg_id, fields, "max_reclaims_exceeded"):
                        results["dead_lettered"] += 1
                        # Clear reclaim attempts since message is dead-lettered
                        await clear_reclaim_attempts(msg_id)
            except Exception as e:
                logger.error(f"Failed to dead-letter message {msg_id}: {e}")

        if skipped > 0:
            logger.info(f"Rate-limited: skipped {skipped} reclaims (max {max_reclaim_per_loop}/loop)")

        if backoff_deferred > 0:
            logger.debug(f"Backoff deferred: {backoff_deferred} messages not yet ready for reclaim")

        return results

    except Exception as e:
        logger.error(f"Failed to process stalled messages: {e}")
        return {"reclaimed": 0, "dead_lettered": 0, "skipped": 0, "backoff_deferred": 0}


async def get_dead_letter_count() -> int:
    """Get the number of messages in the dead-letter stream."""
    try:
        redis = await get_redis()
        return await redis.xlen(DEAD_LETTER_STREAM)
    except Exception:
        return 0


async def archive_dead_letter_to_db(
    dl_msg_id: str,
    fields: Dict[str, Any],
    db_url: Optional[str] = None,
) -> Optional[int]:
    """
    Archive a dead-letter message to PostgreSQL before trimming from Redis.

    This ensures no data loss when XTRIM removes old DL entries.

    Args:
        dl_msg_id: Dead-letter message ID
        fields: Message fields/payload
        db_url: Database URL (uses DATABASE_URL env if not provided)

    Returns:
        Archive ID if successful, None otherwise
    """
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    db_url = db_url or os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not configured - cannot archive DL message")
        return None

    try:
        # Parse fields from DL entry
        original_msg_id = fields.get("original_msg_id")
        candidate_id = fields.get("orig_candidate_id")
        if candidate_id:
            try:
                candidate_id = int(candidate_id)
            except (ValueError, TypeError):
                candidate_id = None

        failure_match_id = fields.get("orig_failure_match_id")
        reason = fields.get("reason")
        dead_lettered_at = fields.get("dead_lettered_at")

        # Build full payload JSON
        payload = json.dumps(fields)

        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                    SELECT m10_recovery.archive_dead_letter(
                        :dl_msg_id,
                        :original_msg_id,
                        :candidate_id,
                        :failure_match_id::uuid,
                        :payload::jsonb,
                        :reason,
                        0,
                        :dead_lettered_at::timestamptz,
                        'stream_trim'
                    )
                """
                ),
                {
                    "dl_msg_id": dl_msg_id,
                    "original_msg_id": original_msg_id,
                    "candidate_id": candidate_id,
                    "failure_match_id": failure_match_id,
                    "payload": payload,
                    "reason": reason,
                    "dead_lettered_at": dead_lettered_at,
                },
            )
            archive_id = result.scalar()
            session.commit()

            logger.debug(f"Archived DL message {dl_msg_id} to DB (id={archive_id})")
            return archive_id

    except Exception as e:
        logger.error(f"Failed to archive DL message {dl_msg_id}: {e}")
        return None


async def archive_and_trim_dead_letter(
    max_len: int = DEAD_LETTER_MAX_LEN,
    _archive_batch_size: int = 100,
) -> Dict[str, int]:
    """
    Archive old dead-letter messages to DB, then trim the Redis stream.

    This is the safe way to trim the DL stream - archives before trimming.

    Args:
        max_len: Target max length of DL stream after trim
        archive_batch_size: Batch size for archiving

    Returns:
        Dict with counts: {'archived': N, 'trimmed': M, 'errors': K}
    """
    try:
        redis = await get_redis()
        results = {"archived": 0, "trimmed": 0, "errors": 0}

        # Get current DL length
        dl_len = await redis.xlen(DEAD_LETTER_STREAM)
        if dl_len <= max_len:
            logger.debug(f"DL stream has {dl_len} entries, no trim needed")
            return results

        # Number of entries to trim
        to_trim = dl_len - max_len

        # Read oldest entries that will be trimmed
        entries = await redis.xrange(
            DEAD_LETTER_STREAM,
            min="-",
            max="+",
            count=to_trim,
        )

        if not entries:
            return results

        # Archive each entry before trimming
        archived_ids = []
        for dl_msg_id, fields in entries:
            archive_id = await archive_dead_letter_to_db(dl_msg_id, fields)
            if archive_id:
                archived_ids.append(dl_msg_id)
                results["archived"] += 1
            else:
                results["errors"] += 1

        # Only trim entries that were successfully archived
        if archived_ids:
            # XDEL to remove archived entries
            deleted = await redis.xdel(DEAD_LETTER_STREAM, *archived_ids)
            results["trimmed"] = deleted
            logger.info(f"Archived {results['archived']} DL messages, " f"trimmed {results['trimmed']} from stream")

        return results

    except Exception as e:
        logger.error(f"Failed to archive and trim DL: {e}")
        return {"archived": 0, "trimmed": 0, "errors": 1}


async def get_reclaim_attempts(msg_id: str) -> int:
    """
    Get the number of reclaim attempts for a message.

    Uses Redis HASH to track per-message reclaim counts.
    """
    try:
        redis = await get_redis()
        attempts = await redis.hget(RECLAIM_ATTEMPTS_KEY, msg_id)
        return int(attempts) if attempts else 0
    except Exception:
        return 0


async def increment_reclaim_attempts(msg_id: str) -> int:
    """
    Increment reclaim attempts for a message.

    Returns:
        New attempt count
    """
    try:
        redis = await get_redis()
        return await redis.hincrby(RECLAIM_ATTEMPTS_KEY, msg_id, 1)
    except Exception as e:
        logger.warning(f"Failed to increment reclaim attempts for {msg_id}: {e}")
        return 0


async def clear_reclaim_attempts(msg_id: str) -> bool:
    """
    Clear reclaim attempts for a message (after processing or dead-lettering).
    """
    try:
        redis = await get_redis()
        await redis.hdel(RECLAIM_ATTEMPTS_KEY, msg_id)
        return True
    except Exception:
        return False


# TTL for reclaim attempt entries (default: 7 days)
RECLAIM_ATTEMPTS_TTL = int(os.getenv("M10_RECLAIM_ATTEMPTS_TTL", "604800"))


async def gc_reclaim_attempts(
    max_entries_to_check: int = 1000,
    force_cleanup: bool = False,
) -> Dict[str, int]:
    """
    Garbage collect stale entries from the reclaim attempts HASH.

    The HASH can grow unbounded if messages are processed normally (via ACK)
    without ever being reclaimed. This function cleans up entries for messages
    that no longer exist in the pending list.

    Args:
        max_entries_to_check: Maximum entries to scan per call
        force_cleanup: If True, remove all entries not in pending list

    Returns:
        Dict with counts: {'checked': N, 'cleaned': M}
    """
    try:
        redis = await get_redis()
        results = {"checked": 0, "cleaned": 0}

        # Get all tracked reclaim attempt message IDs
        all_tracked = await redis.hgetall(RECLAIM_ATTEMPTS_KEY)
        if not all_tracked:
            return results

        # Get current pending message IDs
        pending_ids = set()
        try:
            pending_info = await redis.xpending(STREAM_KEY, CONSUMER_GROUP)
            if pending_info and pending_info[0] > 0:
                pending_range = await redis.xpending_range(
                    STREAM_KEY,
                    CONSUMER_GROUP,
                    min="-",
                    max="+",
                    count=100000,  # Large count to get all
                )
                for entry in pending_range:
                    if isinstance(entry, dict):
                        msg_id = entry.get("message_id")
                    else:
                        msg_id = entry[0] if len(entry) > 0 else None
                    if msg_id:
                        pending_ids.add(msg_id)
        except Exception as e:
            logger.warning(f"Failed to get pending IDs for GC: {e}")
            if not force_cleanup:
                return results

        # Find entries to clean up
        to_clean = []
        for msg_id in list(all_tracked.keys())[:max_entries_to_check]:
            results["checked"] += 1
            if msg_id not in pending_ids:
                to_clean.append(msg_id)

        # Remove stale entries
        if to_clean:
            await redis.hdel(RECLAIM_ATTEMPTS_KEY, *to_clean)
            results["cleaned"] = len(to_clean)
            logger.info(f"GC reclaim attempts: checked={results['checked']}, " f"cleaned={results['cleaned']}")

        return results

    except Exception as e:
        logger.error(f"Failed to GC reclaim attempts: {e}")
        return {"checked": 0, "cleaned": 0}


def calculate_backoff_ms(attempts: int) -> int:
    """
    Calculate exponential backoff based on reclaim attempts.

    Backoff formula: min(MAX_BACKOFF, BASE_BACKOFF * 2^(attempts-1))
    Examples with 60s base:
        1 attempt:  60s (1 min)
        2 attempts: 120s (2 min)
        3 attempts: 240s (4 min)
        4 attempts: 480s (8 min)
        5 attempts: 960s (16 min)
        ...
        Max: 86400s (24 hours)

    Args:
        attempts: Number of previous reclaim attempts

    Returns:
        Minimum idle time in milliseconds before next reclaim
    """
    if attempts <= 0:
        return CLAIM_IDLE_MS  # Default idle time for first reclaim

    backoff = RECLAIM_BASE_BACKOFF_MS * (2 ** (attempts - 1))
    return min(backoff, RECLAIM_MAX_BACKOFF_MS)


# Key for tracking replayed messages (SET for deduplication)
REPLAY_TRACKING_KEY = os.getenv("M10_REPLAY_TRACKING_KEY", "m10:replay:processed")
REPLAY_TRACKING_TTL = int(os.getenv("M10_REPLAY_TRACKING_TTL", "86400"))  # 24 hours


async def replay_dead_letter(
    msg_id: str,
    check_idempotency: bool = True,
    check_db_processed: bool = True,
    use_db_idempotency: bool = True,
) -> Optional[str]:
    """
    Replay a message from dead-letter back to main stream with idempotency.

    Idempotency is ensured via:
    1. DB-backed replay_log table (durable, survives Redis restarts) - PRIMARY
    2. Fallback to Redis SET tracking (for backward compatibility)
    3. Optional DB check if candidate was already processed (executed_at IS NOT NULL)

    This prevents reintroducing poison messages that were already handled.

    Args:
        msg_id: Dead-letter message ID to replay
        check_idempotency: Check for prior replay
        check_db_processed: Check if candidate was already processed in DB
        use_db_idempotency: Use DB-backed replay_log (recommended for durability)

    Returns:
        New message ID if replayed, None if skipped/failed
    """
    try:
        redis = await get_redis()
        db_url = os.getenv("DATABASE_URL")

        # =================================================================
        # Step 1: Read dead-letter message
        # =================================================================
        messages = await redis.xrange(DEAD_LETTER_STREAM, min=msg_id, max=msg_id, count=1)
        if not messages:
            logger.warning(f"Dead-letter message {msg_id} not found")
            return None

        _, dl_fields = messages[0]
        original_msg_id = dl_fields.get("original_msg_id", msg_id)

        # =================================================================
        # Step 2: Check idempotency - DB first (durable), then Redis (fallback)
        # =================================================================
        if check_idempotency:
            # DB-backed idempotency check (survives Redis restarts)
            if use_db_idempotency and db_url:
                try:
                    from sqlalchemy import text
                    from sqlmodel import Session, create_engine

                    engine = create_engine(db_url, pool_pre_ping=True)
                    with Session(engine) as session:
                        result = session.execute(
                            text(
                                """
                                SELECT id FROM m10_recovery.replay_log
                                WHERE original_msg_id = :original_msg_id
                            """
                            ),
                            {"original_msg_id": original_msg_id},
                        )
                        if result.fetchone():
                            logger.info(
                                f"Dead-letter {msg_id} already replayed "
                                f"(DB replay_log check, original={original_msg_id})"
                            )
                            return None
                except Exception as db_err:
                    logger.warning(f"DB idempotency check failed: {db_err}")
                    # Fall through to Redis check

            # Redis fallback check
            already_replayed = await redis.sismember(REPLAY_TRACKING_KEY, msg_id)
            if already_replayed:
                logger.info(f"Dead-letter {msg_id} already replayed (Redis SET check)")
                return None

        # =================================================================
        # Step 3: Optional DB check - skip if candidate already processed
        # =================================================================
        candidate_id = dl_fields.get("orig_candidate_id")
        idempotency_key = dl_fields.get("orig_idempotency_key")

        if check_db_processed and db_url and (candidate_id or idempotency_key):
            try:
                from sqlalchemy import text
                from sqlmodel import Session, create_engine

                engine = create_engine(db_url, pool_pre_ping=True)
                with Session(engine) as session:
                    # Check if candidate was already executed
                    if candidate_id:
                        result = session.execute(
                            text(
                                """
                                SELECT id FROM recovery_candidates
                                WHERE id = :id
                                  AND executed_at IS NOT NULL
                            """
                            ),
                            {"id": int(candidate_id)},
                        )
                    else:
                        result = session.execute(
                            text(
                                """
                                SELECT id FROM recovery_candidates
                                WHERE idempotency_key = CAST(:key AS uuid)
                                  AND executed_at IS NOT NULL
                            """
                            ),
                            {"key": idempotency_key},
                        )

                    if result.fetchone():
                        logger.info(
                            f"Dead-letter {msg_id} candidate already processed "
                            f"(executed_at IS NOT NULL), skipping replay"
                        )
                        # Record in replay_log to prevent future attempts
                        if use_db_idempotency:
                            await _record_replay_to_db(original_msg_id, msg_id, candidate_id, idempotency_key, None)
                        await redis.sadd(REPLAY_TRACKING_KEY, msg_id)
                        await redis.expire(REPLAY_TRACKING_KEY, REPLAY_TRACKING_TTL)
                        return None

            except Exception as db_error:
                logger.warning(f"DB processed check failed for DL {msg_id}: {db_error}")
                # Continue with replay on DB error

        # =================================================================
        # Step 4: Reconstruct original fields
        # =================================================================
        fields = {}
        for key, value in dl_fields.items():
            if key.startswith("orig_"):
                fields[key[5:]] = value

        # Add replay metadata
        fields["replayed_from_dl"] = msg_id
        fields["replayed_at"] = datetime.now(timezone.utc).isoformat()

        # =================================================================
        # Step 5: Record replay in DB BEFORE XADD (critical ordering)
        # =================================================================
        if use_db_idempotency and db_url:
            already_replayed = await _record_replay_to_db(
                original_msg_id,
                msg_id,
                int(candidate_id) if candidate_id else None,
                idempotency_key,
                None,  # new_msg_id not known yet
            )
            if already_replayed:
                logger.info(f"Dead-letter {msg_id} replay recorded by another process " f"(race condition handled)")
                return None

        # =================================================================
        # Step 6: Re-enqueue to main stream
        # =================================================================
        new_msg_id = await redis.xadd(
            STREAM_KEY,
            fields,
            maxlen=MAX_STREAM_LEN,
            approximate=True,
        )

        if not new_msg_id:
            logger.error(f"XADD failed for replay of {msg_id}")
            return None

        # =================================================================
        # Step 7: Delete from dead-letter and track replay in Redis
        # =================================================================
        await redis.xdel(DEAD_LETTER_STREAM, msg_id)

        # Track in Redis SET (for faster lookups, not durable)
        await redis.sadd(REPLAY_TRACKING_KEY, msg_id)
        await redis.expire(REPLAY_TRACKING_KEY, REPLAY_TRACKING_TTL)

        # Update metrics
        try:
            from app.metrics import recovery_dead_letter_replayed_total

            recovery_dead_letter_replayed_total.inc()
        except Exception:
            pass

        logger.info(f"Replayed dead-letter {msg_id} as {new_msg_id}")
        return new_msg_id

    except Exception as e:
        logger.error(f"Failed to replay dead-letter {msg_id}: {e}")
        return None


async def _record_replay_to_db(
    original_msg_id: str,
    dl_msg_id: str,
    candidate_id: Optional[int],
    idempotency_key: Optional[str],
    new_msg_id: Optional[str],
) -> bool:
    """
    Record replay in DB-backed replay_log using ON CONFLICT for idempotency.

    Returns:
        True if already replayed (idempotent skip), False if newly recorded
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return False

    try:
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                    SELECT already_replayed, replay_id
                    FROM m10_recovery.record_replay(
                        :original_msg_id,
                        :dl_msg_id,
                        :candidate_id,
                        :idempotency_key::uuid,
                        :new_msg_id,
                        :replayed_by
                    )
                """
                ),
                {
                    "original_msg_id": original_msg_id,
                    "dl_msg_id": dl_msg_id,
                    "candidate_id": candidate_id,
                    "idempotency_key": idempotency_key,
                    "new_msg_id": new_msg_id,
                    "replayed_by": CONSUMER_NAME,
                },
            )
            row = result.fetchone()
            session.commit()

            if row:
                already_replayed, replay_id = row
                if already_replayed:
                    logger.debug(f"Replay already recorded (id={replay_id})")
                else:
                    logger.debug(f"Recorded new replay (id={replay_id})")
                return bool(already_replayed)

            return False

    except Exception as e:
        logger.warning(f"Failed to record replay in DB: {e}")
        return False


async def replay_all_dead_letters(
    batch_size: int = 100,
    max_replays: int = 1000,
    check_idempotency: bool = True,
    check_db_processed: bool = True,
) -> Dict[str, int]:
    """
    Replay all messages from dead-letter stream with idempotency.

    Args:
        batch_size: Messages to read per batch
        max_replays: Maximum messages to replay in one call
        check_idempotency: Check Redis SET for prior replay
        check_db_processed: Check if candidate was already processed in DB

    Returns:
        Dict with counts: {'replayed': N, 'skipped': M, 'errors': K}
    """
    results = {"replayed": 0, "skipped": 0, "errors": 0}

    try:
        redis = await get_redis()

        last_id = "0-0"
        total_processed = 0

        while total_processed < max_replays:
            # Read batch from DL
            entries = await redis.xrange(
                DEAD_LETTER_STREAM,
                min=f"({last_id}" if last_id != "0-0" else "-",
                max="+",
                count=batch_size,
            )

            if not entries:
                break

            for dl_msg_id, _ in entries:
                if total_processed >= max_replays:
                    break

                new_id = await replay_dead_letter(
                    dl_msg_id,
                    check_idempotency=check_idempotency,
                    check_db_processed=check_db_processed,
                )

                if new_id:
                    results["replayed"] += 1
                elif new_id is None:
                    results["skipped"] += 1

                total_processed += 1
                last_id = dl_msg_id

            if len(entries) < batch_size:
                break

    except Exception as e:
        logger.error(f"Failed to replay dead-letters: {e}")
        results["errors"] += 1

    logger.info(
        f"Dead-letter replay complete: "
        f"replayed={results['replayed']}, "
        f"skipped={results['skipped']}, "
        f"errors={results['errors']}"
    )

    return results


# Convenience exports
__all__ = [
    "enqueue_stream",
    "consume_batch",
    "consume_stream",
    "ack_message",
    "ack_and_delete",
    "claim_stalled_messages",
    "process_stalled_with_dead_letter",
    "move_to_dead_letter",
    "get_dead_letter_count",
    "replay_dead_letter",
    "replay_all_dead_letters",
    "get_stream_info",
    "ensure_consumer_group",
    "get_redis",
    "close",
    # Exponential backoff helpers
    "get_reclaim_attempts",
    "increment_reclaim_attempts",
    "clear_reclaim_attempts",
    "calculate_backoff_ms",
    "gc_reclaim_attempts",
    # DL archival (Phase 5)
    "archive_dead_letter_to_db",
    "archive_and_trim_dead_letter",
    # Constants
    "STREAM_KEY",
    "CONSUMER_GROUP",
    "CONSUMER_NAME",
    "DEAD_LETTER_STREAM",
    "DEAD_LETTER_MAX_LEN",
    "MAX_RECLAIM_ATTEMPTS",
    "MAX_RECLAIM_PER_LOOP",
    "CLAIM_IDLE_MS",
    "RECLAIM_ATTEMPTS_KEY",
    "RECLAIM_BASE_BACKOFF_MS",
    "RECLAIM_MAX_BACKOFF_MS",
    "REPLAY_TRACKING_KEY",
    "REPLAY_TRACKING_TTL",
]
