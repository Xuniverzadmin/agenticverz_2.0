# AGENTICVERZ — PRODUCT DEVELOPMENT CONTRACT (v3)

**Serial:** CONTRACT-PDC-V3
**Status:** ACTIVE
**Effective:** 2025-12-31
**Scope:** Productization + Stabilization only
**Non-Negotiable:** No new runtime power, no architecture changes
**Supremacy Order:** Governance → CI → Product → UX

---

## Executive Summary

This contract governs all productization work post-architecture-freeze.

**Prime Directive:**
> You are now in **stabilization → productization**, not invention.
> CI is the spine. Consoles are the skin. Lifecycle is the muscle.

**What This Contract Prevents:**
- Inventing new architecture when productization is needed
- Skipping CI stabilization to "ship features"
- Cross-console privilege leaks
- Manual CI overrides without governance ratification

---

## CONSOLE CONSTITUTION (FROZEN)

These consoles are **contractual product surfaces**, not infrastructure details.

| # | Domain | Audience | Purpose | Access | Cookie Scope |
|---|--------|----------|---------|--------|--------------|
| 1 | `console.agenticverz.com` | aos-customer | Customer trust & control | Customer users only | console.agenticverz.com |
| 2 | `fops.agenticverz.com` | aos-founder | Founder Ops control plane | Founder-only (RBAC enforced) | fops.agenticverz.com |
| 3 | `preflight-console.agenticverz.com` | aos-internal | Customer UX verification | Internal (IP/VPN) | preflight-console.agenticverz.com |
| 4 | `preflight-fops.agenticverz.com` | aos-internal | Founder ops verification | Internal, read-only | preflight-fops.agenticverz.com |

### Console Hard Rules

- No audience crossover
- No cookie reuse across consoles
- No feature ships to customer console without preflight verification
- CSP strict on founder ops console

---

## PHASE 0 — ARCHITECTURE & GOVERNANCE

**Status:** DONE / FROZEN

### Completed

- L1–L8 layer architecture truthful
- BLCA CLEAN status
- Authority semantics frozen
- SDKs published (PyPI + npm)
- Cost / incidents / replay / policy engines operational
- Session playbooks installed
- PIN-260 Product Architecture Clarity ratified

### Governance Lock

No work permitted in Phase 0 unless a violation is detected.
Architecture is frozen. Only productization remains.

---

## PHASE 1 — CI SIGNAL REDISCOVERY & STABILIZATION

**Status:** ACTIVE (HIGHEST PRIORITY)

> **Objective:** Re-anchor truth, prevent regression, and ensure CI is a **reliable governor**, not noise.

### Why First

Without trusted signals, every later phase is guesswork.
CI must be authoritative before product work proceeds.

### 1.1 CI Signal Rediscovery (MANDATORY)

**Includes:**
- Inventory all existing CI checks
- Classify signals by type:
  - **Structural** (BLCA, layer purity)
  - **Semantic** (authority, policy)
  - **Behavioral** (execution, replay)
  - **Product** (console access, RBAC)
- Remove flaky, redundant, or misleading checks
- Promote only **authoritative signals**

**Output Artifact:**
- `docs/ci/CI_SIGNAL_REGISTRY.md`
- Each signal tagged with:
  - Layer relevance (L1-L8)
  - Blocking vs advisory
  - Owner
  - Failure meaning

**Completion Criteria:**
- [ ] Every CI failure has a clear interpretation
- [ ] No "unknown red" failures
- [ ] BLCA remains supreme structural check
- [ ] Signal registry complete and reviewed

### 1.2 CI/CD Pipeline Stabilization

**Includes:**
- Deterministic CI runs (same commit = same result)
- Clear stage separation:
  - Static checks (lint, format)
  - Structural checks (BLCA, layer)
  - Semantic checks (authority, policy)
  - Product checks (console, RBAC)
- Environment parity fixes
- Removal of order-dependent failures

**Completion Criteria:**
- [ ] Same commit produces same CI result
- [ ] CI trusted enough to block releases
- [ ] No manual overrides except via governance ratification

### 1.3 CI → Governance Wiring

**Includes:**
- CI failures auto-classified into:
  - **Violation** — Requires fix or ratified exception
  - **Regression** — Requires immediate attention
  - **Flake** — Requires removal or stabilization
- Violations require fix or ratified exception (no silent ignore)
- CI results written to governance artifacts

**Completion Criteria:**
- [ ] CI outcomes feed governance, not the other way around
- [ ] No ignored failures without ratification record

---

## PHASE 2 — CONSOLE & PRODUCT SURFACE COMPLETION

**Status:** BLOCKED (Awaiting Phase 1 completion)

> **Objective:** Make the system usable without increasing power.

### 2.1 Customer Console Completion

| Capability | Status | Notes |
|------------|--------|-------|
| Domain-complete UI (5 domains) | | Overview, Activity, Incidents, Policies, Logs |
| Streaming visibility (SSE) | | Real-time execution updates |
| Evidence & replay (read-only) | | Trace inspection, no mutation |
| Safe defaults only | | Pre-approved policy bundles |
| RBAC-aware UI | | Role-appropriate views |

### 2.2 Founder Ops Console Completion

| Capability | Status | Notes |
|------------|--------|-------|
| Kill / freeze / override controls | | K-1 to K-5 invariants |
| Cross-tenant visibility | | Founder-only data access |
| Strict audit logging | | Every founder action recorded |
| CSP enforcement | | No external script injection |

### 2.3 Preflight Customer Console

