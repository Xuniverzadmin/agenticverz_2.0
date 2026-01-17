# Customer Console Build Plan

**Status:** STRATEGIC PLAN
**Created:** 2026-01-16
**Based On:** 7 Domain Audits + Cross-Domain Analysis

---

## 0. Executive Summary

This plan sequences the build order to maximize leverage—each component enables the next, creating a closed-loop ecosystem that can be tested end-to-end.

### Current State (From Audits)

| Domain | Grade | Key Gap |
|--------|-------|---------|
| Accounts | A- | Missing profile update, invoices |
| Connectivity (API Keys) | A- | Missing rotation, test endpoint |
| Connectivity (SDK) | F | **Customer LLM monitoring unimplemented** |
| Activity | B | Needs incident/cost linking |
| Incidents | B | No cost impact, no auto-create from budget |
| Policies | C+ | Limits not enforced at runtime |
| Logs | D | AuditLedger has no write path |
| Analytics | D | No console integration, siloed |
| Limits | F | **3 fragmented systems** |
| Overview | C | Derived correctly, missing sources |
| Cross-Domain | 55% | **Critical silos** |

### Build Strategy

```
FOUNDATION → CORE LOOP → OBSERVABILITY → INTELLIGENCE → POLISH
```

**Principle:** Build the write paths first, then read paths, then cross-domain, then UI.

---

## 1. Dependency Graph

```
                    ┌─────────────────────────────────────────┐
                    │           PHASE 5: POLISH               │
                    │  Overview Dashboard, UI Polish, Alerts  │
                    └─────────────────────────────────────────┘
                                        ▲
                    ┌─────────────────────────────────────────┐
                    │      PHASE 4: INTELLIGENCE LAYER        │
                    │   Analytics Console, Cost Attribution   │
                    └─────────────────────────────────────────┘
                                        ▲
                    ┌─────────────────────────────────────────┐
                    │      PHASE 3: OBSERVABILITY LAYER       │
                    │    Logs Write Path, Audit Trail         │
                    └─────────────────────────────────────────┘
                                        ▲
                    ┌─────────────────────────────────────────┐
                    │        PHASE 2: CORE DOMAIN LOOP        │
                    │  Activity→Incidents→Policies (bidirectional) │
                    └─────────────────────────────────────────┘
                                        ▲
                    ┌─────────────────────────────────────────┐
                    │         PHASE 1: FOUNDATION             │
                    │   Unified Limits, Cross-Domain FKs      │
                    └─────────────────────────────────────────┘
                                        ▲
                    ┌─────────────────────────────────────────┐
                    │           PHASE 0: PREREQUISITES        │
                    │      Accounts, API Keys (already done)  │
                    └─────────────────────────────────────────┘
```

---

## 2. Phase 0: Prerequisites (ALREADY DONE)

**Status:** ✅ COMPLETE

These are already working and provide the foundation:

| Component | Status | Provides |
|-----------|--------|----------|
| Accounts (Projects, Users) | ✅ A- | Tenant isolation, RBAC |
| API Keys CRUD | ✅ A- | Authentication for all APIs |
| Tenant Quotas | ✅ B | Plan-based limits |
| Cost Recording | ✅ B+ | Cost attribution data |

**Test:** Can create tenant, create API key, make authenticated API calls.

---

## 3. Phase 1: Foundation (Days 1-8)

**Goal:** Establish single source of truth for limits and cross-domain linking.

### 1.1 Unified Limits System (Days 1-5)

**Problem:** 3 separate limit systems (Tenant Quotas, Cost Budgets, Policy Limits) with no sync.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  UNIFIED LIMITS SERVICE (L4)                                │
│                                                             │
│  Single source of truth for ALL limits:                     │
│  - Tenant quotas (runs/day, tokens/month)                   │
│  - Cost budgets (daily/monthly spend)                       │
│  - Policy limits (custom constraints)                       │
│  - Rate limits (API key RPM)                                │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Create `/api/v1/limits/*` unified facade | 2 days | All limit operations in one place |
| Migrate cost_budgets → limits table | 1 day | Single schema |
| Add CRUD for policy limits | 1 day | Customer can set limits |
| Add pre-execution limit check | 1 day | **Blocks runs before overspend** |

