# UC SPLIT Partition Plan (2026-02-15)

**Status:** IMPLEMENTED
**Source:** Iteration-3 Decision Table (`HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv`)
**Scope:** 8 SPLIT rows resolved with per-operation UC partition. All kept as shared multi-UC scripts with explicit operation boundaries (no refactoring needed).

---

## Decision: Keep as Shared Multi-UC Scripts

All 8 SPLIT scripts are L4 handlers, L4 authority modules, L5 engines, or L6 drivers that naturally serve multiple usecases via distinct operations. Refactoring would violate the single-handler-per-domain pattern and create artificial file proliferation. The correct resolution is explicit per-operation UC partition.

---

## SPLIT-1: `event_schema_contract.py` -> UC-001 | UC-002

**Path:** `app/hoc/cus/hoc_spine/authority/event_schema_contract.py`
**Type:** L4 Authority (shared contract, not a handler)

| Export | UC |
|--------|-----|
| `validate_event_payload()` | UC-001 (event validation for run monitoring events) |
| `is_valid_event_payload()` | UC-001 (non-throwing variant) |
| `REQUIRED_EVENT_FIELDS` | UC-001 + UC-002 (shared 9-field contract) |
| `VALID_ACTOR_TYPES` | UC-001 + UC-002 (shared actor taxonomy) |
| `CURRENT_SCHEMA_VERSION` | UC-001 + UC-002 (shared version) |

**Partition rule:** Contract definition is shared (UC-001 + UC-002). Validation enforcement is UC-001 primary (called by all event emitters). UC-002 consumes the contract via `_emit_validated_onboarding_event()` in `onboarding_handler.py`.

---

## SPLIT-2: `activity_handler.py` -> UC-001 | UC-006 | UC-010

**Path:** `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py`
**Type:** L4 Handler (6 operations registered)

| Operation | UC | Rationale |
|-----------|-----|-----------|
| `activity.query` | **UC-001** | Core activity reads (runs, signals, metrics, patterns, cost-analysis, attention-queue) |
| `activity.telemetry` | **UC-001** | Telemetry ingestion/query (ingest_usage, ingest_batch, get_usage) |
| `activity.orphan_recovery` | **UC-001** | System resilience (recover orphaned runs) |
| `activity.signal_feedback` | **UC-006** | Signal feedback lifecycle (acknowledge, suppress, reopen, evaluate_expired) |
| `activity.signal_fingerprint` | **UC-010** | Pure computation (fingerprint from row, batch fingerprinting) |
| `activity.discovery` | **UC-010** | Discovery ledger (emit_signal, get_signals) |

**Invariant:** `acknowledge_signal` and `suppress_signal` dispatch within `activity.query` also serve UC-006; however they are primarily registered under `activity.signal_feedback`.

---

## SPLIT-3: `controls_handler.py` -> UC-004 | UC-021

**Path:** `app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`
**Type:** L4 Handler (7 operations registered)

| Operation | UC | Rationale |
|-----------|-----|-----------|
| `controls.query` | **UC-004** | Controls CRUD (list, get, update, enable, disable) |
| `controls.circuit_breaker` | **UC-004** | Circuit breaker state (is_disabled, get_state, reset, get_incidents) |
| `controls.killswitch.read` | **UC-004** | Killswitch reads (verify, get_state, list_guardrails, list_incidents) |
| `controls.killswitch.write` | **UC-004** | Killswitch writes (freeze, unfreeze, get_or_create_state) |
| `controls.evaluation_evidence` | **UC-004** | Per-run control binding evidence (record, query) |
| `controls.thresholds` | **UC-021** | Threshold management (get_defaults, validate_params, get_effective_params) |
| `controls.overrides` | **UC-021** | Limit overrides lifecycle (request, list, get, cancel, approve, reject, expire) |

---

## SPLIT-4: `incidents_handler.py` -> UC-007 | UC-011 | UC-031

**Path:** `app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py`
**Type:** L4 Handler (6 operations registered)

| Operation | UC | Rationale |
|-----------|-----|-----------|
| `incidents.query` | **UC-007** | Incident reads (list, active, resolved, historical, detail, metrics, patterns, recurrence, cost, trend) |
| `incidents.write` | **UC-007** | Incident lifecycle writes (acknowledge, resolve, manual_close) |
| `incidents.cost_guard` | **UC-007** | Cost guard queries (spend_totals, budget, baseline, anomalies) |
| `incidents.recurrence` | **UC-007** | Recurrence grouping (get_group, create_postmortem_stub) |
| `incidents.export` | **UC-011** | Compliance exports (evidence_bundle, soc2_bundle, executive_debrief) |
| `incidents.recovery_rules` | **UC-031** | Recovery rule evaluation (evaluate, get_rules) |

---

## SPLIT-5: `policies_handler.py` -> UC-018 | UC-019 | UC-020 | UC-021 | UC-022 | UC-023

**Path:** `app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`
**Type:** L4 Handler (23 operations registered)

