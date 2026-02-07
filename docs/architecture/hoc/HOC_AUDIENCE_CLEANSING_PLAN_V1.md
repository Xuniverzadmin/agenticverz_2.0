# HOC Audience Cleansing Plan V1 (CUS/INT/FDR Only)

**Date:** 2026-02-07  
**Status:** DRAFT (progressive execution plan)  
**Scope:** `backend/app/hoc/**`, `backend/app/main.py`, canonical literature updates post-implementation

---

## Principle

`hoc/api/` must have exactly three audience roots:
- `cus/` (customer)
- `int/` (internal/system)
- `fdr/` (founder)

No other audience root may exist (e.g., no “system” audience).

---

## Reality (Repo, Evidence-Based)

### What Exists Today

- `backend/app/hoc/api/cus/` contains canonical domain routes plus non-domain surfaces:
  - canonical 10 domains exist (good)
  - `general/`, `agent/`, `ops/`, `recovery/` also exist (misaligned per audience/domain taxonomy)
- `backend/app/hoc/api/int/` contains modules but **no APIRouter routers** (dependency/middleware only).
- `backend/app/hoc/api/infrastructure/` exists as a non-audience folder (no routers).
- L2.1 facades exist and are wired by entrypoint severance:
  - `backend/app/hoc/api/facades/cus/`
  - `backend/app/hoc/api/facades/fdr/`
  - `backend/app/hoc/api/facades/system/` (misaligned; must be abolished)

---

## Target End State

### Audience Layout (Canonical)

```
backend/app/hoc/api/
  cus/          # only canonical 10 customer domains
  int/          # all internal/system surfaces + internal routers
  fdr/          # founder surfaces
  facades/
    cus/
    int/
    fdr/
```

### CUS Contains Only Canonical 10 Domains

`backend/app/hoc/api/cus/` must contain exactly:
- `overview/`
- `activity/`
- `incidents/`
- `policies/`
- `controls/`
- `logs/`
- `analytics/`
- `integrations/`
- `api_keys/`
- `account/`

Everything else currently under CUS must be reclassified.

---

## Progressive Execution Plan (Streamed)

### Batch A — Abolish “system” Facade Root

**Goal:** eliminate `backend/app/hoc/api/facades/system/` and re-home its responsibilities under `facades/int/`.

**Work:**
- Create `backend/app/hoc/api/facades/int/` and re-home the bundles:
  - `general` bundle (health, legacy 410, sdk, debug)
  - `agent` bundle (agents + agent-* internal surfaces)
  - `recovery` bundle (if treated internal)
  - `ops` bundle (internal ops; founder ops remains in `facades/fdr`)
- Update `backend/app/hoc/app.py` to import only from `facades/{cus,int,fdr}`.
- Delete `backend/app/hoc/api/facades/system/` after cutover.

**Gates (must stay green):**
- `check_init_hygiene --ci`
- `check_layer_boundaries`
- `hoc_cross_domain_validator`
- Route snapshot unchanged.

---

### Batch B — Reclassify Misplaced CUS Surfaces into INT/FDR

**Goal:** `backend/app/hoc/api/cus/` becomes “canonical 10 domains only”.

**Work (mapping to decide/execute):**
- `backend/app/hoc/api/cus/general/**` → `backend/app/hoc/api/int/general/**`
  - includes `/health`, legacy 410 surface, sdk/debug
- `backend/app/hoc/api/cus/agent/**` and `backend/app/hoc/api/cus/general/agents.py` → `backend/app/hoc/api/int/agent/**`
- `backend/app/hoc/api/cus/ops/**`:
  - founder-visible `/ops/*` should likely become `backend/app/hoc/api/fdr/ops/**`
  - internal-only ops should become `backend/app/hoc/api/int/ops/**`
- `backend/app/hoc/api/cus/recovery/**` → `backend/app/hoc/api/int/recovery/**`

**Requirements:**
- URL surface must not change unless explicitly approved.
- L2 purity constraints remain intact.
- L2.1 facades must be updated as the canonical inclusion list.

**Gates:**
- same as Batch A, plus:
- route snapshot unchanged
- existing proof tests remain passing where they exist (replay/lifecycle).

---

### Batch C — Re-home `api/infrastructure/` into an Audience Root

**Goal:** remove `backend/app/hoc/api/infrastructure/` as “floating infra”.

**Options (requires decision):**
- Option 1: move to `backend/app/hoc/api/int/infrastructure/` (internal request boundary support)
- Option 2: move into `backend/app/hoc/cus/hoc_spine/services/` (runtime infrastructure)

**Constraint:** do not move until callers are inventoried and a target owner is clear.

---

## Post-Implementation Documentation Update (Mandatory)

After Batches A–C are implemented:
- Update `backend/app/hoc/api/hoc_api_canonical_literature.md` to match the new audience/domain layout.
- Update domain canonical literature (`literature/hoc_domain/*/*CANONICAL*`) where paths moved.
- Update any topology references that mention non-canonical audience roots (CUS/INT/FDR only).

---

## Acceptance Criteria (Global)

1. `backend/app/hoc/api/` contains only audience roots `cus/`, `int/`, `fdr/` (plus `facades/`).
2. `backend/app/hoc/api/cus/` contains only the canonical 10 domains.
3. Entry points do not import routers directly (enforced by CI check 33 and pytest guard).
4. Gates remain green and route snapshot remains stable.

