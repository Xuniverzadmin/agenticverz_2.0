# Intent Boilerplate Templates

**Status:** ENFORCED
**Reference:** PIN-268 (GU-003), PIN-264 (Feature Intent System)

---

## Purpose

Every module in critical directories MUST declare its intent at creation time.
This is enforced by CI via `scripts/ci/check_feature_intent.py`.

**Directories requiring intent:**
- `app/worker/` - All workers
- `app/services/` - All services
- `app/jobs/` - All background jobs
- `app/tasks/` - All scheduled tasks

---

## Quick Reference: Which Intent Do I Need?

| Question | Answer | Intent |
|----------|--------|--------|
| Does this module only read data? | Yes | `PURE_QUERY` |
| Does this module write to DB? | Yes | `STATE_MUTATION` |
| Does this module call external APIs? | Yes | `EXTERNAL_SIDE_EFFECT` |
| Must this module be crash-resumable? | Yes | `RECOVERABLE_OPERATION` |

---

## Template 1: Service (STATE_MUTATION)

Most services write to the database. Use this template:

```python
# Layer: L4 — Domain Engines
# Product: {product-name | system-wide}
# Temporal:
#   Trigger: {user | api | worker | scheduler}
#   Execution: {sync | async}
# Role: {One-line description of what this service does}
# Callers: {Who calls this service?}
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-XXX (if applicable)

"""
{ServiceName}: {Brief description}

This service handles {what it does}.
"""

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE  # or NEVER/DANGEROUS

# ... rest of imports and code ...
```

---

## Template 2: Worker (RECOVERABLE_OPERATION)

Workers must be crash-resumable. Use this template:

```python
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker-pool
#   Execution: sync-over-async
# Role: {What this worker executes}
# Authority: {What state this worker can mutate}
# Callers: WorkerPool (via ThreadPoolExecutor)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md
# Pattern: Sync-over-async per contract

"""
{WorkerName}: {Brief description}

This worker executes {what it does} and must be idempotent.
"""

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Workers must be RECOVERABLE_OPERATION with SAFE retry policy
FEATURE_INTENT = FeatureIntent.RECOVERABLE_OPERATION
RETRY_POLICY = RetryPolicy.SAFE

# ... rest of imports and code ...
```

---

## Template 3: Job (STATE_MUTATION or RECOVERABLE)

Background jobs usually mutate state. Use this template:

```python
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: async
# Role: {What this job does}
# Callers: Scheduler / Cron
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3

"""
{JobName}: {Brief description}

This job runs {on what schedule} to {what it does}.
"""

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

# ... rest of imports and code ...
```

---

## Template 4: External API Caller (EXTERNAL_SIDE_EFFECT)

Modules that call external APIs. Use this template:

```python
# Layer: L4 — Domain Engines
# Product: {product-name | system-wide}
# Temporal:
#   Trigger: {user | api | worker}
#   Execution: async
# Role: {What external service this calls}
# External: {Name of external service}
# Callers: {Who calls this?}
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3

"""
{ServiceName}: {Brief description}

This service calls {external service} for {purpose}.
WARNING: External side effects - cannot be safely retried.
"""

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# External side effects MUST have NEVER retry policy
FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
RETRY_POLICY = RetryPolicy.NEVER

# ... rest of imports and code ...
```

---

## Template 5: Read-Only Query (PURE_QUERY)

Modules that only read data. Use this template:

```python
# Layer: L4 — Domain Engines
# Product: {product-name | system-wide}
# Temporal:
#   Trigger: {user | api}
#   Execution: sync
# Role: {What queries this performs}
# Callers: {Who calls this?}
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3

"""
{QueryServiceName}: {Brief description}

This service provides read-only queries for {what data}.
"""

from app.infra import FeatureIntent

# Phase-2.3: Feature Intent Declaration
# Pure queries don't need retry policy
FEATURE_INTENT = FeatureIntent.PURE_QUERY

# ... rest of imports and code ...
```

---

## Intent Consistency Matrix

| FeatureIntent | Allowed TransactionIntent | Required RetryPolicy |
|---------------|---------------------------|---------------------|
| `PURE_QUERY` | `READ_ONLY` | None |
| `STATE_MUTATION` | `ATOMIC_WRITE`, `LOCKED_MUTATION` | Any |
| `EXTERNAL_SIDE_EFFECT` | `ATOMIC_WRITE` | `NEVER` |
| `RECOVERABLE_OPERATION` | `LOCKED_MUTATION` | `SAFE` |

---

## CI Enforcement

```bash
# Check a specific directory
python3 scripts/ci/check_feature_intent.py app/services/

# Check entire codebase
python3 scripts/ci/check_feature_intent.py app/
```

CI will FAIL if:
- Module uses persistence but has no `FEATURE_INTENT`
- `TransactionIntent` disagrees with `FeatureIntent`
- `RetryPolicy` is wrong for the `FeatureIntent`

---

## References

- PIN-264 (Feature Intent System)
- PIN-268 (Guidance System Upgrade - GU-003)
- `app/infra/feature_intent.py` (Implementation)
- `scripts/ci/check_feature_intent.py` (CI checker)
