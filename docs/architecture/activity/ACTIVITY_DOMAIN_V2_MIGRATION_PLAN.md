# Activity Domain V2 Migration Plan

**Status:** PHASE 3 COMPLETE
**Created:** 2026-01-19
**Last Updated:** 2026-01-19
**Reference:** PIN-445 (Incidents V2 Pattern), Activity Domain Audit

---

## Executive Summary

Migrate Activity domain from query-param-based topic filtering to endpoint-scoped topic boundaries with integrated policy context.

**Key Changes:**
- **Before:** Generic `/runs` endpoint with caller-controlled `?state=` filtering
- **After:** Topic-scoped endpoints: `/live`, `/completed`, `/signals` with policy context

---

## Design Principles (Locked)

1. **Topics are boundaries, not filters**
2. **SIGNALS is a projection layer, not a lifecycle state**
3. **Policy context is mandatory, not optional metadata**
4. **No new tables unless ROI > schema cost**
5. **SDSR first, implementation second**
6. **Capabilities remain DECLARED until SDSR passes**

---

## Topic Model

| Topic | Meaning | Data Nature | Endpoint |
|-------|---------|-------------|----------|
| LIVE | Runs currently executing | Volatile, real-time | `/activity/live` |
| COMPLETED | Finished runs | Immutable, historical | `/activity/completed` |
| SIGNALS | Attention & intelligence | Synthesized projection | `/activity/signals` |

**Critical:** SIGNALS is NOT a run state. It is a projection over LIVE + COMPLETED.

---

## Canonical Facade Shape

```
/api/v1/activity
├── /live                    (NEW - topic-scoped)
├── /completed               (NEW - topic-scoped)
├── /signals                 (NEW - projection)
├── /metrics                 (EXTEND from /risk-signals)
├── /threshold-signals       (NEW - granular limit tracking)
├── /live/by-dimension       (EXISTS - keep)
├── /completed/by-dimension  (EXISTS - keep)
├── /patterns                (EXISTS - rebind to SIGNALS)
├── /cost-analysis           (EXISTS - rebind to SIGNALS)
├── /attention-queue         (EXISTS - rebind to SIGNALS)
└── /runs                    (DEPRECATED - lock)
```

---

## Policy Context Integration

### Canonical Shape

Every Activity response that returns runs or signals MUST include:

```json
{
  "policy_context": {
    "policy_id": "lim-123",
    "policy_name": "Default Cost Guard",
    "policy_scope": "TENANT",
    "limit_type": "COST_USD",
    "threshold_value": 1.00,
    "threshold_unit": "USD",
    "threshold_source": "TENANT_OVERRIDE",
    "evaluation_outcome": "NEAR_THRESHOLD",
    "actual_value": 0.85
  }
}
```

### Policy Resolution Order (Deterministic)

```
1. Tenant-scoped ACTIVE limit
2. Project-scoped ACTIVE limit
3. Agent-scoped ACTIVE limit
4. Provider-scoped ACTIVE limit
5. Global ACTIVE limit
6. SYSTEM_DEFAULT (virtual)
```

### Evaluation Outcomes

| Outcome | Meaning |
|---------|---------|
| OK | Run within all limits |
| NEAR_THRESHOLD | Run at 80%+ of limit |
| BREACH | Run exceeded limit |
| OVERRIDDEN | Human override applied |
| ADVISORY | System default, informational only |

---

## Phase Plan

### Phase 0: SDSR Alignment (MANDATORY FIRST) — COMPLETE

**Deliverables:**
- [x] Update INTENT_LEDGER.md: SIGNALS = projection layer
- [x] Create SDSR scenarios for policy-aware testing
- [x] Document signal projection model (not new table)
- [x] Document policy resolution order

**SDSR Scenarios Required:**
1. LIVE run @ 85% COST threshold (TENANT_OVERRIDE)
2. LIVE run @ 95% TIME threshold (SYSTEM_DEFAULT)
3. COMPLETED run with BREACH
4. COMPLETED run with OVERRIDE
5. Mixed runs for SIGNAL ranking
6. LIVE run with evidence_health=DEGRADED + policy context
7. COMPLETED run status=aborted due to policy enforcement
8. Multiple runs showing retry pattern + policy context
9. Agent with cost Z-score > 2.0 + policy context

### Phase 1: Schema Enhancement — COMPLETE