**Deliverable:** `POST /api/v1/limits/check` returns allowed/blocked BEFORE execution.

**Test:**
```
1. Set daily cost limit = $10
2. Run execution that costs $8
3. Run another execution that would cost $5
4. EXPECT: Second run BLOCKED with clear error
```

### 1.2 Cross-Domain Foreign Keys (Days 6-8)

**Problem:** 9 missing FKs prevent cross-domain queries.

**Build:**

| Migration | Tables Affected | Enables |
|-----------|-----------------|---------|
| Add `incident_id` to `cost_records` | cost_records | Incident → cost impact |
| Add `api_key_id` to `cost_records` | cost_records | API key → cost tracking |
| Add `incident_id` to `cost_anomalies` | cost_anomalies | Anomaly → incident auto-create |
| Add `run_id` to `system_records` | system_records | Activity → logs |
| Add `incident_id` to `llm_run_records` | llm_run_records | Incident → logs |

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Create migration for new FKs | 1 day | Schema ready |
| Update write services to populate FKs | 1 day | Data flows |
| Add indexes for cross-domain queries | 0.5 day | Performance |
| Update models with relationships | 0.5 day | ORM navigation |

**Deliverable:** All cross-domain FKs exist and are populated on write.

**Test:**
```
1. Create a run that fails
2. Incident auto-created with source_run_id
3. Query: SELECT * FROM cost_records WHERE incident_id = ?
4. EXPECT: Cost records linked to incident
```

### Phase 1 Exit Criteria

- [ ] Single `/api/v1/limits/*` facade exists
- [ ] Pre-execution limit check works
- [ ] All 9 FKs added and populated
- [ ] Cross-domain queries return data

---

## 4. Phase 2: Core Domain Loop (Days 9-18)

**Goal:** Activity ↔ Incidents ↔ Policies working bidirectionally.

### 2.1 Activity → Incidents (Days 9-11)

**Problem:** Run failures create incidents, but Activity UI can't see them.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  ACTIVITY DOMAIN ENHANCEMENT                                │
│                                                             │
│  GET /api/v1/runs/{run_id}/incidents                        │
│  GET /api/v1/runs/{run_id}/cost                             │
│  GET /api/v1/runs/{run_id}/logs                             │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Add `/runs/{id}/incidents` endpoint | 0.5 day | Bidirectional navigation |
| Add `/runs/{id}/cost` endpoint | 0.5 day | Cost visibility in Activity |
| Add `/runs/{id}/logs` endpoint | 0.5 day | Log visibility in Activity |
| Update Activity UI with links | 1.5 days | User can navigate |

**Test:**
```
1. Run fails → Incident created
2. GET /api/v1/runs/{run_id}/incidents
3. EXPECT: Returns incident(s) for that run
4. UI shows "This run generated 1 incident" with link
```

### 2.2 Incidents → Policies (Days 12-14)

**Problem:** High-severity incidents create DRAFT proposals only. No feedback loop.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  INCIDENT → POLICY PROPOSAL ENHANCEMENT                     │
│                                                             │
│  1. Incident creates proposal (existing)                    │
│  2. Proposal approved → Policy created (existing)           │
│  3. NEW: Policy prevents future incidents                   │
│  4. NEW: Track prevention effectiveness                     │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Add `policy_effectiveness` tracking | 1 day | Measure policy impact |
| Add `/policies/rules/{id}/effectiveness` | 0.5 day | Show prevention stats |
| Add incident → policy linking in UI | 1 day | User sees connection |
| Add "Incidents prevented" count | 0.5 day | Value demonstration |

**Test:**
```
1. Incident created → Policy proposal generated
2. Approve policy
3. Similar failure occurs
4. EXPECT: Incident suppressed, prevention_record created
5. GET /policies/rules/{id}/effectiveness shows count
```

