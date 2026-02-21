# capability_id: CAP-012
# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Role: Prometheus metrics for embedding operations monitoring.
# Embedding Metrics for Memory Vector Store
"""
Prometheus metrics for embedding operations monitoring.

Tracks:
- Backfill progress
- API calls to embedding providers
- Latency and errors
- Vector query performance
"""

import os

from app.utils.metrics_helpers import get_or_create_counter, get_or_create_gauge, get_or_create_histogram

# Feature flags
VECTOR_SEARCH_ENABLED = os.getenv("VECTOR_SEARCH_ENABLED", "true").lower() == "true"
VECTOR_SEARCH_FALLBACK = os.getenv("VECTOR_SEARCH_FALLBACK", "true").lower() == "true"

# Daily quota limit (0 = unlimited)
EMBEDDING_DAILY_QUOTA = int(os.getenv("EMBEDDING_DAILY_QUOTA", "10000"))
EMBEDDING_QUOTA_EXCEEDED = False  # Runtime flag to block new requests

# Backfill metrics - using idempotent registration (PIN-120 PREV-1)
BACKFILL_PROGRESS = get_or_create_gauge(
    "aos_memory_backfill_progress_total",
    "Number of memory rows with embeddings backfilled",
    ["status"],  # success, pending, failed
)

BACKFILL_BATCH_DURATION = get_or_create_histogram(
    "aos_memory_backfill_batch_duration_seconds",
    "Time to process a backfill batch",
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
)

# Embedding API metrics
EMBEDDING_API_CALLS = get_or_create_counter(
    "aos_embedding_api_calls_total",
    "Total embedding API calls",
    ["provider", "status"],  # openai/anthropic, success/error
)

EMBEDDING_API_LATENCY = get_or_create_histogram(
    "aos_embedding_api_latency_seconds",
    "Embedding API call latency",
    ["provider"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10],
)

EMBEDDING_ERRORS = get_or_create_counter(
    "aos_embedding_errors_total",
    "Total embedding errors",
    ["provider", "error_type"],  # rate_limit, timeout, auth, other
)

EMBEDDING_TOKENS = get_or_create_counter(
    "aos_embedding_tokens_total",
    "Total tokens processed for embeddings",
    ["provider"],
)

# Vector search metrics
VECTOR_QUERY_LATENCY = get_or_create_histogram(
    "aos_vector_query_latency_seconds",
    "Vector similarity search latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1],
)

VECTOR_QUERY_RESULTS = get_or_create_histogram(
    "aos_vector_query_results_count",
    "Number of results returned from vector search",
    buckets=[0, 1, 5, 10, 20, 50, 100],
)

VECTOR_FALLBACK_COUNT = get_or_create_counter(
    "aos_vector_fallback_total",
    "Times vector search fell back to keyword search",
    ["reason"],  # no_embedding, below_threshold, error
)

# Index health metrics
VECTOR_INDEX_SIZE = get_or_create_gauge(
    "aos_vector_index_size",
    "Number of vectors in the index",
)

VECTOR_INDEX_NULL_COUNT = get_or_create_gauge(
    "aos_vector_index_null_count",
    "Number of rows without embeddings",
)


def update_index_stats(with_embedding: int, without_embedding: int):
    """Update index statistics gauges."""
    VECTOR_INDEX_SIZE.set(with_embedding)
    VECTOR_INDEX_NULL_COUNT.set(without_embedding)


def update_backfill_progress(success: int, pending: int, failed: int):
    """Update backfill progress gauges."""
    BACKFILL_PROGRESS.labels(status="success").set(success)
    BACKFILL_PROGRESS.labels(status="pending").set(pending)
    BACKFILL_PROGRESS.labels(status="failed").set(failed)


# Quota exceeded counter
EMBEDDING_QUOTA_EXCEEDED_COUNT = get_or_create_counter(
    "aos_embedding_quota_exhausted_total",
    "Times embedding quota was exceeded and requests blocked",
)

EMBEDDING_DAILY_CALL_COUNT = get_or_create_gauge(
    "aos_embedding_daily_calls",
    "Current daily embedding call count (resets at midnight UTC)",
)

_daily_call_count = 0
_last_reset_date = None


def check_embedding_quota() -> bool:
    """
    Check if embedding quota allows new requests.

    Returns:
        True if quota available, False if exhausted
    """
    global _daily_call_count, _last_reset_date, EMBEDDING_QUOTA_EXCEEDED

    from datetime import datetime, timezone

    # Reset counter at midnight UTC
    today = datetime.now(timezone.utc).date()
    if _last_reset_date != today:
        _daily_call_count = 0
        _last_reset_date = today
        EMBEDDING_QUOTA_EXCEEDED = False

    # Check quota (0 = unlimited)
    if EMBEDDING_DAILY_QUOTA > 0 and _daily_call_count >= EMBEDDING_DAILY_QUOTA:
        EMBEDDING_QUOTA_EXCEEDED = True
        EMBEDDING_QUOTA_EXCEEDED_COUNT.inc()
        return False

    return True


def increment_embedding_count():
    """Increment daily embedding call count."""
    global _daily_call_count
    _daily_call_count += 1
    EMBEDDING_DAILY_CALL_COUNT.set(_daily_call_count)


def get_embedding_quota_status() -> dict:
    """Get current quota status."""
    global _daily_call_count
    return {
        "daily_quota": EMBEDDING_DAILY_QUOTA,
        "current_count": _daily_call_count,
        "remaining": max(0, EMBEDDING_DAILY_QUOTA - _daily_call_count) if EMBEDDING_DAILY_QUOTA > 0 else -1,
        "exceeded": EMBEDDING_QUOTA_EXCEEDED,
    }
