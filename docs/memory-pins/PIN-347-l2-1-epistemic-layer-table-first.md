# PIN-347: L2.1 Epistemic Orchestration Layer — Table-First Design

**Status:** IN_PROGRESS
**Created:** 2026-01-07
**Category:** Architecture / Layer Design
**Milestone:** L2.1 Epistemic Layer Foundation
**Related PINs:** PIN-269 (Claude Authority Spine)

---

## Executive Summary

Established **L2.1 — Epistemic Orchestration & Presentation Layer** with a **table-first design system**. Tables are canonical; MD documentation is reference-only.

**Core Principle:**
> Tables define L2.1. MD explains L2.1. UI skins L2.1. Nothing else decides.

---

## Progress Tracker

### Phase 1: Template Creation (COMPLETE)

| Task | Status | Artifact |
|------|--------|----------|
| Create ESM-L2.1 Template | ✅ COMPLETE | `docs/layers/L2_1/ESM_L2_1_TEMPLATE.md` |
| Define DSM-L2.1 (Domains) | ✅ COMPLETE | `docs/layers/L2_1/DSM_L2_1.md` |
| Freeze OSD-L2.1 (Orders) | ✅ COMPLETE | `docs/layers/L2_1/OSD_L2_1.md` |
| Declare IPC-L2.1 (Projection) | ✅ COMPLETE | `docs/layers/L2_1/IPC_L2_1.md` |
| Create UIS-L2.1 (UI Intent) | ✅ COMPLETE | `docs/layers/L2_1/UIS_L2_1.md` |
| Create FCL-L2.1 (Facilitation) | ✅ COMPLETE | `docs/layers/L2_1/FCL_L2_1.md` |
| Create Governance Assertions | ✅ COMPLETE | `docs/layers/L2_1/L2_1_GOVERNANCE_ASSERTIONS.md` |

**Total:** 7 files, ~2,600 lines

### Phase 2: Table-First Amendment (COMPLETE)

| Task | Status | Artifact |
|------|--------|----------|
| A1: Amend MDs with reference declaration | ✅ COMPLETE | 6 MD files amended |
| A2: Add Table Mapping sections | ✅ COMPLETE | All MDs have mapping |
| A3: Add prohibition headers | ✅ COMPLETE | No new semantics in MD |
| B1: Create SQL schema definitions | ✅ COMPLETE | 3 schema files |
| B2: Create seed reference data | ✅ COMPLETE | 2 seed files (FROZEN) |
| B3: Create human-readable views | ✅ COMPLETE | 1 view file |
| C1: Define surface_id trace key | ✅ COMPLETE | `SURFACE_ID_SPECIFICATION.md` |
| C2: Create L2_1_USAGE_MAP.md | ✅ COMPLETE | 15 surfaces tracked |
| C3: Create governance assertions | ✅ COMPLETE | `L2_1_ASSERTIONS.md` |

**Total:** 9 new files, 6 amended files, ~2,300 lines

### Phase 2.5: L2 Constitution Tables (COMPLETE)

| Task | Status | Artifact |
|------|--------|----------|
| Create l2_1_surface_registry schema | ✅ COMPLETE | `schema/l2_1_surface_registry.schema.sql` |
| Create l2_1_action_capabilities schema | ✅ COMPLETE | `schema/l2_1_action_capabilities.schema.sql` |
| Seed all 15 surfaces | ✅ COMPLETE | `seeds/l2_1_surface_registry.seed.sql` |
| Seed action capabilities (40 actions) | ✅ COMPLETE | `seeds/l2_1_action_capabilities.seed.sql` |

**Key Governance:**
- L2.1 surfaces: READ/DOWNLOAD only (29 actions)
- GC_L actions: WRITE/ACTIVATE only (11 actions) — all require confirmation

**Action Distribution:**

| Domain | READ | DOWNLOAD | WRITE | ACTIVATE |
|--------|------|----------|-------|----------|
| Overview | 2 | 1 | 0 | 0 |
| Activity | 3 | 2 | 0 | 0 |
| Incidents | 4 | 3 | 3 | 0 |
| Policies | 4 | 4 | 3 | 4 |
| Logs | 3 | 3 | 0 | 0 |
| **Total** | **16** | **13** | **6** | **4** |

### Phase 3: Codebase Mapping (PENDING)

| Task | Status | Notes |
|------|--------|-------|
| Codebase Signal Inventory | ⏳ PENDING | Map existing code to domains |
| Populate ESM-L2.1 Instances | ⏳ PENDING | One matrix per domain |
| Gap Classification | ⏳ PENDING | Absent / unsafe / mis-scoped |
| L1 Skin Readiness Check | ⏳ PENDING | Verify UIS fields resolvable |

### Phase 4: Database Application (PENDING)

| Task | Status | Notes |
|------|--------|-------|
| Apply schemas to Neon | ⏳ PENDING | Run DDL |
| Run seed data | ⏳ PENDING | Populate frozen domains/orders |
| Enable governance triggers | ⏳ PENDING | Freeze protection |
| CI integration | ⏳ PENDING | Assertion validation |

---

## L2.1 Naming System (CANONICAL)

### Layer Name

**L2.1 — Epistemic Orchestration & Presentation Layer**

Short Form: `L2_1`

### Schema IDs

| Schema ID | Full Name | Purpose |
|-----------|-----------|---------|
| `ESM_L2_1` | Epistemic Surface Matrix | Primary schema — what can be shown |
| `DSM_L2_1` | Domain Surface Manifest | Declares L1 domains (frozen) |
| `OSD_L2_1` | Order Surface Definition | O1-O5 epistemic orders (frozen) |
| `IPC_L2_1` | Interpreter Projection Contract | Phase-2 projection rules |
| `FCL_L2_1` | Facilitation Classification Layer | Non-authoritative signals |
| `UIS_L2_1` | UI Intent Surface | Visibility, consent, affordances |

