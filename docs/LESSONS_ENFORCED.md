# LESSONS_ENFORCED.md

**Status:** ACTIVE
**Last Updated:** 2025-12-26 (S6 Trace Integrity - Invariants #13, #14, #15 added)
**Purpose:** Mechanically enforced invariants that survive Claude session restarts

---

## Why This Document Exists

> **Claude memory is irrelevant. Only code + CI + contracts persist.**

This document captures lessons that were learned through failure. Each invariant listed here:
1. Caused actual failures in Phase A.5 verification
2. Is now enforced by code or CI
3. Will produce a clear error if violated

If Claude forgets, CI fails, the error message reminds it, and the fix is rediscovered mechanically.

---

## Invariant #4: Async Database URLs

### Rule
asyncpg requires `postgresql+asyncpg://` scheme and `ssl` as connect_args, not URL parameter.

### Enforcement
- Conversion occurs **ONLY** in `app/db.py:get_async_database_url()`
- Manual URL conversion is **FORBIDDEN** elsewhere

### CI Guard
```bash
# Fail if anyone creates async engines outside db.py
grep -R "create_async_engine" backend/app | grep -v "app/db.py" && exit 1
grep -R "postgresql+asyncpg" backend | grep -v "app/db.py" && exit 1
```

### Error Message
```
RuntimeError: ASYNC_DB_URL_INVARIANT_VIOLATION
```

---

## Invariant #5: Import Locality

### Rule
All shared helpers must be explicitly imported. Transitive imports are forbidden.

### Canonical Location
```python
from app.utils.runtime import generate_uuid, utc_now
```

### Enforcement
- `generate_uuid()` and `utc_now()` are defined **ONLY** in `app/utils/runtime.py`
- Services must import them explicitly, not rely on other modules importing them

### CI Guard
```bash
# Fail if generate_uuid / utc_now are used without correct import
grep -R "generate_uuid(" backend/app | grep -v "from app.utils.runtime"
grep -R "utc_now(" backend/app | grep -v "from app.utils.runtime" | grep -v "def utc_now"
```

### Error Message
```
ImportError: cannot import name 'generate_uuid' from '...'
```

---

## Invariant #6: Verification Script Architecture

### Rule
Verification scripts must use the same infrastructure as production code.

### Forbidden
- Manual engine creation (`create_engine()`, `create_async_engine()`)
- URL manipulation (`.replace("postgresql://", ...)`)
- Re-implementing helper logic

### Required
```python
# CORRECT: Use canonical factories
from app.db import get_async_session_factory, get_engine
from app.utils.runtime import generate_uuid, utc_now

AsyncSessionLocal = get_async_session_factory()
sync_engine = get_engine()
```

### CI Guard
```bash
# Fail if verification scripts create engines directly
grep -R "create_engine\|create_async_engine" backend/scripts/verification && exit 1
grep -R "\.replace.*postgresql" backend/scripts/verification && exit 1
```

---

## Invariant #7: Cost Advisory Idempotency

### Rule
One advisory per (run_id, anomaly_type). Duplicates are skipped.

### Enforcement
```sql
CREATE UNIQUE INDEX uniq_cost_advisory_per_run
ON cost_anomalies ((metadata->>'run_id'), anomaly_type)
WHERE metadata->>'run_id' IS NOT NULL;
```

### Error Message
```
UniqueViolation: duplicate key value violates unique constraint "uniq_cost_advisory_per_run"
```

---

## Invariant #8: Incident Without Violation Fact

### Rule
No incident may exist without a persisted violation fact.

### Enforcement (VERIFICATION_MODE)
```python
if VERIFICATION_MODE:
    if not violation.persisted:
        is_persisted = await self.check_violation_persisted(violation.id)
        if not is_persisted:
            raise RuntimeError("INCIDENT_WITHOUT_VIOLATION_FACT")
```

---

## Invariant #9: Evidence Before Incident

### Rule
Evidence must exist before incident creation in VERIFICATION_MODE.

### Enforcement
```python
if VERIFICATION_MODE and not violation.evidence:
    raise RuntimeError("INCIDENT_WITHOUT_EVIDENCE")
```

---

## Invariant #10: No Lazy Service Resolution

### Rule
Services MUST be constructed with explicit dependency injection. Factory or getter functions that hide dependencies are **FORBIDDEN**.

### Why This Matters
Lazy service resolution (e.g., `get_incident_aggregator()`) creates execution-order-dependent failures:
- Production flow → works
- Verification script → different execution order → fails
- This causes recurring "intermittent" failures that are actually deterministic

### Forbidden Pattern
```python
# BANNED: Hidden dependencies
aggregator = get_incident_aggregator()  # DON'T DO THIS
```

### Required Pattern
```python
# REQUIRED: Explicit dependency injection
from app.services.incident_aggregator import create_incident_aggregator

aggregator = create_incident_aggregator()

# OR for maximum control:
from app.services.incident_aggregator import IncidentAggregator
from app.utils.runtime import generate_uuid, utc_now

aggregator = IncidentAggregator(
    clock=utc_now,
    uuid_fn=generate_uuid,
)
```

### Enforcement
- `IncidentAggregator.__init__()` requires `clock` and `uuid_fn` parameters
- `get_incident_aggregator()` is deleted from codebase
- All construction must use `create_incident_aggregator()` or explicit constructor

### CI Guard
```bash
# Fail if banned factory function is used
grep -rq "get_incident_aggregator\s*(" backend/app && exit 1

# Fail if IncidentAggregator is constructed without explicit DI
grep -rE "IncidentAggregator\s*\([^)]*\)" backend/app | grep -v "clock=" && exit 1
```

### Error Message
```
TypeError: IncidentAggregator.__init__() missing required argument: 'clock'
```

---

## Invariant #11: UTC Time Handling

### Rule
`datetime.utcnow()` is **FORBIDDEN**. All timestamps must be timezone-aware (UTC).

### Why This Matters
- `datetime.utcnow()` is deprecated in Python 3.12+
- It produces timezone-naive datetimes that cause comparison bugs
- "Temporal truth" violations corrupt audit trails and failure timelines
- S4 verification caught this as a deprecation warning → elevated to hard invariant

### Canonical Pattern
```python
from app.utils.runtime import utc_now, utc_now_naive

# Standard usage (preferred)
created_at = utc_now()  # Returns timezone-aware UTC datetime

# For asyncpg raw SQL (only when explicitly needed)
inserted_at = utc_now_naive()  # Returns naive UTC for database compatibility
```

### Forbidden Patterns
```python
# BANNED: deprecated and timezone-naive
datetime.utcnow()
datetime.datetime.utcnow()

# BANNED: ambiguous local time
datetime.now()  # without timezone argument

# BANNED: manual UTC construction outside runtime.py
datetime.now(timezone.utc)  # use utc_now() instead
```

### Database Schema
```sql
-- All timestamp columns MUST use TIMESTAMPTZ
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```

### Enforcement
- `utc_now()` and `utc_now_naive()` are defined **ONLY** in `app/utils/runtime.py`
- CI guard in `.github/workflows/import-hygiene.yml` rejects `datetime.utcnow()`
- Runtime.py uses `datetime.now(timezone.utc)` internally

### CI Guard
```bash
# Fail if deprecated datetime.utcnow() is used
grep -rn "datetime\.utcnow" backend/app --include="*.py" && exit 1
grep -rn "utcnow()" backend/app --include="*.py" | grep -v "def utc_now" && exit 1
```

### Error Message
```
DeprecationWarning: datetime.utcnow() is deprecated
::error::Found deprecated datetime.utcnow() usage (use utc_now() from app.utils.runtime)
```

---

## Invariant #12: asyncpg + PgBouncer

### Rule
asyncpg uses **prepared statements**. PgBouncer (transaction pooling) does **NOT** support prepared statements. In VERIFICATION_MODE, asyncpg must connect directly to PostgreSQL.

### Why This Matters
- asyncpg always uses prepared statements for performance
- PgBouncer in transaction/statement pooling mode cannot handle prepared statements
- Results in cryptic errors: `DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_1__" already exists`
- S5 verification caught this → elevated to hard invariant

### Connection Roles

| Use Case | Driver | Port |
|----------|--------|------|
| Production sync | psycopg2 | 6432 (PgBouncer) |
| Verification / async | asyncpg | 5433 (direct PG) |

### Canonical Pattern
```python
from urllib.parse import urlparse

db_url = os.getenv("DATABASE_URL", "")
parsed = urlparse(db_url.replace("+asyncpg", ""))

if "asyncpg" in db_url and parsed.port == 6432:
    raise RuntimeError(
        "VERIFICATION_MODE forbids PgBouncer (port 6432) with asyncpg. "
        "Use direct PostgreSQL port (e.g. 5433)."
    )
```

### Environment Variables
```bash
# Sync path (production, via PgBouncer)
DATABASE_URL_SYNC=postgresql://nova:novapass@localhost:6432/nova_aos

# Async path (verification, direct PG)
DATABASE_URL=postgresql+asyncpg://nova:novapass@localhost:5433/nova_aos
```

### Enforcement
- All asyncpg verification scripts MUST include the port guard
- Guard is placed at script startup, before any DB operations
- Failure is immediate and obvious

### Error Message
```
❌ FAIL: VERIFICATION_MODE forbids PgBouncer (port 6432) with asyncpg.
   asyncpg uses prepared statements which PgBouncer does not support.
   Use direct PostgreSQL port (e.g. 5433).
```

---

## Invariant #17: Acceptance Test Behavioral Gates

**Date Added:** 2025-12-27
**Incident:** PB-S2 acceptance testing wasted hours on auth thrash, DB mismatch, wrong crash target, and mid-test code fixes.

### Failure Categories

| Category | Symptom | Root Cause |
|----------|---------|------------|
| A | Trial-and-error auth headers | No AUTH_CONTRACT declared first |
| B | FK failures, empty tables | Container used Neon, tests used local PgBouncer |
| C | Fixed timezone bug mid-test | Code modification during acceptance |
| D | FK on worker_registry | No readiness checklist before run creation |
| E | Crashed wrong component | Assumed worker, actually backend |

### Rules Added

| Rule ID | Name | Purpose |
|---------|------|---------|
| BL-ACC-001 | Acceptance Immutability | No code changes during acceptance tests |
| BL-RDY-001 | Runtime Readiness | Verify DB match, tenants, worker_registry before runs |
| BL-EXEC-001 | Execution Topology | Identify executor/async_model before crash |

### Enforcement

- **Behavior Library**: `docs/behavior/behavior_library.yaml`
- **Validator**: Responses trigger rule if keywords present without required sections
- **Required Sections**: `ACCEPTANCE_PRECHECK`, `RUNTIME_READINESS`, `EXECUTION_TOPOLOGY`

### Key Invariant

> **Acceptance tests are read-only operations on the system under test.**
> If a precondition fails, STOP and report blocker. Do not fix-to-proceed.

### Correct Behavior

Before PB-S2 or any acceptance scenario:
1. Declare `ACCEPTANCE_PRECHECK` with code freeze
2. Complete `RUNTIME_READINESS` (container DB, tenants, registry)
3. If crash test: complete `EXECUTION_TOPOLOGY` (executor, async model, target)
4. If ANY field is NO → STOP, report blocker, exit

---

## How to Add New Invariants

1. **Document the failure** - What broke, why, when
2. **Write the enforcement code** - Runtime check or CI guard
3. **Add clear error message** - Claude-readable
4. **Add to this document** - With enforcement location
5. **Add CI guard** - If applicable

---

## Invariant #13: Trace Ledger Semantics

### Rule
Traces are append-only. No UPDATE/DELETE permitted post-commit. Archive-before-delete is mandatory.

### Why This Matters
S6 (Trace Integrity Truth) depends on traces being a **fact ledger**, not a mutable log. If traces can be modified:
- Audit trails become unreliable
- Replay produces different results over time
- "What actually happened" becomes unknowable

### Canonical Pattern
```python
# CORRECT: Append-only insert, ignore duplicates
INSERT INTO aos_trace_steps (...) VALUES (...)
ON CONFLICT (trace_id, step_index) DO NOTHING

# FORBIDDEN: Upsert that modifies existing data
ON CONFLICT ... DO UPDATE SET ...  # NEVER for trace steps
```

### Enforcement
```sql
-- DB trigger rejects UPDATE on aos_trace_steps
CREATE TRIGGER enforce_trace_step_immutability
BEFORE UPDATE ON aos_trace_steps
FOR EACH ROW
EXECUTE FUNCTION reject_trace_step_update();

-- DB trigger restricts aos_traces UPDATE to status/completed_at only
CREATE TRIGGER enforce_trace_immutability
BEFORE UPDATE ON aos_traces
FOR EACH ROW
EXECUTE FUNCTION restrict_trace_update();
```

### Error Message
```
S6_IMMUTABILITY_VIOLATION: aos_trace_steps is immutable. UPDATE rejected.
```

---

## Invariant #14: Replay Is Observational

### Rule
Replay must be **read-only**. It must not:
- Emit traces
- Generate new IDs
- Consult wall-clock time

### Why This Matters
If replay emits traces, then "looking at history changes history." This is the #1 audit-destroyer.

### Canonical Pattern
```python
# CORRECT: Replay with emit_traces=False (default)
result = await replay_run(run_id, emit_traces=False)

# FORBIDDEN during replay:
uuid4()           # Generates non-deterministic ID
utc_now()         # Consults wall-clock
datetime.now()    # Same
random.choice()   # Non-deterministic
```

### Enforcement
```python
# In runtime/replay.py
async def replay_run(..., emit_traces: bool = False):
    """
    S6 IMMUTABILITY: By default, replay does NOT emit new traces.
    """
    if emit_traces:
        await self.trace_store.start_trace(...)  # Only if explicitly requested
```

### CI Guard
```bash
# Fail if replay service uses non-deterministic functions
grep -R "uuid4()" app/runtime/replay.py && exit 1
grep -R "utc_now()" app/runtime/replay.py && exit 1
```

### Error Message
```
TRACE_EMITTED_DURING_REPLAY: Replay must be read-only.
```

---

## Invariant #15: First Truth Wins

### Rule
`ON CONFLICT → DO NOTHING`. No "fixing history". No silent reconciliation.

### Why This Matters
This is how financial ledgers work:
- First recorded fact is authoritative
- Corrections are **new entries**, not mutations
- No "latest truth wins" race conditions

### Canonical Pattern
```python
# CORRECT: First truth persists
INSERT INTO aos_traces (...) VALUES (...)
ON CONFLICT (trace_id) DO NOTHING

# FORBIDDEN: Silent merge that overwrites truth
ON CONFLICT (trace_id) DO UPDATE SET trace = EXCLUDED.trace  # NEVER
```

### Enforcement
- All trace INSERT statements use `ON CONFLICT ... DO NOTHING`
- DB triggers reject UPDATE attempts
- Archive-before-delete enforced by trigger

### Error Message
```
S6_IMMUTABILITY_VIOLATION: Trace mutation attempted. First truth wins.
```

---

## Reference

| Invariant | Location | Type |
|-----------|----------|------|
| #4 Async DB URLs | `app/db.py` | Code |
| #5 Import Locality | `app/utils/runtime.py` | Code + CI |
| #6 Verification Scripts | CI | CI |
| #7 Advisory Idempotency | Database index | Database |
| #8 Incident Without Violation | `policy_violation_service.py` | Code |
| #9 Evidence Before Incident | `policy_violation_service.py` | Code |
| #10 No Lazy Service Resolution | `incident_aggregator.py` | Code + CI |
| #11 UTC Time Handling | `app/utils/runtime.py` | Code + CI |
| #12 asyncpg + PgBouncer | Verification scripts | Code |
| #13 Trace Ledger Semantics | `pg_store.py` + DB triggers | Code + Database |
| #14 Replay Is Observational | `runtime/replay.py` | Code + CI |
| #15 First Truth Wins | `pg_store.py` + DB triggers | Code + Database |
| #16 Single Migration Head | `check_migration_heads.sh` + BL-MIG-002 | CI + Behavior Library |

---

## Invariant #16: Single Migration Head

**Date Added:** 2025-12-27
**Incident:** Migration 051 skipped 049/050 via explicit `down_revision = "048..."`, creating a fork with two heads.
**Impact:** Migrations could not be applied cleanly; required manual merge (054_merge_heads).
**Root Cause:** Developer explicitly skipped revisions assuming "independent features" could branch.

### Rule

> **There must be exactly ONE migration head at all times.**
>
> Multiple heads = migration fork = BLOCKED.

### Pattern

```bash
# BEFORE any migration work:
./scripts/ops/check_migration_heads.sh

# Expected output:
✅ Single migration head: 054_merge_heads (head)

# If multiple heads:
❌ BL-MIG-002 VIOLATION: Multiple migration heads detected!
# MUST fix before proceeding
```

### Forbidden

```python
# NEVER skip revisions
down_revision = "048_..."  # Skip 049/050 - FORBIDDEN

# NEVER ignore multiple heads warning
alembic upgrade head  # With multiple heads - BLOCKED
```

### Correct Pattern

```python
# Always chain from the SINGLE current head
down_revision = "054_merge_heads"  # The one and only head

# If fork exists, merge first:
alembic merge heads -m "merge_description"
alembic upgrade head
# Then create new migration
```

### Enforcement

- CI script: `scripts/ops/check_migration_heads.sh` (exit 1 on multiple heads)
- Behavior Library: BL-MIG-002 (BLOCKER severity)
- Boot Contract: Required section `SINGLE HEAD CHECK`

### Exception: Merge Migrations

Creating a merge migration is the **only** allowed operation when multiple heads exist.

Required section: `MERGE_JUSTIFICATION`

```
MERGE JUSTIFICATION (exception to BL-MIG-002)
- Reason: resolving existing fork
- Heads to merge: [050_xxx, 053_xxx]
- Merge command: alembic merge heads -m "merge_description"
- Post-merge verification: alembic heads (must show single)
```

### Error Message

```
BL-MIG-002 VIOLATION: Multiple migration heads detected!
Cannot proceed with migration work until fork is resolved.
Exception: merge migrations allowed with MERGE_JUSTIFICATION section.
```

---

## Invariant #18: FastAPI Async Session Dependencies

### Rule

Functions decorated with `@asynccontextmanager` are **incompatible** with FastAPI's `Depends()`. FastAPI expects async generator functions, not context manager objects.

### Failure Pattern

```python
# BAD: This breaks FastAPI Depends()
@asynccontextmanager
async def get_async_session():
    async with session_factory() as session:
        yield session

# When used with Depends(), FastAPI receives _AsyncGeneratorContextManager
# instead of the yielded session
session: AsyncSession = Depends(get_async_session)  # ❌ BROKEN
# Error: '_AsyncGeneratorContextManager' object has no attribute 'execute'
```

### Correct Pattern

```python
# For use with `async with` in non-FastAPI code
@asynccontextmanager
async def get_async_session():
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# For FastAPI Depends() - NO decorator
async def get_async_session_dep() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Usage in endpoints
session: AsyncSession = Depends(get_async_session_dep)  # ✅ CORRECT
```

### Canonical Location

```
backend/app/db.py
  - get_async_session()       → for `async with` usage
  - get_async_session_dep()   → for FastAPI Depends()
```

### CI Guard

```bash
# Warn if @asynccontextmanager is used with Depends()
grep -r "@asynccontextmanager" backend/app | while read line; do
    file=$(echo $line | cut -d: -f1)
    func=$(echo $line | grep -oP 'def \K\w+')
    if grep -q "Depends($func)" backend/app/**/*.py 2>/dev/null; then
        echo "WARNING: $func uses @asynccontextmanager but is used with Depends()"
    fi
done
```

### Error Message

```
AttributeError: '_AsyncGeneratorContextManager' object has no attribute 'execute'
```

### Reference

- PIN-411 (Aurora Activity Data Population)
- Issue discovered: 2026-01-13

---

## Session Start Protocol

Before ANY work, these invariants should be verified:

```bash
# Quick check - all should pass silently
./scripts/verification/truth_preflight.sh
```

If any invariant is violated, fix it before proceeding.