| Capability | Status | Notes |
|------------|--------|-------|
| Full parity with production | | Same features, internal access |
| Feature flags enabled | | Test unreleased features |
| No founder power | | Customer-only capabilities |

### 2.4 Preflight Founder Ops (Read-only)

| Capability | Status | Notes |
|------------|--------|-------|
| Audit verification | | Review founder actions |
| Incident replay | | Investigate past incidents |
| Zero mutation | | Read-only, no changes |

**Completion Criteria:**
- [ ] No console leaks power to wrong audience
- [ ] Preflight is required gate for customer release
- [ ] All four consoles operational and tested

### 2.5 SDK Trust Testing

| Capability | Status | Notes |
|------------|--------|-------|
| SDK ↔ backend integration tests | | Both Python and JS |
| Replay determinism via SDK | | Hash parity verified |
| CI job gating releases | | No SDK release without green CI |

### 2.6 End-to-End System Certification

| Capability | Status | Notes |
|------------|--------|-------|
| Golden E2E scenarios | | Critical paths tested |
| CI-only (L8) | | No manual execution |
| Single green/red signal | | Whole system health indicator |

---

## PHASE 3 — CUSTOMER LIFECYCLE & RBAC

**Status:** BLOCKED (Awaiting Phase 2 completion)

### 3.1 Customer Onboarding & Offboarding

| Capability | Status | Notes |
|------------|--------|-------|
| Self-serve tenant creation | | No founder intervention needed |
| Default safe policies | | Pre-approved policy bundles |
| Guaranteed access revocation | | Clean offboarding |
| Customer journey mapping | | Documented flows |

### 3.2 Customer RBAC (Sub-users)

| Capability | Status | Notes |
|------------|--------|-------|
| Org / team / user hierarchy | | Multi-level structure |
| Role → capability mapping | | Explicit permissions |
| UI + backend enforcement | | Both layers checked |
| No authority leakage | | Role boundaries respected |

---

## PHASE 4 — COMMERCIALIZATION & PRODUCT CI

**Status:** BLOCKED (Awaiting Phase 3 completion)

### 4.1 Subscription Management

| Capability | Status | Notes |
|------------|--------|-------|
| Plan definitions | | SKU boundaries explicit |
| Entitlement enforcement | | Backend + UI gated |
| Upgrade / downgrade safety | | No data loss on plan change |

### 4.2 Product-Level CI Hardening

| Capability | Status | Notes |
|------------|--------|-------|
| RBAC regression checks | | No permission drift |
| Entitlement regression checks | | No plan bypass |
| Console audience enforcement checks | | No crossover |
| E2E gating for releases | | Green required for deploy |

---

## PHASE 5 — SUPPORT, GTM & OPERABILITY

**Status:** BLOCKED (Awaiting Phase 4 completion)

### 5.1 Customer Support System

| Capability | Status | Notes |
|------------|--------|-------|
| Ticket workflows | | Customer-initiated support |
| Evidence exports | | Shareable incident data |
| Customer/internal data separation | | No crossover |

### 5.2 Demos & GTM

| Capability | Status | Notes |
|------------|--------|-------|
| Demo tenants | | Isolated demo environments |
| Sales-safe scripts | | No production data |
| SKU-aligned documentation | | Matches commercial offering |

---

## PHASE 6 — OPTIONAL POLISH (POST-LAUNCH)

**Status:** OPTIONAL

- Customer-safe templates
- Guided setup wizards
- Explicit SKU contracts

---

## DEPENDENCY ORDER (STRICT)

```
PHASE 0: Architecture & Governance (DONE)
    ↓
PHASE 1: CI Signal Rediscovery & Stabilization
    ↓
PHASE 2: Console & Product Surface Completion
    ↓
PHASE 3: Customer Lifecycle & RBAC
    ↓
PHASE 4: Commercialization & Product CI
    ↓
PHASE 5: Support, GTM & Operability
    ↓
PHASE 6: Optional Polish (POST-LAUNCH)
```

**Skipping order = governance violation.**

---

## GOVERNANCE HARD RULES

| Rule | Enforcement |
|------|-------------|
| No federated agent identity | BLOCKED (intentionally deferred) |
| No new runtime authority | BLOCKED (architecture frozen) |
| No cross-console privilege leaks | BLOCKING |
| No CI overrides without ratification | BLOCKING |
| No Phase N+1 work until Phase N complete | BLOCKING |

---

## SESSION INTEGRATION

### Where We Are (Current State)

```yaml
current_phase: 1
current_phase_name: "CI Signal Rediscovery & Stabilization"
phase_status: ACTIVE
blocking_phases: [2, 3, 4, 5, 6]
```

### Session Start Question

Every session should answer:

> "Which phase are we in, and what specific work item within that phase?"

If the answer is unclear → read this contract first.

### Phase Transition Gate

To transition from Phase N to Phase N+1:
1. All completion criteria for Phase N must be checked
2. Human ratification required
3. Update `current_phase` in this contract

---

## FINAL TRUTH (LOCKED)

> **CI is the spine. Consoles are the skin. Lifecycle is the muscle.**

This contract ensures:
- No missed work
- No premature scaling
- No erosion of governance
- Clear session start point

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `CUSTOMER_CONSOLE_V1_CONSTITUTION.md` | Frozen console structure |
| `PIN-260` | Product Architecture Clarity |
| `PIN-259` | Phase G Steady-State Governance |
| `CI_SIGNAL_REGISTRY.md` | CI signal inventory (Phase 1 output) |
| `SESSION_PLAYBOOK.yaml` | Session governance |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Contract v3 created and ratified |
