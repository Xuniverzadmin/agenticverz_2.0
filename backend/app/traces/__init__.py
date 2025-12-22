# AOS Trace Storage Module
# M6/M8 Deliverable: Run traces with correlation IDs, PostgreSQL storage, replay enforcement

from .idempotency import (
    IdempotencyResponse,
    IdempotencyResult,
    InMemoryIdempotencyStore,
    RedisIdempotencyStore,
    canonical_json,
    get_idempotency_store,
    hash_request,
)
from .models import (
    ParityResult,
    TraceRecord,
    TraceStatus,
    TraceStep,
    TraceSummary,
    compare_traces,
)
from .redact import (
    add_sensitive_field,
    is_sensitive_field,
    redact_dict,
    redact_json_string,
    redact_trace_data,
)
from .replay import (
    IdempotencyViolationError,
    ReplayBehavior,
    ReplayEnforcer,
    ReplayMismatchError,
    ReplayResult,
    get_replay_enforcer,
)
from .store import SQLiteTraceStore, TraceStore

# Conditionally import PostgreSQL store
try:
    from .pg_store import PostgresTraceStore, get_postgres_trace_store

    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    PostgresTraceStore = None
    get_postgres_trace_store = None

# Traces metrics
from .traces_metrics import (
    TRACE_LATENCY_HISTOGRAM,
    TRACE_REQUESTS_COUNTER,
    TracesMetrics,
    get_traces_metrics,
    instrument_trace_request,
)

__all__ = [
    # Models
    "TraceStep",
    "TraceSummary",
    "TraceRecord",
    "TraceStatus",
    "ParityResult",
    "compare_traces",
    # SQLite Store
    "TraceStore",
    "SQLiteTraceStore",
    # PostgreSQL Store (optional)
    "PostgresTraceStore",
    "get_postgres_trace_store",
    "HAS_POSTGRES",
    # Redaction
    "redact_trace_data",
    "redact_dict",
    "redact_json_string",
    "is_sensitive_field",
    "add_sensitive_field",
    # Replay
    "ReplayBehavior",
    "ReplayEnforcer",
    "ReplayResult",
    "ReplayMismatchError",
    "IdempotencyViolationError",
    "get_replay_enforcer",
    # Idempotency (M8)
    "IdempotencyResult",
    "IdempotencyResponse",
    "RedisIdempotencyStore",
    "InMemoryIdempotencyStore",
    "get_idempotency_store",
    "hash_request",
    "canonical_json",
    # Traces Metrics (M8)
    "TracesMetrics",
    "get_traces_metrics",
    "instrument_trace_request",
    "TRACE_LATENCY_HISTOGRAM",
    "TRACE_REQUESTS_COUNTER",
]
