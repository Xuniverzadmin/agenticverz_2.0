# UC Execution Taskpack (UC-018..UC-032) for Claude

- Date: 2026-02-12
- Source context: `UC_EXPANSION_CONTEXT_UC018_UC032.md`
- Goal: execute UC expansion in deterministic, architecture-safe batches and promote each UC through `RED -> YELLOW -> GREEN`.

## 0) Non-Negotiable Architecture Rules

1. Preserve execution topology: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`.
2. Never call L5/L6 directly from L2.
3. L4 orchestrates only; no domain business logic in L4.
4. L5 engines decide; L6 drivers perform effects.
5. No DB/ORM imports in L5 engines.
6. No business conditionals in L6 drivers.
7. Do not introduce `*_service.py` in HOC.

## 1) Global Deterministic Gates

Run in `backend/` unless noted.

Architecture gates:
1. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
2. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
3. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`

UC-MON deterministic gates:
1. `PYTHONPATH=. python3 scripts/verification/uc_mon_route_operation_map_check.py`
2. `PYTHONPATH=. python3 scripts/verification/uc_mon_event_contract_check.py`
3. `PYTHONPATH=. python3 scripts/verification/uc_mon_storage_contract_check.py`
4. `PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`

Domain purity gate (run with current domain):
1. `PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain <domain> --json --advisory`

Pass criteria:
1. Every gate exits `0`.
2. No increase in cross-domain violations.
3. Pairing detector reports `direct_l2_to_l5 = 0` and `orphaned = 0`.
4. Purity audit summary shows `blocking = 0`.

## 2) Execution Protocol (per UC)

1. Register UC in `INDEX.md` and `HOC_USECASE_CODE_LINKAGE.md` as `RED`.
2. Implement minimal wiring/code/test changes.
3. Add/update route-operation evidence in `UC_MONITORING_ROUTE_OPERATION_MAP.md` when routes/operations change.
4. Run domain purity + relevant deterministic gates.
5. If all pass, move to `YELLOW` with evidence.
6. Run full gate pack; if stable, promote to `GREEN`.

## 3) Ordered UC Tasks

## UC-018 (policies) — Policy Snapshot Lifecycle + Integrity

Tasks:
1. Wire snapshot lifecycle through canonical L2->L4->L5->L6 path using snapshot operations.
2. Validate `create/get/history/verify` path around `snapshot_engine` functions.
3. Ensure response includes deterministic anchors (`as_of`, snapshot version/id where applicable).
4. Add focused tests for snapshot creation/history/verification invariants.

Acceptance criteria:
1. Snapshot flows execute only via L4 operations.
2. Snapshot integrity verification is test-covered and deterministic.
3. No L5 DB imports; no L2 direct engine calls.

If broken, fix:
1. Missing wiring: add L4 operation registration/handler, not direct L2->L5 calls.
2. Integrity mismatch handling unclear: fail closed with explicit error path.
3. DB calls in L5: move all persistence to L6 driver.

Gates:
1. Domain purity (`policies`)
2. Route-operation map check
3. Deterministic read check
4. Full strict aggregator

## UC-019 (policies) — Proposals Query Lifecycle

Tasks:
1. Validate list/detail/count draft query flow in proposals query engine + read driver.
2. Ensure L2 routes map to canonical L4 proposal query operations.
3. Add deterministic query semantics (`as_of`/ordering consistency if exposed).

Acceptance criteria:
1. All proposal query endpoints map to L4 and are documented.
2. Query responses are stable for same filters + same `as_of`.
3. No proposal endpoint triggers enforcement mutation.

If broken, fix:
1. Authority drift: separate query ops from enforcement ops.
2. Unstable ordering: enforce deterministic sort key and `as_of`.
3. Missing L4 map entry: add explicit operation binding.

Gates:
1. Domain purity (`policies`)
2. Route-operation map check
3. Deterministic read check
4. Full strict aggregator

## UC-020 (policies) — Rules Query Lifecycle

Tasks:
1. Validate list/detail/count rules query path.
2. Ensure rules query endpoints are query-only and non-mutating.
3. Add tests for deterministic paging/sorting behavior.

Acceptance criteria:
1. Rule queries are L2->L4->L5->L6 only.
2. Deterministic stable responses for repeated same-input reads.
3. Documentation evidence updated in linkage + route map.

If broken, fix:
1. Mixed query/mutation endpoint: split operations by intent.
2. L4 bypass: route through operation registry binding.
3. Non-deterministic read: add canonical ordering and metadata.

Gates:
1. Domain purity (`policies`)
2. Route-operation map check
3. Deterministic read check
4. Full strict aggregator

## UC-021 (policies/controls) — Limits Query Lifecycle

Tasks:
1. Validate limits/budgets/detail query flow across policies query engine and limits read driver.
2. Ensure cross-domain usage stays orchestration-only at L4.
3. Add tests for limit detail consistency and version visibility.

