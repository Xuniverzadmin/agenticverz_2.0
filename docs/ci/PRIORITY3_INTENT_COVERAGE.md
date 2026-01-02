# Priority-3 Intent Freeze Coverage Scope

**Status:** ENFORCED
**Effective:** 2026-01-02
**Reference:** PIN-265 (Phase-3 Intent-Driven Refactoring)
**CI Guard:** `check_intent_violations.py`

---

## Purpose

This document defines the **coverage scope** of the Priority-3 Intent Freeze (FEATURE_INTENT declarations).

The Priority-3 freeze is NOT a full system intent enforcement. It specifically covers layers L3-L6.

---

## Coverage Summary

| Layer | Status | Enforcement | Description |
|-------|--------|-------------|-------------|
| L1 (Product Experience) | DECLARATIVE ONLY | Not enforced | UI pages, components |
| L2 (Product APIs) | DECLARATIVE ONLY | Not enforced | REST endpoints |
| **L3 (Boundary Adapters)** | **ENFORCED** | CI-blocking | Thin translation layers |
| **L4 (Domain Engines)** | **ENFORCED** | CI-blocking | Business rules, system truth |
| **L5 (Execution & Workers)** | **ENFORCED** | CI-blocking | Background jobs |
| **L6 (Platform Substrate)** | **ENFORCED** | CI-blocking | DB, Redis, external services |
| L7 (Ops & Deployment) | DECLARATIVE ONLY | Not enforced | Systemd, Docker |
| L8 (Catalyst / Meta) | DECLARATIVE ONLY | Not enforced | CI, tests, validators |

---

## Why This Scope?

### L3-L6: ENFORCED

These layers are where **state mutations** and **external side effects** occur:

- **L3 (Adapters):** Entry points that can trigger mutations
- **L4 (Domain Engines):** Business logic that mutates state
- **L5 (Workers):** Background jobs that must be recoverable
- **L6 (Platform):** Direct infrastructure access

Intent violations here can cause:
- Silent data corruption
- Non-idempotent retries
- Orphaned transactions
- Lost recovery opportunities

### L2, L7, L8: DECLARATIVE ONLY

These layers are **not yet enforced** because:

- **L2 (APIs):** API routes are thin wrappers; intent is delegated to L3/L4
- **L7 (Ops):** Deployment scripts are not state-touching in production
- **L8 (Meta):** Test files and CI scripts are ephemeral

However, files in these layers **should** declare intent where applicable. This prepares for future full-system enforcement.

---

## Current Coverage Statistics (2026-01-02)

| Layer | Files with Intent | Violations | Enforcement |
|-------|-------------------|------------|-------------|
| L3 | 0 | 0 | BLOCKING |
| L4 | 37 | 0 | BLOCKING |
| L5 | 6 | 0 | BLOCKING |
| L6 | 21 | 0 | BLOCKING |
| **Total Enforced** | **64** | **0** | **BLOCKING** |

---

## Intent Distribution

Based on the latest scan (`check_intent_violations.py --all`):

### By Intent Type

| Intent | Count | Description |
|--------|-------|-------------|
| STATE_MUTATION | 35 | DB writes, atomic operations |
| PURE_QUERY | 14 | Read-only operations |
| EXTERNAL_SIDE_EFFECT | 7 | LLM, webhooks, alerts |
| RECOVERABLE_OPERATION | 5 | Workers, queues, orchestrators |

### By Directory

```
app/costsim:       STATE_MUTATION: 4, EXTERNAL_SIDE_EFFECT: 1
app/infra:         STATE_MUTATION: 2
app/jobs:          EXTERNAL_SIDE_EFFECT: 2, PURE_QUERY: 1, STATE_MUTATION: 1
app/memory:        PURE_QUERY: 2, STATE_MUTATION: 2, EXTERNAL_SIDE_EFFECT: 1
app/optimization:  STATE_MUTATION: 2
app/policy:        STATE_MUTATION: 1
app/services:      STATE_MUTATION: 24, PURE_QUERY: 8, EXTERNAL_SIDE_EFFECT: 3
app/tasks:         PURE_QUERY: 1, RECOVERABLE_OPERATION: 1
app/worker:        RECOVERABLE_OPERATION: 4, STATE_MUTATION: 1
app/workflow:      PURE_QUERY: 2, STATE_MUTATION: 1
```

