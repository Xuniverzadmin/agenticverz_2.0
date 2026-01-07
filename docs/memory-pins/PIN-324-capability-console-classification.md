# PIN-324: Capability Console Classification (L2.1/L1 Reference)

**Status:** COMPLETE
**Created:** 2026-01-06
**Category:** Governance / Console Classification
**Scope:** L2.1 and L1 Capability Visibility Reference
**Prerequisites:** PIN-323 (L2-L2.1 Audit Reinforcement)

---

## Objective

Provide a definitive reference for which capabilities are visible in which console, for L2.1 (frontend API clients) and L1 (product experience) consumption.

---

## Console Domains

| Console | URL | Scope | Data Boundary |
|---------|-----|-------|---------------|
| **Customer Console** | console.agenticverz.com | Single tenant | Tenant-isolated |
| **Founder Console** | fops.agenticverz.com | Cross-tenant | Founder-only |

---

## Capability Distribution Summary

| Category | Count | Capabilities |
|----------|-------|--------------|
| Customer-Only | 4 | CAP-003, CAP-004, CAP-014, CAP-018 |
| Founder-Only | 3 | CAP-005, CAP-011, CAP-017 |
| Shared | 3 | CAP-001, CAP-002, CAP-009 |
| Internal | 6 | CAP-006, CAP-007, CAP-010, CAP-012, CAP-013, CAP-015 |
| SDK-Only | 2 | CAP-008, CAP-016 |
| **Total** | **18** | |

---

## FOUNDER CONSOLE (fops.agenticverz.com)

### Founder-Only Capabilities

| ID | Name | Key Routes |
|----|------|------------|
| **CAP-005** | Founder Console | `/ops/*`, `/founder/timeline/*`, `/founder/controls/*`, `/founder/explorer/*`, `POST /founder/actions/*` |
| **CAP-011** | Governance Orchestration | `/founder/review/*`, `/api/v1/discovery/*`, `POST /founder/review/{id}/approve`, `POST /founder/review/{id}/reject` |
| **CAP-017** | Cross-Project Aggregation | PLANNED (if implemented, founder-only) |

### Shared Capabilities — Founder Routes

| ID | Name | Founder-Only Routes | Separation |
|----|------|---------------------|------------|
| **CAP-001** | Replay | `POST /api/v1/replay/execute`, killswitch, acknowledge, freeze, trace creation | READ customer, EXECUTE founder |
| **CAP-002** | Cost Simulation | reset, validate, canary run/reports | READ customer, CONTROL founder |
| **CAP-009** | Policy Engine | `POST/PUT/DELETE /api/v1/policies` | READ customer, MUTATE founder |

---

## CUSTOMER CONSOLE (console.agenticverz.com)

### Customer-Only Capabilities

| ID | Name | Routes | Notes |
|----|------|--------|-------|
| **CAP-003** | Policy Proposals | `GET /api/v1/policy-proposals/*` | READ-ONLY advisory (PB-S4) |
| **CAP-004** | Prediction Plane | `GET /api/v1/predictions/*` | READ-ONLY advisory (PB-S5) |
| **CAP-014** | Memory System | `GET /api/v1/memory/*`, `GET /api/v1/embedding/*` | READ-ONLY |
| **CAP-018** | Integration Platform | `GET /api/v1/integration/*`, `GET /api/v1/recovery/*`, checkpoints, stats, graduation | READ-ONLY |

### Shared Capabilities — Customer Routes

| ID | Name | Customer Routes | Notes |
|----|------|-----------------|-------|
| **CAP-001** | Replay + Activity/Logs | replay slice/summary/timeline/explain, guard status/incidents/keys/settings, traces, failures | Tenant-scoped audit trail |
| **CAP-002** | Cost Simulation | simulate, divergence, status, incidents, datasets, scenarios | Advisory-only |
| **CAP-009** | Policy Engine | `GET /api/v1/policies/*`, `GET /guard/policies/*` | View only |

---

## NOT CONSOLE-VISIBLE

### Internal Capabilities (6)

| ID | Name | Reason |
|----|------|--------|
| **CAP-006** | Authentication | Delegated to Clerk |
| **CAP-007** | Authorization (RBAC v2) | Internal middleware |
| **CAP-010** | CARE-L Routing | Internal routing |
| **CAP-012** | Workflow Engine | Internal execution |
| **CAP-013** | Learning Pipeline | Internal processing |
| **CAP-015** | Optimization Engine | Internal system |

### SDK-Only Capabilities (2)

| ID | Name | Reason |
|----|------|--------|
| **CAP-008** | Multi-Agent Orchestration | SDK handles invocation |
| **CAP-016** | Skill System | SDK capability |

---

## Key Rules (NON-NEGOTIABLE)

| Rule | Enforcement |
|------|-------------|
| Customer console = tenant-isolated only | No cross-tenant data |
| All customer routes are READ-ONLY | No mutations from customer console |
| Shared capabilities have explicit route separation | Customer READ, Founder MUTATE |
| SDK capabilities never exposed to consoles | CAP-008, CAP-016 |
| Internal capabilities are transparent | Middleware, no direct API |

---

## Visual Reference

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPABILITY DISTRIBUTION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CUSTOMER CONSOLE (console.agenticverz.com)                         │
│  ├── Customer-Only: 4 capabilities                                  │
│  │   └── CAP-003, CAP-004, CAP-014, CAP-018                         │
│  └── Shared (READ): 3 capabilities                                  │
│      └── CAP-001, CAP-002, CAP-009                                  │
│                                                                     │
│  FOUNDER CONSOLE (fops.agenticverz.com)                             │
│  ├── Founder-Only: 3 capabilities                                   │
│  │   └── CAP-005, CAP-011, CAP-017                                  │
│  └── Shared (MUTATE): 3 capabilities                                │
│      └── CAP-001, CAP-002, CAP-009                                  │
│                                                                     │
│  NOT CONSOLE-VISIBLE                                                │
│  ├── Internal: 6 capabilities                                       │
│  │   └── CAP-006, CAP-007, CAP-010, CAP-012, CAP-013, CAP-015       │
│  └── SDK-Only: 2 capabilities                                       │
│      └── CAP-008, CAP-016                                           │
│                                                                     │
│  TOTAL: 18 capabilities                                             │
│  ├── Console-visible: 10 (7 customer + 6 founder, 3 shared)         │
│  └── Not visible: 8 (6 internal + 2 SDK)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Artifacts

| Artifact | Path |
|----------|------|
| Console Classification YAML | `docs/capabilities/CONSOLE_CLASSIFICATION.yaml` |
| Capability Registry | `docs/capabilities/CAPABILITY_REGISTRY.yaml` |
| Route Enumeration | `docs/discovery/PIN-323_ROUTE_ENUMERATION.md` |

---

## References

- PIN-323: L2-L2.1 Audit Reinforcement (COMPLETE)
- PIN-322: L2-L2.1 Progressive Activation (COMPLETE)
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md

---

## Updates

### 2026-01-06: PIN Created
- Definitive console classification reference created
- 18 capabilities classified across 5 categories
- Customer vs Founder route separation documented
