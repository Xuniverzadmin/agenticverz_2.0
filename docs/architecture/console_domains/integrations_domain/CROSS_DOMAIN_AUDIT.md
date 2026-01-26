# Cross-Domain Integration Audit

**Status:** FRAGMENTED - REQUIRES WIRING
**Last Updated:** 2026-01-16
**Integration Maturity:** 55%

---

## 0. Executive Summary

> **Domains are speaking in SILOS. Critical cross-domain flows are missing or one-way only.**

| Finding | Count |
|---------|-------|
| Connected flows | 4 |
| Partially connected | 5 |
| Completely siloed | 6 |
| Missing bidirectional | 8 |

**Critical Gaps:**
- Analytics ↔ Incidents: Cost anomalies don't create incidents
- Policies ↔ Analytics: Budget limits not synchronized
- Activity ↔ Incidents: Can't see incidents from a run
- Connectivity ↔ Analytics: API key usage not tracked

---

## 1. Domain Integration Matrix

```
                 OVERVIEW  ACTIVITY  INCIDENTS  POLICIES  LOGS  ANALYTICS  CONNECTIVITY  ACCOUNTS
OVERVIEW            -         ◄──       ◄──        ◄──     ◄──     ◄──          ◄──         ◄──
ACTIVITY           ──►         -        ──►        ◄──     ──►     ──►           ✗           ✗
INCIDENTS          ──►        ✗✗✗        -         ◄─►     ──►     ✗✗✗          ✗           ✗
POLICIES           ──►        ──►       ──►         -       ✗      ✗✗✗          ✗           ✗
LOGS               ──►        ◄──       ◄──         ✗       -       ✗           ✗           ✗
ANALYTICS          ──►        ◄──       ✗✗✗        ✗✗✗     ✗       -           ✗✗✗         ✗
CONNECTIVITY       ──►         ✗         ✗          ✗       ✗      ✗✗✗          -           ✗
ACCOUNTS           ──►        ──►       ──►        ──►     ──►     ──►         ──►          -

Legend:
  ──►  = One-way CONNECTED (data flows)
  ◄──  = Receives data (read-only)
  ◄─►  = Bidirectional (partial)
  ✗    = No integration needed
  ✗✗✗  = SILOED (should connect but doesn't)
```

---

## 2. Integration Status by Domain Pair

### 2.1 ACTIVITY → INCIDENTS

| Aspect | Status | Evidence |
|--------|--------|----------|
| Run failure creates incident | ✅ CONNECTED | `incident_engine.py:293-471` |
| `source_run_id` populated | ✅ CONNECTED | FK exists |
| Policy suppression checked | ✅ CONNECTED | `_check_policy_suppression()` |

**Gap:** Cannot query incidents FROM Activity UI.

```
MISSING: GET /api/v1/runs/{run_id}/incidents
```

---

### 2.2 INCIDENTS → ACTIVITY

| Aspect | Status | Evidence |
|--------|--------|----------|
| Incident links to source run | ✅ EXISTS | `incidents.source_run_id` |
| Run shows its incidents | ❌ SILOED | No reverse query |
| "View Source Run" button | ❌ MISSING | UI gap |

**Gap:** Bidirectional tracing missing.

```
MISSING:
- runs.incident_ids field
- "This run generated N incidents" in Activity UI
- GET /api/v1/runs/{run_id}/incidents endpoint
```

---

### 2.3 POLICIES → INCIDENTS

| Aspect | Status | Evidence |
|--------|--------|----------|
| Policies can suppress incidents | ✅ CONNECTED | `prevention_records` table |
| Violation creates prevention record | ✅ CONNECTED | Audit trail exists |

**Working correctly.**

---

### 2.4 INCIDENTS → POLICIES

| Aspect | Status | Evidence |
|--------|--------|----------|
| High-severity → policy proposal | ⚠️ PARTIAL | `_maybe_create_policy_proposal()` |
| Proposal status: DRAFT only | ⚠️ LIMITED | Requires human approval |
| Proposal links to incident | ✅ EXISTS | `triggering_incident_id` |

