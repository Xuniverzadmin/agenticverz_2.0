# Wireframe Gap Analysis: Contracts, Test Scenarios & Feature Set

**Generated:** 2025-12-26
**Context:** Runtime v1 Feature Freeze (PIN-183)
**Sources:** PIN-170 Contracts, PIN-167 Human Testing, TR-004 Test Matrix, System Truth Ledger

---

## Executive Summary

| Category | Gaps Found | Severity |
|----------|------------|----------|
| Contract Surfacing | 6 | CRITICAL |
| Test Scenario Support | 4 | HIGH |
| Feature Visibility | 5 | MEDIUM |
| **TOTAL** | **15** | - |

---

## 1. Contract Obligation Gaps

The four contracts (PRE-RUN, CONSTRAINT, DECISION, OUTCOME) define what MUST be visible. Comparing to wireframes:

### 1.1 PRE-RUN Contract Gaps

| Obligation | Required Field | GPT Wireframe | Our Codebase | GAP? |
|------------|---------------|---------------|--------------|------|
| stages | List of stages before execution | Not shown | Not surfaced | **YES** |
| skill_sequence | Skills to be invoked | Not shown | Not surfaced | **YES** |
| estimated_tokens | Token estimate before start | CustomerLimitsPage (budget only) | Partial | **PARTIAL** |
| memory_injection_enabled | Memory injection state | Not shown | Not surfaced | **YES** |
| memory_context_summary | What will be injected | Not shown | Not surfaced | **YES** |
| applicable_policies | Policies that will apply | Not shown | Not surfaced | **YES** |

**Missing Page:** There is no "Pre-Run Preview" page that shows what WILL happen before execution starts.

**Recommendation:**
```
CustomerRunsPage should show:
├── Before starting: "This run will execute: Stage1 → Stage2 → Stage3"
├── Estimated cost: "~500 tokens ($0.015)"
├── Memory state: "Will inject 3 context items from prior runs"
└── Policies: "rate_limit, budget_soft, content_moderation"
```

---

### 1.2 CONSTRAINT Contract Gaps

| Obligation | Required Field | GPT Wireframe | Our Codebase | GAP? |
|------------|---------------|---------------|--------------|------|
| budget_enforcement | Hard vs Soft | CustomerLimitsPage | Shows budget, not mode | **PARTIAL** |
| rate_limits | Per-minute/per-day | CustomerLimitsPage | ✓ Implemented | NO |
| budget_mode | advisory/enforced | Not shown | Not surfaced | **YES** |
| simulation-execution parity | What simulation says = what happens | Not shown | Not enforced | **YES** |

**PIN-167 Finding:** "Budget 5,000 tokens requested, 9,671 actually used (exceeded without blocking)"

**Missing UI Element:**
```
CustomerLimitsPage should show:
├── Budget Mode: "ADVISORY" or "ENFORCED"
├── Current mode should be VISIBLE to customer
└── Warning: "Budget limits are advisory only - execution may exceed"
```

---

### 1.3 DECISION Contract Gaps (Founder-Only)

| Obligation | Required Field | GPT Wireframe (fops) | Our Codebase | GAP? |
|------------|---------------|---------------------|--------------|------|
| routing_occurred | Was CARE used? | FounderPulsePage (signals) | FounderTimelinePage | NO |
| routing_decisions | Agents considered/rejected | Not explicitly shown | Not surfaced | **YES** |
| recovery_evaluated | Was recovery tried? | FounderOpsConsole (at-risk) | Not explicit | **PARTIAL** |
| recovery_action | What action was taken? | Not shown | RecoveryPage (candidates) | **PARTIAL** |
| memory_queried | Was memory accessed? | Not shown | Not surfaced | **YES** |
| decision_source | human/system/hybrid | Not shown | FounderTimelinePage | NO |
| decision_trigger | explicit/autonomous/reactive | Not shown | FounderTimelinePage | NO |

**PIN-167 Finding:** "CARE completely invisible during normal workflow execution"

**Missing UI Element:**
```
FounderTimelinePage should show (per decision):
├── routing_method: "CARE" | "direct" | "fallback"
├── agents_considered: ["agent-1", "agent-2", "agent-3"]
├── agents_rejected: [{agent: "agent-2", reason: "domain_filter"}]
├── memory_queried: true | false
└── memory_injected: ["pin-123", "run-456"]
```

---

### 1.4 OUTCOME Contract Gaps

