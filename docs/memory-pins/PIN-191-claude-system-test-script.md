# PIN-191: Claude System Test Script

**Status:** ACTIVE (Run in Parallel with Founder Beta)
**Category:** Testing / Verification / System Correctness
**Created:** 2025-12-26
**Milestone:** Runtime v1 Beta
**Related:** PIN-188 (Beta Signals), PIN-189 (Phase A Closure)

---

## Purpose

Verify **data propagation and system correctness** across all UI surfaces.

This is NOT:
- UX feedback
- Feature suggestions
- Navigation redesign

This IS:
- Truth verification
- Gap detection
- Propagation validation

---

## Rule (LOCKED)

> **Claude may validate propagation, not suggest UX changes unless a P0 truth gap is found.**

Valid findings:
- "Data missing here" → VALID
- "Inconsistent between pages" → VALID
- "Expected field not shown" → VALID

Invalid findings:
- "This page should show more" → IGNORE
- "Navigation could be better" → IGNORE
- "Add explanation here" → IGNORE

---

## Test Environment

| Component | Requirement |
|-----------|-------------|
| LLM | Real Anthropic Claude (not mock) |
| Database | Real PostgreSQL (Neon or local) |
| API | Real backend (localhost:8000 or api.agenticverz.com) |
| UI | Real console (localhost:5173 or agenticverz.com/console) |

### Preflight Requirement (BLOCKING)

Before running ANY scenario (S2-S6), execute the truth preflight:

```bash
./scripts/verification/truth_preflight.sh
```

**Exit code 0 required. Any other result blocks scenario execution.**

See PIN-194 for detailed preflight requirements.

### CI Subordination Rule

Claude system tests are **subordinate** to the CI truth preflight gate.

| Priority | Gate |
|----------|------|
| 1 (Highest) | CI `Truth Preflight Gate` workflow |
| 2 | Local `truth_preflight.sh` execution |
| 3 | Claude system test execution |

If CI preflight has not passed, Claude MUST NOT proceed with system tests.

See `.github/workflows/truth-preflight.yml` and `docs/OPERATING_RULES.md`.

---

## Test Matrix

### T-001: LLM Timeout → Incident Visibility

**Setup:**
```bash
# Create a run that will timeout
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "workflow_id": "timeout-test",
    "timeout_ms": 100,
    "skills": ["slow_skill"]
  }'
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Guard > Runs | Run shows with TIMEOUT status | [ ] |
| Guard > Runs > Detail | OUTCOME section shows timeout reason | [ ] |
| Guard > Incidents | Incident created for timeout | [ ] |
| Incidents > Detail | Root cause shows timeout | [ ] |
| Founder Timeline | Decision record shows halt | [ ] |

**Pass Criteria:** All 5 locations show consistent timeout information.

---

### T-002: Token Overrun → Cost Delta Visibility

**Setup:**
```bash
# Create a run with budget that will be exceeded
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "workflow_id": "cost-test",
    "budget_tokens": 100,
    "skills": ["expensive_skill"]
  }'
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Guard > Runs > Detail | PRE-RUN shows budget: 100 tokens | [ ] |
| Guard > Runs > Detail | COST shows estimated vs actual | [ ] |
| Guard > Runs > Detail | Delta badge shows difference | [ ] |
| Guard > Limits | Budget usage updated | [ ] |
| Founder Timeline | Cost decision recorded | [ ] |

**Pass Criteria:** Cost delta visible with correct sign (+ or -).

---

### T-003: Budget Mode Advisory vs Enforced

**Setup:**
```bash
# Test 1: Advisory mode (should continue)
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{"budget_mode": "advisory", "budget_tokens": 50}'

# Test 2: Enforced mode (should halt)
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{"budget_mode": "enforced", "budget_tokens": 50}'
```

**Verify in UI:**

| Page | Advisory Run | Enforced Run | Check |
|------|--------------|--------------|-------|
| Guard > Runs > Detail | Badge: ADVISORY | Badge: ENFORCED | [ ] |
| Guard > Runs > Detail | Run continued past budget | Run halted at budget | [ ] |
| Guard > Limits | Warning shown for advisory | No warning for enforced | [ ] |
| Founder Timeline | Decision: "continued (advisory)" | Decision: "halted (enforced)" | [ ] |

**Pass Criteria:** Mode correctly reflected in all locations.

---

### T-004: Policy Violation → Constraint Visibility

