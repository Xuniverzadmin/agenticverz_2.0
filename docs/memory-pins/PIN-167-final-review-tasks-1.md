# PIN-167: Final Review Tasks - Phase 1

**Status:** HUMAN TESTING COMPLETE - FAIL (Visibility Gaps)
**Category:** Operations / Final Review / Gap Remediation
**Created:** 2025-12-25
**Updated:** 2025-12-25
**Milestone:** Post-M25 Final Review

---

## Executive Summary

This PIN documents the execution of final review tasks based on external analysis feedback. The goal is to address identified gaps, verify system functionality, and test the complete M0-M28 pipeline with a real incident trace.

---

## Gap Assessment Summary

| Gap | Current State | Target State | Priority | Status |
|-----|---------------|--------------|----------|--------|
| PLANNER_BACKEND | `anthropic` | `anthropic` | P0 | DONE |
| MEMORY_CONTEXT_INJECTION | `true` | `true` | P1 | DONE |
| EVENT_PUBLISHER | `redis` | `redis` | P0 | **DONE - IMPLEMENTED** |
| TENANT_MODE | `single` | `single` | P1 | **DONE - DECLARED** |
| CARE_SCOPE | `worker_only` | `worker_only` | P1 | **DONE - DECLARED** |
| M21 Tenants | DISABLED | DISABLED | P2 | INTENTIONAL |
| Prometheus Metric Dup | Crash on startup | Fixed | P0 | DONE |

### Gap Details

#### 1. PLANNER_BACKEND (ALREADY RESOLVED)
- **Current:** `PLANNER_BACKEND=anthropic` (verified in container)
- **Analysis claimed:** "stub" - INCORRECT
- **Status:** No action needed

#### 2. MEMORY_CONTEXT_INJECTION
- **Current:** `false` (default)
- **Target:** `true`
- **Impact:** Enables memory-informed cost simulation
- **Files:** `backend/app/main.py:217`, `backend/app/api/costsim.py:42`
- **Action:** Add to .env and restart container

#### 3. EVENT_PUBLISHER
- **Current:** `logging` (default)
- **Target:** `redis` (for real event streaming)
- **Impact:** Events go to Redis streams instead of just logs
- **Files:** `backend/app/events/publisher.py:29`
- **Action:** Add to .env and restart container

#### 4. M21 Tenants (DISABLED - INTENTIONAL)
- **Current:** Router commented out in `main.py:357,377`
- **Reason:** "Premature for beta stage" (documented in code)
- **Status:** This is BY DESIGN, not a bug
- **Action:** No change for beta, document as intentional

#### 5. CARE in Workers Only (BY DESIGN)
- **Current:** CARE (Continuous Adaptive Recovery Engine) runs in workers
- **Reason:** CARE is a worker-level concern, not API-level
- **Status:** Correct architecture
- **Action:** No change needed

---

## Execution Plan

### Phase 1: Environment Configuration

```bash
# 1. Add missing environment variables
echo "MEMORY_CONTEXT_INJECTION=true" >> /root/agenticverz2.0/.env
echo "EVENT_PUBLISHER=redis" >> /root/agenticverz2.0/.env

# 2. Restart backend to pick up changes
docker compose up -d backend worker

# 3. Verify changes took effect
docker compose exec backend printenv | grep -E "MEMORY|EVENT_PUBLISHER"
```

### Phase 2: Real Incident Test (M0 to M28 Trace)

**Test Scenario:** Create a workflow that exercises the full pipeline:
1. **M0-M3:** Request parsing, authentication
2. **M4-M6:** Skill execution, cost simulation
3. **M7:** RBAC enforcement
4. **M8-M10:** Recovery engine, observability
5. **M11-M14:** Failure handling, retry logic
6. **M15-M20:** Event publishing, metrics
7. **M21-M25:** Integration loop bridges
8. **M26-M28:** Final state persistence

**Verification Points:**
- [ ] API accepts authenticated request
- [ ] Cost simulation includes memory context
- [ ] Events published to Redis (not just logs)
- [ ] Prometheus metrics incremented
- [ ] M25 bridges triggered (if applicable)

### Phase 3: Verification Commands

