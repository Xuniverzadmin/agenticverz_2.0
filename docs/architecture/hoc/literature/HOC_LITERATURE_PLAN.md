# HOC Literature Generation Plan

**Version:** 1.1.0
**Status:** ACTIVE
**Created:** 2026-01-28
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## Objective

Generate prescriptive architecture documentation for every file in `hoc/cus/` — describing not how the platform works today, but how each file SHOULD be wired given its layer, domain, and function per the ratified topology.

**This is a build plan, not a status report.**

---

## Scope

| Included | Excluded |
|----------|----------|
| `hoc/cus/` (11 customer domains) | L1 Frontend (separate project, DEFERRED) |
| L2.1 Facades through L6 Drivers | L7 Models (DEFERRED) |
| Prescriptive wiring | `app/api/` (legacy, redundant) |
| | `app/services/` (legacy, redundant) |
| | Descriptive "how it works today" |

---

## Layer Definitions (from HOC_LAYER_TOPOLOGY_V1.4.0)

### L2.1 Facade — ORGANIZER (to be built)

**Objective:** One facade per domain. Groups L2 routers by audience+domain. Conceals API structure from outside world.

**Contract:**
- Imports L2 routers ONLY
- No business logic, no validation, no DB
- MUST NOT import L3, L4, L5, L6, L7

**Methodology to build:**
1. For each domain, enumerate all L2 API files in `hoc/api/cus/{domain}/`
2. Create `hoc/api/facades/cus/{domain}.py`
3. Facade class imports `router` objects from each L2 file
4. Facade exposes `routers = [...]` list
5. FastAPI app mounts the facade, not individual routers

**Build spec derived from:** Literature generator lists all L2 routers per domain that SHOULD be grouped.

### L2 API — HTTP TRANSLATION

**Objective:** HTTP request/response handling. Thin. Delegates to L3.

**Contract:**
- Input validation (FastAPI + Pydantic)
- Auth/tenant extraction
- Response formatting
- MUST call L3 adapters, MUST NOT call L5 directly

### L3 Adapter — TRANSLATION + DISTRIBUTION

**Objective:** Bridge between L2 HTTP world and L5 domain logic. Only layer where cross-domain imports are legal.

**Contract:**
- Translation + aggregation ONLY
- No state mutation, no retries, no policy decisions
- Tenant scoping enforcement
- MUST NOT access DB directly (no sqlmodel, no session.commit)

**4 Archetypes:**

| Archetype | When to Use | Example |
|-----------|-------------|---------|
| **Domain Adapter** | L2 route needs same-domain L5 engine | `policies/L3_adapters/policy_adapter.py` |
| **Cross-Domain Bridge** | Domain A facts trigger Domain B actions | `incidents/L3_adapters/anomaly_bridge.py` |
| **Tenant Isolator** | Customer-facing data needs field stripping | `integrations/L3_adapters/customer_logs_adapter.py` |
| **Integration Wrapper** | External SDK needs AOS interface | `integrations/L3_adapters/slack_adapter.py` |

**Methodology to build:**
1. For each L5 engine without an L3 bridge → create domain adapter
2. For each cross-domain import in L5 → extract to L3 cross-domain bridge
3. For each customer-facing endpoint → ensure tenant isolation in L3
4. For each external integration → wrap in L3 with AOS protocol

**Build spec derived from:** Literature generator flags L5 engines with no L3 bridge as gaps.

### L4 Runtime — CONTROL PLANE (general/ only)

**Objective:** Centralized execution authority. Three independent parts.

**Contract:**
- Authority: grant/deny permission (pure, no side effects)
- Execution: mechanical triggering (assumes authority granted)
- Consequences: react to outcomes (non-blocking)
- Parts do NOT call each other
- OWNS commit authority (only layer that calls session.commit)
- All execution enters L4 exactly once

**Methodology:**
- L5 engines doing governance checks → extract to L4/authority
- L5 engines doing retry/orchestration → extract to L4/execution
- L5 engines creating incidents on failure → extract to L4/consequences

### L5 Engines — BUSINESS LOGIC

**Objective:** Domain-specific decisions, pattern detection, computation.

**Contract:**
- Calls L6 drivers for DB operations
- MUST NOT import sqlmodel, sqlalchemy, Session
- MUST NOT import app.models directly
- MUST NOT reach up to L2 or L3

### L6 Drivers — DB OPERATIONS

**Objective:** Query building, data transformation, DB read/write.

**Contract:**
- Imports L7 models
- Returns domain objects (dataclass, dict, Pydantic), NOT ORM models
- Owns query logic — engines never write SQL
- MUST NOT contain business logic

### L7 Models — DEFERRED

> L7 model classification, domain-specific model design, and DB migration are out of scope for this phase. Will be addressed in a separate plan.

---

## Import Flow (RATIFIED)

```
L2.1 → L2 → L3 ─┬─→ L4 → L5 → L6 → L7
                 │        ↓
                 └───────→ L5 (cross-domain at L3 only)
```

| Layer | Cross-Domain | Reason |
|-------|-------------|--------|
| L2.1, L2 | FORBIDDEN | Stay within audience/domain |
| **L3** | **ALLOWED** | Aggregation point for multi-domain data |
| L4 | Same audience only | Shared runtime per audience |
| L5, L6 | FORBIDDEN | Domain isolation |

