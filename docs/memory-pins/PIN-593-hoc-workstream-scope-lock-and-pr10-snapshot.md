# PIN-593 HOC Workstream Scope Lock and PR10 Snapshot

## Date
2026-02-20

## Context
Course correction required that blocker cleanup proceed only under `hoc/*`, while non-HOC debt remains visible but non-blocking as tombstoned legacy debt.

## What Was Locked
- Blocking scope: `backend/app/hoc/**`
- Tombstoned scope: non-`hoc/*` violations recorded in `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`

## Execution Snapshot
- Clean branch from `origin/main`: `hoc/ws-a-hoc-scope-tombstone`
- PR opened: `https://github.com/Xuniverzadmin/agenticverz_2.0/pull/10`
- Commits:
  - `8d2678b3` governance scope + workflow/script updates
  - `745fc236` HOC violation file-set enumeration in tombstone ledger

## Audit Numbers (Skeptical Pass)
- Layer segregation: `all=99`, `hoc=93`, `non-hoc=6`
- Relative imports: `all=63`, `hoc=34`, `non-hoc=29`
- Capability linkage (`MISSING_CAPABILITY_ID`): `total=9`, `hoc=5`, `non-hoc=4`

## Why This PIN
This anchors the exact governance stance for ongoing remediation: only `hoc/*` violations are active closure scope for the current workstream, and all non-HOC debt is explicitly tracked as tombstoned backlog.
