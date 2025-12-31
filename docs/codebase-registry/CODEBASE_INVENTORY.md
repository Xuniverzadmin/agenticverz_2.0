# Codebase Inventory vs Layered Inventory

**Date:** 2025-12-30
**Status:** Complete
**Purpose:** Full mapping of repository structure to layer model

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Files Scanned** | 1,441 |
| **With Explicit Headers** | 210 (14.6%) |
| **Without Headers (path-inferred)** | 1,231 (85.4%) |
| **UNKNOWN (no classification)** | 2 (0.1%) |
| **HIGH Confidence** | 210 (14.6%) |
| **MEDIUM Confidence** | 1,209 (83.9%) |
| **LOW Confidence** | 22 (1.5%) |

---

## Layer Distribution

| Layer | Name | Count | % | Description |
|-------|------|------:|---|-------------|
| **L1** | Product Experience | 106 | 7.4% | UI pages, components, hooks, types |
| **L2** | Product APIs | 60 | 4.2% | REST endpoints, surface contracts |
| **L3** | Boundary Adapters | 25 | 1.7% | LLM adapters, external integrations |
| **L4** | Domain Engines | 154 | 10.7% | Policy, workflow, skills, agents |
| **L5** | Execution & Workers | 29 | 2.0% | Jobs, tasks, runtime |
| **L6** | Platform Substrate | 123 | 8.5% | DB, auth, models, utils, SDK |
| **L7** | Ops & Deployment | 750 | 52.0% | Docs, scripts, config, monitoring |
| **L8** | Catalyst / Meta | 192 | 13.3% | Tests, validators, CI |
| UNKNOWN | - | 2 | 0.1% | Unclassified |

### Layer Distribution Chart

```
L7 ████████████████████████████████████████████████████ 750 (52.0%)
L8 █████████████ 192 (13.3%)
L4 ██████████ 154 (10.7%)
L6 ████████ 123 (8.5%)
L1 ███████ 106 (7.4%)
L2 ████ 60 (4.2%)
L5 ██ 29 (2.0%)
L3 ██ 25 (1.7%)
```

**Key Insight:** L7 (Ops) dominates because of extensive documentation (421 markdown files) and scripts. This is healthy — it indicates strong operational maturity.

---

## File Type Distribution

| Type | Count | % |
|------|------:|---|
| Python | 549 | 38.1% |
| Markdown | 421 | 29.2% |
| YAML | 155 | 10.8% |
| TypeScript | 144 | 10.0% |
| Shell | 113 | 7.8% |
| JSON | 52 | 3.6% |
| JavaScript | 3 | 0.2% |
| Other | 4 | 0.3% |

---

## Directory → Layer Mapping

| Directory | Files | Primary Layers |
|-----------|------:|----------------|
| `backend/` | 523 | L4 (154), L8 (168), L6 (99) |
| `docs/` | 538 | L7 (538) |
| `scripts/` | 180 | L7 (161), L8 (19) |
| `website/` | 137 | L1 (106), L2 (26) |
| `monitoring/` | 33 | L7 (33) |
| `sdk/` | 29 | L6 (20), L8 (5), L7 (4) |
| `config/` | 1 | L7 (1) |
| **TOTAL** | **1,441** | |

---

### backend/ (523 files)

| Layer | Count | Description |
|-------|------:|-------------|
| L4 | 154 | Domain logic (policy, workflow, skills) |
| L8 | 168 | Tests |
| L6 | 99 | Platform (db, auth, models, utils) |
| L2 | 34 | API routes |
| L5 | 29 | Workers, runtime |
| L3 | 25 | Adapters (planners, integrations) |
| L7 | 13 | CLI, specs |
| UNKNOWN | 1 | data/failure_catalog.json |

### website/aos-console/ (137 files)

| Layer | Count | Description |
|-------|------:|-------------|
| L1 | 106 | Pages, components, hooks |
| L2 | 26 | API layer (services) |
| L6 | 4 | Utilities |
| UNKNOWN | 1 | - |

### docs/ (538 files)

| Layer | Count | Description |
|-------|------:|-------------|
| L7 | 538 | All documentation |

### scripts/ (180 files)

| Layer | Count | Description |
|-------|------:|-------------|
| L7 | 161 | Operational scripts |
| L8 | 19 | Test/validation scripts |

### monitoring/ (33 files)

| Layer | Count | Description |
|-------|------:|-------------|
| L7 | 33 | Prometheus, Grafana configs |

### sdk/ (29 files)

| Layer | Count | Description |
|-------|------:|-------------|
| L6 | 20 | SDK code |
| L8 | 5 | SDK tests |
| L7 | 4 | SDK docs, config |

---

## Product Distribution

| Product | Count | % |
|---------|------:|---|
| unspecified | 1,228 | 85.2% |
| system-wide | 173 | 12.0% |
| ai-console | 16 | 1.1% |
| product-builder | 10 | 0.7% |

**Note:** 85% "unspecified" = files without explicit product headers (path-inferred only)

---

## Confidence Distribution

| Confidence | Count | Meaning |
|------------|------:|---------|
| **HIGH** | 210 | Explicit header with layer declaration |
| **MEDIUM** | 1,209 | Path-inferred classification |
| **LOW** | 22 | Weak inference (mostly `__init__.py`) |

