# PIN-006: Execution Plan Review & Realistic Roadmap

**Serial:** PIN-006
**Created:** 2025-12-01
**Status:** Active
**Category:** Architecture / Planning

---

## Executive Summary

This PIN reviews the proposed "Machine-Native SDK Build Plan" and provides a critical assessment of timelines, scope, and priorities. It identifies what's good, what's problematic, and recommends a realistic 12-week MVP plan.

---

## Part 1: Assessment of Proposed Plan

### What's Good

**1. Clear interface definitions**
The six runtime interfaces are specific and implementable:
- `runtime.execute(skill, params)`
- `runtime.describe_skill(name)`
- `runtime.query(what, filters)`
- `runtime.simulate(plan[])`
- `runtime.get_resource_contract(run_id)`
- `failure_catalog`

**2. Realistic tiering**
Tier 0 → Tier 1 → Tier 2 → Tier 3 progression makes sense.

**3. Stability tests defined**
Determinism tests, failure injection, budget exhaustion, concurrency — correct focus areas.

**4. Iteration loop is sensible**
Pick internal workflow → model → run → capture failures → update → release.

---

### Problems Identified

#### 1. Timeline is 2x Too Optimistic

| What | Proposed | Realistic |
|------|----------|-----------|
| Tier 0 (5 skills) | Weeks 1-6 | 8-10 weeks |
| Tier 1 (5 skills) | Weeks 6-12 | 14-18 weeks |
| Tier 2 (3 skills) | Weeks 12-16 | 20-26 weeks |
| Web console | "minimal" | 4-6 weeks alone |

**Why the gap:**
- `kv_store` needs Redis connection pooling, namespace isolation, TTL edge cases
- `email_send` needs SMTP config, bounce handling, deliverability testing
- `file_parse (PDF)` is messy (encodings, scanned PDFs, malformed files)
- `code_execute (sandbox)` is a security nightmare — even "v1" takes 4+ weeks
- Web console "minimal" still means auth, routing, state management, API integration

---

#### 2. Failure Catalog is Underspecified

Proposed:
> "Store: code, category, retryable, suggestions, recovery stats"
> "Query interface: `failure_catalog.match(error)`"

Unanswered questions:
- How does `match()` work? Exact code? Fuzzy similarity? ML-based?
- What's "recovery stats" — success rate of what recovery action?
- Where is this data stored? How is it updated?

**Recommendation:** Start with a dumb lookup table. `code → {category, retryable, suggestions}`. No ML. No "similarity." Prove value first.

---

#### 3. Simulation Engine is Hand-Wavy

Proposed:
> "Rule-based cost/latency estimator"
> "Risk matrix"
> "Feasibility checks"

Problems:
- What rules?
- How do you estimate latency for `http_call` to an arbitrary URL?
- How do you know risk probability without historical data?

**Reality:** Simulation without historical data is guessing.

**Recommendation for v1:**
- Sum of `cost_estimate` from each skill (static)
- Sum of `avg_latency_ms` from skill metadata (static)
- Permission checks (deterministic)
- Budget check (deterministic)

No "risk matrix" until you have data.

---

#### 4. Web Console is Scope Creep

Proposed "minimal" features:
- Run viewer
- Plan simulator
- Skill inspector
- Run search

Each is a significant feature. "Minimal but production-ready" is contradictory.

**Recommendation:** Ship with CLI only first. Web console is Phase 2. Developers evaluating SDKs care about the SDK, not the dashboard. LangChain didn't need a web console for adoption.

---

#### 5. Missing: Error Code Taxonomy

"Structured failures" mentioned repeatedly but no taxonomy defined.

**Must define NOW:**

```
ERROR_CATEGORY:
  - TRANSIENT    (retry might work)
  - PERMANENT    (don't retry)
  - RESOURCE     (budget/rate limit)
  - PERMISSION   (not allowed)
  - VALIDATION   (bad input)

ERROR_CODES:
  - TIMEOUT
  - DNS_FAILURE
  - CONNECTION_REFUSED
  - HTTP_4XX
  - HTTP_5XX
  - RATE_LIMITED
  - BUDGET_EXCEEDED
  - DAILY_LIMIT_EXCEEDED
  - PERMISSION_DENIED
  - SKILL_NOT_FOUND
  - INVALID_INPUT
  - SCHEMA_VALIDATION_FAILED
  - UPSTREAM_ERROR
  - INTERNAL_ERROR
```

This taxonomy must be defined BEFORE building skills. Otherwise each skill invents its own codes → inconsistency.

---

#### 6. Missing: What "Determinism" Actually Means

Proposed:
> "Guarantees determinism for same inputs + skill version"

But `http_call` is inherently non-deterministic (external APIs change). `llm_invoke` is non-deterministic (LLM outputs vary).