**Gap:** Only HIGH/CRITICAL severity triggers proposals. No automatic enforcement.

---

### 2.5 ANALYTICS → INCIDENTS (CRITICAL GAP)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Cost anomaly detection | ✅ EXISTS | `cost_anomaly_detector.py` |
| Budget breach detected | ✅ EXISTS | `BUDGET_EXCEEDED` type |
| Anomaly creates incident | ❌ SILOED | **No integration** |
| `incident_id` on anomaly | ❌ MISSING | Field exists but never populated |

**Critical Gap:** Budget breaches create NO incidents.

```
EXPECTED FLOW:
  cost_anomaly.severity = HIGH
  cost_anomaly.type = BUDGET_EXCEEDED
  → Create incident automatically
  → Link incident_id back to anomaly

ACTUAL FLOW:
  cost_anomaly created
  → Logged to cost_anomalies table
  → NO INCIDENT CREATED
  → Customer unaware unless checking Analytics
```

---

### 2.6 INCIDENTS → ANALYTICS

| Aspect | Status | Evidence |
|--------|--------|----------|
| Incident shows cost impact | ❌ SILOED | No cost_cents on incident |
| Cost records link to incident | ❌ MISSING | No `incident_id` field |
| "Cost of this failure" view | ❌ MISSING | UI gap |

**Gap:** Cannot see financial impact of incidents.

```
MISSING:
- cost_records.incident_id FK
- GET /api/v1/incidents/{id}/cost-impact endpoint
- "This incident cost $X" in Incidents UI
```

---

### 2.7 ACTIVITY → ANALYTICS

| Aspect | Status | Evidence |
|--------|--------|----------|
| Run generates cost record | ✅ CONNECTED | `cost_records.run_id` exists |
| Cost attribution works | ✅ CONNECTED | By tenant, user, feature |
| Run detail shows cost | ❌ MISSING | No cost in Activity UI |

**Gap:** One-way only. Activity doesn't display cost impact.

```
MISSING:
- GET /api/v1/runs/{run_id}/cost endpoint
- "This run cost $X" in Activity UI
- Cost trend in Activity dashboard
```

---

### 2.8 POLICIES ↔ ANALYTICS (CRITICAL GAP)

| Aspect | Status | Evidence |
|--------|--------|----------|
| Policy limits table | ✅ EXISTS | `limits` in Policies |
| Cost budgets table | ✅ EXISTS | `cost_budgets` in Analytics |
| Synchronization | ❌ SILOED | **No sync mechanism** |

**Critical Gap:** Two separate "truth" sources for budgets.

```
PROBLEM:
  Policies says: "Monthly limit = $100"  (limits table)
  Analytics says: "Monthly limit = $150" (cost_budgets table)

  Enforcement uses: Policies
  Cost tracking uses: Analytics

  RESULT: Inconsistent behavior
```

**Required:** Single source of truth for budget limits.

---

### 2.9 CONNECTIVITY → ANALYTICS

| Aspect | Status | Evidence |
|--------|--------|----------|
| API key exists | ✅ EXISTS | `api_keys` table |
| API key usage tracking | ❌ SILOED | No `api_key_id` in cost_records |
| Cost per API key report | ❌ MISSING | Not implemented |

**Gap:** Cannot attribute costs to specific API keys.

```
MISSING:
- cost_records.api_key_id FK
- GET /api/v1/analytics/costs?group_by=api_key
- "API Key X used $Y" in Connectivity UI
```

---

### 2.10 ACTIVITY → LOGS

| Aspect | Status | Evidence |
|--------|--------|----------|
| Traces created for runs | ✅ CONNECTED | `aos_traces` table |
| `run_id` populated | ⚠️ PARTIAL | Sometimes missing |
| LLM records linked | ⚠️ PARTIAL | Via run_id only |
| System records linked | ❌ MISSING | No run_id field |

**Gap:** Incomplete trace propagation.

```
MISSING:
- Consistent run_id on all log types
- GET /api/v1/runs/{run_id}/logs endpoint
- "View Logs" button in Activity UI
```

---

### 2.11 LOGS → INCIDENTS

