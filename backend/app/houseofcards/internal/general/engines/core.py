# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Core runtime execution (StructuredOutcome, never throws)
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Authority: Skill execution, budget queries, state queries
# Callers: API routes, workers, SDK
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md (L5 Worker Rules)
# Invariant: execute() NEVER throws - always returns StructuredOutcome

# runtime/core.py

"""
Core Runtime Implementation (M1)

Machine-native runtime that provides:
1. execute() - Never throws, returns StructuredOutcome
2. describe_skill() - Returns SkillDescriptor with stable fields
3. query() - Deterministic queries for budget, state, history
4. get_resource_contract() - Resource constraints and limits

Design principles (from PIN-005):
- Queryable state (agent asks questions, gets structured answers)
- Capability awareness (agent knows what it can do and what it costs)
- Failure as data (errors are navigable, not opaque)
- Self-describing skills (skills explain their behavior and constraints)
- Resource contracts (boundaries declared upfront)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Mapping, Optional, Union

# M6: Import metrics recording functions
try:
    from app.workflow.metrics import record_cost_simulation_drift, record_step_duration

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    record_step_duration = None
    record_cost_simulation_drift = None

logger = logging.getLogger("nova.runtime.core")


def _canonical_json(obj: Any) -> str:
    """
    Canonical JSON serialization for deterministic outputs.
    Keys sorted, no whitespace, UTF-8.
    """

    def _serializer(o: Any) -> Any:
        if hasattr(o, "to_dict"):
            return o.to_dict()
        if hasattr(o, "__dict__"):
            return o.__dict__
        if isinstance(o, Enum):
            return o.value
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_serializer)


def _content_hash(obj: Any, length: int = 16) -> str:
    """Compute deterministic content hash."""
    canonical = _canonical_json(obj).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:length]


class ErrorCategory(str, Enum):
    """Error categories from M0 error taxonomy."""

    TRANSIENT = "TRANSIENT"  # Retry might work
    PERMANENT = "PERMANENT"  # Don't retry
    RESOURCE = "RESOURCE"  # Budget/rate limit
    PERMISSION = "PERMISSION"  # Not allowed
    VALIDATION = "VALIDATION"  # Bad input

    def is_retryable(self) -> bool:
        """Whether this error category is retryable."""
        return self in (ErrorCategory.TRANSIENT, ErrorCategory.RESOURCE)


@dataclass(frozen=True)
class StructuredOutcome:
    """
    Structured outcome that M0 golden files & replay tests expect.

    This is the canonical return type for all skill executions.
    Never throws - always returns a StructuredOutcome.

    Fields:
        id: Unique call identifier (deterministic for replay)
        ok: True if execution succeeded, False otherwise
        result: The skill's return value (if ok=True)
        error: Structured error info (if ok=False)
        meta: Execution metadata (timing, cost, side-effects)

    Stable fields (for determinism):
        - id, ok, error.code, error.category

    Non-deterministic fields:
        - meta.started_at, meta.ended_at, meta.duration_s
        - result (for I/O skills like http_call, llm_invoke)
    """

    id: str
    ok: bool
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization and golden file comparison."""
        return asdict(self)

    def to_canonical_json(self) -> str:
        """Return canonical JSON representation for replay testing."""
        return _canonical_json(self.to_dict())

    def content_hash(self, exclude_fields: Optional[set] = None) -> str:
        """
        Compute deterministic content hash.

        Args:
            exclude_fields: Fields to exclude (e.g. {'meta'} for timing-invariant hash)
        """
        data = self.to_dict()
        if exclude_fields:
            data = {k: v for k, v in data.items() if k not in exclude_fields}
        return _content_hash(data)

    @classmethod
    def success(cls, call_id: str, result: Any, meta: Optional[Dict[str, Any]] = None) -> "StructuredOutcome":
        """Factory for successful outcome."""
        return cls(id=call_id, ok=True, result=result, meta=meta or {})

    @classmethod
    def failure(
        cls,
        call_id: str,
        code: str,
        message: str,
        category: Union[ErrorCategory, str] = ErrorCategory.PERMANENT,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "StructuredOutcome":
        """Factory for failed outcome with structured error."""
        cat_value = category.value if isinstance(category, ErrorCategory) else category
        error = {"code": code, "message": message, "category": cat_value, "retryable": retryable}
        if details:
            error["details"] = details
        return cls(id=call_id, ok=False, error=error, meta=meta or {})


@dataclass(frozen=True)
class SkillDescriptor:
    """
    Skill metadata returned by describe_skill().

    Contains stable fields for determinism and planner consumption.

    Fields:
        skill_id: Unique skill identifier
        name: Human-readable name
        version: Semantic version string
        description: Human-readable description
        inputs_schema: JSON Schema for inputs
        outputs_schema: JSON Schema for outputs
        stable_fields: List of deterministic output fields
        idempotent: Whether the skill is idempotent
        cost_model: Cost estimation model
        failure_modes: Known failure mode codes
        constraints: Execution constraints (timeout, limits)
    """

    skill_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    inputs_schema_version: str = "1.0"
    outputs_schema_version: str = "1.0"
    stable_fields: Union[List[str], Mapping[str, str]] = field(default_factory=list)
    idempotent: bool = True
    cost_model: Dict[str, Any] = field(default_factory=lambda: {"base_cents": 0})
    failure_modes: List[Any] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        stable = self.stable_fields
        if isinstance(stable, list):
            stable = {f: "deterministic" for f in stable}
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs_schema": self.inputs_schema,
            "outputs_schema": self.outputs_schema,
            "inputs_schema_version": self.inputs_schema_version,
            "outputs_schema_version": self.outputs_schema_version,
            "stable_fields": dict(stable) if isinstance(stable, Mapping) else stable,
            "idempotent": self.idempotent,
            "cost_model": self.cost_model,
            "failure_modes": list(self.failure_modes),
            "constraints": self.constraints,
        }


