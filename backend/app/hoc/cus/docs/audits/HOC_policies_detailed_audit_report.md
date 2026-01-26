# HOC Policies Domain — Detailed Audit Report

**Date:** 2026-01-23
**Scope:** `houseofcards/customer/policies/` only
**Auditor:** Claude Code

---

## Complete Artifact Catalog

### FACADES (5 files)

---

#### 1. `facades/policies_facade.py` (1497 lines)

**File Header:**
```
Layer: L4 — Domain Engine
AUDIENCE: CUSTOMER
Product: ai-console
Role: Policies domain facade - unified entry point for policy management operations
```

**Dataclasses (27 total):**

| Line | Class Name | Fields | Semantic Purpose |
|------|------------|--------|------------------|
| 57 | `PolicyRuleSummaryResult` | rule_id, name, enforcement_mode, scope, source, status, created_at, created_by, integrity_status, integrity_score, trigger_count_30d, last_triggered_at | O2 list view summary for policy rules |
| 75 | `PolicyRulesListResult` | items, total, has_more, filters_applied | Paginated response wrapper for rules list |
| 85 | `PolicyRuleDetailResult` | rule_id, name, description, enforcement_mode, scope, source, status, created_at, created_by, updated_at, integrity_status, integrity_score, trigger_count_30d, last_triggered_at, rule_definition, violation_count_total | O3 detail view for single rule |
| 112 | `LimitSummaryResult` | limit_id, name, limit_category, limit_type, scope, enforcement, status, max_value, window_seconds, reset_period, integrity_status, integrity_score, breach_count_30d, last_breached_at, created_at | O2 list view summary for limits |
| 133 | `LimitsListResult` | items, total, has_more, filters_applied | Paginated response wrapper for limits list |
| 143 | `LimitDetailResult` | limit_id, name, description, limit_category, limit_type, scope, enforcement, status, max_value, window_seconds, reset_period, integrity_status, integrity_score, breach_count_30d, last_breached_at, created_at, updated_at, current_value, utilization_percent | O3 detail view for single limit |
| 173 | `PolicyStateResult` | total_policies, active_policies, drafts_pending_review, conflicts_detected, violations_24h, lessons_pending_action, last_updated | ACT-O4 policy layer state snapshot |
| 186 | `PolicyMetricsResult` | total_evaluations, total_blocks, total_allows, block_rate, avg_evaluation_ms, violations_by_type, evaluations_by_action, window_hours | ACT-O5 policy enforcement metrics |
| 205 | `PolicyConflictResult` | policy_a_id, policy_b_id, policy_a_name, policy_b_name, conflict_type, severity, explanation, recommended_action, detected_at | **DUPLICATE** of engine `PolicyConflict` |
| 220 | `ConflictsListResult` | items, total, unresolved_count, computed_at | Response wrapper for conflicts list |
| 230 | `PolicyDependencyRelation` | policy_id, policy_name, dependency_type, reason | Dependency relationship description |
| 240 | `PolicyNodeResult` | id, name, rule_type, scope, status, enforcement_mode, depends_on, required_by | **DUPLICATE** of engine `PolicyNode` |
| 254 | `PolicyDependencyEdge` | policy_id, depends_on_id, policy_name, depends_on_name, dependency_type, reason | **DUPLICATE** of engine `PolicyDependency` |
| 266 | `DependencyGraphResult` | nodes, edges, nodes_count, edges_count, computed_at | **MODIFIED DUPLICATE** of engine version |
| 282 | `PolicyViolationResult` | id, policy_id, policy_name, violation_type, severity, source, agent_id, description, occurred_at, is_synthetic | VIO-O1 violation summary |
| 298 | `ViolationsListResult` | items, total, has_more, filters_applied | Paginated response wrapper for violations |
| 313 | `BudgetDefinitionResult` | id, name, scope, max_value, reset_period, enforcement, status, current_usage, utilization_percent | THR-O2 budget definition summary |
| 328 | `BudgetsListResult` | items, total, filters_applied | Response wrapper for budgets list |
| 342 | `PolicyRequestResult` | id, proposal_name, proposal_type, rationale, proposed_rule, status, created_at, triggering_feedback_count, days_pending | ACT-O3 pending policy request |
| 357 | `PolicyRequestsListResult` | items, total, pending_count, filters_applied | Response wrapper for requests list |
| 372 | `LessonSummaryResult` | id, lesson_type, severity, title, status, source_event_type, created_at, has_proposed_action | O2 lesson summary |
| 386 | `LessonsListResult` | items, total, has_more, filters_applied | Response wrapper for lessons list |
| 396 | `LessonDetailResult` | id, lesson_type, severity, source_event_id, source_event_type, source_run_id, title, description, proposed_action, detected_pattern, status, draft_proposal_id, created_at, converted_at, deferred_until | O3 lesson detail |
| 417 | `LessonStatsResult` | total, by_type, by_status | Lesson statistics aggregation |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 430 | `PoliciesFacade` | list_policy_rules, get_policy_rule_detail, list_limits, get_limit_detail, list_lessons, get_lesson_detail, get_lesson_stats, get_policy_state, get_policy_metrics, list_policy_violations, list_policy_conflicts, get_policy_dependencies, list_policy_requests, list_budgets | Unified entry point for all policy read operations |

