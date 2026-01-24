# PIN-192: Phase A.5 — Founder-Driven Verification

**Status:** ACTIVE
**Category:** Verification / Testing / Pre-Beta
**Created:** 2025-12-26
**Milestone:** Runtime v1 Pre-Beta
**Related:** PIN-188 (Beta Signals), PIN-189 (Phase A Closure), PIN-191 (Claude Tests)

---

## What This Phase Is

> **Phase A.5 — Founder-Driven Verification**
> System truth verification by founder, before inviting others.

This is NOT:
- ❌ Founder Beta (behavioral signal from others)
- ❌ Customer Beta (misuse + scale testing)
- ❌ Product validation (desirability)

This IS:
- ✅ Mechanical correctness
- ✅ Data propagation audit
- ✅ Truth consistency proof
- ✅ Pre-invitation confidence

---

## Rules (LOCKED)

### Rule 1: No UI Changes Except P0 Truth Bugs

**May fix:**
- Missing data
- Incorrect links
- Wrong badges
- Broken propagation

**May NOT add:**
- New pages
- New O4 depth
- New explanations
- New workflows

### Rule 2: No Scorecard Interpretation Yet

- Fill scorecards → Yes
- Decide O4 unlock → No
- Decide exit criteria → No
- Just notes for now

### Rule 3: Beta Banner Stays ON

Protection against self-deception.

---

# Part 1: Founder-as-Customer Verification Checklist

## 1.1 URL Verification (All Four Subdomains)

> Verify all four subdomains resolve and behave correctly.

| Subdomain | URL | Loads? | Auth Works? | Correct Content? |
|-----------|-----|--------|-------------|------------------|
| Console | `console.agenticverz.com/guard` | [ ] | [ ] | [ ] |
| FOPS | `fops.agenticverz.com/ops` | [ ] | [ ] | [ ] |
| Preflight-Console | `preflight-console.agenticverz.com/guard` | [ ] | [ ] | [ ] |
| Preflight-FOPS | `preflight-fops.agenticverz.com/ops` | [ ] | [ ] | [ ] |

**If subdomains not deployed yet, use existing routes:**

| Console | URL | Loads? | Auth Works? | Correct Content? |
|---------|-----|--------|-------------|------------------|
| Guard | `agenticverz.com/console/guard` | [ ] | [ ] | [ ] |
| Ops | `agenticverz.com/console/ops` | [ ] | [ ] | [ ] |
| Timeline | `agenticverz.com/console/fdr/timeline` | [ ] | [ ] | [ ] |
| Controls | `agenticverz.com/console/fdr/controls` | [ ] | [ ] | [ ] |
| Incidents | `agenticverz.com/console/guard/incidents` | [ ] | [ ] | [ ] |
| Runs | `agenticverz.com/console/guard/runs` | [ ] | [ ] | [ ] |
| Traces | `agenticverz.com/console/traces` | [ ] | [ ] | [ ] |

---

## 1.2 Scenario A: Cost Violation

**Setup:**
1. Configure advisory budget (low threshold)
2. Trigger a run that exceeds budget

**Verification:**

| Check | Location | Expected | Pass? |
|-------|----------|----------|-------|
| Budget mode shown | Guard > Runs > Detail > PRE-RUN | "ADVISORY" badge | [ ] |
| Estimated cost shown | Guard > Runs > Detail > COST | Number visible | [ ] |
| Actual cost shown | Guard > Runs > Detail > COST | Number visible | [ ] |
| Delta calculated | Guard > Runs > Detail > COST | +/- difference shown | [ ] |
| Warning for advisory | Guard > Limits | Warning indicator | [ ] |
| Decision recorded | Founder Timeline | Cost decision entry | [ ] |

**Notes:**
```
_______________________________________________________
```

---

## 1.3 Scenario B: Policy Violation

**Setup:**
1. Create/enable a strict policy
2. Trigger a run that violates it

**Verification:**

| Check | Location | Expected | Pass? |
|-------|----------|----------|-------|
| Constraint shown | Guard > Runs > Detail > CONSTRAINTS | Policy ✗ | [ ] |
| Policy name visible | Guard > Runs > Detail > CONSTRAINTS | Policy ID/name | [ ] |
| Policy linked | Guard > Runs > Detail > CONSTRAINTS | Clickable link | [ ] |
| Incident created | Guard > Incidents | Policy violation entry | [ ] |
| Decision recorded | Founder Timeline | policy_blocked entry | [ ] |

