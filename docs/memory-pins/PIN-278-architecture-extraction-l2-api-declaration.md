# PIN-278: Architecture Extraction & L2 API Declaration

**Status:** ✅ COMPLETE
**Created:** 2026-01-02
**Category:** Architecture / Declaration

---

## Summary

Declarative architecture extraction producing frozen ARCH_DECLARATION, L2_API_CONTRACT, and component inventory for frontend planning handoff.

---

## Details

## Overview

Completed authoritative architecture extraction from the AOS codebase. This extraction:
- Declares (not discovers) the actual architecture
- Produces frozen artifacts for frontend planning
- Reconciles with system truth (BLCA verified)
- Leaves no room for improvisation

## Artifacts Produced

| Artifact | Path | Purpose |
|----------|------|---------|
| ARCH_SCOPE.yaml | docs/architecture/ | Extraction boundaries (frozen) |
| component_inventory.json | artifacts/architecture/ | Full component list (326 files) |
| ARCH_GRAPH.md | docs/architecture/ | Layer model + connections |
| ARCH_DECLARATION.md | docs/architecture/ | Frozen architecture declaration |
| L2_API_INVENTORY.json | artifacts/apis/ | 336 routes with categories |
| L2_API_CONTRACT.md | docs/apis/ | Frontend-facing API contracts |
| DRIFT_REPORT.md | artifacts/architecture/ | Reconciliation (CLEAN) |

## Key Metrics

| Metric | Value |
|--------|------:|
| Total files scanned | 326 |
| Total routes | 336 |
| Layer header coverage | 71.5% |
| BLCA violations | 0 |
| Drift status | CLEAN |

## Layer Breakdown

| Layer | Name | Files | Components | Routes | Coverage |
|-------|------|------:|----------:|-------:|---------:|
| L2 | Product APIs | 34 | 693 | 354 | 29.4% |
| L3 | Boundary Adapters | 27 | 98 | 0 | 96.3% |
| L4 | Domain Engines | 165 | 1130 | 7 | 64.2% |
| L5 | Execution & Workers | 24 | 124 | 0 | 70.8% |
| L6 | Platform Substrate | 76 | 538 | 12 | 97.4% |

## Route Categories (Frontend)

| Category | Routes | Purpose |
|----------|-------:|---------|
| core | 45 | Auth, execution, tenants |
| monitoring | 39 | Incidents, costs, status |
| governance | 120 | Agents, policies, recovery |
| operations | 36 | Founder/ops actions |
| supporting | 30 | Traces, memory, embedding |
| internal | 35 | Not for customer frontend |

## Top Directories by Components

| Directory | Files | Components | Routes |
|-----------|------:|----------:|-------:|
| api | 33 | 659 | 336 |
| services | 35 | 179 | 0 |
| auth | 19 | 149 | 8 |
| policy | 19 | 147 | 0 |
| skills | 26 | 136 | 0 |

## Coverage Gaps (Future Work)

| Directory | Files | Coverage | Priority |
|-----------|------:|--------:|----------|
| memory | 9 | 0.0% | HIGH |
| runtime | 2 | 0.0% | HIGH |
| costsim | 15 | 6.7% | MEDIUM |
| skills | 26 | 7.7% | MEDIUM |

## Architectural Invariants (Declared)

- **INV-001:** No layer may import from a higher layer
- **INV-002:** L4 owns meaning (all business logic)
- **INV-003:** L6 is terminal (no app dependencies)
- **INV-004:** L3 adapters < 200 LOC, no business logic
- **INV-005:** PostgreSQL is only truth store (Redis advisory)

## Commit

- **Hash:** 2a026868
- **Branch:** main
- **Pushed:** origin/main

## Next Steps

1. Frontend planning can proceed with declared truth
2. Classify 31 unassigned routes during journey mapping
3. Add layer headers to 107 files without declared purpose (lower priority)

## Reference

- PIN-240: Seven-Layer Codebase Mental Model (constitutional)
- PIN-245: Integration Integrity System
- PIN-248: Codebase Inventory & Layer System