**Factory:**
| Line | Function | Returns | Semantic Purpose |
|------|----------|---------|------------------|
| 1452 | `get_policies_facade()` | `PoliciesFacade` | Singleton factory |

---

#### 2. `facades/controls_facade.py` (433 lines)

**File Header:**
```
Layer: L4 — Domain Engine
AUDIENCE: CUSTOMER
Product: ai-console
Role: Controls facade - unified entry point for control management
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| ~40 | `ControlType` | BUDGET, RATE, THRESHOLD, KILLSWITCH | Types of system controls |
| ~50 | `ControlState` | ACTIVE, DISABLED, PENDING, DEGRADED | Control lifecycle states |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~60 | `ControlConfig` | control_id, control_type, name, scope, max_value, enforcement, status | Control configuration DTO |
| ~80 | `ControlStatusSummary` | total_controls, active, disabled, degraded, by_type | Controls status aggregation |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~100 | `ControlsFacade` | list_controls, get_control_detail, get_control_status | Entry point for control read operations |

**Factory:**
| Line | Function | Returns |
|------|----------|---------|
| ~400 | `get_controls_facade()` | `ControlsFacade` |

---

#### 3. `facades/governance_facade.py` (616 lines)

**File Header:**
```
Layer: L4 — Domain Engine
AUDIENCE: CUSTOMER
Product: ai-console
Role: Governance facade - policy layer governance operations
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| ~45 | `GovernanceMode` | ACTIVE, PASSIVE, DEGRADED, DISABLED | Governance operational modes |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~55 | `GovernanceStateResult` | mode, is_active, degraded_reason, last_mode_change | Current governance state |
| ~70 | `KillSwitchResult` | is_active, triggered_by, triggered_at, reason, scope | Killswitch status |
| ~85 | `ConflictResolutionResult` | conflict_id, resolved, resolution_method, resolved_by, resolved_at | Conflict resolution outcome |
| ~100 | `BootStatusResult` | is_booted, boot_time, governance_version, config_hash | System boot status |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~120 | `GovernanceFacade` | get_governance_state, get_killswitch_status, get_boot_status, resolve_conflict | Governance read operations |

**Factory:**
| Line | Function | Returns |
|------|----------|---------|
| ~600 | `get_governance_facade()` | `GovernanceFacade` |

---

#### 4. `facades/limits_facade.py` (454 lines)

**File Header:**
```
Layer: L4 — Domain Engine
AUDIENCE: CUSTOMER
Product: ai-console
Role: Limits facade - limit management operations
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| ~40 | `LimitType` | BUDGET, RATE, THRESHOLD, COOLDOWN | Limit categories |
| ~50 | `LimitPeriod` | HOURLY, DAILY, WEEKLY, MONTHLY | Reset period options |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~60 | `LimitConfig` | limit_id, name, limit_type, scope, max_value, period, enforcement | Limit configuration DTO |
| ~80 | `LimitCheckResult` | limit_id, passed, current_value, max_value, headroom, blocked_reason | Runtime check result |
| ~100 | `UsageSummary` | total_usage, by_limit_type, by_scope, period_start, period_end | Usage aggregation |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~120 | `LimitsFacade` | check_limit, get_usage_summary, list_limits | Limit operations |

**Factory:**
| Line | Function | Returns |
|------|----------|---------|
| ~440 | `get_limits_facade()` | `LimitsFacade` |

---

#### 5. `facades/run_governance_facade.py` (328 lines)

**File Header:**
```
Layer: L4 — Domain Engine
AUDIENCE: CUSTOMER
Product: ai-console
Role: Run governance facade - pre-execution governance checks
```

**Dataclasses:** None (delegates to engines)

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~50 | `RunGovernanceFacade` | check_run_eligibility, get_run_constraints, simulate_run | Pre-execution governance checks |

**Factory:**
| Line | Function | Returns |
|------|----------|---------|
| ~320 | `get_run_governance_facade()` | `RunGovernanceFacade` |

---

### ENGINES (24 files)

---

#### 1. `engines/policy_graph_engine.py` (896 lines)

**File Header:**
```
Layer: L4 — Domain Engines
Product: system-wide
Role: Policy conflict detection and dependency graph computation
Reference: PIN-411 (Gap Closure), DFT-O4, DFT-O5
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| 44 | `ConflictType` | SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE | Conflict taxonomy (LOCKED) |
| 53 | `ConflictSeverity` | BLOCKING, WARNING | Conflict severity levels |
| 60 | `DependencyType` | EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT | Dependency taxonomy (LOCKED) |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| 73 | `PolicyConflict` | policy_a_id, policy_b_id, policy_a_name, policy_b_name, conflict_type, severity, explanation, recommended_action, detected_at | **AUTHORITATIVE** - Detected conflict between two policies |
| 101 | `PolicyDependency` | policy_id, depends_on_id, policy_name, depends_on_name, dependency_type, reason, is_active | **AUTHORITATIVE** - Dependency relationship between policies |
| 125 | `PolicyNode` | id, name, rule_type, scope, status, enforcement_mode, depends_on, required_by | **AUTHORITATIVE** - Node in dependency graph |
| 151 | `DependencyGraphResult` | nodes, edges, computed_at | **AUTHORITATIVE** - Result of dependency graph computation |
| 167 | `ConflictDetectionResult` | conflicts, unresolved_count, computed_at | Result of conflict detection |