**Notes:**
```
_______________________________________________________
```

---

## 1.4 Scenario C: Incident Creation (LLM Error/Timeout)

**Setup:**
1. Force an LLM timeout or error
2. Or trigger any incident-worthy event

**Verification:**

| Check | Location | Expected | Pass? |
|-------|----------|----------|-------|
| Incident appears | Guard > Incidents | New incident in list | [ ] |
| Incident has ID | Guard > Incidents | INC-xxx format | [ ] |
| Click opens detail | Incidents > Detail | O3 page loads | [ ] |
| Root cause shown | Incidents > Detail | Reason visible | [ ] |
| Run linked | Incidents > Detail | "View Run" works | [ ] |
| Trace linked | Incidents > Detail or Run | "View Trace" works | [ ] |
| Breadcrumb correct | Incidents > Detail | "Incidents > INC-xxx" | [ ] |
| Decision recorded | Founder Timeline | Incident decision entry | [ ] |

**Notes:**
```
_______________________________________________________
```

---

## 1.5 Scenario D: Trace Integrity

**Setup:**
1. Create a multi-step run
2. Optionally cause a retry or step failure

**Verification:**

| Check | Location | Expected | Pass? |
|-------|----------|----------|-------|
| Trace exists | Traces list | Entry appears | [ ] |
| Click opens detail | Traces > Detail | O3 page loads | [ ] |
| Status correct | Traces > Detail | COMPLETE/PARTIAL/ERROR | [ ] |
| Hash shown | Traces > Detail | Root hash visible | [ ] |
| Verification status | Traces > Detail | VERIFIED/UNVERIFIED | [ ] |
| Step count correct | Traces > Detail | Matches actual steps | [ ] |
| No raw JSON | Traces > Detail | Values truncated | [ ] |
| Run linked | Traces > Detail | "View Run" works | [ ] |
| Breadcrumb correct | Traces > Detail | "Traces > TRACE-xxx" | [ ] |

**Notes:**
```
_______________________________________________________
```

---

## 1.6 Scenario E: Memory Injection

**Setup:**
1. Create a run with memory context

**Verification:**

| Check | Location | Expected | Pass? |
|-------|----------|----------|-------|
| Memory shown | Guard > Runs > Detail > PRE-RUN | "Memory Injected: N" | [ ] |
| Count correct | Guard > Runs > Detail > PRE-RUN | Matches input | [ ] |
| Decision recorded | Founder Timeline | Memory injection entry | [ ] |

**Notes:**
```
_______________________________________________________
```

---

## 1.7 Cross-Entity Navigation

**Verification:**

| Navigation | Action | Works? |
|------------|--------|--------|
| Incidents list → Detail | Click incident row | [ ] |
| Incident → Run | Click "View Run" | [ ] |
| Run → Trace | Click "View Trace" | [ ] |
| Trace → Run | Click "View Run" | [ ] |
| Any O3 → O2 list | Click breadcrumb | [ ] |
| Cross-entity | Breadcrumb resets | [ ] |

---

## 1.8 Data Propagation Audit

For EACH scenario above, verify the full chain:

| Layer | Question | Scenario A | Scenario B | Scenario C | Scenario D |
|-------|----------|------------|------------|------------|------------|
| Backend | Event exists in DB? | [ ] | [ ] | [ ] | [ ] |
| API | Returns correctly? | [ ] | [ ] | [ ] | [ ] |
| UI O1 | Counted on dashboard? | [ ] | [ ] | [ ] | [ ] |
| UI O2 | Listed in table? | [ ] | [ ] | [ ] | [ ] |
| UI O3 | Explained in detail? | [ ] | [ ] | [ ] | [ ] |
| Cross-links | Land correctly? | [ ] | [ ] | [ ] | [ ] |

**If ANY "No" → P0 truth bug. Fix immediately.**

---

# Part 2: Acceptance Criteria Before Inviting Others

## Minimum Bar (All Must Pass)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | All URL routes load without error | [ ] |
| 2 | Auth works on all pages | [ ] |
| 3 | Beta banner visible everywhere | [ ] |
| 4 | Scenario A (cost) passes all checks | [ ] |
| 5 | Scenario B (policy) passes all checks | [ ] |
| 6 | Scenario C (incident) passes all checks | [ ] |
| 7 | Scenario D (trace) passes all checks | [ ] |
| 8 | Cross-entity navigation works | [ ] |
| 9 | No raw JSON visible anywhere | [ ] |
| 10 | Breadcrumbs correct on all O3 pages | [ ] |