| Operation | UC | Rationale |
|-----------|-----|-----------|
| `policies.query` | **UC-018** | Policy reads (rules, limits, state, metrics, conflicts, deps, violations, budgets) |
| `policies.rules` | **UC-018** | Rule CRUD (create, update, get) |
| `policies.proposals_query` | **UC-018** | Proposals query engine |
| `policies.rules_query` | **UC-018** | Rules query engine |
| `policies.policy_facade` | **UC-018** | Core policy engine (evaluate, pre_check, state, violations, versions, deps, temporal) |
| `policies.approval` | **UC-018** | Approval workflow (create, review, update, batch_escalate, batch_expire) |
| `policies.enforcement` | **UC-019** | Enforcement (evaluate, get_status, evaluate_batch) |
| `policies.enforcement_write` | **UC-019** | Enforcement writes (record_enforcement) |
| `policies.health` | **UC-019** | Health checks (m20_policy, m9_failure, m10_recovery) |
| `policies.guard_read` | **UC-019** | Guard reads (async) |
| `policies.sync_guard_read` | **UC-019** | Guard reads (sync) |
| `policies.workers` | **UC-019** | Workers ops (verify_run, get_run, list_runs, budgets, advisories) |
| `policies.governance` | **UC-020** | Governance (kill_switch, mode, state, conflicts, boot_status) |
| `rbac.audit` | **UC-020** | RBAC audit (query_audit_logs, cleanup) |
| `policies.limits` | **UC-021** | Limit CRUD (create, update, delete, get) |
| `policies.limits_query` | **UC-021** | Limits query engine |
| `policies.rate_limits` | **UC-021** | Rate limits (list, get, update, check, usage, reset) |
| `policies.lessons` | **UC-022** | Lessons learned (detect, emit, list, convert, defer, dismiss, reactivate) |
| `policies.recovery.match` | **UC-022** | Recovery matching (suggest, suggest_hybrid, candidates) |
| `policies.recovery.write` | **UC-022** | Recovery writes (upsert, enqueue, update) |
| `policies.recovery.read` | **UC-022** | Recovery reads (detail, selected_action, provenance) |
| `policies.simulate` | **UC-023** | Simulation (simulate) |
| `policies.customer_visibility` | **UC-023** | Customer visibility (fetch_run_outcome, fetch_decision_summary) |
| `policies.replay` | **UC-023** | Replay reads (incidents, proxy_calls, events, timeline) |

---

## SPLIT-6: `trace_api_engine.py` -> UC-003 | UC-017

**Path:** `app/hoc/cus/logs/L5_engines/trace_api_engine.py`
**Type:** L5 Engine (class methods, not L4 operations)

| Method | UC | Rationale |
|--------|-----|-----------|
| `list_traces()` | **UC-003** | Trace query/listing |
| `store_trace()` | **UC-003** | Trace storage with redaction |
| `get_trace()` | **UC-003** | Trace retrieval by run_id |
| `delete_trace()` | **UC-003** | Trace deletion |
| `cleanup_old_traces()` | **UC-003** | Trace maintenance |
| `get_trace_by_root_hash()` | **UC-017** | Deterministic replay: trace lookup by root hash |
| `compare_traces()` | **UC-017** | Deterministic replay: trace comparison |
| `check_idempotency()` | **UC-017** | Deterministic replay: idempotency check |

---

## SPLIT-7: `pg_store.py` -> UC-003 | UC-017

**Path:** `app/hoc/cus/logs/L6_drivers/pg_store.py`
**Type:** L6 Driver (class methods)

| Method | UC | Rationale |
|--------|-----|-----------|
| `start_trace()` | **UC-003** | Trace lifecycle: start |
| `record_step()` | **UC-003** | Trace lifecycle: record step (S6 immutability) |
| `complete_trace()` | **UC-003** | Trace lifecycle: complete |
| `mark_trace_aborted()` | **UC-003** | Trace lifecycle: fail-closed abort (PIN-406) |
| `store_trace()` | **UC-003** | SDK/simulation trace storage (S6 append-only) |
| `get_trace()` | **UC-003** | Trace retrieval with tenant isolation |
| `search_traces()` | **UC-003** | Trace search with multi-filter |
| `list_traces()` | **UC-003** | Trace listing |
| `delete_trace()` | **UC-003** | Trace deletion (archive-first) |
| `get_trace_count()` | **UC-003** | Trace count |
| `cleanup_old_traces()` | **UC-003** | Archive + delete old traces |
| `get_trace_by_root_hash()` | **UC-017** | Deterministic replay: lookup by root hash |
| `check_idempotency_key()` | **UC-017** | Deterministic replay: idempotency check |

---

## SPLIT-8: `trace_store.py` -> UC-017 | UC-032

**Path:** `app/hoc/cus/logs/L6_drivers/trace_store.py`
**Type:** L6 Driver (abstract base + SQLite/InMemory implementations)

| Method | UC | Rationale |
|--------|-----|-----------|
| `start_trace()` | **UC-017** | Local replay: trace start |
| `record_step()` | **UC-017** | Local replay: record step |
| `complete_trace()` | **UC-017** | Local replay: complete |
| `get_trace()` | **UC-017** | Local replay: retrieval |
| `list_traces()` | **UC-017** | Local replay: listing |
| `delete_trace()` | **UC-017** | Local replay: deletion |
| `get_trace_count()` | **UC-017** | Local replay: count |
| `cleanup_old_traces()` | **UC-017** | Local replay: cleanup |
| `search_traces()` | **UC-017** | Local replay: multi-filter search |
| `get_trace_by_root_hash()` | **UC-017** | Deterministic replay: root hash lookup |
| `find_matching_traces()` | **UC-032** | Replay verification: find traces with matching plan+seed |
| `update_trace_determinism()` | **UC-032** | Replay verification: update determinism fields post-finalization |

---

## Architecture Compliance

- All 8 SPLIT scripts remain in their current locations (no file moves).
- No new files created — partition is documented at operation granularity.
- L4 handlers serve multiple UCs via distinct registered operations (this is the intended HOC pattern).
- L5 engines and L6 drivers serve multiple UCs via distinct class methods.
- No operation straddles UC boundaries ambiguously — every method has a single primary UC.