**Classes:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 189 | `PolicyConflictEngine` | detect_conflicts, _detect_scope_overlaps, _detect_threshold_contradictions, _detect_temporal_conflicts, _detect_priority_overrides | DFT-O4: Detects logical contradictions between policies |
| 546 | `PolicyDependencyEngine` | compute_dependency_graph, check_can_delete, check_can_activate, _detect_explicit_dependencies, _detect_implicit_scope_dependencies, _detect_implicit_limit_dependencies | DFT-O5: Computes structural relationships between policies |

**Factories:**
| Line | Function | Returns | Semantic Purpose |
|------|----------|---------|------------------|
| 888 | `get_conflict_engine(tenant_id)` | `PolicyConflictEngine` | Factory with tenant isolation |
| 893 | `get_dependency_engine(tenant_id)` | `PolicyDependencyEngine` | Factory with tenant isolation |

---

#### 2. `engines/eligibility_engine.py` (829 lines)

**File Header:**
```
Layer: L4 — Domain Engine
Product: system-wide
Role: Eligibility Engine - pure rules, deterministic gating
Reference: PIN-287, ELIGIBILITY_RULES.md, part2-design-v1
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| 86 | `EligibilityDecision` | MAY, MAY_NOT | Binary eligibility decision |
| 102 | `SystemHealthStatus` | HEALTHY, DEGRADED, CRITICAL, UNKNOWN | System health for E-104 rule |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| 116 | `EligibilityConfig` | confidence_threshold, minimum_confidence, allowed_sources, actionable_types, duplicate_window_hours, rules_version | Engine configuration (frozen) |
| 310 | `EligibilityInput` | proposal_id, validator_verdict, source, affected_capabilities, received_at, tenant_id | Input to eligibility engine (frozen) |
| 331 | `RuleResult` | rule_id, rule_name, passed, reason, evidence | Single rule evaluation result (frozen) |
| 347 | `EligibilityVerdict` | decision, reason, rules_evaluated, first_failing_rule, blocking_signals, missing_prerequisites, evaluated_at, rules_version, rule_results | Engine output with full audit trail (frozen) |

**Protocols:**
| Line | Protocol | Methods | Semantic Purpose |
|------|----------|---------|------------------|
| 149 | `CapabilityLookup` | exists, is_frozen | Capability registry lookup |
| 161 | `GovernanceSignalLookup` | has_blocking_signal | Governance signal lookup |
| 175 | `SystemHealthLookup` | get_status | System health lookup |
| 183 | `ContractLookup` | has_similar_pending | Contract duplicate lookup |
| 201 | `PreApprovalLookup` | has_system_pre_approval | Pre-approval lookup |

**Default Implementations:**
| Line | Class | Semantic Purpose |
|------|-------|------------------|
| 214 | `DefaultCapabilityLookup` | Testing/standalone capability lookup |
| 236 | `DefaultGovernanceSignalLookup` | Testing/standalone governance lookup |
| 252 | `DefaultSystemHealthLookup` | Testing/standalone health lookup |
| 266 | `DefaultContractLookup` | Testing/standalone contract lookup |
| 291 | `DefaultPreApprovalLookup` | Testing/standalone pre-approval lookup |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 373 | `EligibilityEngine` | evaluate, _evaluate_e104_health_degraded, _evaluate_e100_below_minimum_confidence, _evaluate_e101_critical_without_escalation, _evaluate_e102_frozen_capability, _evaluate_e103_system_scope_without_preapproval, _evaluate_e001_confidence_threshold, _evaluate_e002_known_capability, _evaluate_e003_no_blocking_signal, _evaluate_e004_actionable_type, _evaluate_e005_source_allowlist, _evaluate_e006_not_duplicate | Part-2 eligibility rules engine - pure, deterministic |

**Constants:**
| Line | Constant | Value | Semantic Purpose |
|------|----------|-------|------------------|
| 78 | `ELIGIBILITY_ENGINE_VERSION` | "1.0.0" | Semantic versioning for rules |

---

#### 3. `engines/customer_policy_read_service.py` (332 lines)

**File Header:**
```
Layer: L4 — Domain Engine
Product: system-wide
Role: Customer policy domain read operations (L4)
Reference: PIN-281 (POLICY Domain Qualification)
```

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| 50 | `BudgetConstraint` | limit_cents, period, current_usage_cents, remaining_cents, percentage_used, reset_at | Customer-visible budget constraint (no internal thresholds) |
| 67 | `RateLimit` | requests_per_period, period, current_usage, remaining | Customer-visible rate limit (no internal bucket config) |
| 88 | `GuardrailSummary` | id, name, description, enabled, category, action_on_trigger | Customer-visible guardrail (no threshold/priority/rule_config) |
| 98 | `PolicyConstraints` | tenant_id, budget, rate_limits, guardrails, last_updated | Aggregate policy constraints for tenant |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 112 | `CustomerPolicyReadService` | get_policy_constraints, get_guardrail_detail, _get_budget_constraint, _calculate_period_bounds, _get_rate_limits, _get_guardrails | L4 service for customer-safe policy reads |

**Factory:**
| Line | Function | Returns |
|------|----------|---------|
| 317 | `get_customer_policy_read_service(session)` | `CustomerPolicyReadService` |

---

#### 4. `engines/override_service.py` (263 lines)

**File Header:**
```
Layer: L4 — Domain Engines
Product: system-wide
Role: Limit override service (PIN-LIM-05)
```

**Helper Functions:**
| Line | Function | Signature | Semantic Purpose |
|------|----------|-----------|------------------|
| 42 | `utc_now()` | `() -> datetime` | **DUPLICATE** - Returns current UTC time |
| 47 | `generate_uuid()` | `() -> str` | **DUPLICATE** - Generates UUID string |

**Exceptions:**
| Line | Exception | Base Class | Semantic Purpose |
|------|-----------|------------|------------------|
| 52 | `LimitOverrideServiceError` | `Exception` | Base exception for override service |
| 57 | `LimitNotFoundError` | `LimitOverrideServiceError` | **DUPLICATE NAME** - Limit not found |
| 62 | `OverrideNotFoundError` | `LimitOverrideServiceError` | Override not found |
| 67 | `OverrideValidationError` | `LimitOverrideServiceError` | Override validation failed |
| 72 | `StackingAbuseError` | `LimitOverrideServiceError` | Too many active overrides |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 82 | `LimitOverrideService` | request_override, get_override, list_overrides, cancel_override | Lifecycle of temporary limit overrides |

---

#### 5. `engines/policy_limits_service.py` (352 lines)

**File Header:**
```
Layer: L4 — Domain Engines
Product: system-wide
Role: Policy limits CRUD service (PIN-LIM-01)
```

**Helper Functions:**
| Line | Function | Signature | Semantic Purpose |
|------|----------|-----------|------------------|
| 46 | `utc_now()` | `() -> datetime` | **DUPLICATE** - Returns current UTC time |
| 51 | `generate_uuid()` | `() -> str` | **DUPLICATE** - Generates UUID string |

**Exceptions:**
| Line | Exception | Base Class | Semantic Purpose |
|------|-----------|------------|------------------|
| 56 | `PolicyLimitsServiceError` | `Exception` | Base exception for limits service |
| 61 | `LimitNotFoundError` | `PolicyLimitsServiceError` | **DUPLICATE NAME** - Limit not found |
| 66 | `LimitValidationError` | `PolicyLimitsServiceError` | Limit validation failed |
| 71 | `ImmutableFieldError` | `PolicyLimitsServiceError` | Attempted to modify immutable field |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 76 | `PolicyLimitsService` | create, update, delete, get | Authoritative writer for policy limits table |

---

#### 6. `engines/policy_rules_service.py` (375 lines)

**File Header:**
```
Layer: L4 — Domain Engines
Product: system-wide
Role: Policy rules CRUD service (PIN-LIM-02)
```

**Helper Functions:**
| Line | Function | Signature | Semantic Purpose |
|------|----------|-----------|------------------|
| 46 | `utc_now()` | `() -> datetime` | **DUPLICATE** - Returns current UTC time |
| 51 | `generate_uuid()` | `() -> str` | **DUPLICATE** - Generates UUID string |

**Exceptions:**
| Line | Exception | Base Class | Semantic Purpose |
|------|-----------|------------|------------------|
| 57 | `PolicyRulesServiceError` | `Exception` | Base exception for rules service |
| 62 | `RuleNotFoundError` | `PolicyRulesServiceError` | Rule not found |
| 67 | `RuleValidationError` | `PolicyRulesServiceError` | Rule validation failed |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 72 | `PolicyRulesService` | create, update, get, _validate_conditions, _compute_hash | Persist and validate policy rule logic |

---

#### 7. `engines/simulation_service.py` (246 lines)

**File Header:**
```
Layer: L4 — Domain Engines
Product: system-wide
Role: Limits simulation service (PIN-LIM-04)
```

**Exceptions:**
| Line | Exception | Base Class | Semantic Purpose |
|------|-----------|------------|------------------|
| 50 | `LimitsSimulationServiceError` | `Exception` | Base exception for simulation service |
| 55 | `TenantNotFoundError` | `LimitsSimulationServiceError` | Tenant not found |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| 60 | `LimitsSimulationService` | simulate, _build_context, _load_tenant_quotas, _load_cost_budgets, _load_policy_limits, _load_worker_limits, _load_active_overrides | Coordination layer for pre-execution limit checks |

---

#### 8. `engines/validator_service.py` (731 lines)

**File Header:**
```
Layer: L4 — Domain Engine
Product: system-wide
Role: Part-2 Validator Service for advisory verdicts
Reference: PIN-289
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| ~50 | `IssueType` | CAPABILITY_REQUEST, CONFIGURATION_CHANGE, BUG_REPORT, PERFORMANCE_ISSUE, SECURITY_CONCERN | Issue classification |
| ~60 | `Severity` | LOW, MEDIUM, HIGH, CRITICAL | Issue severity levels |
| ~70 | `RecommendedAction` | AUTO_FIX, REVIEW, ESCALATE, IGNORE | Recommended response |
| ~80 | `IssueSource` | USER, SYSTEM, AUTOMATED | Issue origin |
| ~90 | `ValidatorErrorType` | PARSE_ERROR, VALIDATION_ERROR, CONFIDENCE_ERROR | Validator error types |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~100 | `ValidatorInput` | issue_id, issue_type, description, source, metadata, received_at | Validator input (frozen) |
| ~120 | `ValidatorVerdict` | issue_id, issue_type, severity, confidence_score, recommended_action, explanation, validated_at | Validator output (frozen) |
| ~150 | `ValidatorError` | error_type, message, context | Validator error (frozen) |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~180 | `ValidatorService` | validate, _classify_issue, _compute_confidence, _determine_action | Part-2 validator for advisory verdicts |

