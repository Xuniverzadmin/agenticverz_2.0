# PIN-240: Seven-Layer Codebase Mental Model

**Status:** CONSTITUTIONAL
**Created:** 2025-12-29
**Category:** Architecture / Mental Model
**Milestone:** Post-M29 - Architectural Clarity

---

## Summary

Establishes the canonical 7-layer vertical stack for reasoning about the AOS codebase. This replaces horizontal "product mapping" with vertical "layer thinking" — a fundamental shift in how we understand code ownership and boundaries.

---

## Core Insight

> **Products are perspectives. Layers are reality.**

Mapping artifacts to products gives lists.
Mapping artifacts to layers gives **understanding**.

Once you see layers, product alignment becomes obvious and boring.

---

## The 7-Layer Mental Map

```
┌──────────────────────────────────────────────────────────────────────┐
│ L1 — PRODUCT EXPERIENCE (Frontend)                                   │
│      Pages, Layouts, Routes, Pure Presentation                       │
├──────────────────────────────────────────────────────────────────────┤
│ L2 — PRODUCT APIs (Surface Contracts)                                │
│      Console-only routes, Auth-scoped APIs, Intent not execution     │
├──────────────────────────────────────────────────────────────────────┤
│ L3 — BOUNDARY ADAPTERS (Translation Layer)                           │
│      PDF generation, Evidence formatting, Summaries, Recommendations │
├──────────────────────────────────────────────────────────────────────┤
│ L4 — DOMAIN ENGINES (System Truth)                                   │
│      Detection algorithms, Policy engines, Recovery logic, Matching  │
├──────────────────────────────────────────────────────────────────────┤
│ L5 — EXECUTION & WORKERS                                             │
│      Background jobs, Schedulers, Evaluators, Async loops            │
├──────────────────────────────────────────────────────────────────────┤
│ L6 — PLATFORM SUBSTRATE                                              │
│      Auth, Budgeting, Event emitters, SDKs, DB models, Telemetry     │
├──────────────────────────────────────────────────────────────────────┤
│ L7 — FUNDAMENTAL OPS & SCRIPTS                                       │
│      Deployment, CI helpers, Migrations, One-off tools               │
└──────────────────────────────────────────────────────────────────────┘
```

**Rule:** Every artifact fits **exactly one layer**. If it doesn't → it's broken.

---

## Layer Definitions

### L1 — Product Experience (Frontend)

**What lives here:**
- Pages (`OverviewPage.tsx`, `IncidentsPage.tsx`)
- Layouts (`AIConsoleLayout.tsx`)
- Routes (`AIConsoleApp.tsx`)
- Pure presentation logic

**Mental rule:**
> If this file disappeared, only *screens* disappear.

**Ownership:** Always product-specific.

**Violation signal:** Logic lives in presentation.

---

### L2 — Product APIs (Surface Contracts)

**What lives here:**
- Console-only routes (`guard.py`)
- Auth-scoped APIs (`customer_visibility.py`)
- Read/write *intent*, not execution

**Mental rule:**
> These APIs explain *what the product promises*, not *how the system works*.

**Ownership:** Product-specific.

**Violation signal:** Workers call this layer.

---

### L3 — Boundary Adapters (Translation Layer)

**What lives here:**
- PDF generation (`evidence_report.py`)
- Certificate signing (`certificate.py`)
- Prediction summaries (`prediction.py`)
- Policy recommendations (`policy_proposal.py`)

**Mental rule:**
> Adapters translate **platform truth → product meaning**.

**Allowed behaviors:**
- Read domain state
- Lightly write *product-local* state

**Forbidden behaviors:**
- Own core rules
- Run independently
- Be required by workers

**Ownership:** Product-scoped, but thin.

---

### L4 — Domain Engines (System Truth)

**What lives here:**
- Detection algorithms (`pattern_detection.py`)
- Recovery logic (`recovery_matcher.py`, `recovery_rule_engine.py`)
- Cost analysis (`cost_anomaly_detector.py`)
- Policy engines

**Mental rule:**
> If this logic is wrong, **every product breaks**.

**Ownership:** NEVER product-owned, even if only one product uses it today.

**This is where most mislabeling happens.**

---

### L5 — Execution & Workers

**What lives here:**
- Background jobs
- Schedulers
- Evaluators (`recovery_evaluator.py`)
- Async loops
- Cron tasks

**Mental rule:**
> This layer answers: *"What actually runs when nobody is watching?"*

**Ownership:** System-wide.

**Violation signal:** Frontend logic leaks here.

---

### L6 — Platform Substrate

**What lives here:**
- Auth infrastructure
- Budgeting (BudgetLLM)
- Event emitters (`event_emitter.py`)
- SDKs
- DB models
- Telemetry
- Metrics

**Mental rule:**
> This layer must not know what a "product" is.

**Ownership:** System-wide. Supports everything.

---

### L7 — Fundamental Ops & Scripts

**What lives here:**
- Deployment scripts (`aos-console-deploy.sh`)
- CI helpers
- Migrations
- Preflight scripts
- Registry tooling
- One-off tools

**Mental rule:**
> This layer touches the real world (files, servers, time).

**Ownership:** Varies. Allowed to be ugly. Must be explicit.

---

## Product as Layer Slice

