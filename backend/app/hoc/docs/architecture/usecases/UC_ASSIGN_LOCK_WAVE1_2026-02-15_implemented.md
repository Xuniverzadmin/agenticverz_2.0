# UC ASSIGN Lock Wave-1 (2026-02-15)

**Status:** IMPLEMENTED
**Source:** Iteration-3 Decision Table (`HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv`)
**Scope:** 7 ASSIGN rows locked into canonical linkage with operation-level evidence.

---

## Proof Table

| # | Script | Assigned UC | Operation(s) | Handler Ref | Test Refs | Gate Output |
|---|--------|-------------|-------------|-------------|-----------|-------------|
| 1 | `activity/L5_engines/signal_feedback_engine.py` | UC-006 | `activity.signal_feedback` (ack/suppress/reopen/evaluate_expired/query_feedback) | `activity_handler.py:ActivitySignalFeedbackHandler` | `test_uc018_uc032_expansion.py::TestUC006`, storage verifier `storage.feedback_driver.*` | cross_domain_validator: CLEAN |
| 2 | `activity/L6_drivers/signal_feedback_driver.py` | UC-006 | L6 persistence: `insert_feedback`, `query_feedback`, `update_feedback_state`, `list_active_suppressions`, `mark_expired_as_evaluated` | Called by `signal_feedback_engine.py` (L5) | storage verifier `storage.feedback_driver.*` PASS | cross_domain_validator: CLEAN |
| 3 | `analytics/L6_drivers/analytics_artifacts_driver.py` | UC-008 | L6 persistence: `save_artifact` (UPSERT), `get_artifact`, `list_artifacts` on `analytics_artifacts` table | Called by `analytics_handler.py:AnalyticsArtifactsHandler` | storage verifier `storage.analytics_artifacts_driver.*` PASS (7 checks) | cross_domain_validator: CLEAN |
| 4 | `controls/L6_drivers/evaluation_evidence_driver.py` | UC-004 | L6 persistence: `record_evidence`, `query_evidence` on `controls_evaluation_evidence` table | Called by `controls_handler.py:ControlsEvaluationEvidenceHandler` | storage verifier `storage.eval_evidence_driver.*` PASS (6 checks) | cross_domain_validator: CLEAN |
| 5 | `hoc_spine/authority/onboarding_policy.py` | UC-002 | Endpoint-to-state gating (`get_required_state`), 4-condition activation predicate (`check_activation_predicate`) | Consumed by `onboarding_handler.py` | `test_activation_predicate_authority.py` (11 tests), `test_api_key_surface_policy.py` (11 tests) | CI check 35: PASS |
| 6 | `hoc_spine/orchestrator/handlers/onboarding_handler.py` | UC-002 | `account.onboarding.query`, `account.onboarding.advance` | Self (L4 handler) | `test_activation_predicate_authority.py`, `test_event_schema_contract.py`, `uc001_uc002_validation.py` (19/19) | CI check 35: PASS |
| 7 | `integrations/L6_drivers/connector_registry_driver.py` | UC-002 | Runtime connector cache (CACHE ONLY — not activation authority). `register`, `get`, `list`, `delete`, `health_check` | Consumed by `onboarding_handler.py` (runtime only) | `test_activation_predicate_authority.py` (9 tests — proves cache NOT used for activation) | CI check 35: PASS |

---

## Linkage Changes Applied

All 7 rows now have explicit canonical anchors in `HOC_USECASE_CODE_LINKAGE.md`:

- **UC-002** (rows 5, 6, 7): Added `onboarding_policy.py`, `onboarding_handler.py`, `connector_registry_driver.py` as Iteration-3 ASSIGN anchors with operation evidence.
- **UC-004** (row 4): Added `evaluation_evidence_driver.py` as Iteration-3 ASSIGN anchor with `record_evidence`/`query_evidence` operations.
- **UC-006** (rows 1, 2): Added `signal_feedback_engine.py` and `signal_feedback_driver.py` as Iteration-3 ASSIGN anchors with full feedback lifecycle operations.
- **UC-008** (row 3): Added `analytics_artifacts_driver.py` as Iteration-3 ASSIGN anchor with UPSERT/query/list operations.

## Architecture Compliance

- All 7 scripts respect L2.1 -> L2 -> L4 -> L5 -> L6 -> L7 topology.
- No L2 -> L5/L6 direct calls introduced.
- L5 engines contain no DB/ORM imports at runtime.
- L6 drivers contain no business conditionals.
- Transaction boundaries remain L4-owned.

## Note on UC-006 vs UC-010

The `signal_feedback_engine.py` and `signal_feedback_driver.py` files declare `UC-010` in their layer headers but are assigned to `UC-006` by the Iteration-3 decision table. This is correct because:
- UC-006 (Activity Stream + Feedback) covers the signal feedback write lifecycle (ack/suppress/reopen).
- UC-010 (Activity Feedback Lifecycle) covers the broader feedback state machine including TTL/expiry evaluation.
- Both UCs share these files; the ASSIGN decision anchors them primarily to UC-006 where the core operations live.
- The signal_feedback operation (`activity.signal_feedback`) is registered in `activity_handler.py` which SPLIT maps to UC-001|UC-006|UC-010.
