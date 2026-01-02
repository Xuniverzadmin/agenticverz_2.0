# PIN-276: Bucket A/B Permanent Fix Design

**Status:** DESIGN APPROVED
**Category:** CI / Infrastructure
**Created:** 2026-01-02
**Related:** PIN-267, PIN-275

---

## Executive Summary

Buckets A and B must be **closed permanently** through system changes, not test patches. This PIN defines the exact structural changes required to eliminate these problem classes forever.

**Core Principle:** If you "fix tests" without changing system rules, these buckets WILL return.

---

## The Real Problem

| Bucket | Root Cause | NOT the cause |
|--------|------------|---------------|
| A | Test execution shares state | asyncio, pytest, flaky tests |
| B | Infra truth is implicit | Missing services |

Current state allows ambiguity. Future drift is inevitable under:
- Parallel CI
- New engineers
- Infra additions
- Customer traffic

**Solution:** Change the rules of the system.

---

## Bucket A: Test Isolation (NON-NEGOTIABLE FIX)

### Invariant Violation

> A test can affect another test.

This is unacceptable in a production-grade system.

### Required Fix: Choose ONE Strategy

#### Option A (Recommended): Transaction Rollback Per Test

**Properties:** Fast, local, deterministic

**Rule:**
- Every test runs inside a DB transaction
- Transaction is rolled back after the test
- No test commits durable state

**Implementation:**
```python
# conftest.py - Session-scoped engine, function-scoped transaction
@pytest.fixture(scope="function")
async def db_session(engine):
    async with engine.begin() as conn:
        # Create savepoint for nested transactions
        await conn.begin_nested()
        yield conn
        # Rollback everything
        await conn.rollback()
```

**Result:**
- Zero state bleed
- Zero ordering dependence
- No infra duplication

#### Option B: Ephemeral Schema Per Test

**Properties:** Stronger, slower, bulletproof

**Rule:**
- Each test uses a unique schema
- Dropped after test

#### Option C: Ephemeral Database Per Test

**Properties:** Ultimate isolation, highest cost (CI only)

### A1 Decision Rule (LOCKED)

```
Bucket A is considered FIXED only when:
- Running pytest --random-order never changes results
- Running pytest -n auto never changes results
- Any test can be run in isolation OR suite with same result
```

**No exceptions.**

### A2 System Rule (Add to SESSION_PLAYBOOK.yaml)

```yaml
TEST_ISOLATION_RULE:
  invariant: "No test may depend on state created by another test"
  enforcement:
    - transaction rollback OR schema isolation
    - random order CI check
  violation: "Architecture bug, not test bug"
```

Once this exists:
- Engineers stop "fixing flaky tests"
- They fix **state leaks**

---

## Bucket B: Infra Skips (FIXED, NOT STUBBED)

### Core Rule

> If infra exists in production, it must exist locally in a real form.

This does NOT mean "full production setup".

### Correct Infra Model

Every infra component must be in exactly one state:

| State | Meaning |
|-------|---------|
| A | Not available anywhere |
| B | Real, minimal, local-compatible |
| C | Full production-grade |

**Bucket B only exists when infra is State A.**
Goal: Promote infra from A → B, not skip tests forever.

### Required Infra Promotions

#### B1. Database
**Current:** State C
**Status:** DONE

#### B2. RBAC / Clerk
**Current:** State B (real semantics, local-compatible)
**Status:** DONE

#### B3. Prometheus
**Current:** State A (skipped)
**Required:** State B

**State B Prometheus means:**
- Real Prometheus client
- In-process registry
- No external server
- Metrics available synchronously

**NOT:**
- Fake counters
- Dummy returns

**Result:**
- Metrics tests RUN
- Infra tests RUN
- No skips

#### B4. Replay Infrastructure
**Current:** State A (skipped)
**Required:** State B

**State B Replay means:**
- Replay produces an artifact
- Stored in memory or local DB
- Deterministic
- Not production-scale, but real semantics

#### B5. Agents / M12
**Current:** Explicitly deferred
**Status:** CORRECT - product decision, not infra

### Enforced Rule (Add to INFRA_REGISTRY.md)

```text
Rule:
No test may be skipped due to missing infra
unless the infra is in State A.

If infra is in State B or C,
tests MUST run.
```

This prevents silent drift forever.

---

## Final State After Implementation

### Bucket A
- Does not exist
- Test order irrelevant
- Parallel-safe
- CI scalable

### Bucket B
- Does not exist
- Infra gaps resolved structurally
- No fake stubs
- No surprises at customer onboarding

### CI
- Deterministic
- Honest
- Predictive of production behavior

---

## Execution Order

**DO NOT MIX THESE**

### Phase 1: Bucket A Elimination

1. Choose isolation strategy (recommend Option A)
2. Implement globally in conftest.py
3. Add random-order CI check
4. Prove determinism with `pytest --random-order`

### Phase 2: Bucket B Elimination

1. Promote Prometheus to State B
2. Promote Replay infra to State B
3. Remove all infra-based skips
4. Re-run full suite

### Phase 3: Lock the Rules

1. Update SESSION_PLAYBOOK.yaml with TEST_ISOLATION_RULE
2. Update INFRA_REGISTRY.md with State enforcement
3. Add CI guardrails (fail on new skips without governance)

---

## Hard Stop Rule (Post-Implementation)

After this is complete:

| Condition | Classification |
|-----------|----------------|
| Test fails due to isolation | **BUG** |
| Test fails due to missing infra | **Infra not done** |
| Test is skipped | **Governance violation** |

No more ambiguity.

---

## Prometheus State B Design (Concrete)

```python
# backend/tests/conftest.py

from prometheus_client import CollectorRegistry, Counter, Histogram

@pytest.fixture(scope="function")
def prometheus_registry():
    """Per-test Prometheus registry - no external server needed."""
    registry = CollectorRegistry()
    yield registry
    # Automatically cleaned up

@pytest.fixture(scope="function")
def metrics(prometheus_registry):
    """Real metrics with real semantics, isolated per test."""
    return {
        "requests": Counter(
            "test_requests_total",
            "Test request counter",
            registry=prometheus_registry
        ),
        "latency": Histogram(
            "test_latency_seconds",
            "Test latency histogram",
            registry=prometheus_registry
        ),
    }
```

This is:
- Real Prometheus client
- Real counters and histograms
- Isolated per test
- No external server
- State B compliant

---

## Conclusion

> What you're building now is not just a codebase —
> it's an **organization-proof system**.

These fixes change the system contract, not just tests. Future engineers cannot reintroduce these problems because the rules prevent it.

---

## Changelog

- 2026-01-02: Initial design approved
