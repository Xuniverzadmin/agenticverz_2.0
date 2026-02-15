# UC_MONITORING_USECASE_PLAN.md

## Purpose
Define audit-ready monitoring usecases for CUS domains and capture current gap analysis + pending implementation items.

## Companion Methods
- `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_IMPLEMENTATION_METHODS.md`

## Scope
- Audience: `cust`
- Domains in scope: `activity`, `incidents`, `policies`, `controls`, `analytics`, `logs`
- Architecture constraint: L2 -> L4 -> L5 -> L6 -> L7 only.

## Scenario Paths
1. Scenario A (configured controls): enforce control decisions at runtime with auditable outcomes.
2. Scenario B (no configured controls): run baseline-observation monitoring, generate proposals, keep enforcement explicit.

## Usecase Set

### UC-003 (legacy `UC-MON-01`): Ingest LLM Run + Canonical Deterministic Trace
- Primary domains: `logs` (primary), `analytics` (derived), `activity` (derived)
- Objective: canonical run/event persistence with integrity chain and replay metadata.
- Core outputs: run record, ordered event stream, integrity hash chain, replay metadata.
- Key audit events: `RunIngested`, `TraceCanonicalized`, `TracePersisted`, `EvidenceChainComputed`

### UC-004 (legacy `UC-MON-02`): Runtime Controls Evaluation (Configured Path)
- Primary domains: `controls` (primary), `logs`, `activity`, `incidents`, `analytics`, optional `policies`
- Objective: evaluate active controls and apply allow/warn/throttle/block/degrade decisions.
- Core outputs: decision evidence linked to run and control version.
- Key audit events: `ControlsEvaluated`, `ControlDecisionApplied`, `ThresholdSignalEmitted`, `OverrideApplied`

### UC-005 (legacy `UC-MON-03`): Default Monitoring Baseline (No Controls Configured)
- Primary domains: `controls` (baseline read), `analytics`, `activity`, `logs`, optional `incidents`
- Objective: non-silent baseline monitoring with explicit versioned baseline artifacts.
- Core outputs: baseline signals, attention items, control/policy proposal seeds.
- Key audit events: `BaselineLoaded`, `BaselineSignalsComputed`, `ControlProposalGenerated`, `AttentionQueueUpdated`

### UC-006 (legacy `UC-MON-04`): Activity Stream + Attention Queue + Feedback
- Primary domains: `activity` (primary), `logs`, `analytics`, `controls`, linked `incidents`
- Objective: deterministic activity feed and signal feedback workflow.
- Core outputs: activity cards, evidence links, `ack`/`suppress` feedback events.
- Key audit events: `SignalAcknowledged`, `SignalSuppressed`

### UC-007 (legacy `UC-MON-05`): Incident Lifecycle from Run-Linked Signals
- Primary domains: `incidents` (primary), `logs`, `activity`, `controls`, `policies`, `analytics`
- Objective: create/update incident records with run lineage and severity/recurrence logic.
- Core outputs: incident create/update/link/resolve lifecycle with explicit correlations.
- Key audit events: `IncidentCreated`, `IncidentRunLinked`, `IncidentSeverityUpdated`, `IncidentResolved`

### UC-008 (legacy `UC-MON-06`): Reproducible Analytics from Persisted Inputs
- Primary domains: `analytics` (primary), `logs`, `activity`, `controls`
- Objective: compute reproducible usage/cost/anomaly outputs from persisted data.
- Core outputs: versioned datasets, window-scoped analytics artifacts, anomaly actions.
- Key audit events: `AnalyticsDatasetBuilt`, `AnomalyDetected`, `AnomalyAcknowledged`, `AnomalyResolved`

### UC-009 (legacy `UC-MON-07`): Controls + Policies Proposal Generation
- Primary domains: `controls` proposals, `policies` proposals, `analytics`, `activity`, `logs`
- Objective: generate actionable, evidence-linked proposals from observed patterns.
- Core outputs: proposal artifacts with evidence and acceptance/rejection lifecycle.
- Key audit events: `ControlProposalCreated`, `PolicyProposalCreated`, `ProposalAccepted`, `ProposalRejected`