---

## Enforcement Scripts

### 1. Intent Violation Checker (`check_intent_violations.py`)

**Location:** `scripts/ops/check_intent_violations.py`

**Usage:**
```bash
# Full scan with coverage details
python scripts/ops/check_intent_violations.py --all

# CI mode (exit 1 on violations)
python scripts/ops/check_intent_violations.py --ci

# Scan specific path
python scripts/ops/check_intent_violations.py --path backend/app/services/
```

**What it checks:**
- PURE_QUERY files must NOT have session.commit(), session.add(), etc.
- PURE_QUERY files must NOT have httpx/requests calls
- STATE_MUTATION files must have RETRY_POLICY
- EXTERNAL_SIDE_EFFECT files must have RETRY_POLICY

### 2. Obligation Aging Reporter (`obligation_aging_report.py`)

**Location:** `scripts/ops/obligation_aging_report.py`

**Usage:**
```bash
# Full report
python scripts/ops/obligation_aging_report.py

# CI mode (exit 1 on stale obligations)
python scripts/ops/obligation_aging_report.py --ci

# Custom max age
python scripts/ops/obligation_aging_report.py --max-age 45

# JSON output
python scripts/ops/obligation_aging_report.py --json
```

---

## Violation Types

### MUTATION_IN_PURE_QUERY

A file declares `FEATURE_INTENT = FeatureIntent.PURE_QUERY` but contains mutation patterns:

- `session.commit()`
- `session.flush()`
- `session.add()`
- `session.delete()`
- INSERT/UPDATE/DELETE statements

**Fix:** Change intent to `STATE_MUTATION` and add `RETRY_POLICY = RetryPolicy.SAFE`

### EXTERNAL_CALL_IN_PURE_QUERY

A file declares `FEATURE_INTENT = FeatureIntent.PURE_QUERY` but makes external calls:

- `httpx.get/post/put/delete/patch`
- `requests.get/post/put/delete/patch`
- Email sending (`.send()`)
- Redis writes (`redis_client.set/delete/lpush/rpush`)

**Fix:** Change intent to `EXTERNAL_SIDE_EFFECT` and add `RETRY_POLICY = RetryPolicy.NEVER`

### MISSING_RETRY_POLICY

A file declares `STATE_MUTATION` or `EXTERNAL_SIDE_EFFECT` but has no `RETRY_POLICY`.

**Fix:** Add `RETRY_POLICY = RetryPolicy.SAFE` (for STATE_MUTATION) or `RETRY_POLICY = RetryPolicy.NEVER` (for EXTERNAL_SIDE_EFFECT)

---

## Future Expansion

### Phase: L2 Enforcement (APIs)

When ready, extend enforcement to L2:
- Add intent declarations to all API routes
- Verify routes delegate correctly to L3/L4

### Phase: L7/L8 Enforcement (Ops/Meta)

When ready, extend enforcement to L7/L8:
- Add intent declarations to deployment scripts
- Verify test files don't accidentally mutate production state

---

## CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
intent-violation-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Check Intent Violations
      run: |
        python scripts/ops/check_intent_violations.py --ci
```

---

## History

| Date | Action | Reference |
|------|--------|-----------|
| 2026-01-02 | Initial L3-L6 enforcement (64 files) | PIN-265, Phase-3 |
| 2026-01-02 | Created intent violation checker | PIN-265 |
| 2026-01-02 | Fixed worker_registry_service.py misclassification | PIN-265 |

---

## See Also

- PIN-264: Phase-2.3 Feature Intent System
- PIN-265: Phase-3 Intent-Driven Refactoring
- `docs/ci/PRIORITY5_INTENT_CANONICAL.md`: Priority-5 (Critical) files
- `backend/app/infra/feature_intent.py`: Intent enums and validation
- `docs/infra/INFRA_OBLIGATION_REGISTRY.yaml`: Infrastructure obligations
