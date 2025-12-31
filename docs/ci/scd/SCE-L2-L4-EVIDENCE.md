# SCE Evidence: L2 to L4 Boundary

**Generated:** 2025-12-31T20:24:08.461132+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/api/cost_guard.py | backend/app/contracts/guard.py | import | 32 |
| backend/app/api/guard.py | backend/app/services/replay_determinism.py | import | 77 |
| backend/app/api/guard.py | backend/app/services/guard_write_service.py | import | 49 |
| backend/app/api/guard.py | backend/app/contracts/guard.py | import | 49 |
| backend/app/api/cost_intelligence.py | backend/app/services/cost_write_service.py | import | 31 |
| backend/app/api/cost_intelligence.py | backend/app/services/cost_anomaly_detector.py | import | 1102 |
| backend/app/api/cost_ops.py | backend/app/contracts/ops.py | import | 31 |
| backend/app/api/recovery.py | backend/app/services/recovery_write_service.py | import | 28 |
| backend/app/api/recovery.py | backend/app/services/recovery_matcher.py | import | 27 |
| backend/app/api/recovery.py | backend/app/services/recovery_rule_engine.py | import | 782 |
| backend/app/api/recovery.py | backend/app/services/scoped_execution.py | import | 883 |
| backend/app/api/runtime.py | backend/app/commands/runtime_command.py | import | 202 |
| backend/app/api/runtime.py | backend/app/auth/tier_gating.py | import | 48 |
| backend/app/api/runtime.py | backend/app/worker/simulate.py | import | 164 |
| backend/app/api/ops.py | backend/app/contracts/ops.py | import | 76 |
| backend/app/api/recovery_ingest.py | backend/app/services/recovery_write_service.py | import | 36 |
| backend/app/api/v1_killswitch.py | backend/app/auth/tier_gating.py | import | 41 |
| backend/app/api/v1_killswitch.py | backend/app/services/guard_write_service.py | import | 63 |
| backend/app/api/policy.py | backend/app/auth/rbac.py | import | 736 |
| backend/app/api/policy.py | backend/app/auth/tier_gating.py | import | 62 |
| backend/app/api/discovery.py | backend/app/discovery/ledger.py | import | 14 |
| backend/app/api/founder_actions.py | backend/app/contracts/ops.py | import | 36 |
| backend/app/api/founder_actions.py | backend/app/services/founder_action_write_service.py | import | 45 |
| backend/app/api/integration.py | backend/app/integrations/__init__.py | import | 169 |
| backend/app/api/integration.py | backend/app/integrations/events.py | import | 48 |
| backend/app/api/integration.py | backend/app/integrations/graduation_engine.py | import | 169 |
| backend/app/api/workers.py | backend/app/policy/engine.py | import | 55 |
| backend/app/api/workers.py | backend/app/contracts/decisions.py | import | 52 |
| backend/app/api/workers.py | backend/app/routing/care.py | import | 1152 |
| backend/app/api/workers.py | backend/app/services/worker_write_service_async.py | import | 56 |
| backend/app/api/workers.py | backend/app/services/recovery_matcher.py | import | 1170 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/api/legacy_routes.py | consume | 1. Confusion when legacy paths silently fail | docstring: 1. Confusion when l |
| backend/app/workflow/canonicalize.py | consume | List of event dictionaries | docstring: List of event dicti |
| backend/app/services/guard_write_service.py | consume | List of (event_type, description) tuples | docstring: List of (event_type |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/main.py | object_construction | class CreateAgentRequest looks like sign | MEDIUM |
| backend/app/main.py | object_construction | class CreateAgentResponse looks like sig | MEDIUM |
| backend/app/main.py | object_construction | class GoalRequest looks like signal payl | MEDIUM |
| backend/app/main.py | object_construction | class GoalResponse looks like signal pay | MEDIUM |
| backend/app/main.py | object_construction | class RunResponse looks like signal payl | MEDIUM |
| backend/app/main.py | object_construction | class MemoryResponse looks like signal p | MEDIUM |
| backend/app/main.py | object_construction | class ProvenanceResponse looks like sign | MEDIUM |
| backend/app/main.py | enqueue_call | function update_queue_depth matches sign | MEDIUM |
| backend/app/main.py | event_publish | call to get_publisher matches signal pat | HIGH |
| backend/app/main.py | enqueue_call | call to update_queue_depth matches signa | MEDIUM |
| backend/app/main.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/main.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/main.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/main.py | object_construction | class RetryRequest looks like signal pay | MEDIUM |
| backend/app/main.py | object_construction | class RetryResponse looks like signal pa | MEDIUM |
| backend/app/main.py | object_construction | class RerunRequest looks like signal pay | MEDIUM |
| backend/app/main.py | object_construction | class RerunResponse looks like signal pa | MEDIUM |
| backend/app/auth/shadow_audit.py | object_construction | class ShadowAuditEvent looks like signal | MEDIUM |
| backend/app/auth/shadow_audit.py | event_subscribe | function log_founder_isolation_check mat | MEDIUM |
| backend/app/auth/rbac_engine.py | event_subscribe | call to _db_session_factory matches sign | MEDIUM |
| backend/app/auth/rbac.py | enqueue_call | call to submit matches signal pattern | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/optimization/killswitch.py | object_construction | class KillSwitchEvent looks like signal  | MEDIUM |
| backend/app/optimization/killswitch.py | event_subscribe | function on_activate matches signal patt | MEDIUM |
| backend/app/api/predictions.py | object_construction | class PredictionSummaryResponse looks li | MEDIUM |
| backend/app/api/predictions.py | object_construction | class PredictionListResponse looks like  | MEDIUM |
| backend/app/api/predictions.py | object_construction | class PredictionDetailResponse looks lik | MEDIUM |
| backend/app/api/predictions.py | event_subscribe | function get_prediction_stats matches si | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class OAuthLoginRequest looks like signa | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class OAuthLoginResponse looks like sign | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class EmailSignupRequest looks like sign | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class EmailSignupResponse looks like sig | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class EmailVerifyRequest looks like sign | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class AuthResponse looks like signal pay | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class RefreshRequest looks like signal p | MEDIUM |
| backend/app/api/onboarding.py | object_construction | class LogoutRequest looks like signal pa | MEDIUM |
| backend/app/api/onboarding.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/api/onboarding.py | event_subscribe | call to get_authorization_url matches si | MEDIUM |
| backend/app/api/onboarding.py | event_subscribe | call to get_authorization_url matches si | MEDIUM |
| backend/app/api/onboarding.py | event_subscribe | call to get_email_verification_service m | MEDIUM |
| backend/app/api/onboarding.py | dispatch_call | call to send_otp matches signal pattern | HIGH |
| backend/app/api/onboarding.py | event_subscribe | call to get_email_verification_service m | MEDIUM |
| backend/app/api/costsim.py | object_construction | class SimulateRequest looks like signal  | MEDIUM |
| backend/app/api/costsim.py | object_construction | class V2SimulationResponse looks like si | MEDIUM |
| backend/app/api/costsim.py | object_construction | class ComparisonResponse looks like sign | MEDIUM |
| backend/app/api/costsim.py | object_construction | class SandboxSimulateResponse looks like | MEDIUM |
| backend/app/api/costsim.py | object_construction | class SandboxStatusResponse looks like s | MEDIUM |
| backend/app/api/costsim.py | object_construction | class DivergenceReportResponse looks lik | MEDIUM |
| backend/app/api/costsim.py | object_construction | class CanaryRunResponse looks like signa | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to get_publisher matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to send_otp matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to _send_webhook matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to _send_webhook matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to _check_and_emit_cost_advisory matches signa | HIGH |
| observed_not_declared | Pattern 'call to emit_policy_precheck_decision matches signa | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit_policy_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _check_and_block_async_send matches signal  | MEDIUM |
| observed_not_declared | Pattern 'call to emit_routing_decision matches signal patter | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to _emit_sync_impl matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to _emit_sync_impl matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to IntegrationDispatcher matches signal patter | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to _create_notify_adjustment matches signal pa | MEDIUM |
| observed_not_declared | Pattern 'call to _emit_metrics matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L8 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| half_circuit | Signal 'call to emit_budget_enforcement_decision matches sig | MEDIUM |
| half_circuit | Signal 'function emit_session_idle_timeout matches signal pa | MEDIUM |
| half_circuit | Signal 'function send_alert matches signal pattern 'send'' h | MEDIUM |
| half_circuit | Signal 'function send_one matches signal pattern 'send'' has | MEDIUM |
| half_circuit | Signal 'function emit_batch matches signal pattern 'emit'' h | MEDIUM |
| half_circuit | Signal 'call to integrationdispatcher matches signal pattern | MEDIUM |
| half_circuit | Signal 'call to _send_alert_disable matches signal pattern'  | MEDIUM |
| half_circuit | Signal 'call to eventemitter matches signal pattern' has emi | MEDIUM |
| half_circuit | Signal 'call to emailsendinput matches signal pattern' has e | MEDIUM |
| half_circuit | Signal 'function emit_session_ended matches signal pattern ' | MEDIUM |
| half_circuit | Signal 'function test_r2_emits_recovery_suggested matches si | MEDIUM |
| half_circuit | Signal 'function test_emit_single_event matches signal patte | MEDIUM |
| half_circuit | Signal 'function emit_freeze matches signal pattern 'emit''  | MEDIUM |
| half_circuit | Signal 'function test_get_publisher_returns_logging_by_defau | MEDIUM |
| half_circuit | Signal 'function send_otp matches signal pattern 'send'' has | MEDIUM |
| half_circuit | Signal 'function reset_publisher matches signal pattern 'pub | MEDIUM |
| half_circuit | Signal 'call to emit_llm_call matches signal pattern' has em | MEDIUM |
| half_circuit | Signal 'function emit_llm_call matches signal pattern 'emit' | MEDIUM |
| half_circuit | Signal 'call to helper_emit_care_decision matches signal pat | MEDIUM |
| half_circuit | Signal 'function emit_feedback matches signal pattern 'emit' | MEDIUM |
| half_circuit | Signal 'call to webhooksendskill matches signal pattern' has | MEDIUM |
| half_circuit | Signal 'function _emit matches signal pattern 'emit'' has em | MEDIUM |
| half_circuit | Signal 'call to record_alert_send_failure matches signal pat | MEDIUM |
| half_circuit | Signal ' boundary_crossing_observed' has emitter but no cons | MEDIUM |
| half_circuit | Signal 'call to emit_recovery_decision matches signal patter | MEDIUM |
| half_circuit | Signal 'call to dispatch matches signal pattern' has emitter | MEDIUM |
| half_circuit | Signal 'function emit_incident_viewed matches signal pattern | MEDIUM |
| half_circuit | Signal 'function emit_all matches signal pattern 'emit'' has | MEDIUM |
| half_circuit | Signal 'function emit_care_optimization_decision matches sig | MEDIUM |
| half_circuit | Signal 'function test_emission_rule_strict_failure_emits mat | MEDIUM |
| half_circuit | Signal 'function emit_export_started matches signal pattern  | MEDIUM |
| half_circuit | Signal 'function has_resend matches signal pattern 'send'' h | MEDIUM |
| half_circuit | Signal 'function dispatcher_config matches signal pattern 'd | MEDIUM |
| half_circuit | Signal 'function emit_replay_started matches signal pattern  | MEDIUM |
| half_circuit | Signal 'function _send_alert matches signal pattern 'send''  | MEDIUM |
| half_circuit | Signal 'call to emit_recovery_evaluation_decision matches si | MEDIUM |
| half_circuit | Signal 'function emit_routing_decision matches signal patter | MEDIUM |
| half_circuit | Signal 'function test_invariant_every_failure_emits_decision | MEDIUM |

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
