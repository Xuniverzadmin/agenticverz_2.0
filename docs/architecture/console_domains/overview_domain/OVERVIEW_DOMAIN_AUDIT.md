# Overview Domain Audit

**Status:** FULLY INTEGRATED — Activity/Policies candidates plugged in
**Last Updated:** 2026-01-22
**Reference:** PIN-411 (Unified Facades), PIN-463 (L4 Facade Pattern)

---

## Architecture Pattern

This domain follows the **L4 Facade Pattern** for data access:

| Layer | File | Role |
|-------|------|------|
| L2 API | `backend/app/api/aos_overview.py` | HTTP handling, response formatting |
| L4 Facade | `backend/app/services/overview_facade.py` | Business logic, tenant isolation |

**Data Flow:** `L1 (UI) → L2 (API) → L4 (Facade) → L6 (Database)`

**Key Rules:**
- L2 routes delegate to L4 facade (never direct SQL)
- Facade returns typed dataclasses (never ORM models)
- All operations are tenant-scoped
- Overview is PROJECTION-ONLY (aggregates from other domains)

**Full Reference:** [PIN-463: L4 Facade Architecture Pattern](../../memory-pins/PIN-463-l4-facade-architecture-pattern.md), [LAYER_MODEL.md](../LAYER_MODEL.md)

---

> **INTEGRATION COMPLETE (2026-01-17):**
> - ✅ Removed 4 wrong capabilities (cost breakdowns → Analytics, feedback → internal ops)
> - ✅ Fixed 2 wrongly bound capabilities (decisions_list, cost_summary)
> - ✅ Plugged Activity candidates: `live_runs`, `queued_runs` into `/highlights`
> - ✅ Plugged Policies candidates: `policy_breaches` into `/highlights`
> - ✅ Added Activity domain to `domain_counts` in highlights response

---

## 0. Domain Characteristics

> **Overview is a DERIVED STATE domain.**
> It owns NO tables. It computes/aggregates data from other domains.

**Question Overview Answers:** "Is the system okay right now?"

**Object Family:**
- Status (computed)
- Health (derived)
- Pulse (aggregated)

**Architecture Rule:**
- Overview is PROJECTION-ONLY (no owned tables)
- All data derived from Activity, Incidents, Policies, Logs domains
- Read-only queries, no mutations

---

## 0.1 CONSTITUTIONAL PRINCIPLE: Derived State with Domain Lineage

> **Overview does NOT operate in silo.**
> Every piece of data shown in Overview MUST have clear lineage to a navigable sidebar domain.

### The Principle

Overview is a **projection layer** that aggregates state from other domains. It must:

1. **Link back to source domains** - Every metric must trace to a sidebar domain
2. **Enable drill-through** - Users must be able to navigate to the source domain for details
3. **Not provide discrete info** - No standalone data that exists only in Overview
4. **Maintain traceability** - The lineage path must be documented and navigable

### Navigable Sidebar Domains (Source of Truth)

Per Customer Console v1 Constitution:

| Domain | Question | Can Overview Derive From? |
|--------|----------|---------------------------|
| **Activity** | "What ran / is running?" | ✅ YES (runs, costs, executions) |
| **Incidents** | "What went wrong?" | ✅ YES (active incidents, severity) |
| **Policies** | "How is behavior defined?" | ✅ YES (proposals, limits, breaches) |
| **Logs** | "What is the raw truth?" | ✅ YES (audit_ledger, traces) |
| **Analytics** | "How much am I spending?" | ✅ YES (cost summaries - not breakdowns) |
| **Account** | "Who am I?" | ⚠️ INDIRECT (tenant context only) |
| **Connectivity** | "How does system connect?" | ⚠️ INDIRECT (integration status only) |

### Anti-Pattern: Discrete Info Without Domain

**FORBIDDEN:** Overview endpoints that show data users cannot drill into:

```
❌ /overview/feedback → Links to pattern_feedback table
   But "Feedback" is NOT a sidebar domain
   User cannot navigate to Feedback domain for details
   This is DISCRETE info with no domain lineage
```

**REQUIRED:** If Overview shows a metric, user must be able to:
1. See the summary in Overview
2. Click to navigate to the source domain
3. See the detailed items that produced that metric

