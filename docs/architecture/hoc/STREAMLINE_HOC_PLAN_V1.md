# Streamline HOC Plan V1

**Date:** 2026-02-06  
**Status:** DRAFT (execution plan; evidence-driven)  
**Scope:** Stabilize HOC runtime + domains under first principles, aligned to `docs/COHERENCE_GLOBAL_PLAN.md`.

---

## North Star (Operational)

1. One canonical API surface: `backend/app/hoc/api/**` (customer + founder), with `/api/v1/*` treated as legacy-only (410 handlers).
2. One canonical execution authority: `backend/app/hoc/cus/hoc_spine/**` (orchestration, authority, lifecycle, consequences, transaction boundaries).
3. One linear execution topology for customer domains:

`L2 (hoc/api) → L4 (hoc_spine registry/handlers) → L5 (domain engines) → L6 (drivers) → L7 (models)`

---

## Non-Negotiables (First Principles)

1. **No assumptions:** every status claim requires a reproducible scan/test.
2. **Progressive work only:** implement in small batches with gates after each batch.
3. **No dead-copy maintenance:** if a file is not imported by runtime entrypoints, do not spend time updating it unless re-homing or deletion is explicitly approved.
4. **Guarded docs:** any document marked **READ-ONLY** is not edited unless explicitly commanded.

---

## Always-On Gates (Run After Every Batch)

From repo root:

```bash
cd backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py
```

Residual `/api/v1` string tracker (signal only; not a correctness gate):

```bash
cd backend
python3 - <<'PY'
from __future__ import annotations

from pathlib import Path

ROOT = Path("app")
EXCLUDE_DIRS = {
    ROOT / "api",
    ROOT / "services",
    ROOT / "adapters",
    ROOT / "hoc" / "cus" / "_domain_map",
}
EXCLUDE_FILES = {
    ROOT / "hoc" / "api" / "cus" / "general" / "legacy_routes.py",
}

needle = "/api/v1"
per_file: dict[str, int] = {}

for p in ROOT.rglob("*.py"):
    if any(ex in p.parents for ex in EXCLUDE_DIRS):
        continue
    if p in EXCLUDE_FILES:
        continue
    c = p.read_text(errors="ignore").count(needle)
    if c:
        per_file[str(p)] = c

print(f"remaining: {sum(per_file.values())} ({len(per_file)} files)")
for path, c in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0]))[:40]:
    print(f\"{path}: {c}\")
PY
```

Optional: runtime-authoritative tracker (excludes `app/hoc/int/**` duplicates if `hoc/int` is not wired by entrypoints):

```bash
cd backend
python3 - <<'PY'
from __future__ import annotations

from pathlib import Path

ROOT = Path("app")
EXCLUDE_DIRS = {
    ROOT / "api",
    ROOT / "services",
    ROOT / "adapters",
    ROOT / "hoc" / "cus" / "_domain_map",
    ROOT / "hoc" / "int",
}
EXCLUDE_FILES = {
    ROOT / "hoc" / "api" / "cus" / "general" / "legacy_routes.py",
}

needle = "/api/v1"
per_file: dict[str, int] = {}

for p in ROOT.rglob("*.py"):
    if any(ex in p.parents for ex in EXCLUDE_DIRS):
        continue
    if p in EXCLUDE_FILES:
        continue
    c = p.read_text(errors="ignore").count(needle)
    if c:
        per_file[str(p)] = c

print(f"remaining_no_hoc_int: {sum(per_file.values())} ({len(per_file)} files)")
for path, c in sorted(per_file.items(), key=lambda kv: (-kv[1], kv[0]))[:40]:
    print(f\"{path}: {c}\")
PY
```

---

## Workstreams (Ordered)

### Stream 1 — Fix Live Outputs First (Coherence Phase 1/2)

**Goal:** Remove `/api/v1` from any *runtime-generated* URLs/messages returned to clients.

**Why:** If we keep emitting `/api/v1`, we create broken client behavior even if routing is correct.

**Batch 1 (highest priority):**
- `backend/app/hoc/cus/logs/L5_engines/evidence_facade.py`
  - Stop generating `/api/v1/evidence/...` download URLs; emit canonical `/evidence/...`.
- `backend/app/hoc/cus/controls/L6_drivers/scoped_execution_driver.py`
  - Update any help/error strings referencing `/api/v1/recovery/scope` to `/recovery/scope`.