**If ANY fails: Do NOT invite others. Fix first.**

---

## Invitation Readiness Declaration

Before inviting anyone, sign this:

```
I, _________________, confirm that:

[ ] All 10 acceptance criteria above PASS
[ ] No known P0 truth bugs exist
[ ] Beta banner is visible on all pages
[ ] I will NOT explain the system verbally during sessions
[ ] I will only observe and take notes
[ ] Scorecards will be filled, not interpreted

Date: _______________
```

---

# Part 3: Transition from A.5 → Official Beta

## A.5 Ends When

| Condition | Met? |
|-----------|------|
| All acceptance criteria pass | [ ] |
| At least 2 other people invited | [ ] |
| First external session completed | [ ] |
| First scorecard filled (by observer, not founder) | [ ] |

---

## Official Beta Starts When

The moment you:

1. Have **at least 2 other people** using independently
2. **Stop explaining verbally** (silence during sessions)
3. **Only observe** (no guidance, no hints)
4. **Scorecards reflect their confusion**, not yours

---

## Transition Marker

When ready, update this PIN:

```
TRANSITION RECORD
================
Phase A.5 End Date: _______________
Official Beta Start Date: _______________
First External Users: _______________, _______________
First Scorecard Session: _______________

Signed: _______________
```

---

## What Changes at Transition

| Aspect | Phase A.5 | Official Beta |
|--------|-----------|---------------|
| Who uses it | Founder only | Founder + others |
| Verbal explanation | Allowed (to self) | Forbidden |
| Scorecard authority | Notes only | Decides O4/exit |
| Fix velocity | Immediate | Only P0 truth bugs |
| Signal source | Self-verification | External behavior |

---

## Post-Transition Rules

Once in Official Beta:

1. **PIN-188 scorecards become authoritative**
2. **7-day rule applies** (for exit criteria)
3. **O4 unlock requires valid pull signal**
4. **No UI changes without scorecard signal**

---

# Summary

| Phase | Purpose | Current |
|-------|---------|---------|
| A | UI structure law | ✅ COMPLETE |
| A.5 | Founder verification | 🎯 ACTIVE |
| B | Subdomain rollout | 📋 DESIGNED |
| Beta | External signal collection | ⏳ WAITING |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | **S2 FAILED**: Run 3 (S2 attempt) executed but cost_cents=NULL, cost_records=0. P0-006 identified. "PARTIAL" corrected to FAILED. Phase A.5 blocked until cost wiring complete. |
| 2025-12-26 | **S1 PASSED**: P0-005 RESOLVED. Run `6a3187aa-9da8-427f-ab71-f9d06673a5b2` executed and **persisted to Neon PostgreSQL**. S1 scenario ACCEPTED. |
| 2025-12-26 | **VERIFICATION RUN 2**: BLOCKED by P0-005 (in-memory only storage). Option B executed, run completed with artifacts, but 0 rows persisted to Neon. Code at `workers.py:180-192` uses in-memory dict, never PostgreSQL. |
| 2025-12-26 | **VERIFICATION RUN 1**: BLOCKED by P0-001 (database mismatch). Backend connects to Neon cloud (0 data) while test data is in local PostgreSQL. See PIN-191 for full findings. |
| 2025-12-26 | Created PIN-192 - Phase A.5 Founder-Driven Verification |

---

## Verification Run 1 Results (2025-12-26)

### Status: BLOCKED

**Blocker**: P0-001 - Database mismatch between backend (Neon cloud) and test data (local PostgreSQL)

### API Endpoint Status (Empty State Verification)

| Endpoint | Status | Response |
|----------|--------|----------|
| `/guard/status` | WORKS | Returns empty incident state |
| `/guard/incidents` | WORKS | Returns empty list |
| `/guard/costs/summary` | WORKS | Returns zero spend |
| `/guard/keys` | WORKS | Returns empty list |
| `/ops/pulse` | WORKS | Returns healthy state |
| `/ops/infra` | WORKS | Returns infra metrics |
| `/ops/revenue` | WORKS | Returns zero revenue |
| `/ops/customers` | WORKS | Returns empty list |
| `/ops/incidents` | ERROR | Internal Server Error |
| `/api/v1/runtime/traces` | WORKS | Returns empty (0 traces) |
| `/costsim/v2/incidents` | WORKS | Returns 1 incident |