### Lineage Documentation Requirement

Every Overview endpoint MUST document:
- Source table(s) queried
- Source domain(s) that own those tables
- Navigation path for drill-through

---

## 0.2 Domain Lineage Audit (2026-01-17)

### Endpoint Lineage Matrix

| Endpoint | Tables Queried | Source Domain | Drill-Through | Status |
|----------|----------------|---------------|---------------|--------|
| `/highlights` | incidents, policy_proposals, limit_breaches, audit_ledger | Incidents, Policies, Logs | ✅ All navigable | **PASS** |
| `/decisions` | incidents, policy_proposals | Incidents, Policies | ✅ Links to source | **PASS** |
| `/decisions/count` | incidents, policy_proposals | Incidents, Policies | ✅ Links to `/decisions` | **PASS** |
| `/costs` | worker_runs, limits, limit_breaches | Activity, Policies | ✅ Links to Activity/Policies | **PASS** |
| `/recovery-stats` | incidents | Incidents | ✅ Links to Incidents | **PASS** |
| ~~/feedback~~ | ~~pattern_feedback~~ | ~~No domain~~ | ~~No drill-through~~ | **REMOVED** |

**Note:** `/feedback` was removed (2026-01-17) - `pattern_feedback` is internal operations data. See Section 0.3.

---

## 0.3 GOVERNANCE BLOCK: pattern_feedback is Internal Operations

> **RESOLVED (2026-01-17):** `/feedback` endpoint REMOVED from Overview.
> `pattern_feedback` is internal operations data, NOT customer-facing.

### Decision Record

| Item | Value |
|------|-------|
| **Date** | 2026-01-17 |
| **Table** | `pattern_feedback` |
| **Classification** | Internal Operations |
| **Customer Domain** | NONE (not exposed to customers) |
| **Reason** | No navigable sidebar domain for drill-through |

### What pattern_feedback Contains

`pattern_feedback` stores **system-detected patterns** (failure patterns, cost spikes):
- `pattern_type`: failure_pattern, cost_spike, etc.
- `severity`: info, warning, critical
- `is_helpful`: internal operations feedback on pattern quality
- `provenance`: links to source runs (internal reference)

This is **NOT CRM feedback** (customer satisfaction, support tickets).
This is **internal operations data** for system pattern detection.

### Ownership

| Aspect | Value |
|--------|-------|
| **Table** | `pattern_feedback` |
| **Layer** | L6 Platform Substrate |
| **Owner** | Internal Operations / Ops Console |
| **Customer Visibility** | NONE |
| **Overview Linkage** | FORBIDDEN |

### Governance Block (ENFORCED)

**RULE: OVR-LINEAGE-001 — No Internal Ops in Overview**

> Overview MUST NOT expose internal operations data that has no
> customer-navigable domain.

**Blocked Tables:**
- `pattern_feedback` — internal pattern detection
- Any future `*_internal`, `*_ops`, `*_system` tables

**Enforcement:**
- Code review must reject Overview endpoints querying blocked tables
- BLCA should flag `pattern_feedback` imports in `overview.py`

**If pattern feedback needs customer exposure:**
1. Create a proper domain (or assign to existing domain like Policies)
2. Add sidebar navigation
3. THEN and ONLY THEN can Overview aggregate from it

---

## 1. Panel Questions (11 Panels across 3 Topics)

### Panel Coverage Summary (2026-01-17)

```
Total Panels:           11
├── FILLED (Overview):   7  (64%)
├── ANALYTICS domain:    3  (27%) - Cost breakdowns belong in Analytics
└── REMOVED:             1  (9%)  - Internal ops, no domain lineage
```

### SUMMARY Subdomain

#### HIGHLIGHTS Topic (System Health Overview) — 3/3 FILLED ✅

| O-Level | Panel ID | Panel Question | Status | Endpoint |
|---------|----------|----------------|--------|----------|
| O1 | OVR-SUM-HL-O1 | What is the current system activity level? | ✅ **FILLED** | `/highlights` → pulse.live_runs, queued_runs, domain_counts |
| O2 | OVR-SUM-HL-O2 | What non-ignorable signals require human attention? | ✅ **FILLED** | `/highlights` → pulse (incidents, breaches, decisions) |
| O4 | OVR-SUM-HL-O4 | What policy decisions are pending? | ✅ **FILLED** | `/highlights` + `/decisions` |

