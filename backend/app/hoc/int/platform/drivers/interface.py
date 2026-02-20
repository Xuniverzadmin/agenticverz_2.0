# capability_id: CAP-012
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Planner interface definition (contract)
# Callers: planners/*
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: LLM Integration

# planner/interface.py
"""
PlannerInterface Protocol (M2.5)

Defines the contract that all planner implementations must follow.
This enables planner modularity - swap between Claude, OpenAI, local models,
or rule-based planners without changing the runtime.

See: app/specs/planner_determinism.md for full specification.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union


def _canonical_json(obj: Any) -> str:
    """Canonical JSON serialization for deterministic outputs."""

    def _serializer(o: Any) -> Any:
        if hasattr(o, "to_dict"):
            return o.to_dict()
        if hasattr(o, "__dict__"):
            return o.__dict__
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_serializer)


def _content_hash(obj: Any, length: int = 16) -> str:
    """Compute deterministic content hash."""
    canonical = _canonical_json(obj).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:length]


class DeterminismMode(str, Enum):
    """Determinism mode for planner outputs."""

    FULL = "full"  # Same inputs → Identical plan (byte-for-byte)
    STRUCTURAL = "structural"  # Same inputs → Same plan structure
    NONE = "none"  # No guarantees


@dataclass
class PlanStep:
    """A single step in an execution plan."""

    step_id: str
    skill: str
    params: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    on_error: str = "abort"  # abort, continue, retry
    retry_count: int = 3
    output_key: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "step_id": self.step_id,
            "skill": self.skill,
            "params": self.params,
            "depends_on": self.depends_on,
            "on_error": self.on_error,
            "retry_count": self.retry_count,
            "output_key": self.output_key or self.step_id,
            "description": self.description,
        }


@dataclass
class PlanMetadata:
    """
    Metadata about plan generation.

    DETERMINISM NOTE:
    - generated_at is EXCLUDED from deterministic comparison
    - Only deterministic_fields are compared during replay
    - cache_key is computed from deterministic inputs only
    """

    planner: str
    planner_version: str
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_cents: int = 0
    deterministic: bool = False
    cache_key: Optional[str] = None
    # Non-deterministic field - excluded from replay comparison
    # Set to fixed sentinel for deterministic planners, actual timestamp for non-deterministic
    _generated_at: Optional[str] = field(default=None, repr=False)

    @property
    def generated_at(self) -> str:
        """Get generation timestamp (non-deterministic, for logging only)."""
        if self._generated_at is None:
            return datetime.now(timezone.utc).isoformat()
        return self._generated_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (includes non-deterministic fields)."""
        return {
            "planner": self.planner,
            "planner_version": self.planner_version,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_cents": self.cost_cents,
            "deterministic": self.deterministic,
            "cache_key": self.cache_key,
            "generated_at": self.generated_at,  # Non-deterministic, excluded from hash
        }

    def to_deterministic_dict(self) -> Dict[str, Any]:
        """Serialize only deterministic fields (for replay comparison)."""
        return {
            "planner": self.planner,
            "planner_version": self.planner_version,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_cents": self.cost_cents,
            "deterministic": self.deterministic,
            "cache_key": self.cache_key,
            # generated_at intentionally excluded
        }