### 2.3 Analytics → Incidents Auto-Create (Days 15-18)

**Problem:** Budget breaches don't create incidents. Critical gap.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  COST ANOMALY → INCIDENT PROPAGATION                        │
│                                                             │
│  When: cost_anomaly.severity = HIGH                         │
│        cost_anomaly.type = BUDGET_EXCEEDED                  │
│  Then: Create incident automatically                        │
│        Link incident_id back to anomaly                     │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Modify `cost_anomaly_detector.py` | 1.5 days | Auto-create incidents |
| Add BUDGET_EXCEEDED incident category | 0.5 day | Proper categorization |
| Link incident_id to cost_anomaly | 0.5 day | Bidirectional |
| Add to Overview highlights | 0.5 day | Dashboard visibility |
| E2E test scenario | 1 day | Verify full flow |

**Test:**
```
1. Set budget limit = $100
2. Spend $120 (via test runs)
3. Run anomaly detection
4. EXPECT:
   - cost_anomaly created (BUDGET_EXCEEDED, HIGH)
   - incident auto-created
   - incident visible in Overview
   - incident links to anomaly
```

### Phase 2 Exit Criteria

- [ ] Activity → Incidents bidirectional
- [ ] Policy effectiveness tracked
- [ ] Budget breach → Incident auto-created
- [ ] Full loop testable: Run → Incident → Policy → Prevention

---

## 5. Phase 3: Observability Layer (Days 19-26)

**Goal:** Complete audit trail across all domains.

### 3.1 Audit Ledger Write Path (Days 19-22)

**Problem:** `audit_ledger` table exists but nothing writes to it.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  AUDIT LEDGER SERVICE (L4)                                  │
│                                                             │
│  Emit audit entries for:                                    │
│  - Policy rule changes (CRUD)                               │
│  - Limit changes (CRUD)                                     │
│  - Incident lifecycle (create, acknowledge, resolve)        │
│  - API key lifecycle (create, freeze, revoke)               │
│  - Budget changes                                           │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Create `AuditLedgerService` | 1 day | Centralized audit |
| Add audit hooks to PolicyEngine | 0.5 day | Policy changes audited |
| Add audit hooks to IncidentEngine | 0.5 day | Incident changes audited |
| Add audit hooks to LimitsService | 0.5 day | Limit changes audited |
| Add audit hooks to KeysService | 0.5 day | Key changes audited |
| Verify Logs domain queries work | 1 day | Data visible in UI |

**Test:**
```
1. Create a policy rule
2. GET /api/v1/logs/audit?entity_type=POLICY_RULE
3. EXPECT: Audit entry with actor, action, timestamp
```

### 3.2 Domain Events Table (Days 23-26)

**Problem:** No unified timeline across domains.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN EVENTS (Unified Audit Trail)                        │
│                                                             │
│  Table: domain_events                                       │
│  - tenant_id, timestamp, source_domain                      │
│  - event_type, entity_id, related_entities                  │
│  - summary, data (JSONB)                                    │
│                                                             │
│  Endpoint: GET /api/v1/timeline                             │
│  → Returns cross-domain event stream                        │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Create `domain_events` table | 0.5 day | Schema |
| Create `DomainEventService` | 1 day | Emit from all domains |
| Add event emission to Activity | 0.5 day | run_started, run_failed |
| Add event emission to Incidents | 0.5 day | incident_created, resolved |
| Add event emission to Policies | 0.5 day | rule_created, rule_applied |
| Add event emission to Analytics | 0.5 day | budget_exceeded, anomaly_detected |
| Create `/api/v1/timeline` endpoint | 0.5 day | Unified query |

**Test:**
```
1. Run fails → incident created → policy proposed
2. GET /api/v1/timeline?tenant_id=X&last_24h=true
3. EXPECT: All events in chronological order with correlation
```

### Phase 3 Exit Criteria

