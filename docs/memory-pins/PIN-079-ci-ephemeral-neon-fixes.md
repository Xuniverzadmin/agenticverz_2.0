# PIN-079: CI Ephemeral Neon Branch Fixes

**Status:** COMPLETE
**Created:** 2025-12-15
**Author:** Claude Code
**Related:** PIN-045 (CI Infrastructure Fixes)

---

## Executive Summary

This PIN documents fixes applied to stabilize CI after implementing ephemeral Neon branches for database isolation. Multiple cascading issues were discovered and resolved, improving CI pass rate from 12/14 to 13/14 jobs.

---

## Issues Discovered & Fixed

### Issue 1: GitHub Actions Blocks Secret Outputs

**Symptom:**
```
##[warning]Skip output 'database_url' since it may contain secret
```
Jobs received empty `database_url` and fell back to Docker despite Neon being available.

**Root Cause:** GitHub Actions automatically blocks job outputs containing secrets (passwords).

**Fix:** Each DB-dependent job constructs DATABASE_URL via `neonctl` + `GITHUB_ENV` instead of receiving from job outputs.

**Pattern:**
```yaml
- name: Configure database connection
  run: |
    CONN=$(neonctl connection-string "$BRANCH_NAME" ...)
    echo "DATABASE_URL=$CONN" >> $GITHUB_ENV
```

**Files Changed:** `.github/workflows/ci.yml` (6 jobs updated)

---

### Issue 2: Alembic Revision ID Too Long

**Symptom:**
```
value too long for type character varying(32)
```

**Root Cause:** Revision `029_m15_1_1_simplify_sba_validator` was 34 characters, exceeding PostgreSQL's `alembic_version.version_num` varchar(32) limit.

**Fix:** Renamed to `029_m15_sba_validator` (21 chars).

**Files Changed:**
- `backend/alembic/versions/029_m15_sba_validator.py` (renamed)
- `backend/alembic/versions/030_m17_care_routing.py` (updated down_revision)

---

### Issue 3: Wrong Import Path (`app.database`)

**Symptom:**
```
ModuleNotFoundError: No module named 'app.database'
```

**Root Cause:** Multiple files imported from non-existent `app.database` instead of `app.db_async`.

**Fix:** Changed imports in 3 files (5 occurrences):

| File | Occurrences |
|------|-------------|
| `backend/app/tasks/m10_metrics_collector.py` | 3 |
| `backend/app/api/policy.py` | 1 |
| `backend/app/api/policy_layer.py` | 1 |

---

### Issue 4: Pydantic Forward Reference Not Resolved

**Symptom:**
```
pydantic.errors.PydanticUndefinedAnnotation: name 'PolicyViolation' is not defined
```
Server failed to start during e2e-tests.

**Root Cause:** `PolicyEvaluationResult` uses forward reference `"PolicyViolation"` but Pydantic v2 requires `model_rebuild()` after all classes are defined.

**Fix:** Added at end of `backend/app/policy/models.py`:
```python
# Resolve Forward References (Pydantic v2)
PolicyEvaluationResult.model_rebuild()
```

---

### Issue 5: Outbox Constraint vs Index Mismatch

**Symptom:**
```
psycopg2.errors.UndefinedObject: constraint "uq_outbox_pending" does not exist
```

**Root Cause:** Migration 022 creates a partial UNIQUE INDEX:
```sql
CREATE UNIQUE INDEX uq_outbox_pending ON m10_recovery.outbox(...) WHERE processed_at IS NULL;
```
But `publish_outbox` function uses `ON CONFLICT ON CONSTRAINT` which requires an actual named constraint.

**Fix:** Migration 034 updates function to use proper partial index syntax:
```sql
ON CONFLICT (aggregate_type, aggregate_id, event_type) WHERE processed_at IS NULL
```

**Files Changed:** `backend/alembic/versions/034_fix_outbox_constraint.py`

---

### Issue 6: E2E Worker Logs Truncated

**Symptom:** Worker appeared running but runs stayed "running" forever. Couldn't diagnose because logs showed only first 20 lines.

**Fix:** Enhanced CI worker startup:
- Wait for `worker_pool_starting` log message (not just process alive)
- Show last 50 lines instead of 20
- Add debug step showing full worker.log after tests
- Query runs table to verify run status

**Files Changed:** `.github/workflows/ci.yml`

---

## CI Consistency Checker Upgrades (v1.1)

Added new checks based on lessons learned:

