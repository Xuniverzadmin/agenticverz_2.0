# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Deterministic execution utilities (pure computation, no boundary crossing)
# Callers: runtime, workers
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy (runtime)
# Reference: PIN-470, Determinism
# NOTE: Reclassified L6→L5 (2026-01-24) - No DB/cache boundary, pure algorithmic computation

# Deterministic Utilities for M11 Skills
# Provides seeded randomness and backoff for replay-safe operations

import hashlib
import hmac
import struct
import time
from typing import Optional


def seeded_jitter(workflow_run_id: str, attempt: int) -> float:
    """
    Generate deterministic jitter value from workflow ID and attempt number.

    Uses HMAC-SHA256 to produce a consistent float between 0 and 1
    that is reproducible given the same inputs.

    Args:
        workflow_run_id: Unique workflow run identifier
        attempt: Current attempt number (1-based)

    Returns:
        Float between 0.0 and 1.0
    """
    key = workflow_run_id.encode()
    msg = f"{workflow_run_id}:{attempt}".encode()
    digest = hmac.new(key, msg, hashlib.sha256).digest()
    # Take first 4 bytes and convert to float 0..1
    return struct.unpack(">I", digest[:4])[0] / (2**32)


def deterministic_backoff_ms(
    workflow_run_id: str,
    attempt: int,
    initial_ms: int = 200,
    multiplier: float = 2.0,
    jitter_pct: float = 0.1,
    max_ms: int = 10000,
) -> int:
    """
    Calculate exponential backoff with deterministic jitter.

    The jitter is derived from the workflow_run_id and attempt number,
    making the backoff sequence reproducible for replay verification.

    Args:
        workflow_run_id: Unique workflow run identifier
        attempt: Current attempt number (1-based)
        initial_ms: Initial backoff in milliseconds
        multiplier: Exponential multiplier per attempt
        jitter_pct: Jitter percentage (0.1 = +/- 10%)
        max_ms: Maximum backoff in milliseconds

    Returns:
        Backoff duration in milliseconds
    """
    # Base exponential backoff
    base = initial_ms * (multiplier ** (attempt - 1))

    # Get deterministic jitter value 0..1
    jitter = seeded_jitter(workflow_run_id, attempt)

    # Apply jitter: range is [1 - jitter_pct, 1 + jitter_pct]
    factor = 1 + (2 * jitter - 1) * jitter_pct

    # Calculate final backoff with cap
    return int(min(base * factor, max_ms))


def deterministic_timestamp(workflow_run_id: str, step_index: int, base_time: Optional[float] = None) -> int:
    """
    Generate a deterministic timestamp for replay scenarios.

    In production, returns current time. In replay mode with base_time,
    returns a reproducible offset from base_time.

    Args:
        workflow_run_id: Unique workflow run identifier
        step_index: Step index within workflow
        base_time: Base timestamp for replay (None = use current time)

    Returns:
        Unix timestamp in seconds
    """
    if base_time is None:
        return int(time.time())

    # In replay mode, add deterministic offset
    jitter = seeded_jitter(workflow_run_id, step_index)
    offset = int(jitter * 60)  # Up to 60 second offset
    return int(base_time) + offset


def generate_idempotency_key(workflow_run_id: str, skill_name: str, step_index: int) -> str:
    """
    Generate a deterministic idempotency key for a skill execution.

    Args:
        workflow_run_id: Unique workflow run identifier
        skill_name: Name of the skill being executed
        step_index: Step index within workflow

    Returns:
        Idempotency key string
    """
    data = f"{workflow_run_id}:{skill_name}:{step_index}".encode()
    digest = hashlib.sha256(data).hexdigest()[:16]
    return f"idem_{digest}"


def hash_params(params: dict) -> str:
    """
    Generate a hash of skill parameters for idempotency comparison.

    Args:
        params: Skill input parameters

    Returns:
        SHA256 hash prefix (16 chars)
    """
    import json

    canonical = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
