# Determinism and Replay Specification v1

**Serial:** PIN-009 (draft)
**Created:** 2025-12-01
**Status:** Active
**Category:** Technical Specification

---

## Purpose

This document defines the determinism and replay guarantees provided by the AOS runtime. It serves as the binding contract for:

- Runtime engineers implementing execution logic
- Skill implementers building deterministic skills
- Planner adapters generating reproducible plans
- Testers validating runtime behavior
- SREs debugging production runs

---

## Core Definitions

### Determinism

**Determinism** = Given the same inputs and skill versions, the runtime produces identical behavior (not necessarily identical outputs from external systems).

| Aspect | Deterministic? | Notes |
|--------|----------------|-------|
| Retry logic (count, backoff timing formula) | ✅ Yes | Same retry count and backoff calculation for same error codes |
| Error classification | ✅ Yes | Same error code mapping for same HTTP status/exception type |
| Cost calculation | ✅ Yes | Same cost_cents for same skill invocation parameters |
| Skill selection order | ✅ Yes | Plan execution order is fixed |
| Budget enforcement | ✅ Yes | Same budget check outcome for same remaining budget |
| Side-effect metadata sequence | ✅ Yes | Same side-effect descriptors in same order |
| External API response content | ❌ No | Network calls return live data |
| LLM generation content | ❌ No | LLM outputs vary by design |
| Timestamps | ❌ No | Wall-clock times differ |
| Latency measurements | ❌ No | Network/system load varies |

### Replay

**Replay** = Re-executing a stored plan (list of skill calls + inputs + skill versions) without re-invoking the planner.

A replay is **successful** if the runtime exhibits identical behavior for all deterministic aspects.

---

## Deterministic Behaviors (Guaranteed)

The following behaviors are guaranteed deterministic:

### 1. Retry Policy Execution

```python
# Given same error code + retry policy → same retry decision
retry_decision = should_retry(
    error_code="ERR_HTTP_503",
    attempt_number=2,
    max_retries=3,
    retry_policy=skill_metadata.retry
)
# Result is deterministic
```

**Guarantees:**
- Same `attempt_number` and `max_retries` → same retry decision
- Backoff delay formula produces same value for same inputs
- Jitter (if any) is seeded deterministically per run_id

### 2. Error Code Mapping

```python
# Given same exception type → same error code
error_code = map_exception_to_code(exception)
# ERR_HTTP_503, ERR_DNS_FAILURE, etc.
```

**Guarantees:**
- HTTP 503 → always `ERR_HTTP_503`
- DNS resolution failure → always `ERR_DNS_FAILURE`
- Mapping is defined in `error_taxonomy.md`

### 3. Cost Calculation

```python
# Given same skill + parameters → same cost estimate
cost_cents = calculate_cost(
    skill_id="llm_invoke",
    model="claude-sonnet-4-20250514",
    input_tokens=1000,
    output_tokens=500
)
# Result is deterministic
```

**Guarantees:**
- Cost formula is fixed per skill version
- Token counting is deterministic
- Cost rounding rules are fixed

### 4. Budget Enforcement

```python
# Given same remaining budget + cost → same budget check
allowed = check_budget(
    remaining_cents=100,
    required_cents=50,
    budget_policy=agent_profile.budget
)
# Result is deterministic
```

### 5. Skill Execution Order

Plan steps execute in declared order. No reordering occurs.

### 6. StructuredOutcome Shape

For the same skill call result, the `StructuredOutcome` structure is identical:
- Same `status` for same result type
- Same `code` for same error/success type
- Same `retryable` flag for same error code

---

## Non-Deterministic Behaviors (Documented)

The following are explicitly NOT deterministic:

### 1. External API Responses

HTTP calls to external services return live data. Content varies.

**Implication:** Replay cannot guarantee same response content.

### 2. LLM Outputs

LLM invocations (even with temperature=0) may produce different text.

**Implication:** Replay cannot guarantee same LLM output.

### 3. Timestamps

`StructuredOutcome.timestamp` reflects wall-clock time at execution.

**Implication:** Replay will have different timestamps.

### 4. Latency Measurements

`StructuredOutcome.latency_ms` depends on network/system conditions.

**Implication:** Replay will have different latency values.

### 5. Rate Limit State

Rate limiter state depends on concurrent usage.

**Implication:** A call that succeeded originally may hit rate limits on replay.

---

## Replay Specification

### What is Stored for Replay

A replayable plan contains:

```json
{
  "plan_id": "uuid",
  "created_at": "ISO8601",
  "agent_id": "uuid",
  "goal": "original goal text",
  "steps": [
    {
      "step_id": "uuid",
      "skill_id": "http_call",
      "skill_version": "1.2.0",
      "parameters": {
        "url": "https://api.example.com/data",
        "method": "GET",
        "timeout_ms": 5000
      }
    }
  ],
  "context": {
    "budget_cents": 1000,
    "allowed_skills": ["http_call", "llm_invoke", "json_transform"]
  }
}
```