**Setup:**
```bash
# Create a run that violates a policy
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{
    "agent_id": "test-agent",
    "skills": ["blocked_skill"],
    "policy_id": "strict-policy"
  }'
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Guard > Runs > Detail | CONSTRAINTS section shows policy ✗ | [ ] |
| Guard > Runs > Detail | Policy name linked | [ ] |
| Guard > Incidents | Policy violation incident | [ ] |
| Incidents > Detail | Policy referenced | [ ] |
| Founder Timeline | Decision: policy_blocked | [ ] |

**Pass Criteria:** Policy violation visible with correct policy ID.

---

### T-005: Memory Injection → PRE-RUN Visibility

**Setup:**
```bash
# Create a run with memory injection
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{
    "agent_id": "test-agent",
    "memory_context": ["pin-001", "pin-002"],
    "skills": ["memory_skill"]
  }'
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Guard > Runs > Detail | PRE-RUN shows "Memory Injected: 2 pins" | [ ] |
| Founder Timeline | Memory injection recorded | [ ] |
| Founder Timeline | Pin IDs visible | [ ] |

**Pass Criteria:** Memory injection count and IDs visible.

---

### T-006: Retry → DecisionTimeline Causality

**Setup:**
```bash
# Create a run that will retry
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{
    "agent_id": "test-agent",
    "max_retries": 3,
    "skills": ["flaky_skill"]
  }'
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Founder Timeline | Multiple decision records for same run | [ ] |
| Founder Timeline | Retry count visible | [ ] |
| Founder Timeline | Each retry shows reason | [ ] |
| Guard > Runs > Detail | Final outcome reflects retries | [ ] |

**Pass Criteria:** Retry chain visible with causal linking.

---

### T-007: Trace Hash Mismatch → Verification Status

**Setup:**
```bash
# Create a run, then corrupt trace hash
# (This may require direct DB manipulation for testing)
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Traces > Detail | Verification Status: UNVERIFIED | [ ] |
| Traces > Detail | Warning indicator visible | [ ] |
| Guard > Runs > Detail | Trace link shows warning | [ ] |

**Pass Criteria:** Unverified state clearly indicated.

---

### T-008: Cross-Entity Navigation

**Setup:**
```bash
# Create incident → run → trace chain
```

**Verify in UI:**

| Navigation | Expected | Check |
|------------|----------|-------|
| Incidents list → Incident detail | O2 → O3 works | [ ] |
| Incident detail → Run | Cross-link works | [ ] |
| Run detail → Trace | Cross-link works | [ ] |
| Trace detail → Run | Back-link works | [ ] |
| All pages | Breadcrumb correct | [ ] |

**Pass Criteria:** All cross-entity links work, breadcrumbs reset correctly.

---

### T-009: Rate Limit Hit → Constraint Visibility

**Setup:**
```bash
# Rapidly create runs to hit rate limit
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/v1/runs \
    -H "X-API-Key: $AOS_API_KEY" \
    -d '{"agent_id": "test-agent"}'
done
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Guard > Limits | Rate limit usage shown | [ ] |
| Guard > Runs > Detail | CONSTRAINTS shows rate ✗ (if hit) | [ ] |
| Founder Timeline | Rate limit decision recorded | [ ] |

**Pass Criteria:** Rate limit visibility consistent.

---

### T-010: Multi-Step Run → Step Summary

**Setup:**
```bash
# Create a run with multiple steps
curl -X POST http://localhost:8000/api/v1/runs \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{
    "agent_id": "test-agent",
    "skills": ["step1", "step2", "step3", "step4", "step5"]
  }'
```

**Verify in UI:**

| Page | Expected | Check |
|------|----------|-------|
| Guard > Runs > Detail | Step count shown | [ ] |
| Traces > Detail | All 5 steps listed | [ ] |
| Traces > Detail | Success/fail count correct | [ ] |
| Traces > Detail | Duration shown | [ ] |

**Pass Criteria:** Step summary accurate, no step missing.

---

## Test Execution Log

| Test ID | Date | Result | Notes |
|---------|------|--------|-------|
| T-001 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-002 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-003 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-004 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-005 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-006 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-007 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-008 | 2025-12-26 | PARTIAL | Cross-entity nav testable via empty state |
| T-009 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |
| T-010 | 2025-12-26 | BLOCKED | Database mismatch - see P0-001 |

---

## Findings Log

### P0 Truth Gaps (Must Fix)

| Finding | Location | Expected | Actual | Status |
|---------|----------|----------|--------|--------|
| **P0-001**: Database mismatch | Backend container → DATABASE_URL | Local PostgreSQL (localhost:6432/nova_aos) | Neon Cloud (neondb) | RESOLVED (Option B selected) |
| **P0-002**: Trace API returns 0 | `/api/v1/runtime/traces` | 2 traces (from local DB) | 0 traces | CAUSED BY P0-001 |
| **P0-003**: Runs API returns 0 | `/api/v1/workers/business-builder/runs` | 106 runs (from local DB) | 0 runs | CAUSED BY P0-001 |
| **P0-004**: Incidents API error | `/ops/incidents` | Incident list | Internal Server Error | OPEN |
| **P0-005**: In-memory only run storage | `backend/app/api/workers.py:180-192` | Runs persisted to PostgreSQL | **FIXED**: Now uses async PostgreSQL persistence | ✅ **RESOLVED** |

### Database State Comparison (2025-12-26)

| Entity | Local PostgreSQL | Neon Cloud | Propagation |
|--------|------------------|------------|-------------|
| Runs | 106 (40 succeeded, 9 failed, 57 running) | 0 | BLOCKED |
| Traces | 2 (tenant: default) | 0 | BLOCKED |
| Incidents (costsim_cb_incidents) | 1 (P1 severity) | Unknown | BLOCKED |

### Root Cause Analysis

The backend container is configured with:
```
DATABASE_URL=postgresql://neondb_owner:***@ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