#### COST_INTELLIGENCE Topic (Financial Posture) — 1/4 FILLED (3 → Analytics)

| O-Level | Panel ID | Panel Question | Status | Notes |
|---------|----------|----------------|--------|-------|
| O1 | OVR-SUM-CI-O1 | What is our current spend posture? | ✅ **FILLED** | `/costs` → totals, limits, violations |
| O2 | OVR-SUM-CI-O2 | Which features are driving costs? | → **ANALYTICS** | `/analytics/statistics/cost` → by_feature |
| O3 | OVR-SUM-CI-O3 | Cost details by model? | → **ANALYTICS** | `/analytics/statistics/cost` → by_model |
| O4 | OVR-SUM-CI-O4 | What cost anomalies exist? | → **ANALYTICS** | `/cost/anomalies` |

#### DECISIONS Topic (Action Queue) — 3/4 FILLED (1 REMOVED)

| O-Level | Panel ID | Panel Question | Status | Endpoint |
|---------|----------|----------------|--------|----------|
| O1 | OVR-SUM-DC-O1 | What decisions require human approval/rejection? | ✅ **FILLED** | `/decisions` |
| O2 | OVR-SUM-DC-O2 | How many decisions pending? | ✅ **FILLED** | `/decisions/count` |
| O3 | OVR-SUM-DC-O3 | Recovery statistics? | ✅ **FILLED** | `/recovery-stats` |
| O4 | OVR-SUM-DC-O4 | Feedback summary? | ❌ **REMOVED** | Internal ops (OVR-LINEAGE-001) |

---

## 2. Capability Registry

**Total Active Capabilities:** 10
**Working (Correctly Bound):** 7 OBSERVED + 3 DECLARED
**Deprecated (Moved to LEGACY_DEPRECATED):** 4

### 2.1 Active Capabilities (2026-01-17)

| Capability | Registry Endpoint | Status | Domain Lineage |
|------------|-------------------|--------|----------------|
| `overview.activity_snapshot` | `/api/v1/activity/summary` | OBSERVED | → Activity |
| `overview.incident_snapshot` | `/api/v1/incidents/summary` | OBSERVED | → Incidents |
| `overview.policy_snapshot` | `/api/v1/policy-proposals/stats/summary` | OBSERVED | → Policies |
| `overview.decisions_list` | `/api/v1/overview/decisions` | OBSERVED | → Incidents, Policies |
| `overview.decisions_count` | `/api/v1/overview/decisions/count` | OBSERVED | → Incidents, Policies |
| `overview.cost_summary` | `/api/v1/overview/costs` | OBSERVED | → Analytics (cost totals) |
| `overview.recovery_stats` | `/api/v1/overview/recovery-stats` | OBSERVED | → Incidents |
| **`overview.live_runs`** | `/api/v1/overview/highlights` | **DECLARED** | → Activity (worker_runs) |
| **`overview.queued_runs`** | `/api/v1/overview/highlights` | **DECLARED** | → Activity (worker_runs) |
| **`overview.policy_breaches`** | `/api/v1/overview/highlights` | **DECLARED** | → Policies (limit_breaches) |

### 2.2 Removed Capabilities (2026-01-17)

**Moved to:** `backend/AURORA_L2_CAPABILITY_REGISTRY/LEGACY_DEPRECATED/`

| Capability | Reason | Correct Owner |
|------------|--------|---------------|
| `overview.cost_by_feature` | Detailed cost breakdown | **Analytics** domain |
| `overview.cost_by_model` | Detailed cost breakdown | **Analytics** domain |
| `overview.cost_anomalies` | Cost anomaly detection | **Analytics** domain |
| `overview.feedback_summary` | Internal ops data | **Ops Console** (no customer domain) |

### 2.3 Binding Corrections Applied (2026-01-17)

| Capability | Before | After |
|------------|--------|-------|
| `overview.decisions_list` | `/fdr/timeline/decisions` | `/api/v1/overview/decisions` |
| `overview.cost_summary` | `/cost/summary` | `/api/v1/overview/costs` |

---