Acceptance criteria:
1. Query paths are deterministic and read-only.
2. No cross-domain direct imports from L5/L6 violating boundaries.
3. Stable evidence query documented.

If broken, fix:
1. Cross-domain import leakage: move coordination to L4.
2. L6 business branching: move branching decisions to L5.
3. Missing deterministic metadata: add `as_of` and data version.

Gates:
1. Domain purity (`policies` and `controls`)
2. Cross-domain validator
3. Deterministic read check
4. Full strict aggregator

## UC-022 (policies) — Sandbox Definition + Execution Telemetry

Tasks:
1. Validate `define/list/get policy` and execution record/stats surfaces via L4 sandbox handler.
2. Ensure write/read separation and deterministic replayability of execution records.
3. Add tests for sandbox policy CRUD + telemetry consistency.

Acceptance criteria:
1. Sandbox operations are registry-bound and traceable.
2. Execution records/stats are reproducible for same snapshot/version inputs.
3. No direct L2->L5 call path.

If broken, fix:
1. Telemetry without deterministic anchors: include execution version + timestamp contract.
2. Handler reflection/dynamic dispatch: replace with explicit map.
3. Mutations bypassing authority: enforce L4 authorization guard.

Gates:
1. Domain purity (`policies`)
2. Event contract check (if events emitted)
3. Storage contract check (if schema changes)
4. Full strict aggregator

## UC-023 (policies) — Conflict Resolution Explainability

Tasks:
1. Validate conflict resolution flow between policy conflict resolver and optimizer conflict resolver driver.
2. Ensure explainability payload exists for resolved conflicts.
3. Add tests for deterministic winner selection given same policy set.

Acceptance criteria:
1. Conflict outcomes are deterministic and explainable.
2. No hidden runtime randomness in resolution path.
3. L4 operation mapping + evidence docs updated.

If broken, fix:
1. Non-deterministic branch behavior: anchor ordering/precedence explicitly.
2. Explainability missing: add structured reason fields.
3. Driver making policy decisions: move logic back to engine.

Gates:
1. Domain purity (`policies`)
2. Deterministic read check
3. Full strict aggregator

## UC-024 (analytics) — Cost Anomaly Detection Lifecycle

Tasks:
1. Close `No (gap)` anomaly operations (`detect_*`, `run_anomaly_detection`, persistence path).
2. Ensure anomaly lifecycle routes map through L4 analytics handler.
3. Add tests for anomaly detection determinism and persistence idempotency.

Acceptance criteria:
1. All anomaly operations are wired and test-covered.
2. Detection and persisted outputs are reproducible under fixed input window.
3. Storage contract remains valid.

If broken, fix:
1. Missing route->operation mapping: add explicit operation entries.
2. Duplicate anomaly writes: add idempotent write key/version binding.
3. Drift logic in driver: move decision rules into L5 engine.

Gates:
1. Domain purity (`analytics`)
2. Route-operation map check
3. Storage contract check
4. Deterministic read check
5. Full strict aggregator

## UC-025 (analytics) — Prediction Cycle Lifecycle

Tasks:
1. Wire and validate `predict_failure_likelihood`, `predict_cost_overrun`, `run_prediction_cycle`.
2. Ensure prediction reads/writes are versioned and deterministic.
3. Add tests for repeated same-input prediction stability.

Acceptance criteria:
1. Prediction operations are registry-bound and deterministic.
2. Prediction records include version/hash metadata where applicable.
3. No architecture boundary violations.

If broken, fix:
1. Unstable outputs: bind to model/version + input hash.
2. Missing persistence lineage: add provenance fields in L6 payload.
3. L2 direct access to L6: route via L4/L5 path.

Gates:
1. Domain purity (`analytics`)
2. Route-operation map check
3. Deterministic read check
4. Storage contract check (if schema touched)
5. Full strict aggregator

## UC-026 (analytics) — Dataset Validation Lifecycle

Tasks:
1. Validate dataset list/get/validate/validate-all flows.
2. Ensure deterministic validation output format and ordering.
3. Add tests for validation reproducibility by dataset and as-of context.

Acceptance criteria:
1. Dataset validation endpoints are fully mapped and covered.
2. Same dataset + same inputs yields stable validation result.
3. Evidence in linkage and route map is complete.

If broken, fix:
1. Partial route wiring: add missing L4 operations and handlers.
2. Inconsistent validation output: normalize schema and ordering.
3. Cross-layer coupling: remove direct imports violating layer model.

Gates:
1. Domain purity (`analytics`)
2. Route-operation map check
3. Deterministic read check
4. Full strict aggregator

## UC-027 (analytics) — Snapshot/Baseline Scheduled Jobs

Tasks:
1. Activate and validate hourly/daily snapshot jobs.
2. Ensure baseline computations are deterministic and replay-safe.
3. Add job-level tests for repeatability and no duplicate writes.

Acceptance criteria:
1. Job entry points are callable and validated.
2. Snapshot baseline outputs are deterministic for fixed input windows.
3. Job writes satisfy idempotency expectations.