@dataclass
class PlannerOutput:
    """
    Structured planner output.

    Contains the execution plan plus metadata about generation.

    DETERMINISM CONTRACT:
    - Steps and their ordering are deterministic
    - Metadata (excluding generated_at) is deterministic
    - Use to_deterministic_dict() for replay comparison
    - Use to_dict() for full serialization including timestamps
    """

    steps: List[PlanStep]
    metadata: PlanMetadata
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (includes non-deterministic fields)."""
        return {
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata.to_dict(),
            "warnings": self.warnings,
        }

    def to_deterministic_dict(self) -> Dict[str, Any]:
        """Serialize only deterministic fields (for replay comparison)."""
        return {
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata.to_deterministic_dict(),
            "warnings": self.warnings,
        }

    def to_canonical_json(self) -> str:
        """Return canonical JSON representation for replay testing (deterministic only)."""
        return _canonical_json(self.to_deterministic_dict())

    def content_hash(self) -> str:
        """Compute deterministic content hash of the plan (excludes timestamps)."""
        return _content_hash(self.to_deterministic_dict())

    @property
    def plan(self) -> Dict[str, Any]:
        """Alias for to_dict() for backwards compatibility."""
        return self.to_dict()


@dataclass
class PlannerError:
    """
    Structured planner error.

    Planners should return this instead of raising exceptions.
    """

    code: str
    message: str
    retryable: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    retry_after_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details,
            "retry_after_ms": self.retry_after_ms,
        }


# Error codes for planners
class PlannerErrorCode:
    """Standard planner error codes."""

    RATE_LIMITED = "PLANNER_RATE_LIMITED"
    CONTEXT_TOO_LONG = "PLANNER_CONTEXT_TOO_LONG"
    INVALID_GOAL = "PLANNER_INVALID_GOAL"
    NO_SKILLS_AVAILABLE = "PLANNER_NO_SKILLS_AVAILABLE"
    GENERATION_FAILED = "PLANNER_GENERATION_FAILED"
    INVALID_PLAN = "PLANNER_INVALID_PLAN"
    TIMEOUT = "PLANNER_TIMEOUT"


class PlannerInterface(ABC):
    """
    Abstract base class for planner implementations.

    All planners must implement this interface to be used with the AOS runtime.

    Implementations:
    - StubPlanner: Rule-based, deterministic (for testing)
    - ClaudeAdapter: Claude-based planning
    - OpenAIAdapter: GPT-based planning (future)
    - LocalModelAdapter: Local LLM planning (future)
    """

    @property
    @abstractmethod
    def planner_id(self) -> str:
        """
        Unique identifier for this planner.

        Examples: "stub", "claude", "openai", "local"
        """
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Planner version (semantic versioning).

        Should be bumped when planner behavior changes.
        """
        ...

    @abstractmethod
    def get_determinism_mode(self) -> DeterminismMode:
        """
        Return the determinism mode of this planner.

        - FULL: Same inputs → Identical plan
        - STRUCTURAL: Same inputs → Same structure
        - NONE: No guarantees
        """
        ...

    @abstractmethod
    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Union[PlannerOutput, PlannerError]:
        """
        Generate an execution plan for the given goal.

        Args:
            agent_id: ID of the agent requesting the plan
            goal: Natural language goal/task description
            context_summary: Summary of relevant context
            memory_snippets: Relevant memory items
            tool_manifest: Available skills/tools

        Returns:
            PlannerOutput on success, PlannerError on failure

        Note:
            This method should NEVER raise exceptions.
            All errors should be returned as PlannerError.
        """
        ...

    def validate_plan(self, output: PlannerOutput) -> List[str]:
        """
        Validate a generated plan.

        Args:
            output: The plan to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not output.steps:
            errors.append("Plan has no steps")
            return errors

        step_ids = set()
        for step in output.steps:
            # Check for duplicate step IDs
            if step.step_id in step_ids:
                errors.append(f"Duplicate step_id: {step.step_id}")
            step_ids.add(step.step_id)

            # Check dependencies reference valid steps
            for dep in step.depends_on:
                if dep not in step_ids:
                    # Might be forward reference - check if it exists anywhere
                    all_ids = {s.step_id for s in output.steps}
                    if dep not in all_ids:
                        errors.append(f"Step {step.step_id} depends on unknown step: {dep}")

            # Check required fields
            if not step.skill:
                errors.append(f"Step {step.step_id} has no skill")

        return errors

    def estimate_cost(
        self, goal: str, context_summary: Optional[str] = None, tool_manifest: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Estimate the cost of generating a plan.

        Args:
            goal: The goal to plan for
            context_summary: Optional context
            tool_manifest: Available tools

        Returns:
            Dict with estimated_tokens, estimated_cost_cents
        """
        # Default implementation - override in subclasses
        goal_tokens = len(goal.split())
        context_tokens = len(context_summary.split()) if context_summary else 0
        manifest_tokens = len(str(tool_manifest).split()) if tool_manifest else 0

        estimated_input = goal_tokens + context_tokens + manifest_tokens
        estimated_output = 200  # Typical plan size

        return {
            "estimated_input_tokens": estimated_input,
            "estimated_output_tokens": estimated_output,
            "estimated_cost_cents": max(1, (estimated_input + estimated_output) // 1000),
        }


class PlannerRegistry:
    """
    Registry for planner implementations.

    Manages planner instances and provides factory methods.
    """

    _planners: Dict[str, PlannerInterface] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, planner: PlannerInterface, is_default: bool = False) -> None:
        """Register a planner implementation."""
        cls._planners[planner.planner_id] = planner
        if is_default or cls._default is None:
            cls._default = planner.planner_id

    @classmethod
    def get(cls, planner_id: Optional[str] = None) -> Optional[PlannerInterface]:
        """Get a planner by ID (or default if not specified)."""
        if planner_id is None:
            planner_id = cls._default
        return cls._planners.get(planner_id)

    @classmethod
    def list(cls) -> List[str]:
        """List all registered planner IDs."""
        return list(cls._planners.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered planners (for testing)."""
        cls._planners.clear()
        cls._default = None


# Utility functions


def normalize_goal(goal: str) -> str:
    """Normalize goal text for consistent processing."""
    return goal.strip()


def normalize_context(context: Optional[str]) -> Optional[str]:
    """Normalize context text."""
    if context is None:
        return None
    return context.strip()


def compute_plan_input_hash(
    agent_id: str,
    goal: str,
    context_summary: Optional[str],
    memory_snippets: Optional[List[Dict]],
    tool_manifest: Optional[List[Dict]],
) -> str:
    """
    Compute deterministic hash of planner inputs.

    Used for caching and replay testing.
    """
    import hashlib
    import json

    normalized = {
        "agent_id": agent_id,
        "goal": normalize_goal(goal),
        "context_summary": normalize_context(context_summary),
        "memory_snippets": memory_snippets or [],
        "tool_manifest": tool_manifest or [],
    }

    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
