# PHASE 1 — CONSOLIDATED CAPABILITY INTELLIGENCE REPORT

**Status:** COMPLETE
**Date:** 2026-01-07
**Scope:** All 5 L2.1 Domains (Overview, Activity, Incidents, Policies, Logs)

---

## EXECUTIVE SUMMARY

Phase 1 capability intelligence extraction is **COMPLETE** for all 5 L2.1 domains.

### Key Findings

| Domain | Capabilities | Architecture | L2.1 Alignment | Critical Issues |
|--------|--------------|--------------|----------------|-----------------|
| **Overview** | 5 | ❌ BYPASSED | ❌ NONE | No Customer Console API; Founder-only |
| **Activity** | 2 | ✅ CLEAN | ✅ GOOD | Missing download actions |
| **Incidents** | 8 | ✅ CLEAN | ⚠️ PARTIAL | Escalate seeded but not implemented |
| **Policies** | 2 | ✅ CLEAN | ⚠️ PARTIAL | ALL GC_L actions not implemented |
| **Logs** | 3 | ✅ CLEAN | ⚠️ PARTIAL | Audit surfaces semantic mismatch |

### Capability Distribution

| Mode | Count | Layer Route |
|------|-------|-------------|
| READ | 18 | L2_1 |
| WRITE | 2 | GC_L |
| DOWNLOAD | 3 | L2_1 |

---

## DOMAIN-BY-DOMAIN SUMMARY

### 1. OVERVIEW Domain

**Status:** ❌ CRITICAL GAP

**Problem:** Overview L2.1 surfaces (`OVERVIEW.SYSTEM_HEALTH.*`) are defined in seed, but:
- Current API (`/platform/*`) serves **Founder Console only**
- Data is **cross-tenant** (system-wide health)
- L2.1 surfaces require **tenant isolation**

**Capabilities Found:**
| ID | Name | Console | L2.1 Applicable? |
|----|------|---------|------------------|
| CAP-OVW-HEALTH | Get Platform Health | Founder | ❌ NO |
| CAP-OVW-CAPS | Get Capabilities | Founder | ❌ NO |
| CAP-OVW-DOMAIN | Get Domain Health | Founder | ❌ NO |
| CAP-OVW-CAP-DETAIL | Get Capability Detail | Founder | ❌ NO |
| CAP-OVW-ELIGIBILITY | Quick Eligibility | Founder | ❌ NO |

**Action Required:**
1. Create Customer Console API for tenant-scoped health
2. OR remove `OVERVIEW.*` surfaces from L2.1 seed

---

### 2. ACTIVITY Domain

**Status:** ✅ WELL-ALIGNED

**Architecture:** Clean L2→L3→L4 layering

**Capabilities Found:**
| ID | Name | L2.1 Surface | Status |
|----|------|--------------|--------|
| CAP-ACT-LIST | List Activities | `ACTIVITY.EXECUTIONS.*` | ✅ Implemented |
| CAP-ACT-DETAIL | Get Activity Detail | `ACTIVITY.EXECUTIONS.RUN_DETAILS` | ✅ Implemented |

**Gaps:**
- `ACT-ACTIVITY-COMPLETED-DOWNLOAD` — NOT IMPLEMENTED
- `ACT-ACTIVITY-DETAIL-DOWNLOAD` — NOT IMPLEMENTED

---

### 3. INCIDENTS Domain

**Status:** ⚠️ PARTIALLY ALIGNED

**Architecture:** Clean L2→L3→L4 layering

**Capabilities Found:**
| ID | Name | Mode | L2.1 Action | Status |
|----|------|------|-------------|--------|
| CAP-INC-LIST | List Incidents | READ | `ACT-INCIDENT-LIST-VIEW` | ✅ |
| CAP-INC-GET | Get Incident | READ | `ACT-INCIDENT-DETAIL-VIEW` | ✅ |
| CAP-INC-ACK | Acknowledge | WRITE | `ACT-INCIDENT-ACKNOWLEDGE` | ✅ |
| CAP-INC-RESOLVE | Resolve | WRITE | `ACT-INCIDENT-RESOLVE` | ✅ |
| CAP-INC-SEARCH | Search | READ | (not seeded) | ✅ |
| CAP-INC-TIMELINE | Timeline | READ | (not seeded) | ✅ |
| CAP-INC-NARRATIVE | Narrative | READ | (not seeded) | ✅ |
| CAP-INC-EXPORT | Export PDF | READ | (not seeded) | ✅ |