This connects to Neon cloud database which has no data, while historical test data exists in local PostgreSQL at `localhost:6432/nova_aos`.

**Impact**: All verification scenarios (S1-S6) are blocked until database alignment is resolved.

### P0-005 Root Cause Analysis (CRITICAL)

**Discovery Date:** 2025-12-26 (Verification Run 2)

After executing Option B (fresh verification data in Neon), a run completed successfully with full artifacts but **0 rows appeared in any database**.

**Root Cause Code** (`backend/app/api/workers.py:180-192`):

```python
# Simple in-memory storage for runs
# In production, this would be persisted to PostgreSQL
_runs_store: Dict[str, Dict[str, Any]] = {}

def _store_run(run_id: str, data: Dict[str, Any]) -> None:
    """Store a run in memory."""
    _runs_store[run_id] = data

def _get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a run from memory."""
    return _runs_store.get(run_id)
```

**Impact:**
- ❌ Runs complete successfully but are NEVER persisted
- ❌ Container restart = all run history lost
- ❌ No database query will ever return runs
- ❌ UI will always show 0 runs regardless of execution
- ❌ Traces may have similar issue (needs verification)

**This is SEPARATE from P0-001** - even with correct DATABASE_URL, runs won't persist because the code explicitly uses in-memory storage only.

**Severity:** CRITICAL - Blocks ALL verification scenarios. Data propagation cannot be verified if data is never persisted.

### Remediation Options

1. **Option A**: Configure backend to use local PostgreSQL
   - Change `DATABASE_URL` to `postgresql://nova:novapass@localhost:6432/nova_aos`
   - Restart backend container

2. **Option B**: Migrate data to Neon cloud
   - pg_dump from local → pg_restore to Neon
   - Verify schema compatibility

3. **Option C**: Create fresh test data in Neon
   - Execute verification scenarios to create new data
   - Verify end-to-end propagation

### API Authentication Findings

| Endpoint Type | Required Headers | Status |
|---------------|------------------|--------|
| `/guard/*` | `X-Roles: admin` + `X-API-Key` + `tenant_id` param | WORKS |
| `/ops/*` | `X-Roles: founder` + `X-API-Key` (FOPS key) | PARTIAL |
| `/api/v1/runtime/*` | `X-Roles: founder` | WORKS |
| `/costsim/v2/*` | `X-Roles: founder` | WORKS |

### Non-Critical Observations (Log Only)

| Observation | Location | Notes |
|-------------|----------|-------|
| Stale runs with "running" status | Local DB `runs` table | 57 runs stuck in running state from Dec 6 |
| Empty tenant_id | Local DB `runs` table | Most runs have empty tenant_id |
| Incident has truncated ID | costsim/v2/incidents response | ID shows as "d25cea5a-226" instead of full UUID |

---

## What Claude Must NOT Do

- [ ] Suggest new pages
- [ ] Suggest navigation changes
- [ ] Suggest UI polish
- [ ] Add features
- [ ] Change copy/labels
- [ ] Redesign layouts

Claude verifies **truth propagation only**.

---

## Integration with Founder Beta

| Claude Tests | Founder Beta |
|--------------|--------------|
| Run in parallel | Protected |
| Finds truth gaps | Finds comprehension gaps |
| No scorecard | Scorecard per session |
| System correctness | Human understanding |

Both run. Neither contaminates the other.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Added preflight requirement section, reference to `truth_preflight.sh` (PIN-194) |
| 2025-12-26 | **P0-005 FIXED**: Implemented PostgreSQL persistence in `workers.py`. Run `6a3187aa-9da8-427f-ab71-f9d06673a5b2` persisted successfully to Neon. Health shows `runs_in_db: 1`, `persistence: "postgresql"`. |
| 2025-12-26 | **VERIFICATION RUN 2**: Discovered P0-005 in-memory only run storage (`workers.py:180-192`). Runs execute successfully but NEVER persist to any database. CRITICAL BLOCKER. |
| 2025-12-26 | Executed Option B: Fresh verification run in Neon with tenant `a5-verify-2025-12-26`. Run completed (run_id: `c702fcf0-7401-4166-af84-0908f028488e`) with full artifacts. |
| 2025-12-26 | **VERIFICATION RUN 1**: Discovered P0-001 database mismatch (backend → Neon, test data → local). All tests BLOCKED. |
| 2025-12-26 | Created PIN-191 - Claude System Test Script |
