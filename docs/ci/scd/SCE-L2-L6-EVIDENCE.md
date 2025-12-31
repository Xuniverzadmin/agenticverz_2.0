# SCE Evidence: L2 to L6 Boundary

**Generated:** 2025-12-31T20:24:08.463180+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/api/cost_guard.py | backend/app/db.py | import | 39 |
| backend/app/api/cost_guard.py | backend/app/auth/console_auth.py | import | 29 |
| backend/app/api/customer_visibility.py | backend/app/middleware/tenancy.py | import | 30 |
| backend/app/api/guard.py | backend/app/utils/guard_cache.py | import | 49 |
| backend/app/api/guard.py | backend/app/models/tenant.py | import | 66 |
| backend/app/api/guard.py | backend/app/db.py | import | 55 |
| backend/app/api/guard.py | backend/app/models/killswitch.py | import | 56 |
| backend/app/api/guard.py | backend/app/auth/console_auth.py | import | 46 |
| backend/app/api/cost_intelligence.py | backend/app/db.py | import | 22 |
| backend/app/api/status_history.py | backend/app/db.py | import | 34 |
| backend/app/api/cost_ops.py | backend/app/db.py | import | 44 |
| backend/app/api/cost_ops.py | backend/app/auth/console_auth.py | import | 28 |
| backend/app/api/recovery.py | backend/app/middleware/rate_limit.py | import | 26 |
| backend/app/api/recovery.py | backend/app/metrics.py | import | 219 |
| backend/app/api/v1_proxy.py | backend/app/models/killswitch.py | import | 52 |
| backend/app/api/v1_proxy.py | backend/app/db.py | import | 51 |
| backend/app/api/v1_proxy.py | backend/app/models/tenant.py | import | 58 |
| backend/app/api/policy_layer.py | backend/app/db_async.py | import | 17 |
| backend/app/api/runtime.py | backend/app/auth/tenant_auth.py | import | 47 |
| backend/app/api/runtime.py | backend/app/middleware/rate_limit.py | import | 49 |
| backend/app/api/ops.py | backend/app/models/killswitch.py | import | 89 |
| backend/app/api/ops.py | backend/app/db.py | import | 86 |
| backend/app/api/ops.py | backend/app/auth/console_auth.py | import | 73 |
| backend/app/api/recovery_ingest.py | backend/app/middleware/rate_limit.py | import | 35 |
| backend/app/api/recovery_ingest.py | backend/app/metrics.py | import | 29 |
| backend/app/api/v1_killswitch.py | backend/app/auth/tenant_auth.py | import | 40 |
| backend/app/api/v1_killswitch.py | backend/app/models/tenant.py | import | 60 |
| backend/app/api/v1_killswitch.py | backend/app/db.py | import | 42 |
| backend/app/api/v1_killswitch.py | backend/app/models/killswitch.py | import | 43 |
| backend/app/api/policy.py | backend/app/auth/tenant_auth.py | import | 61 |
| backend/app/api/policy.py | backend/app/db_async.py | import | 63 |
| backend/app/api/policy.py | backend/app/db.py | import | 607 |
| backend/app/api/policy.py | backend/app/utils/rate_limiter.py | import | 290 |
| backend/app/api/discovery.py | backend/app/db.py | import | 59 |
| backend/app/api/founder_actions.py | backend/app/db.py | import | 44 |
| backend/app/api/founder_actions.py | backend/app/auth/console_auth.py | import | 35 |
| backend/app/api/integration.py | backend/app/db.py | import | 207 |
| backend/app/api/workers.py | backend/app/models/tenant.py | import | 54 |
| backend/app/api/workers.py | backend/app/db.py | import | 53 |
| backend/tests/api/test_policy_api.py | backend/app/db.py | import | 191 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/api/legacy_routes.py | consume | 1. Confusion when legacy paths silently fail | docstring: 1. Confusion when l |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/db.py | event_subscribe | function get_async_session_factory match | MEDIUM |
| backend/app/db.py | event_subscribe | call to get_async_session_factory matche | MEDIUM |
| backend/app/db.py | event_subscribe | call to session_factory matches signal p | MEDIUM |
| backend/app/db.py | object_construction | class ApprovalRequest looks like signal  | MEDIUM |
| backend/app/db.py | event_subscribe | function transition_status matches signa | MEDIUM |
| backend/app/db.py | return_signal | function returns dict with signal-like k | LOW |
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
| backend/app/db_async.py | event_subscribe | function async_session_context matches s | MEDIUM |
| backend/app/logging_config.py | event_subscribe | call to StreamHandler matches signal pat | MEDIUM |
| backend/app/logging_config.py | event_subscribe | call to addHandler matches signal patter | MEDIUM |
| backend/app/auth/console_auth.py | object_construction | class AuthAuditEvent looks like signal p | MEDIUM |
| backend/app/auth/console_auth.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/auth/rbac_middleware.py | dispatch_call | function dispatch matches signal pattern | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class TokenPayload looks like signal pay | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class MockRequest looks like signal payl | MEDIUM |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
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
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_batch matches signal pattern' observed | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to _send_webhook matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to _send_webhook matches signal pattern' obser | MEDIUM |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L8 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L6 imports from L4 but allowed imports are set() | MEDIUM |
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
| half_circuit | Signal 'call to loggingpublisher matches signal pattern' has | MEDIUM |
| half_circuit | Signal 'function test_emit_api_call matches signal pattern ' | MEDIUM |
| half_circuit | Signal 'boundary_crossing_observed' has emitter but no consu | MEDIUM |
| half_circuit | Signal 'function _create_notify_adjustment matches signal pa | MEDIUM |

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