---

## Tool: Literature Generator

**Script:** `scripts/ops/hoc_literature_generator.py`
**Input:** `docs/architecture/hoc/HOC_CUS_DOMAIN_AUDIT.csv`

### What it does (deterministic, AST-based)

| Step | Method | Output |
|------|--------|--------|
| Parse each .py file | `ast.parse()` | Functions, classes, imports, docstrings |
| Classify layer + domain | Path regex | Layer and domain assignment |
| Apply LAYER_CONTRACT rules | Import analysis vs rules | Violations |
| Detect missing pieces | Layer presence analysis | Gaps |
| Find callers | ripgrep across backend/ | Current caller map (reference only) |

### What it does NOT do

- No LLM summarization (avoids hallucination)
- No guessing caller intent
- No inferring relationships not in code
- No declaring "how the platform works today"

### Outputs

**Markdown:**
- `LITERATURE_INDEX.md` — TOC + conformance scores + disclaimer
- `GAP_REGISTER.md` — All missing pieces + L7 model classification
- `WIRING_VIOLATIONS.md` — Every import rule break
- `{NN}_{domain}/DOMAIN_WIRING_MAP.md` — Vertical connectivity diagram
- `{NN}_{domain}/{layer}.md` — Per-file identity + prescriptive wiring

**JSON (machine-readable):**
- `literature_index.json` — Full parsed inventory per domain
- `gap_register.json` — Gaps (L2.1 through L6)
- `violations.json` — All violations with file, line, rule, fix

### Running

```bash
# Full run (with caller discovery)
python scripts/ops/hoc_literature_generator.py

# Fast run (skip caller discovery)
python scripts/ops/hoc_literature_generator.py --skip-callers

# Custom CSV / output
python scripts/ops/hoc_literature_generator.py --csv path/to/audit.csv --output path/to/output/
```

---

## Current State (2026-01-28 run)

| Metric | Value |
|--------|-------|
| Domains | 11 |
| Files parsed | 399 / 405 (6 .tsx failures — expected) |
| Violations | 82 |
| Gaps | 34 |

### Per-Domain Summary

| # | Domain | L2 | L3 | L5 | L6 | Violations | Gaps | Conformance |
|---|--------|----|----|----|-----|-----------|------|-------------|
| 1 | general | 4 | 0 | 36 | 13 | 11 | 4 | 50% |
| 2 | overview | 1 | 0 | 1 | 1 | 1 | 3 | 60% |
| 3 | activity | 1 | 0 | 8 | 3 | 1 | 3 | 60% |
| 4 | incidents | 2 | 1 | 16 | 11 | 4 | 2 | 80% |
| 5 | policies | 38 | 2 | 61 | 14 | 42 | 3 | 80% |
| 6 | controls | 0 | 1 | 9 | 8 | 5 | 2 | 40% |
| 7 | logs | 4 | 1 | 17 | 12 | 4 | 2 | 80% |
| 8 | analytics | 4 | 2 | 20 | 8 | 7 | 7 | 80% |
| 9 | integrations | 3 | 21 | 16 | 3 | 6 | 3 | 80% |
| 10 | apis | 0 | 0 | 0 | 1 | 0 | 2 | 20% |
| 11 | account | 1 | 0 | 8 | 3 | 1 | 3 | 60% |

> **Conformance = topology rule adherence, NOT feature completeness or production readiness.**

### Top Gap Categories

| Gap Type | Count | Summary |
|----------|-------|---------|
| L2.1 Facade | 11 | All domains — none built yet |
| L3 Adapter | 6 | general, overview, activity, controls, apis, account |
| L6 Driver | 7 | L5 engines with DB imports but no matching driver |
| L2 API | 2 | controls, apis — no route handlers |

---

## Execution Plan

| Phase | What | Prerequisite |
|-------|------|-------------|
| **DONE** | Literature generator built + first run | Audit CSV |
| **NEXT** | Fix caller discovery (ripgrep patterns too narrow) | Script fix |
| P1 | Review literature per domain — human validates prescriptive wiring | Literature outputs |
| P2 | Build L2.1 facades (11 files, mechanical — group routers) | P1 approval |
| P3 | Build missing L3 adapters (6 domains) | P1 approval |
| P4 | Extract L5→L6 violations (L5 engines doing DB directly → create L6 drivers) | P1 approval |
| **DEFERRED** | L7 model classification + domain-specific models + DB migration | Separate plan |
| **DEFERRED** | L1 Frontend | Separate project |

---

## Known Script Issues (to fix)

1. **Caller discovery shows 0** — ripgrep patterns need broadening. Current patterns match exact module paths, but many imports use relative or shortened forms.

2. **6 .tsx parse failures** — Expected. AST parser is Python-only. Frontend files should be excluded from CSV (L1 removed from scope).

## Deferred (separate plan)

- L7 model classification (3-bucket: system invariant / domain-owned / cross-domain fact)
- Domain-specific model design + DB migration
- L1 Frontend

---

## References

- HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)
- HOC_CUS_DOMAIN_AUDIT.csv (437 files, 11 domains)
- PIN-470: HOC Layer Inventory
- PIN-483: HOC Domain Migration Complete