## 3. L4 Domain Facade

**File:** `backend/app/services/overview_facade.py`
**Getter:** `get_overview_facade()` (singleton)

The Overview Facade is the single entry point for all overview aggregation logic. L2 API routes
must call facade methods rather than implementing inline SQL queries.

**Pattern:**
```python
from app.services.overview_facade import get_overview_facade

facade = get_overview_facade()
result = await facade.get_highlights(session, tenant_id)
```

**Operations Provided:**
- `get_highlights()` - System pulse & domain counts (O1, O2)
- `get_decisions()` - Pending decisions queue (O1)
- `get_decisions_count()` - Decisions count summary
- `get_cost_summary()` - Cost intelligence summary
- `get_recovery_stats()` - Recovery statistics (O3)

**Architectural Rules:**
- Overview is PROJECTION-ONLY (no owned tables)
- All data derived from Activity, Incidents, Policies, Logs
- L2 routes call facade methods, never direct SQL
- Facade returns typed dataclass results
- All operations are read-only

---

## 4. API Routes (Actual Overview Facade)

### Primary Facade: `/api/v1/overview/*`

**File:** `backend/app/api/overview.py`

| Endpoint | Method | Returns | Serves Topic | Domain Lineage |
|----------|--------|---------|--------------|----------------|
| `/api/v1/overview/highlights` | GET | SystemPulse, DomainCounts | HIGHLIGHTS | Incidents, Policies, Logs |
| `/api/v1/overview/decisions` | GET | DecisionItems list | DECISIONS | Incidents, Policies |
| `/api/v1/overview/decisions/count` | GET | Decision counts by domain/priority | DECISIONS | Incidents, Policies |
| `/api/v1/overview/costs` | GET | CostActuals, Limits, Violations | COST_INTELLIGENCE | Activity, Policies |
| `/api/v1/overview/recovery-stats` | GET | Recovery statistics | DECISIONS | Incidents |

### 3.1 GET /api/v1/overview/highlights

**Response Model:** `HighlightsResponse`

```
{
  "pulse": {
    "status": "HEALTHY|DEGRADED|BLOCKED",
    "active_incidents": int,
    "pending_decisions": int,
    "recent_breaches": int
  },
  "domain_counts": [
    {"domain": "Incidents", "total": int, "pending": int, "critical": int},
    {"domain": "Policies", "total": int, "pending": int, "critical": int}
  ],
  "last_activity_at": datetime
}
```

**Derived From:**
- `incidents` table → active incident count, critical count
- `policy_proposals` table → pending proposal count
- `limit_breaches` table → recent breach count
- `audit_ledger` table → last activity timestamp

### 3.2 GET /api/v1/overview/decisions

**Query Params:**
- `source_domain`: INCIDENT | POLICY
- `priority`: CRITICAL | HIGH | MEDIUM | LOW
- `limit`: int (default 50)
- `offset`: int

**Response Model:** `DecisionsResponse`

```
{
  "items": [
    {
      "source_domain": "INCIDENT|POLICY",
      "entity_type": string,
      "entity_id": string,
      "decision_type": string,
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "summary": string,
      "created_at": datetime
    }
  ],
  "total": int,
  "has_more": bool,
  "filters_applied": dict
}
```

**Derived From:**
- `incidents` table → ACTIVE incidents needing acknowledgement
- `policy_proposals` table → DRAFT proposals needing approval

### 3.3 GET /api/v1/overview/costs

**Query Params:**
- `period_days`: int (default 30)

**Response Model:** `CostsResponse`

```
{
  "currency": "USD",
  "period": {"start": datetime, "end": datetime},
  "actuals": {"llm_run_cost": float},
  "limits": [
    {"limit_id": string, "name": string, "budget": float, "spent": float, "status": "OK|NEAR_THRESHOLD|BREACHED"}
  ],
  "violations": {"breach_count": int, "total_overage": float}
}
```

**Derived From:**
- `worker_runs` table → SUM(cost_cents) for period
- `limits` table → budget limits
- `limit_breaches` table → breach events

### 3.4 GET /api/v1/overview/decisions/count

**Response Model:** `DecisionsCountResponse`