---

## Layer Detail View

### L1 — Product Experience (106 files)

All files in `website/aos-console/console/src/`:

| Subdirectory | Files | With Headers |
|--------------|------:|-------------:|
| components/ | ~60 | 0 |
| pages/ | ~15 | 0 |
| hooks/ | 5 | 2 |
| lib/ | 8 | 8 |
| types/ | 8 | 8 |

### L2 — Product APIs (60 files)

| Location | Files | With Headers |
|----------|------:|-------------:|
| backend/app/api/ | 33 | 0 |
| backend/app/main.py | 1 | 1 |
| website/.../services/ | 26 | 0 |

### L3 — Boundary Adapters (25 files)

| Location | Files | With Headers |
|----------|------:|-------------:|
| backend/app/planners/ | 6 | 5 |
| backend/app/integrations/ | 1 | 1 |
| backend/app/planner/ | 3 | 3 |
| backend/app/services/ (adapters) | 5 | 5 |
| backend/app/auth/ (oauth) | 3 | 3 |
| backend/app/events/ | 3 | 3 |
| backend/app/skills/ (http) | 4 | 1 |

### L4 — Domain Engines (154 files)

| Subdomain | Files | With Headers |
|-----------|------:|-------------:|
| policy/ | 25 | 18 |
| skills/ | 26 | 0 |
| agents/ | 22 | 9 |
| services/ | 11 | 9 |
| workflow/ | 9 | 8 |
| costsim/ | 16 | 0 |
| integrations/ | 8 | 8 |
| routing/ | 7 | 6 |
| optimization/ | 6 | 4 |
| workers/bb | 7 | 6 |
| auth/ | 5 | 5 |
| learning/ | 4 | 3 |
| contracts/ | 4 | 4 |
| predictions/ | 2 | 2 |
| discovery/ | 2 | 2 |

### L5 — Execution & Workers (29 files)

| Location | Files | With Headers |
|----------|------:|-------------:|
| worker/ | 11 | 0 |
| tasks/ | 5 | 4 |
| jobs/ | 4 | 3 |
| workers/ | 3 | 3 |
| runtime/ | 2 | 0 |
| optimization/envelope | 2 | 2 |
| policy/runtime | 1 | 1 |
| integrations/ | 1 | 1 |

### L6 — Platform Substrate (123 files)

| Subdomain | Files | With Headers |
|-----------|------:|-------------:|
| schemas/ | 17 | 5 |
| utils/ | 15 | 14 |
| memory/ | 10 | 0 |
| SDK (python+js) | 20 | 0 |
| models/ | 8 | 7 |
| traces/ | 8 | 7 |
| auth/ | 5 | 4 |
| middleware/ | 4 | 3 |
| stores/ | 3 | 2 |
| config/ | 3 | 3 |
| storage/ | 2 | 2 |
| secrets/ | 2 | 2 |
| security/ | 2 | 2 |
| core (db, auth, etc) | 7 | 7 |
| workflow/infra | 3 | 3 |

### L7 — Ops & Deployment (750 files)

| Category | Files |
|----------|------:|
| docs/memory-pins/ | 200+ |
| docs/contracts/ | 50+ |
| docs/codebase-registry/ | 130+ |
| docs/test_reports/ | 30+ |
| scripts/ops/ | 60+ |
| scripts/preflight/ | 10+ |
| monitoring/ | 33 |
| Other docs | 200+ |

### L8 — Catalyst / Meta (192 files)

| Category | Files |
|----------|------:|
| backend/tests/ | 168 |
| scripts (validators) | 19 |
| SDK tests | 5 |

---

## UNKNOWN Files (2 remaining)

| File | Recommended Layer |
|------|-------------------|
| `backend/app/data/failure_catalog.json` | L6 (data file) |
| 1 website file (path inference gap) | L1 |

These are edge cases in path inference, not missing declarations.

---

## Summary: Inventory → Layer Alignment

### ✅ What's Working

1. **UNKNOWN ≈ 0** — Goal achieved (183 → 2)
2. **L4 is largest domain layer** — Domain logic concentrated correctly
3. **L7 dominates overall** — Documentation maturity is high
4. **HIGH confidence = explicit headers** — 210 files fully declared
5. **Product boundaries clean** — ai-console vs system-wide separated

### ⚠️ Coverage Gaps (Not Issues, Just Observations)

| Gap | Count | Priority |
|-----|------:|----------|
| API routes without headers | 33 | Low (path-inferred) |
| Skills without headers | 26 | Low (path-inferred) |
| SDK without headers | 20 | Low (external package) |
| Costsim without headers | 16 | Medium |
| Memory without headers | 10 | Medium |

These are **not broken** — they're classified via path inference. Adding explicit headers would increase HIGH confidence but doesn't change behavior.

---

## Appendix: Scripts Used

| Script | Purpose |
|--------|---------|
| `/tmp/full_inventory.py` | Complete inventory scanner |
| `/tmp/find_unknown_files_v2.py` | UNKNOWN file detector |
| `/tmp/add_headers_batch*.py` | Header addition scripts |

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-30 | Initial inventory complete |
| 2025-12-30 | Research pass: 186 headers added |
| 2025-12-30 | UNKNOWN: 183 → 2 |