| Obligation | Required Field | GPT Wireframe | Our Codebase | GAP? |
|------------|---------------|---------------|--------------|------|
| execution_completed | Did it finish? | CustomerRunsPage | ✓ status column | NO |
| constraints_satisfied | Which constraints met? | Not shown | Not surfaced | **YES** |
| constraints_violated | Which constraints failed? | CustomerRunsPage (errors) | Partial | **PARTIAL** |
| intent_fulfilled | Was goal achieved? | CustomerRunsPage | outcome_type only | **PARTIAL** |
| cost_recording | Actual cost vs estimated | CustomerRunsPage | ✓ cost column | NO |

**PIN-167 Finding:** "Cost tables show 0 despite workflows consuming tokens"

**Missing UI Element:**
```
CustomerRunsPage should show:
├── Estimated vs Actual cost comparison
├── Constraints: "budget: ✓ | rate_limit: ✓ | policy: ✗"
└── Intent: "Task completed" vs "Task partially completed (2/3 stages)"
```

---

## 2. Test Scenario Support Gaps

From TR-004 (Test Matrix) and PIN-167 (Human Testing):

### 2.1 Scenario 1: Incident Creation

**Test Finding:** "No preview of what stages would execute before starting"

| Expected UI | Current State | GAP |
|-------------|---------------|-----|
| Pre-run preview | Not implemented | **MISSING** |
| Stage breakdown | Not shown | **MISSING** |
| Cost estimate | Partial (budget only) | **PARTIAL** |

---

### 2.2 Scenario 2: Execution Routing

**Test Finding:** "routing_decisions field always empty in workflow responses"

| Expected UI | Current State | GAP |
|-------------|---------------|-----|
| CARE involvement visible | Not shown to customers | **BY DESIGN** (founder-only) |
| Routing stats in fops | FounderPulsePage has signals | NO |
| Routing stability metric | Exists but misleading | **NEEDS FIX** |

**Note:** CARE invisibility to customers is correct (PIN-183). Founder console should show it.

---

### 2.3 Scenario 3: Recovery Suggestion

**Test Finding:** "Recovery API is powerful but completely separate from workflow flow"

| Expected UI (Founder) | Current State | GAP |
|----------------------|---------------|-----|
| Recovery candidates in timeline | RecoveryPage (separate) | **FRAGMENTED** |
| Recovery actions taken | Not in workflow view | **MISSING** |
| Link to recovery evaluation | Not implemented | **MISSING** |

**Recommendation:** FounderTimelinePage should link to recovery decisions when they occur.

---

### 2.4 Scenario 5: Cost/Ops Visibility

**Test Finding:** "Prometheus has 60+ metrics but requires insider knowledge"

| Expected UI (Founder) | Current State | GAP |
|----------------------|---------------|-----|
| Key metrics summary | FounderPulsePage (4 signals) | **PARTIAL** |
| Prometheus integration | Not linked | **MISSING** |
| Grafana dashboard links | Not shown | **MISSING** |

**Recommendation:** FounderOpsConsole should include links to Prometheus/Grafana dashboards.

---

### 2.5 Scenario 6: Memory Carryover

**Test Finding:** "MEMORY_CONTEXT_INJECTION enabled but invisible"

| Expected UI | Current State | GAP |
|-------------|---------------|-----|
| Memory injection status | Not shown | **MISSING** |
| What was injected | Not shown | **MISSING** |
| Memory sources | Not shown | **MISSING** |

**This is a contract violation (PRE-RUN: memory_injection_enabled MUST be visible)**

---

## 3. Feature Set Gaps

Based on capabilities that exist in backend but aren't surfaced:

### 3.1 Customer Console (console.agenticverz.com)

| Feature | Backend Status | UI Status | GAP |
|---------|---------------|-----------|-----|
| Run history | ✓ API exists | CustomerRunsPage | NO |
| Budget display | ✓ API exists | CustomerLimitsPage | NO |
| Rate limits | ✓ API exists | CustomerLimitsPage | NO |
| API keys | ✓ API exists | CustomerKeysPage | NO |
| Incidents | ✓ API exists | IncidentsPage | NO |
| Pre-run preview | ✗ Not exposed | Not implemented | **MISSING** |
| Budget mode visibility | ✓ Exists | Not shown | **MISSING** |
| Constraint satisfaction | ✓ Exists | Not shown | **MISSING** |

---

### 3.2 Founder Console (fops.agenticverz.com)

| Feature | Backend Status | UI Status | GAP |
|---------|---------------|-----------|-----|
| System pulse | ✓ API exists | FounderPulsePage | NO |
| At-risk customers | ✓ API exists | FounderOpsConsole | NO |
| Decision timeline | ✓ API exists | FounderTimelinePage | NO |
| Kill-switches | ✓ API exists | FounderControlsPage | NO |
| CARE routing visibility | ✓ Exists | Not in timeline | **PARTIAL** |
| Memory query visibility | ✓ Exists | Not shown | **MISSING** |
| Prometheus link | ✓ Running | Not linked | **MISSING** |
| Grafana link | ✓ Running | Not linked | **MISSING** |
| Recovery-to-timeline link | ✓ Both exist | Not connected | **MISSING** |