```
{
  "total": int,
  "by_domain": {"INCIDENT": int, "POLICY": int},
  "by_priority": {"CRITICAL": int, "HIGH": int, "MEDIUM": int, "LOW": int}
}
```

**Derived From:**
- `incidents` table → ACTIVE incidents by severity
- `policy_proposals` table → DRAFT proposals count

### 3.5 GET /api/v1/overview/recovery-stats

**Query Params:**
- `period_days`: int (default 30)

**Response Model:** `RecoveryStatsResponse`

```
{
  "total_incidents": int,
  "recovered": int,
  "pending_recovery": int,
  "failed_recovery": int,
  "recovery_rate_pct": float,
  "period": {"start": datetime, "end": datetime}
}
```

**Derived From:**
- `incidents` table → lifecycle_state counts (RESOLVED, ACTIVE, failed)

---

## 4. Derived State Computation

### 4.1 Source Domains

Overview aggregates from **5 source domains**:

| Source | Table | Metrics Derived |
|--------|-------|-----------------|
| **Activity** | `worker_runs` | Cost totals, execution counts |
| **Incidents** | `incidents` | Active count, severity breakdown |
| **Policies** | `policy_proposals` | Pending approvals, draft count |
| **Limits** | `limits`, `limit_breaches` | Budget status, violations |
| **Logs** | `audit_ledger` | Last activity timestamp |

### 4.2 Computation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  REQUEST: GET /overview/highlights          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              1. Extract tenant_id from auth_context         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              2. Query Multiple Domain Tables                │
│                                                             │
│   SELECT COUNT(*) FROM incidents WHERE lifecycle_state='ACTIVE'
│   SELECT COUNT(*) FROM policy_proposals WHERE status='draft'
│   SELECT COUNT(*) FROM limit_breaches WHERE created_at > -24h
│   SELECT MAX(created_at) FROM audit_ledger                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              3. Compute Derived Metrics                     │
│                                                             │
│   - pulse.status = BLOCKED if critical incidents > 0        │
│   - pulse.status = DEGRADED if any incidents               │
│   - pulse.status = HEALTHY otherwise                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              4. Project into Response Model                 │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 No Caching

All Overview queries are computed on-demand:
- No materialized views
- No caching layer
- Real-time aggregation from source tables

---

## 5. Derived Signals (Customer-Visible)

> **NOTE:** GovernanceSignalService, PlatformHealthService, and HealthProbe are
> **internal ops/meta layer** concerns (Ops/Founder consoles). They do NOT belong
> in the customer-facing Overview domain.

### Customer Overview Signals (What Should Be Here)

Customer Overview should derive signals from **customer data only**:

| Signal | Source | Computation |
|--------|--------|-------------|
| Activity pulse | `worker_runs` | Count of RUNNING, FAILED in window |
| Incident severity | `incidents` | MAX(severity) of ACTIVE incidents |
| Policy backlog | `policy_proposals` | Count of DRAFT proposals |
| Cost health | `limits`, `limit_breaches` | Any BREACHED limits? |
| System calm | `worker_runs` | No activity in X minutes |

### What Does NOT Belong Here

| Service | Why Not Customer Concern |
|---------|-------------------------|
| `GovernanceSignalService` | BLCA, CI status = internal ops |
| `PlatformHealthService` | Platform infrastructure health = ops console |
| `HealthProbe` | DB/Redis connectivity = ops console |

These belong in **Ops Console** or **Founder Console**, not customer Overview.

---

## 6. Coverage Summary (2026-01-17 — FULLY INTEGRATED)