A product is simply a **vertical slice across layers**.

### AI Console Slice

```
AI Console =
  L1 (Console UI pages)
+ L2 (Console APIs: guard.py, customer_visibility.py)
+ L3 (Console adapters: evidence_report.py, certificate.py)
```

**Rule:** If AI Console owns anything below L3, architecture is broken.

### Ops Console Slice (Future)

```
Ops Console =
  L1 (Ops UI pages)
+ L2 (Ops APIs)
+ L3 (Ops adapters)
```

### Product Builder Slice (Future)

```
Product Builder =
  L1 (Builder UI)
+ L2 (Builder APIs)
+ L3 (Builder adapters)
```

---

## Layer Ownership Matrix

| Layer | AI Console | Ops Console | Product Builder | System-Wide |
|-------|------------|-------------|-----------------|-------------|
| L1 | Own | Own | Own | — |
| L2 | Own | Own | Own | — |
| L3 | Own | Own | Own | — |
| L4 | — | — | — | **Own** |
| L5 | — | — | — | **Own** |
| L6 | — | — | — | **Own** |
| L7 | Partial | Partial | Partial | **Own** |

---

## Debugging by Layer

When something feels messy, ask:

> "Why is L1 logic talking to L4?"
> "Why is L2 importing L5?"
> "Why does L4 know about console auth?"

These questions reveal architecture rot.

### Common Layer Violations

| Symptom | Likely Violation |
|---------|------------------|
| UI makes DB calls | L1 → L6 skip |
| Workers import console APIs | L5 → L2 reverse |
| Adapters run on schedule | L3 acting as L5 |
| Domain engines check auth | L4 → L2 coupling |
| Products own detection logic | L1/L2/L3 → L4 theft |

---

## How to Apply This

### 1. Mental Annotation

When opening any file, first ask:
> "Which layer am I in?"

Not:
> "Which product is this for?"

### 2. File Header Convention (Optional)

Add 1-line layer header to important files:

```python
# Layer: L3 — Boundary Adapter (Console → Platform)
```

```typescript
// Layer: L1 — Product Experience (AI Console)
```

### 3. Code Review Gate

Before approving changes, verify:
- No upward layer violations (L5 → L2)
- No cross-layer theft (L1 owning L4 logic)
- Product code stays in L1-L3

---

## Why This Matters

| Old View | New View |
|----------|----------|
| "Which product owns this?" | "Which layer is this?" |
| Horizontal slices (confusing) | Vertical stack (clear) |
| Product boundaries feel arbitrary | Layer boundaries feel natural |
| Ownership debates | Obvious classification |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│           7-LAYER MENTAL MODEL                              │
├─────────────────────────────────────────────────────────────┤
│  L1: EXPERIENCE    │ Pages, routes, presentation            │
│  L2: PRODUCT API   │ Console routes, auth-scoped            │
│  L3: ADAPTERS      │ Translation: platform → product        │
│  ─────────────────── PRODUCT BOUNDARY ─────────────────────│
│  L4: DOMAIN        │ Truth & rules (NEVER product-owned)    │
│  L5: EXECUTION     │ Workers, jobs, schedulers              │
│  L6: PLATFORM      │ Auth, SDK, DB, telemetry               │
│  L7: OPS           │ Deploy, CI, migrations                 │
├─────────────────────────────────────────────────────────────┤
│  PRODUCT = L1 + L2 + L3 (slice, not horizontal cut)        │
│  LAYER JUMP = Bug or architecture rot                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Refinements (v1.1)

### Cross-Layer Communication Rules

| From | Can Call | Cannot Call |
|------|----------|-------------|
| L1 | L2, L3 | L4, L5, L6, L7 |
| L2 | L3, L4 | L1, L5, L6 |
| L3 | L4, L6 | L1, L2, L5 |
| L4 | L5, L6 | L1, L2, L3 |
| L5 | L4, L6 | L1, L2, L3 |
| L6 | L6 (peers) | L1-L5 (except by request) |
| L7 | Any | N/A (ops privilege) |

### L3 Adapter Thickness Rule

```
L3 Adapter Constraints:
- Maximum 200 lines of code
- No business logic (only translation)
- No state mutation (read-only or ephemeral)
- No independent execution (always called by L2)

If violated → promote to L4 or split into L3 + L4
```

### L2 Subcategories

```
L2a — Product APIs (Console-scoped)
      - verify_console_token auth
      - Customer Console routes (guard.py)

L2b — Public APIs (Tenant-scoped)
      - verify_api_key / tier-gating auth
      - SDK-callable routes (v1_killswitch.py)
```

### L6 Includes Shared UI

```
L6 Platform Substrate includes:
- Backend: Auth, SDK, DB models, telemetry
- Frontend: Design system, shared hooks, common utilities
```

---

## Related PINs

- [PIN-235](PIN-235-products-first-architecture-migration.md) - Products-First Architecture
- [PIN-237](PIN-237-codebase-registry-survey.md) - Codebase Registry Survey
- [PIN-238](PIN-238-code-registration-evolution-governance.md) - Code Registration Governance
- [PIN-239](PIN-239-product-boundary-enforcement.md) - Product Boundary Enforcement

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-29 | Initial creation. Constitutional mental model established. |