**Clarification needed:**

| Layer | Deterministic? |
|-------|---------------|
| Runtime behavior | ✅ Yes (same error handling, retry logic) |
| Execution metadata | ✅ Yes (same cost calculation, side-effect logging) |
| Skill results | ❌ No (I/O skills have external dependencies) |

"Deterministic runtime" ≠ "Deterministic results"

---

#### 7. Missing: Resource Allocation

Task list without owners. Questions:
- Solo developer or team?
- Who builds runtime vs skills vs console vs docs?
- What's the actual capacity per week?

**If solo:** Cut scope by 60%. Focus on runtime + 3 skills + CLI + one demo.

---

#### 8. Monthly Architecture Reviews are Premature

Monthly reviews useful when you have:
- Multiple contributors with diverging approaches
- Production users giving feedback
- Technical debt accumulating

At current stage: Ship first, review later.

---

## Part 2: Recommended Realistic Roadmap

### Phase 1: Core Contracts (Weeks 1-2)

**Goal:** Define the foundation before writing code.

| Deliverable | Description |
|-------------|-------------|
| Error taxonomy | Categories + codes + when to use each |
| `StructuredOutcome` schema | Pydantic model for all skill returns |
| `SkillMetadata` schema | What `describe_skill()` returns |
| `ResourceContract` schema | Budget/rate limits/timeouts structure |
| `FailureInfo` schema | Structured error with recovery hints |

**No code yet.** Just specs in markdown/Pydantic.

---

### Phase 2: Runtime Core (Weeks 3-6)

**Goal:** Build the runtime wrapper that makes everything machine-native.

| Deliverable | Description |
|-------------|-------------|
| `runtime.execute()` | Wrapper that never throws, returns `StructuredOutcome` |
| `runtime.describe_skill()` | Returns `SkillMetadata` for any registered skill |
| `runtime.query()` | Query budget, state, history, rate limits |
| `runtime.get_resource_contract()` | Returns current constraints for a run |
| Skill executor refactor | All skills go through `runtime.execute()` |

---

### Phase 3: Three Skills Done Right (Weeks 7-10)

**Goal:** Prove the runtime works with real skills.

| Skill | Key Features |
|-------|--------------|
| `http_call` | Full failure handling (timeout, DNS, 4xx, 5xx), side-effect logging, cost model |
| `llm_invoke` | Multi-model, cost tracking, token accounting, structured responses |
| `json_transform` | JSONPath extraction, schema validation, deterministic |

Each skill must:
- Use `StructuredOutcome` return format
- Have complete `SkillMetadata`
- Handle all error categories properly
- Have unit tests + failure injection tests

---

### Phase 4: CLI + Demo (Weeks 11-12)

**Goal:** Make it usable and demonstrable.

| Deliverable | Description |
|-------------|-------------|
| `aos run` | Execute a goal against an agent |
| `aos simulate` | Dry-run a plan, show cost/feasibility |
| `aos describe-skill` | Show skill metadata |
| `aos query` | Query runtime state |
| Demo script | End-to-end machine-native behavior demo |

**Demo scenario:**
```
Goal: "Fetch Bitcoin price and summarize"

1. runtime.get_resource_contract() → shows budget
2. runtime.simulate(plan) → shows cost estimate
3. runtime.execute(http_call) → timeout occurs
4. Structured failure returned with recovery hint
5. Automatic retry with backoff
6. Success → runtime.execute(llm_invoke) → summarize
7. Full execution trace with costs
```

---

### Phase 5: Iterate (Week 13+)

Based on internal usage, add:
- `kv_store` (Redis)
- `slack_send` / `webhook_send`
- Improved failure catalog
- Additional skills as needed

---

## Part 3: What NOT to Build Yet

| Feature | Why Defer |
|---------|-----------|
| Web console | CLI is sufficient for alpha; console is 4-6 weeks |
| Failure catalog with ML/similarity | Lookup table first; intelligence requires data |
| Risk matrix in simulation | Need historical data; static estimates first |
| `code_execute` sandbox | Security complexity; defer to Phase 3 |
| `browser_action` | Complex; defer to Phase 3 |
| `file_parse (PDF)` | Edge cases are endless; defer |
| Monthly architecture reviews | Ship first |
| External alpha | After internal validation |

---

## Part 4: Critical Specs Needed Next

Before writing more code, define these specs:

### 1. StructuredOutcome Schema

