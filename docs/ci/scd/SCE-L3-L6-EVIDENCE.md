# SCE Evidence: L3 to L6 Boundary

**Generated:** 2025-12-31T20:24:08.465746+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/services/policy_proposal.py | backend/app/models/policy.py | import | 31 |
| backend/app/services/policy_proposal.py | backend/app/db.py | import | 29 |
| backend/app/services/policy_proposal.py | backend/app/models/feedback.py | import | 29 |
| backend/app/services/prediction.py | backend/app/models/tenant.py | import | 32 |
| backend/app/services/prediction.py | backend/app/models/prediction.py | import | 31 |
| backend/app/services/prediction.py | backend/app/db.py | import | 29 |
| backend/app/services/prediction.py | backend/app/models/feedback.py | import | 29 |
| backend/app/costsim/v2_adapter.py | backend/app/costsim/models.py | import | 38 |
| backend/app/skills/adapters/metrics.py | backend/app/metrics.py | import | 34 |

---

## Declared Signals (from metadata)

*No declared signals found.*

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/db.py | event_subscribe | function get_async_session_factory match | MEDIUM |
| backend/app/db.py | event_subscribe | call to get_async_session_factory matche | MEDIUM |
| backend/app/db.py | event_subscribe | call to session_factory matches signal p | MEDIUM |
| backend/app/db.py | object_construction | class ApprovalRequest looks like signal  | MEDIUM |
| backend/app/db.py | event_subscribe | function transition_status matches signa | MEDIUM |
| backend/app/db.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/db_async.py | event_subscribe | function async_session_context matches s | MEDIUM |
| backend/app/logging_config.py | event_subscribe | call to StreamHandler matches signal pat | MEDIUM |
| backend/app/logging_config.py | event_subscribe | call to addHandler matches signal patter | MEDIUM |
| backend/app/auth/console_auth.py | object_construction | class AuthAuditEvent looks like signal p | MEDIUM |
| backend/app/auth/console_auth.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/auth/oauth_providers.py | event_subscribe | function get_authorization_url matches s | MEDIUM |
| backend/app/auth/oauth_providers.py | event_subscribe | function get_authorization_url matches s | MEDIUM |
| backend/app/auth/rbac_middleware.py | dispatch_call | function dispatch matches signal pattern | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class TokenPayload looks like signal pay | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class MockRequest looks like signal payl | MEDIUM |
| backend/app/planners/anthropic_adapter.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/logging_context.py | event_subscribe | function get_correlation_id matches sign | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | function set_correlation_id matches sign | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to get_correlation_id matches signa | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to removeHandler matches signal pat | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to StreamHandler matches signal pat | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to addHandler matches signal patter | MEDIUM |
| backend/app/workflow/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/health.py | object_construction | class MockResponse looks like signal pay | MEDIUM |
| backend/app/workflow/metrics.py | event_subscribe | function record_cost_simulation_drift ma | MEDIUM |
| backend/app/models/tenant.py | event_subscribe | function retention_days matches signal p | MEDIUM |
| backend/app/models/governance.py | object_construction | class GovernanceSignal looks like signal | MEDIUM |
| backend/app/models/governance.py | object_construction | class GovernanceSignalResponse looks lik | MEDIUM |
| backend/app/models/costsim_cb.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/models/costsim_cb.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/models/external_response.py | object_construction | class ExternalResponse looks like signal | MEDIUM |
| backend/app/models/external_response.py | object_construction | class InterpretedResponse looks like sig | MEDIUM |
| backend/app/models/killswitch.py | object_construction | class IncidentEvent looks like signal pa | MEDIUM |
| backend/app/models/killswitch.py | object_construction | class ReplayRequest looks like signal pa | MEDIUM |
| backend/app/models/killswitch.py | object_construction | class DemoSimulationRequest looks like s | MEDIUM |
| backend/app/models/feedback.py | object_construction | class PatternFeedbackResponse looks like | MEDIUM |
| backend/app/models/prediction.py | object_construction | class PredictionEvent looks like signal  | MEDIUM |
| backend/app/models/prediction.py | object_construction | class PredictionEventResponse looks like | MEDIUM |
| backend/app/models/policy.py | object_construction | class PolicyProposalResponse looks like  | MEDIUM |
| backend/app/models/policy.py | object_construction | class PolicyApprovalRequest looks like s | MEDIUM |
| backend/app/models/policy.py | object_construction | class PolicyVersionResponse looks like s | MEDIUM |
| backend/app/learning/tables.py | exception_signal | raises LearningBoundaryViolation which l | MEDIUM |
| backend/app/utils/canonical_json.py | event_subscribe | function canonical_json_bytes matches si | MEDIUM |
| backend/app/utils/canonical_json.py | event_subscribe | call to canonical_json_bytes matches sig | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _send_otp_email matches signal pattern' obs | MEDIUM |
| observed_not_declared | Pattern 'call to emit_prediction matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit_prediction matches signal pattern' obs | HIGH |
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
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to RedisPublisher matches signal pattern' obse | HIGH |
| observed_not_declared | Pattern 'call to LoggingPublisher matches signal pattern' ob | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
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
| half_circuit | Signal 'function test_send_message matches signal pattern 's | MEDIUM |
| half_circuit | Signal 'call to poll_and_dispatch matches signal pattern' ha | MEDIUM |
| half_circuit | Signal 'function publish matches signal pattern 'publish'' h | MEDIUM |
| half_circuit | Signal 'call to _emit_metrics matches signal pattern' has em | MEDIUM |
| half_circuit | Signal 'function emit_budget_decision matches signal pattern | MEDIUM |
| half_circuit | Signal 'call to publish matches signal pattern' has emitter  | MEDIUM |
| half_circuit | Signal 'function _send_otp_email matches signal pattern 'sen | MEDIUM |

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
