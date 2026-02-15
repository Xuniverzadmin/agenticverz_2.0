# PROD_READINESS_TRACKER.md

## Purpose
Track real-world production readiness validation separately from architecture/usecase closure.

## Policy
1. Usecase `GREEN` in architecture docs means code/contract/governance closure.
2. Production readiness requires real provider + real environment evidence.
3. Do not downgrade architecture status for pending production rollout checks; track here.
4. Latest deterministic architecture reality check for UC-018..UC-032:
   `app/hoc/docs/architecture/usecases/UC018_UC032_REALITY_AUDIT_2026-02-12.md` (re-validated at 2026-02-12T18:29Z).
5. Wave-1 script coverage architecture audit completed for policies/logs:
   `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_1_AUDIT_2026-02-12.md` (does not change prod readiness status by itself).
6. Wave-2 script coverage architecture audit completed for analytics/incidents/activity:
   `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md` (does not change prod readiness status by itself).
7. Wave-3 script coverage architecture audit completed for controls/account:
   `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_AUDIT_2026-02-12.md` (does not change prod readiness status by itself).
8. Wave-4 script coverage architecture audit completed for hoc_spine/integrations/api_keys/overview/agent/ops/apis:
   `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_4_AUDIT_2026-02-12.md` (does not change prod readiness status by itself).

## Status Legend
- `NOT_STARTED`
- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_GO_LIVE`

## UC Readiness Register
| UC | Architecture Status | Prod Readiness Status | Owner | Last Updated | Notes |
| --- | --- | --- | --- | --- | --- |
| UC-001 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | LLM run monitoring live validation pending. |
| UC-002 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Onboarding live validation pending. |
| UC-003 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Deterministic trace ingest: run real-provider + real-env replay readiness checks. |
| UC-004 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Runtime controls evaluation: live threshold and enforcement behavior pending. |
| UC-005 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Baseline monitoring (no controls): live observation path pending. |
| UC-006 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Activity stream + feedback lifecycle in real env pending. |
| UC-007 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Incident lifecycle from signals in staging/prod-like env pending. |
| UC-008 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Analytics artifact reproducibility on real traffic pending. |
| UC-009 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Controls/policies proposal lifecycle in live env pending. |
| UC-010 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Activity feedback TTL/expiry/reopen live validation pending. |
| UC-011 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Incident resolution + postmortem artifact real workflow pending. |
| UC-012 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Recurrence signature/grouping behavior on real datasets pending. |
| UC-013 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Canonical policy proposal accept path live validation pending. |
| UC-014 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Controls override lifecycle live approval/expiry validation pending. |
| UC-015 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Threshold resolver version binding on real runs pending. |
| UC-016 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Analytics reproducibility hash/version live checks pending. |
| UC-017 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-11 | Replay mode labeling (FULL/TRACE_ONLY) in real env pending. |
| UC-018 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Policy snapshot lifecycle + integrity: real snapshot replay and verification drills pending. |
| UC-019 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Policies proposals query lifecycle: live tenant query parity and latency validation pending. |
| UC-020 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Policies rules query lifecycle: production rule visibility and query consistency checks pending. |
| UC-021 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Policies limits query lifecycle: real budget/limit read validation across live policy states pending. |
| UC-022 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Policies sandbox lifecycle: live sandbox policy execution telemetry validation pending. |
| UC-023 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Policy conflict explainability: live conflict resolution audit-trail validation pending. |
| UC-024 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Analytics anomaly lifecycle: real anomaly detection and persistence behavior pending. |
| UC-025 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Analytics prediction lifecycle: live prediction stability and model/version traceability pending. |
| UC-026 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Analytics dataset validation lifecycle: real dataset drift/validation operations pending. |
| UC-027 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Analytics snapshot/baseline jobs: production scheduler run and replay checks pending. |
| UC-028 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Analytics cost write lifecycle: live write-path idempotency and provenance validation pending. |
| UC-029 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Incidents recovery-rule lifecycle: live recovery decisioning behavior and safety checks pending. |
| UC-030 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Incidents policy-violation truth pipeline: live violation truth-check and incident creation drills pending. |
| UC-031 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Incidents pattern/postmortem learnings lifecycle: live recurrence + learnings quality validation pending. |
| UC-032 | `GREEN` | `NOT_STARTED` | `tbd` | 2026-02-12 | Logs redaction governance lifecycle: production redaction policy and trace-safe export validation pending. |

## Required Evidence (Per UC)
1. Real provider credential path works (BYOK and/or managed key as applicable).
2. Real connector handshake succeeds for target environment(s).
3. SDK installation + attestation recorded in persistent store.
4. Deterministic trace capture available for at least one real run.
5. Replay behavior validated (full replay or trace-only, explicitly marked).
6. Secret rotation and revocation flow validated.
7. Failure-path drills executed and audited.

## Evidence Template
| Field | Value |
| --- | --- |
| UC |  |
| Tenant ID |  |
| Project ID |  |
| Environment |  |
| Provider Mode |  |
| Validation Item |  |
| Command/Test ID |  |
| Result |  |
| Timestamp (UTC) |  |
| Artifact/Log Reference |  |

## Promotion Rule
Mark `Prod Readiness Status = READY_FOR_GO_LIVE` only when all required evidence items are completed for the UC and reviewed.
