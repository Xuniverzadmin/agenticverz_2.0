# HOC CUS Capability Sweep Waves Plan (2026-02-20)

## Final Goal
Reduce full-HOC capability backlog by clearing CUS-domain `MISSING_CAPABILITY_ID` debt in deterministic waves while keeping changed-file CI green on every PR.

## Baseline
- Snapshot date: 2026-02-20
- Source command:
  - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')`
- Baseline result:
  - Blocking: `929`
  - Warnings: `13`

## Operating Constraints
1. Scope-first focus: prioritize `backend/app/hoc/cus/**`.
2. No broad refactors; metadata-first remediation (`# capability_id:` headers + registry evidence sync).
3. Keep each wave PR-sized and reviewable.
4. Every wave must pass changed-file capability checks before merge.

## Wave Plan
| Step | Wave | Scope | Goal | Status | Evidence |
|---|---|---|---|---|---|
| 1 | Prep | establish backlog snapshots + hot clusters | lock deterministic baseline and target list | DONE | baseline `929 + 13` captured |
| 2 | C1 | `cus/hoc_spine/orchestrator/**`, `cus/hoc_spine/services/**`, `cus/hoc_spine/authority/**` | remove largest orchestration cluster debt | DONE | C1 scope blocking cleared (`78 -> 0`), full sweep `929 -> 851`, warnings `13 -> 13` |
| 3 | C2 | `cus/policies/L5_engines/**`, `cus/policies/L6_drivers/**`, `api/cus/policies/**` | clear policy domain capability metadata debt | DONE | C2 scope blocking cleared (`123 -> 0`), full sweep `851 -> 728`, warnings `13 -> 11` |
| 4 | C3 | `cus/logs/**`, `cus/analytics/**`, `cus/incidents/**`, `cus/integrations/**` | clear remaining CUS domain clusters | DONE | C3 scope blocking cleared (`178 -> 0`), full sweep `728 -> 550`, warnings `11 -> 11` |
| 5 | C4 | warning cleanup (`MISSING_EVIDENCE`) for CAP-001/CAP-006/CAP-018 | reduce warnings `13 -> 0` where ratified | DONE | full sweep warnings `11 -> 0` (blocking unchanged at `550`) |
| 6 | Closure | refresh trackers + publish pin | formalize residual backlog and next lane | TODO | queue/ledger + PIN update |

## Wave Execution Checklist (per wave)
1. Capture pre-wave counts:
   - full HOC sweep count
   - target cluster count
2. Implement remediation:
   - add `# capability_id: CAP-xxx` on scoped files
   - sync `docs/capabilities/CAPABILITY_REGISTRY.yaml` evidence mappings
3. Run mandatory audits:
   - changed-file capability check (must pass)
   - full HOC sweep (record delta)
4. Update governance artifacts:
   - plan status rows
   - blocker queue + tombstone ledger
   - evidence/PIN doc

## Success Criteria
1. CUS-target waves complete with deterministic deltas logged.
2. Changed-file capability check remains green every wave.
3. Full HOC blocking count shows monotonic reduction from baseline `929`.
4. Warnings are explicitly remediated or ratified with evidence.

## Expected Outcome Envelope
- Near-term target after C1+C2: move from `929` into high-`700` range.
- Mid-term target after C3: move toward low-`600` / high-`500` range, depending on residual shared-int clusters.

## C1 Result Snapshot
- Scope audited: `backend/app/hoc/cus/hoc_spine/orchestrator/**`, `backend/app/hoc/cus/hoc_spine/authority/contracts/**`.
- Header mapping applied:
  - `CAP-012` for orchestrator files.
  - `CAP-011` for authority contract files.
- Registry evidence synced in `docs/capabilities/CAPABILITY_REGISTRY.yaml`.
- Audit results:
  - C1 changed-file capability check: PASS.
  - C1 scope check: blocking `78 -> 0`.
- Full HOC sweep: blocking `929 -> 851` (`-78`), warnings stable at `13`.

## C2 Result Snapshot
- Scope audited: `backend/app/hoc/cus/policies/L5_engines/**`, `backend/app/hoc/cus/policies/L6_drivers/**`, `backend/app/hoc/api/cus/policies/**`.
- Header mapping applied:
  - `CAP-009` default for policy-engine surfaces.
  - `CAP-003` for `policy_proposals.py`.
  - `CAP-007` for `rbac_api.py`.
  - Existing `CAP-001` and `CAP-018` API files retained and evidence synced.
- Audit results:
  - C2 changed-file capability check: PASS.
  - C2 scope check: blocking `123 -> 0`.
- Full HOC sweep: blocking `851 -> 728` (`-123`), warnings `13 -> 11`.

## C3 Result Snapshot
- Scope audited: `backend/app/hoc/cus/logs/**`, `backend/app/hoc/cus/analytics/**`, `backend/app/hoc/cus/incidents/**`, `backend/app/hoc/cus/integrations/**`.
- Header mapping applied:
  - `CAP-001` for logs + incidents clusters.
  - `CAP-002` for analytics cluster.
  - `CAP-018` for integrations cluster.
- Registry evidence synced in `docs/capabilities/CAPABILITY_REGISTRY.yaml`.
- Audit results:
  - C3 changed-file capability check: PASS.
  - C3 scope check: blocking `178 -> 0`.
- Full HOC sweep: blocking `728 -> 550` (`-178`), warnings `11 -> 11`.

## C4 Result Snapshot
- Scope audited: full-HOC warning backlog (`MISSING_EVIDENCE`) after C3.
- Registry evidence sync completed for:
  - `CAP-018`: `backend/app/hoc/api/int/recovery/recovery.py`, `backend/app/hoc/api/int/recovery/recovery_ingest.py`
  - `CAP-001`: `backend/app/hoc/int/analytics/engines/authority.py`
  - `CAP-006`: `backend/app/hoc/int/general/{drivers,engines}/*` auth-gateway surfaces and `backend/app/hoc/int/integrations/engines/gateway_middleware.py`
- Audit results:
  - Full HOC sweep warnings: `11 -> 0`.
  - Full HOC sweep blocking: unchanged at `550`.

## Approval Gate
- If approved, execute Wave C1 first and open a focused PR with:
  - C1-only file set
  - before/after sweep numbers
  - updated blockers ledger + implemented evidence note