| Aspect | Status | Evidence |
|--------|--------|----------|
| Traces have incident_id | ✅ CONNECTED | `aos_traces.incident_id` |
| System records have incident_id | ❌ MISSING | No field |
| LLM records have incident_id | ❌ MISSING | No field |

**Gap:** Only aos_traces linked to incidents.

---

## 3. Missing Foreign Keys

| Table | Missing FK | Target Table | Purpose |
|-------|------------|--------------|---------|
| `runs` | `incident_ids` | `incidents` | Reverse lookup |
| `cost_records` | `incident_id` | `incidents` | Cost attribution |
| `cost_records` | `api_key_id` | `api_keys` | Key-based analytics |
| `cost_records` | `policy_rule_id` | `policy_rules` | Policy impact |
| `cost_anomalies` | `incident_id` | `incidents` | Anomaly → Incident |
| `system_records` | `run_id` | `runs` | Activity → Logs |
| `system_records` | `incident_id` | `incidents` | Incident → Logs |
| `llm_run_records` | `incident_id` | `incidents` | Incident → Logs |
| `limits` | `cost_budget_id` | `cost_budgets` | Policies ↔ Analytics |

---

## 4. Missing Cross-Domain Endpoints

### Activity Domain

```
GET /api/v1/runs/{run_id}/incidents      ← Show incidents from this run
GET /api/v1/runs/{run_id}/cost           ← Show cost impact
GET /api/v1/runs/{run_id}/logs           ← Show all log entries
GET /api/v1/runs/{run_id}/policies       ← Show policies that applied
```

### Incidents Domain

```
GET /api/v1/incidents/{id}/source-run    ← Navigate to Activity
GET /api/v1/incidents/{id}/cost-impact   ← Show financial impact
GET /api/v1/incidents/{id}/related       ← Show correlated incidents
GET /api/v1/incidents/{id}/timeline      ← Cross-domain timeline
```

### Analytics Domain

```
GET /api/v1/analytics/costs?incident_id= ← Costs from incident
GET /api/v1/analytics/costs?api_key_id=  ← Costs by API key
GET /api/v1/analytics/costs?policy_id=   ← Costs affected by policy
```

### Policies Domain

```
GET /api/v1/policies/limits/{id}/sync-status  ← Check budget sync
POST /api/v1/policies/limits/{id}/sync        ← Force sync with Analytics
GET /api/v1/policies/rules/{id}/incidents     ← Incidents this rule affected
GET /api/v1/policies/rules/{id}/effectiveness ← Prevention metrics
```

---

## 5. Missing Cross-Domain Queries

### Query 1: Run → Incidents

```sql
-- Show all incidents caused by a specific run
SELECT i.*
FROM incidents i
WHERE i.source_run_id = :run_id
ORDER BY i.created_at DESC;
```

### Query 2: Incident → Cost Impact

```sql
-- Show cost impact of an incident
SELECT
  SUM(cr.cost_cents) as total_cost_cents,
  COUNT(*) as affected_runs
FROM incidents i
JOIN runs r ON r.id = i.source_run_id
JOIN cost_records cr ON cr.run_id = r.id
WHERE i.id = :incident_id;
```

### Query 3: API Key → Cost

```sql
-- Show costs by API key (REQUIRES NEW FK)
SELECT
  ak.key_prefix,
  SUM(cr.cost_cents) as total_cost_cents
FROM cost_records cr
JOIN api_keys ak ON ak.id = cr.api_key_id  -- FK doesn't exist yet
WHERE cr.tenant_id = :tenant_id
GROUP BY ak.id;
```

### Query 4: Policy → Prevention Stats

```sql
-- Show how many incidents a policy prevented
SELECT
  pr.policy_id,
  COUNT(*) as prevented_count,
  SUM(pr.estimated_cost_saved) as savings
FROM prevention_records pr
WHERE pr.policy_id = :policy_id
  AND pr.outcome = 'prevented';
```

### Query 5: Unified Timeline