### Replay Invariants

During replay, the following MUST hold:

1. **Same retry behavior:** If step failed with `ERR_HTTP_503` and was retried 2 times originally, replay exhibits same retry count (assuming same error).

2. **Same cost accounting:** If step cost 5 cents originally, replay charges 5 cents (for same parameters).

3. **Same side-effect sequence:** If original logged `[webhook_sent, email_queued]`, replay logs same descriptors (with different timestamps).

4. **Same budget enforcement:** If original was stopped for budget, replay stops at same point.

5. **Same error codes:** If original returned `ERR_HTTP_TIMEOUT`, replay returns same code for same failure type.

### What Replay Does NOT Guarantee

1. **Content parity:** API responses may differ.
2. **Timing parity:** Latencies will differ.
3. **Success parity:** A call that succeeded may fail (or vice versa) due to external state changes.

### Replay Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `dry_run` | Simulate execution without side effects | Cost estimation, debugging |
| `full_replay` | Execute with live calls | Retry failed runs |
| `mock_replay` | Use stored responses from original run | Determinism testing |

---

## Determinism-Breaking Actions

The following actions break determinism guarantees:

| Action | Impact | Mitigation |
|--------|--------|------------|
| Skill version upgrade | Behavior may change | Pin versions in plan |
| Error taxonomy change | Error codes may map differently | Version error taxonomy |
| Retry policy change | Retry behavior changes | Store policy in plan |
| Budget policy change | Enforcement differs | Store policy in plan |
| Clock skew | Timeout behavior varies | Use monotonic clocks |
| Random number generation | Non-reproducible | Seed with run_id |

---

## Implementation Requirements

### For Runtime Engineers

1. **Never use unseeded randomness** in retry/backoff logic
2. **Always use error taxonomy** for error code mapping
3. **Store skill versions** in plan at creation time
4. **Use monotonic clocks** for timeout calculations
5. **Log deterministic aspects** separately from non-deterministic

### For Skill Implementers

1. **Declare deterministic outputs** in SkillMetadata
2. **Document non-deterministic behaviors** explicitly
3. **Use consistent cost formulas** per version
4. **Return same error codes** for same failure types

### For Testers

1. **Test deterministic aspects only** in replay tests
2. **Mock external calls** for determinism validation
3. **Verify retry counts, not retry timing**
4. **Verify error codes, not error messages**

---

## Testing Determinism

### Required Test Categories

| Test Type | Validates | Frequency |
|-----------|-----------|-----------|
| Unit: retry logic | Same decision for same inputs | Every commit |
| Unit: error mapping | Same code for same exception | Every commit |
| Unit: cost calculation | Same cost for same params | Every commit |
| Integration: replay behavior | Same behavior parity | Every PR |
| E2E: mock replay | Full plan replay with mocks | Nightly |

### Example Determinism Test

```python
def test_retry_decision_is_deterministic():
    """Same inputs produce same retry decision."""
    policy = RetryPolicy(max_retries=3, backoff_base_ms=100)

    # Run 100 times - must be identical
    results = [
        should_retry("ERR_HTTP_503", attempt=2, policy=policy)
        for _ in range(100)
    ]

    assert all(r == results[0] for r in results)
```

### Example Replay Test

```python
def test_replay_exhibits_same_retry_count():
    """Replay produces same retry count for same error."""
    original_plan = load_plan("test_plan.json")

    # Mock HTTP to always return 503
    with mock_http(always_503=True):
        original_result = execute(original_plan)
        replay_result = replay(original_plan)

    assert original_result.retry_count == replay_result.retry_count
    assert original_result.final_code == replay_result.final_code
```

---

## Observability

### Determinism Metrics

```
aos_replay_behavior_match_total{aspect="retry_count"}
aos_replay_behavior_match_total{aspect="error_code"}
aos_replay_behavior_mismatch_total{aspect="..."}
```

### Replay Trace Fields

```json
{
  "trace_id": "...",
  "replay_mode": "full_replay",
  "original_run_id": "...",
  "behavior_match": {
    "retry_count": true,
    "error_codes": true,
    "cost_cents": true
  }
}
```

---

---

## Field Stability Tables

### StructuredOutcome Field Stability

| Field | Must be Deterministic? | Affects Replay Assertion? | Notes |
|-------|------------------------|---------------------------|-------|
| `run_id` | NO | NO | Correlation only, unique per execution |
| `step_id` | YES | YES | Must match plan step ordering |
| `status` | YES | YES | Same result type → same status |
| `code` | YES | YES | Core replay invariant |
| `message` | NO | NO | Human-readable, may vary slightly |
| `details` | PARTIAL | NO | Structure deterministic, content may vary |
| `cost_cents` | YES | YES | Core budget invariant |
| `latency_ms` | NO | NO | Depends on network/system |
| `retryable` | YES | YES | Derived from error code |
| `side_effects` | YES (order) | YES | Order must match, timestamps ignored |
| `metadata.skill_id` | YES | YES | Immutable reference |
| `metadata.skill_version` | YES | YES | Immutable reference |
| `observability.trace_id` | NO | NO | Unique per execution |
| `observability.span_id` | NO | NO | Unique per execution |
| `observability.backend_retries` | YES | YES | Retry count invariant |
| `timestamp` | NO | NO | Wall-clock, always differs |

