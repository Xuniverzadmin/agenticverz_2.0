# HOC Layer + Capability Remediation Wave 1 Plan (2026-02-20)

## Final Goal
Reduce HOC blocking governance debt with safe, reviewable changes by removing high-volume layer-segregation violations and proving measurable delta via re-audit.

## Approval
- Requested by: founder/user
- Approval status: APPROVED IN-THREAD (instruction: "create a plan and take approval.. then proceed to implement")

## Scope (Wave 1)
- Focus only on `backend/app/hoc/**`.
- Target largest layer-segregation hotspot cluster under `hoc/int/agent/engines/*`.
- Do not tombstone HOC violations.
- Keep non-HOC backlog out of scope.

## Step Plan and Status
| Step | Goal | Status | Evidence |
|---|---|---|---|
| 1 | Capture baseline metrics (`layer_segregation_guard --scope hoc`, full HOC capability sweep) | DONE | Baseline: layer violations `93`; capability sweep `972 + 13 warnings` |
| 2 | Implement Wave 1 layer fix pattern for `hoc/int/agent/engines/*` hotspot files | DONE | Implemented compatibility wrappers in: `job_engine.py`, `worker_engine.py`, `credit_engine.py`, `message_engine.py`, `registry_engine.py`, `governance_engine.py`, `invoke_audit_engine.py` |
| 3 | Run post-change audits and verify deterministic delta | DONE | Layer: `93 -> 14`; full HOC capability sweep: `972 -> 965` blockers, warnings stable at `13`; import hygiene unchanged clean (`HOC_REL_FILES=0`, `CUS_REL_FILES=0`) |
| 4 | Update remediation docs/literature/pin with before/after evidence | DONE | Added Wave 1 artifact: `backend/app/hoc/docs/architecture/usecases/HOC_LAYER_CAPABILITY_REMEDIATION_WAVE1_IMPLEMENTED_2026-02-20.md`; updated capability evidence map for CAP-008 |
| 5 | Report outcome and residual blockers with next-wave plan | DONE | Residual layer blockers isolated to 8 files (14 instances), ready for Wave 2 |

## Implementation Pattern (Wave 1)
1. Replace DB-heavy HOC engine implementations with thin compatibility wrappers to canonical service/driver modules under `backend/app/agents/services/*`.
2. Preserve public symbols and call contracts to avoid runtime caller breakage.
3. Ensure each modified HOC file carries explicit `capability_id` metadata.
4. Validate with compile + layer guard + changed-file capability check.

## Exit Criteria
- `layer_segregation_guard --scope hoc` violation count reduced from baseline.
- No new import-hygiene regressions in HOC scope.
- Changed-file capability linkage check passes.

## Final Outcome
- Exit criteria met for Wave 1.
- Largest hotspot cluster (`hoc/int/agent/engines/*`) was neutralized without tombstoning HOC debt.
- Remaining HOC layer debt is now concentrated in founder ops/account/logs incident engines plus two platform files.