```sql
-- Show all domain events for a tenant (REQUIRES NEW TABLE)
SELECT
  de.timestamp,
  de.source_domain,
  de.event_type,
  de.entity_id,
  de.summary
FROM domain_events de
WHERE de.tenant_id = :tenant_id
ORDER BY de.timestamp DESC
LIMIT 100;
```

---

## 6. Required Synchronization Mechanisms

### 6.1 Policies ↔ Analytics Budget Sync

**Option A: Policies as Source of Truth**

```python
# When policy limit changes
@event_handler("policy_limit_updated")
def sync_to_analytics(limit: Limit):
    cost_budget = get_or_create_budget(limit.tenant_id)
    cost_budget.monthly_limit_cents = limit.max_value * 100
    cost_budget.sync_source = "policies"
    save(cost_budget)
```

**Option B: Event-Driven Sync**

```python
# Emit event on either side
emit_event("budget_limit_changed", {
    "tenant_id": tenant_id,
    "source": "policies",  # or "analytics"
    "limit_type": "monthly_cost",
    "new_value": 10000
})

# Both domains subscribe and validate
@subscribe("budget_limit_changed")
def handle_budget_change(event):
    if event.source != MY_DOMAIN:
        update_local_budget(event)
```

### 6.2 Analytics → Incidents Auto-Creation

```python
# In cost_anomaly_detector.py
def detect_and_escalate(tenant_id: str):
    anomalies = detect_anomalies(tenant_id)

    for anomaly in anomalies:
        if anomaly.severity in ["HIGH", "CRITICAL"]:
            if anomaly.anomaly_type == "BUDGET_EXCEEDED":
                # CREATE INCIDENT
                incident = create_incident(
                    tenant_id=tenant_id,
                    category="BUDGET_EXCEEDED",
                    severity=anomaly.severity,
                    source="cost_anomaly",
                    source_id=anomaly.id,
                    title=f"Budget exceeded: {anomaly.entity_type}",
                    description=f"Spent {anomaly.value} vs limit {anomaly.threshold}"
                )

                # LINK BACK
                anomaly.incident_id = incident.id
                save(anomaly)
```

### 6.3 Unified Audit Trail

```python
# domain_events table
class DomainEvent(SQLModel):
    id: str
    tenant_id: str
    timestamp: datetime
    source_domain: str      # "Activity" | "Incidents" | "Policies" | etc.
    event_type: str         # "run_failed" | "incident_created" | etc.
    entity_id: str          # run_id | incident_id | policy_id
    related_entities: dict  # { "incident_id": "...", "run_id": "..." }
    summary: str
    data: dict

# Emit from each domain
def emit_domain_event(domain: str, event_type: str, entity_id: str, **kwargs):
    event = DomainEvent(
        tenant_id=get_current_tenant(),
        timestamp=utcnow(),
        source_domain=domain,
        event_type=event_type,
        entity_id=entity_id,
        **kwargs
    )
    save(event)
```

---

## 7. Integration Priority Matrix

| Integration | Severity | Effort | Priority |
|-------------|----------|--------|----------|
| Analytics → Incidents (auto-create) | CRITICAL | 3 days | **P0** |
| Policies ↔ Analytics (budget sync) | CRITICAL | 5 days | **P0** |
| Activity ↔ Incidents (bidirectional) | HIGH | 2 days | **P1** |
| Connectivity → Analytics (API key) | HIGH | 2 days | **P1** |
| Activity → Analytics (cost view) | MEDIUM | 1 day | **P2** |
| Incidents → Analytics (cost impact) | MEDIUM | 2 days | **P2** |
| Activity ↔ Logs (complete linking) | MEDIUM | 2 days | **P2** |
| Unified audit trail | MEDIUM | 3 days | **P3** |

**Total Estimated Effort:** 15-20 engineering days

---

## 8. Remediation Phases

### Phase 1: Critical Wiring (Days 1-5)

**Goal:** Close the two critical gaps.

1. **Analytics → Incidents**
   - Modify `cost_anomaly_detector.py`
   - Auto-create incidents for BUDGET_EXCEEDED
   - Add `incident_id` to `cost_anomalies` table
   - Test: Budget breach creates incident