---

### 3.3 Preflight Consoles

| Feature | Backend Status | UI Status | GAP |
|---------|---------------|-----------|-----|
| FounderPreflightDTO | ✓ Schema defined | No UI yet | **NEEDS DEPLOYMENT** |
| CustomerPreflightDTO | ✓ Schema defined | No UI yet | **NEEDS DEPLOYMENT** |
| Promotion checklist | ✓ API exists | No UI yet | **NEEDS DEPLOYMENT** |

---

## 4. Summary: Missing Elements by Priority

### P0 - Contract Violations (Must Fix)

| Gap | Contract | Current State | Required Action |
|-----|----------|---------------|-----------------|
| Pre-run preview | PRE-RUN | Not implemented | Add stage/skill preview before run start |
| Memory injection visibility | PRE-RUN | Not shown | Show memory_injection_enabled + summary |
| Budget mode visibility | CONSTRAINT | Not shown | Show "ADVISORY" or "ENFORCED" label |
| Constraint satisfaction | OUTCOME | Not shown | Show which constraints passed/failed |

### P1 - Visibility Improvements (Should Fix)

| Gap | Area | Current State | Required Action |
|-----|------|---------------|-----------------|
| CARE routing in timeline | Founder | Not explicit | Add routing_method, agents_rejected to timeline |
| Memory query in timeline | Founder | Not shown | Add memory_queried, memory_injected to timeline |
| Recovery-timeline link | Founder | Fragmented | Link recovery decisions to timeline |
| Prometheus/Grafana links | Founder | Hidden | Add dashboard links to fops |

### P2 - Nice to Have

| Gap | Area | Current State | Required Action |
|-----|------|---------------|-----------------|
| Preflight UIs | Both planes | Schema only | Build preflight pages |
| Estimated vs actual cost | Customer | Partial | Show comparison |
| Policies queryable upfront | Customer | Post-execution only | Add policy preview |

---

## 5. Wireframe Amendments Required

### CustomerRunsPage Amendments

```diff
Current:
- run_id, status, skill_name, duration, cost, error_message

Proposed:
+ run_id, status, skill_name, duration, cost, error_message
+ estimated_cost (compare with actual)
+ constraints_status: { budget: ✓, rate_limit: ✓, policy: ✗ }
+ stages_completed: "2/3"
```

### CustomerLimitsPage Amendments

```diff
Current:
- Budget progress bar
- Rate limits

Proposed:
+ Budget progress bar
+ Budget Mode Badge: "ADVISORY" (amber) or "ENFORCED" (green)
+ Rate limits
+ Warning text when ADVISORY mode
```

### FounderTimelinePage Amendments

```diff
Current:
- Decision records with type, source, trigger

Proposed:
+ Decision records with type, source, trigger
+ For ROUTING decisions:
+   - routing_method: CARE | direct | fallback
+   - agents_considered: ["agent-1", "agent-2"]
+   - agents_rejected: [{agent, reason}]
+ For MEMORY decisions:
+   - memory_queried: true/false
+   - memory_injected: ["pin-123", "run-456"]
+ Link to recovery page for RECOVERY decisions
```

### FounderOpsConsole Amendments

```diff
Current:
- System truth strip
- At-risk customers
- All customers
- Playbooks
- Timeline placeholder

Proposed:
+ System truth strip
+ At-risk customers
+ All customers
+ Playbooks
+ Timeline placeholder
+ Monitoring Links Section:
+   - Prometheus: localhost:9090
+   - Grafana: localhost:3000 (6 dashboards)
```

---

## 6. Conclusion

**15 gaps identified across contracts, tests, and features.**

The wireframes are architecturally aligned (100% route match) but have contract surfacing gaps. The system works correctly under the hood, but violates the "no opacity" principle from the contract framework.

**Most Critical Gap:** Pre-run visibility - customers cannot see what WILL happen before execution starts.

**Runtime v1 Compliance:** These are surfacing issues, not feature additions. They can be addressed without violating the feature freeze (PIN-183) because:
1. The data already exists in APIs
2. This is "fix surfacing, not semantics" (per PIN-183 rules)
3. No new primitives or contracts required

**Recommended Next Phase:** Address P0 gaps as "Phase 5E-5: Contract Surfacing Fixes"