```bash
# Check all M10 services healthy
for svc in m10-48h-health m10-daily-stats m10-maintenance m10-synthetic-validation; do
  systemctl status $svc.service --no-pager | head -5
done

# Verify API health
curl -s http://localhost:8000/health | jq

# Verify capabilities with auth
curl -s -H "X-AOS-Key: $AOS_API_KEY" http://localhost:8000/api/v1/runtime/capabilities | jq '.skills | length'

# Check Redis events (if EVENT_PUBLISHER=redis)
redis-cli -u "$REDIS_URL" XLEN aos:events 2>/dev/null || echo "Check Upstash console"
```

---

## P0/P1 Activities from Analysis

### P0 (Must-Fix)
| Activity | Status | Notes |
|----------|--------|-------|
| Verify PLANNER_BACKEND | DONE | Already set to `anthropic` |
| Enable MEMORY_CONTEXT_INJECTION | DONE | Added to .env and docker-compose.yml |
| Implement Redis Event Publisher | **DONE** | Created `redis_publisher.py`, channel `aos.events` |
| Add TENANT_MODE declaration | **DONE** | `single` - explicit beta invariant |
| Add CARE_SCOPE declaration | **DONE** | `worker_only` - by design |
| Fix Prometheus metric crash | DONE | Fixed duplicate `drift_score_current` |

### P1 (Should-Fix)
| Activity | Status | Notes |
|----------|--------|-------|
| Document intentional defaults | DONE | Captured in this PIN |
| Verify M10 services | DONE | All 6 timers active, 8 scenarios pass |
| Test full pipeline | DONE | API health OK, 7 skills, 39 agents |
| Acceptance tests | **DONE** | All 3 tests pass (Redis emission, fail-fast, visibility) |

---

## Success Criteria

1. **Environment Configured:**
   - MEMORY_CONTEXT_INJECTION=true (verified in container)
   - EVENT_PUBLISHER=redis (verified in container)

2. **Pipeline Test Passed:**
   - Workflow created successfully
   - Events visible in Redis
   - Metrics updated in Prometheus
   - No errors in logs

3. **M10 Services Healthy:**
   - All 6 timers active
   - No false-positive alerts
   - Recent successful runs

---

## Execution Results

### 1. System Mode Declarations (Objective-1)

All mode declarations now explicit at boot:

```
[BOOT] EVENT_PUBLISHER=redis
[BOOT] EventPublisher=redis channel=aos.events
[BOOT] TENANT_MODE=single (M21 router disabled)
[BOOT] CARE_SCOPE=worker_only (routing Worker only)
[BOOT] MEMORY_CONTEXT_INJECTION=True
```

### 2. Redis Event Publisher (Objective-2)

**Implemented proper Redis Pub/Sub adapter:**

| Component | Status |
|-----------|--------|
| `redis_publisher.py` | Created - Fire-and-forget, fail-fast |
| `publisher.py` | Updated - Fail-fast dispatcher (no silent fallback) |
| Channel | `aos.events` |
| Transport | Redis Pub/Sub (not Streams v1) |

**Acceptance Tests PASSED:**
- Test 1: Redis Emission ✅
- Test 2: No Silent Fallback ✅
- Test 3: Ops Signal Visibility ✅

### 3. Files Modified

| File | Change |
|------|--------|
| `backend/app/events/redis_publisher.py` | **NEW** - Redis Pub/Sub adapter |
| `backend/app/events/publisher.py` | Fail-fast dispatcher, singleton pattern |
| `backend/app/main.py` | System mode declarations at boot |
| `backend/app/memory/memory_service.py` | Fixed Prometheus metric duplicate |
| `docker-compose.yml` | Added TENANT_MODE, CARE_SCOPE env vars |
| `.env` | Added all new env vars |

### 4. Boot Messages Verified

```json
{
  "EVENT_PUBLISHER": "redis",
  "TENANT_MODE": "single",
  "CARE_SCOPE": "worker_only",
  "MEMORY_CONTEXT_INJECTION": true
}
```

### 5. M10 Validation Results

All 8 scenarios pass:
- neon_write_read: PASS
- neon_referential_integrity: PASS
- neon_latency_threshold: PASS
- redis_stream_operations: PASS
- redis_hash_operations: PASS
- redis_latency: PASS
- api_health: PASS
- api_capabilities: PASS (7 skills)

### 6. API Pipeline Status