2. **Policies ↔ Analytics**
   - Choose sync mechanism (recommend event-driven)
   - Implement budget sync trigger
   - Add validation on both sides
   - Test: Policy limit change reflects in Analytics

### Phase 2: Bidirectional Activity (Days 6-8)

**Goal:** Enable correlation from Activity domain.

3. **Activity ↔ Incidents**
   - Add `GET /api/v1/runs/{run_id}/incidents`
   - Update Activity UI with "View Incidents" button
   - Test: Can navigate from run to its incidents

4. **Connectivity → Analytics**
   - Add `api_key_id` to `cost_records`
   - Add `GET /api/v1/analytics/costs?group_by=api_key`
   - Test: Can see costs by API key

### Phase 3: Cost Visibility (Days 9-12)

**Goal:** Show financial impact across domains.

5. **Activity → Analytics**
   - Add `GET /api/v1/runs/{run_id}/cost`
   - Add cost badge in Activity UI
   - Test: Run detail shows cost

6. **Incidents → Analytics**
   - Add `incident_id` to `cost_records`
   - Add `GET /api/v1/incidents/{id}/cost-impact`
   - Test: Incident shows total cost impact

### Phase 4: Unified Audit (Days 13-15)

**Goal:** Single timeline across all domains.

7. **Domain Events Table**
   - Create `domain_events` table
   - Add event emission to all domains
   - Add `GET /api/v1/timeline` endpoint
   - Test: Can see cross-domain timeline

---

## 9. Success Criteria

After remediation, these should work:

| Scenario | Before | After |
|----------|--------|-------|
| Budget breach | Anomaly logged only | Incident created automatically |
| Policy limit change | Analytics unaware | Analytics budget updated |
| View run | Can't see incidents | Shows incident count + link |
| View incident | Can't see cost | Shows total cost impact |
| View API key | Can't see usage | Shows cost attribution |
| Cross-domain search | Query 8 tables | Single timeline query |

---

## 10. Related Files

### Domain Engines

| File | Domain | Cross-Domain Writes |
|------|--------|---------------------|
| `incident_engine.py` | Incidents | Writes: incidents, aos_traces |
| `policy_violation_service.py` | Policies | Writes: prevention_records |
| `cost_anomaly_detector.py` | Analytics | Writes: cost_anomalies (no incident) |
| `cost_write_service.py` | Analytics | Writes: cost_records |

### API Routes

| File | Domain | Cross-Domain Reads |
|------|--------|-------------------|
| `activity.py` | Activity | Reads: runs only |
| `incidents.py` | Incidents | Reads: incidents, runs |
| `policies.py` | Policies | Reads: rules, limits |
| `cost_intelligence.py` | Analytics | Reads: cost_records |

### Models

| File | Tables | Missing FKs |
|------|--------|-------------|
| `worker_runs.py` | runs | incident_ids |
| `incident.py` | incidents | ✓ has source_run_id |
| `cost_records.py` | cost_records | incident_id, api_key_id |
| `cost_anomalies.py` | cost_anomalies | incident_id (exists, not populated) |

---

## 11. Overall Assessment

| Aspect | Grade | Notes |
|--------|-------|-------|
| **Activity ↔ Incidents** | C | One-way only |
| **Policies ↔ Incidents** | B | Works for suppression |
| **Analytics ↔ Incidents** | F | **Completely siloed** |
| **Policies ↔ Analytics** | F | **No sync** |
| **Connectivity ↔ Analytics** | F | **No integration** |
| **Activity ↔ Logs** | C | Partial linking |
| **Overview aggregation** | B | Correct pattern |
| **Accounts scoping** | A | Enforced everywhere |

**Overall Integration Maturity: 55%**

**Critical Finding:** The system is operationally functional but analytically fragmented. Operators can perform domain tasks but cannot correlate cross-domain cause-and-effect. Budget breaches don't create incidents. Policies and Analytics maintain separate budget truths. API key costs are invisible.

**Recommendation:** Implement Phase 1 (5 days) to close critical gaps, then Phase 2 (3 days) for bidirectional activity linking. This achieves ~80% integration maturity for 8 days of effort.