```
Active Overview Capabilities:   10 (7 OBSERVED + 3 DECLARED)
Deprecated Capabilities:        4  (moved to LEGACY_DEPRECATED)
Capability Binding Issues:      0  ← RESOLVED

Overview-specific endpoints:    5/5 (100%)
  - /highlights:                ✅ IMPLEMENTED (system pulse + domain counts)
                                   → NOW includes: live_runs, queued_runs (Activity)
                                   → NOW includes: Activity domain count
                                   → NOW includes: policy_breaches in Policies critical
  - /decisions:                 ✅ IMPLEMENTED (pending decisions queue)
  - /decisions/count:           ✅ IMPLEMENTED (counts by domain/priority)
  - /costs:                     ✅ IMPLEMENTED (cost totals + limit status)
  - /recovery-stats:            ✅ IMPLEMENTED (incident recovery stats)

Domain Coverage:
  - Activity:   ✅ live_runs, queued_runs, total runs
  - Incidents:  ✅ active_incidents, recovery_stats
  - Policies:   ✅ pending_decisions, recent_breaches
  - Analytics:  ✅ cost totals (via /costs endpoint)

Domain Lineage:                 100% compliant
  - All endpoints have drill-through to navigable sidebar domains
  - No discrete info without domain linkage
  - Internal ops data (pattern_feedback) excluded

NOTE: Cost breakdowns (by-model, by-feature), anomalies belong in ANALYTICS domain.
See docs/contracts/ANALYTICS_DOMAIN_CONSTITUTION.md
```

---

## 7. Fix Status (2026-01-17)

### 7.1 Completed Fixes ✅

| Fix | Capability | Action | Status |
|-----|------------|--------|--------|
| **F1** | `overview.decisions_list` | Rebound to `/api/v1/overview/decisions` | ✅ DONE |
| **F2** | `overview.cost_summary` | Rebound to `/api/v1/overview/costs` | ✅ DONE |
| **F3** | `overview.cost_by_feature` | Moved to LEGACY_DEPRECATED (Analytics owns) | ✅ DONE |
| **F4** | `overview.cost_by_model` | Moved to LEGACY_DEPRECATED (Analytics owns) | ✅ DONE |
| **F5** | `overview.cost_anomalies` | Moved to LEGACY_DEPRECATED (Analytics owns) | ✅ DONE |
| **F6** | `overview.feedback_summary` | Moved to LEGACY_DEPRECATED (internal ops) | ✅ DONE |

### 7.2 Endpoints by Domain Ownership (Clarified)

| Capability | Domain Owner | Endpoint | Rationale |
|------------|--------------|----------|-----------|
| `overview.cost_summary` | **Overview** | `/api/v1/overview/costs` | "Is the system okay?" needs cost health |
| `analytics.cost.by_model` | **Analytics** | `/api/v1/analytics/statistics/cost` | "How much am I spending?" |
| `analytics.cost.by_feature` | **Analytics** | `/api/v1/analytics/statistics/cost` | "How much am I spending?" |
| `analytics.cost.anomalies` | **Analytics** | `/api/v1/cost/anomalies` | "What patterns exist?" |

### 7.3 Future Signal Integration

| Signal | Purpose | Source |
|--------|---------|--------|
| Health score signal | Persist health state transitions | `PlatformHealthService` |
| Activity calm signal | Indicate quiet system periods | Activity monitoring |

---

## 8. Panel Coverage Matrix

| Panel | Question | Capability | Route | Derivation | Status |
|-------|----------|------------|-------|------------|--------|
| HL-O1 | Activity level? | `overview.activity_snapshot` | `/overview/highlights` | `worker_runs` count | **PARTIAL** |
| HL-O2 | Attention signals? | `overview.incident_snapshot` | `/overview/highlights` | `incidents` active | **PARTIAL** |
| HL-O4 | Policy pending? | `overview.policy_snapshot` | `/overview/decisions` | `policy_proposals` draft | **PARTIAL** |
| CI-O1 | Spend posture? | `overview.cost_summary` | `/overview/costs` | `worker_runs` cost | **WRONG CAP** |
| CI-O2 | Cost by feature? | `analytics.cost.by_feature` | `/analytics/statistics/cost` | Analytics domain | ✅ **ANALYTICS** |
| CI-O3 | Cost by model? | `analytics.cost.by_model` | `/analytics/statistics/cost` | Analytics domain | ✅ **ANALYTICS** |
| CI-O4 | Cost anomalies? | `analytics.cost.anomalies` | `/cost/anomalies` | Analytics domain | ✅ **ANALYTICS** |
| DC-O1 | Decisions queue? | `overview.decisions_list` | `/overview/decisions` | Incidents + Proposals | **WRONG CONSOLE** |
| DC-O2 | Decisions count? | `overview.decisions_count` | `/overview/decisions/count` | `incidents` + `policy_proposals` | ✅ **DONE** |
| DC-O3 | Recovery stats? | `overview.recovery_stats` | `/overview/recovery-stats` | `incidents` lifecycle | ✅ **DONE** |
| DC-O4 | Feedback summary? | `overview.feedback_summary` | `/overview/feedback` | `pattern_feedback` | ✅ **DONE** |

