# PIN-264: Phase-2.3 Feature Intent System

**Status:** COMPLETE
**Date:** 2025-12-31
**Category:** Architecture / Self-Defense
**Related PINs:** Phase-2.1 (Self-Defending Primitives), Phase-2.2 (Intent Declaration)

---

## Summary

Phase-2.3 extends the intent declaration system from function-level (TransactionIntent) to feature-level (FeatureIntent + RetryPolicy). This creates a three-layer hierarchy where module-level intent constrains function-level intent, which in turn constrains implementation primitives.

## Problem Statement

Phase-2.2 established TransactionIntent for function-level self-defense. However:

1. **Gap 1:** Intent exists only for transactions, not for other critical axes (idempotency, retry safety, side-effects)
2. **Gap 2:** Intent is enforced at function level, not feature level
3. **Gap 3:** CI enforces correctness, but not completeness

A feature is rarely one function. Without feature-level intent, engineers can write functions that are "locally correct, globally wrong."

## Solution: Intent Hierarchy

```
FeatureIntent (module-level)
     ↓ constrains
TransactionIntent (function-level)
     ↓ constrains
Primitive (implementation-level)
```

If any layer disagrees, CI fails.

## Implementation

### Files Created

| File | Purpose |
|------|---------|
| `app/infra/feature_intent.py` | FeatureIntent, RetryPolicy enums, @feature decorator |
| `app/infra/feature_intent_examples.py` | Golden examples for all valid combinations |
| `scripts/ci/check_feature_intent.py` | CI enforcement for module-level declarations |

### Files Updated

| File | Changes |
|------|---------|
| `app/infra/__init__.py` | Export feature intent system |
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | v2.28 - Full intent hierarchy documentation |

## FeatureIntent Enum

| Intent | Meaning | Allowed TransactionIntent |
|--------|---------|--------------------------|
| `PURE_QUERY` | Read-only, no state changes | READ_ONLY only |
| `STATE_MUTATION` | Changes system state (DB writes) | ATOMIC_WRITE, LOCKED_MUTATION |
| `EXTERNAL_SIDE_EFFECT` | Calls external services | ATOMIC_WRITE only |
| `RECOVERABLE_OPERATION` | Must be idempotent and resumable | LOCKED_MUTATION only |

## RetryPolicy Enum

| Policy | Meaning | Required For |
|--------|---------|--------------|
| `NEVER` | Retries are forbidden | EXTERNAL_SIDE_EFFECT (required) |
| `SAFE` | Retries are safe (idempotent) | RECOVERABLE_OPERATION (required) |
| `DANGEROUS` | Retries need manual review | Warning only |

## Module Declaration Pattern

Every state-touching module must declare at module level:

```python
from app.infra import FeatureIntent, RetryPolicy

FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE
```

## Intent Consistency Matrix

| FeatureIntent | Allowed TransactionIntent | Required RetryPolicy |
|---------------|--------------------------|---------------------|
| PURE_QUERY | READ_ONLY | any |
| STATE_MUTATION | ATOMIC_WRITE, LOCKED_MUTATION | any |
| EXTERNAL_SIDE_EFFECT | ATOMIC_WRITE | NEVER (required) |
| RECOVERABLE_OPERATION | LOCKED_MUTATION | SAFE (required) |

## CI Enforcement

`scripts/ci/check_feature_intent.py` validates:

1. **MISSING_FEATURE_INTENT:** Module uses persistence but has no FEATURE_INTENT declaration
2. **INTENT_CONSISTENCY:** TransactionIntent not in allowed set for FeatureIntent
3. **MISSING_RETRY_POLICY:** EXTERNAL_SIDE_EFFECT or RECOVERABLE_OPERATION without RETRY_POLICY
4. **RETRY_POLICY_VIOLATION:** Forbidden combination (e.g., EXTERNAL_SIDE_EFFECT + SAFE)

## Golden Examples

`app/infra/feature_intent_examples.py` provides reference implementations for:

- `PureQueryExample` - PURE_QUERY + READ_ONLY
- `AtomicWriteExample` - STATE_MUTATION + ATOMIC_WRITE
- `LockedMutationExample` - STATE_MUTATION + LOCKED_MUTATION
- `ExternalSideEffectExample` - EXTERNAL_SIDE_EFFECT + ATOMIC_WRITE + NEVER
- `RecoverableOperationExample` - RECOVERABLE_OPERATION + LOCKED_MUTATION + SAFE

## Anti-Patterns Documented

1. Missing FEATURE_INTENT in persistence modules
2. Intent mismatch (PURE_QUERY with LOCKED_MUTATION)
3. Side effects with wrong retry policy (SAFE instead of NEVER)
4. Recoverable without lock (ATOMIC_WRITE instead of LOCKED_MUTATION)

## Canonical Instruction Set (from user feedback)

1. **FeatureIntent mandatory:** Every module that touches state MUST declare
2. **Intent consistency:** Feature ↔ function ↔ primitive must align
3. **RetryPolicy declaration:** EXTERNAL_SIDE_EFFECT requires NEVER, RECOVERABLE requires SAFE
4. **Golden examples:** Every intent combination has a reference implementation
5. **Incident → Constraint Loop:** Incidents become CI-enforced invariants
6. **SESSION_PLAYBOOK is declarative:** Source of truth, not human memory

## Phase-2 Complete Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase-2.1 | Self-Defending Primitives (SingleConnectionTxn) | COMPLETE |
| Phase-2.2 | Intent Declaration (TransactionIntent + @transactional) | COMPLETE |
| Phase-2.3 | Feature Intent (FeatureIntent + RetryPolicy) | COMPLETE |

## Next Steps (Future Work)

1. Migrate existing modules to declare FEATURE_INTENT (128 violations found)
2. Add test coverage for intent validation
3. Consider additional intent axes (e.g., PII handling, audit requirements)

---

## References

- `app/infra/feature_intent.py` - Core implementation
- `app/infra/feature_intent_examples.py` - Golden examples
- `scripts/ci/check_feature_intent.py` - CI enforcement
- `docs/playbooks/SESSION_PLAYBOOK.yaml` - v2.28 documentation
