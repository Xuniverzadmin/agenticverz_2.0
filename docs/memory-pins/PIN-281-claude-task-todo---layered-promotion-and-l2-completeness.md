# PIN-281: Claude Task TODO — Layered Promotion & L2 Completeness

**Status:** ACTIVE
**Date:** 2026-01-03
**Category:** Governance / Claude Playbook
**Milestone:** Customer Console v1 Governance
**Related PINs:** PIN-280 (Promotion Guide), PIN-279 (L2 Distillation), PIN-240 (Customer Console Constitution)

---

## Purpose

Operational Claude task specification for promoting missing capabilities safely, one layer at a time. This is a **governance-first, layer-safe** execution playbook with no shortcuts.

**Governing Principle:** Claude may only promote ONE capability across ONE layer per session.

---

## Global Rules (Non-Negotiable)

| Rule | Enforcement |
|------|-------------|
| One capability at a time | BLOCKING |
| One layer boundary per PR | BLOCKING |
| Registry update mandatory | BLOCKING |
| If proof is missing → STOP | BLOCKING |
| No UI wiring until L3→L2 complete | BLOCKING |
| No reuse of ops/internal services for customer scope | BLOCKING |

If any rule is violated, abort and report.

---

## Phase 0 — Governance Setup (BLOCKING)

### Task 0.1 — Create Promotion Register

**File:** `docs/governance/L2_PROMOTION_REGISTER.yaml`

**Schema:**

```yaml
capability_id:
  description: ""
  current_max_layer: L?
  target_layer: L?
  audience: CUSTOMER | FOUNDER | INTERNAL
  mutation_type: READ | WRITE | CONTROL
  risk_class: LOW | MEDIUM | HIGH
  approval:
    required: true
    owner: HUMAN
  status: DRAFT
```

**Rule:** Do not promote anything without registry entry.

---

### Task 0.2 — Declare Intentional Omissions

**File:** `docs/governance/INTENTIONAL_OMISSIONS.yaml`

Populate only with explicitly approved internal-only capabilities.

---

## Phase 1 — L7 → L6 (Reality Promotion)

**Goal:** Ensure data is exposure-safe, not just present.

### Task 1.x (per capability)

1. Verify migrations are applied and enabled
2. If raw tables exist:
   - Create customer-safe views
   - Enforce tenant scoping
   - Remove sensitive columns

**Output Artifacts:**
- SQL view / materialized view
- Migration file
- Registry update (`current_max_layer: L6`)

**Rule:** Do NOT expose raw tables upward.

---

## Phase 2 — L6 → L5 (Execution Promotion)

**Goal:** Make data servable and stable.

### Task 2.x (per capability)

1. Check if read path depends on: jobs, snapshots, aggregation
2. If missing:
   - Create idempotent read builders
   - No side effects
   - No domain logic

**Output Artifacts:**
- Job / task / builder
- Bounded execution
- Registry update (`current_max_layer: L5`)

**Rule:** Do NOT add policy logic here.

---

## Phase 3 — L5 → L4 (Meaning Promotion)

**Goal:** Define customer-level meaning.

### Task 3.x (per capability)

1. Create customer-scoped domain service
2. Requirements:
   - Interpret execution output
   - Apply domain semantics
   - Avoid ops/internal assumptions

**Output Artifacts:**
- `customer_<domain>_service.py`
- Unit tests
- Registry update (`current_max_layer: L4`)

**Rule:** Do NOT reuse ops services directly.

---

## Phase 4 — L4 → L3 (Boundary Promotion) — CRITICAL

**Goal:** Create product boundary.

### Task 4.x (per capability)

1. Create explicit adapter
2. Enforce:
   - Tenant scope
   - RBAC
   - Rate limits
   - Redaction

**Output Artifacts:**
- `customer_<capability>_adapter.py`
- Adapter tests
- Registry update (`current_max_layer: L3`)

**Rule:** Do NOT multiplex unrelated capabilities.

---

## Phase 5 — L3 → L2 (API Promotion)

**Goal:** Expose exactly what adapter allows.

### Task 5.x (per capability)

1. Create L2 router:
   - One adapter per route
   - No business logic
2. Update:
   - `L2_API_DOMAIN_MAPPING.csv`
   - Promotion register (`target_layer: L2`, `status: PROMOTED`)

**Output Artifacts:**
- Router file
- Schema definitions
- Mapping CSV diff

**Rule:** No API without adapter proof.

---

## Phase 6 — Validation & Freeze

### Task 6.1 — BLCA Validation

Run:
- `layer_validator.py`
- `intent_validator.py`
- `visibility_validator.py`

All must pass.

---

### Task 6.2 — Change Record

**File:** `docs/change-records/CR-XXXX.md`

Include:
- capability_id
- layer transition
- reason
- risk assessment
- rollback plan

---

## Execution Order (Mandatory)

Claude must execute tasks in this order:

| Order | Capability | Risk |
|-------|------------|------|
| 1 | Logs | Medium |
| 2 | Activity | Low |
| 3 | Policies | Medium |
| 4 | Keys | Medium |
| 5 | Incident Actions | Medium |
| 6 | Killswitch | HIGH |

Claude must **stop after each capability** and wait for human approval.

---

## Failure Conditions (Auto-Stop)

Claude must STOP if:
- Adapter would expose ops semantics
- Capability requires authority clarification
- Registry entry is missing
- Layer jump is required

---

## Final Assertion (Required Before Every Response)

> "I have promoted exactly ONE capability across exactly ONE layer boundary, with registry proof and no governance violations."

If this sentence is not true → DO NOT RESPOND.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│           LAYERED PROMOTION DISCIPLINE                      │
├─────────────────────────────────────────────────────────────┤
│  PHASE 0: Create L2_PROMOTION_REGISTER.yaml (BLOCKING)      │
│  PHASE 1: L7→L6 — Customer-safe views, tenant scoping       │
│  PHASE 2: L6→L5 — Idempotent read builders                  │
│  PHASE 3: L5→L4 — Customer domain services                  │
│  PHASE 4: L4→L3 — Boundary adapters (CRITICAL)              │
│  PHASE 5: L3→L2 — API routes (one adapter per route)        │
│  PHASE 6: Validation + Change record                        │
├─────────────────────────────────────────────────────────────┤
│  ORDER: Logs → Activity → Policies → Keys → Actions → Kill  │
│  RULE: One capability. One layer. One PR. Registry proof.   │
└─────────────────────────────────────────────────────────────┘
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-03 | Initial task specification |