### Scenarios Blocked

| Scenario | Status | Reason |
|----------|--------|--------|
| S1: Clean Run | BLOCKED | No runs in target DB |
| S2: Cost Advisory Overrun | BLOCKED | No cost data |
| S3: Policy Violation | BLOCKED | No policy events |
| S4: LLM Failure/Timeout | BLOCKED | No failure events |
| S5: Memory Injection | BLOCKED | No memory injection data |
| S6: Trace Integrity | BLOCKED | No traces in target DB |

### Next Steps

1. ~~**Resolve P0-001**: Align database configuration~~ → RESOLVED via Option B
2. **NEW BLOCKER - P0-005**: Runs stored in-memory only, never persisted to PostgreSQL
3. **Remediate P0-005**: Implement database persistence in `workers.py`
4. **Re-run verification**: Execute all scenarios with persistence fixed
5. **Complete checklist**: Fill in Section 1.1-1.8

---

## Verification Run 2 Results (2025-12-26)

### Status: BLOCKED by P0-005

**Executed Option B**: Created fresh verification run with tenant `a5-verify-2025-12-26`

| Aspect | Result |
|--------|--------|
| Run ID | `c702fcf0-7401-4166-af84-0908f028488e` |
| Status | Completed (queued → success artifacts returned) |
| Artifacts | Market report, landing page HTML/CSS, positioning |
| Neon DB after run | 0 rows in any table |

### P0-005: In-Memory Only Run Storage

**Root Cause** (`backend/app/api/workers.py:180-192`):

```python
# Simple in-memory storage for runs
# In production, this would be persisted to PostgreSQL
_runs_store: Dict[str, Dict[str, Any]] = {}
```

**Impact:**
- Runs execute successfully (API returns artifacts)
- BUT runs are NEVER persisted to PostgreSQL
- Container restart = all run history lost
- UI will always show 0 runs regardless of execution
- Cannot verify data propagation if no data is persisted

**This is SEPARATE from P0-001** - database configuration was not the issue; the code itself never persists runs.

### Scenarios Status Update

| Scenario | Status | Blocker |
|----------|--------|---------|
| S1: Clean Run | ✅ PASSED | P0-005 RESOLVED - Run persisted to Neon |
| S2: Cost Advisory Overrun | ❌ FAILED | P0-006 - Cost not wired to worker execution |
| S3: Policy Violation | BLOCKED | S2 must pass first |
| S4: LLM Failure/Timeout | BLOCKED | S2 must pass first |
| S5: Memory Injection | BLOCKED | S2 must pass first |
| S6: Trace Integrity | BLOCKED | S2 must pass first |

---

## Verification Run 3 Results (2025-12-26) — S2 Attempt

### Status: FAILED (INVALID ATTEMPT)

**Executed S2 scenario**: Cost Advisory Overrun test

| Aspect | Result |
|--------|--------|
| Run ID | `3fe67469-44d8-4be6-8bbf-b4f14603d078` |
| Tenant | `demo-tenant` |
| Budget | 50c daily, hard_limit=false |
| Tokens | 9634 |
| cost_cents | **NULL** (not recorded) |
| cost_records | **0 rows** |

### P0-006: Cost Signal Not Wired to Worker Execution

**Root Cause**: Cost accounting is not part of the worker execution lifecycle.

Current execution graph:
```
Worker Run → Artifacts → Classification
```

Required execution graph:
```
Worker Run → Resource Consumption → Cost Computation → Persistence → Classification
```

**Impact:**
- No cost signal is ever produced
- Classification operates on **absence of data**, not low data
- System is testing "absence of cost", not "cost advisory"
- This is a false negative, not a success

### Why "PARTIAL" Was Incorrect

Initially marked as PARTIAL, but by PIN-193/PIN-194 rules:
- AC-1 (Cost Persistence) = BLOCKED
- That alone is a **hard FAIL**
- Therefore S2 is NOT accepted
- Therefore Phase A.5 may NOT proceed to S3

**"PARTIAL" is not a valid gate status.**

### Next Steps

1. Wire cost capture into worker execution (compute cost, persist with run)
2. Add non-NULL cost invariant enforcement
3. Re-run S2 from scratch
4. Accept S2 only when AC-1 passes
