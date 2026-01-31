# HOC Spine Topology Proposal — V1.5.0

**Status:** PROPOSED (pending ratification)
**Created:** 2026-01-28
**Supersedes:** general domain concept in HOC_LAYER_TOPOLOGY_V1.4.0

---

## Two Constitutions, One Topology

```
HOC
├── hoc_spine/                    SYSTEM CONSTITUTION
│   Defines: what, when, how for domain shared runtime,
│   orchestration, and lifecycle management.
│   Scope: Cross-domain. All domains depend on spine.
│   NOT a domain. Infrastructure that domains run on.
│
└── cus/{domain}/                 CUSTOMER CONSTITUTION(S)
    Defines: what, when, how for customer-facing functions
    (policy creation, LLM monitoring, incident capture, etc.)
    Scope: Per-domain. Domain-isolated.
    Each domain is a self-contained vertical.
```

---

## Layer Structure — Both Follow Same Layers

```
                    hoc_spine/                          cus/{domain}/
                    ──────────                          ─────────────
L4 Runtime          L4_runtime/                         —
                    ├── authority/                       (uses spine's L4)
                    ├── execution/
                    └── consequences/

Spine Services      services/                           —
                    ├── audit_store.py                   (domains import
                    ├── runtime_switch.py                 spine services
                    ├── contract_engine.py                legally)
                    ├── alerts_facade.py
                    ├── compliance_facade.py
                    ├── scheduler_facade.py
                    ├── monitors_facade.py
                    ├── lifecycle_facade.py
                    ├── retrieval_facade.py
                    ├── lifecycle_stages_base.py
                    ├── onboarding.py
                    ├── offboarding.py
                    ├── guard_write_engine.py
                    ├── cus_credential_service.py
                    ├── profile_policy_mode.py
                    └── retrieval_mediator.py

Spine Schemas       schemas/                            —
                    ├── rac_models.py
                    ├── common.py
                    └── response.py

Spine Drivers       drivers/                            —
                    ├── transaction_coordinator.py
                    ├── cross_domain.py
                    └── ...

L5 Engines          —                                   L5_engines/
                                                        (domain-specific
                                                         business logic)

L6 Drivers          —                                   L6_drivers/
                                                        (domain-specific
                                                         DB operations)
```

---

## Import Rules (Modified)

```
                  hoc_spine
                  ┌─────────────────────┐
                  │  L4_runtime          │
                  │    ↓                 │
                  │  services + schemas  │
                  │    ↓                 │
                  │  drivers             │
                  └────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
   cus/incidents/    cus/policies/    cus/analytics/  ...
   ┌────────────┐    ┌────────────┐   ┌────────────┐
   │ L2.1       │    │ L2.1       │   │ L2.1       │
   │  ↓         │    │  ↓         │   │  ↓         │
   │ L2 API     │    │ L2 API     │   │ L2 API     │
   │  ↓         │    │  ↓         │   │  ↓         │
   │ L3 Adapter │    │ L3 Adapter │   │ L3 Adapter │
   │  ↓         │    │  ↓         │   │  ↓         │
   │ L5 Engine ←┼────┼─ spine     │   │ L5 Engine  │
   │  ↓         │    │  ↓         │   │  ↓         │
   │ L6 Driver  │    │ L6 Driver  │   │ L6 Driver  │
   └────────────┘    └────────────┘   └────────────┘
```

### 5 Import Rules

| Rule | From | To | Legal? |
|------|------|----|--------|
| **SPINE-001** | Any domain layer (L3, L5) | `hoc_spine/services/`, `hoc_spine/schemas/` | **YES** — spine is shared infrastructure |
| **SPINE-002** | Any domain layer | `hoc_spine/L4_runtime/` | **YES** — all execution enters L4 once |
| **SPINE-003** | `hoc_spine/L4_runtime/` | Domain L5 engines | **YES** — L4 orchestrates L5 |
| **DOMAIN-001** | Domain A L5 | Domain B L5 | **FORBIDDEN** — cross-domain at L3 only |
| **DOMAIN-002** | Domain L2 | Domain L5 or L6 | **FORBIDDEN** — must go through L3 |

---

## What Changes from V1.4.0

| V1.4.0 | V1.5.0 | Why |
|--------|--------|-----|
| `general` is domain #1 with L4+L5+L6 | `general` is abolished. Split into `hoc_spine` (system constitution) + remaining domain-specific files redistributed | General was doing two jobs |
| L4 lives inside `general/` | L4 lives inside `hoc_spine/` | L4 is cross-cutting, not domain-specific |
| Cross-domain L5 imports from general treated as violations | Spine imports are legal by definition | They were never cross-domain — they were infrastructure calls |
| 11 customer domains | 10 customer domains + 1 spine | `general` removed as domain |
| ~15 files in general/L5 that everyone imports = violations | Same files in `hoc_spine/services/` = legal | Classification fix, not code fix |

---

## General's Remaining Domain Files

After spine extraction, ~20 files remain that are genuinely general-domain logic (e.g., `canonical_json`, `webhook_verify`, `panel_invariant_monitor`, `knowledge_sdk`, `dag_sorter`, etc.). These need a decision:

| Option | Description |
|--------|-------------|
| **A: Keep as `general` domain** | Rename to make clear it's a domain, not the spine. These are customer-facing general utilities. |
| **B: Redistribute** | Move each file to the domain it most serves (e.g., `knowledge_sdk` → account? `panel_*` → overview?) |
| **C: Absorb into spine** | If they're truly shared, they belong in spine services |

**Decision: PENDING**

---

## Impact on Violation Count

Current 82 violations would change:
- **~11 general violations** — most become non-violations (spine imports are legal)
- **~30 policies L2→L5 violations** that import `general.L5_engines.*` — become L2→spine (still need L3 adapter, but the cross-domain aspect is resolved)
- Remaining ~40 violations stay as-is (genuine L5→L7, L5→DB violations within domains)

---

## Directory Structure (Physical)

```
backend/app/hoc/
├── hoc_spine/                        ← SYSTEM CONSTITUTION
│   ├── L4_runtime/
│   │   ├── engines/
│   │   ├── facades/
│   │   └── drivers/
│   ├── services/
│   ├── schemas/
│   └── drivers/
├── cus/                              ← CUSTOMER CONSTITUTION(S)
│   ├── overview/
│   ├── activity/
│   ├── incidents/
│   ├── policies/
│   ├── controls/
│   ├── logs/
│   ├── analytics/
│   ├── integrations/
│   ├── apis/
│   └── account/
└── api/                              ← L2 APIs (unchanged)
    ├── facades/cus/                  ← L2.1 (to build)
    └── cus/{domain}/
```

---

## References

- HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0) — current baseline
- HOC_LITERATURE_PLAN.md (V1.1.0) — literature generation plan
- PIN-470: HOC Layer Inventory
- PIN-483: HOC Domain Migration Complete
