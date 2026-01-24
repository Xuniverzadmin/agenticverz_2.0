# HOC Layer Fit Analysis - Detailed Report

**Generated:** 2026-01-23
**Total Files:** 715
**Layer Fit:** 155 (21.7%)
**Misfit:** 560 (78.3%)
**Total Work Items:** 542

---

## Section 1: By Folder Layer (Where files are located)

| Folder Layer | Files | FIT | MISFIT | NO_ACTION | HEADER_FIX | RECLASSIFY | EXTRACT_DRIVER | EXTRACT_AUTH | SPLIT |
|--------------|-------|-----|--------|-----------|------------|------------|----------------|--------------|-------|
| **L2** | 84 | 22 | 62 | 22 | 9 | 0 | 53 | 0 | 0 |
| **L3** | 62 | 8 | 54 | 12 | 12 | 4 | 25 | 1 | 8 |
| **L4** | 457 | 62 | 395 | 74 | 24 | 183 | 154 | 11 | 11 |
| **L6** | 111 | 63 | 48 | 65 | 9 | 34 | 2 | 0 | 1 |
| **UNCLASSIFIED** | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |

**Key Insight:** L4 (engines/) has the most files (457) but also the most misfits (395). Most need RECLASSIFY_ONLY (183) or EXTRACT_DRIVER (154).

---

## Section 2: By Declared Layer (What headers claim)

| Declared | Files | FIT | Dominant L2 | Dominant L3 | Dominant L4 | Dominant L6 | No Signals |
|----------|-------|-----|-------------|-------------|-------------|-------------|------------|
| **L2** | 95 | 20 | 52 | 0 | 4 | 23 | 16 |
| **L3** | 72 | 8 | 24 | 6 | 2 | 36 | 4 |
| **L4** | 348 | 49 | 19 | 6 | 13 | 285 | 25 |
| **L5** | 36 | 5 | 2 | 0 | 0 | 29 | 5 |
| **L6** | 83 | 53 | 13 | 0 | 0 | 53 | 17 |
| **UNDECLARED** | 76 | 20 | 20 | 0 | 1 | 50 | 5 |

**Key Insight:** 348 files declare L4 but only 13 behave like L4. 285 of them behave like L6 (DB operations).

---

## Section 3: By Detected/Dominant Layer (Actual behavior)

| Detected | Files | FIT | In L2/ | In L3/ | In L4/ | In L6/ |
|----------|-------|-----|--------|--------|--------|--------|
| **L2** | 130 | 27 | 69 | 10 | 44 | 7 |
| **L3** | 12 | 6 | 0 | 10 | 2 | 0 |
| **L4** | 21 | 9 | 0 | 0 | 21 | 0 |
| **L6** | 480 | 65 | 15 | 40 | 345 | 79 |
| **NONE** | 72 | 48 | 0 | 2 | 45 | 25 |

**Key Insight:** 480 files behave like L6 (DB operations), but only 79 are in the L6 folder. 345 are in L4 (engines/) - these need EXTRACT_DRIVER or RECLASSIFY.

---

## Section 4: Work Backlog Summary

| # | Action | Files | Effort | CUSTOMER | FOUNDER | INTERNAL | API |
|---|--------|-------|--------|----------|---------|----------|-----|
| 1 | **HEADER_FIX_ONLY** | 54 | LOW | 22 | 3 | 26 | 3 |
| 2 | **RECLASSIFY_ONLY** | 222 | LOW | 119 | 6 | 97 | 0 |
| 3 | **EXTRACT_DRIVER** | 234 | MEDIUM | 177 | 10 | 47 | 0 |
| 4 | **EXTRACT_AUTHORITY** | 12 | HIGH | 3 | 0 | 9 | 0 |
| 5 | **SPLIT_FILE** | 20 | HIGH | 17 | 1 | 2 | 0 |
| 6 | **NO_ACTION** | 173 | NONE | 103 | 2 | 67 | 1 |

---

## Section 5: Work Backlog by Domain

### HEADER_FIX_ONLY (54 files) - LOW Effort