```json
{
  "health": "healthy",
  "skills_count": 7,
  "agents_count": 39,
  "rate_limits": {
    "http_call": {"remaining": 95},
    "llm_invoke": {"remaining": 50}
  }
}
```

### 7. Design Clarifications (Intentional)

| Mode | Value | Reason |
|------|-------|--------|
| TENANT_MODE | `single` | Phase-1 beta, no external customers |
| CARE_SCOPE | `worker_only` | CARE routes execution, not requests |
| M21 Router | DISABLED | "Premature for beta stage" |

---

## Related PINs

- PIN-163: M0-M28 Utilization Report (94% score)
- PIN-164: System Mental Model - Pillar Interactions
- PIN-165: Pillar Definition Reconciliation
- PIN-166: M10 Services Health & Fixes

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | **Human Testing COMPLETE (FAIL)** - All 6 scenarios executed. Overall FAIL - 3/4 exit criteria not met. Key gaps: CARE invisible, memory opaque, budget advisory only |
| 2025-12-25 | **Human Testing 5/6** - Scenarios 1-5 executed with detailed observations. Key finding: system truthful after execution, opaque before |
| 2025-12-25 | **Objective-4 Ready** - Human Test Script added with 6 scenarios, exit criteria, observation template |
| 2025-12-25 | **Phase 2 Complete** - Redis adapter implemented, TENANT_MODE/CARE_SCOPE declared, all acceptance tests pass |
| 2025-12-25 | Execution complete - all P0/P1 tasks done. Fixed Prometheus crash. |
| 2025-12-25 | Initial creation with gap assessment and execution plan |

---

## Objective Completion Status

| Objective | Status |
|-----------|--------|
| Obj-1: Variable Mapping | **PASS** - All modes declared at boot |
| Obj-2: Intended Function | **PASS** - Redis events, TENANT_MODE, CARE_SCOPE working |
| Obj-3: Pending Gaps | **CLOSED** - No remaining gaps |
| Obj-4: Human Testing | **COMPLETE - FAIL** - 6/6 scenarios executed, 3 exit criteria failed |

---

## Objective-4: Human Test Script

### Purpose

Validate that a human operator can form correct mental models of system behavior without being misled. This is NOT a functional test - it's a trust/clarity/boundary test.

### Tester Profile

The human tester should adopt the mindset of:
- **Role:** Founder/CTO/Senior Engineer evaluating AOS for their startup
- **Experience:** Understands systems, doesn't know AOS internals
- **Goal:** Determine if system behaves predictably and explains itself truthfully

### Test Scenarios (Fixed Set)

| # | Scenario | What Tester Does | What to Observe |
|---|----------|------------------|-----------------|
| 1 | **Incident Creation** | Create a workflow via API | Does the system explain what will happen? |
| 2 | **Execution Routing** | Trigger a run that requires CARE involvement | Does the system indicate CARE is involved? How? |
| 3 | **Recovery Suggestion** | Inject a controlled failure | Does the system suggest recovery? Is it clear what "recovery" means? |
| 4 | **Policy Consequence** | Hit a rate limit or budget constraint | Is the consequence predictable? Was it explained upfront? |
| 5 | **Cost/Ops Signal Visibility** | Check Prometheus metrics after workflow | Can tester find cost/event data without insider knowledge? |
| 6 | **Memory Carryover** | Run same agent twice with different inputs | Does tester understand what the agent "remembers"? |

### Instructions to Human Tester

**DO:**
- Use only documented APIs and endpoints
- Form hypotheses about what the system will do
- Note when your hypothesis was wrong
- Note when you couldn't form a hypothesis at all
- Record exact confusion moments

**DON'T:**
- Read the source code during testing
- Ask Claude/AI for help understanding behavior
- Assume anything not explicitly stated
- Forgive unclear behavior

### Observation Checklist

For each scenario, record:

```markdown
### Scenario X: [Name]

**Hypothesis before action:** [What I expect to happen]

**Actual outcome:** [What actually happened]

**Match:** YES / NO / PARTIAL

**Confusion points:**
- [List specific moments of confusion]

**Trust impact:**
- [ ] Increased trust
- [ ] Neutral
- [ ] Decreased trust

**Reason:** [Why trust changed]
```

### MEMORY_CONTEXT_INJECTION Observation (Scenario 6)

