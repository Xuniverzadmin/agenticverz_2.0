# PIN-280: L2 Promotion Governance — Layer-Respecting Promotion Guide

**Status:** ACTIVE
**Date:** 2026-01-03
**Category:** Architecture / Promotion Governance
**Milestone:** Customer Console v1 Governance
**Related PINs:** PIN-279 (L2 Distillation), PIN-240 (Customer Console Constitution), PIN-248 (Codebase Inventory)

---

## Purpose

Independent assessment of PIN-279's L2 distillation findings. This PIN corrects two dangerous assumptions, re-classifies the 9 accidental omissions by broken layer, and provides a **layer-respecting promotion guide** that prevents governance collapse.

**Core Principle:** Wiring L1→L2 directly would violate layering in multiple cases. Promotion must proceed layer-by-layer.

---

## Critical Corrections to PIN-279

### Assumption A (Dangerous)

**PIN-279 claimed:** "REACHABLE_SET Count = 24 boundary-exposed capabilities"

**Reality:**
- What's listed is **adapter/middleware presence**, not **capability-specific reachability**
- Adapters like `policy_adapter.py` or `runtime_adapter.py` multiplex many capabilities
- Therefore **reachability ≠ exposure readiness**

**Conclusion:** L4→L3 is only partially promoted, not complete.

---

### Assumption B (Subtle)

**PIN-279 claimed:** "Accidental omissions are UI wiring problems"

**Reality:**
- Several "NOT_WIRED" items are **not UI problems**
- They are **missing boundary contracts** (L3) or **missing aggregation semantics** (L4)

**Conclusion:** Wiring L1→L2 directly would **violate layering** in multiple cases.

---

## Re-Classification of 9 Accidental Omissions

The 9 gaps from PIN-279 are re-classified by **lowest broken layer**, not UI symptom.

### Bucket 1 — True L1 Wiring Gaps (Safe to Wire)

These already have clean L2 semantics:

| Capability | Status |
|------------|--------|
| `ACTIVITY_LIST` | Can be promoted L2 → L1 only |
| `EXECUTION_DETAIL` | Can be promoted L2 → L1 only |

**Action:** Wire directly to existing L2 endpoints.

---

### Bucket 2 — Missing L3 Façades (NOT Safe to Wire Yet)

| Capability | Problem |
|------------|---------|
| `LOG_LIST` | Exists as internal/ops API, lacks customer-scoped boundary |
| `LOG_DETAIL` | Would leak internal structure if exposed directly |
| `LOG_EXPORT` | No customer-safe aggregation |
| `POLICY_CONSTRAINTS` | Ops semantics, not customer semantics |

**Action:** Create L3 customer façades BEFORE L2 exposure.

**Warning:** Wiring these at L1 would be a governance breach.

---

### Bucket 3 — Authority-Bearing Actions (Require Governance Decision)

| Capability | Concern |
|------------|---------|
| `KILLSWITCH_UI` | Mutation / control surface |
| `INCIDENT_ACTIONS (Ack/Resolve)` | State mutation authority |
| `KEYS_PAGE` | Credential management |

**Action:** Promote with explicit authority contracts, not "UI enablement".

---

## Layer-Respecting Promotion Guide

### PHASE 0 — Governance First (Before Any Code)

Create governance artifact:

```
docs/governance/L2_PROMOTION_REGISTER.yaml
```

**Schema:**

```yaml
capability_id:
  audience: CUSTOMER | FOUNDER | INTERNAL
  mutation: READ | WRITE | CONTROL
  current_layer_max: L1 | L2 | L3 | L4 | L5
  intended_L2_exposure: true | false
  approval:
    required: true
    owner: <human>
```

**Rule:** No promotion without an entry here.

---

### PHASE 1 — L7 → L6 (Reality Gaps)

**Finding:** Analysis assumes migrations = readiness. That's incomplete.

**Required Promotion:** Add exposure-grade views/materializations where missing.

