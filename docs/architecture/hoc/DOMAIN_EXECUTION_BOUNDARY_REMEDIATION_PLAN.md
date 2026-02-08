# Domain Execution Boundary Remediation Plan

**Status:** ✅ COMPLETE  
**Owner:** Codex (plan authority; implementation agents must not edit this plan)  
**Scope:** `backend/app/hoc/cus/*` + `backend/app/hoc/cus/hoc_spine/*`  
**Objective:** Reach **0 orphaned L5 entry modules** and **0 direct L2→L5 imports** while preserving the binding topology `L2 → L4 → L5 → L6 → L7`.

---

## Definitions

**L5 entry module (for pairing metrics):** A module whose filename stem matches:
- `*_engine.py`
- `*_facade.py`
- `*_bridge.py`

This excludes internal helpers (e.g., `*_enums.py`, `*_schemas.py`, `signal_identity.py`) so the metrics represent *domain execution boundary* reality rather than internal module sprawl.

**Wired via L4:** L4 hoc_spine imports the entry module (directly or via coordinator/bridge/handler).  
**Direct L2→L5 (gap):** L2 API imports an L5 entry module directly.  
**Orphaned:** No L2 or L4 import references exist for the entry module.

**Source of truth tool:** `scripts/ops/l5_spine_pairing_gap_detector.py`

---

## Current Snapshot (Frozen Baseline)

Baseline file: `docs/architecture/hoc/L2_L4_L5_BASELINE.json`

As of **2026-02-08** (baseline freeze after entry-module heuristic):
- `total_l5_engines`: 66
- `wired_via_l4`: 66
- `direct_l2_to_l5`: 0
- `orphaned`: 0

---

## Remediation Strategy (First Principles)

1. **If an orphaned entry module is truly unused:** delete it.  
2. **If it is used internally by a facade/engine:** rename it to *stop advertising itself as an entry module* (remove `_engine` suffix) or relocate into `L5_support/` (requires approval for moves).  
3. **If it should be callable from the product surface:** wire it through L4 hoc_spine operation registry and (if applicable) add/route an L2 endpoint to call L4 (never L5).

---

## Phase 0 — Triage (No Behavior Changes)

Goal: classify each orphan as `DELETE`, `DEMOTE`, or `WIRE`.

Steps:
1. For each orphan module, confirm repo-wide `import` references are zero.
2. Confirm there is no operation registry binding and no L4 handler/bridge import.
3. Decide remediation action.

Mechanical checks:
- `python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
- `rg -n "\\b(from|import)\\b.*\\b<stem>\\b" -S .`

---

## Phase 1 — Orphan Remediation (By Domain)

### account
- Candidates: `crm_validator_engine.py`, `email_verification_engine.py`, `user_write_engine.py`
- Default action: `DELETE` (unless triage finds a valid surface owner)

### activity
- Candidates: `attention_ranking_engine.py`, `cost_analysis_engine.py`, `pattern_detection_engine.py`
- Default action: `DELETE`

### analytics
- Candidates: `ai_console_panel_engine.py`, `alert_worker_engine.py`, `coordinator_engine.py`, `cost_model_engine.py`, `cost_write_engine.py`, `costsim_models_engine.py`, `pattern_detection_engine.py`, `provenance_engine.py`, `v2_adapter_engine.py`
- Default action: `DELETE`

### controls
- Candidates: `budget_enforcement_engine.py`
- Default action: `DELETE`

### incidents
- Candidates: `incident_pattern_engine.py`, `llm_failure_engine.py`, `postmortem_engine.py`, `prevention_engine.py`, `recurrence_analysis_engine.py`
- Default action: `DELETE`

### integrations
- Candidates: `cost_bridges_engine.py`, `graduation_engine.py`, `http_connector_engine.py`, `iam_engine.py`, `mcp_connector_engine.py`
- Default action: `DELETE`

### logs
- Candidates: `audit_engine.py`, `trace_facade.py`
- Default action: `DELETE`

### policies
- Candidates: `eligibility_engine.py`, `learning_proof_engine.py`, `llm_policy_engine.py`, `plan_generation_engine.py`, `policy_graph_engine.py`, `prevention_engine.py`, `sandbox_engine.py`
- Default action: `DELETE`

---

## Phase 2 — Re-Freeze and Document

Goal: after remediation, freeze an updated baseline and update architecture docs.

Steps:
1. Run pairing detector; confirm `direct_l2_to_l5 == 0` and `orphaned == 0`.
2. Freeze baseline: `python3 scripts/ops/l5_spine_pairing_gap_detector.py --freeze-baseline`
3. Update `docs/architecture/hoc/INDEX.md` pairing summary with the new baseline numbers.

---

## Phase 3 — Guardrail (Optional)

Goal: prevent regressions.

Option A (strict): CI fails if `orphaned > 0`.  
Option B (recommended): CI fails only if `direct_l2_to_l5 > 0` (already enforced) and logs orphan count for tracking.

---

## Definition of Done

- Pairing detector: `direct_l2_to_l5 == 0`, `orphaned == 0`
- Purity audit: `backend/scripts/ops/hoc_l5_l6_purity_audit.py --json --advisory --all-domains` → `0 blocking, 0 advisory`
- CI guards: init hygiene + layer boundaries + cross-domain validator all CLEAN