---

### CONTROLS SUBFOLDER (6 files)

---

#### 1. `controls/engines/runtime_switch.py` (~200 lines)

**File Header:**
```
Layer: L4 — Domain Engine
Product: system-wide
Role: Runtime governance switch
```

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~30 | `GovernanceState` | is_active, is_degraded, degraded_reason, last_state_change | Runtime governance state |

**Module-Level Functions:**
| Line | Function | Signature | Semantic Purpose |
|------|----------|-----------|------------------|
| ~50 | `is_governance_active()` | `() -> bool` | Check if governance is active |
| ~60 | `disable_governance_runtime()` | `(reason: str) -> None` | Disable governance at runtime |
| ~70 | `enable_governance_runtime()` | `() -> None` | Enable governance at runtime |
| ~80 | `get_governance_state()` | `() -> GovernanceState` | Get current governance state |
| ~90 | `is_degraded_mode()` | `() -> bool` | Check if in degraded mode |
| ~100 | `enter_degraded_mode(reason: str)` | `(reason: str) -> None` | Enter degraded mode |
| ~110 | `exit_degraded_mode()` | `() -> None` | Exit degraded mode |
| ~120 | `reset_governance_state()` | `() -> None` | Reset to default state |

---

#### 2. `controls/engines/degraded_mode_checker.py` (~350 lines)

