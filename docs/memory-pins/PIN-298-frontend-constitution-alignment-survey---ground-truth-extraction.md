# PIN-298: Frontend Constitution Alignment Survey - Ground Truth Extraction

**Status:** ✅ COMPLETE
**Created:** 2026-01-05
**Category:** Governance / Survey
**Milestone:** Frontend Constitution

---

## Summary

Comprehensive system survey extracting ground truth for frontend constitution alignment. 358 L2 endpoints catalogued, 8 layers verified, 33 object families identified, all frozen domains confirmed.

---

## Details

## Survey Objective

Extract ground-truth data about existing architecture, capabilities, and constraints so frontend analysis can be done without invention, inference, or preemptive design.

**Method:** Codebase exploration, governance document extraction, API introspection
**Date:** 2026-01-05

---

## Key Findings

### A. Layer Inventory (All 8 Layers Implemented)

| Layer | Name | Files | Status |
|-------|------|-------|--------|
| L1 | Product Experience | website/aos-console/ | IMPLEMENTED |
| L2 | Product APIs | 38 routers | IMPLEMENTED |
| L3 | Boundary Adapters | 13 adapters | IMPLEMENTED |
| L4 | Domain Engines | 60 files | IMPLEMENTED |
| L5 | Execution & Workers | 46 files | IMPLEMENTED |
| L6 | Platform Substrate | 31+ files | IMPLEMENTED |
| L7 | Ops & Deployment | 114 scripts | IMPLEMENTED |
| L8 | Catalyst / Meta | 172 tests | IMPLEMENTED |

**Enforcement:** BLCA reports 0 violations (CLEAN)

---

### B. L2 API Surface

- **Total Endpoints:** 358
- **Read-Only:** 186 (52%)
- **Mutating:** 172 (48%)
- **Object Families:** 33
- **Auth Scopes:** 4 (none/middleware, api_key, console, fops)

**Console-Scoped (`/guard/*`):** 26 endpoints
**FOPS-Scoped (`/ops/*`):** 21 endpoints

---

### C. Data Objects

- **Total Objects:** 20+ SQLModel classes
- **Append-Only:** 8 (UsageRecord, AuditLog, Traces, etc.)
- **Conditionally Immutable:** 3 (WorkerRun, SystemContract, GovernanceJob)
- **Supersession-Only:** 2 (GovernanceSignal, FounderAction)

---

### D. RBAC State

- **RBACv1:** Enforcement authority (currently `RBAC_ENFORCE=false`)
- **RBACv2:** Shadow mode (reference authority)
- **Roles:** 10 defined (founder, operator, admin, developer, viewer, machine, ci, replay, etc.)
- **Cross-Tenant:** Operator bypass exists for founders

---

### E. Frontend Consoles

| Console | Path | Audience | Status |
|---------|------|----------|--------|
| Customer Console | `/guard/*` | Customers | IMPLEMENTED |
| Founder Ops | `/ops/*` | Founders | IMPLEMENTED |
| Landing | `/` | Public | IMPLEMENTED |

**Subdomain Routing:** PLANNED (not wired)

---

### F. Frozen Domains (v1 Constitution)

1. **Overview** - Is the system okay right now?
2. **Activity** - What ran / is running?
3. **Incidents** - What went wrong?
4. **Policies** - How is behavior defined?
5. **Logs** - What is the raw truth?

---

### G. Closed Phases

- Phase-1 (Platform Monitoring): CLOSED
- Part-2 (CRM Governance): CLOSED
- Phase-F (Structural Completion): CLOSED
- Phase-G (Steady-State): PERMANENT

---

### H. Known Unknowns

| Item | State |
|------|-------|
| 30+ untracked Part-2 files | NOT COMMITTED |
| RBAC Enforcement | DISABLED |
| JWT Verification | DISABLED |
| Subdomain routing | NOT WIRED |
| 8 modified core files | UNCOMMITTED (lint fallout) |

---

## Survey Attestation

- Facts only: YES
- No interpretation: YES
- Unknowns labeled: YES

---

## References

- docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md
- docs/governance/PHASE_G_STEADY_STATE_GOVERNANCE.md
- PIN-290, PIN-297, PIN-284


---

## Related PINs

- [PIN-290](PIN-290-.md)
- [PIN-297](PIN-297-.md)
- [PIN-284](PIN-284-.md)