- [ ] Audit ledger has data (governance actions)
- [ ] Domain events table populated
- [ ] `/api/v1/timeline` returns unified view
- [ ] Can trace any entity across domains

---

## 6. Phase 4: Intelligence Layer (Days 27-36)

**Goal:** Analytics visible in console, cost attribution complete.

### 4.1 Analytics Console Integration (Days 27-31)

**Problem:** Analytics backend exists (B+) but no console presence (D).

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  ANALYTICS IN CONSOLE                                       │
│                                                             │
│  Option A: Add Analytics as 6th sidebar domain              │
│  Option B: Embed Analytics under Overview                   │
│  Option C: Create Analytics subsection in Connectivity      │
│                                                             │
│  RECOMMEND: Option A (cleanest UX)                          │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Decision: Domain or subsection | 0.5 day | Architecture choice |
| Create unified `/api/v1/analytics/*` facade | 1.5 days | Clean API |
| Build Analytics dashboard page | 2 days | Cost visibility |
| Build Usage tracking page | 1 day | Token/run visibility |
| Build Budgets management page | 1 day | Limit configuration |

**Deliverable:** Customer can see and configure all cost/usage from console.

### 4.2 API Key Cost Attribution (Days 32-34)

**Problem:** API key costs invisible. Can't track per-key spend.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  API KEY → COST ATTRIBUTION                                 │
│                                                             │
│  1. cost_records.api_key_id populated (Phase 1 FK)          │
│  2. GET /api/v1/analytics/costs?group_by=api_key            │
│  3. Connectivity UI shows cost per key                      │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Ensure api_key_id populated on cost write | 0.5 day | Data flows |
| Add cost-by-api-key endpoint | 0.5 day | Query available |
| Add cost column to Keys page | 1 day | UI visibility |
| Add cost alerts for keys | 1 day | Proactive monitoring |

**Test:**
```
1. Make API calls with key X
2. GET /api/v1/connectivity/api-keys/{id}
3. EXPECT: Shows "This key has used $Y this month"
```

### 4.3 Incident Cost Impact (Days 35-36)

**Problem:** Incidents don't show financial impact.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  INCIDENT → COST IMPACT                                     │
│                                                             │
│  GET /api/v1/incidents/{id}/cost-impact                     │
│  Returns:                                                   │
│  - Total cost of failed runs                                │
│  - Cost of recovery attempts                                │
│  - Estimated savings if prevented                           │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Create cost-impact endpoint | 0.5 day | Query |
| Calculate recovery costs | 0.5 day | Full picture |
| Add to Incident detail UI | 1 day | Visibility |

**Test:**
```
1. Incident from failed run
2. GET /api/v1/incidents/{id}/cost-impact
3. EXPECT: { "total_cost_cents": 500, "runs_affected": 3 }
```

### Phase 4 Exit Criteria

- [ ] Analytics visible in console (sidebar or embedded)
- [ ] API key costs visible in Connectivity
- [ ] Incident cost impact visible in Incidents
- [ ] Customer can answer "How much am I spending and where?"

---

## 7. Phase 5: Polish (Days 37-45)

**Goal:** Overview works correctly, UI complete, alerts functional.

### 5.1 Overview Dashboard Fix (Days 37-40)

**Problem:** Capability bindings wrong, some unmapped.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  OVERVIEW CAPABILITY REBINDING                              │
│                                                             │
│  Fix 3 wrong bindings:                                      │
│  - overview.decisions_list → /api/v1/overview/decisions     │
│  - overview.cost_summary → /api/v1/overview/costs           │
│  - overview.cost_by_feature → /api/v1/overview/costs        │
│                                                             │
│  Implement 5 unmapped:                                      │
│  - overview.cost_by_model                                   │
│  - overview.cost_anomalies                                  │
│  - overview.decisions_count                                 │
│  - overview.recovery_stats                                  │
│  - overview.feedback_summary                                │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Rebind 3 wrong capabilities | 1 day | Correct data source |
| Implement cost_by_model in facade | 0.5 day | Model breakdown |
| Implement cost_anomalies in facade | 0.5 day | Anomaly visibility |
| Implement decisions_count | 0.25 day | Quick stat |
| Implement recovery_stats | 0.5 day | Recovery visibility |
| Implement feedback_summary | 0.25 day | Feedback loop |
| Update Overview UI panels | 1 day | Display all data |