**CUSTOMER** (20 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| activity | 1 | run_governance_facade.py |
| agent | 1 | panel_signal_collector.py |
| analytics | 1 | ai_console_panel_engine.py |
| general | 4 | alerts_facade.py, compliance_facade.py +2 more |
| incidents | 2 | panel_verification_engine.py, evidence_report.py |
| integrations | 4 | cost_safety_rails.py, integrations_facade.py +2 more |
| logs | 3 | trace_facade.py, evidence_facade.py +1 more |
| ops | 1 | ops.py |
| policies | 3 | policy_driver.py, run_governance_facade.py +1 more |

**FOUNDER** (2 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| ops | 2 | ops_facade.py, ops_domain_models.py |

**INTERNAL** (23 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| account | 3 | lifecycle_gate.py, tenant_resolver.py +1 more |
| agent | 6 | panel_verification_engine.py, panel_signal_collector.py +4 more |
| analytics | 1 | console_auth.py |
| general | 4 | core.py, gateway_config.py +2 more |
| integrations | 1 | gateway_middleware.py |
| logs | 1 | jwt_auth.py |
| platform | 5 | feedback.py, routing_models.py +3 more |
| policies | 2 | boot_guard.py, limit_hook.py |

**API** (9 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| customer | 2 | billing_dependencies.py, protection_dependencies.py |
| founder | 1 | founder_lifecycle.py |
| infrastructure | 3 | tenant.py, rate_limit.py +1 more |
| internal | 3 | billing_gate.py, founder_auth.py +1 more |


### RECLASSIFY_ONLY (222 files) - LOW Effort

**CUSTOMER** (119 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| account | 3 | profile.py, identity_resolver.py +1 more |
| activity | 2 | llm_threshold_service.py, activity_enums.py |
| agent | 10 | panel_capability_resolver.py, semantic_validator.py +8 more |
| analytics | 7 | leader.py, killswitch.py +5 more |
| general | 14 | webhook_verify.py, alert_emitter.py +12 more |
| incidents | 10 | incident_driver.py, guard_write_service.py +8 more |
| integrations | 16 | bridges.py, prevention_contract.py +14 more |
| logs | 12 | idempotency.py, job_execution.py +10 more |
| platform | 3 | sandbox_executor.py, job_scheduler.py +1 more |
| policies | 42 | logs_read_service.py, recovery_write_service.py +40 more |

**FOUNDER** (6 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| agent | 2 | founder_action_write_service.py, ops_write_service.py |
| ops | 4 | ops_write_service.py, error_store.py +2 more |

**INTERNAL** (97 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| account | 2 | lifecycle_provider.py, tenant_auth.py |
| agent | 30 | blackboard_ops.py, panel_capability_resolver.py +28 more |
| general | 15 | redis_publisher.py, subscribers.py +13 more |
| incidents | 4 | failure_semantics.py, observability_guard.py +2 more |
| integrations | 4 | oidc_provider.py, oauth_providers.py +2 more |
| logs | 4 | audit_handlers.py, pool.py +2 more |
| platform | 26 | governance.py, emitters.py +24 more |
| policies | 8 | publisher.py, brand.py +6 more |
| recovery | 4 | recovery_write_service.py, scoped_execution.py +2 more |


### EXTRACT_DRIVER (234 files) - MEDIUM Effort

**CUSTOMER** (132 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| account | 7 | accounts_facade.py, notifications_facade.py +5 more |
| activity | 1 | activity_facade.py |
| agent | 1 | panel_signal_translator.py |
| analytics | 9 | analytics_facade.py, cost_anomaly_detector.py +7 more |
| api_keys | 3 | api_keys_facade.py, keys_service.py +1 more |
| general | 19 | monitors_facade.py, scheduler_facade.py +17 more |
| incidents | 13 | incidents_facade.py, policy_violation_service.py +11 more |
| integrations | 20 | cost_snapshots.py, customer_incidents_adapter.py +18 more |
| logs | 23 | logs_facade.py, cost_anomaly_detector.py +21 more |
| overview | 1 | overview_facade.py |
| platform | 1 | platform_health_service.py |
| policies | 34 | policies_facade.py, limits_facade.py +32 more |

**FOUNDER** (4 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| incidents | 1 | ops_incident_service.py |
| ops | 3 | founder_action_write_service.py, founder_review.py +1 more |

**INTERNAL** (45 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| agent | 20 | llm_invoke_v2.py, registry_service.py +18 more |
| analytics | 2 | simulate.py, runner.py |
| api_keys | 2 | api_key_service.py, onboarding_transitions.py |
| general | 4 | rbac_rules_loader.py, authorization.py +2 more |
| incidents | 3 | recovery_evaluator.py, lifecycle_worker.py +1 more |
| integrations | 1 | worker.py |
| logs | 1 | gateway_audit.py |
| platform | 7 | care.py, state_resolver.py +5 more |
| policies | 5 | policy_checker.py, graduation_evaluator.py +3 more |

**API** (53 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| customer | 45 | cost_ops.py, recovery.py +43 more |
| founder | 6 | founder_actions.py, founder_contract_review.py +4 more |
| internal | 2 | main.py, aos_cli.py |


### EXTRACT_AUTHORITY (12 files) - HIGH Effort

**CUSTOMER** (3 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| general | 1 | pool_manager.py |
| integrations | 1 | webhook_adapter.py |
| platform | 1 | pool_manager.py |

**INTERNAL** (9 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| agent | 2 | calendar_write.py, retry_policy.py |
| analytics | 1 | authority.py |
| general | 4 | skill_http.py, authorization_choke.py +2 more |
| platform | 1 | engine.py |
| policies | 1 | rbac.py |


### SPLIT_FILE (20 files) - HIGH Effort

**CUSTOMER** (17 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| account | 1 | channel_service.py |
| analytics | 1 | detection_facade.py |
| incidents | 2 | prevention_engine.py, channel_service.py |
| integrations | 6 | cost_bridges.py, founder_ops_adapter.py +4 more |
| logs | 3 | certificate.py, replay_determinism.py +1 more |
| platform | 1 | platform_eligibility_adapter.py |
| policies | 3 | certificate.py, policy_models.py +1 more |

**FOUNDER** (1 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| ops | 1 | founder_review_adapter.py |

**INTERNAL** (2 files)

| Domain | Files | Sample Files |
|--------|-------|--------------|
| integrations | 1 | rbac_integration.py |
| policies | 1 | rbac_middleware.py |


---

## Section 6: Recommended Execution Plan

1. **Week 1: Quick Wins (276 LOW effort files)**
   - HEADER_FIX_ONLY: 54 files - Just update file headers
   - RECLASSIFY_ONLY: 222 files - Move files to correct folders

2. **Week 2-3: Main Work (234 MEDIUM effort files)**
   - EXTRACT_DRIVER: 234 files - Extract DB operations to L6 drivers
   - Requires: Driver extraction templates and conventions

3. **Week 4: Complex Work (32 HIGH effort files)**
   - EXTRACT_AUTHORITY: 12 files - Move HTTP/decisions to proper layers
   - SPLIT_FILE: 20 files - Split multi-responsibility files
   - Requires: Careful architectural review

**Total: 542 work items**