---

## 9. Related Files

| File | Purpose |
|------|---------|
| `backend/app/api/overview.py` | Unified overview facade (L2) |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_overview.*.yaml` | Capabilities |
| `design/l2_1/intents/AURORA_L2_INTENT_OVR-*.yaml` | Panel intents |

**Source Tables (Read-Only):**
| Table | Domain | What Overview Reads |
|-------|--------|---------------------|
| `worker_runs` | Activity | Execution counts, costs |
| `incidents` | Incidents | Active count, severity |
| `policy_proposals` | Policies | Pending approvals |
| `limits`, `limit_breaches` | Policies | Budget status |
| `audit_ledger` | Logs | Last activity timestamp |

---

## 10. Architecture Notes

### Overview Domain Question
> "Is the system okay right now?"

### Derived State Pattern
Overview computes answers by aggregating from:
1. **Activity** → execution counts, costs
2. **Incidents** → failure counts, severity
3. **Policies** → pending decisions, violations
4. **Logs** → last activity timestamp

### No Owned Tables
Overview MUST NOT create its own tables. All data is projected from other domains.

### Domain Lineage Requirement (Constitutional)

> **Overview does NOT operate in silo.**
> Every metric shown MUST link to a navigable sidebar domain.

This means:
- If Overview shows "50 active incidents" → user can click to Incidents domain
- If Overview shows "3 pending proposals" → user can click to Policies domain
- If Overview shows "feedback count" → user MUST be able to drill into source domain

**Anti-pattern:** Showing discrete info that exists only in Overview with no drill-through path.

### Real-Time Computation
No caching. Every request queries source tables directly.

### Health State Machine
```
HEALTHY ──(incident)──> DEGRADED ──(critical)──> BLOCKED
   ↑                        │                        │
   └──────(resolved)────────┴──────(resolved)────────┘
