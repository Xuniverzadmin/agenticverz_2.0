# W*/T* Application Plan v1 (HOC) — Targeted, Evidence-Driven

**Date:** 2026-02-08  
**Status:** COMPLETE (implemented)  
**Scope:** `backend/app/hoc/cus/**` + `backend/tests/governance/t0/**`  

> Note: this filename contains `*`. When using shell commands, quote the path.

---

## Why This Document Exists

We have two separate taxonomies in the repo:

- **T0–T4**: governance *tiers* (capability maturity + proof gates) defined in
  `docs/architecture/gap_implementation/GAP_IMPLEMENTATION_PLAN_V1.md`.
- **W0–W4**: wiring/integration *phases* defined in
  `docs/architecture/gap_implementation/GAP_IMPLEMENTATION_PLAN_V2.md` and referenced by
  `backend/AUDIENCE_REGISTRY.yaml`.

HOC CUS domains are primarily governed by the **HOC topology + layer rules**
(`L2.1 → L2 → L4 hoc_spine → L5 → L6 → L7`) and the mechanical guardrails.

This plan exists to avoid “blindly applying” T/W labels to everything, while
still using T/W where they *actually* describe a real, runtime capability.

---

## First-Principles Policy

### P1 — HOC Topology Beats Taxonomy Labels

For `backend/app/hoc/cus/**`, the binding constraints are:
- L6 drivers must be **pure I/O** and must not depend on L4/hoc_spine authority.
- Cross-domain coordination and side-effects belong in L4 hoc_spine.

T/W labels are optional metadata. They are never a substitute for topology.

### P2 — Apply W/T Only When a Module Implements a Named Gap Capability

Add `# PHASE: Wx` or reference a `T*` tier only if:
- the module is an implementation of a specific GAP in v1/v2 plans, or
- the module is a wiring adapter whose acceptance criteria lives in the W-phase plan.

Otherwise, do not add labels; they rot and create false confidence.

---

## Current Reality (HOC CUS)

As of 2026-02-08, `backend/app/hoc/cus/**` contains only a handful of `# PHASE: W*`
headers (9 total) and effectively no systematic `T*` labeling. This is expected.

The correctness gates for HOC are mechanical scripts/tests:
- L2→L4→L5 wiring (pairing detector)
- L5/L6 purity (purity audit)
- init hygiene, layer boundaries, cross-domain validator

---

## Targeted Remediation: Fix Current T0 Failures (Do Not Broadly Re-Label)

### Goal

Make `backend/tests/governance/t0` pass without weakening the intent of the tests,
and without sweeping “metadata standardization” across domains.

### Why These Failures Matter

These failures are not cosmetic; they indicate:
- broken import surfaces (runtime can mask failures via eager re-exports), and/or
- authority inversion (L6 importing hoc_spine).

### Failure Set (Observed)

1. **policies**: `app.hoc.cus.policies.L5_engines.plan_generation` imports `get_planner`
   from `app.hoc.int.platform.facades`, but `get_planner` is not provided there.

2. **incidents / controls**: L6 drivers import hoc_spine modules, and the T0 law tests
   treat hoc_spine as a sibling “domain” import (cross-domain L6 imports).

---

## Implementation Plan (Domain-Grouped)

### Sequencing (Activities)

1. Fix the import surface sentinel first (policies `plan_generation.py`).
2. Remove all `L6_drivers -> app.hoc.cus.hoc_spine.*` imports (strict Option B).
3. Re-run `pytest tests/governance/t0 -q` from `backend/` and keep it mechanically green.
4. Re-run safety gates (purity audit, init hygiene, layer boundaries, cross-domain validator).

### Implementation Evidence (2026-02-08)

Observed results (ran from `backend/` unless noted):