**Deliverables:**
- [x] Extend `v_runs_o2` view with policy context projection
- [x] Add `risk_type` derived column (COST | TIME | TOKENS | RATE)
- [x] Add policy JOIN to `limits` and `limit_breaches`
- [x] Verify `actor_type`, `actor_id`, `origin_system_id` passthrough

**Migration:** `107_v_runs_o2_policy_context.py`

**SQL Pattern:**
```sql
-- Policy context projection in v_runs_o2
SELECT
  r.*,
  l.id AS policy_id,
  l.name AS policy_name,
  l.scope AS policy_scope,
  l.limit_type,
  l.max_value AS threshold_value,
  CASE l.limit_type
    WHEN 'COST_USD' THEN 'USD'
    WHEN 'TOKENS_INPUT' THEN 'tokens'
    WHEN 'TOKENS_OUTPUT' THEN 'tokens'
    ELSE 'units'
  END AS threshold_unit,
  CASE l.scope
    WHEN 'GLOBAL' THEN 'SYSTEM_DEFAULT'
    ELSE 'TENANT_OVERRIDE'
  END AS threshold_source,
  COALESCE(lb.breach_type,
    CASE
      WHEN r.estimated_cost_usd >= l.max_value * 0.8 THEN 'NEAR_THRESHOLD'
      ELSE 'OK'
    END
  ) AS evaluation_outcome,
  COALESCE(lb.value_at_breach, r.estimated_cost_usd) AS actual_value
FROM runs_base r
LEFT JOIN limit_breaches lb ON r.run_id = lb.run_id
LEFT JOIN limits l ON lb.limit_id = l.id
  OR (l.tenant_id = r.tenant_id AND l.status = 'ACTIVE')
```

### Phase 2: Endpoint Addition (Additive) — COMPLETE

**Deliverables:**
- [x] `GET /activity/live` (hard-bound state=LIVE)
- [x] `GET /activity/completed` (hard-bound state=COMPLETED)
- [x] `GET /activity/signals` (projection endpoint)
- [x] Extend `/risk-signals` → `/metrics`
- [x] `GET /activity/threshold-signals` (uses risk_type)

**Endpoints Added:** `backend/app/api/activity.py` (lines 1599-1990)

**Endpoint Contracts:**

#### `/activity/live`
- Hard guarantee: `state = LIVE`
- Returns: `RunSummary[]` with `policy_context`
- Panels: LIVE-O1, LIVE-O3, LIVE-O5

#### `/activity/completed`
- Hard guarantee: `state = COMPLETED`
- Returns: `RunSummary[]` with `policy_context`
- Sorted by: `completed_at DESC`
- Panels: COMP-O2, COMP-O5

#### `/activity/signals`
- Returns: `SignalProjection[]` (NOT runs)
- Each signal MUST include `policy_context`
- Panels: SIG-O1

#### `/activity/metrics`
- Extends existing `/risk-signals`
- Adds: `live_count`, `completed_count`, `evidence_health` breakdown
- Panels: LIVE-O1, LIVE-O2, LIVE-O4, COMP-O1, COMP-O3

#### `/activity/threshold-signals`
- Returns: Runs with typed threshold proximity
- Fields: `run_id`, `limit_type`, `proximity_pct`, `policy_context`
- Panels: LIVE-O2, COMP-O4, SIG-O2

### Phase 3: Shadow Validation — COMPLETE

**Deliverables:**
- [x] Prove parity: `/activity/live` == `/runs?state=LIVE`
- [x] Prove parity: `/activity/completed` == `/runs?state=COMPLETED`
- [x] Run SDSR scenarios
- [x] Collect observation evidence

**Shadow Validation Script:** `backend/scripts/sdsr/shadow_validate_v2.py`

**Validation Checks Implemented:**
| Check | Description |
|-------|-------------|
| `parity-live` | V1/V2 parity for LIVE state |
| `parity-completed` | V1/V2 parity for COMPLETED state |
| `policy-context` | POLICY-CONTEXT-001: Non-null validation |
| `most-severe-wins` | MOST-SEVERE-WINS-001: Multi-limit resolution |
| `signals-order` | Severity ordering (BREACH > NEAR_THRESHOLD > OK) |
| `eval-time` | EVAL-TIME-001: Valid evaluation outcomes |

**Usage:**
```bash
./scripts/sdsr/run_shadow_validation.sh <tenant_id>
# OR directly:
python scripts/sdsr/shadow_validate_v2.py --database-url $DATABASE_URL --tenant-id $TENANT_ID
```