```

---

## 11. Implementation Status (What's Actually Built)

**Date:** 2026-01-17

### Summary

| Component | Status | Notes |
|-----------|--------|-------|
| `/api/v1/overview/highlights` | ✅ IMPLEMENTED | Aggregates incidents, policies, breaches |
| `/api/v1/overview/decisions` | ✅ IMPLEMENTED | Lists pending decisions |
| `/api/v1/overview/decisions/count` | ✅ IMPLEMENTED (2026-01-17) | Counts by domain/priority |
| `/api/v1/overview/costs` | ✅ IMPLEMENTED | Cost totals and limit status |
| `/api/v1/overview/recovery-stats` | ✅ IMPLEMENTED (2026-01-17) | Recovery statistics |
| ~~/api/v1/overview/feedback~~ | ❌ REMOVED (2026-01-17) | Internal ops data - see Section 0.3 |
| Customer pulse signal | ❌ NOT IMPLEMENTED | Needs derivation logic |

### API Implementation Details

**`/api/v1/overview/highlights`** - WORKING
- Queries: incidents, policy_proposals, limit_breaches, audit_ledger
- Returns: SystemPulse with status, counts, last_activity_at

**`/api/v1/overview/decisions`** - WORKING
- Queries: incidents (ACTIVE), policy_proposals (DRAFT)
- Returns: List of decision items with priority

**`/api/v1/overview/decisions/count`** - WORKING (NEW 2026-01-17)
- Queries: incidents (ACTIVE by severity), policy_proposals (DRAFT)
- Returns: Total count, by_domain dict, by_priority dict

**`/api/v1/overview/costs`** - WORKING
- Queries: worker_runs, limits, limit_breaches
- Returns: Actuals, limits status, violations

**`/api/v1/overview/recovery-stats`** - WORKING (NEW 2026-01-17)
- Queries: incidents (lifecycle_state)
- Returns: total, recovered, pending, failed counts + recovery_rate_pct

**~~/api/v1/overview/feedback~~** - ❌ REMOVED (2026-01-17)
- **Was:** Queried pattern_feedback (is_helpful)
- **Removed because:** `pattern_feedback` is internal operations data
- **No customer domain:** Users cannot drill through to see details
- **Governance:** See Section 0.3 (OVR-LINEAGE-001)

### Domain Separation Clarification

**Cost breakdowns belong in Analytics, not Overview:**
- Cost by-model: `/api/v1/analytics/statistics/cost` → `by_model` in response
- Cost by-feature: `/api/v1/analytics/statistics/cost` → `by_feature` in response
- Cost anomalies: `/api/v1/cost/anomalies`

See: `docs/contracts/ANALYTICS_DOMAIN_CONSTITUTION.md`

### Capability Binding Status ✅ CLEAN

All Overview capabilities are now correctly bound (2026-01-17):

| Capability | Binding | Status |
|------------|---------|--------|
| `overview.decisions_list` | `/api/v1/overview/decisions` | ✅ CORRECT |
| `overview.cost_summary` | `/api/v1/overview/costs` | ✅ CORRECT |
| `overview.decisions_count` | `/api/v1/overview/decisions/count` | ✅ CORRECT |
| `overview.recovery_stats` | `/api/v1/overview/recovery-stats` | ✅ CORRECT |

**Deprecated capabilities moved to LEGACY_DEPRECATED:**
- `overview.cost_by_feature` → Analytics domain owns
- `overview.cost_by_model` → Analytics domain owns
- `overview.cost_anomalies` → Analytics domain owns
- `overview.feedback_summary` → Internal ops (no customer domain)

---

## 12. Activity/Policies Domain Integration (2026-01-17) ✅ COMPLETED

### 12.1 Activity Domain → Overview (IMPLEMENTED)

| Capability | Source | Exposed In | Status |
|------------|--------|------------|--------|
| `activity.summary` | `/api/v1/activity/summary` | `overview.activity_snapshot` | ✅ OBSERVED |
| **`overview.live_runs`** | `worker_runs.status='running'` | `/highlights` → `pulse.live_runs` | ✅ DECLARED |
| **`overview.queued_runs`** | `worker_runs.status='queued'` | `/highlights` → `pulse.queued_runs` | ✅ DECLARED |

**Implementation:** The `/overview/highlights` endpoint now queries `worker_runs` table for:
- `live_runs`: COUNT where status='running'
- `queued_runs`: COUNT where status='queued'

Both metrics are included in the `SystemPulse` response and the Activity `DomainCount`.

### 12.2 Policies Domain → Overview (IMPLEMENTED)

| Capability | Source | Exposed In | Status |
|------------|--------|------------|--------|
| `policies.proposals_summary` | `/api/v1/policy-proposals/stats/summary` | `overview.policy_snapshot` | ✅ OBSERVED |
| **`overview.policy_breaches`** | `limit_breaches` (last 24h) | `/highlights` → `pulse.recent_breaches` | ✅ DECLARED |

**Implementation:** The `/overview/highlights` endpoint already queried `limit_breaches` for recent breaches.
This is now formally registered as `overview.policy_breaches` capability with proper domain lineage.

### 12.3 Updated SystemPulse Response

```json
{
  "pulse": {
    "status": "HEALTHY|ATTENTION_NEEDED|CRITICAL",
    "active_incidents": 0,
    "pending_decisions": 0,
    "recent_breaches": 0,
    "live_runs": 0,      // NEW: from Activity domain
    "queued_runs": 0     // NEW: from Activity domain
  },
  "domain_counts": [
    {"domain": "Activity", "total": 100, "pending": 5, "critical": 0},    // NEW
    {"domain": "Incidents", "total": 10, "pending": 2, "critical": 1},
    {"domain": "Policies", "total": 25, "pending": 3, "critical": 2}
  ],
  "last_activity_at": "2026-01-17T12:00:00Z"
}
```

### 12.4 What Overview Should NOT Derive From

| Capability | Domain | Why Not Overview |
|------------|--------|------------------|
| Cost breakdowns (by-model, by-feature) | Analytics | "Where is spend going?" = Analytics question |
| Cost anomalies | Analytics | Pattern detection = Analytics question |
| Internal feedback | (None) | No customer domain for drill-through |
| Raw logs | Logs | Detail level, not summary |
| Audit trails | Logs | Detail level, not summary |