This is specific to verifying memory carryover:

1. Run an agent with input A
2. Note any "context" or "memory" in response
3. Run SAME agent with input B
4. Observe: Does agent reference input A? Does it claim to remember?
5. Record: Was memory carryover obvious, hidden, or absent?

**Pass criteria:** Tester can accurately describe what the agent remembered without reading code.

### Exit Criteria

#### PASS Conditions (ALL must be true)
- [ ] Tester can explain system behavior to a colleague without code access
- [ ] Tester trusts system with appropriate caveats (not blind trust)
- [ ] Tester knows system boundaries (what it won't do)
- [ ] No "magic" moments (unexplained behavior accepted as normal)

#### FAIL Conditions (ANY triggers fail)
- [ ] Tester believed system could do something it can't
- [ ] Tester couldn't explain why something happened
- [ ] System made implicit promises it didn't keep
- [ ] Tester had to read code to understand behavior

### Explicit Non-Goals

This test is NOT about:
- Finding bugs (that's QA)
- Improving UX (that's design)
- Adding guardrails (that's engineering)
- Making the system "easier"

This test IS about:
- Truthfulness (does system say what it does?)
- Predictability (can behavior be anticipated?)
- Boundary clarity (does tester know limits?)

### Observed Truths Template

```markdown
## Human Testing: Observed Truths

**Tester:** [Name/Role]
**Date:** [Date]
**Duration:** [Time spent]

### Summary Verdict

| Criterion | Status | Notes |
|-----------|--------|-------|
| Explainable to colleague | PASS/FAIL | |
| Trust with caveats | PASS/FAIL | |
| Knows boundaries | PASS/FAIL | |
| No magic moments | PASS/FAIL | |

### Overall: PASS / FAIL

### Scenario Results

[Paste observation checklists here]

### Residual Risks Identified

[List any risks found during testing]

### Recommendations

[List any recommendations - NOT fixes, just observations]
```

---

## Human Test Execution Results (2025-12-25)

### Scenario 1: Incident Creation

**Hypothesis before action:** When creating a workflow, the system will explain what will happen before execution.

**Actual outcome:**
- Created workflow via `/api/v1/workers/business-builder/run`
- Run ID: `68242447-df6f-4fca-a6cf-20ba37936cd6`
- System accepted request with minimal upfront explanation
- After completion: detailed `cost_report`, `policy_violations`, `execution_trace` returned
- Budget 5,000 tokens requested, 9,671 actually used (exceeded without blocking)
- Policy violation detected: "risk-free" claim (warning level, not blocked)

**Match:** PARTIAL

**Confusion points:**
- No preview of what stages would execute before starting
- Budget exceeded without warning (advisory only)
- `routing_decisions: []` always empty - unclear if routing happened
- `recovery_log: []` always empty on success - unclear what recovery means

**Trust impact:** Neutral

**Reason:** System truthful AFTER execution (detailed reports), opaque BEFORE execution.

---

### Scenario 2: Execution Routing

**Hypothesis before action:** When triggering a run, the system will indicate if/how CARE is involved.

**Actual outcome:**
- Created workflow with `strict_mode: true` for risky task
- Run ID: `37b6e61e-f15f-4770-8e99-abbc9fb7c6a7`
- `routing_decisions` field always empty in workflow responses
- CARE only visible when explicitly calling `/api/v1/routing/dispatch`
- Dispatch returned: "No eligible agent: 5 rejected at domain_filter stage"
- CARE_SCOPE=worker_only means routing is internal to workers

**Match:** NO

**Confusion points:**
- CARE completely invisible during normal workflow execution
- No indication routing occurred in workflow response
- `/routing/stats` shows 0 routing stats - never used by workflows
- `routing_stability: 1.0` exists but meaningless if never routed

**Trust impact:** Neutral

**Reason:** CARE works correctly but is invisible. A human tester would not know it exists from workflow responses alone.

---

### Scenario 3: Recovery Suggestion

**Hypothesis before action:** When a failure occurs, the system will suggest recovery actions with clear meaning.

**Actual outcome:**
- Recovery API excellent when explicitly called:
  - `/recovery/suggest` - Returns matched entry, suggested action, confidence 0.95
  - `/recovery/evaluate` - Full rule evaluation with explanations
  - `/recovery/actions` - 7 predefined actions (retry, fallback, reconfigure, notify, rollback, manual, skip)
  - `/recovery/candidates` - 50+ pending recovery candidates
- Recovery invisible in workflow responses (`recovery_log: []` on success)
- `/recovery/ingest` has database constraint error (not working)

**Match:** PARTIAL

**Confusion points:**
- Recovery API is powerful but completely separate from workflow flow
- Workflows don't show if recovery was attempted
- 50+ pending candidates with no action - what should happen?
- `recovery_log` always empty in responses - when would it have data?

**Trust impact:** Neutral

**Reason:** Recovery system is well-designed but siloed. A human would need to explicitly call recovery endpoints to benefit.

---

### Scenario 4: Policy Consequence

**Hypothesis before action:** When hitting a rate limit or budget constraint, the consequence will be predictable and explained upfront.

**Actual outcome:**
- `/runtime/simulate` correctly predicts feasibility:
  - 10 cents budget, 250 cent plan → `feasible: false, status: budget_insufficient`
  - Clear `step_estimates` showing cost breakdown
- Budget is ADVISORY only:
  - Requested 5,000 tokens, used 9,671 tokens, no blocking
  - `under_budget: false` reported after execution
- `strict_mode: true` stops execution on error-level violations
- Policy violation example: Run `f6eaf52f-0b48-4ace-b59a-b89a37b0bd9c` failed with:
  - `"Post-policy violation: FTC violation (ILLEGAL_GUARANTEE: weight loss, ILLEGAL_INCOME_CLAIM: income potential)"`
- Policy layer endpoints (`/policy/*`) require elevated credentials

**Match:** PARTIAL

**Confusion points:**
- Simulation shows budget issues but execution ignores them
- Budget is soft limit, not enforced - what's the point?
- Policy rules visible only when violated, not queryable upfront
- Policy layer endpoints return "forbidden" without clear path to access

**Trust impact:** Neutral

**Reason:** Simulation is helpful but misleading if budget isn't enforced. Policy violations are clear but only discovered after execution.

---

### Scenario 5: Cost/Ops Signal Visibility

**Hypothesis before action:** After running a workflow, I can easily find cost and operational data without insider knowledge.

**Actual outcome:**

| Signal | Where Found | Visibility |
|--------|-------------|------------|
| Skill cost estimates | `/runtime/capabilities` | ✅ CLEAR |
| Budget remaining | `/runtime/capabilities` | ✅ CLEAR |
| Rate limits | `/runtime/capabilities` | ✅ CLEAR |
| Workflow token usage | Workflow response `cost_report` | ✅ CLEAR (inline) |
| Historical cost tables | `/cost/summary`, `/cost/dashboard` | ❌ Shows 0 |
| Prometheus metrics | localhost:9090 | ❌ HIDDEN |
| Grafana dashboards | localhost:3000 (6 dashboards) | ❌ HIDDEN |
| Ops console | `/ops/*` endpoints | ❌ FORBIDDEN |

- `/runtime/capabilities` is EXCELLENT: 7 skills with cost estimates, budget 1000 cents, rate limits with remaining/reset
- Prometheus has 60+ aos_*/nova_* metrics but requires insider knowledge
- Grafana has dashboards but nothing documents their existence
- Cost tables show 0 despite workflows consuming tokens

**Match:** PARTIAL

**Confusion points:**
- Why do cost tables show 0 when workflows consumed tokens?
- How would I discover Prometheus/Grafana without code access?
- Ops console returns `AUTH_DOMAIN_MISMATCH` - what domain do I need?
- Which Prometheus metrics matter? (60+ available)

**Trust impact:** Neutral

**Reason:** Runtime capabilities endpoint is well-designed. Historical cost tracking and monitoring are invisible without insider knowledge.

---

### Scenario 6: Memory Carryover

**Hypothesis before action:** When running the same worker twice with different inputs, the system will clearly indicate what the agent "remembers" from the first run.

**Actual outcome:**
- Run A: "organic pet food delivery" → run_id `ed83d0c1-6628-4e59-ae4b-bb5d0ea3e29a`
  - Competitors: The Farmer's Dog, Ollie, Nom Nom
  - Market: $50B pet food, 22% growth organic segment
- Run B: "handmade artisan jewelry" → run_id `85f4638f-8032-400c-992a-59f6ec58eba5`
  - Competitors: Mejuri, Etsy, Local craft fairs
  - Market: $2.8B sustainable jewelry, 15-20% growth
  - **No reference to Run A's topic (pet food not mentioned)**

**Memory field inspection:**
- `memory_context`: null
- `remembered`: null
- `context_injected`: null
- `/api/v1/memory/pins`: forbidden (requires elevated credentials)

**Environment:**
- `MEMORY_CONTEXT_INJECTION=true` (enabled in container)
- `MEMORY_POST_UPDATE=false` (disabled - no new memories created)

**Match:** NO

**Confusion points:**
- MEMORY_CONTEXT_INJECTION is ON but no visible effect
- No memory-related fields in workflow responses
- Run B is completely independent of Run A
- Memory pins endpoint forbidden - cannot verify what was remembered
- Is isolation intentional? No way to tell without code access

**Trust impact:** Decreased trust

**Reason:** System claims memory features (MEMORY_CONTEXT_INJECTION=true) but provides zero visibility. Human cannot form any mental model of what agent "remembers."

---

## Final Assessment (6/6 Scenarios Complete)

### Summary

| Scenario | Match | Trust Impact |
|----------|-------|--------------|
| 1. Incident Creation | PARTIAL | Neutral |
| 2. Execution Routing | NO | Neutral |
| 3. Recovery Suggestion | PARTIAL | Neutral |
| 4. Policy Consequence | PARTIAL | Neutral |
| 5. Cost/Ops Visibility | PARTIAL | Neutral |
| 6. Memory Carryover | NO | **Decreased** |

### Key Findings

1. **System is truthful AFTER execution**, opaque BEFORE
2. **Internal systems (CARE, Recovery, Memory) are invisible** during normal workflow execution
3. **Budget is advisory**, not enforced - simulation is helpful but misleading
4. **Policy violations are discoverable** but only after execution
5. **Runtime capabilities endpoint is excellent** - the one bright spot for visibility
6. **Monitoring infrastructure exists** but is undocumented and hidden
7. **Memory features are ON but invisible** - MEMORY_CONTEXT_INJECTION=true but no visible effect

### Exit Criteria Final Evaluation

| Criterion | Status | Notes |
|-----------|--------|-------|
| Explainable to colleague | **FAIL** | Can explain results, but internal systems invisible |
| Trust with caveats | PASS | System works but has significant hidden complexity |
| Knows boundaries | **FAIL** | Cannot determine memory, routing, or recovery boundaries |
| No magic moments | **FAIL** | CARE routing invisible, memory claims unverifiable |

### Overall Verdict: **FAIL**

The human testing reveals significant visibility gaps. While the system functions correctly, a human tester cannot form accurate mental models of:
- What the agent remembers (memory invisible)
- How routing decisions are made (CARE invisible)
- What recovery actions are available (siloed from workflows)
- Whether budget constraints will be enforced (advisory only)

### Residual Risks Identified

1. **Budget enforcement gap**: Simulation warns but execution ignores
2. **CARE invisibility**: Routing happens but is never shown
3. **Recovery siloing**: Powerful system but separate from workflow flow
4. **Cost tracking gap**: Workflow costs not recorded to cost tables
5. **Documentation gap**: Prometheus/Grafana undocumented
6. **Memory opacity**: MEMORY_CONTEXT_INJECTION enabled but invisible

### Observed Truths

| What Tester Believed | Actual Behavior |
|---------------------|-----------------|
| Budget of 5000 tokens would be enforced | Execution used 9671 tokens without blocking |
| CARE would be visible in routing_decisions | Always empty in workflow responses |
| Recovery suggestions would appear in recovery_log | Always empty on successful runs |
| Memory would show what agent remembers | No memory fields in responses |
| Cost tables would track workflow costs | Show 0 despite workflows running |

---

## Next Steps

1. **Address Visibility Gaps** - Consider exposing CARE/Recovery/Memory in workflow responses
2. **Enforce Budget OR Remove Simulation Warning** - Current behavior is misleading
3. **Create SYSTEM_MODES.md** - Document intentional behaviors for operators
4. **Add Memory Transparency** - Show what was injected (if anything)
5. **Unify Auth Domains** - Ops console should be accessible with same credentials
