# PIN-303: Frontend Constitution Alignment System Survey

**Status:** COMPLETE
**Created:** 2026-01-05
**Category:** Governance / Frontend Constitution
**Milestone:** Tech Debt Clearance
**Continues:** PIN-302

---

## Summary

Executed comprehensive system survey for Frontend Constitution Alignment. Collected facts across 8 sections: Architecture, L2 APIs, Data Objects, RBAC, Frontend, Testing, Constraints, and Known Unknowns. No interpretation—facts only.

---

## Details

### Purpose

This survey was executed to establish ground truth before any frontend constitution work. Prior work (PIN-300 through PIN-302) was **semantic governance**—this survey is **system introspection**.

### Survey Scope

| Section | Coverage | Status |
|---------|----------|--------|
| A. Architecture Ground Truth | L1-L8 layers, service map | COMPLETE |
| B. L2 API Survey | 38 routers, ~200+ endpoints | COMPLETE |
| C. Data Objects & Truth Sources | 15+ objects, immutability rules | COMPLETE |
| D. Authority & RBAC Reality | 7 roles, cross-tenant boundaries | COMPLETE |
| E. Frontend Reality Check | 2 consoles, 8+ pages | COMPLETE |
| F. Testing & Verification | CLI, 9 test categories | COMPLETE |
| G. Known Constraints & Freezes | 5 frozen domains, 6 hard rules | COMPLETE |
| H. Known Unknowns | 4 partial, 3 suspected, 4 messy | COMPLETE |

### Key Findings (Facts Only)

#### Architecture
- 8 layers (L1-L8) all present and implemented
- 12 services mapped with ownership and mutation rights
- L4 owns domain semantics; L6 owns persistence

#### L2 API Surface
- 38 API routers in `/backend/app/api/`
- ~200+ HTTP endpoints
- Mix of stored (incidents, logs) and derived (costs, patterns) outputs

#### Data Objects
- 15+ core objects with defined immutability
- Runs immutable after execution (PB-S1)
- Traces constitutionally immutable (S6)
- Policies versioned, not overwritten

#### RBAC Reality
- 7 actual roles: OWNER, ADMIN, DEV, VIEWER, MACHINE, FOUNDER, OPERATOR
- M28 (presentation) → M7 (canonical) one-way mapping
- Cross-tenant reads: Founder-only with isolation guard
- Cross-project aggregation: NOT PRESENT in customer paths

#### Frontend State
- Customer AI Console: PRESENT (`/guard/*` backend, React frontend)
- Founder Ops Console: Backend ready, frontend UNKNOWN
- 8+ pages mapped with data fetches and actions

#### Known Unknowns
- Founder Console Frontend: Location unknown
- Clerk Integration: STUB only
- Cost Simulation UI: Backend only
- M28 vs M7 Role Duality: Transitional

### Survey Discipline

The following rules were enforced:
1. Fill every cell
2. If unknown, write UNKNOWN
3. If not present, write NOT PRESENT
4. No inference or explanation
5. No opinions or future intent

### What This Unlocks

With survey complete, the following can now proceed:
1. Constitutional alignment analysis (mechanical)
2. Gap identification (what exists vs what's declared)
3. Frontend binding to frozen intents (zero inference)

## Files

- Survey output in conversation (not persisted as file)
- Template provided by founder for structured collection

## Key Statistics

| Metric | Value |
|--------|-------|
| API Routers | 38 |
| HTTP Endpoints | ~200+ |
| Data Objects | 15+ |
| Roles | 7 |
| Frozen Domains | 5 |
| Test Categories | 9 |
| Known Unknowns | 11 items |

## References

- CUSTOMER_CONSOLE_V1_CONSTITUTION.md — Frozen domains
- PIN-300 — Semantic Promotion Gate
- PIN-301 — L2 Intent Declaration Progress
- PIN-302 — Tier-2 Semantic Closure
- Phase A.5 Closure — Truth-grade invariants

---

## Related PINs

- [PIN-300](PIN-300-.md) — Semantic Promotion Gate
- [PIN-301](PIN-301-l2-intent-declaration-progress---semantic-promotion-gate.md) — Intent Progress
- [PIN-302](PIN-302-tier-2-semantic-closure---policies-and-ai-console-keys.md) — Tier-2 Closure