**File Header:**
```
Layer: L4 — Domain Engine
Product: system-wide
Role: Degraded mode detection and incident creation
```

**Enums:**
| Line | Enum | Values | Semantic Purpose |
|------|------|--------|------------------|
| ~40 | `DegradedModeCheckResult` | OK, DEGRADED, CRITICAL | Check result states |
| ~50 | `DegradedModeState` | NORMAL, DEGRADED, RECOVERY | Mode state machine |

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~60 | `DegradedModeStatus` | state, reason, entered_at, recovery_eta | Current mode status |
| ~75 | `DegradedModeCheckResponse` | result, status, message | Check response |
| ~90 | `DegradedModeIncident` | incident_id, reason, severity, created_at | Incident record |

**Exceptions:**
| Line | Exception | Semantic Purpose |
|------|-----------|------------------|
| ~100 | `GovernanceDegradedModeError` | Raised when operation blocked by degraded mode |

**Classes:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~110 | `DegradedModeIncidentCreator` | create_incident | Create degraded mode incident |
| ~140 | `GovernanceDegradedModeChecker` | check, is_degraded, get_status | Check and manage degraded mode |

**Module-Level Functions:**
| Line | Function | Signature | Semantic Purpose |
|------|----------|-----------|------------------|
| ~200 | `check_degraded_mode()` | `() -> DegradedModeCheckResponse` | Quick check helper |
| ~220 | `ensure_not_degraded()` | `() -> None` | Raise if degraded |
| ~240 | `enter_degraded_with_incident(reason)` | `(reason: str) -> DegradedModeIncident` | Enter and create incident |