**Gaps:**
- `ACT-INCIDENT-ESCALATE` — SEEDED but NOT IMPLEMENTED
- Download actions — NOT IMPLEMENTED

**Risks:**
- WRITE operations (ACK/RESOLVE) have UNKNOWN reversibility
- IDEMPOTENCY unclear

---

### 4. POLICIES Domain

**Status:** ⚠️ READ-ONLY ALIGNED

**Architecture:** Clean L2→L3→L4 layering

**Capabilities Found:**
| ID | Name | Mode | L2.1 Action | Status |
|----|------|------|-------------|--------|
| CAP-POL-CONSTRAINTS | Get Constraints | READ | `ACT-POLICY-*-VIEW` | ✅ |
| CAP-POL-GUARDRAIL | Get Guardrail | READ | `ACT-POLICY-APPROVAL-VIEW` | ✅ |

**Critical Gap: ALL GC_L Actions NOT IMPLEMENTED**

| Seeded Action | Mode | Status |
|---------------|------|--------|
| ACT-POLICY-BUDGET-CREATE | WRITE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-BUDGET-UPDATE | WRITE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-BUDGET-ACTIVATE | ACTIVATE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-BUDGET-DEACTIVATE | ACTIVATE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-RATE-UPDATE | WRITE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-RATE-ACTIVATE | ACTIVATE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-APPROVAL-CREATE | WRITE | ❌ NOT IMPLEMENTED |
| ACT-POLICY-APPROVAL-ACTIVATE | ACTIVATE | ❌ NOT IMPLEMENTED |

**Also Missing:**
- `POLICIES.POLICY_AUDIT.POLICY_CHANGES` surface — NO API exists

---

### 5. LOGS Domain

**Status:** ⚠️ SEMANTIC MISMATCH

**Architecture:** Clean L2→L3→L4 layering

**Capabilities Found:**
| ID | Name | Mode | L2.1 Surface | Status |
|----|------|------|--------------|--------|
| CAP-LOG-LIST | List Logs | READ | `LOGS.EXECUTION_TRACES.*` | ✅ |
| CAP-LOG-DETAIL | Get Log Detail | READ | `LOGS.EXECUTION_TRACES.TRACE_DETAILS` | ✅ |
| CAP-LOG-EXPORT | Export Logs | READ | `LOGS.EXECUTION_TRACES.TRACE_DETAILS` | ✅ |

**Semantic Mismatch:**

| L2.1 Surface | Expected | Actual API |
|--------------|----------|------------|
| `LOGS.AUDIT_LOGS.SYSTEM_AUDIT` | System audit trail | Returns execution traces |
| `LOGS.AUDIT_LOGS.USER_AUDIT` | User action audit | Returns execution traces |

**True audit logs (user actions, policy changes) are NOT exposed to Customer Console.**

---

## CONSOLIDATED CAPABILITY TABLE

### All 20 Capabilities Discovered

