# Planner Determinism Contract

**Version:** 1.0.0
**Status:** Active
**Last Updated:** 2025-12-01
**Related:** determinism_and_replay.md, canonical_json.md

---

## Purpose

This contract defines the determinism guarantees for planner implementations in AOS. All planners MUST adhere to these rules to support:
1. Replay testing
2. Cost estimation
3. Plan validation
4. Debugging and auditing

---

## PlannerInterface Protocol

All planners MUST implement this interface:

```python
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass


@dataclass
class PlannerOutput:
    """Structured planner output."""
    plan: Dict[str, Any]          # The execution plan
    metadata: Dict[str, Any]      # Planner metadata (tokens, cost, etc.)
    deterministic: bool           # Whether this output is deterministic


class PlannerInterface(Protocol):
    """Protocol for planner implementations."""

    @property
    def planner_id(self) -> str:
        """Unique identifier for this planner."""
        ...

    @property
    def version(self) -> str:
        """Planner version (semantic versioning)."""
        ...

    def plan(
        self,
        agent_id: str,
        goal: str,
        context_summary: Optional[str] = None,
        memory_snippets: Optional[List[Dict[str, Any]]] = None,
        tool_manifest: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> PlannerOutput:
        """Generate a plan for the given goal."""
        ...

    def get_determinism_mode(self) -> str:
        """Return determinism mode: 'full', 'structural', or 'none'."""
        ...
```

---

## Determinism Modes

### 1. Full Determinism (`full`)

**Requirement:** Same inputs → Identical plan (byte-for-byte)

**Use cases:**
- StubPlanner for testing
- Cached/memoized planners
- Rule-based planners

**Implementation:**
```python
class StubPlanner:
    def get_determinism_mode(self) -> str:
        return "full"

    def plan(self, ...) -> PlannerOutput:
        # Use seeded random if any randomness needed
        # Output must be identical for same inputs
        return PlannerOutput(
            plan=self._generate_plan(...),
            metadata={"planner": "stub", "version": "1.0.0"},
            deterministic=True
        )
```

### 2. Structural Determinism (`structural`)

**Requirement:** Same inputs → Same plan structure, content may vary

**Guarantees:**
- Same number of steps
- Same skill sequence
- Same dependencies
- Parameters may differ in non-essential details

**Use cases:**
- LLM-based planners with temperature=0
- Template-based planners

**Implementation:**
```python
class ClaudeAdapter:
    def get_determinism_mode(self) -> str:
        return "structural"

    def plan(self, ...) -> PlannerOutput:
        # LLM output may vary slightly
        # But structure should be consistent
        return PlannerOutput(
            plan=self._call_claude(...),
            metadata={...},
            deterministic=False  # Cannot guarantee byte-identical
        )
```

### 3. Non-Deterministic (`none`)

**Requirement:** No guarantees

**Use cases:**
- Exploratory planners
- A/B testing planners
- Dynamic adaptation planners

---

## Plan Structure Contract

All planners MUST produce plans with this structure:

```json
{
  "steps": [
    {
      "step_id": "s1",
      "skill": "skill_name",
      "params": { ... },
      "depends_on": [],
      "on_error": "abort|continue|retry",
      "retry_count": 3
    }
  ],
  "metadata": {
    "planner": "planner_id",
    "planner_version": "1.0.0",
    "model": "claude-sonnet-4-20250514",
    "input_tokens": 1500,
    "output_tokens": 200,
    "cost_cents": 2,
    "generated_at": "2025-12-01T00:00:00Z",
    "deterministic": true
  }
}
```

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `steps` | array | YES | Ordered list of plan steps |
| `steps[].step_id` | string | YES | Unique step identifier |
| `steps[].skill` | string | YES | Skill to execute |
| `steps[].params` | object | YES | Skill parameters |

### Optional Fields

| Field | Default | Description |
|-------|---------|-------------|
| `depends_on` | `[]` | Step IDs this step depends on |
| `on_error` | `"abort"` | Error handling policy |
| `retry_count` | `3` | Max retries for transient errors |
| `output_key` | `step_id` | Key for storing step output |