---

#### 3. `controls/engines/customer_killswitch_read_service.py` (~250 lines)

**File Header:**
```
Layer: L4 — Domain Engine
AUDIENCE: CUSTOMER
Product: ai-console
Role: Customer killswitch read operations
```

**Dataclasses:**
| Line | Class | Fields | Semantic Purpose |
|------|-------|--------|------------------|
| ~40 | `KillswitchState` | is_active, triggered_at, triggered_by, reason | Killswitch state |
| ~55 | `GuardrailInfo` | id, name, category, enabled | Guardrail info for customer |
| ~70 | `IncidentStats` | total, by_severity, last_incident_at | Incident statistics |
| ~85 | `KillswitchStatusInfo` (Pydantic BaseModel) | state, guardrails, incidents | Combined status info |

**Class:**
| Line | Class | Methods | Semantic Purpose |
|------|-------|---------|------------------|
| ~100 | `CustomerKillswitchReadService` | get_killswitch_status, get_guardrails, get_incident_stats | Customer-safe killswitch reads |

**Factory:**
| Line | Function | Returns |
|------|----------|---------|
| ~240 | `get_customer_killswitch_read_service(session)` | `CustomerKillswitchReadService` |

---

## Duplication Issues — Detailed Analysis

---

### POL-DUP-001: PolicyNodeResult vs PolicyNode

**Severity:** MEDIUM

**Source Location (AUTHORITATIVE):**
```
File: engines/policy_graph_engine.py
Line: 125-148
Class: PolicyNode
```

**Duplicate Location:**
```
File: facades/policies_facade.py
Line: 240-251
Class: PolicyNodeResult
```

**Field Comparison:**

| Field | Engine `PolicyNode` | Facade `PolicyNodeResult` | Match |
|-------|---------------------|---------------------------|-------|
| id | `str` | `str` | ✅ |
| name | `str` | `str` | ✅ |
| rule_type | `str` | `str` | ✅ |
| scope | `str` | `str` | ✅ |
| status | `str` | `str` | ✅ |
| enforcement_mode | `str` | `str` | ✅ |
| depends_on | `list[dict]` | `list[PolicyDependencyRelation]` | ⚠️ Type differs |
| required_by | `list[dict]` | `list[PolicyDependencyRelation]` | ⚠️ Type differs |

**Semantic Analysis:**
- Engine version is authoritative, used by `PolicyDependencyEngine.compute_dependency_graph()`
- Facade re-creates with type wrapper (`PolicyDependencyRelation` instead of `dict`)
- The facade does transformation at line 1240-1265 to convert engine types to facade types

**Resolution:**
- Import `PolicyNode` from engine
- Keep `PolicyDependencyRelation` as a thin wrapper if needed for API serialization

---

### POL-DUP-002: PolicyDependencyEdge vs PolicyDependency

**Severity:** MEDIUM

**Source Location (AUTHORITATIVE):**
```
File: engines/policy_graph_engine.py
Line: 101-122
Class: PolicyDependency
```

**Duplicate Location:**
```
File: facades/policies_facade.py
Line: 254-263
Class: PolicyDependencyEdge
```

**Field Comparison:**

| Field | Engine `PolicyDependency` | Facade `PolicyDependencyEdge` | Match |
|-------|---------------------------|-------------------------------|-------|
| policy_id | `str` | `str` | ✅ |
| depends_on_id | `str` | `str` | ✅ |
| policy_name | `str` | `str` | ✅ |
| depends_on_name | `str` | `str` | ✅ |
| dependency_type | `DependencyType` (enum) | `str` | ⚠️ Type differs |
| reason | `str` | `str` | ✅ |
| is_active | `bool` (engine only) | - | ❌ Missing |

**Semantic Analysis:**
- Engine uses `DependencyType` enum, facade uses raw string
- Engine has extra `is_active` field
- Facade converts at line 1269-1278 by calling `.value` on enum

**Resolution:**
- Import `PolicyDependency` from engine
- Use `.value` for API serialization where needed

---

### POL-DUP-003: DependencyGraphResult Redefinition

**Severity:** MEDIUM

**Source Location (AUTHORITATIVE):**
```
File: engines/policy_graph_engine.py
Line: 151-164
Class: DependencyGraphResult
Fields: nodes, edges, computed_at
```