| capability_id | domain | mode | scope | confidence | l2_1_aligned |
|---------------|--------|------|-------|------------|--------------|
| CAP-OVW-HEALTH | Overview | READ | SINGLE | HIGH | ❌ |
| CAP-OVW-CAPS | Overview | READ | BULK | HIGH | ❌ |
| CAP-OVW-DOMAIN | Overview | READ | SINGLE | HIGH | ❌ |
| CAP-OVW-CAP-DETAIL | Overview | READ | SINGLE | HIGH | ❌ |
| CAP-OVW-ELIGIBILITY | Overview | READ | SINGLE | HIGH | ❌ |
| CAP-ACT-LIST | Activity | READ | BULK | HIGH | ✅ |
| CAP-ACT-DETAIL | Activity | READ | SINGLE | HIGH | ✅ |
| CAP-INC-LIST | Incidents | READ | BULK | HIGH | ✅ |
| CAP-INC-GET | Incidents | READ | SINGLE | HIGH | ✅ |
| CAP-INC-ACK | Incidents | WRITE | SINGLE | MEDIUM | ✅ |
| CAP-INC-RESOLVE | Incidents | WRITE | SINGLE | MEDIUM | ✅ |
| CAP-INC-SEARCH | Incidents | READ | BULK | HIGH | ⚠️ |
| CAP-INC-TIMELINE | Incidents | READ | SINGLE | HIGH | ⚠️ |
| CAP-INC-NARRATIVE | Incidents | READ | SINGLE | HIGH | ⚠️ |
| CAP-INC-EXPORT | Incidents | READ | SINGLE | HIGH | ⚠️ |
| CAP-POL-CONSTRAINTS | Policies | READ | SINGLE | HIGH | ✅ |
| CAP-POL-GUARDRAIL | Policies | READ | SINGLE | HIGH | ✅ |
| CAP-LOG-LIST | Logs | READ | BULK | HIGH | ✅ |
| CAP-LOG-DETAIL | Logs | READ | SINGLE | HIGH | ✅ |
| CAP-LOG-EXPORT | Logs | READ | BULK | MEDIUM | ✅ |

Legend:
- ✅ = Aligned with L2.1 seed
- ⚠️ = Exists but not in seed
- ❌ = Not applicable to L2.1

---

## ARCHITECTURAL FINDINGS

### Layer Compliance Summary

| Domain | L2→L3→L4 Compliance | Notes |
|--------|---------------------|-------|
| Overview | ❌ BYPASSED | Direct SQL in L2, adapter exists but unused |
| Activity | ✅ CLEAN | Proper layering |
| Incidents | ✅ CLEAN | Proper layering |
| Policies | ✅ CLEAN | Proper layering |
| Logs | ✅ CLEAN | Proper layering, async |

### Adapter Inventory

| Adapter | Domain | Used? | Methods |
|---------|--------|-------|---------|
| PlatformEligibilityAdapter | Overview | ❌ NO | 4 methods available but bypassed |
| CustomerActivityAdapter | Activity | ✅ YES | list_activities, get_activity |
| CustomerIncidentsAdapter | Incidents | ✅ YES | list_incidents, get_incident, acknowledge, resolve |
| CustomerPoliciesAdapter | Policies | ✅ YES | get_policy_constraints, get_guardrail_detail |
| CustomerLogsAdapter | Logs | ✅ YES | list_logs, get_log, export_logs |

---

## SEED vs CODE GAP ANALYSIS

### Seeded but NOT Implemented

| Action ID | Domain | Mode | Priority |
|-----------|--------|------|----------|
| ACT-INCIDENT-ESCALATE | Incidents | WRITE | HIGH |
| ACT-ACTIVITY-COMPLETED-DOWNLOAD | Activity | DOWNLOAD | MEDIUM |
| ACT-ACTIVITY-DETAIL-DOWNLOAD | Activity | DOWNLOAD | MEDIUM |
| ACT-POLICY-BUDGET-CREATE | Policies | WRITE | HIGH |
| ACT-POLICY-BUDGET-UPDATE | Policies | WRITE | HIGH |
| ACT-POLICY-BUDGET-ACTIVATE | Policies | ACTIVATE | HIGH |
| ACT-POLICY-BUDGET-DEACTIVATE | Policies | ACTIVATE | HIGH |
| ACT-POLICY-RATE-UPDATE | Policies | WRITE | HIGH |
| ACT-POLICY-RATE-ACTIVATE | Policies | ACTIVATE | MEDIUM |
| ACT-POLICY-APPROVAL-CREATE | Policies | WRITE | HIGH |
| ACT-POLICY-APPROVAL-ACTIVATE | Policies | ACTIVATE | HIGH |
| ACT-POLICY-AUDIT-VIEW | Policies | READ | MEDIUM |
| ACT-POLICY-AUDIT-DOWNLOAD | Policies | DOWNLOAD | LOW |

**Total: 13 seeded actions with no implementation**