If broken, fix:
1. Uncalled entry points: wire through canonical orchestrated trigger.
2. Duplicate batch writes: enforce upsert/version constraints.
3. Time authority drift: use single `as_of` per job execution.

Gates:
1. Domain purity (`analytics`)
2. Storage contract check
3. Deterministic read check
4. Full strict aggregator

## UC-028 (analytics) — Cost Write Lifecycle

Tasks:
1. Validate create/update cost records, feature tags, and budgets through L5/L6 write path.
2. Ensure writes preserve deterministic provenance attributes.
3. Add tests for idempotent repeated writes.

Acceptance criteria:
1. Cost write functions are wired, called, and covered.
2. Repeated identical write requests are idempotent.
3. No write logic leaks into L2 or L4.

If broken, fix:
1. Uncalled write functions: add canonical operations and tests.
2. Non-idempotent inserts: add unique key/upsert strategy in L6.
3. Missing provenance: add hash/version metadata fields.

Gates:
1. Domain purity (`analytics`)
2. Storage contract check
3. Full strict aggregator

## UC-029 (incidents) — Recovery Rule Evaluation Lifecycle

Tasks:
1. Close `No (gap)` recovery-rule evaluation surfaces.
2. Validate decision functions (`evaluate_rules`, `suggest_recovery_mode`, `should_auto_execute`) in real path.
3. Add tests for deterministic decisions under fixed confidence inputs.

Acceptance criteria:
1. Recovery-rule path is operation-bound and test-covered.
2. Decision outputs are deterministic for same inputs.
3. No direct L2->L5 bypass remains.

If broken, fix:
1. Direct L2 usage of recovery functions: route through L4 operation.
2. Decision randomness: normalize thresholds and precedence.
3. Cross-domain write in L5: push writes into incident drivers.

Gates:
1. Domain purity (`incidents`)
2. Route-operation map check
3. Deterministic read check
4. Full strict aggregator

## UC-030 (incidents) — Policy Violation Truth Pipeline

Tasks:
1. Wire and validate violation truth checks + incident creation pipeline.
2. Ensure persistence path via `policy_violation_driver` is authoritative.
3. Add tests for truth-check failure, suppression, and positive create path.

Acceptance criteria:
1. Truth-check path is executed and evidence-backed.
2. Pending design-ahead functions become validated runtime behavior.
3. Incident creation remains deterministic/idempotent for same violation key.

If broken, fix:
1. Truth check skipped: enforce precondition gate in engine.
2. Incident duplication: use deterministic correlation key.
3. Driver making truth decisions: move rule logic to engine.

Gates:
1. Domain purity (`incidents`)
2. Storage contract check
3. Event contract check
4. Full strict aggregator

## UC-031 (incidents) — Pattern + Postmortem Learnings Lifecycle

Tasks:
1. Validate pattern detection + recurrence + postmortem learnings flow.
2. Ensure L5 pattern/postmortem engines are called from canonical incident handlers.
3. Add tests for deterministic grouping and learnings output.

Acceptance criteria:
1. Pattern and postmortem paths are no longer underutilized.
2. Recurrence/postmortem outputs are reproducible for same data window.
3. Evidence queries and docs updated.

If broken, fix:
1. Orphaned analysis modules: register explicit operations and handlers.
2. Non-deterministic grouping: enforce signature/version strategy.
3. Missing lineage fields: persist artifact ids + version fields.

Gates:
1. Domain purity (`incidents`)
2. Route-operation map check
3. Deterministic read check
4. Storage contract check (if schema touched)
5. Full strict aggregator

## UC-032 (logs) — Redaction Governance + Trace-Safe Export

Tasks:
1. Close redaction `No (gap)` surfaces for traces.
2. Consolidate/validate redaction behavior across L5 and L6 implementations.
3. Add tests for deterministic redaction output, sensitive-field registration, and replay safety.

Acceptance criteria:
1. Trace redaction paths are wired and covered.
2. Same input trace yields same redacted output.
3. No bypass around canonical redaction path.

If broken, fix:
1. Dual implementation drift (L5 vs L6): choose canonical flow and remove divergence in call path.
2. Inconsistent redaction patterns: centralize pattern registry and deterministic order.
3. Redaction after persistence instead of before export path: fix ordering in orchestrated flow.

Gates:
1. Domain purity (`logs`)
2. Event contract check
3. Deterministic read check
4. Full strict aggregator

## 4) Batch Promotion Rule

1. Complete UC in order (`018` to `032`).
2. Each UC must have explicit evidence section in `HOC_USECASE_CODE_LINKAGE.md`.
3. Do not promote to `GREEN` unless all selected gates are `PASS` and command outputs are captured.
4. If any gate fails, fix only through architecture-compliant changes, rerun full gate set, and then promote.

## 5) Required Deliverables per UC

1. Code changes (minimal and reversible).
2. Tests for positive path, negative path, determinism path.
3. Updated route-operation/evidence docs.
4. Gate command outputs recorded in implemented handover artifact.