```python
class StructuredOutcome(BaseModel):
    success: bool
    result: Optional[Any] = None
    failure: Optional[FailureInfo] = None
    execution: ExecutionMetadata
    side_effects: List[SideEffect] = []

class FailureInfo(BaseModel):
    code: str                          # e.g., "TIMEOUT"
    category: ErrorCategory            # TRANSIENT, PERMANENT, etc.
    message: str
    retryable: bool
    retry_after_ms: Optional[int] = None
    suggestions: List[str] = []

class ExecutionMetadata(BaseModel):
    skill: str
    version: str
    latency_ms: int
    cost_cents: int
    retries: int
    timestamp: datetime
    trace_id: str

class SideEffect(BaseModel):
    type: str                          # HTTP_REQUEST, DB_WRITE, etc.
    target: str
    reversible: bool
```

### 2. SkillMetadata Schema

```python
class SkillMetadata(BaseModel):
    name: str
    version: str
    description: str
    input_schema: dict                 # JSON Schema
    output_schema: dict                # JSON Schema
    cost_model: CostModel
    failure_modes: List[FailureMode]
    constraints: SkillConstraints
    composition_hints: Optional[CompositionHints] = None

class CostModel(BaseModel):
    base_cents: int = 0
    per_unit: Optional[str] = None     # e.g., "per_kb", "per_token"
    per_unit_cents: int = 0

class FailureMode(BaseModel):
    code: str
    category: ErrorCategory
    typical_cause: str
    retryable: bool

class SkillConstraints(BaseModel):
    max_input_size_bytes: Optional[int] = None
    timeout_ms: int = 30000
    rate_limit_per_minute: Optional[int] = None
    blocked_patterns: List[str] = []
```

### 3. Error Code Taxonomy

```python
class ErrorCategory(str, Enum):
    TRANSIENT = "transient"      # Retry might work
    PERMANENT = "permanent"      # Don't retry
    RESOURCE = "resource"        # Budget/rate limit
    PERMISSION = "permission"    # Not allowed
    VALIDATION = "validation"    # Bad input

# Standard error codes
ERROR_CODES = {
    # Transient
    "TIMEOUT": ErrorCategory.TRANSIENT,
    "DNS_FAILURE": ErrorCategory.TRANSIENT,
    "CONNECTION_REFUSED": ErrorCategory.TRANSIENT,
    "HTTP_5XX": ErrorCategory.TRANSIENT,
    "UPSTREAM_UNAVAILABLE": ErrorCategory.TRANSIENT,

    # Permanent
    "HTTP_4XX": ErrorCategory.PERMANENT,
    "NOT_FOUND": ErrorCategory.PERMANENT,
    "INVALID_RESPONSE": ErrorCategory.PERMANENT,

    # Resource
    "RATE_LIMITED": ErrorCategory.RESOURCE,
    "BUDGET_EXCEEDED": ErrorCategory.RESOURCE,
    "DAILY_LIMIT_EXCEEDED": ErrorCategory.RESOURCE,
    "QUOTA_EXHAUSTED": ErrorCategory.RESOURCE,

    # Permission
    "PERMISSION_DENIED": ErrorCategory.PERMISSION,
    "SKILL_NOT_ALLOWED": ErrorCategory.PERMISSION,
    "BLOCKED_TARGET": ErrorCategory.PERMISSION,

    # Validation
    "INVALID_INPUT": ErrorCategory.VALIDATION,
    "SCHEMA_VALIDATION_FAILED": ErrorCategory.VALIDATION,
    "MISSING_REQUIRED_FIELD": ErrorCategory.VALIDATION,
}
```

---

## Part 5: Success Criteria for Alpha

Alpha is ready when:

| Criteria | Measurement |
|----------|-------------|
| Runtime interfaces work | All 4 core interfaces implemented and tested |
| 3 skills complete | http_call, llm_invoke, json_transform with full metadata |
| CLI functional | `aos run`, `aos simulate`, `aos describe-skill` work |
| Demo works | End-to-end machine-native demo runs successfully |
| Tests pass | Determinism, failure injection, budget tests green |
| Internal workflow | At least 1 real Agenticverz/Mobiverz workflow running |

---

## Summary

### Grade for Original Plan: B+

Good structure, but:
- Timelines 2x too optimistic
- Some features underspecified
- Web console should be cut
- Error taxonomy missing
- "Determinism" needs clarification

### Recommended Focus

**Weeks 1-12:**
1. Core contracts (specs)
2. Runtime core (4 interfaces)
3. Three skills done right
4. CLI + demo

**Cut from v1:**
- Web console
- ML-based failure matching
- Risk matrix
- code_execute, browser_action, file_parse

### Next Action

Define the exact specs for:
1. `StructuredOutcome`
2. `SkillMetadata`
3. Error taxonomy

These are the foundation. Everything builds on them.

---

## Related PINs

- [PIN-001](PIN-001-aos-roadmap-status.md) - Original roadmap
- [PIN-002](PIN-002-critical-review.md) - Critical architecture review
- [PIN-005](PIN-005-machine-native-architecture.md) - Machine-native architecture definition

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Initial creation - Execution plan review and realistic roadmap |
