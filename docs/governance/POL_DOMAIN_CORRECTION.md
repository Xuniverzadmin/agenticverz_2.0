# POL Domain Correction: Four-Plane Architecture

**Status:** PROPOSED
**Created:** 2026-01-15
**Authority:** Architecture Correction
**Reference:** HISAR Sweep Analysis

---

## Diagnosis

**POL is not one domain.**

The current POL domain collapses four fundamentally different system roles:

1. **Control-plane** — Policy definition (mutable, authoritative)
2. **Decision-plane** — Policy evaluation (computed, deterministic)
3. **Enforcement-plane** — Policy outcomes (historical truth)
4. **Analytics-plane** — Usage statistics (derived, NOT policy)

SDSR is correctly refusing to verify this misalignment.

---

## The Four-Plane Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         POLICY ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PLANE 1: CONTROL (Authoritative, Mutable)                              │
│  ══════════════════════════════════════════                              │
│  "What policies exist and how they are configured"                       │
│                                                                          │
│  • Tenant-scoped                                                         │
│  • Human-authored or agent-suggested                                     │
│  • CRUD, versioned                                                       │
│  • NOT derived from runtime                                              │
│  • NOT statistical                                                       │
│                                                                          │
│  Router: /policy-layer/*                                                 │
│  SDSR: NOT APPLICABLE (authoritative config, not observable truth)      │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PLANE 2: DECISION (Read-only, Computed)                                │
│  ═══════════════════════════════════════                                 │
│  "What the policy engine decides given state"                            │
│                                                                          │
│  • Derived but deterministic                                             │
│  • Effective policy state                                                │
│  • Resolved conflicts                                                    │
│  • Dependency graph                                                      │
│  • Current risk ceilings after overrides                                 │
│                                                                          │
│  Router: /policy-layer/* (computed views)                                │
│  SDSR: APPLICABLE (pure READ projections)                                │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PLANE 3: ENFORCEMENT (Historical Truth)                                │
│  ═══════════════════════════════════════                                 │
│  "What actually happened because of policies"                            │
│                                                                          │
│  • Execution history                                                     │
│  • Decision outcomes                                                     │
│  • Override actions                                                      │
│  • Violation ledger                                                      │
│                                                                          │
│  Router: /enforcement/* or existing execution routers                    │
│  SDSR: STRICT (if data isn't there, panel stays unbound)                │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PLANE 4: ANALYTICS (Derived, Statistical)                              │
│  ═════════════════════════════════════════                               │
│  "Statistical analysis of usage patterns"                                │
│                                                                          │
│  • NOT POLICY — policy-adjacent                                          │
│  • Consumes: runs, costs, violations, enforcement outcomes               │
│  • Should be under ANALYTICS or GOVERNANCE_INSIGHTS domain               │
│                                                                          │
│  Router: /analytics/* or /cost/*                                         │
│  SDSR: APPLICABLE (observable facts)                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Panel Reclassification

### PLANE 1: CONTROL (Status: DECLARED is correct)

| Old Panel | New Classification | Capability | Status |
|-----------|-------------------|------------|--------|
| POL-GOV-ACT-O1 | CONTROL | policies.active_summary | DECLARED |
| POL-GOV-ACT-O2 | CONTROL | policies.active_list | DECLARED |
| POL-GOV-DFT-O1 | CONTROL | policies.defaults_summary | DECLARED |
| POL-GOV-DFT-O2 | CONTROL | policies.versions_list | DECLARED |
| POL-GOV-DFT-O3 | CONTROL | policies.current_version | DECLARED |
| POL-GOV-DFT-O4 | CONTROL | policies.conflicts_list | DECLARED |
| POL-GOV-DFT-O5 | CONTROL | policies.dependencies_list | DECLARED |
| POL-GOV-LIB-O1 | CONTROL | policies.safety_rules | DECLARED |
| POL-GOV-LIB-O2 | CONTROL | policies.ethical_constraints | DECLARED |
| POL-GOV-LIB-O5 | CONTROL | policies.temporal_policies | DECLARED |
| POL-LIM-THR-O1 | CONTROL | policies.risk_ceilings | DECLARED |
| POL-LIM-THR-O3 | CONTROL | policies.quota_runs | DECLARED |
| POL-LIM-THR-O4 | CONTROL | policies.quota_tokens | DECLARED |
| POL-LIM-THR-O5 | CONTROL | policies.cooldowns_list | DECLARED |

**SDSR Status:** NOT APPLICABLE — These are authoritative configuration, not observable truth.

---

### PLANE 2: DECISION (Status: DECLARED until computed views exist)

| Old Panel | New Classification | Capability | Router |
|-----------|-------------------|------------|--------|
| POL-GOV-ACT-O4 | DECISION | policies.layer_state | /policy-layer/state |
| POL-GOV-ACT-O5 | DECISION | policies.layer_metrics | /policy-layer/metrics |

**SDSR Status:** APPLICABLE once endpoints return pure READ projections.

---

### PLANE 3: ENFORCEMENT (Status: Bind to execution history)

| Old Panel | New Classification | Capability | Source |
|-----------|-------------------|------------|--------|
| POL-LIM-VIO-O1 | ENFORCEMENT | policies.violations_list | Enforcement logs |
| POL-LIM-VIO-O2 | ENFORCEMENT | policies.cost_incidents | Guard outcomes |
| POL-LIM-VIO-O3 | ENFORCEMENT | policies.simulated_incidents | CostSim results |
| POL-LIM-VIO-O4 | ENFORCEMENT | policies.anomalies_list | Detection outcomes |
| POL-LIM-VIO-O5 | ENFORCEMENT | policies.divergence_report | Divergence analysis |

**SDSR Status:** STRICT — If enforcement data doesn't exist, panel stays DECLARED.

---

### PLANE 4: ANALYTICS (MOVE OUT OF POL)

**These panels are MISFILED. They belong under ANALYTICS or GOVERNANCE_INSIGHTS.**

| Old Panel | New Domain | Capability | Notes |
|-----------|------------|------------|-------|
| POL-LIM-USG-O1 | ANALYTICS | analytics.tenant_usage | Usage statistics |
| POL-LIM-USG-O2 | ANALYTICS | analytics.cost_dashboard | Cost analysis |
| POL-LIM-USG-O3 | ANALYTICS | analytics.cost_by_user | User cost breakdown |
| POL-LIM-USG-O4 | ANALYTICS | analytics.cost_projection | Forecasting |
| POL-LIM-USG-O5 | ANALYTICS | analytics.billing_status | Billing state |

**Action:** Remove from POL domain entirely. Rebind to analytics capabilities.

---

### SDSR FAILURES: Wrong Endpoint Type

These endpoints are **command/mutation endpoints**, not **observable state endpoints**:

| Endpoint | Problem | Resolution |
|----------|---------|------------|
| `/guard/policies` | Command-style response | Not observable |
| `/costsim/*` | Simulation output | Not observation |
| `/api/v1/policies/requests` | Workflow inbox | Not stable state |
| `/cost/budgets` | Mutation endpoint | Create read projection |

**HISAR forbids pretending transactions are facts.**

---

## Intent YAML Schema Addition

Add to intent YAMLs:

```yaml
policy_plane: CONTROL | DECISION | ENFORCEMENT | ANALYTICS

# For CONTROL plane:
sdsr:
  applicable: false
  reason: "Authoritative configuration, not observable truth"

# For DECISION/ENFORCEMENT plane:
sdsr:
  applicable: true
  auth_mode: SERVICE

# For ANALYTICS plane (after domain move):
observation_scope:
  type: TENANT
  semantic_alias: CUSTOMER
```

---

## Backend Router Contract: /policy-layer

### Minimal Viable Endpoints (Control Plane)

```
GET  /policy-layer/policies              → List active policies
GET  /policy-layer/policies/{id}         → Policy detail
POST /policy-layer/policies              → Create policy
PUT  /policy-layer/policies/{id}         → Update policy
GET  /policy-layer/library               → Global policy library
GET  /policy-layer/defaults              → Default/suggested policies
GET  /policy-layer/versions              → Version history
GET  /policy-layer/versions/current      → Current version
```

### Decision Plane Endpoints (Computed Views)

```
GET  /policy-layer/state                 → Effective policy state
GET  /policy-layer/conflicts             → Resolved conflicts
GET  /policy-layer/dependencies          → Dependency graph
GET  /policy-layer/risk-ceilings         → Current risk ceilings
GET  /policy-layer/cooldowns             → Active cooldowns
```

### Enforcement Data (Separate Router)

```
GET  /enforcement/violations             → Violation ledger
GET  /enforcement/overrides              → Human overrides
GET  /enforcement/outcomes               → Decision outcomes
```

---

## Corrected Domain Map

```
BEFORE (Collapsed):
┌─────────────────────────────────────────┐
│                  POL                     │
│  (27 panels, 10% coverage, BROKEN)       │
└─────────────────────────────────────────┘

AFTER (Four Planes):
┌─────────────────────────────────────────┐
│  POL-CONTROL (14 panels)                 │
│  Status: DECLARED (correct)              │
│  SDSR: NOT APPLICABLE                    │
├─────────────────────────────────────────┤
│  POL-DECISION (2 panels)                 │
│  Status: DECLARED → OBSERVED             │
│  SDSR: APPLICABLE when endpoints exist   │
├─────────────────────────────────────────┤
│  POL-ENFORCEMENT (5 panels)              │
│  Status: DECLARED → OBSERVED             │
│  SDSR: STRICT                            │
├─────────────────────────────────────────┤
│  ANALYTICS (5 panels) ← MOVED            │
│  Status: Rebind to analytics domain      │
│  SDSR: APPLICABLE                        │
└─────────────────────────────────────────┘
```

---

## Action Plan

### Step 1: Accept Partial Observation (Immediate)

For POL-CONTROL panels, **DECLARED is the correct end state**.

```yaml
capability:
  status: DECLARED
sdsr:
  applicable: false
  reason: "Control plane: authoritative configuration"
```

### Step 2: Create /policy-layer Module (Backend)

Minimal implementation:
- state
- versions
- current
- conflicts
- dependencies
- limits

No SDSR initially. Honest existence.

### Step 3: Reclassify Panels by Plane

Add `policy_plane` to intent YAMLs.

### Step 4: Move Usage & Billing OUT of POL

Create new domain or merge into existing analytics.

### Step 5: SDSR Only Where Reality Exists

Run SDSR **only** for:
- ENFORCEMENT panels (historical truth)
- DECISION panels (computed views)
- ANALYTICS panels (derived facts)

**Never** for:
- Drafts
- Proposals
- Libraries
- Workflows

---

## Summary

| Plane | Panels | SDSR | Target Status |
|-------|--------|------|---------------|
| CONTROL | 14 | NOT APPLICABLE | DECLARED |
| DECISION | 2 | APPLICABLE | OBSERVED |
| ENFORCEMENT | 5 | STRICT | OBSERVED |
| ANALYTICS | 5 | APPLICABLE | MOVE OUT |

**Nothing is broken.**

The architecture outgrew a flat domain model. HISAR + SDSR forced the distinction between **authority**, **decision**, **execution**, and **analysis**.

---

## References

- HISAR.md — Execution doctrine
- SDSR.md — Observation semantics
- PIN-422 — HISAR Execution Doctrine