## Additional Closure Usecases (Gap-Plug Pack)

### UC-010 (legacy `UC-ACT-01`): Activity Feedback Lifecycle (Ack/Suppress/TTL/Expiry/Reopen/Bulk)
- Domain: `activity` (primary)
- Objective: full feedback lifecycle with deterministic `as_of` semantics and bulk target-set hashing.
- Required events: `SignalAcknowledged`, `SignalSuppressed`, `SignalFeedbackExpired|SignalFeedbackEvaluated`, `BulkSignalFeedbackApplied`

### UC-011 (legacy `UC-INC-02`): Incident Resolution + Postmortem Artifact Contract
- Domain: `incidents` (primary)
- Objective: enforce explicit resolution payload + required evidence and create postmortem stub.
- Required events: `IncidentResolved`, `IncidentStateChanged`, `IncidentPostmortemCreated`, `IncidentEvidenceLinked`

### UC-012 (legacy `UC-INC-03`): Incident Recurrence Grouping + Signature Binding
- Domain: `incidents` (primary)
- Objective: deterministic recurrence grouping using persisted `recurrence_signature` + `signature_version`.
- Required events: `IncidentRecurrenceGrouped`

### UC-013 (legacy `UC-POL-02`): Policy Proposal Acceptance via Canonical Write Flow
- Domain: `policies` (primary)
- Objective: proposal generation is non-enforcing; enforcement changes only via canonical accept/compile/publish flow.
- Required events: `PolicyProposalAccepted`, `PolicyCompiled`, `PolicyVersionCreated`, `PolicyVersionActivated`

### UC-014 (legacy `UC-CTL-02`): Override Lifecycle (Request/Approve/Reject/Cancel/Expire)
- Domain: `controls` (primary)
- Objective: explicit override workflow with actor lineage and expiry semantics.
- Required events: `OverrideRequested`, `OverrideApproved`, `OverrideRejected`, `OverrideCanceled`, `OverrideExpired`, `ControlsEvaluated`

### UC-015 (legacy `UC-CTL-03`): Threshold Resolver Version Binding Per Run
- Domain: `controls` (primary)
- Objective: persist resolver version + evaluated thresholds per run; preserve reproducibility.
- Required events: `ThresholdEvaluated`

### UC-016 (legacy `UC-ANA-02`): Analytics Reproducibility Contract
- Domain: `analytics` (primary)
- Objective: persist `dataset_version`, `input_window_hash`, `compute_code_version`, `as_of` for every derived artifact.
- Required events: `AnalyticsDatasetBuilt`, `AnalyticsMetricComputed`, `AnomalyDetected`

### UC-017 (legacy `UC-LOG-02`): Trace API + Replay Mode Labeling
- Domain: `logs` (primary)
- Objective: enforce replay mode (`FULL|TRACE_ONLY`) and versioned replay artifacts with explicit integrity lineage.
- Required events: `ReplayModeDetermined`, `ReplayAttempted`, `ReplaySucceeded|ReplayFailed`, `TraceRedactedVersionCreated`

## Prerequisites (Before Implementing UC-010..UC-017)
1. `as_of` determinism baseline must remain green:
- `PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py` => `0 WARN`, `0 FAIL`
2. UC-MON aggregate validator strict mode should stay green:
- `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict` => exit `0`
3. Event base contract remains canonical and enforced:
- `backend/app/hoc/cus/hoc_spine/authority/event_schema_contract.py`
4. Migration chain `128..132` remains intact and reversible.
5. Policy authority boundary lock:
- proposal endpoints cannot mutate enforcement state unless canonical accept flow executes.

