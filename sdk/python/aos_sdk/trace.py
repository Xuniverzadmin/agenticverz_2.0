"""
AOS Trace Schema v1.1

Canonical trace format for simulation replay and verification.

Design Principles:
- Traces are immutable records of simulation/execution
- DETERMINISTIC fields (seed, plan, input/output hashes) form the root_hash
- AUDIT fields (timestamps, duration_ms) are preserved but excluded from hash
- Canonical JSON ensures identical bytes for identical data
- Hash chain provides integrity verification
- Schema versioned for future compatibility

Hash Rules (v1.1):
- root_hash computed ONLY from deterministic fields
- Audit fields (timestamp, duration_ms) preserved for logging but excluded
- Two traces with same seed+plan+inputs+outputs will have IDENTICAL root_hash

Usage:
    from aos_sdk.trace import Trace, TraceStep

    trace = Trace(seed=42, plan=[...])
    trace.add_step(...)
    trace.finalize()

    # Save/load
    trace.save("run_001.trace.json")
    loaded = Trace.load("run_001.trace.json")

    # Verify replay - root_hash stable across runs
    assert trace.root_hash == loaded.root_hash
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from .runtime import RuntimeContext, canonical_json

# Trace schema version - bumped to 1.1 for deterministic hashing
TRACE_SCHEMA_VERSION = "1.1.0"


@dataclass
class TraceStep:
    """
    Individual step in a trace.

    Fields are split into:
    - DETERMINISTIC: step_index, skill_id, input_hash, output_hash, rng_state_before, outcome, idempotency_key
    - AUDIT: timestamp, duration_ms, error_code (for debugging, excluded from hash)
    - REPLAY: replay_behavior (controls how step is handled during replay)

    Idempotency:
        idempotency_key: Unique key for this step's side effects. Used to:
            - Prevent duplicate execution of non-idempotent operations
            - Enable safe replay by checking if operation was already performed
        replay_behavior: How to handle this step during replay:
            - "execute": Re-execute the step (default for idempotent operations)
            - "skip": Skip if idempotency_key already executed
            - "check": Verify output matches original, fail if different
    """

    # Deterministic fields (included in hash)
    step_index: int
    skill_id: str
    input_hash: str
    output_hash: str
    rng_state_before: str
    outcome: Literal["success", "failure", "skipped"]

    # Idempotency fields (deterministic - included in hash)
    idempotency_key: Optional[str] = None
    replay_behavior: Literal["execute", "skip", "check"] = "execute"

    # Audit fields (excluded from deterministic hash)
    duration_ms: int = 0
    error_code: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def deterministic_payload(self) -> Dict[str, Any]:
        """
        Return ONLY deterministic fields for hashing.

        This payload is used to compute the step's contribution to root_hash.
        Audit fields (timestamp, duration_ms) are excluded.
        Idempotency fields (idempotency_key, replay_behavior) ARE included.
        """
        return {
            "step_index": self.step_index,
            "skill_id": self.skill_id,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "rng_state_before": self.rng_state_before,
            "outcome": self.outcome,
            "idempotency_key": self.idempotency_key,
            "replay_behavior": self.replay_behavior,
        }

    def deterministic_hash(self) -> str:
        """Compute hash of deterministic payload only."""
        return hashlib.sha256(canonical_json(self.deterministic_payload()).encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step to dict (includes all fields for storage)."""
        return {
            # Deterministic
            "step_index": self.step_index,
            "skill_id": self.skill_id,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "rng_state_before": self.rng_state_before,
            "outcome": self.outcome,
            # Idempotency (deterministic)
            "idempotency_key": self.idempotency_key,
            "replay_behavior": self.replay_behavior,
            # Audit
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceStep":
        """Deserialize step from dict."""
        return cls(
            step_index=data["step_index"],
            skill_id=data["skill_id"],
            input_hash=data["input_hash"],
            output_hash=data["output_hash"],
            rng_state_before=data["rng_state_before"],
            outcome=data["outcome"],
            idempotency_key=data.get("idempotency_key"),
            replay_behavior=data.get("replay_behavior", "execute"),
            duration_ms=data.get("duration_ms", 0),
            error_code=data.get("error_code"),
            timestamp=data.get("timestamp"),
        )


@dataclass
class Trace:
    """
    Complete execution trace for replay and verification.

    A trace captures everything needed to replay a simulation:
    - Random seed (deterministic)
    - Frozen timestamp (deterministic - part of context)
    - Plan (deterministic)
    - Each step's input/output hashes (deterministic)
    - Audit data (timestamps, durations - for logging only)

    The root_hash is computed ONLY from deterministic fields, ensuring
    two traces with identical seeds and inputs produce identical hashes
    regardless of when they were executed.

    Attributes:
        version: Schema version for compatibility
        seed: Random seed used (deterministic)
        timestamp: Frozen start time (deterministic - from RuntimeContext)
        tenant_id: Tenant isolation identifier (deterministic)
        plan: Original plan (deterministic)
        steps: Recorded execution steps
        root_hash: Deterministic hash (computed on finalize)
        finalized: Whether trace is complete
        metadata: Additional metadata (excluded from hash)
    """

    seed: int
    plan: List[Dict[str, Any]]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tenant_id: str = "default"
    version: str = TRACE_SCHEMA_VERSION
    steps: List[TraceStep] = field(default_factory=list)
    root_hash: Optional[str] = None
    finalized: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        skill_id: str,
        input_data: Any,
        output_data: Any,
        rng_state: str,
        duration_ms: int,
        outcome: Literal["success", "failure", "skipped"],
        error_code: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        replay_behavior: Literal["execute", "skip", "check"] = "execute",
    ) -> TraceStep:
        """
        Add a step to the trace.

        Args:
            skill_id: Skill that was executed
            input_data: Input to the skill (will be hashed)
            output_data: Output from the skill (will be hashed)
            rng_state: RNG state before execution
            duration_ms: Execution duration (audit only, not in hash)
            outcome: Result status
            error_code: Error code if failed (audit only)
            idempotency_key: Unique key for non-idempotent operations (e.g., payment_id)
            replay_behavior: How to handle during replay:
                - "execute": Re-execute (default, for idempotent ops)
                - "skip": Skip if already executed (for side effects)
                - "check": Verify output matches original

        Returns:
            The created TraceStep

        Raises:
            ValueError: If trace is already finalized
        """
        if self.finalized:
            raise ValueError("Cannot add steps to finalized trace")

        step = TraceStep(
            step_index=len(self.steps),
            skill_id=skill_id,
            input_hash=hash_data(input_data),
            output_hash=hash_data(output_data),
            rng_state_before=rng_state,
            outcome=outcome,
            idempotency_key=idempotency_key,
            replay_behavior=replay_behavior,
            duration_ms=duration_ms,
            error_code=error_code,
        )
        self.steps.append(step)
        return step

    def finalize(self) -> str:
        """
        Finalize trace and compute root hash.

        The root_hash is computed from DETERMINISTIC fields only:
        - seed, timestamp (frozen), tenant_id
        - Each step's deterministic_payload

        Returns:
            Root hash of the finalized trace

        Raises:
            ValueError: If trace is already finalized
        """
        if self.finalized:
            raise ValueError("Trace already finalized")

        self.finalized = True
        self.root_hash = self._compute_root_hash()
        return self.root_hash

    def _compute_root_hash(self) -> str:
        """
        Compute Merkle-like root hash over deterministic fields only.

        Hash chain construction:
        1. Start with seed:timestamp:tenant_id
        2. For each step, chain with step.deterministic_hash()

        This ensures identical traces produce identical hashes
        regardless of audit fields (execution time, duration).
        """
        # Base hash from deterministic trace metadata
        base = f"{self.seed}:{self.timestamp}:{self.tenant_id}"
        chain_hash = hashlib.sha256(base.encode()).hexdigest()

        # Chain each step's deterministic hash
        for step in self.steps:
            step_det_hash = step.deterministic_hash()
            combined = f"{chain_hash}:{step_det_hash}"
            chain_hash = hashlib.sha256(combined.encode()).hexdigest()

        return chain_hash

    def verify(self) -> bool:
        """
        Verify trace integrity.

        Returns:
            True if root_hash matches recomputed hash
        """
        if not self.finalized or not self.root_hash:
            return False
        return self.root_hash == self._compute_root_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize trace to dict (includes all fields)."""
        return {
            "version": self.version,
            "seed": self.seed,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "plan": self.plan,
            "steps": [s.to_dict() for s in self.steps],
            "root_hash": self.root_hash,
            "finalized": self.finalized,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Serialize to canonical JSON string."""
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trace":
        """Deserialize trace from dict."""
        trace = cls(
            seed=data["seed"],
            plan=data["plan"],
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            tenant_id=data.get("tenant_id", "default"),
            version=data.get("version", TRACE_SCHEMA_VERSION),
            metadata=data.get("metadata", {}),
        )

        for step_data in data.get("steps", []):
            step = TraceStep.from_dict(step_data)
            trace.steps.append(step)

        trace.root_hash = data.get("root_hash")
        trace.finalized = data.get("finalized", False)

        return trace

    @classmethod
    def from_json(cls, json_str: str) -> "Trace":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str) -> None:
        """
        Save trace to file.

        Args:
            path: File path (should end in .trace.json)
        """
        Path(path).write_text(self.to_json())

    @classmethod
    def load(cls, path: str) -> "Trace":
        """
        Load trace from file.

        Args:
            path: File path to load

        Returns:
            Loaded Trace object
        """
        return cls.from_json(Path(path).read_text())


