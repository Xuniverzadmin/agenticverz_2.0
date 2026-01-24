# PIN-260: Product Architecture Clarity — One Console, All Products

**Serial:** PIN-260
**Title:** Product Architecture Clarity — One Console, All Products
**Category:** Architecture / Product Strategy
**Status:** RATIFIED
**Created:** 2025-12-31
**Authority:** Human-approved correction

---

## Executive Summary

This PIN documents a critical architectural clarification:

> **The AI Console is not one product among many — it IS the product container.**
> **All product capabilities fit within the frozen console framework.**
> **No new architecture is required.**

This prevents future sessions from:
- Proposing "new products" that are actually existing domains
- Suggesting architectural changes when productization is needed
- Conflating feature gaps with architecture gaps

---

## The Frozen Console Framework

The Customer Console v1 Constitution (FROZEN 2025-12-29) defines:

```
┌────────────────────────────────────────────────────────────────┐
│  AI CONSOLE — FROZEN STRUCTURE                                 │
├────────────────────────────────────────────────────────────────┤
│  CORE LENSES (Sidebar — FROZEN)                                │
│                                                                │
│    Overview    → "Is the system okay right now?"               │
│    Activity    → "What ran / is running?"                      │
│    Incidents   → "What went wrong?"                            │
│    Policies    → "How is behavior defined?"                    │
│    Logs        → "What is the raw truth?"                      │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  CONNECTIVITY                                                  │
│    Integrations │ API Keys                                     │
├────────────────────────────────────────────────────────────────┤
│  ACCOUNT (Secondary Navigation)                                │
│    Projects │ Users │ Profile │ Billing │ Support              │
└────────────────────────────────────────────────────────────────┘
```

### What the Framework Allows

Per Constitution Section 3.3:

| Level | Definition | Expandable? |
|-------|------------|-------------|
| **Domain** | Fundamental user question | NO — Frozen |
| **Subdomain** | Real system boundary | Cautiously |
| **Topic** | View or capability | YES — Safe to add |
| **Orders (O1-O5)** | Depth levels | YES — Safe to add |

**Key insight:** New features fit as Topics within frozen domains. The framework accommodates unlimited feature addition without structural change.

---

## Product-to-Domain Mapping (AUTHORITATIVE)

| "Product" Name | Actually Is | Console Domain | Evidence |
|----------------|-------------|----------------|----------|
| AI Cost Guard | Cost visibility feature | **Overview** + **Activity** | `backend/app/api/cost_guard.py` |
| AI Incident Console | The Incidents domain | **Incidents** | `IncidentsPage.tsx` |
| Agent Governance Platform | The Policies domain | **Policies** | `PoliciesPage.tsx`, `policy/models.py` |
| Compliance Evidence Generator | The Logs domain | **Logs** | `LogsPage.tsx`, trace system |
| Execution Monitor | The Activity domain | **Activity** | `ActivityPage.tsx` |
| System Health Dashboard | The Overview domain | **Overview** | `OverviewPage.tsx` |

### External Products (Not Console)

| Product | Location | Status |
|---------|----------|--------|
| Python SDK | PyPI: `aos-sdk` | PUBLISHED |
| JavaScript SDK | npm: `@agenticverz/aos-sdk` | PUBLISHED |
| Ops Console | `pages/ops/` | Separate jurisdiction |
| Founder Console | `pages/fdr/` | Separate jurisdiction |

---

## The Correction

### What Was Wrong

Previous analysis suggested "missing products" that were actually:
1. **Domain names** presented as product names
2. **Features** that fit within existing domains
3. **Architectural choices** misidentified as gaps

### What Is True

| Misconception | Reality |
|---------------|---------|
| "We need an Incident Console" | Incidents domain EXISTS |
| "We need a Governance Platform" | Policies domain EXISTS |
| "We need Cost Intelligence" | Overview + Activity + `/guard/costs/*` EXISTS |
| "We need Compliance Evidence" | Logs domain + trace system EXISTS |
| "SDK needs packaging" | SDK is PUBLISHED on PyPI + npm |

### The Hard Infrastructure Is Built

The system already has:
- Recovery classes (R1/R2/R3)
- Kill-switch (K-1 to K-5 invariants)
- Cost anomaly detection
- Policy evaluation engine
- Decision records with full provenance
- SSE streaming for real-time visibility
- Deterministic trace/replay system

---

## Productization vs Architecture

### Productization Gaps (What Remains)

These are NOT architecture gaps — they are product definition work:

| Gap Type | Description |
|----------|-------------|
| **SKU Definition** | Naming what already exists implicitly |
| **Feature Polish** | Completing Topics within domains |
| **UX Scaffolding** | Guided setup for non-expert users |
| **Customer Defaults** | Pre-approved policy bundles |
| **Documentation** | User-facing feature documentation |

### True Architecture Gaps

Only one remains genuinely architectural:

| Gap | Status | Rationale |
|-----|--------|-----------|
| Federated Agent Identity | **Intentionally Deferred** | Requires new identity layer, expands threat model |

---

## Governance Rules

### What This PIN Prevents

1. **Domain Proliferation**: No suggesting new sidebar domains
2. **Architecture Inflation**: No proposing "new products" that are existing domains
3. **Gap Confusion**: Distinguishing productization from architecture work

### What This PIN Allows

1. **Topic Addition**: New features within existing domains
2. **Order Expansion**: Deeper views (O1-O5) within topics
3. **Feature Polish**: Completing existing capabilities
4. **UX Improvement**: Better surfacing of existing functionality

---

## Console Jurisdiction Boundaries

| Console | Scope | Data Boundary |
|---------|-------|---------------|
| **Customer Console** | Single tenant | Tenant-isolated |
| **Founder Console** | Cross-tenant | Founder-only |
| **Ops Console** | Infrastructure | Operator-only |

Same domains may exist across consoles, but **data, scope, and authority differ**.

---

## Session Bootstrap Integration

This PIN is referenced in `SESSION_PLAYBOOK.yaml` under product architecture rules.

### Quick Reference for Sessions

```
PRODUCT ARCHITECTURE TRUTH (PIN-260)

1. AI Console IS the product container
2. 5 Core Domains are FROZEN: Overview, Activity, Incidents, Policies, Logs
3. "Products" map to domains, not new architecture
4. Features fit as Topics within domains
5. SDK is PUBLISHED (PyPI + npm)
6. Only true gap: Federated Agent Identity (deferred)

If suggesting a "new product" → check if it's actually a domain feature
If suggesting "missing architecture" → check if it's productization work
```

---

## One-Line Truth

> **The hard infrastructure is already built. What remains is productization discipline: feature polish within frozen domains.**

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `CUSTOMER_CONSOLE_V1_CONSTITUTION.md` | Frozen console structure |
| `PIN-259` | Phase G Steady-State Governance |
| `PIN-035` | SDK Package Registry (published) |
| `SESSION_PLAYBOOK.yaml` | Session governance |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | PIN-260 created and ratified |