- `PYTHONPATH=. python3 -m pytest tests/governance/t0 -q` → `599 passed, 18 xfailed, 1 xpassed`
- `PYTHONPATH=. python3 -m pytest tests/governance/t4 -q` → `429 passed`
- Repo root: `PYTHONPATH=backend python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py` → `0 blocking, 0 advisory`
- Repo root: `PYTHONPATH=backend python3 backend/scripts/ci/check_init_hygiene.py --ci` → `0 blocking violations`
- Repo root: `PYTHONPATH=backend python3 backend/scripts/ci/check_layer_boundaries.py --ci` → `CLEAN`
- Repo root: `PYTHONPATH=backend python3 backend/scripts/ops/hoc_cross_domain_validator.py` → `CLEAN`
- Repo root: `PYTHONPATH=backend python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` → `69 wired, 0 orphaned, 0 direct`

Strict Option B applied: no `L6_drivers` under the canonical 10 CUS domains import `app.hoc.cus.hoc_spine.*` (no exceptions).

### A) policies — Repair Import Surface Sentinel

**Problem:** `backend/app/hoc/cus/policies/L5_engines/plan_generation.py` imports
`get_planner` from `backend/app/hoc/int/platform/facades/`, but that package does not
export it.

**Fix strategy:**
- Repoint the import to an existing canonical planner accessor (preferred), *or*
- Provide a canonical `get_planner()` in `backend/app/hoc/int/platform/facades/`
  (e.g. `backend/app/hoc/int/platform/facades/__init__.py`) that forwards to the canonical accessor.

**Acceptance:** importing `app.hoc.cus.policies.L5_engines.plan_generation` succeeds and
`pytest tests/governance/t0/test_import_surface_sentinels.py -q` passes.

### B) incidents — Remove L6 → hoc_spine Imports (Authority Inversion)

**Problem:** `backend/app/hoc/cus/incidents/L6_drivers/incident_driver.py` emits RAC acks by
importing `hoc_spine.schemas.*` + `hoc_spine.services.*`.

**Fix strategy:**
- Replace hoc_spine imports with dependency injection:
  - `IncidentDriver` accepts an injected ack emitter callable/port (wired by L4), or
  - `IncidentDriver` returns ack facts to L4 and L4 emits the ack.
- If a shared DTO/Protocol is needed by both L4 and L6, move it to a neutral location:
  - domain-local `incidents/L5_schemas/**` (preferred), or
  - a dedicated shared schemas package intended for L6 use.

**Acceptance:** `rg "hoc_spine" backend/app/hoc/cus/incidents/L6_drivers -n` returns no results;
`pytest tests/governance/t0/test_law4_context_ownership.py -q` passes.

### C) controls — Remove L6 → hoc_spine Imports (DTOs + Config/Metric Ports)

**Problems:**
- `threshold_driver.py` imports a DTO from hoc_spine.
- `circuit_breaker_driver.py` and `circuit_breaker_async_driver.py` lazily import hoc_spine services.

**Fix strategy:**
- Inline/move DTO(s) like `LimitSnapshot` into `controls/L6_drivers/threshold_driver.py`
  or `controls/L5_schemas/**` so L6 no longer imports hoc_spine.
- Repoint `circuit_breaker_driver.py` and `circuit_breaker_async_driver.py` to import config/metrics
  from a neutral non-HOC-spine module (e.g. `app.costsim.config`, `app.costsim.metrics`) or inject ports.

**Acceptance:** `rg "hoc_spine" backend/app/hoc/cus/controls/L6_drivers -n` returns no results;
T0 law tests pass.

---

## Verification Block (No Assumptions)

Run from `backend/`:

```bash
PYTHONPATH=. python3 -m pytest tests/governance/t0 -q
PYTHONPATH=. python3 -m pytest tests/governance/t4 -q
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci
PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py
PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py --all-domains --advisory
```

HOC wiring boundary checks (repo root):

```bash
python3 scripts/ops/l5_spine_pairing_gap_detector.py --check
```

---

## Non-Goals

- Do not add W*/T* headers “everywhere”.
- Do not weaken the T0 law tests to make them pass.
- Do not introduce hoc_spine imports into L6 under any “exception” regime.