def hash_data(data: Any) -> str:
    """
    Compute deterministic hash of any data.

    Uses canonical JSON serialization to ensure
    identical data produces identical hashes.

    Args:
        data: Any JSON-serializable data

    Returns:
        SHA256 hash hex string (first 16 chars)
    """
    canonical = canonical_json(data)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def diff_traces(trace1: Trace, trace2: Trace) -> Dict[str, Any]:
    """
    Compare two traces for DETERMINISTIC equality.

    Compares only deterministic fields:
    - seed, timestamp (frozen), tenant_id
    - step input/output hashes, rng_state, outcome
    - root_hash

    Audit fields (step timestamps, duration_ms) are NOT compared.

    Args:
        trace1: First trace (usually original)
        trace2: Second trace (usually replay)

    Returns:
        Dict with:
        - match: bool - whether traces are deterministically identical
        - differences: list of specific differences
        - summary: human-readable summary
    """
    differences = []

    # Check deterministic metadata
    if trace1.seed != trace2.seed:
        differences.append({"field": "seed", "trace1": trace1.seed, "trace2": trace2.seed})

    if trace1.timestamp != trace2.timestamp:
        differences.append(
            {"field": "timestamp", "trace1": trace1.timestamp, "trace2": trace2.timestamp}
        )

    if trace1.tenant_id != trace2.tenant_id:
        differences.append(
            {"field": "tenant_id", "trace1": trace1.tenant_id, "trace2": trace2.tenant_id}
        )

    # Check step count
    if len(trace1.steps) != len(trace2.steps):
        differences.append(
            {"field": "step_count", "trace1": len(trace1.steps), "trace2": len(trace2.steps)}
        )

    # Check individual steps (deterministic fields only)
    for i, (s1, s2) in enumerate(zip(trace1.steps, trace2.steps)):
        if s1.skill_id != s2.skill_id:
            differences.append(
                {"field": f"step[{i}].skill_id", "trace1": s1.skill_id, "trace2": s2.skill_id}
            )
        if s1.input_hash != s2.input_hash:
            differences.append(
                {"field": f"step[{i}].input_hash", "trace1": s1.input_hash, "trace2": s2.input_hash}
            )
        if s1.output_hash != s2.output_hash:
            differences.append(
                {
                    "field": f"step[{i}].output_hash",
                    "trace1": s1.output_hash,
                    "trace2": s2.output_hash,
                }
            )
        if s1.rng_state_before != s2.rng_state_before:
            differences.append(
                {
                    "field": f"step[{i}].rng_state",
                    "trace1": s1.rng_state_before,
                    "trace2": s2.rng_state_before,
                }
            )
        if s1.outcome != s2.outcome:
            differences.append(
                {"field": f"step[{i}].outcome", "trace1": s1.outcome, "trace2": s2.outcome}
            )

    # Check root hash (should match if all above match)
    if trace1.root_hash != trace2.root_hash:
        differences.append(
            {"field": "root_hash", "trace1": trace1.root_hash, "trace2": trace2.root_hash}
        )

    match = len(differences) == 0

    if match:
        summary = "Traces are deterministically identical"
    else:
        summary = f"Traces differ in {len(differences)} field(s): {', '.join(d['field'] for d in differences[:3])}"
        if len(differences) > 3:
            summary += f" and {len(differences) - 3} more"

    return {"match": match, "differences": differences, "summary": summary}