### Relationship Map

```
Phase 2 Interpreter
        ↓
IPC-L2.1 (projection)
        ↓
ESM-L2.1 (epistemic surface)
        ↓
{ FCL-L2.1 | UIS-L2.1 | GC_L proposals }
        ↓
L1 UI (skin only)
```

**Direction Rule:** No arrows may be reversed.

---

## Frozen Domains (L1 Constitution)

| Domain ID | Name | Core Question |
|-----------|------|---------------|
| `overview` | Overview | Is the system okay right now? |
| `activity` | Activity | What ran / is running? |
| `incidents` | Incidents | What went wrong? |
| `policies` | Policies | How is behavior defined? |
| `logs` | Logs | What is the raw truth? |

**Total:** 5 domains, 8 subdomains, 15 topics

---

## Frozen Orders (O1-O5)

| Order | Name | Depth | Terminal |
|-------|------|-------|----------|
| O1 | Snapshot | shallow | No |
| O2 | Presence | list | No |
| O3 | Explanation | single | No |
| O4 | Context | relational | No |
| O5 | Proof | terminal | **Yes** |

**O5 is immutable proof only — no further navigation.**

---

## Surface ID Format

```
{DOMAIN}.{SUBDOMAIN}.{TOPIC}

Examples:
  OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS
  ACTIVITY.EXECUTIONS.ACTIVE_RUNS
  INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS
```

**Regex:** `^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$`

---

## Governance Assertions (GA-001 to GA-010)

| ID | Assertion | Severity |
|----|-----------|----------|
| GA-001 | No Authority | CRITICAL |
| GA-002 | No Execution | CRITICAL |
| GA-003 | No Learning | CRITICAL |
| GA-004 | No Cross-Tenant Scope | CRITICAL |
| GA-005 | Phase-2 Projection Only | HIGH |
| GA-006 | L1 Constitution Alignment | HIGH |
| GA-007 | Order Contract Compliance | HIGH |
| GA-008 | Replay Invariant | HIGH |
| GA-009 | Non-Authoritative Signals Only | MEDIUM |
| GA-010 | UI Intent Not Layout | MEDIUM |

---

## File Inventory

### Documentation (`docs/layers/L2_1/`)

```
ESM_L2_1_TEMPLATE.md      # Master template
DSM_L2_1.md               # Domain manifest
OSD_L2_1.md               # Order definitions
IPC_L2_1.md               # Projection contract
UIS_L2_1.md               # UI intent surface
FCL_L2_1.md               # Facilitation layer
L2_1_GOVERNANCE_ASSERTIONS.md  # High-level assertions
```

### Design (`design/l2_1/`)

```
schema/
  l2_1_epistemic_surface.schema.sql    # Main ESM table DDL
  l2_1_domain_registry.schema.sql      # Domain registry DDL
  l2_1_order_definitions.schema.sql    # Order definitions DDL
  l2_1_surface_registry.schema.sql     # L2 Constitution (Phase 2.5)
  l2_1_action_capabilities.schema.sql  # Action capability routing (Phase 2.5)

seeds/
  l2_1_domain_registry.seed.sql        # 5 domains, 8 subdomains, 15 topics
  l2_1_order_definitions.seed.sql      # O1-O5 with transitions
  l2_1_surface_registry.seed.sql       # 15 surface definitions (Phase 2.5)
  l2_1_action_capabilities.seed.sql    # 40 action capabilities (Phase 2.5)

views/
  l2_1_epistemic_surface.view.md       # Auto-generated reference

trace/
  SURFACE_ID_SPECIFICATION.md          # Trace key format
  L2_1_USAGE_MAP.md                    # Usage tracking

governance/
  L2_1_ASSERTIONS.md                   # Table-level assertions
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Source of truth | Tables (not MD) | Prevents terminology drift |
| Domain set | Frozen (5 domains) | Aligned with L1 Constitution |
| Order set | Frozen (O1-O5) | Epistemic depth is fixed |
| Authority | Always NONE | L2.1 is presentation only |
| Tenant isolation | Always true | Security boundary |
| Enrichment | Always false | Phase-2 projection only |
| Action routing | L2.1=READ/DOWNLOAD, GC_L=WRITE/ACTIVATE | Constitutional separation of concerns |
| GC_L confirmation | Required for all mutations | Human safety requirement |

---

## Claude Stop Conditions

Claude must **STOP and ASK** if:

- Domain requested doesn't exist in L1 Constitution
- Topic cannot map to a real system boundary
- Order implies action or enforcement
- Data violates replay invariants

**No silent assumptions allowed.**

---

## Next Steps

1. **Phase 3:** Map codebase to L2.1 surfaces
2. **Phase 4:** Apply schemas to database
3. **CI Integration:** Add assertion validation to pipeline
4. **UI Implementation:** Wire surfaces to components

---

## References

- `docs/layers/L2_1/` — All L2.1 documentation
- `design/l2_1/` — Table-first design files
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md` — L1 Authority
- PIN-269 (Claude Authority Spine)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-07 | Created PIN-347 |
| 2026-01-07 | Phase 1 complete: 7 template files |
| 2026-01-07 | Phase 2 complete: Table-first amendment |
| 2026-01-07 | 15 surface IDs defined and tracked |
| 2026-01-07 | Phase 2.5 complete: L2 Constitution tables |
| 2026-01-07 | l2_1_surface_registry schema + 15 surfaces seeded |
| 2026-01-07 | l2_1_action_capabilities schema + 40 actions seeded |
| 2026-01-07 | Action routing enforced: L2.1=READ/DOWNLOAD, GC_L=WRITE/ACTIVATE |
