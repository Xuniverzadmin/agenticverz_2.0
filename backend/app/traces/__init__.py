# AOS Trace Storage Module
# M6/M8 Deliverable: Run traces with correlation IDs, PostgreSQL storage, replay enforcement

from .models import (
    TraceStep,
    TraceSummary,
    TraceRecord,
    TraceStatus,
    ParityResult,
    compare_traces,
)
from .store import TraceStore, SQLiteTraceStore
from .redact import (
    redact_trace_data,
    redact_dict,
    redact_json_string,
    is_sensitive_field,
    add_sensitive_field,
)
from .replay import (
    ReplayBehavior,
    ReplayEnforcer,
    ReplayResult,
    ReplayMismatchError,
    IdempotencyViolationError,
    get_replay_enforcer,
)
from .idempotency import (
    IdempotencyResult,
    IdempotencyResponse,
    RedisIdempotencyStore,
    InMemoryIdempotencyStore,
    get_idempotency_store,
    hash_request,
    canonical_json,
)

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
    TracesMetrics,
    get_traces_metrics,
    instrument_trace_request,
    TRACE_LATENCY_HISTOGRAM,
    TRACE_REQUESTS_COUNTER,
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