def create_trace_from_context(ctx: RuntimeContext, plan: List[Dict[str, Any]]) -> Trace:
    """
    Create a new trace from a RuntimeContext.

    Args:
        ctx: RuntimeContext with seed and timestamp
        plan: Plan to be traced

    Returns:
        New Trace initialized from context
    """
    return Trace(seed=ctx.seed, timestamp=ctx.timestamp(), tenant_id=ctx.tenant_id, plan=plan)


# Idempotency tracking for replay safety
_executed_idempotency_keys: set = set()


def reset_idempotency_state():
    """Reset idempotency tracking (for testing)."""
    global _executed_idempotency_keys
    _executed_idempotency_keys = set()


def mark_idempotency_key_executed(key: str):
    """Mark an idempotency key as executed."""
    _executed_idempotency_keys.add(key)


def is_idempotency_key_executed(key: str) -> bool:
    """Check if an idempotency key has been executed."""
    return key in _executed_idempotency_keys


@dataclass
class ReplayResult:
    """Result of replaying a trace step."""

    step_index: int
    action: Literal["executed", "skipped", "checked", "failed"]
    reason: Optional[str] = None
    output_match: Optional[bool] = None  # For "check" behavior


def replay_step(
    step: TraceStep, execute_fn: Optional[callable] = None, idempotency_store: Optional[set] = None
) -> ReplayResult:
    """
    Replay a single trace step with idempotency safety.

    Args:
        step: The trace step to replay
        execute_fn: Function to execute the step (returns output data)
        idempotency_store: Set of executed idempotency keys (uses global if None)

    Returns:
        ReplayResult indicating what action was taken

    Behavior based on replay_behavior:
        - "execute": Always execute the step
        - "skip": Skip if idempotency_key already executed
        - "check": Execute and verify output matches original
    """
    store = idempotency_store if idempotency_store is not None else _executed_idempotency_keys

    # Check idempotency for "skip" behavior
    if step.replay_behavior == "skip" and step.idempotency_key:
        if step.idempotency_key in store:
            return ReplayResult(
                step_index=step.step_index,
                action="skipped",
                reason=f"Idempotency key '{step.idempotency_key}' already executed",
            )

    # Execute the step
    if execute_fn is None:
        # Dry run - no actual execution
        if step.replay_behavior == "skip" and step.idempotency_key:
            store.add(step.idempotency_key)
        return ReplayResult(
            step_index=step.step_index,
            action="executed" if step.replay_behavior != "check" else "checked",
            reason="Dry run - no execution function provided",
            output_match=True if step.replay_behavior == "check" else None,
        )

    try:
        output = execute_fn()
        output_hash = hash_data(output)

        # Mark idempotency key as executed
        if step.idempotency_key:
            store.add(step.idempotency_key)

        # For "check" behavior, verify output matches
        if step.replay_behavior == "check":
            matches = output_hash == step.output_hash
            return ReplayResult(
                step_index=step.step_index,
                action="checked" if matches else "failed",
                reason=None
                if matches
                else f"Output hash mismatch: {output_hash} != {step.output_hash}",
                output_match=matches,
            )

        return ReplayResult(step_index=step.step_index, action="executed", reason=None)

    except Exception as e:
        return ReplayResult(step_index=step.step_index, action="failed", reason=str(e))


def generate_idempotency_key(run_id: str, step_index: int, skill_id: str, input_hash: str) -> str:
    """
    Generate a deterministic idempotency key for a step.

    This creates a unique key based on:
    - run_id: The execution run
    - step_index: Position in the plan
    - skill_id: The skill being executed
    - input_hash: Hash of the input data

    Use this for non-idempotent operations like:
    - Payment processing
    - Database writes
    - External API calls with side effects
    """
    key_data = f"{run_id}:{step_index}:{skill_id}:{input_hash}"
    return hashlib.sha256(key_data.encode()).hexdigest()[:32]
