# SCE Evidence: L7 to L3 Boundary

**Generated:** 2025-12-31T20:24:08.471398+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| scripts/ops/runtime_smoke.py | backend/app/skills/adapters/openai_adapter.py | import | 271 |
| scripts/ops/runtime_smoke.py | backend/app/skills/adapters/metrics.py | import | 285 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| scripts/ops/canary/canary_runner.py | consume | - Partial writes (atomic rename) | docstring: - Partial writes (a |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/cli.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/auth/oauth_providers.py | event_subscribe | function get_authorization_url matches s | MEDIUM |
| backend/app/auth/oauth_providers.py | event_subscribe | function get_authorization_url matches s | MEDIUM |
| backend/app/planners/anthropic_adapter.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/services/evidence_report.py | event_subscribe | call to _build_decision_timeline matches | MEDIUM |
| backend/app/services/evidence_report.py | event_subscribe | call to _build_prevention_proof matches  | MEDIUM |
| backend/app/services/evidence_report.py | event_subscribe | function _build_decision_timeline matche | MEDIUM |
| backend/app/services/evidence_report.py | event_subscribe | function _build_prevention_proof matches | MEDIUM |
| backend/app/services/certificate.py | object_construction | class CertificatePayload looks like sign | MEDIUM |
| backend/app/services/certificate.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/services/policy_proposal.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/services/policy_proposal.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/services/policy_proposal.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/services/email_verification.py | dispatch_call | function send_otp matches signal pattern | MEDIUM |
| backend/app/services/email_verification.py | dispatch_call | call to _send_otp_email matches signal p | HIGH |
| backend/app/services/email_verification.py | dispatch_call | function _send_otp_email matches signal  | MEDIUM |
| backend/app/services/email_verification.py | event_subscribe | function get_email_verification_service  | MEDIUM |
| backend/app/services/prediction.py | event_publish | function emit_prediction matches signal  | MEDIUM |
| backend/app/services/prediction.py | event_subscribe | function run_prediction_cycle matches si | MEDIUM |
| backend/app/services/prediction.py | event_publish | call to emit_prediction matches signal p | HIGH |
| backend/app/services/prediction.py | event_publish | call to emit_prediction matches signal p | HIGH |
| backend/app/services/prediction.py | event_subscribe | function get_prediction_summary matches  | MEDIUM |
| backend/app/events/nats_adapter.py | event_publish | function publish matches signal pattern  | MEDIUM |
| backend/app/events/nats_adapter.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/events/publisher.py | event_publish | function publish matches signal pattern  | MEDIUM |
| backend/app/events/publisher.py | event_publish | function publish matches signal pattern  | MEDIUM |
| backend/app/events/publisher.py | event_publish | function get_publisher matches signal pa | MEDIUM |
| backend/app/events/publisher.py | event_publish | call to RedisPublisher matches signal pa | HIGH |
| backend/app/events/publisher.py | event_publish | call to LoggingPublisher matches signal  | HIGH |
| backend/app/events/publisher.py | event_publish | function reset_publisher matches signal  | MEDIUM |
| backend/app/events/redis_publisher.py | event_publish | function publish matches signal pattern  | MEDIUM |
| backend/app/events/redis_publisher.py | event_publish | call to publish matches signal pattern | HIGH |
| scripts/ops/m26_real_cost_test.py | event_subscribe | function test_projection_honesty matches | MEDIUM |
| scripts/ops/m26_real_cost_test.py | event_subscribe | call to test_projection_honesty matches  | MEDIUM |
| scripts/ops/runtime_smoke.py | return_signal | function returns dict with signal-like k | LOW |
| scripts/ops/runtime_smoke.py | return_signal | function returns dict with signal-like k | LOW |
| scripts/ops/runtime_smoke.py | return_signal | function returns dict with signal-like k | LOW |
| scripts/ops/runtime_smoke.py | dispatch_call | call to WebhookSendSkill matches signal  | HIGH |
| scripts/ops/runtime_smoke.py | event_subscribe | function test_execution_context matches  | MEDIUM |
| scripts/ops/m25_trigger_real_incident.py | event_subscribe | call to trigger_integration_loop matches | MEDIUM |
| scripts/ops/visibility_validator.py | event_subscribe | function check_promotion_legitimacy matc | MEDIUM |
| scripts/ops/visibility_validator.py | event_subscribe | call to check_promotion_legitimacy match | MEDIUM |
| scripts/ops/scenario_test_matrix.py | event_subscribe | function scenario_a4_neon_db matches sig | MEDIUM |
| scripts/ops/m25_gate_passage_demo.py | event_subscribe | function get_graduation_status matches s | MEDIUM |
| scripts/ops/m25_gate_passage_demo.py | return_signal | function returns dict with signal-like k | LOW |
| scripts/ops/m25_gate_passage_demo.py | return_signal | function returns dict with signal-like k | LOW |
| scripts/ops/m25_gate_passage_demo.py | event_subscribe | function get_simulation_counts matches s | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to _send_otp_email matches signal pattern' obs | MEDIUM |
| observed_not_declared | Pattern 'call to emit_prediction matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit_prediction matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to RedisPublisher matches signal pattern' obse | HIGH |
| observed_not_declared | Pattern 'call to LoggingPublisher matches signal pattern' ob | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to WebhookSendSkill matches signal pattern' ob | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to ResendEmailer matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_alert matches signal pattern' observed | MEDIUM |
| observed_not_declared | Pattern 'call to send_alert matches signal pattern' observed | MEDIUM |
| observed_not_declared | Pattern 'call to send_alert_with_retry matches signal patter | MEDIUM |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L3 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L3 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L5 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L5 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
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

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