**Example (Logs):**

```sql
-- L6 promotion: customer-safe log view
CREATE VIEW customer_logs AS
SELECT
  trace_id,
  occurred_at,
  severity,
  message
FROM internal_logs
WHERE tenant_id = current_setting('app.tenant_id');
```

**Rule:** No raw tables exposed upward.

---

### PHASE 2 — L6 → L5 (Execution Semantics)

**Finding:** Some data exists but is never summarized or stabilized for read paths.

**Required Promotion:** Add read-model builders (not workers that mutate behavior).

**Example:**

```python
# backend/app/jobs/log_snapshot_builder.py
def build_customer_log_snapshot():
    ...
```

**Rule:** L5 promotion must be idempotent, bounded, read-safe.

---

### PHASE 3 — L5 → L4 (Meaning Contracts)

**Finding:** Several domains (Logs, Policies) have no customer meaning defined.

**Required Promotion:** Create customer-scoped domain services, not reuse ops services.

**Example:**

```python
# backend/app/services/customer_log_service.py
class CustomerLogService:
    def list_logs(self, tenant_id, filters):
        ...
```

**Rule:** No customer UI talks to ops semantics.

---

### PHASE 4 — L4 → L3 (Boundary Façades) ⚠️ MOST CRITICAL

**Finding:** This is where PIN-279 is weakest.

**Required Promotion:** Create explicit customer façades.

**Example:**

```python
# backend/app/adapters/customer_logs_adapter.py
class CustomerLogsAdapter:
    def list(self, tenant_id, params):
        return CustomerLogService(...).list_logs(...)
```

**Enforce:**
- Tenant scoping
- Redaction
- Rate limits

**Rule:** Adapters are the product boundary, not APIs.

---

### PHASE 5 — L3 → L2 (API Exposure)

Only now add routes.

**Example:**

```python
# backend/app/api/guard_logs.py
@router.get("/guard/logs")
def list_logs(...):
    return customer_logs_adapter.list(...)
```

**Update:**
- `L2_API_DOMAIN_MAPPING.csv`
- `L2_PROMOTION_REGISTER.yaml`

**Rule:** Every L2 route must point to exactly one adapter.

---

### PHASE 6 — L2 → L1 (UI Wiring)

Only now wire UI.

**Applies to:**
- Activity (Bucket 1 - safe)
- Logs (after Phase 1-5)
- Policies (after Phase 1-5)
- Keys (after governance approval)
- Incident actions (after governance approval)

---

## Execution Discipline

### Mandatory Rule

> **One layer promotion per PR. One capability per PR.**

For each PR:
- Target layer boundary (e.g. L4→L3)
- Single capability_id
- Registry update required
- BLCA must pass

If Claude cannot prove a link:
- Must stop
- Add `BLOCKED: missing semantic contract`

---

## Governance Guards

### Guard 1 — Promotion Gate Script

Extend `scripts/ops/layer_validator.py` to assert:
- No new L2 route without adapter
- No adapter without domain service
- No domain service without execution/read model

---

### Guard 2 — Change Record Enforcement

Every promotion PR must add:

```
docs/change-records/CR-<id>.md
```

Containing:
- capability_id
- from_layer → to_layer
- reason
- risk class

---

### Guard 3 — Claude Scope Lock

Update Claude playbook:

> "Claude may only promote ONE capability across ONE layer per session."

This prevents cross-layer hallucination.

---

## Summary

| Finding | Correction |
|---------|------------|
| PIN-279 is L2/L1-biased | Real gaps are L4→L3 and L3→L2 |
| 9 gaps treated as UI problems | Re-classified into 3 buckets by broken layer |
| Direct wiring suggested | Layer-respecting 6-phase promotion required |
| No execution discipline | One layer, one capability per PR |

**Final Warning:** If you wire UI now without layer promotion, you will collapse governance.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial assessment and promotion guide |