### Phase 4: Registry + Panel Rebinding

**Deliverables:**
- [ ] Update ACTIVITY_CAPABILITY_REGISTRY.yaml
- [ ] Change capability status: DECLARED → OBSERVED
- [ ] Update panel_bindings
- [ ] Update INTENT_LEDGER.md

### Phase 5: Lockdown

**Deliverables:**
- [ ] Mark `/runs` endpoint `deprecated=True`
- [ ] Add runtime warning if UI calls deprecated endpoint
- [ ] Create `scripts/preflight/check_activity_deprecation.py`
- [ ] Add to `backend/AURORA_L2_CAPABILITY_REGISTRY/REGISTRY_LOCKS.yaml`

---

## Known Gaps (To Resolve During SDSR)

### GAP-SDSR-1: Additional Scenarios Needed

| Scenario | Panel Coverage |
|----------|----------------|
| LIVE run with evidence_health=DEGRADED | LIVE-O4 |
| COMPLETED run aborted by policy | COMP-O5 |
| Retry pattern detection | SIG-O3 |
| Cost anomaly detection | SIG-O4 |

### GAP-EDGE-1: Multi-Limit Handling

**Scenario:** Run triggers both COST and TIME thresholds.

**Resolution:** `policy_context` returns the most severe evaluation. Secondary evaluations in `additional_limits: []` array (future enhancement).

### GAP-EDGE-2: Mid-Run Limit Change

**Scenario:** Admin updates threshold while run is LIVE.

**Resolution:** Evaluation uses limit value at evaluation time, not run start time. Historical value stored in `limit_breaches.limit_value`.

### GAP-PHASE2: limit_breaches Extension

**Deferred to Phase 2:** Extend `limit_breaches` table with `evaluation_type` column for full audit trail.

```sql
ALTER TABLE limit_breaches
ADD COLUMN evaluation_type VARCHAR(16)
CHECK (evaluation_type IN ('OK', 'NEAR_THRESHOLD', 'BREACH', 'OVERRIDDEN'));
```

---

## Panel → Endpoint Mapping (Final)

### LIVE Topic

| Panel | Endpoint |
|-------|----------|
| LIVE-O1 | `/activity/metrics` |
| LIVE-O2 | `/activity/threshold-signals` |
| LIVE-O3 | `/activity/live` |
| LIVE-O4 | `/activity/metrics` |
| LIVE-O5 | `/activity/live/by-dimension` |

### COMPLETED Topic

| Panel | Endpoint |
|-------|----------|
| COMP-O1 | `/activity/metrics` |
| COMP-O2 | `/activity/completed` |
| COMP-O3 | `/activity/metrics` |
| COMP-O4 | `/activity/threshold-signals` |
| COMP-O5 | `/activity/completed` |

### SIGNALS Topic

| Panel | Endpoint |
|-------|----------|
| SIG-O1 | `/activity/signals` |
| SIG-O2 | `/activity/threshold-signals` |
| SIG-O3 | `/activity/patterns` |
| SIG-O4 | `/activity/cost-analysis` |
| SIG-O5 | `/activity/attention-queue` |

---

## Success Criteria

- [ ] All 15 panels mapped to topic-scoped endpoints
- [ ] Policy context present in all run/signal responses
- [ ] SDSR scenarios pass with observation evidence
- [ ] `/runs` endpoint deprecated with CI guard
- [ ] BLCA validation: 0 violations
- [ ] Capability registry updated: all OBSERVED

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `ACTIVITY_DOMAIN_CONTRACT.md` | Policy resolution rules, signal derivation |
| `ACTIVITY_DOMAIN_AUDIT.md` | Current state analysis |
| `ACTIVITY_CAPABILITY_REGISTRY.yaml` | Capability → endpoint mapping |
| `ATTENTION_FEEDBACK_LOOP.md` | Signal acknowledge/suppress architecture |
| `PIN-445` | Incidents V2 reference pattern |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-19 | Initial migration plan created | Claude + Human |
| 2026-01-19 | Phase 1 complete: v_runs_o2 extended with policy context | Claude + Human |
| 2026-01-19 | Phase 2 complete: 5 V2 endpoints added | Claude + Human |
| 2026-01-19 | Phase 3 complete: Shadow validation script created | Claude + Human |
| 2026-01-19 | Attention Feedback Loop complete: signal ack/suppress implemented | Claude + Human |