**Acceptance (in addition to always-on gates):**
```bash
cd backend
rg "download_url=.*api/v1" app/hoc/cus/logs/L5_engines/evidence_facade.py
rg "/api/v1/recovery/scope" app/hoc/cus/controls/L6_drivers/scoped_execution_driver.py
```
Target: 0 matches for both.

**Evidence artifact:** create/update an evidence note under `docs/architecture/hoc/` for this stream (file name decided at execution time).

---

### Stream 2 — Fix Authoritative Runtime Matchers (Coherence Phase 2)

**Goal:** Consolidate and update *authoritative* request matchers so canonical routes are correctly recognized without `/api/v1`, and so hoc_spine becomes the single owner of request authorization policy.

**Rule:** Only fix the code that is actually imported by runtime entrypoints.

**Target canonical authority owner:**
- `backend/app/hoc/cus/hoc_spine/authority/**` (single runtime authority for request authorization policy)

**Non-canonical / likely dead copies (do not touch unless proven imported):**
- `backend/app/hoc/int/**`
- `backend/app/hoc/api/int/**`

**Execution steps:**
1. Prove current import path(s) by searching `backend/app/main.py` and startup wiring.
2. Extract policy/matcher logic into hoc_spine authority modules (no FastAPI):
   - `hoc_spine.authority.rbac_policy` (path+method → required capability/permission)
   - `hoc_spine.authority.gateway_policy` (public-path and auth-exempt policy)
   - `hoc_spine.authority.onboarding_policy` (onboarding-state gates by route)
   - `hoc_spine.authority.route_planes` (route plane classification)
3. Make legacy locations thin shims (re-export only) until severance is complete:
   - `backend/app/auth/**` becomes re-export shims into hoc_spine authority (no logic).
4. Strip or dual-match `/api/v1` prefixes in the extracted policy:
   - Prefer canonical-only matching (`/X`) unless a legacy `/api/v1/*` request can still reach the middleware.
5. Preserve truly versioned exceptions only if they are real mounted routes.

**Decision checkpoints required before executing batch changes:**
- OAuth redirect URIs: are callbacks still under `/api/v1/auth/*` and truly mounted, or must they move?
- Backward-compat posture: do we keep dual-match (`/api/v1/X` and `/X`) or canonical-only?
- RBAC data ownership: tenant roles/capabilities remain owned by the `account` domain; hoc_spine owns request authorization *policy* and decisioning.

**Evidence artifact:** update a single “runtime matcher audit” report (file name decided at execution time) containing:
- file list (authoritative only)
- before/after match patterns
- acceptance output from always-on gates

---

### Stream 3 — Remove Residual `/api/v1` in HOC Runtime Docs/Strings (Coherence Phase 1)

**Goal:** Remove stale `/api/v1` from docstrings, comments, curl examples, and error strings that are not runtime behavior.

**Rule:** Only do this after Streams 1–2 are stable to avoid churn.

**Acceptance:** residual tracker decreases; always-on gates remain green.

---

### Stream 4 — Predictions Decision (Coherence Phase 3/4)

**Reality to respect:**
- `backend/app/predictions/api.py` defines a router prefix at `/api/v1/c2/predictions`.
- If it is not mounted by `backend/app/main.py`, it is not part of the live API surface.

**Decision:**
1. Retire/disable the predictions API module; remove stale exemptions.
2. Re-home predictions into canonical HOC surface (preferred) and document it in domain literature.

**Acceptance:** route scan from `app.main` matches the decision (either route appears under canonical surface, or all references are removed).

---

## Execution Cadence (Stop-The-Loop Discipline)

For each batch:
1. Implement smallest change set.
2. Run always-on gates.
3. Record evidence output in a single artifact for that stream.
4. Only then proceed to the next batch.

---

## Current State (To Be Recorded at Start of Execution)

Before executing Stream 1, record:
1. Always-on gates output.
2. Residual `/api/v1` string count (tracker).
3. `app.main` route scan for `/api/v1/*` (must remain legacy-only unless explicitly changed):

```bash
cd backend
python3 - <<'PY'
from app.main import app
routes=[(getattr(r,'path',''), getattr(getattr(r,'endpoint',None),'__module__','')) for r in app.routes]
v1=[r for r in routes if r[0].startswith('/api/v1')]
print('v1_route_count', len(v1))
for p,m in sorted(v1):
    print(p, m)
PY
```