---

## Deterministic Fields

These fields MUST be identical for same inputs (in `full` mode):

| Field | Determinism |
|-------|-------------|
| `step_id` | DETERMINISTIC |
| `skill` | DETERMINISTIC |
| `params` (structure) | DETERMINISTIC |
| `depends_on` | DETERMINISTIC |
| `on_error` | DETERMINISTIC |
| `retry_count` | DETERMINISTIC |

### Allowed Variance

| Field | Notes |
|-------|-------|
| `metadata.generated_at` | Timestamp varies |
| `metadata.input_tokens` | May vary with context |
| `metadata.output_tokens` | LLM variance |
| `metadata.cost_cents` | Derived from tokens |
| `params` (values) | In `structural` mode only |

---

## Input Normalization

Planners MUST normalize inputs before planning to ensure determinism:

```python
def normalize_goal(goal: str) -> str:
    """Normalize goal text for deterministic hashing."""
    return goal.strip().lower()

def normalize_context(context: Optional[str]) -> Optional[str]:
    """Normalize context for consistent inputs."""
    if context is None:
        return None
    return context.strip()

def plan_input_hash(
    agent_id: str,
    goal: str,
    context_summary: Optional[str],
    memory_snippets: Optional[List[Dict]],
    tool_manifest: Optional[List[Dict]]
) -> str:
    """Compute deterministic hash of planner inputs."""
    from app.utils.canonical_json import content_hash

    normalized = {
        "agent_id": agent_id,
        "goal": normalize_goal(goal),
        "context_summary": normalize_context(context_summary),
        "memory_snippets": memory_snippets or [],
        "tool_manifest": tool_manifest or []
    }

    return content_hash(normalized)
```

---

## Replay Testing Contract

For planners with `full` determinism:

```python
def test_planner_determinism():
    """Verify planner produces identical output for same inputs."""
    planner = StubPlanner()

    inputs = {
        "agent_id": "test-agent",
        "goal": "Fetch user data from API",
        "tool_manifest": get_test_manifest()
    }

    # First call
    output1 = planner.plan(**inputs)

    # Second call with identical inputs
    output2 = planner.plan(**inputs)

    # Must be byte-identical
    assert canonical_json(output1.plan) == canonical_json(output2.plan)
```

For planners with `structural` determinism:

```python
def test_planner_structural_determinism():
    """Verify planner produces structurally equivalent plans."""
    planner = ClaudeAdapter()

    inputs = {...}

    output1 = planner.plan(**inputs)
    output2 = planner.plan(**inputs)

    # Structure must match
    assert len(output1.plan["steps"]) == len(output2.plan["steps"])
    for s1, s2 in zip(output1.plan["steps"], output2.plan["steps"]):
        assert s1["skill"] == s2["skill"]
        assert s1["step_id"] == s2["step_id"]
```

---

## Error Handling

Planners MUST return structured errors, never throw exceptions:

```python
@dataclass
class PlannerError:
    """Planner error structure."""
    code: str               # Error code
    message: str            # Human-readable message
    retryable: bool         # Can this be retried?
    details: Dict[str, Any] # Additional context


def plan(...) -> Union[PlannerOutput, PlannerError]:
    """Return structured output or error."""
    try:
        ...
    except RateLimitError:
        return PlannerError(
            code="PLANNER_RATE_LIMITED",
            message="Planner API rate limited",
            retryable=True,
            details={"retry_after_ms": 5000}
        )
```

---

## Planner Registry

```python
PLANNER_REGISTRY = {
    "stub": {
        "class": "app.planner.stub_planner.StubPlanner",
        "determinism": "full",
        "cost_model": {"base_cents": 0, "per_call_cents": 0}
    },
    "claude": {
        "class": "app.planner.claude_adapter.ClaudeAdapter",
        "determinism": "structural",
        "cost_model": {"base_cents": 0, "per_token_cents": 0.003}
    }
}
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Initial specification |