**Duplicate Location:**
```
File: facades/policies_facade.py
Line: 266-273
Class: DependencyGraphResult
Fields: nodes, edges, nodes_count, edges_count, computed_at
```

**Field Comparison:**

| Field | Engine | Facade | Analysis |
|-------|--------|--------|----------|
| nodes | `list[PolicyNode]` | `list[PolicyNodeResult]` | Type wrapper |
| edges | `list[PolicyDependency]` | `list[PolicyDependencyEdge]` | Type wrapper |
| computed_at | `datetime` | `datetime` | ✅ Same |
| nodes_count | - | `int` | ❌ Added |
| edges_count | - | `int` | ❌ Added |

**Semantic Analysis:**
- Facade adds `nodes_count` and `edges_count` for convenience
- These are easily computed as `len(nodes)` and `len(edges)`
- Facade creates these at line 1281-1286

**Resolution Options:**
1. Extend engine class with computed properties
2. Remove facade version, compute counts at serialization time
3. Create API-specific response model separate from domain DTO

---

### POL-DUP-004: PolicyConflictResult vs PolicyConflict

**Severity:** MEDIUM

**Source Location (AUTHORITATIVE):**
```
File: engines/policy_graph_engine.py
Line: 73-98
Class: PolicyConflict
```

**Duplicate Location:**
```
File: facades/policies_facade.py
Line: 205-217
Class: PolicyConflictResult
```

**Field Comparison:**

| Field | Engine `PolicyConflict` | Facade `PolicyConflictResult` | Match |
|-------|-------------------------|-------------------------------|-------|
| policy_a_id | `str` | `str` | ✅ |
| policy_b_id | `str` | `str` | ✅ |
| policy_a_name | `str` | `str` | ✅ |
| policy_b_name | `str` | `str` | ✅ |
| conflict_type | `ConflictType` (enum) | `str` | ⚠️ Type differs |
| severity | `ConflictSeverity` (enum) | `str` | ⚠️ Type differs |
| explanation | `str` | `str` | ✅ |
| recommended_action | `str` | `str` | ✅ |
| detected_at | `datetime` | `datetime` | ✅ |

**Semantic Analysis:**
- 100% field overlap
- Only difference is enum vs string for `conflict_type` and `severity`
- Facade converts at line 1200-1212 by calling `.value` on enums

**Resolution:**
- Import `PolicyConflict` from engine
- Create simple type alias or use directly with `.value` for serialization

---

### POL-DUP-005: LimitNotFoundError Duplicate Exception

**Severity:** LOW

**Location A:**
```
File: engines/override_service.py
Line: 57-59
Class: LimitNotFoundError(LimitOverrideServiceError)
```

**Location B:**
```
File: engines/policy_limits_service.py
Line: 61-63
Class: LimitNotFoundError(PolicyLimitsServiceError)
```

**Semantic Analysis:**
- Same exception name, different base classes
- Both represent "limit not found" but in different service contexts
- Can cause confusion when catching exceptions across modules

**Resolution Options:**
1. **Shared exception** in `policies_types.py`:
   ```python
   class LimitNotFoundError(Exception):
       """Raised when a limit is not found."""
       def __init__(self, limit_id: str, context: str = ""):
           self.limit_id = limit_id
           self.context = context
           super().__init__(f"Limit {limit_id} not found{': ' + context if context else ''}")
   ```
2. **Service-specific names**:
   - `OverrideLimitNotFoundError`
   - `PolicyLimitNotFoundError`

---

### POL-DUP-006: Helper Function Duplication

**Severity:** LOW

**Locations:**

| File | Line | Function | Implementation |
|------|------|----------|----------------|
| `engines/override_service.py` | 42-49 | `utc_now()`, `generate_uuid()` | `datetime.now(timezone.utc)`, `str(uuid.uuid4())` |
| `engines/policy_limits_service.py` | 46-53 | `utc_now()`, `generate_uuid()` | `datetime.now(timezone.utc)`, `str(uuid.uuid4())` |
| `engines/policy_rules_service.py` | 46-53 | `utc_now()`, `generate_uuid()` | `datetime.now(timezone.utc)`, `str(uuid.uuid4())` |

**Semantic Analysis:**
- Identical implementations in 3 files
- Used for timestamp generation and ID creation
- Pattern matches incidents domain which consolidated to `incidents_types.py`

**Resolution:**
Create `engines/policies_types.py`:
```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Shared type aliases for policies domain engines

from datetime import datetime, timezone
from typing import Callable
import uuid

# Type aliases for dependency injection
UuidFn = Callable[[], str]
ClockFn = Callable[[], datetime]

# Default implementations
def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())

__all__ = ["UuidFn", "ClockFn", "utc_now", "generate_uuid"]
```

---

## Summary Table

