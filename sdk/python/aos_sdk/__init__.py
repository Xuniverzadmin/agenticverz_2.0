"""
AOS SDK - Python SDK for the Agentic Operating System

The most predictable, reliable, deterministic SDK for building machine-native agents.

Core Classes:
    AOSClient: HTTP client for AOS API
    RuntimeContext: Deterministic runtime context (seed, time, RNG)
    Trace: Execution trace for replay and verification

Usage:
    from aos_sdk import AOSClient, RuntimeContext, Trace

    # Deterministic simulation
    ctx = RuntimeContext(seed=42, now="2025-12-06T12:00:00Z")
    client = AOSClient()
    result = client.simulate(plan, seed=ctx.seed)

    # Trace and replay
    trace = Trace(seed=42, plan=plan)
    trace.add_step(...)
    trace.finalize()
    trace.save("run.trace.json")
"""

from .client import AOSClient, AOSError
from .runtime import RuntimeContext, canonical_json, hash_trace, freeze_time
from .trace import (
    Trace, TraceStep, diff_traces, hash_data, create_trace_from_context,
    TRACE_SCHEMA_VERSION, ReplayResult, replay_step, generate_idempotency_key,
    reset_idempotency_state, mark_idempotency_key_executed, is_idempotency_key_executed
)

__version__ = "0.1.0"
__all__ = [
    # Client
    "AOSClient",
    "AOSError",
    # Runtime
    "RuntimeContext",
    "canonical_json",
    "hash_trace",
    "freeze_time",
    # Trace
    "Trace",
    "TraceStep",
    "diff_traces",
    "hash_data",
    "create_trace_from_context",
    "TRACE_SCHEMA_VERSION",
    # Replay & Idempotency
    "ReplayResult",
    "replay_step",
    "generate_idempotency_key",
    "reset_idempotency_state",
    "mark_idempotency_key_executed",
    "is_idempotency_key_executed",
    # Version
    "__version__"
]