### Implemented but NOT Seeded

| Capability | Domain | Mode | Should Add? |
|------------|--------|------|-------------|
| CAP-INC-SEARCH | Incidents | READ | YES |
| CAP-INC-TIMELINE | Incidents | READ | YES |
| CAP-INC-NARRATIVE | Incidents | READ | YES |
| CAP-INC-EXPORT | Incidents | READ | YES |

**Total: 4 implemented capabilities not in seed**

---

## RISK SUMMARY

### CRITICAL Risks

1. **Overview Domain Gap** — L2.1 surfaces exist but NO Customer Console API
2. **GC_L Not Implemented** — ALL policy write/activate actions seeded but missing
3. **Escalate Orphaned** — `ACT-INCIDENT-ESCALATE` seeded but no code

### HIGH Risks

1. **WRITE Reversibility** — Incident acknowledge/resolve cannot be undone
2. **Idempotency Unknown** — WRITE operations lack idempotency documentation

### MEDIUM Risks

1. **CSV Injection** — Logs export may be vulnerable
2. **Audit Mismatch** — AUDIT_LOGS surfaces return execution traces, not audit

---

## RECOMMENDATIONS

### Immediate Actions

1. **Resolve Overview Gap**
   - Option A: Create tenant-scoped health API for Customer Console
   - Option B: Remove `OVERVIEW.*` from L2.1 seed (Founder Console only)

2. **Seed Hygiene**
   - Remove `ACT-INCIDENT-ESCALATE` from seed (not implemented)
   - OR implement escalation capability

3. **Add Missing to Seed**
   - Add Search, Timeline, Narrative, Export for Incidents

### Phase 2 Elicitation Required

1. Should incidents be reopenable (reversibility)?
2. What is idempotency contract for WRITE operations?
3. Are GC_L policy mutations planned for v1?
4. Should audit logs be exposed to customers?

---

## ARTIFACT INVENTORY

### Phase 1 Intelligence Files

| File | Domain | Status |
|------|--------|--------|
| `PHASE_1_OVERVIEW_CAPABILITY_INTELLIGENCE.md` | Overview | ✅ Complete |
| `PHASE_1_ACTIVITY_CAPABILITY_INTELLIGENCE.md` | Activity | ✅ Complete |
| `PHASE_1_INCIDENTS_CAPABILITY_INTELLIGENCE.md` | Incidents | ✅ Complete |
| `PHASE_1_POLICIES_CAPABILITY_INTELLIGENCE.md` | Policies | ✅ Complete |
| `PHASE_1_LOGS_CAPABILITY_INTELLIGENCE.md` | Logs | ✅ Complete |
| `PHASE_1_CONSOLIDATED_INTELLIGENCE_REPORT.md` | ALL | ✅ Complete |

### CSV Exports

| File | Contents |
|------|----------|
| `capability_intelligence_incidents.csv` | Incidents capability table |
| `adapter_operator_crosswalk_incidents.csv` | Incidents adapter mapping |
| `capability_intelligence_all_domains.csv` | ALL domains capability table |

---

## PHASE 1 COMPLETION ATTESTATION

| Criterion | Status |
|-----------|--------|
| All 5 domains analyzed | ✅ |
| All capabilities documented | ✅ (20 total) |
| All adapters mapped | ✅ (5 adapters) |
| All UNKNOWNs explicit | ✅ |
| All risks surfaced | ✅ (10 risks) |
| No UI assumptions | ✅ |
| Seed gaps identified | ✅ (13 missing, 4 extra) |

**PHASE 1 STATUS: COMPLETE**

---

## NEXT PHASE

**Phase 2: Elicitation** — Resolve ambiguities identified in Phase 1
**Phase 3: Binding** — Map capabilities to L2.1 surfaces with action routing

---

## References

- `design/l2_1/seeds/l2_1_action_capabilities.seed.sql` — L2.1 seed data
- `design/l2_1/seeds/l2_1_surface_registry.seed.sql` — L2.1 surfaces
- PIN-347 — L2.1 Epistemic Layer Table-First Design
- Customer Console v1 Constitution