```bash
# Check 5: No DATABASE_URL in job outputs (GitHub blocks secrets)
# Check 6: Neon jobs construct DATABASE_URL via neonctl
# Alembic revision ID length validation (<=32 chars)
# Migration head count check (single head only)
# Idempotent migration pattern check
```

**File:** `scripts/ops/ci_consistency_check.sh`

---

## Results

### Before Fixes
| Job | Status |
|-----|--------|
| e2e-tests | FAILED (ModuleNotFoundError) |
| m10-tests | FAILED (4/8 passed) |

### After Fixes
| Job | Status |
|-----|--------|
| e2e-tests | PASSED (20/20) |
| m10-tests | **PASSED (8/8)** |

**Overall:** 12/14 → **14/14** jobs passing

---

### Issue 7: Concurrent Migration Race Condition

**Symptom:**
```
psycopg2.errors.InternalError_: tuple concurrently updated
```
`costsim-wiremock` and other jobs intermittently failed when running migrations simultaneously.

**Root Cause:** Multiple CI jobs (integration, costsim, costsim-integration, costsim-wiremock, e2e-tests, m10-tests) all ran `alembic upgrade head` in parallel on the same Neon ephemeral branch. This caused concurrent updates to the `alembic_version` table.

**Fix:** Added dedicated `run-migrations` job that runs migrations ONCE after `setup-neon-branch`. All DB-dependent jobs now:
1. Depend on `run-migrations` job
2. Only run migrations for Docker fallback (`if: needs.setup-neon-branch.outputs.use_neon != 'true'`)

**Pattern:**
```yaml
# New job runs migrations once
run-migrations:
  needs: [setup-neon-branch]
  if: needs.setup-neon-branch.outputs.use_neon == 'true'
  steps:
    - run: alembic upgrade head  # ONLY migration run

# DB jobs depend on it and skip migrations for Neon
costsim-wiremock:
  needs: [setup-neon-branch, run-migrations, unit-tests]
  if: always() && ...
  steps:
    - name: Run Alembic migrations (Docker fallback only)
      if: needs.setup-neon-branch.outputs.use_neon != 'true'
      run: alembic upgrade head
```

**Files Changed:** `.github/workflows/ci.yml`

---

## M10 Issues - RESOLVED

All M10 schema drift issues fixed by migration 035:

1. **Function signature mismatch:** ✅ FIXED
   - Created `claim_outbox_events` overloads for both signatures
   - Created `complete_outbox_event` overloads for worker and test signatures

2. **Missing columns:** ✅ FIXED
   - Added `stream_msg_id` column
   - Added `stream_name` column
   - Added `process_after` column

**Migration:** `backend/alembic/versions/035_m10_schema_repair.py`

---

## Key Learnings

1. **GitHub Actions Secret Handling:** Never pass DATABASE_URL as job output - use GITHUB_ENV within each job.

2. **Alembic Revision IDs:** Keep under 28 chars for safety margin (limit is 32).

3. **Pydantic v2 Forward References:** Always call `model_rebuild()` on classes using forward references.

4. **PostgreSQL Partial Unique Indexes:** Cannot use `ON CONFLICT ON CONSTRAINT` - must specify columns + WHERE predicate.

5. **CI Diagnostics:** Always log enough context for debugging - truncated logs hide root causes.

6. **Concurrent Migrations:** When multiple CI jobs share a database, run migrations ONCE in a dedicated job. Never run `alembic upgrade head` in parallel across jobs.

---

## Files Changed Summary

| File | Change |
|------|--------|
| `.github/workflows/ci.yml` | Neon per-job DATABASE_URL, worker diagnostics, **run-migrations job** |
| `scripts/ops/ci_consistency_check.sh` | v1.1 with new checks |
| `backend/alembic/versions/029_m15_sba_validator.py` | Renamed (shorter ID) |
| `backend/alembic/versions/030_m17_care_routing.py` | Updated down_revision |
| `backend/alembic/versions/034_fix_outbox_constraint.py` | NEW - fix publish_outbox |
| `backend/alembic/versions/035_m10_schema_repair.py` | NEW - M10 schema repair |
| `backend/app/tasks/m10_metrics_collector.py` | Import fix |
| `backend/app/api/policy.py` | Import fix |
| `backend/app/api/policy_layer.py` | Import fix |
| `backend/app/policy/models.py` | model_rebuild() |

---

## Verification Commands

```bash
# Check alembic revision IDs
PYTHONPATH=. alembic heads

# Test imports
DATABASE_URL="..." python -c "from app.api.policy_layer import router; print('OK')"

# Run CI consistency check
bash scripts/ops/ci_consistency_check.sh
```