## Domain Coverage Matrix
| Domain | Covered by usecases | Coverage quality |
| --- | --- | --- |
| `activity` | 01, 03, 04, 05, 06, 07 | Good, needs deeper feedback lifecycle invariants |
| `incidents` | 02, 05 | Good, needs full resolution/postmortem closure invariants |
| `policies` | 02, 07 | Partial, authority boundaries need stricter mutation guards |
| `controls` | 02, 03, 04, 05, 06, 07 | Good, needs override lifecycle detail and per-run version binding |
| `analytics` | 01, 03, 05, 06, 07 | Good, needs reproducibility contract hardening |
| `logs` | 01, 03, 04, 05, 06, 07 | Strong, needs explicit replay mode contract |

## Analysis Summary
1. Domain touch coverage is complete across all six domains.
2. Current usecase set is strong for architectural intent and cross-domain flow.
3. For code-audit closure, each domain still needs explicit core-function invariants and acceptance checks.

## Pending Items (Gap Backlog)

### P0 (Must close for implementation start) — ALL COMPLETE (2026-02-11)
1. ~~Build grep-checkable route->handler->engine->store map in `UC_MONITORING_ROUTE_OPERATION_MAP.md`.~~ DONE — 73 routes across 6 domains, 96 verification checks pass.
2. ~~Define canonical event schema usage per UC plus domain extension fields.~~ DONE — 5 domain extension field sets defined, 46 contract checks pass.
3. Add strict policy authority rule to UC-MON-07: proposals cannot mutate enforcement state until accepted through canonical policy write flow. — PENDING (policy mutation guard not yet implemented).
4. ~~Add replay mode contract to UC-MON-01 (`full_replay` vs `trace_only`) and persist mode per run.~~ DONE — migration 132, `aos_traces.replay_mode` column.
5. ~~Define deterministic read contract with `as_of` watermark on relevant read APIs.~~ DONE — contract defined, storage ready, L2 wiring advisory.

### P1 (Must close for YELLOW->GREEN of monitoring UCs)
1. Activity feedback lifecycle completion: TTL/expiry/reopen semantics and bulk status behavior. — STORAGE READY (migration 128: `signal_feedback` table), L5/L6 wiring pending.
2. Incident lifecycle completion: resolution workflow, recurrence grouping, postmortem minimum fields. — STORAGE READY (migration 129: `incidents` ADD COLUMN), L5/L6 wiring pending.
3. Controls lifecycle completion: override request/approve/reject/cancel transitions with audit lineage. — STORAGE READY (migration 130: `controls_evaluation_evidence` table), L5/L6 wiring pending.
4. Controls/run binding: persist exact control version used for each run decision. — STORAGE READY (migration 130: `control_set_version` column).
5. Analytics reproducibility: persist dataset version + input window hash for every derived artifact. — STORAGE READY (migration 131: `analytics_artifacts` table).
6. ~~Migration pack for new storage fields added and verified.~~ DONE — 5 migrations (128-132), 53 storage checks pass.
7. ~~CI/verifier scripts for UC-MON pack added and passing.~~ DONE — 4 verifiers + 1 aggregator, 215 checks pass (5 WARN advisory).

### P2 (Hardening)
1. ~~Add verifier script for UC-MON route-to-operation mapping.~~ DONE — `uc_mon_route_operation_map_check.py`, 96/96 pass.
2. Add synthetic test pack for Scenario A vs Scenario B execution parity. — PENDING.
3. Add canonical evidence query checklist per UC in linkage doc. — PENDING.

### Current Phase: Advisory (local-first). No CI-blocking checks wired yet.

## Suggested Execution Order
1. Implement UC-MON-01 foundations (logs + event schema + replay mode contract).
2. Implement UC-MON-03 baseline path (no-controls scenario).
3. Implement UC-MON-04 activity surface and feedback lifecycle.
4. Implement UC-MON-06 analytics reproducibility artifacts.
5. Implement UC-MON-02 controls enforcement path.
6. Implement UC-MON-05 incidents lifecycle closure.
7. Implement UC-MON-07 proposal generation + acceptance guardrails.

## Exit Criteria for This Plan
1. Each UC has file-level linkage to L2/L4/L5/L6 handlers/drivers.
2. Domain invariants are encoded as tests and passing in CI.
3. Usecase statuses can be promoted in canonical docs with evidence.