@dataclass(frozen=True)
class ResourceContract:
    """
    Resource contract for budget, rate limits, and concurrency.

    Declared upfront, not discovered through failure.

    Fields:
        resource_id: Unique resource identifier
        budget_cents: Budget in cents
        rate_limit_per_min: Rate limit per minute
        max_concurrent: Max concurrent executions
        schema_version: Contract schema version
    """

    resource_id: str
    budget_cents: int = 1000
    rate_limit_per_min: int = 60
    max_concurrent: int = 5
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "resource_id": self.resource_id,
            "budget_cents": self.budget_cents,
            "rate_limit_per_min": self.rate_limit_per_min,
            "max_concurrent": self.max_concurrent,
            "schema_version": self.schema_version,
        }


# Type alias for async skill handlers
SkillHandler = Callable[[Mapping[str, Any]], Coroutine[Any, Any, Any]]


class Runtime:
    """
    Machine-Native Runtime (M1)

    Core runtime providing the four interfaces specified in PIN-008:
    1. execute(skill_id, inputs, timeout_s) -> StructuredOutcome
    2. describe_skill(skill_id) -> SkillDescriptor
    3. query(query_type, **params) -> Dict
    4. get_resource_contract(resource_id) -> ResourceContract

    Design goals:
    - Never throws exceptions (returns structured outcomes)
    - Deterministic behavior for same inputs
    - Queryable state for agent consumption
    - Self-describing capabilities
    """

    def __init__(self):
        # Registry: skill_id -> async handler
        self._registry: Dict[str, SkillHandler] = {}
        # Descriptors: skill_id -> SkillDescriptor
        self._skill_descriptors: Dict[str, SkillDescriptor] = {}
        # Contracts: resource_id -> ResourceContract
        self._resource_contracts: Dict[str, ResourceContract] = {}
        # Execution history for query("what_did_i_try_already")
        self._execution_history: List[Dict[str, Any]] = []
        # Budget tracking
        self._budget_spent_cents: int = 0
        self._budget_total_cents: int = 1000

    def register_skill(self, descriptor: SkillDescriptor, handler: SkillHandler) -> None:
        """
        Register a skill with its descriptor and handler.

        Args:
            descriptor: Skill metadata
            handler: Async function that executes the skill

        Raises:
            RuntimeError: If skill is already registered
        """
        if descriptor.skill_id in self._registry:
            raise RuntimeError(f"skill_already_registered: {descriptor.skill_id}")
        self._registry[descriptor.skill_id] = handler
        self._skill_descriptors[descriptor.skill_id] = descriptor

    def register_resource_contract(self, contract: ResourceContract) -> None:
        """
        Register a resource contract.

        Args:
            contract: Resource contract with budget/rate limits

        Raises:
            RuntimeError: If contract is already registered
        """
        if contract.resource_id in self._resource_contracts:
            raise RuntimeError(f"contract_already_registered: {contract.resource_id}")
        self._resource_contracts[contract.resource_id] = contract

    async def execute(
        self, skill_id: str, inputs: Mapping[str, Any], timeout_s: Optional[float] = None
    ) -> StructuredOutcome:
        """
        Execute a registered skill under deterministic guards.

        NEVER THROWS - always returns StructuredOutcome.

        Args:
            skill_id: The skill to execute
            inputs: Input parameters for the skill
            timeout_s: Optional timeout in seconds

        Returns:
            StructuredOutcome with ok=True/False and result/error
        """
        start_ts = time.time()
        call_id = str(uuid.uuid4())
        meta = {
            "call_id": call_id,
            "skill_id": skill_id,
            "started_at": start_ts,
            "inputs_hash": hash(frozenset(inputs.items())) if inputs else 0,
        }

        # Check if skill exists
        if skill_id not in self._registry:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_SKILL_NOT_FOUND",
                message=f"Skill not found: {skill_id}",
                category=ErrorCategory.PERMANENT,
                retryable=False,
                meta=meta,
            )
            self._record_execution(skill_id, inputs, outcome)
            return outcome

        handler = self._registry[skill_id]
        descriptor = self._skill_descriptors[skill_id]

        # Estimate cost and check budget
        estimated_cost = descriptor.cost_model.get("base_cents", 0)
        if self._budget_spent_cents + estimated_cost > self._budget_total_cents:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_BUDGET_EXCEEDED",
                message=f"Budget exceeded: {self._budget_spent_cents}/{self._budget_total_cents} cents",
                category=ErrorCategory.RESOURCE,
                retryable=False,
                meta=meta,
            )
            self._record_execution(skill_id, inputs, outcome)
            return outcome

        try:
            coro = handler(inputs)
            if timeout_s is not None:
                result = await asyncio.wait_for(coro, timeout=timeout_s)
            else:
                result = await coro

            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            meta["cost_cents"] = estimated_cost
            self._budget_spent_cents += estimated_cost

            outcome = StructuredOutcome.success(call_id, result, meta)
            self._record_execution(skill_id, inputs, outcome)

            # M6: Record metrics for observability
            self._record_metrics(skill_id, meta["duration_s"], True, estimated_cost, estimated_cost)

            return outcome

        except asyncio.TimeoutError:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_TIMEOUT",
                message=f"Execution timed out after {timeout_s}s",
                category=ErrorCategory.TRANSIENT,
                retryable=True,
                meta=meta,
            )
            self._record_execution(skill_id, inputs, outcome)

            # M6: Record metrics for observability
            self._record_metrics(skill_id, meta["duration_s"], False, estimated_cost, 0)

            return outcome

        except Exception as exc:
            meta["ended_at"] = time.time()
            meta["duration_s"] = meta["ended_at"] - start_ts
            outcome = StructuredOutcome.failure(
                call_id=call_id,
                code="ERR_RUNTIME_EXCEPTION",
                message=str(exc),
                category=ErrorCategory.PERMANENT,
                retryable=False,
                meta={**meta, "exception_type": type(exc).__name__},
            )
            self._record_execution(skill_id, inputs, outcome)

            # M6: Record metrics for observability
            self._record_metrics(skill_id, meta["duration_s"], False, estimated_cost, 0)

            return outcome

    def describe_skill(self, skill_id: str) -> Optional[SkillDescriptor]:
        """
        Return stable descriptor for a skill.

        Used by planners and UI for capability discovery.

        Args:
            skill_id: The skill to describe

        Returns:
            SkillDescriptor if found, None otherwise
        """
        return self._skill_descriptors.get(skill_id)

    async def query(self, query_type: str, **params: Any) -> Dict[str, Any]:
        """
        Lightweight query interface for discovery and state.

        Deterministic for same inputs (seeded, no external calls).

        Supported query types:
        - remaining_budget_cents: Current budget remaining
        - what_did_i_try_already: Previous execution attempts
        - allowed_skills: List of available skills
        - last_step_outcome: Most recent execution outcome
        - skills_available_for_goal: Skills matching a goal (deterministic)

        Args:
            query_type: Type of query
            **params: Query-specific parameters

        Returns:
            Dict with query results
        """
        if query_type == "remaining_budget_cents":
            return {
                "remaining_cents": self._budget_total_cents - self._budget_spent_cents,
                "spent_cents": self._budget_spent_cents,
                "total_cents": self._budget_total_cents,
            }

        elif query_type == "what_did_i_try_already":
            step = params.get("step")
            skill = params.get("skill")
            history = self._execution_history
            if step:
                history = [h for h in history if h.get("step") == step]
            if skill:
                history = [h for h in history if h.get("skill_id") == skill]
            return {"history": history[-10:]}  # Last 10 entries

        elif query_type == "allowed_skills":
            return {"skills": list(self._registry.keys()), "count": len(self._registry)}

        elif query_type == "last_step_outcome":
            if self._execution_history:
                last = self._execution_history[-1]
                return {"outcome": last}
            return {"outcome": None}

        elif query_type == "skills_available_for_goal":
            goal = params.get("goal", "")
            # Deterministic pseudo-matching based on goal hash
            seed = sum(ord(c) for c in goal) % 997
            all_skills = list(self._skill_descriptors.values())
            # Deterministic shuffle using seed
            matched = sorted(all_skills, key=lambda s: (hash(s.skill_id) + seed) % 1000)
            return {"goal": goal, "skills": [s.skill_id for s in matched[:5]], "seed": seed}

        else:
            return {
                "error": f"Unknown query type: {query_type}",
                "supported": [
                    "remaining_budget_cents",
                    "what_did_i_try_already",
                    "allowed_skills",
                    "last_step_outcome",
                    "skills_available_for_goal",
                ],
            }

    def get_resource_contract(self, resource_id: str) -> Optional[ResourceContract]:
        """
        Return the contract for a resource.

        Provides budget, rate limits, concurrency info upfront.

        Args:
            resource_id: The resource to get contract for

        Returns:
            ResourceContract if found, None otherwise
        """
        return self._resource_contracts.get(resource_id)

    def _record_execution(self, skill_id: str, inputs: Mapping[str, Any], outcome: StructuredOutcome) -> None:
        """Record execution for query("what_did_i_try_already")."""
        self._execution_history.append(
            {
                "skill_id": skill_id,
                "inputs_keys": list(inputs.keys()) if inputs else [],
                "ok": outcome.ok,
                "error_code": outcome.error.get("code") if outcome.error else None,
                "call_id": outcome.id,
                "timestamp": time.time(),
            }
        )

    def _record_metrics(
        self,
        skill_id: str,
        duration_seconds: float,
        success: bool,
        simulated_cents: int,
        actual_cents: int,
    ) -> None:
        """
        Record execution metrics for M6 observability.

        Records:
        - Step duration to Prometheus histogram
        - Cost drift (simulated vs actual) to Prometheus histogram

        Args:
            skill_id: The skill that was executed
            duration_seconds: How long execution took
            success: Whether execution succeeded
            simulated_cents: Pre-execution cost estimate
            actual_cents: Actual cost incurred
        """
        if not METRICS_AVAILABLE:
            return

        try:
            # Record step duration
            if record_step_duration is not None:
                record_step_duration(skill_id, duration_seconds, success)

            # Record cost drift (simulated vs actual)
            if record_cost_simulation_drift is not None and simulated_cents > 0:
                record_cost_simulation_drift(skill_id, simulated_cents, actual_cents)

        except Exception as e:
            # Don't let metrics failures break execution
            logger.warning(f"Failed to record metrics for {skill_id}: {e}")

    def set_budget(self, total_cents: int, spent_cents: int = 0) -> None:
        """Configure budget for testing."""
        self._budget_total_cents = total_cents
        self._budget_spent_cents = spent_cents

    def get_all_skills(self) -> List[str]:
        """Get list of all registered skill IDs."""
        return list(self._registry.keys())

    def clear_history(self) -> None:
        """Clear execution history (for testing)."""
        self._execution_history.clear()