**Test:**
```
1. Load Overview dashboard
2. EXPECT: All 11 panels populated with real data
3. All data from correct endpoints (not founder console)
```

### 5.2 Logs Domain Cleanup (Days 41-42)

**Problem:** 16 wrong capabilities, need cleanup and correct binding.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  LOGS CAPABILITY CLEANUP                                    │
│                                                             │
│  Delete: 14 wrong + 2 extra capabilities                    │
│  Create: 3 correct capabilities                             │
│  - logs.audit_trail → /api/v1/logs/audit                    │
│  - logs.llm_records → /api/v1/logs/llm-runs                 │
│  - logs.system_records → /api/v1/logs/system                │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Delete 16 wrong capability files | 0.5 day | Clean registry |
| Create 3 correct capability files | 0.5 day | Correct bindings |
| Verify SDSR scenarios pass | 0.5 day | Validation |
| Update Logs UI | 0.5 day | Correct panels |

### 5.3 Alert System (Days 43-45)

**Problem:** No proactive notifications for approaching limits, anomalies.

**Build:**

```
┌─────────────────────────────────────────────────────────────┐
│  ALERT SYSTEM                                               │
│                                                             │
│  Triggers:                                                  │
│  - Limit approaching (80%, 90%, 100%)                       │
│  - Budget exceeded                                          │
│  - Cost anomaly detected                                    │
│  - Incident created (HIGH/CRITICAL)                         │
│                                                             │
│  Channels:                                                  │
│  - Console notification (in-app)                            │
│  - Webhook (customer endpoint)                              │
│  - Email (future)                                           │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**

| Task | Effort | Leverage |
|------|--------|----------|
| Create AlertService | 1 day | Centralized alerts |
| Add webhook delivery | 1 day | External integration |
| Add in-app notifications | 0.5 day | Console visibility |
| Add alert configuration UI | 0.5 day | Customer control |

**Test:**
```
1. Set alert: notify when spend > 80% of budget
2. Spend reaches 82%
3. EXPECT: Webhook fired, in-app notification shown
```

### Phase 5 Exit Criteria

- [ ] Overview all 11 panels working
- [ ] Logs 3 correct capabilities, 16 wrong deleted
- [ ] Alerts fire on thresholds
- [ ] Customer proactively notified

---

## 8. Full System Test Scenarios

After all phases, these E2E scenarios must pass:

### Scenario 1: Cost Control Loop

```
1. Customer sets daily budget = $50
2. Customer runs executions totaling $45
3. Customer attempts run that would cost $10
4. EXPECT: Run BLOCKED with "Budget exceeded" error
5. Customer increases budget to $100
6. Customer retries run
7. EXPECT: Run succeeds
8. GET /api/v1/analytics/costs shows $55 spent
```

### Scenario 2: Incident → Policy Loop

```
1. Run fails with error X
2. EXPECT: Incident created automatically
3. Incident proposes policy "Prevent error X"
4. Customer approves policy
5. Similar run attempts
6. EXPECT: Run blocked by policy, prevention_record created
7. GET /policies/rules/{id}/effectiveness shows 1 prevented
```

### Scenario 3: Cross-Domain Tracing

```
1. Run fails → Incident → Policy proposed
2. GET /api/v1/runs/{run_id}/incidents → returns incident
3. GET /api/v1/incidents/{id}/source-run → returns run
4. GET /api/v1/incidents/{id}/cost-impact → returns cost
5. GET /api/v1/timeline → shows all events in order
6. GET /api/v1/logs/audit → shows governance actions
```

### Scenario 4: Budget Breach Escalation

```
1. Customer sets monthly budget = $1000
2. Spend accumulates to $1050
3. Anomaly detection runs
4. EXPECT: BUDGET_EXCEEDED anomaly created
5. EXPECT: Incident auto-created from anomaly
6. EXPECT: Overview shows "Budget exceeded" alert
7. EXPECT: Webhook fired to customer endpoint
```

### Scenario 5: API Key Attribution

```
1. Customer has 2 API keys: key_A, key_B
2. Make calls with key_A (cost $100)
3. Make calls with key_B (cost $50)
4. GET /api/v1/connectivity/api-keys
5. EXPECT: key_A shows $100, key_B shows $50
6. Freeze key_A
7. GET /api/v1/logs/audit?entity_type=API_KEY
8. EXPECT: Audit entry for freeze action
```

---

## 9. Timeline Summary

| Phase | Days | Focus | Key Deliverable |
|-------|------|-------|-----------------|
| **0** | Done | Prerequisites | Accounts, API Keys working |
| **1** | 1-8 | Foundation | Unified limits, cross-domain FKs |
| **2** | 9-18 | Core Loop | Activity ↔ Incidents ↔ Policies |
| **3** | 19-26 | Observability | Audit trail, domain events |
| **4** | 27-36 | Intelligence | Analytics console, cost attribution |
| **5** | 37-45 | Polish | Overview fix, alerts |

**Total: 45 engineering days**

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Phase 1 (Limits) blocks everything | Parallel work on Activity↔Incidents UI |
| FK migrations break existing queries | Add indexes, test queries before deploy |
| Analytics console scope creep | Timebox to 5 days, MVP only |
| Audit volume too high | Add sampling/filtering in AuditLedgerService |
| Cross-domain queries slow | Add composite indexes, consider materialized views |

---

## 11. Success Metrics

After Phase 5 completion:

| Metric | Target |
|--------|--------|
| Cross-domain integration | 90%+ (up from 55%) |
| Limit systems | 1 unified (down from 3) |
| Audit coverage | 100% governance actions |
| E2E scenarios passing | 5/5 |
| Customer questions answerable | All 5 domain questions |

### The Five Questions

| Domain | Question | Answerable After |
|--------|----------|------------------|
| Overview | Is the system okay? | Phase 5 |
| Activity | What ran / is running? | Phase 2 |
| Incidents | What went wrong? | Phase 2 |
| Policies | How is behavior defined? | Phase 2 |
| Logs | What is the raw truth? | Phase 3 |
| Analytics | How much am I spending? | Phase 4 |

---

## 12. Appendix: Audit Summary

### Documents Created

| Audit | Location | Grade |
|-------|----------|-------|
| Connectivity | `docs/architecture/connectivity/CONNECTIVITY_DOMAIN_AUDIT.md` | API Keys: A-, SDK: F |
| Accounts | `docs/architecture/accounts/ACCOUNTS_SECTION_AUDIT.md` | A- |
| Overview | `docs/architecture/overview/OVERVIEW_DOMAIN_AUDIT.md` | C |
| Logs | `docs/architecture/logs/LOGS_DOMAIN_AUDIT.md` | D |
| Analytics | `docs/architecture/analytics/ANALYTICS_DOMAIN_AUDIT.md` | Backend B+, Console D |
| Limits | `docs/architecture/limits/LIMITS_MANAGEMENT_AUDIT.md` | F |
| Cross-Domain | `docs/architecture/integration/CROSS_DOMAIN_AUDIT.md` | 55% |

### Key Findings Driving This Plan

1. **Limits fragmentation** (3 systems) must be unified first—everything depends on limits working correctly.

2. **Cross-domain FKs missing** (9 total) block all bidirectional queries—add early.

3. **Analytics → Incidents gap** is critical—budget breaches create no incidents.

4. **Audit ledger empty**—governance actions not recorded.

5. **Overview capabilities wrong**—dashboard shows incorrect/missing data.

6. **SDK integration unimplemented**—customer LLM monitoring is the entire value proposition (separate track).