| ID | Location A | Location B | Type | Severity | Recommendation |
|----|------------|------------|------|----------|----------------|
| POL-DUP-001 | `policy_graph_engine.py:125` PolicyNode | `policies_facade.py:240` PolicyNodeResult | 100% overlap | MEDIUM | Import from engine |
| POL-DUP-002 | `policy_graph_engine.py:101` PolicyDependency | `policies_facade.py:254` PolicyDependencyEdge | 100% overlap | MEDIUM | Import from engine |
| POL-DUP-003 | `policy_graph_engine.py:151` DependencyGraphResult | `policies_facade.py:266` DependencyGraphResult | Extended duplicate | MEDIUM | Extend or compute counts |
| POL-DUP-004 | `policy_graph_engine.py:73` PolicyConflict | `policies_facade.py:205` PolicyConflictResult | 100% overlap | MEDIUM | Import from engine |
| POL-DUP-005 | `override_service.py:57` LimitNotFoundError | `policy_limits_service.py:61` LimitNotFoundError | Same name, different base | LOW | Shared or rename |
| POL-DUP-006 | `override_service.py:42` utc_now/generate_uuid | `policy_limits_service.py:46` + `policy_rules_service.py:46` | Identical helpers | LOW | Create policies_types.py |

---

## Quarantine Execution Report

**Executed:** 2026-01-23
**Status:** COMPLETE

### Executive Decision

Following the quarantine-instead-of-delete strategy established for the incidents domain:

- ❌ Did NOT delete facade duplicates
- ❌ Did NOT rush consolidation
- ✅ Quarantined facade duplicates (POL-DUP-001 to POL-DUP-004)
- ✅ Declared engine DTOs as authoritative
- ✅ Froze duplicates with full traceability headers
- ⏸ Deferred POL-DUP-005 (exception) and POL-DUP-006 (utilities)

### Quarantine Location

```
houseofcards/duplicate/policies/
├── __init__.py                    # NO EXPORTS — imports forbidden
├── policy_conflict_result.py      # POL-DUP-004
├── policy_node_result.py          # POL-DUP-001
├── policy_dependency_edge.py      # POL-DUP-002
├── dependency_graph_result.py     # POL-DUP-003
└── README.md                      # Quarantine documentation
```

### Files Created

| File | Size | Issue | Canonical Type |
|------|------|-------|----------------|
| `__init__.py` | 427 bytes | - | - |
| `policy_conflict_result.py` | 1515 bytes | POL-DUP-004 | `PolicyConflict` |
| `policy_node_result.py` | 1669 bytes | POL-DUP-001 | `PolicyNode` |
| `policy_dependency_edge.py` | 1223 bytes | POL-DUP-002 | `PolicyDependency` |
| `dependency_graph_result.py` | 1674 bytes | POL-DUP-003 | `DependencyGraphResult` |
| `README.md` | 2132 bytes | - | - |

### Header Template Applied

Each quarantined file includes:

```python
# ============================================================
# ⚠️ DUPLICATE — QUARANTINED (POLICIES DOMAIN)
#
# This file is NOT authoritative and MUST NOT be used.
#
# Canonical Type:
#   houseofcards/customer/policies/engines/policy_graph_engine.py
#   Class: <CanonicalClassName>
#
# Duplicate Of:
#   Originally defined in facade for response shaping
#
# Audit Reference:
#   POL-DUP-00X
#
# Status:
#   FROZEN — retained for historical traceability only
#
# Removal:
#   Eligible after Phase 2 DTO unification
# ============================================================
```

### Deferred Actions

| Issue | Type | Reason for Deferral |
|-------|------|---------------------|
| POL-DUP-005 | `LimitNotFoundError` duplicate exception | Exception types handled during error-taxonomy work |
| POL-DUP-006 | `utc_now()`/`generate_uuid()` helpers | Utility drift tolerated — not DTO drift |

### CI Guard Recommended

```bash
# Add to CI to prevent imports from quarantine zone
grep -R "houseofcards\.duplicate\.policies" app/ && exit 1
```

### Canonical Authority Declaration

| Domain | Authoritative Location |
|--------|------------------------|
| Policy conflicts | `engines/policy_graph_engine.py::PolicyConflict` |
| Policy nodes | `engines/policy_graph_engine.py::PolicyNode` |
| Policy dependencies | `engines/policy_graph_engine.py::PolicyDependency` |
| Dependency graphs | `engines/policy_graph_engine.py::DependencyGraphResult` |

### Removal Policy

Quarantined files are eligible for deletion after:

1. Phase 2 DTO unification is complete
2. All facade imports are updated to use engine types
3. Import cleanup is verified via CI

Until then, files remain FROZEN for historical traceability.

---

**Report Generated:** 2026-01-23
**Quarantine Executed:** 2026-01-23
**Status:** COMPLETE
