# Phase 4 — End-to-End Proof Plan (Determinism + Truth Preservation)

**Created:** 2026-02-07  
**Status:** READY  
**Scope:** `backend/app/**` (HOC runtime + hoc_spine)

---

## Goal

Produce executable evidence that HOC is deterministic and truth-preserving end-to-end:

- L2 → L4 → L5 → L6 topology remains intact.
- `/api/v1/*` remains legacy-only (410).
- Replay is stable (same IR + facts → same result).
- No cross-domain violations outside hoc_spine.

---

## Always-On Gates (Run Before + After)

```bash
cd backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py
PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py tests/hoc_spine/test_no_duplicate_routes.py
```

Route snapshot (record for evidence):

```bash
cd backend
python3 - <<'PY'
from app.main import app
routes=[(getattr(r,'path',''), sorted(getattr(r,'methods',[]) or []), getattr(getattr(r,'endpoint',None),'__module__','')) for r in app.routes]
print('total_routes', len(routes))
print('v1_routes', len([r for r in routes if r[0].startswith('/api/v1')]))
print('controls_routes', len([r for r in routes if r[0].startswith('/controls')]))
print('predictions_routes', len([r for r in routes if r[0].startswith('/predictions')]))
PY
```

---

## Proof Workstreams (Execute In Order)

### P4.1 Replay Determinism (Unit-Level)

Run replay tests (fast, deterministic):

```bash
cd backend
PYTHONPATH=. pytest -q tests/dsl/test_replay.py
```

### P4.2 Golden Lifecycle Replay (Workflow-Level)

```bash
cd backend
PYTHONPATH=. pytest -q tests/workflow/test_golden_lifecycle.py
```

### P4.3 Replay Parity (Optional; Integration)

Only if environment/config supports it:

```bash
cd backend
PYTHONPATH=. pytest -q tests/integration/test_replay_parity.py
```

---

## Documentation Sync (Truth-Map Hygiene)

After major rewires (e.g., Controls L2 re-home), ensure truth-map artifacts reflect current wiring:

- `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md` (replace `policies/controls.py` with `controls/controls.py`)
- `docs/architecture/hoc/CUS_HOC_SPINE_COMPONENT_COVERAGE.md` (remove stale note about controls living under policies)

Rule: do not update docs unless explicitly commanded by the user.

---

## Evidence Artifact (Single Output)

Create `docs/architecture/hoc/PHASE4_E2E_PROOF_EVIDENCE.md` containing:

- Output of Always-On Gates
- Route snapshot output
- `pytest` summaries for P4.1 and P4.2 (and P4.3 if run)