### Plan Field Stability

| Field | Must be Deterministic? | Notes |
|-------|------------------------|-------|
| `plan_id` | YES | Immutable after creation |
| `agent_id` | YES | Immutable reference |
| `goal` | YES | Original goal text |
| `steps[].step_id` | YES | Stable ordering reference |
| `steps[].skill_id` | YES | Immutable per step |
| `steps[].skill_version` | YES | Pinned at plan creation |
| `steps[].parameters` | YES | Immutable inputs |
| `context.budget_cents` | YES | Budget at plan creation |
| `context.allowed_skills` | YES | Permissions at plan creation |
| `created_at` | NO | Informational only |

---

## Forbidden Fields (MUST NOT Affect Determinism)

The following fields MUST NEVER influence runtime behavior or replay assertions:

| Field | Reason |
|-------|--------|
| `timestamp` | Wall-clock time varies |
| `latency_ms` | Network/system dependent |
| `trace_id` | Unique per execution |
| `span_id` | Unique per execution |
| `message` | Human-readable, may have minor variations |
| `details.response_body` | External API content |
| `details.llm_output` | LLM content varies |

**Implementation Rule:** Any code path that uses these fields to make decisions MUST be flagged as a determinism violation.

---

## Allowed Nondeterminism Zones

| Zone | What Varies | What Stays Constant |
|------|-------------|---------------------|
| **External API Content** | Response body, headers | Error code mapping, retry behavior |
| **LLM Output** | Generated text, tokens | Cost calculation, timeout handling |
| **Timing** | Latency, timestamps | Timeout thresholds, backoff formula |
| **Rate Limits** | Current limiter state | Rate limit error code (ERR_RATE_LIMITED) |
| **Concurrent State** | Other agent activity | Per-agent isolation guarantees |

---

## Side-Effect Ordering Guarantee

Side-effects MUST be recorded in **execution order** and MUST be **stable across replays**.

### Rules

1. **Append-only:** Side-effects are appended to the list as they occur
2. **No reordering:** Order reflects actual execution sequence
3. **Timestamp ignored:** Timestamps are informational, not compared in replay
4. **Type + target deterministic:** Same skill + params → same side-effect type

### Example

```json
{
  "side_effects": [
    {"type": "http_request", "target": "api.example.com", "timestamp": "..."},
    {"type": "webhook_sent", "target": "hooks.slack.com", "timestamp": "..."}
  ]
}
```

During replay, the assertion checks:
- ✅ Same number of side-effects
- ✅ Same `type` values in same order
- ✅ Same `target` values in same order
- ❌ Timestamps are NOT compared

---

## How Retries Influence Replay

### Retry Count is a Replay Invariant

If the original execution retried a step N times, the replay MUST exhibit the same retry count when encountering the same error sequence.

### Retry Decision Formula

```python
def should_retry(error_code: str, attempt: int, policy: RetryPolicy) -> bool:
    """Deterministic retry decision."""
    if attempt >= policy.max_retries:
        return False
    if error_code not in policy.retryable_codes:
        return False
    return True
```

### Backoff Calculation

```python
def calculate_backoff_ms(attempt: int, policy: RetryPolicy, run_id: str) -> int:
    """Deterministic backoff with optional seeded jitter."""
    base = policy.backoff_base_ms * (policy.backoff_multiplier ** attempt)
    if policy.jitter_enabled:
        # Jitter is seeded by run_id for reproducibility
        seed = hash(f"{run_id}:{attempt}")
        jitter = (seed % 100) / 100.0 * policy.jitter_max_ms
        return int(base + jitter)
    return int(base)
```

### Replay Assertion Example

```python
def assert_retry_behavior_matches(original: RunResult, replay: RunResult):
    """Verify retry behavior is deterministic."""
    for step_id in original.steps:
        orig_step = original.get_step(step_id)
        replay_step = replay.get_step(step_id)

        assert orig_step.retry_count == replay_step.retry_count, \
            f"Step {step_id}: retry count mismatch"
        assert orig_step.final_code == replay_step.final_code, \
            f"Step {step_id}: final error code mismatch"
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Added field stability tables, forbidden fields, nondeterminism zones |
| 2025-12-01 | Added side-effect ordering guarantee |
| 2025-12-01 | Added retry influence on replay section |
| 2025-12-01 | Initial specification v1 |

---

## Related Documents

- [error_taxonomy.md](error_taxonomy.md) - Error code definitions
- [PIN-008](../../docs/memory-pins/PIN-008-v1-milestone-plan-full.md) - v1 Milestone Plan
- [PIN-005](../../docs/memory-pins/PIN-005-machine-native-architecture.md) - Machine-Native Architecture
