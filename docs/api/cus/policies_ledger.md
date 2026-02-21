# CUS Domain Ledger: policies

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 268
**Unique method+path:** 268

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/alerts/history | list_history | List alert history (GAP-111). |
| GET | /hoc/api/cus/alerts/history/{event_id} | get_event | Get a specific alert event. |
| POST | /hoc/api/cus/alerts/history/{event_id}/acknowledge | acknowledge_event | Acknowledge an alert event. |
| POST | /hoc/api/cus/alerts/history/{event_id}/resolve | resolve_event | Resolve an alert event. |
| GET | /hoc/api/cus/alerts/routes | list_routes | List alert routes. |
| POST | /hoc/api/cus/alerts/routes | create_route | Create an alert route (GAP-124). |
| DELETE | /hoc/api/cus/alerts/routes/{route_id} | delete_route | Delete an alert route. |
| GET | /hoc/api/cus/alerts/routes/{route_id} | get_route | Get a specific alert route. |
| GET | /hoc/api/cus/alerts/rules | list_rules | List alert rules. |
| POST | /hoc/api/cus/alerts/rules | create_rule | Create an alert rule (GAP-110). |
| DELETE | /hoc/api/cus/alerts/rules/{rule_id} | delete_rule | Delete an alert rule. |
| GET | /hoc/api/cus/alerts/rules/{rule_id} | get_rule | Get a specific alert rule. |
| PUT | /hoc/api/cus/alerts/rules/{rule_id} | update_rule | Update an alert rule. |
| GET | /hoc/api/cus/compliance/reports | list_reports | List compliance reports. |
| GET | /hoc/api/cus/compliance/reports/{report_id} | get_report | Get a specific compliance report. |
| GET | /hoc/api/cus/compliance/rules | list_rules | List compliance rules. |
| GET | /hoc/api/cus/compliance/rules/{rule_id} | get_rule | Get a specific compliance rule. |
| GET | /hoc/api/cus/compliance/status | get_compliance_status | Get overall compliance status. |
| POST | /hoc/api/cus/compliance/verify | verify_compliance | Run compliance verification (GAP-103). |
| POST | /hoc/api/cus/customer/acknowledge | acknowledge_declaration | Acknowledge PRE-RUN declaration. |
| GET | /hoc/api/cus/customer/declaration/{declaration_id} | get_declaration | Retrieve a previously created PRE-RUN declaration. |
| GET | /hoc/api/cus/customer/outcome/{run_id} | get_outcome_reconciliation | Get outcome reconciliation after execution. |
| POST | /hoc/api/cus/customer/pre-run | get_pre_run_declaration | Get PRE-RUN declaration before execution. |
| GET | /hoc/api/cus/detection/anomalies | list_anomalies | List anomalies for the tenant. |
| GET | /hoc/api/cus/detection/anomalies/{anomaly_id} | get_anomaly | Get a specific anomaly by ID. |
| POST | /hoc/api/cus/detection/anomalies/{anomaly_id}/acknowledge | acknowledge_anomaly | Acknowledge an anomaly. |
| POST | /hoc/api/cus/detection/anomalies/{anomaly_id}/resolve | resolve_anomaly | Resolve an anomaly. |
| POST | /hoc/api/cus/detection/run | run_detection | Run anomaly detection on demand (GAP-102). |
| GET | /hoc/api/cus/detection/status | get_detection_status | Get detection engine status. |
| POST | /hoc/api/cus/enforcement/batch | batch_enforcement_check | Check enforcement for multiple requests at once. |
| POST | /hoc/api/cus/enforcement/check | check_enforcement | Check enforcement policy before making an LLM call. |
| GET | /hoc/api/cus/enforcement/status | get_enforcement_status | Get current enforcement status for an integration. |
| GET | /hoc/api/cus/evidence/chains | list_chains | List evidence chains. |
| POST | /hoc/api/cus/evidence/chains | create_chain | Create an evidence chain (GAP-104). |
| GET | /hoc/api/cus/evidence/chains/{chain_id} | get_chain | Get a specific evidence chain. |
| POST | /hoc/api/cus/evidence/chains/{chain_id}/evidence | add_evidence | Add evidence to a chain. |
| GET | /hoc/api/cus/evidence/chains/{chain_id}/verify | verify_chain | Verify chain integrity. |
| POST | /hoc/api/cus/evidence/export | create_export | Create evidence export (GAP-105). |
| GET | /hoc/api/cus/evidence/exports | list_exports | List evidence exports. |
| GET | /hoc/api/cus/evidence/exports/{export_id} | get_export | Get export status. |
| GET | /hoc/api/cus/governance/boot-status | get_boot_status | Get SPINE component health status (GAP-095). |
| GET | /hoc/api/cus/governance/conflicts | list_conflicts | List policy conflicts. |
| POST | /hoc/api/cus/governance/kill-switch | toggle_kill_switch | Toggle the governance kill switch (GAP-090). |
| POST | /hoc/api/cus/governance/mode | set_governance_mode | Set governance mode (GAP-091). |
| POST | /hoc/api/cus/governance/resolve-conflict | resolve_conflict | Manually resolve a policy conflict (GAP-092). |
| GET | /hoc/api/cus/governance/state | get_governance_state | Get current governance state. |
| GET | /hoc/api/cus/guard/costs/explained | get_cost_explained | GET /guard/costs/explained |
| GET | /hoc/api/cus/guard/costs/incidents | get_cost_incidents | GET /guard/costs/incidents |
| GET | /hoc/api/cus/guard/costs/summary | get_cost_summary | GET /guard/costs/summary |
| GET | /hoc/api/cus/guard/incidents | list_incidents | List incidents - "What did you stop for me?" |
| POST | /hoc/api/cus/guard/incidents/search | search_incidents | Search incidents with filters - M23 component map spec. |
| GET | /hoc/api/cus/guard/incidents/{incident_id} | get_incident_detail | Get incident detail with timeline. |
| POST | /hoc/api/cus/guard/incidents/{incident_id}/acknowledge | acknowledge_incident | Acknowledge an incident. |
| POST | /hoc/api/cus/guard/incidents/{incident_id}/export | export_incident_evidence | Export incident as a legal-grade PDF evidence report. |
| GET | /hoc/api/cus/guard/incidents/{incident_id}/narrative | get_customer_incident_narrative | GET /guard/incidents/{id}/narrative |
| POST | /hoc/api/cus/guard/incidents/{incident_id}/resolve | resolve_incident | Resolve an incident. |
| GET | /hoc/api/cus/guard/incidents/{incident_id}/timeline | get_decision_timeline | Get decision timeline - M23 component map spec. |
| GET | /hoc/api/cus/guard/keys | list_api_keys | List API keys with status. |
| POST | /hoc/api/cus/guard/keys/{key_id}/freeze | freeze_api_key | Freeze an API key. |
| POST | /hoc/api/cus/guard/keys/{key_id}/unfreeze | unfreeze_api_key | Unfreeze an API key. |
| POST | /hoc/api/cus/guard/killswitch/activate | activate_killswitch | Stop all traffic - Emergency kill switch. |
| POST | /hoc/api/cus/guard/killswitch/deactivate | deactivate_killswitch | Resume traffic - Deactivate kill switch. |
| GET | /hoc/api/cus/guard/logs | list_logs | List execution logs for customer. |
| GET | /hoc/api/cus/guard/logs/export | export_logs | Export logs for customer. |
| GET | /hoc/api/cus/guard/logs/{log_id} | get_log | Get log detail with execution steps. |
| POST | /hoc/api/cus/guard/onboarding/verify | onboarding_verify | REAL safety verification for onboarding. |
| GET | /hoc/api/cus/guard/policies | get_policy_constraints | Get policy constraints for customer. |
| GET | /hoc/api/cus/guard/policies/guardrails/{guardrail_id} | get_guardrail_detail | Get guardrail detail. |
| POST | /hoc/api/cus/guard/replay/{call_id} | replay_call | Replay a call - Trust builder. |
| GET | /hoc/api/cus/guard/settings | get_settings | Get read-only settings. |
| GET | /hoc/api/cus/guard/snapshot/today | get_today_snapshot | Get today's metrics - "What did it cost/save me?" |
| GET | /hoc/api/cus/guard/status | get_guard_status | Get protection status - "Am I safe right now?" |
| GET | /hoc/api/cus/integration/checkpoints | list_pending_checkpoints | List all pending human checkpoints for the tenant. |
| GET | /hoc/api/cus/integration/checkpoints/{checkpoint_id} | get_checkpoint | Get details of a specific checkpoint. |
| POST | /hoc/api/cus/integration/checkpoints/{checkpoint_id}/resolve | resolve_checkpoint | Resolve a pending checkpoint. |
| GET | /hoc/api/cus/integration/graduation | get_graduation_status | Get M25 graduation status (HARDENED). |
| POST | /hoc/api/cus/integration/graduation/re-evaluate | trigger_graduation_re_evaluation | Trigger a re-evaluation of graduation status. |
| POST | /hoc/api/cus/integration/graduation/record-view | record_timeline_view | Record a REAL timeline view for Gate 3 graduation. |
| POST | /hoc/api/cus/integration/graduation/simulate/prevention | simulate_prevention | Simulate a prevention event for demo/testing purposes. |
| POST | /hoc/api/cus/integration/graduation/simulate/regret | simulate_regret | Simulate a regret event for demo/testing purposes. |
| POST | /hoc/api/cus/integration/graduation/simulate/timeline-view | simulate_timeline_view | Simulate viewing a prevention timeline for Gate 3. |
| GET | /hoc/api/cus/integration/loop/{incident_id} | get_loop_status | Get current loop status for an incident. |
| GET | /hoc/api/cus/integration/loop/{incident_id}/narrative | get_loop_narrative | Get narrative artifacts for an incident loop. |
| POST | /hoc/api/cus/integration/loop/{incident_id}/retry | retry_loop_stage | Retry a failed loop stage. |
| POST | /hoc/api/cus/integration/loop/{incident_id}/revert | revert_loop | Revert all changes made by a loop. |
| GET | /hoc/api/cus/integration/loop/{incident_id}/stages | get_loop_stages | Get detailed stage information for a loop. |
| GET | /hoc/api/cus/integration/loop/{incident_id}/stream | stream_loop_status | SSE endpoint for live loop status updates. |
| GET | /hoc/api/cus/integration/stats | get_integration_stats | Get integration loop statistics for the specified period. |
| GET | /hoc/api/cus/integration/timeline/{incident_id} | get_prevention_timeline | Get the prevention timeline for an incident. |
| GET | /hoc/api/cus/lifecycle/agents | list_agents | List agents (GAP-131). |
| POST | /hoc/api/cus/lifecycle/agents | create_agent | Create a new agent (GAP-131). |
| GET | /hoc/api/cus/lifecycle/agents/{agent_id} | get_agent | Get a specific agent (GAP-131). |
| POST | /hoc/api/cus/lifecycle/agents/{agent_id}/start | start_agent | Start an agent (GAP-132). |
| POST | /hoc/api/cus/lifecycle/agents/{agent_id}/stop | stop_agent | Stop an agent (GAP-132). |
| POST | /hoc/api/cus/lifecycle/agents/{agent_id}/terminate | terminate_agent | Terminate an agent (GAP-132). |
| GET | /hoc/api/cus/lifecycle/runs | list_runs | List runs (GAP-133). |
| POST | /hoc/api/cus/lifecycle/runs | create_run | Create a new run (GAP-133). |
| GET | /hoc/api/cus/lifecycle/runs/{run_id} | get_run | Get a specific run (GAP-133). |
| POST | /hoc/api/cus/lifecycle/runs/{run_id}/cancel | cancel_run | Cancel a run (GAP-136). |
| POST | /hoc/api/cus/lifecycle/runs/{run_id}/pause | pause_run | Pause a run (GAP-134). |
| POST | /hoc/api/cus/lifecycle/runs/{run_id}/resume | resume_run | Resume a paused run (GAP-135). |
| GET | /hoc/api/cus/lifecycle/summary | get_summary | Get lifecycle summary. |
| GET | /hoc/api/cus/limits/overrides | list_overrides | List overrides for the tenant. |
| POST | /hoc/api/cus/limits/overrides | create_override | Request a temporary limit override. |
| DELETE | /hoc/api/cus/limits/overrides/{override_id} | cancel_override | Cancel a pending or active override. |
| GET | /hoc/api/cus/limits/overrides/{override_id} | get_override | Get override by ID. |
| POST | /hoc/api/cus/limits/simulate | simulate_execution | Simulate an execution against all limits. |
| GET | /hoc/api/cus/monitors | list_monitors | List monitors. |
| POST | /hoc/api/cus/monitors | create_monitor | Create a monitor (GAP-121). |
| GET | /hoc/api/cus/monitors/status | get_status | Get overall monitoring status (GAP-120). |
| DELETE | /hoc/api/cus/monitors/{monitor_id} | delete_monitor | Delete a monitor. |
| GET | /hoc/api/cus/monitors/{monitor_id} | get_monitor | Get a specific monitor. |
| PUT | /hoc/api/cus/monitors/{monitor_id} | update_monitor | Update a monitor. |
| POST | /hoc/api/cus/monitors/{monitor_id}/check | run_check | Run a health check (GAP-120). |
| GET | /hoc/api/cus/monitors/{monitor_id}/history | get_history | Get health check history. |
| GET | /hoc/api/cus/notifications | list_notifications | List notifications for the tenant. |
| POST | /hoc/api/cus/notifications | send_notification | Send a notification (GAP-109). |
| GET | /hoc/api/cus/notifications/channels | list_channels | List available notification channels. |
| GET | /hoc/api/cus/notifications/preferences | get_preferences | Get notification preferences for the current user. |
| PUT | /hoc/api/cus/notifications/preferences | update_preferences | Update notification preferences for the current user. |
| GET | /hoc/api/cus/notifications/{notification_id} | get_notification | Get a specific notification. |
| POST | /hoc/api/cus/notifications/{notification_id}/read | mark_as_read | Mark a notification as read. |
| GET | /hoc/api/cus/policies/budgets | list_budget_definitions | List budget definitions (THR-O2). Customer facade. |
| GET | /hoc/api/cus/policies/conflicts | list_policy_conflicts | Detect policy conflicts (DFT-O4). Uses PolicyConflictEngine  |
| GET | /hoc/api/cus/policies/dependencies | get_policy_dependencies | Get policy dependency graph (DFT-O5). Uses PolicyDependencyE |
| GET | /hoc/api/cus/policies/lessons | list_lessons | List lessons learned (O2). READ-ONLY customer facade. |
| GET | /hoc/api/cus/policies/lessons/stats | get_lesson_stats | Get lesson statistics (O1). READ-ONLY customer facade. |
| GET | /hoc/api/cus/policies/lessons/{lesson_id} | get_lesson_detail | Get lesson detail (O3). READ-ONLY customer facade. |
| GET | /hoc/api/cus/policies/limits | list_limits | List limits with unified query filters. READ-ONLY. |
| POST | /hoc/api/cus/policies/limits | create_limit | Create a new policy limit. |
| DELETE | /hoc/api/cus/policies/limits/{limit_id} | delete_limit | Soft-delete a policy limit. |
| GET | /hoc/api/cus/policies/limits/{limit_id} | get_limit_detail | Get limit detail (O3). Tenant isolation enforced. |
| PUT | /hoc/api/cus/policies/limits/{limit_id} | update_limit | Update an existing policy limit. |
| GET | /hoc/api/cus/policies/limits/{limit_id}/evidence | get_limit_evidence | Get limit evidence (O4). Preflight console only. |
| GET | /hoc/api/cus/policies/limits/{limit_id}/params | get_threshold_params | Get threshold parameters for a limit. |
| PUT | /hoc/api/cus/policies/limits/{limit_id}/params | set_threshold_params | Set threshold parameters for a limit. |
| GET | /hoc/api/cus/policies/list | list_policies_public |  |
| GET | /hoc/api/cus/policies/metrics | get_policy_metrics | Get policy metrics (ACT-O5). Customer facade. |
| GET | /hoc/api/cus/policies/requests | list_policy_requests | List pending policy requests (ACT-O3). Customer facade. |
| GET | /hoc/api/cus/policies/rules | list_policy_rules | List policy rules with unified query filters. READ-ONLY. |
| POST | /hoc/api/cus/policies/rules | create_rule | Create a new policy rule. |
| GET | /hoc/api/cus/policies/rules/{rule_id} | get_policy_rule_detail | Get policy rule detail (O3). Tenant isolation enforced. |
| PUT | /hoc/api/cus/policies/rules/{rule_id} | update_rule | Update an existing policy rule. |
| GET | /hoc/api/cus/policies/rules/{rule_id}/evidence | get_rule_evidence | Get rule evidence (O4). Preflight console only. |
| GET | /hoc/api/cus/policies/state | get_policy_state | Get policy layer state (ACT-O4). Customer facade. |
| GET | /hoc/api/cus/policies/violations | list_policy_violations | List policy violations (VIO-O1). Unified customer facade. |
| GET | /hoc/api/cus/policy-layer/conflicts | list_conflicts | List policy conflicts. |
| POST | /hoc/api/cus/policy-layer/conflicts/{conflict_id}/resolve | resolve_conflict | Resolve a policy conflict. |
| GET | /hoc/api/cus/policy-layer/cooldowns | list_active_cooldowns | List all active cooldowns. |
| DELETE | /hoc/api/cus/policy-layer/cooldowns/{agent_id} | clear_cooldowns | Clear cooldowns for an agent. |
| GET | /hoc/api/cus/policy-layer/dependencies | get_dependency_graph | Get the policy dependency graph. |
| POST | /hoc/api/cus/policy-layer/dependencies/add | add_dependency_with_dag_check | Add a policy dependency with DAG validation. |
| GET | /hoc/api/cus/policy-layer/dependencies/dag/validate | validate_dependency_dag | Validate that policy dependencies form a valid DAG. |
| GET | /hoc/api/cus/policy-layer/dependencies/evaluation-order | get_evaluation_order | Get the topological evaluation order for policies. |
| GET | /hoc/api/cus/policy-layer/ethical-constraints | list_ethical_constraints | List all ethical constraints. |
| POST | /hoc/api/cus/policy-layer/evaluate | evaluate_action | Evaluate a proposed action against all applicable policies. |
| POST | /hoc/api/cus/policy-layer/evaluate/batch | evaluate_batch | Evaluate multiple actions in a single call. |
| POST | /hoc/api/cus/policy-layer/evaluate/context-aware | evaluate_with_context | Context-aware policy evaluation (GAP 4). |
| GET | /hoc/api/cus/policy-layer/lessons | list_lessons | List lessons learned. |
| GET | /hoc/api/cus/policy-layer/lessons/stats | get_lesson_stats | Get lesson statistics for a tenant. |
| GET | /hoc/api/cus/policy-layer/lessons/{lesson_id} | get_lesson | Get a specific lesson by ID. |
| POST | /hoc/api/cus/policy-layer/lessons/{lesson_id}/convert | convert_lesson_to_draft | Convert a lesson to a draft policy proposal. |
| POST | /hoc/api/cus/policy-layer/lessons/{lesson_id}/defer | defer_lesson | Defer a lesson until a future date. |
| POST | /hoc/api/cus/policy-layer/lessons/{lesson_id}/dismiss | dismiss_lesson | Dismiss a lesson (mark as not actionable). |
| GET | /hoc/api/cus/policy-layer/metrics | get_policy_metrics | Get policy engine metrics for the specified time window. |
| POST | /hoc/api/cus/policy-layer/reload | reload_policies | Hot-reload policies from database. |
| GET | /hoc/api/cus/policy-layer/risk-ceilings | list_risk_ceilings | List all risk ceilings with current values. |
| GET | /hoc/api/cus/policy-layer/risk-ceilings/{ceiling_id} | get_risk_ceiling | Get a specific risk ceiling with current utilization. |
| PATCH | /hoc/api/cus/policy-layer/risk-ceilings/{ceiling_id} | update_risk_ceiling | Update a risk ceiling configuration. |
| POST | /hoc/api/cus/policy-layer/risk-ceilings/{ceiling_id}/reset | reset_risk_ceiling | Reset a risk ceiling's current value to 0. |
| GET | /hoc/api/cus/policy-layer/safety-rules | list_safety_rules | List all safety rules. |
| PATCH | /hoc/api/cus/policy-layer/safety-rules/{rule_id} | update_safety_rule | Update a safety rule configuration. |
| POST | /hoc/api/cus/policy-layer/simulate | simulate_evaluation | Simulate policy evaluation without side effects. |
| GET | /hoc/api/cus/policy-layer/state | get_policy_state | Get the current state of the policy layer. |
| POST | /hoc/api/cus/policy-layer/temporal-metrics/prune | prune_temporal_metrics | Prune and compact temporal metric events. |
| GET | /hoc/api/cus/policy-layer/temporal-metrics/storage-stats | get_temporal_storage_stats | Get storage statistics for temporal metrics. |
| GET | /hoc/api/cus/policy-layer/temporal-policies | list_temporal_policies | List temporal (sliding window) policies. |
| POST | /hoc/api/cus/policy-layer/temporal-policies | create_temporal_policy | Create a new temporal policy. |
| GET | /hoc/api/cus/policy-layer/temporal-policies/{policy_id}/utilization | get_temporal_utilization | Get current utilization for a temporal policy. |
| GET | /hoc/api/cus/policy-layer/versions | list_policy_versions | List all policy versions. |
| POST | /hoc/api/cus/policy-layer/versions | create_policy_version | Create a new policy version snapshot. |
| POST | /hoc/api/cus/policy-layer/versions/activate | activate_policy_version | Activate a policy version with pre-activation integrity chec |
| GET | /hoc/api/cus/policy-layer/versions/current | get_current_version | Get the currently active policy version. |
| POST | /hoc/api/cus/policy-layer/versions/rollback | rollback_to_version | Rollback to a previous policy version. |
| POST | /hoc/api/cus/policy-layer/versions/{version_id}/check | check_version_integrity | Run integrity checks on a version without activating. |
| GET | /hoc/api/cus/policy-layer/versions/{version_id}/provenance | get_version_provenance | Get the provenance (change history) for a policy version. |
| GET | /hoc/api/cus/policy-layer/violations | list_violations | List policy violations with filtering. |
| GET | /hoc/api/cus/policy-layer/violations/{violation_id} | get_violation | Get a specific violation by ID. |
| POST | /hoc/api/cus/policy-layer/violations/{violation_id}/acknowledge | acknowledge_violation | Acknowledge a violation (mark as reviewed). |
| GET | /hoc/api/cus/policy-proposals | list_proposals | List policy proposals (PB-S4). |
| GET | /hoc/api/cus/policy-proposals/stats/summary | get_proposal_stats | Get policy proposal statistics (PB-S4). |
| GET | /hoc/api/cus/policy-proposals/{proposal_id} | get_proposal | Get detailed policy proposal by ID (PB-S4). |
| POST | /hoc/api/cus/policy-proposals/{proposal_id}/approve | approve_proposal | Approve a policy proposal (PIN-373). |
| POST | /hoc/api/cus/policy-proposals/{proposal_id}/reject | reject_proposal | Reject a policy proposal (PIN-373). |
| GET | /hoc/api/cus/policy-proposals/{proposal_id}/versions | list_proposal_versions | List all versions of a policy proposal (PB-S4). |
| GET | /hoc/api/cus/policy/active | get_active_policies | V2 Facade: What governs execution now? |
| GET | /hoc/api/cus/policy/active/{policy_id} | get_active_policy_detail | V2 Facade: Policy detail for cross-domain navigation. |
| POST | /hoc/api/cus/policy/eval | evaluate_policy | Sandbox evaluation of policy for a skill execution. |
| GET | /hoc/api/cus/policy/lessons | get_policy_lessons | V2 Facade: What governance emerged? |
| GET | /hoc/api/cus/policy/lessons/{lesson_id} | get_policy_lesson_detail | V2 Facade: Lesson detail for cross-domain navigation. |
| GET | /hoc/api/cus/policy/library | get_policy_library | V2 Facade: What patterns are available? |
| GET | /hoc/api/cus/policy/requests | list_approval_requests | List approval requests with optional filtering. |
| POST | /hoc/api/cus/policy/requests | create_approval_request | Create a new approval request (persisted to DB). |
| GET | /hoc/api/cus/policy/requests/{request_id} | get_approval_request | Get the current status of an approval request. |
| POST | /hoc/api/cus/policy/requests/{request_id}/approve | approve_request | Approve an approval request. |
| POST | /hoc/api/cus/policy/requests/{request_id}/reject | reject_request | Reject an approval request. |
| GET | /hoc/api/cus/policy/thresholds | get_policy_thresholds | V2 Facade: What limits are enforced? |
| GET | /hoc/api/cus/policy/thresholds/{threshold_id} | get_policy_threshold_detail | V2 Facade: Threshold detail for cross-domain navigation. |
| GET | /hoc/api/cus/policy/violations | get_policy_violations_v2 | V2 Facade: What enforcement occurred? |
| GET | /hoc/api/cus/policy/violations/{violation_id} | get_policy_violation_detail | V2 Facade: Violation detail for cross-domain navigation. |
| GET | /hoc/api/cus/rate-limits | list_limits | List limits (GAP-122). |
| POST | /hoc/api/cus/rate-limits/check | check_limit | Check if a limit allows an operation. |
| GET | /hoc/api/cus/rate-limits/usage | get_usage | Get current usage summary. |
| GET | /hoc/api/cus/rate-limits/{limit_id} | get_limit | Get a specific limit. |
| PUT | /hoc/api/cus/rate-limits/{limit_id} | update_limit | Update a limit configuration. |
| POST | /hoc/api/cus/rate-limits/{limit_id}/reset | reset_limit | Reset a limit's usage counter. |
| GET | /hoc/api/cus/rbac/audit | query_audit_logs | Query RBAC audit logs. |
| POST | /hoc/api/cus/rbac/audit/cleanup | cleanup_audit_logs | Clean up old audit logs. |
| GET | /hoc/api/cus/rbac/info | get_policy_info | Get current RBAC policy information. |
| GET | /hoc/api/cus/rbac/matrix | get_permission_matrix | Get current permission matrix. |
| POST | /hoc/api/cus/rbac/reload | reload_policies | Hot-reload RBAC policies from file. |
| GET | /hoc/api/cus/replay/{incident_id}/explain/{item_id} | explain_replay_item | Get detailed explanation for a single replay item. |
| GET | /hoc/api/cus/replay/{incident_id}/slice | get_replay_slice | Get time-windowed replay slice of an incident. |
| GET | /hoc/api/cus/replay/{incident_id}/summary | get_incident_summary | Get incident summary for replay context. |
| GET | /hoc/api/cus/replay/{incident_id}/timeline | get_replay_timeline | Get full timeline for an incident (unpaginated for scrubbing |
| POST | /hoc/api/cus/retrieval/access | access_data | Mediated data access (GAP-094). |
| GET | /hoc/api/cus/runtime/capabilities | get_capabilities | Get available capabilities for an agent/tenant. |
| POST | /hoc/api/cus/runtime/query | query_runtime | Query runtime state. |
| POST | /hoc/api/cus/runtime/replay/{run_id} | replay_run | Replay a stored plan and optionally verify determinism parit |
| GET | /hoc/api/cus/runtime/resource-contract/{resource_id} | get_resource_contract | Get resource contract for a specific resource. |
| POST | /hoc/api/cus/runtime/simulate | simulate_plan | Simulate a plan before execution. |
| GET | /hoc/api/cus/runtime/skills | list_available_skills | List all available skills. |
| GET | /hoc/api/cus/runtime/skills/{skill_id} | describe_skill | Get detailed descriptor for a skill. |
| GET | /hoc/api/cus/runtime/traces | list_traces | List stored traces for a tenant. |
| GET | /hoc/api/cus/runtime/traces/{run_id} | get_trace | Get a specific trace by run ID. |
| GET | /hoc/api/cus/scheduler/jobs | list_jobs | List scheduled jobs. |
| POST | /hoc/api/cus/scheduler/jobs | create_job | Create a scheduled job (GAP-112). |
| DELETE | /hoc/api/cus/scheduler/jobs/{job_id} | delete_job | Delete a scheduled job. |
| GET | /hoc/api/cus/scheduler/jobs/{job_id} | get_job | Get a specific scheduled job. |
| PUT | /hoc/api/cus/scheduler/jobs/{job_id} | update_job | Update a scheduled job. |
| POST | /hoc/api/cus/scheduler/jobs/{job_id}/pause | pause_job | Pause a scheduled job. |
| POST | /hoc/api/cus/scheduler/jobs/{job_id}/resume | resume_job | Resume a paused job. |
| GET | /hoc/api/cus/scheduler/jobs/{job_id}/runs | list_job_runs | List job run history. |
| POST | /hoc/api/cus/scheduler/jobs/{job_id}/trigger | trigger_job | Trigger a job to run immediately. |
| GET | /hoc/api/cus/scheduler/runs/{run_id} | get_run | Get a specific job run. |
| GET | /hoc/api/cus/status_history | query_status_history | Query status history with filters. |
| GET | /hoc/api/cus/status_history/download/{export_id} | download_export | Download an exported file using signed URL. |
| GET | /hoc/api/cus/status_history/entity/{entity_type}/{entity_id} | get_entity_history | Get complete status history for a specific entity. |
| POST | /hoc/api/cus/status_history/export | create_export | Create an export of status history records. |
| GET | /hoc/api/cus/status_history/stats | get_stats | Get statistics about status history records. |
| GET | /hoc/api/cus/workers | list_workers | List all available workers. |
| GET | /hoc/api/cus/workers/available | list_available_workers_for_tenant | List workers available to the current tenant with their conf |
| GET | /hoc/api/cus/workers/business-builder/events/{run_id} | get_run_events | Get all events for a run (non-streaming). |
| GET | /hoc/api/cus/workers/business-builder/health | worker_health | Health check for Business Builder Worker. |
| POST | /hoc/api/cus/workers/business-builder/replay | replay_execution_endpoint | Replay a previous execution using Golden Replay (M4). |
| POST | /hoc/api/cus/workers/business-builder/run | run_worker | Execute the Business Builder Worker. |
| POST | /hoc/api/cus/workers/business-builder/run-streaming | run_worker_streaming | Execute the Business Builder Worker with real-time event str |
| GET | /hoc/api/cus/workers/business-builder/runs | list_runs | List recent worker runs. |
| DELETE | /hoc/api/cus/workers/business-builder/runs/{run_id} | delete_run | Delete a run from storage. |
| GET | /hoc/api/cus/workers/business-builder/runs/{run_id} | get_run | Get details of a worker run. |
| POST | /hoc/api/cus/workers/business-builder/runs/{run_id}/retry | retry_run | Retry a completed or failed run - Phase-2.5. |
| GET | /hoc/api/cus/workers/business-builder/schema/brand | get_brand_schema | Get the JSON schema for BrandRequest. |
| GET | /hoc/api/cus/workers/business-builder/schema/run | get_run_schema | Get the JSON schema for WorkerRunRequest. |
| GET | /hoc/api/cus/workers/business-builder/stream/{run_id} | stream_run_events | Stream real-time events for a worker run via Server-Sent Eve |
| POST | /hoc/api/cus/workers/business-builder/validate-brand | validate_brand | Validate a brand schema without executing the worker. |
| GET | /hoc/api/cus/workers/{worker_id} | get_worker_details | Get detailed information about a specific worker. |
| GET | /hoc/api/cus/workers/{worker_id}/config | get_worker_config | Get the effective configuration for a worker (tenant overrid |
| PUT | /hoc/api/cus/workers/{worker_id}/config | set_worker_config | Set tenant-specific configuration for a worker. |
