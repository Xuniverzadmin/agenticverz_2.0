# Phase 5 — Duplicate Detection Summary

**Generated:** 2026-01-27
**Generator:** `hoc_phase5_duplicate_detector.py`
**Reference:** PIN-470, PIN-479
**Files scanned:** 385

---

## Detection Results

| Mode | Type | Threshold | Duplicates Found |
|------|------|-----------|-----------------|
| Mode 1 | Exact File (SHA-256) | 100% | 2 |
| Mode 2 | Function/Class Signature | >70% body | 388 |
| Mode 3 | Block Similarity (same name) | >80% | 36 |
| **Total** | | | **426** |

**Consolidation candidates:** 90

---

## Mode 1: Exact File Duplicates

| ID | Domain A | File | Domain B | File | Recommendation |
|----|----------|------|----------|------|----------------|
| D001 | general | `L5_engines/audit_durability.py` | general | `L5_engines/durability.py` | DELETE_FROM_GENERAL |
| D002 | general | `L5_lifecycle/engines/base.py` | general | `L5_engines/lifecycle_stages_base.py` | DELETE_FROM_GENERAL |

---

## Mode 2: Function/Class Signature Duplicates

| ID | Type | Domain A | Location A | Domain B | Location B | Similarity | Recommendation |
|----|------|----------|-----------|----------|-----------|-----------|----------------|
| D501 | FUNCTION | account | `L6_drivers/user_write_driver.py:utc_now():51-53` | analytics | `L6_drivers/cost_write_driver.py:utc_now():52-54` | 100.0% | EXTRACT_TO_GENERAL |
| D502 | FUNCTION | account | `L6_drivers/user_write_driver.py:utc_now():51-53` | general | `L5_controls/drivers/guard_write_driver.py:utc_now():64-66` | 100.0% | DELETE_FROM_ACCOUNT |
| D503 | FUNCTION | account | `L6_drivers/user_write_driver.py:utc_now():51-53` | general | `L5_utils/time.py:utc_now():23-25` | 100.0% | DELETE_FROM_ACCOUNT |
| D504 | FUNCTION | account | `L6_drivers/user_write_driver.py:utc_now():51-53` | incidents | `L6_drivers/guard_write_driver.py:utc_now():66-68` | 100.0% | EXTRACT_TO_GENERAL |
| D505 | FUNCTION | analytics | `L6_drivers/cost_write_driver.py:utc_now():52-54` | general | `L5_controls/drivers/guard_write_driver.py:utc_now():64-66` | 100.0% | DELETE_FROM_ANALYTICS |
| D506 | FUNCTION | analytics | `L6_drivers/cost_write_driver.py:utc_now():52-54` | general | `L5_utils/time.py:utc_now():23-25` | 100.0% | DELETE_FROM_ANALYTICS |
| D507 | FUNCTION | analytics | `L6_drivers/cost_write_driver.py:utc_now():52-54` | incidents | `L6_drivers/guard_write_driver.py:utc_now():66-68` | 100.0% | EXTRACT_TO_GENERAL |
| D508 | FUNCTION | controls | `L6_drivers/override_driver.py:utc_now():54-56` | policies | `L5_engines/policy_limits_engine.py:utc_now():78-80` | 100.0% | EXTRACT_TO_GENERAL |
| D509 | FUNCTION | controls | `L6_drivers/override_driver.py:utc_now():54-56` | policies | `L5_engines/policy_rules_engine.py:utc_now():79-81` | 100.0% | EXTRACT_TO_GENERAL |
| D510 | FUNCTION | general | `L5_controls/drivers/guard_write_driver.py:utc_now():64-66` | general | `L5_utils/time.py:utc_now():23-25` | 100.0% | DELETE_FROM_GENERAL |
| D511 | FUNCTION | general | `L5_controls/drivers/guard_write_driver.py:utc_now():64-66` | incidents | `L6_drivers/guard_write_driver.py:utc_now():66-68` | 100.0% | DELETE_FROM_INCIDENTS |
| D512 | FUNCTION | general | `L5_utils/time.py:utc_now():23-25` | incidents | `L6_drivers/guard_write_driver.py:utc_now():66-68` | 100.0% | DELETE_FROM_INCIDENTS |
| D513 | FUNCTION | general | `L6_drivers/cross_domain.py:utc_now():62-64` | general | `L5_engines/knowledge_lifecycle_manager.py:utc_now():73-75` | 100.0% | DELETE_FROM_GENERAL |
| D514 | FUNCTION | general | `L6_drivers/cross_domain.py:utc_now():62-64` | incidents | `L5_engines/incident_engine.py:utc_now():93-95` | 100.0% | DELETE_FROM_INCIDENTS |
| D515 | FUNCTION | general | `L6_drivers/cross_domain.py:utc_now():62-64` | logs | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | DELETE_FROM_LOGS |
| D516 | FUNCTION | general | `L6_drivers/cross_domain.py:utc_now():62-64` | policies | `L5_engines/lessons_engine.py:utc_now():85-87` | 100.0% | DELETE_FROM_POLICIES |
| D517 | FUNCTION | general | `L6_drivers/cross_domain.py:utc_now():62-64` | policies | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | DELETE_FROM_POLICIES |
| D518 | FUNCTION | general | `L5_engines/knowledge_lifecycle_manager.py:utc_now():73-75` | incidents | `L5_engines/incident_engine.py:utc_now():93-95` | 100.0% | DELETE_FROM_INCIDENTS |
| D519 | FUNCTION | general | `L5_engines/knowledge_lifecycle_manager.py:utc_now():73-75` | logs | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | DELETE_FROM_LOGS |
| D520 | FUNCTION | general | `L5_engines/knowledge_lifecycle_manager.py:utc_now():73-75` | policies | `L5_engines/lessons_engine.py:utc_now():85-87` | 100.0% | DELETE_FROM_POLICIES |
| D521 | FUNCTION | general | `L5_engines/knowledge_lifecycle_manager.py:utc_now():73-75` | policies | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | DELETE_FROM_POLICIES |
| D522 | FUNCTION | incidents | `L5_engines/incident_engine.py:utc_now():93-95` | logs | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | EXTRACT_TO_GENERAL |
| D523 | FUNCTION | incidents | `L5_engines/incident_engine.py:utc_now():93-95` | policies | `L5_engines/lessons_engine.py:utc_now():85-87` | 100.0% | EXTRACT_TO_GENERAL |
| D524 | FUNCTION | incidents | `L5_engines/incident_engine.py:utc_now():93-95` | policies | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | EXTRACT_TO_GENERAL |
| D525 | FUNCTION | logs | `L5_engines/mapper.py:utc_now():43-45` | policies | `L5_engines/lessons_engine.py:utc_now():85-87` | 100.0% | EXTRACT_TO_GENERAL |
| D526 | FUNCTION | logs | `L5_engines/mapper.py:utc_now():43-45` | policies | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | EXTRACT_TO_GENERAL |
| D527 | FUNCTION | policies | `L5_engines/lessons_engine.py:utc_now():85-87` | policies | `L5_engines/mapper.py:utc_now():43-45` | 100.0% | EXTRACT_TO_GENERAL |
| D528 | FUNCTION | policies | `L5_engines/policy_limits_engine.py:utc_now():78-80` | policies | `L5_engines/policy_rules_engine.py:utc_now():79-81` | 100.0% | EXTRACT_TO_GENERAL |
| D529 | FUNCTION | account | `L5_engines/email_verification.py:get_email_verification_service():297-302` | api_keys | `L5_engines/email_verification.py:get_email_verification_service():293-298` | 100.0% | EXTRACT_TO_GENERAL |
| D530 | FUNCTION | account | `L5_engines/notifications_facade.py:get_notifications_facade():467-480` | integrations | `L5_engines/notifications_facade.py:get_notifications_facade():463-476` | 100.0% | EXTRACT_TO_GENERAL |
| D531 | FUNCTION | account | `L5_engines/profile.py:_get_bool_env():246-251` | policies | `L5_engines/profile.py:_get_bool_env():246-251` | 100.0% | EXTRACT_TO_GENERAL |
| D532 | FUNCTION | account | `L5_engines/profile.py:get_governance_profile():254-273` | policies | `L5_engines/profile.py:get_governance_profile():254-273` | 100.0% | EXTRACT_TO_GENERAL |
| D533 | FUNCTION | account | `L5_engines/profile.py:load_governance_config():276-323` | policies | `L5_engines/profile.py:load_governance_config():276-323` | 100.0% | EXTRACT_TO_GENERAL |
| D534 | FUNCTION | account | `L5_engines/profile.py:validate_governance_config():326-401` | policies | `L5_engines/profile.py:validate_governance_config():326-401` | 100.0% | EXTRACT_TO_GENERAL |
| D535 | FUNCTION | account | `L5_engines/profile.py:get_governance_config():411-424` | policies | `L5_engines/profile.py:get_governance_config():411-424` | 100.0% | EXTRACT_TO_GENERAL |
| D536 | FUNCTION | account | `L5_engines/profile.py:reset_governance_config():427-430` | policies | `L5_engines/profile.py:reset_governance_config():427-430` | 100.0% | EXTRACT_TO_GENERAL |
| D537 | FUNCTION | account | `L5_engines/profile.py:validate_governance_at_startup():438-459` | policies | `L5_engines/profile.py:validate_governance_at_startup():438-459` | 100.0% | EXTRACT_TO_GENERAL |
| D538 | FUNCTION | activity | `L5_engines/run_governance_facade.py:get_run_governance_facade():325-338` | general | `L4_runtime/facades/run_governance_facade.py:get_run_governance_facade():322-335` | 100.0% | DELETE_FROM_ACTIVITY |
| D539 | FUNCTION | activity | `L5_engines/run_governance_facade.py:get_run_governance_facade():325-338` | policies | `L5_engines/run_governance_facade.py:get_run_governance_facade():317-330` | 100.0% | EXTRACT_TO_GENERAL |
| D540 | FUNCTION | general | `L4_runtime/facades/run_governance_facade.py:get_run_governance_facade():322-335` | policies | `L5_engines/run_governance_facade.py:get_run_governance_facade():317-330` | 100.0% | DELETE_FROM_POLICIES |
| D541 | FUNCTION | activity | `L5_engines/threshold_engine.py:create_threshold_signal_record():638-678` | controls | `L6_drivers/llm_threshold_driver.py:create_threshold_signal_record():630-670` | 100.0% | EXTRACT_TO_GENERAL |
| D542 | FUNCTION | activity | `L5_engines/threshold_engine.py:collect_signals_from_evaluation():681-708` | controls | `L6_drivers/llm_threshold_driver.py:collect_signals_from_evaluation():673-700` | 100.0% | EXTRACT_TO_GENERAL |
| D545 | FUNCTION | controls | `L6_drivers/override_driver.py:generate_uuid():59-61` | general | `L6_drivers/cross_domain.py:generate_uuid():67-69` | 100.0% | DELETE_FROM_CONTROLS |
| D546 | FUNCTION | controls | `L6_drivers/override_driver.py:generate_uuid():59-61` | policies | `L5_engines/policy_limits_engine.py:generate_uuid():83-85` | 100.0% | EXTRACT_TO_GENERAL |
| D547 | FUNCTION | controls | `L6_drivers/override_driver.py:generate_uuid():59-61` | policies | `L5_engines/policy_rules_engine.py:generate_uuid():84-86` | 100.0% | EXTRACT_TO_GENERAL |
| D548 | FUNCTION | general | `L6_drivers/cross_domain.py:generate_uuid():67-69` | policies | `L5_engines/policy_limits_engine.py:generate_uuid():83-85` | 100.0% | DELETE_FROM_POLICIES |
| D549 | FUNCTION | general | `L6_drivers/cross_domain.py:generate_uuid():67-69` | policies | `L5_engines/policy_rules_engine.py:generate_uuid():84-86` | 100.0% | DELETE_FROM_POLICIES |
| D550 | FUNCTION | policies | `L5_engines/policy_limits_engine.py:generate_uuid():83-85` | policies | `L5_engines/policy_rules_engine.py:generate_uuid():84-86` | 100.0% | EXTRACT_TO_GENERAL |
| D551 | FUNCTION | controls | `L5_engines/alerts_facade.py:get_alerts_facade():663-676` | general | `L5_engines/alerts_facade.py:get_alerts_facade():666-679` | 100.0% | DELETE_FROM_CONTROLS |
| D552 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:is_governance_active():82-90` | general | `L5_engines/runtime_switch.py:is_governance_active():78-86` | 100.0% | DELETE_FROM_GENERAL |
| D553 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:is_degraded_mode():93-106` | general | `L5_engines/runtime_switch.py:is_degraded_mode():89-102` | 100.0% | DELETE_FROM_GENERAL |
| D558 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:get_governance_state():226-240` | general | `L5_engines/runtime_switch.py:get_governance_state():222-236` | 100.0% | DELETE_FROM_GENERAL |
| D559 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:reset_governance_state():243-254` | general | `L5_engines/runtime_switch.py:reset_governance_state():239-250` | 100.0% | DELETE_FROM_GENERAL |
| D561 | FUNCTION | general | `L5_controls/engines/degraded_mode_checker.py:check_degraded_mode():605-618` | general | `L5_engines/degraded_mode_checker.py:check_degraded_mode():612-625` | 100.0% | DELETE_FROM_GENERAL |
| D562 | FUNCTION | general | `L5_controls/engines/degraded_mode_checker.py:ensure_not_degraded():621-636` | general | `L5_engines/degraded_mode_checker.py:ensure_not_degraded():628-643` | 100.0% | DELETE_FROM_GENERAL |
| D563 | FUNCTION | general | `L5_controls/engines/degraded_mode_checker.py:enter_degraded_with_incident():639-667` | general | `L5_engines/degraded_mode_checker.py:enter_degraded_with_incident():646-674` | 100.0% | DELETE_FROM_GENERAL |
| D564 | FUNCTION | general | `L5_controls/engines/degraded_mode_checker.py:_reset_degraded_mode_state():671-675` | general | `L5_engines/degraded_mode_checker.py:_reset_degraded_mode_state():678-682` | 100.0% | DELETE_FROM_GENERAL |
| D565 | FUNCTION | general | `L5_ui/engines/rollout_projection.py:founder_view_to_dict():657-710` | policies | `L5_engines/rollout_projection.py:founder_view_to_dict():649-702` | 100.0% | DELETE_FROM_POLICIES |
| D566 | FUNCTION | general | `L5_ui/engines/rollout_projection.py:completion_report_to_dict():713-724` | policies | `L5_engines/rollout_projection.py:completion_report_to_dict():705-716` | 100.0% | DELETE_FROM_POLICIES |
| D567 | FUNCTION | general | `L4_runtime/engines/constraint_checker.py:check_inspection_allowed():254-280` | general | `L5_engines/constraint_checker.py:check_inspection_allowed():253-279` | 100.0% | DELETE_FROM_GENERAL |
| D568 | FUNCTION | general | `L4_runtime/engines/constraint_checker.py:get_constraint_violations():283-310` | general | `L5_engines/constraint_checker.py:get_constraint_violations():282-309` | 100.0% | DELETE_FROM_GENERAL |
| D569 | FUNCTION | general | `L4_runtime/engines/phase_status_invariants.py:check_phase_status_invariant():324-341` | policies | `L5_engines/phase_status_invariants.py:check_phase_status_invariant():323-340` | 100.0% | DELETE_FROM_POLICIES |
| D570 | FUNCTION | general | `L4_runtime/engines/phase_status_invariants.py:ensure_phase_status_invariant():344-361` | policies | `L5_engines/phase_status_invariants.py:ensure_phase_status_invariant():343-360` | 100.0% | DELETE_FROM_POLICIES |
| D571 | FUNCTION | general | `L4_runtime/engines/plan_generation_engine.py:generate_plan_for_run():218-252` | policies | `L5_engines/plan_generation_engine.py:generate_plan_for_run():211-245` | 100.0% | DELETE_FROM_POLICIES |
| D572 | FUNCTION | general | `L5_support/CRM/engines/job_executor.py:create_default_executor():458-476` | policies | `L5_engines/job_executor.py:create_default_executor():465-483` | 100.0% | DELETE_FROM_POLICIES |
| D573 | FUNCTION | general | `L5_support/CRM/engines/job_executor.py:execution_result_to_evidence():484-520` | policies | `L5_engines/job_executor.py:execution_result_to_evidence():491-527` | 100.0% | DELETE_FROM_POLICIES |
| D574 | FUNCTION | general | `L5_schemas/agent.py:_utc_now():30-32` | general | `L5_schemas/artifact.py:_utc_now():30-32` | 100.0% | DELETE_FROM_GENERAL |
| D575 | FUNCTION | general | `L5_schemas/agent.py:_utc_now():30-32` | general | `L5_schemas/plan.py:_utc_now():30-32` | 100.0% | DELETE_FROM_GENERAL |
| D576 | FUNCTION | general | `L5_schemas/artifact.py:_utc_now():30-32` | general | `L5_schemas/plan.py:_utc_now():30-32` | 100.0% | DELETE_FROM_GENERAL |
| D577 | FUNCTION | general | `L5_schemas/rac_models.py:create_run_expectations():304-354` | logs | `L5_schemas/audit_models.py:create_run_expectations():296-346` | 100.0% | DELETE_FROM_LOGS |
| D578 | FUNCTION | general | `L5_schemas/rac_models.py:create_run_expectations():304-354` | logs | `L5_schemas/models.py:create_run_expectations():296-346` | 100.0% | DELETE_FROM_LOGS |
| D579 | FUNCTION | logs | `L5_schemas/audit_models.py:create_run_expectations():296-346` | logs | `L5_schemas/models.py:create_run_expectations():296-346` | 100.0% | EXTRACT_TO_GENERAL |
| D580 | FUNCTION | general | `L5_schemas/rac_models.py:create_domain_ack():357-388` | logs | `L5_schemas/audit_models.py:create_domain_ack():349-380` | 100.0% | DELETE_FROM_LOGS |
| D581 | FUNCTION | general | `L5_schemas/rac_models.py:create_domain_ack():357-388` | logs | `L5_schemas/models.py:create_domain_ack():349-380` | 100.0% | DELETE_FROM_LOGS |
| D582 | FUNCTION | logs | `L5_schemas/audit_models.py:create_domain_ack():349-380` | logs | `L5_schemas/models.py:create_domain_ack():349-380` | 100.0% | EXTRACT_TO_GENERAL |
| D583 | FUNCTION | general | `L6_drivers/knowledge_plane.py:get_knowledge_plane_registry():441-446` | general | `L5_lifecycle/drivers/knowledge_plane.py:get_knowledge_plane_registry():440-445` | 100.0% | DELETE_FROM_GENERAL |
| D584 | FUNCTION | general | `L6_drivers/knowledge_plane.py:_reset_registry():449-454` | general | `L5_lifecycle/drivers/knowledge_plane.py:_reset_registry():448-453` | 100.0% | DELETE_FROM_GENERAL |
| D585 | FUNCTION | general | `L6_drivers/knowledge_plane.py:_reset_registry():449-454` | integrations | `L5_schemas/datasource_model.py:_reset_registry():545-550` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D586 | FUNCTION | general | `L6_drivers/knowledge_plane.py:_reset_registry():449-454` | integrations | `L6_drivers/connector_registry.py:_reset_registry():811-816` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D587 | FUNCTION | general | `L5_lifecycle/drivers/knowledge_plane.py:_reset_registry():448-453` | integrations | `L5_schemas/datasource_model.py:_reset_registry():545-550` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D588 | FUNCTION | general | `L5_lifecycle/drivers/knowledge_plane.py:_reset_registry():448-453` | integrations | `L6_drivers/connector_registry.py:_reset_registry():811-816` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D589 | FUNCTION | integrations | `L5_schemas/datasource_model.py:_reset_registry():545-550` | integrations | `L6_drivers/connector_registry.py:_reset_registry():811-816` | 100.0% | EXTRACT_TO_GENERAL |
| D590 | FUNCTION | general | `L6_drivers/knowledge_plane.py:create_knowledge_plane():458-469` | general | `L5_lifecycle/drivers/knowledge_plane.py:create_knowledge_plane():457-468` | 100.0% | DELETE_FROM_GENERAL |
| D591 | FUNCTION | general | `L6_drivers/knowledge_plane.py:get_knowledge_plane():472-475` | general | `L5_lifecycle/drivers/knowledge_plane.py:get_knowledge_plane():471-474` | 100.0% | DELETE_FROM_GENERAL |
| D592 | FUNCTION | general | `L6_drivers/knowledge_plane.py:list_knowledge_planes():478-483` | general | `L5_lifecycle/drivers/knowledge_plane.py:list_knowledge_planes():477-482` | 100.0% | DELETE_FROM_GENERAL |
| D593 | FUNCTION | general | `L5_lifecycle/drivers/execution.py:get_ingestion_executor():1287-1294` | integrations | `L6_drivers/execution.py:get_ingestion_executor():1288-1295` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D594 | FUNCTION | general | `L5_lifecycle/drivers/execution.py:get_indexing_executor():1297-1304` | integrations | `L6_drivers/execution.py:get_indexing_executor():1298-1305` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D595 | FUNCTION | general | `L5_lifecycle/drivers/execution.py:get_classification_executor():1307-1314` | integrations | `L6_drivers/execution.py:get_classification_executor():1308-1315` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D596 | FUNCTION | general | `L5_lifecycle/drivers/execution.py:reset_executors():1317-1322` | integrations | `L6_drivers/execution.py:reset_executors():1318-1323` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D597 | FUNCTION | general | `L5_engines/alert_log_linker.py:get_alert_log_linker():680-685` | incidents | `L5_engines/alert_log_linker.py:get_alert_log_linker():679-684` | 100.0% | DELETE_FROM_INCIDENTS |
| D598 | FUNCTION | general | `L5_engines/alert_log_linker.py:_reset_alert_log_linker():688-691` | incidents | `L5_engines/alert_log_linker.py:_reset_alert_log_linker():687-690` | 100.0% | DELETE_FROM_INCIDENTS |
| D599 | FUNCTION | general | `L5_engines/alert_log_linker.py:create_alert_log_link():697-727` | incidents | `L5_engines/alert_log_linker.py:create_alert_log_link():696-726` | 100.0% | DELETE_FROM_INCIDENTS |
| D600 | FUNCTION | general | `L5_engines/alert_log_linker.py:get_alerts_for_run():730-745` | incidents | `L5_engines/alert_log_linker.py:get_alerts_for_run():729-744` | 100.0% | DELETE_FROM_INCIDENTS |
| D601 | FUNCTION | general | `L5_engines/alert_log_linker.py:get_logs_for_alert():748-759` | incidents | `L5_engines/alert_log_linker.py:get_logs_for_alert():747-758` | 100.0% | DELETE_FROM_INCIDENTS |
| D602 | FUNCTION | general | `L5_engines/audit_durability.py:check_rac_durability():284-302` | general | `L5_engines/durability.py:check_rac_durability():284-302` | 100.0% | DELETE_FROM_GENERAL |
| D603 | FUNCTION | general | `L5_engines/audit_durability.py:ensure_rac_durability():305-325` | general | `L5_engines/durability.py:ensure_rac_durability():305-325` | 100.0% | DELETE_FROM_GENERAL |
| D604 | FUNCTION | general | `L5_engines/audit_store.py:_determine_durability_mode():77-100` | logs | `L6_drivers/audit_store.py:_determine_durability_mode():84-107` | 100.0% | DELETE_FROM_LOGS |
| D605 | FUNCTION | general | `L5_engines/audit_store.py:_determine_durability_mode():77-100` | logs | `L6_drivers/store.py:_determine_durability_mode():83-106` | 100.0% | DELETE_FROM_LOGS |
| D606 | FUNCTION | logs | `L6_drivers/audit_store.py:_determine_durability_mode():84-107` | logs | `L6_drivers/store.py:_determine_durability_mode():83-106` | 100.0% | EXTRACT_TO_GENERAL |
| D607 | FUNCTION | general | `L5_engines/audit_store.py:get_audit_store():435-448` | logs | `L6_drivers/audit_store.py:get_audit_store():442-455` | 100.0% | DELETE_FROM_LOGS |
| D608 | FUNCTION | general | `L5_engines/audit_store.py:get_audit_store():435-448` | logs | `L6_drivers/store.py:get_audit_store():441-454` | 100.0% | DELETE_FROM_LOGS |
| D609 | FUNCTION | logs | `L6_drivers/audit_store.py:get_audit_store():442-455` | logs | `L6_drivers/store.py:get_audit_store():441-454` | 100.0% | EXTRACT_TO_GENERAL |
| D610 | FUNCTION | general | `L5_engines/compliance_facade.py:get_compliance_facade():505-518` | logs | `L5_engines/compliance_facade.py:get_compliance_facade():502-515` | 100.0% | DELETE_FROM_LOGS |
| D611 | FUNCTION | general | `L5_engines/control_registry.py:get_control_registry():450-455` | logs | `L5_engines/control_registry.py:get_control_registry():449-454` | 100.0% | DELETE_FROM_LOGS |
| D612 | FUNCTION | general | `L5_engines/fatigue_controller.py:get_alert_fatigue_controller():695-700` | policies | `L5_engines/fatigue_controller.py:get_alert_fatigue_controller():695-700` | 100.0% | DELETE_FROM_POLICIES |
| D613 | FUNCTION | general | `L5_engines/fatigue_controller.py:_reset_controller():703-708` | policies | `L5_engines/fatigue_controller.py:_reset_controller():703-708` | 100.0% | DELETE_FROM_POLICIES |
| D614 | FUNCTION | general | `L5_engines/fatigue_controller.py:check_alert_fatigue():712-727` | policies | `L5_engines/fatigue_controller.py:check_alert_fatigue():712-727` | 100.0% | DELETE_FROM_POLICIES |
| D615 | FUNCTION | general | `L5_engines/fatigue_controller.py:suppress_alert():730-743` | policies | `L5_engines/fatigue_controller.py:suppress_alert():730-743` | 100.0% | DELETE_FROM_POLICIES |
| D616 | FUNCTION | general | `L5_engines/fatigue_controller.py:get_fatigue_stats():746-749` | policies | `L5_engines/fatigue_controller.py:get_fatigue_stats():746-749` | 100.0% | DELETE_FROM_POLICIES |
| D617 | FUNCTION | general | `L5_engines/lifecycle_facade.py:get_lifecycle_facade():696-709` | general | `L5_engines/lifecycle/lifecycle_facade.py:get_lifecycle_facade():691-704` | 100.0% | DELETE_FROM_GENERAL |
| D618 | FUNCTION | general | `L5_engines/monitors_facade.py:get_monitors_facade():528-541` | integrations | `L5_engines/monitors_facade.py:get_monitors_facade():525-538` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D619 | FUNCTION | general | `L5_engines/retrieval_facade.py:get_retrieval_facade():505-518` | integrations | `L5_engines/retrieval_facade.py:get_retrieval_facade():507-520` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D620 | FUNCTION | general | `L5_engines/retrieval_mediator.py:get_retrieval_mediator():431-444` | integrations | `L5_engines/retrieval_mediator.py:get_retrieval_mediator():432-445` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D621 | FUNCTION | general | `L5_engines/retrieval_mediator.py:configure_retrieval_mediator():447-471` | integrations | `L5_engines/retrieval_mediator.py:configure_retrieval_mediator():448-472` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D622 | FUNCTION | incidents | `L5_engines/hallucination_detector.py:create_detector_for_tenant():445-467` | policies | `L5_engines/hallucination_detector.py:create_detector_for_tenant():444-466` | 100.0% | EXTRACT_TO_GENERAL |
| D623 | FUNCTION | integrations | `L5_notifications/engines/channel_engine.py:get_notify_service():1032-1037` | integrations | `L5_engines/channel_engine.py:get_notify_service():1037-1042` | 100.0% | EXTRACT_TO_GENERAL |
| D624 | FUNCTION | integrations | `L5_notifications/engines/channel_engine.py:_reset_notify_service():1040-1043` | integrations | `L5_engines/channel_engine.py:_reset_notify_service():1045-1048` | 100.0% | EXTRACT_TO_GENERAL |
| D625 | FUNCTION | integrations | `L5_notifications/engines/channel_engine.py:get_channel_config():1049-1064` | integrations | `L5_engines/channel_engine.py:get_channel_config():1054-1069` | 100.0% | EXTRACT_TO_GENERAL |
| D626 | FUNCTION | integrations | `L5_notifications/engines/channel_engine.py:send_notification():1067-1086` | integrations | `L5_engines/channel_engine.py:send_notification():1072-1091` | 100.0% | EXTRACT_TO_GENERAL |
| D627 | FUNCTION | integrations | `L5_notifications/engines/channel_engine.py:check_channel_health():1089-1102` | integrations | `L5_engines/channel_engine.py:check_channel_health():1094-1107` | 100.0% | EXTRACT_TO_GENERAL |
| D628 | FUNCTION | logs | `L5_support/CRM/engines/audit_engine.py:audit_result_to_record():803-835` | logs | `L5_engines/audit_engine.py:audit_result_to_record():803-835` | 100.0% | EXTRACT_TO_GENERAL |
| D629 | FUNCTION | logs | `L5_support/CRM/engines/audit_engine.py:create_audit_input_from_evidence():838-888` | logs | `L5_engines/audit_engine.py:create_audit_input_from_evidence():838-888` | 100.0% | EXTRACT_TO_GENERAL |
| D630 | FUNCTION | logs | `L6_drivers/job_execution.py:_hash_value():652-657` | logs | `L5_engines/audit_evidence.py:_hash_value():170-175` | 100.0% | EXTRACT_TO_GENERAL |
| D631 | FUNCTION | logs | `L5_engines/audit_reconciler.py:get_audit_reconciler():309-322` | logs | `L5_engines/reconciler.py:get_audit_reconciler():308-321` | 100.0% | EXTRACT_TO_GENERAL |
| D632 | FUNCTION | logs | `L5_engines/completeness_checker.py:check_evidence_completeness():471-493` | logs | `L5_engines/export_completeness_checker.py:check_evidence_completeness():471-493` | 100.0% | EXTRACT_TO_GENERAL |
| D633 | FUNCTION | logs | `L5_engines/completeness_checker.py:ensure_evidence_completeness():496-518` | logs | `L5_engines/export_completeness_checker.py:ensure_evidence_completeness():496-518` | 100.0% | EXTRACT_TO_GENERAL |
| D634 | FUNCTION | logs | `L5_engines/mapper.py:get_control_mappings_for_incident():258-277` | policies | `L5_engines/mapper.py:get_control_mappings_for_incident():258-277` | 100.0% | EXTRACT_TO_GENERAL |
| D635 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class IssueType:86-97` | policies | `L5_engines/validator_engine.py:class IssueType:90-101` | 100.0% | EXTRACT_TO_GENERAL |
| D636 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class Severity:105-115` | policies | `L5_engines/validator_engine.py:class Severity:109-119` | 100.0% | EXTRACT_TO_GENERAL |
| D637 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class RecommendedAction:123-133` | policies | `L5_engines/validator_engine.py:class RecommendedAction:127-137` | 100.0% | EXTRACT_TO_GENERAL |
| D638 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class IssueSource:141-148` | policies | `L5_engines/validator_engine.py:class IssueSource:145-152` | 100.0% | EXTRACT_TO_GENERAL |
| D639 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class ValidatorInput:157-170` | policies | `L5_engines/validator_engine.py:class ValidatorInput:161-174` | 100.0% | EXTRACT_TO_GENERAL |
| D640 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class ValidatorVerdict:179-196` | policies | `L5_engines/validator_engine.py:class ValidatorVerdict:183-200` | 100.0% | EXTRACT_TO_GENERAL |
| D641 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class ValidatorErrorType:204-210` | policies | `L5_engines/validator_engine.py:class ValidatorErrorType:208-214` | 100.0% | EXTRACT_TO_GENERAL |
| D642 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class ValidatorError:214-223` | policies | `L5_engines/validator_engine.py:class ValidatorError:218-227` | 100.0% | EXTRACT_TO_GENERAL |
| D643 | CLASS | account | `L5_support/CRM/engines/validator_engine.py:class ValidatorService:329-735` | policies | `L5_engines/validator_engine.py:class ValidatorService:333-739` | 100.0% | EXTRACT_TO_GENERAL |
| D644 | CLASS | account | `L5_engines/email_verification.py:class VerificationResult:60-66` | api_keys | `L5_engines/email_verification.py:class VerificationResult:56-62` | 100.0% | EXTRACT_TO_GENERAL |
| D645 | CLASS | account | `L5_engines/email_verification.py:class EmailVerificationError:69-75` | api_keys | `L5_engines/email_verification.py:class EmailVerificationError:65-71` | 100.0% | EXTRACT_TO_GENERAL |
| D646 | CLASS | account | `L5_engines/email_verification.py:class EmailVerificationService:78-290` | api_keys | `L5_engines/email_verification.py:class EmailVerificationService:74-286` | 100.0% | EXTRACT_TO_GENERAL |
| D647 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationChannel:67-73` | integrations | `L5_engines/notifications_facade.py:class NotificationChannel:63-69` | 100.0% | EXTRACT_TO_GENERAL |
| D649 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationPriority:76-81` | integrations | `L5_engines/notifications_facade.py:class NotificationPriority:72-77` | 100.0% | EXTRACT_TO_GENERAL |
| D652 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationStatus:84-90` | integrations | `L5_engines/notifications_facade.py:class NotificationStatus:80-86` | 100.0% | EXTRACT_TO_GENERAL |
| D654 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationInfo:94-124` | integrations | `L5_engines/notifications_facade.py:class NotificationInfo:90-120` | 100.0% | EXTRACT_TO_GENERAL |
| D655 | CLASS | account | `L5_engines/notifications_facade.py:class ChannelInfo:128-144` | integrations | `L5_engines/notifications_facade.py:class ChannelInfo:124-140` | 100.0% | EXTRACT_TO_GENERAL |
| D656 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationPreferences:148-162` | integrations | `L5_engines/notifications_facade.py:class NotificationPreferences:144-158` | 100.0% | EXTRACT_TO_GENERAL |
| D657 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationsFacade:165-457` | integrations | `L5_engines/notifications_facade.py:class NotificationsFacade:161-453` | 100.0% | EXTRACT_TO_GENERAL |
| D658 | CLASS | account | `L5_engines/profile.py:class GovernanceProfile:68-106` | policies | `L5_engines/profile.py:class GovernanceProfile:68-106` | 100.0% | EXTRACT_TO_GENERAL |
| D659 | CLASS | account | `L5_engines/profile.py:class GovernanceConfig:110-149` | policies | `L5_engines/profile.py:class GovernanceConfig:110-149` | 100.0% | EXTRACT_TO_GENERAL |
| D660 | CLASS | account | `L5_engines/profile.py:class GovernanceConfigError:233-238` | policies | `L5_engines/profile.py:class GovernanceConfigError:233-238` | 100.0% | EXTRACT_TO_GENERAL |
| D661 | CLASS | general | `L5_engines/lifecycle_facade.py:class RunState:80-87` | general | `L5_engines/lifecycle/lifecycle_facade.py:class RunState:75-82` | 100.0% | DELETE_FROM_GENERAL |
| D662 | CLASS | activity | `L5_engines/run_governance_facade.py:class RunGovernanceFacade:76-315` | general | `L4_runtime/facades/run_governance_facade.py:class RunGovernanceFacade:73-312` | 100.0% | DELETE_FROM_ACTIVITY |
| D663 | CLASS | activity | `L5_engines/run_governance_facade.py:class RunGovernanceFacade:76-315` | policies | `L5_engines/run_governance_facade.py:class RunGovernanceFacade:68-307` | 100.0% | EXTRACT_TO_GENERAL |
| D664 | CLASS | general | `L4_runtime/facades/run_governance_facade.py:class RunGovernanceFacade:73-312` | policies | `L5_engines/run_governance_facade.py:class RunGovernanceFacade:68-307` | 100.0% | DELETE_FROM_POLICIES |
| D665 | CLASS | activity | `L5_engines/threshold_engine.py:class ThresholdParams:85-129` | controls | `L6_drivers/llm_threshold_driver.py:class ThresholdParams:97-141` | 100.0% | EXTRACT_TO_GENERAL |
| D666 | CLASS | activity | `L5_engines/threshold_engine.py:class ThresholdParamsUpdate:132-145` | controls | `L6_drivers/llm_threshold_driver.py:class ThresholdParamsUpdate:144-157` | 100.0% | EXTRACT_TO_GENERAL |
| D667 | CLASS | activity | `L5_engines/threshold_engine.py:class ThresholdSignal:153-162` | controls | `L6_drivers/llm_threshold_driver.py:class ThresholdSignal:165-174` | 100.0% | EXTRACT_TO_GENERAL |
| D668 | CLASS | activity | `L5_engines/threshold_engine.py:class ThresholdEvaluationResult:166-172` | controls | `L6_drivers/llm_threshold_driver.py:class ThresholdEvaluationResult:178-184` | 100.0% | EXTRACT_TO_GENERAL |
| D672 | CLASS | activity | `L5_engines/threshold_engine.py:class ThresholdSignalRecord:621-635` | controls | `L6_drivers/llm_threshold_driver.py:class ThresholdSignalRecord:613-627` | 100.0% | EXTRACT_TO_GENERAL |
| D674 | CLASS | controls | `L6_drivers/circuit_breaker.py:class Incident:123-156` | controls | `L6_drivers/circuit_breaker_async.py:class Incident:118-151` | 100.0% | EXTRACT_TO_GENERAL |
| D675 | CLASS | controls | `L5_engines/alerts_facade.py:class AlertSeverity:64-69` | general | `L5_engines/alerts_facade.py:class AlertSeverity:67-72` | 100.0% | DELETE_FROM_CONTROLS |
| D676 | CLASS | controls | `L5_engines/alerts_facade.py:class AlertStatus:72-76` | general | `L5_engines/alerts_facade.py:class AlertStatus:75-79` | 100.0% | DELETE_FROM_CONTROLS |
| D677 | CLASS | controls | `L5_engines/alerts_facade.py:class AlertRule:80-108` | general | `L5_engines/alerts_facade.py:class AlertRule:83-111` | 100.0% | DELETE_FROM_CONTROLS |
| D678 | CLASS | controls | `L5_engines/alerts_facade.py:class AlertEvent:112-144` | general | `L5_engines/alerts_facade.py:class AlertEvent:115-147` | 100.0% | DELETE_FROM_CONTROLS |
| D679 | CLASS | controls | `L5_engines/alerts_facade.py:class AlertRoute:148-170` | general | `L5_engines/alerts_facade.py:class AlertRoute:151-173` | 100.0% | DELETE_FROM_CONTROLS |
| D680 | CLASS | controls | `L5_engines/alerts_facade.py:class AlertsFacade:173-653` | general | `L5_engines/alerts_facade.py:class AlertsFacade:176-656` | 100.0% | DELETE_FROM_CONTROLS |
| D681 | CLASS | general | `L5_controls/drivers/runtime_switch.py:class GovernanceState:62-68` | general | `L5_engines/runtime_switch.py:class GovernanceState:58-64` | 100.0% | DELETE_FROM_GENERAL |
| D682 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class DegradedModeCheckResult:45-51` | general | `L5_engines/degraded_mode_checker.py:class DegradedModeCheckResult:52-58` | 100.0% | DELETE_FROM_GENERAL |
| D683 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class DegradedModeState:54-59` | general | `L5_engines/degraded_mode_checker.py:class DegradedModeState:61-66` | 100.0% | DELETE_FROM_GENERAL |
| D684 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class GovernanceDegradedModeError:70-101` | general | `L5_engines/degraded_mode_checker.py:class GovernanceDegradedModeError:77-108` | 100.0% | DELETE_FROM_GENERAL |
| D685 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class DegradedModeStatus:105-126` | general | `L5_engines/degraded_mode_checker.py:class DegradedModeStatus:112-133` | 100.0% | DELETE_FROM_GENERAL |
| D686 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class DegradedModeCheckResponse:130-157` | general | `L5_engines/degraded_mode_checker.py:class DegradedModeCheckResponse:137-164` | 100.0% | DELETE_FROM_GENERAL |
| D687 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class DegradedModeIncident:161-171` | general | `L5_engines/degraded_mode_checker.py:class DegradedModeIncident:168-178` | 100.0% | DELETE_FROM_GENERAL |
| D688 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class DegradedModeIncidentCreator:174-301` | general | `L5_engines/degraded_mode_checker.py:class DegradedModeIncidentCreator:181-308` | 100.0% | DELETE_FROM_GENERAL |
| D689 | CLASS | general | `L5_controls/engines/degraded_mode_checker.py:class GovernanceDegradedModeChecker:309-602` | general | `L5_engines/degraded_mode_checker.py:class GovernanceDegradedModeChecker:316-609` | 100.0% | DELETE_FROM_GENERAL |
| D690 | CLASS | general | `L5_workflow/contracts/engines/contract_engine.py:class ContractState:114-148` | general | `L5_engines/contract_engine.py:class ContractState:113-147` | 100.0% | DELETE_FROM_GENERAL |
| D691 | CLASS | general | `L5_workflow/contracts/engines/contract_engine.py:class ContractStateMachine:151-304` | general | `L5_engines/contract_engine.py:class ContractStateMachine:150-303` | 100.0% | DELETE_FROM_GENERAL |
| D692 | CLASS | general | `L5_workflow/contracts/engines/contract_engine.py:class ContractService:312-718` | general | `L5_engines/contract_engine.py:class ContractService:311-717` | 100.0% | DELETE_FROM_GENERAL |
| D693 | CLASS | general | `L5_ui/engines/rollout_projection.py:class RolloutStage:89-100` | policies | `L5_engines/rollout_projection.py:class RolloutStage:81-92` | 100.0% | DELETE_FROM_POLICIES |
| D694 | CLASS | general | `L5_ui/engines/rollout_projection.py:class BlastRadius:119-131` | policies | `L5_engines/rollout_projection.py:class BlastRadius:111-123` | 100.0% | DELETE_FROM_POLICIES |
| D695 | CLASS | general | `L5_ui/engines/rollout_projection.py:class StabilizationWindow:135-146` | policies | `L5_engines/rollout_projection.py:class StabilizationWindow:127-138` | 100.0% | DELETE_FROM_POLICIES |
| D696 | CLASS | general | `L5_ui/engines/rollout_projection.py:class ContractSummary:150-159` | policies | `L5_engines/rollout_projection.py:class ContractSummary:142-151` | 100.0% | DELETE_FROM_POLICIES |
| D697 | CLASS | general | `L5_ui/engines/rollout_projection.py:class ExecutionSummary:163-171` | policies | `L5_engines/rollout_projection.py:class ExecutionSummary:155-163` | 100.0% | DELETE_FROM_POLICIES |
| D698 | CLASS | general | `L5_ui/engines/rollout_projection.py:class AuditSummary:175-182` | policies | `L5_engines/rollout_projection.py:class AuditSummary:167-174` | 100.0% | DELETE_FROM_POLICIES |
| D699 | CLASS | general | `L5_ui/engines/rollout_projection.py:class RolloutPlan:186-192` | policies | `L5_engines/rollout_projection.py:class RolloutPlan:178-184` | 100.0% | DELETE_FROM_POLICIES |
| D700 | CLASS | general | `L5_ui/engines/rollout_projection.py:class FounderRolloutView:196-212` | policies | `L5_engines/rollout_projection.py:class FounderRolloutView:188-204` | 100.0% | DELETE_FROM_POLICIES |
| D701 | CLASS | general | `L5_ui/engines/rollout_projection.py:class GovernanceCompletionReport:216-234` | policies | `L5_engines/rollout_projection.py:class GovernanceCompletionReport:208-226` | 100.0% | DELETE_FROM_POLICIES |
| D702 | CLASS | general | `L5_ui/engines/rollout_projection.py:class CustomerRolloutView:238-252` | policies | `L5_engines/rollout_projection.py:class CustomerRolloutView:230-244` | 100.0% | DELETE_FROM_POLICIES |
| D703 | CLASS | general | `L5_ui/engines/rollout_projection.py:class RolloutProjectionService:260-649` | policies | `L5_engines/rollout_projection.py:class RolloutProjectionService:252-641` | 100.0% | DELETE_FROM_POLICIES |
| D704 | CLASS | general | `L4_runtime/engines/constraint_checker.py:class InspectionOperation:47-53` | general | `L5_engines/constraint_checker.py:class InspectionOperation:46-52` | 100.0% | DELETE_FROM_GENERAL |
| D705 | CLASS | general | `L4_runtime/engines/constraint_checker.py:class InspectionConstraintViolation:66-86` | general | `L5_engines/constraint_checker.py:class InspectionConstraintViolation:65-85` | 100.0% | DELETE_FROM_GENERAL |
| D706 | CLASS | general | `L4_runtime/engines/constraint_checker.py:class InspectionConstraintChecker:89-251` | general | `L5_engines/constraint_checker.py:class InspectionConstraintChecker:88-250` | 100.0% | DELETE_FROM_GENERAL |
| D707 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class HealthLookup:93-98` | policies | `L5_engines/governance_orchestrator.py:class HealthLookup:93-98` | 100.0% | DELETE_FROM_POLICIES |
| D708 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class JobState:107-130` | policies | `L5_engines/governance_orchestrator.py:class JobState:107-130` | 100.0% | DELETE_FROM_POLICIES |
| D709 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class JobStateMachine:138-250` | policies | `L5_engines/governance_orchestrator.py:class JobStateMachine:138-250` | 100.0% | DELETE_FROM_POLICIES |
| D710 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class ExecutionOrchestrator:258-332` | policies | `L5_engines/governance_orchestrator.py:class ExecutionOrchestrator:258-332` | 100.0% | DELETE_FROM_POLICIES |
| D711 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class JobStateTracker:340-420` | policies | `L5_engines/governance_orchestrator.py:class JobStateTracker:340-420` | 100.0% | DELETE_FROM_POLICIES |
| D712 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class AuditEvidence:429-444` | policies | `L5_engines/governance_orchestrator.py:class AuditEvidence:429-444` | 100.0% | DELETE_FROM_POLICIES |
| D713 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class AuditTrigger:447-493` | policies | `L5_engines/governance_orchestrator.py:class AuditTrigger:447-493` | 100.0% | DELETE_FROM_POLICIES |
| D714 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class ContractActivationError:501-507` | policies | `L5_engines/governance_orchestrator.py:class ContractActivationError:501-507` | 100.0% | DELETE_FROM_POLICIES |
| D715 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class ContractActivationService:510-621` | policies | `L5_engines/governance_orchestrator.py:class ContractActivationService:510-621` | 100.0% | DELETE_FROM_POLICIES |
| D716 | CLASS | general | `L4_runtime/engines/governance_orchestrator.py:class GovernanceOrchestrator:629-807` | policies | `L5_engines/governance_orchestrator.py:class GovernanceOrchestrator:629-807` | 100.0% | DELETE_FROM_POLICIES |
| D717 | CLASS | general | `L4_runtime/engines/phase_status_invariants.py:class InvariantCheckResult:47-53` | policies | `L5_engines/phase_status_invariants.py:class InvariantCheckResult:46-52` | 100.0% | DELETE_FROM_POLICIES |
| D718 | CLASS | general | `L4_runtime/engines/phase_status_invariants.py:class PhaseStatusInvariantEnforcementError:68-99` | policies | `L5_engines/phase_status_invariants.py:class PhaseStatusInvariantEnforcementError:67-98` | 100.0% | DELETE_FROM_POLICIES |
| D719 | CLASS | general | `L4_runtime/engines/phase_status_invariants.py:class InvariantCheckResponse:103-124` | policies | `L5_engines/phase_status_invariants.py:class InvariantCheckResponse:102-123` | 100.0% | DELETE_FROM_POLICIES |
| D720 | CLASS | general | `L4_runtime/engines/phase_status_invariants.py:class PhaseStatusInvariantChecker:127-321` | policies | `L5_engines/phase_status_invariants.py:class PhaseStatusInvariantChecker:126-320` | 100.0% | DELETE_FROM_POLICIES |
| D721 | CLASS | general | `L4_runtime/engines/plan_generation_engine.py:class PlanGenerationContext:62-68` | policies | `L5_engines/plan_generation_engine.py:class PlanGenerationContext:55-61` | 100.0% | DELETE_FROM_POLICIES |
| D722 | CLASS | general | `L4_runtime/engines/plan_generation_engine.py:class PlanGenerationResult:72-81` | policies | `L5_engines/plan_generation_engine.py:class PlanGenerationResult:65-74` | 100.0% | DELETE_FROM_POLICIES |
| D723 | CLASS | general | `L4_runtime/engines/plan_generation_engine.py:class PlanGenerationEngine:89-210` | policies | `L5_engines/plan_generation_engine.py:class PlanGenerationEngine:82-203` | 100.0% | DELETE_FROM_POLICIES |
| D724 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class HealthObserver:79-96` | policies | `L5_engines/job_executor.py:class HealthObserver:86-103` | 100.0% | DELETE_FROM_POLICIES |
| D725 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class StepHandler:99-122` | policies | `L5_engines/job_executor.py:class StepHandler:106-129` | 100.0% | DELETE_FROM_POLICIES |
| D726 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class StepOutput:131-141` | policies | `L5_engines/job_executor.py:class StepOutput:138-148` | 100.0% | DELETE_FROM_POLICIES |
| D727 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class ExecutionContext:145-159` | policies | `L5_engines/job_executor.py:class ExecutionContext:152-166` | 100.0% | DELETE_FROM_POLICIES |
| D728 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class ExecutionResult:163-180` | policies | `L5_engines/job_executor.py:class ExecutionResult:170-187` | 100.0% | DELETE_FROM_POLICIES |
| D729 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class JobExecutor:188-406` | policies | `L5_engines/job_executor.py:class JobExecutor:195-413` | 100.0% | DELETE_FROM_POLICIES |
| D730 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class NoOpHandler:414-431` | policies | `L5_engines/job_executor.py:class NoOpHandler:421-438` | 100.0% | DELETE_FROM_POLICIES |
| D731 | CLASS | general | `L5_support/CRM/engines/job_executor.py:class FailingHandler:434-450` | policies | `L5_engines/job_executor.py:class FailingHandler:441-457` | 100.0% | DELETE_FROM_POLICIES |
| D732 | CLASS | general | `L5_schemas/rac_models.py:class AuditStatus:43-49` | logs | `L5_schemas/audit_models.py:class AuditStatus:35-41` | 100.0% | DELETE_FROM_LOGS |
| D733 | CLASS | general | `L5_schemas/rac_models.py:class AuditStatus:43-49` | logs | `L5_schemas/models.py:class AuditStatus:35-41` | 100.0% | DELETE_FROM_LOGS |
| D734 | CLASS | logs | `L5_schemas/audit_models.py:class AuditStatus:35-41` | logs | `L5_schemas/models.py:class AuditStatus:35-41` | 100.0% | EXTRACT_TO_GENERAL |
| D735 | CLASS | general | `L5_schemas/rac_models.py:class AuditDomain:52-58` | logs | `L5_schemas/audit_models.py:class AuditDomain:44-50` | 100.0% | DELETE_FROM_LOGS |
| D736 | CLASS | general | `L5_schemas/rac_models.py:class AuditDomain:52-58` | logs | `L5_schemas/models.py:class AuditDomain:44-50` | 100.0% | DELETE_FROM_LOGS |
| D737 | CLASS | logs | `L5_schemas/audit_models.py:class AuditDomain:44-50` | logs | `L5_schemas/models.py:class AuditDomain:44-50` | 100.0% | EXTRACT_TO_GENERAL |
| D738 | CLASS | general | `L5_schemas/rac_models.py:class AuditAction:61-75` | logs | `L5_schemas/audit_models.py:class AuditAction:53-67` | 100.0% | DELETE_FROM_LOGS |
| D739 | CLASS | general | `L5_schemas/rac_models.py:class AuditAction:61-75` | logs | `L5_schemas/models.py:class AuditAction:53-67` | 100.0% | DELETE_FROM_LOGS |
| D740 | CLASS | logs | `L5_schemas/audit_models.py:class AuditAction:53-67` | logs | `L5_schemas/models.py:class AuditAction:53-67` | 100.0% | EXTRACT_TO_GENERAL |
| D741 | CLASS | general | `L5_schemas/rac_models.py:class AuditExpectation:79-139` | logs | `L5_schemas/audit_models.py:class AuditExpectation:71-131` | 100.0% | DELETE_FROM_LOGS |
| D742 | CLASS | general | `L5_schemas/rac_models.py:class AuditExpectation:79-139` | logs | `L5_schemas/models.py:class AuditExpectation:71-131` | 100.0% | DELETE_FROM_LOGS |
| D743 | CLASS | logs | `L5_schemas/audit_models.py:class AuditExpectation:71-131` | logs | `L5_schemas/models.py:class AuditExpectation:71-131` | 100.0% | EXTRACT_TO_GENERAL |
| D744 | CLASS | general | `L5_schemas/rac_models.py:class AckStatus:142-147` | logs | `L5_schemas/audit_models.py:class AckStatus:134-139` | 100.0% | DELETE_FROM_LOGS |
| D745 | CLASS | general | `L5_schemas/rac_models.py:class AckStatus:142-147` | logs | `L5_schemas/models.py:class AckStatus:134-139` | 100.0% | DELETE_FROM_LOGS |
| D746 | CLASS | logs | `L5_schemas/audit_models.py:class AckStatus:134-139` | logs | `L5_schemas/models.py:class AckStatus:134-139` | 100.0% | EXTRACT_TO_GENERAL |
| D747 | CLASS | general | `L5_schemas/rac_models.py:class DomainAck:151-229` | logs | `L5_schemas/audit_models.py:class DomainAck:143-221` | 100.0% | DELETE_FROM_LOGS |
| D748 | CLASS | general | `L5_schemas/rac_models.py:class DomainAck:151-229` | logs | `L5_schemas/models.py:class DomainAck:143-221` | 100.0% | DELETE_FROM_LOGS |
| D749 | CLASS | logs | `L5_schemas/audit_models.py:class DomainAck:143-221` | logs | `L5_schemas/models.py:class DomainAck:143-221` | 100.0% | EXTRACT_TO_GENERAL |
| D750 | CLASS | general | `L5_schemas/rac_models.py:class ReconciliationResult:233-296` | logs | `L5_schemas/audit_models.py:class ReconciliationResult:225-288` | 100.0% | DELETE_FROM_LOGS |
| D751 | CLASS | general | `L5_schemas/rac_models.py:class ReconciliationResult:233-296` | logs | `L5_schemas/models.py:class ReconciliationResult:225-288` | 100.0% | DELETE_FROM_LOGS |
| D752 | CLASS | logs | `L5_schemas/audit_models.py:class ReconciliationResult:225-288` | logs | `L5_schemas/models.py:class ReconciliationResult:225-288` | 100.0% | EXTRACT_TO_GENERAL |
| D754 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgePlaneStatus:36-45` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgePlaneStatus:35-44` | 100.0% | DELETE_FROM_GENERAL |
| D755 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgeNodeType:48-57` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgeNodeType:47-56` | 100.0% | DELETE_FROM_GENERAL |
| D756 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgeNode:61-112` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgeNode:60-111` | 100.0% | DELETE_FROM_GENERAL |
| D757 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgePlane:116-257` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgePlane:115-256` | 100.0% | DELETE_FROM_GENERAL |
| D758 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgePlaneError:260-277` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgePlaneError:259-276` | 100.0% | DELETE_FROM_GENERAL |
| D759 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgePlaneStats:281-302` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgePlaneStats:280-301` | 100.0% | DELETE_FROM_GENERAL |
| D760 | CLASS | general | `L6_drivers/knowledge_plane.py:class KnowledgePlaneRegistry:305-434` | general | `L5_lifecycle/drivers/knowledge_plane.py:class KnowledgePlaneRegistry:304-433` | 100.0% | DELETE_FROM_GENERAL |
| D761 | CLASS | general | `L5_lifecycle/drivers/execution.py:class IngestionSourceType:65-71` | integrations | `L6_drivers/execution.py:class IngestionSourceType:66-72` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D762 | CLASS | general | `L5_lifecycle/drivers/execution.py:class IngestionBatch:75-92` | integrations | `L6_drivers/execution.py:class IngestionBatch:76-93` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D763 | CLASS | general | `L5_lifecycle/drivers/execution.py:class IngestionResult:96-118` | integrations | `L6_drivers/execution.py:class IngestionResult:97-119` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D764 | CLASS | general | `L5_lifecycle/drivers/execution.py:class DataIngestionExecutor:121-618` | integrations | `L6_drivers/execution.py:class DataIngestionExecutor:122-619` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D765 | CLASS | general | `L5_lifecycle/drivers/execution.py:class IndexingResult:626-646` | integrations | `L6_drivers/execution.py:class IndexingResult:627-647` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D766 | CLASS | general | `L5_lifecycle/drivers/execution.py:class IndexingExecutor:649-936` | integrations | `L6_drivers/execution.py:class IndexingExecutor:650-937` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D767 | CLASS | general | `L5_lifecycle/drivers/execution.py:class SensitivityLevel:943-948` | integrations | `L6_drivers/execution.py:class SensitivityLevel:944-949` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D768 | CLASS | general | `L5_lifecycle/drivers/execution.py:class PIIType:951-962` | integrations | `L6_drivers/execution.py:class PIIType:952-963` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D769 | CLASS | general | `L5_lifecycle/drivers/execution.py:class PIIDetection:966-971` | integrations | `L6_drivers/execution.py:class PIIDetection:967-972` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D770 | CLASS | general | `L5_lifecycle/drivers/execution.py:class ClassificationResult:975-999` | integrations | `L6_drivers/execution.py:class ClassificationResult:976-1000` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D771 | CLASS | general | `L5_lifecycle/drivers/execution.py:class ClassificationExecutor:1002-1275` | integrations | `L6_drivers/execution.py:class ClassificationExecutor:1003-1276` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D772 | CLASS | general | `L5_lifecycle/engines/base.py:class StageStatus:47-52` | general | `L5_engines/lifecycle_stages_base.py:class StageStatus:47-52` | 100.0% | DELETE_FROM_GENERAL |
| D773 | CLASS | general | `L5_lifecycle/engines/base.py:class StageContext:56-79` | general | `L5_engines/lifecycle_stages_base.py:class StageContext:56-79` | 100.0% | DELETE_FROM_GENERAL |
| D774 | CLASS | general | `L5_lifecycle/engines/base.py:class StageResult:83-155` | general | `L5_engines/lifecycle_stages_base.py:class StageResult:83-155` | 100.0% | DELETE_FROM_GENERAL |
| D775 | CLASS | general | `L5_lifecycle/engines/base.py:class StageHandler:159-211` | general | `L5_engines/lifecycle_stages_base.py:class StageHandler:159-211` | 100.0% | DELETE_FROM_GENERAL |
| D776 | CLASS | general | `L5_lifecycle/engines/base.py:class BaseStageHandler:214-250` | general | `L5_engines/lifecycle_stages_base.py:class BaseStageHandler:214-250` | 100.0% | DELETE_FROM_GENERAL |
| D777 | CLASS | general | `L5_lifecycle/engines/base.py:class StageRegistry:253-317` | general | `L5_engines/lifecycle_stages_base.py:class StageRegistry:253-317` | 100.0% | DELETE_FROM_GENERAL |
| D778 | CLASS | general | `L5_engines/alert_log_linker.py:class AlertLogLinkType:51-60` | incidents | `L5_engines/alert_log_linker.py:class AlertLogLinkType:50-59` | 100.0% | DELETE_FROM_INCIDENTS |
| D779 | CLASS | general | `L5_engines/alert_log_linker.py:class AlertLogLinkStatus:63-69` | incidents | `L5_engines/alert_log_linker.py:class AlertLogLinkStatus:62-68` | 100.0% | DELETE_FROM_INCIDENTS |
| D780 | CLASS | general | `L5_engines/alert_log_linker.py:class AlertLogLinkError:72-103` | incidents | `L5_engines/alert_log_linker.py:class AlertLogLinkError:71-102` | 100.0% | DELETE_FROM_INCIDENTS |
| D781 | CLASS | general | `L5_engines/alert_log_linker.py:class AlertLogLink:107-196` | incidents | `L5_engines/alert_log_linker.py:class AlertLogLink:106-195` | 100.0% | DELETE_FROM_INCIDENTS |
| D782 | CLASS | general | `L5_engines/alert_log_linker.py:class AlertLogLinkResponse:200-215` | incidents | `L5_engines/alert_log_linker.py:class AlertLogLinkResponse:199-214` | 100.0% | DELETE_FROM_INCIDENTS |
| D783 | CLASS | general | `L5_engines/alert_log_linker.py:class AlertLogLinker:218-673` | incidents | `L5_engines/alert_log_linker.py:class AlertLogLinker:217-672` | 100.0% | DELETE_FROM_INCIDENTS |
| D784 | CLASS | general | `L5_engines/audit_durability.py:class DurabilityCheckResult:44-50` | general | `L5_engines/durability.py:class DurabilityCheckResult:44-50` | 100.0% | DELETE_FROM_GENERAL |
| D785 | CLASS | general | `L5_engines/audit_durability.py:class RACDurabilityEnforcementError:53-81` | general | `L5_engines/durability.py:class RACDurabilityEnforcementError:53-81` | 100.0% | DELETE_FROM_GENERAL |
| D786 | CLASS | general | `L5_engines/audit_durability.py:class DurabilityCheckResponse:85-102` | general | `L5_engines/durability.py:class DurabilityCheckResponse:85-102` | 100.0% | DELETE_FROM_GENERAL |
| D787 | CLASS | general | `L5_engines/audit_durability.py:class RACDurabilityChecker:105-281` | general | `L5_engines/durability.py:class RACDurabilityChecker:105-281` | 100.0% | DELETE_FROM_GENERAL |
| D788 | CLASS | general | `L5_engines/audit_store.py:class StoreDurabilityMode:64-68` | logs | `L6_drivers/audit_store.py:class StoreDurabilityMode:71-75` | 100.0% | DELETE_FROM_LOGS |
| D789 | CLASS | general | `L5_engines/audit_store.py:class StoreDurabilityMode:64-68` | logs | `L6_drivers/store.py:class StoreDurabilityMode:70-74` | 100.0% | DELETE_FROM_LOGS |
| D790 | CLASS | logs | `L6_drivers/audit_store.py:class StoreDurabilityMode:71-75` | logs | `L6_drivers/store.py:class StoreDurabilityMode:70-74` | 100.0% | EXTRACT_TO_GENERAL |
| D791 | CLASS | general | `L5_engines/audit_store.py:class RACDurabilityError:71-74` | logs | `L6_drivers/audit_store.py:class RACDurabilityError:78-81` | 100.0% | DELETE_FROM_LOGS |
| D792 | CLASS | general | `L5_engines/audit_store.py:class RACDurabilityError:71-74` | logs | `L6_drivers/store.py:class RACDurabilityError:77-80` | 100.0% | DELETE_FROM_LOGS |
| D793 | CLASS | logs | `L6_drivers/audit_store.py:class RACDurabilityError:78-81` | logs | `L6_drivers/store.py:class RACDurabilityError:77-80` | 100.0% | EXTRACT_TO_GENERAL |
| D794 | CLASS | general | `L5_engines/audit_store.py:class AuditStore:103-425` | logs | `L6_drivers/audit_store.py:class AuditStore:110-432` | 100.0% | DELETE_FROM_LOGS |
| D795 | CLASS | general | `L5_engines/audit_store.py:class AuditStore:103-425` | logs | `L6_drivers/store.py:class AuditStore:109-431` | 100.0% | DELETE_FROM_LOGS |
| D796 | CLASS | logs | `L6_drivers/audit_store.py:class AuditStore:110-432` | logs | `L6_drivers/store.py:class AuditStore:109-431` | 100.0% | EXTRACT_TO_GENERAL |
| D797 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceScope:63-69` | logs | `L5_engines/compliance_facade.py:class ComplianceScope:60-66` | 100.0% | DELETE_FROM_LOGS |
| D798 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceStatus:72-77` | logs | `L5_engines/compliance_facade.py:class ComplianceStatus:69-74` | 100.0% | DELETE_FROM_LOGS |
| D799 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceRule:81-99` | logs | `L5_engines/compliance_facade.py:class ComplianceRule:78-96` | 100.0% | DELETE_FROM_LOGS |
| D800 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceViolation:103-119` | logs | `L5_engines/compliance_facade.py:class ComplianceViolation:100-116` | 100.0% | DELETE_FROM_LOGS |
| D801 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceReport:123-151` | logs | `L5_engines/compliance_facade.py:class ComplianceReport:120-148` | 100.0% | DELETE_FROM_LOGS |
| D802 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceStatusInfo:155-171` | logs | `L5_engines/compliance_facade.py:class ComplianceStatusInfo:152-168` | 100.0% | DELETE_FROM_LOGS |
| D803 | CLASS | general | `L5_engines/compliance_facade.py:class ComplianceFacade:174-495` | logs | `L5_engines/compliance_facade.py:class ComplianceFacade:171-492` | 100.0% | DELETE_FROM_LOGS |
| D804 | CLASS | general | `L5_engines/control_registry.py:class SOC2Category:52-59` | logs | `L5_engines/control_registry.py:class SOC2Category:51-58` | 100.0% | DELETE_FROM_LOGS |
| D805 | CLASS | general | `L5_engines/control_registry.py:class SOC2ComplianceStatus:62-69` | logs | `L5_engines/control_registry.py:class SOC2ComplianceStatus:61-68` | 100.0% | DELETE_FROM_LOGS |
| D806 | CLASS | general | `L5_engines/control_registry.py:class SOC2Control:73-99` | logs | `L5_engines/control_registry.py:class SOC2Control:72-98` | 100.0% | DELETE_FROM_LOGS |
| D807 | CLASS | general | `L5_engines/control_registry.py:class SOC2ControlMapping:103-133` | logs | `L5_engines/control_registry.py:class SOC2ControlMapping:102-132` | 100.0% | DELETE_FROM_LOGS |
| D808 | CLASS | general | `L5_engines/control_registry.py:class SOC2ControlRegistry:136-443` | logs | `L5_engines/control_registry.py:class SOC2ControlRegistry:135-442` | 100.0% | DELETE_FROM_LOGS |
| D809 | CLASS | general | `L5_engines/cus_credential_service.py:class CusCredentialService:55-477` | integrations | `L5_vault/engines/cus_credential_engine.py:class CusCredentialService:58-480` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D810 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueMode:37-43` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueMode:37-43` | 100.0% | DELETE_FROM_POLICIES |
| D811 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueAction:46-54` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueAction:46-54` | 100.0% | DELETE_FROM_POLICIES |
| D812 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueConfig:58-92` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueConfig:58-92` | 100.0% | DELETE_FROM_POLICIES |
| D813 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueState:96-253` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueState:96-253` | 100.0% | DELETE_FROM_POLICIES |
| D814 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueStats:257-301` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueStats:257-301` | 100.0% | DELETE_FROM_POLICIES |
| D815 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueError:304-324` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueError:304-324` | 100.0% | DELETE_FROM_POLICIES |
| D816 | CLASS | general | `L5_engines/fatigue_controller.py:class FatigueCheckResult:328-348` | policies | `L5_engines/fatigue_controller.py:class FatigueCheckResult:328-348` | 100.0% | DELETE_FROM_POLICIES |
| D817 | CLASS | general | `L5_engines/fatigue_controller.py:class AlertFatigueController:351-688` | policies | `L5_engines/fatigue_controller.py:class AlertFatigueController:351-688` | 100.0% | DELETE_FROM_POLICIES |
| D818 | CLASS | general | `L5_engines/lifecycle_facade.py:class AgentState:69-77` | general | `L5_engines/lifecycle/lifecycle_facade.py:class AgentState:64-72` | 100.0% | DELETE_FROM_GENERAL |
| D819 | CLASS | general | `L5_engines/lifecycle_facade.py:class AgentLifecycle:91-119` | general | `L5_engines/lifecycle/lifecycle_facade.py:class AgentLifecycle:86-114` | 100.0% | DELETE_FROM_GENERAL |
| D820 | CLASS | general | `L5_engines/lifecycle_facade.py:class RunLifecycle:123-157` | general | `L5_engines/lifecycle/lifecycle_facade.py:class RunLifecycle:118-152` | 100.0% | DELETE_FROM_GENERAL |
| D821 | CLASS | general | `L5_engines/lifecycle_facade.py:class LifecycleSummary:161-187` | general | `L5_engines/lifecycle/lifecycle_facade.py:class LifecycleSummary:156-182` | 100.0% | DELETE_FROM_GENERAL |
| D822 | CLASS | general | `L5_engines/lifecycle_facade.py:class LifecycleFacade:190-686` | general | `L5_engines/lifecycle/lifecycle_facade.py:class LifecycleFacade:185-681` | 100.0% | DELETE_FROM_GENERAL |
| D823 | CLASS | general | `L5_engines/monitors_facade.py:class MonitorType:67-73` | integrations | `L5_engines/monitors_facade.py:class MonitorType:64-70` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D824 | CLASS | general | `L5_engines/monitors_facade.py:class MonitorStatus:76-81` | integrations | `L5_engines/monitors_facade.py:class MonitorStatus:73-78` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D825 | CLASS | general | `L5_engines/monitors_facade.py:class CheckStatus:84-89` | integrations | `L5_engines/monitors_facade.py:class CheckStatus:81-86` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D826 | CLASS | general | `L5_engines/monitors_facade.py:class MonitorConfig:93-129` | integrations | `L5_engines/monitors_facade.py:class MonitorConfig:90-126` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D827 | CLASS | general | `L5_engines/monitors_facade.py:class HealthCheckResult:133-155` | integrations | `L5_engines/monitors_facade.py:class HealthCheckResult:130-152` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D828 | CLASS | general | `L5_engines/monitors_facade.py:class MonitorStatusSummary:159-177` | integrations | `L5_engines/monitors_facade.py:class MonitorStatusSummary:156-174` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D829 | CLASS | general | `L5_engines/monitors_facade.py:class MonitorsFacade:180-518` | integrations | `L5_engines/monitors_facade.py:class MonitorsFacade:177-515` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D830 | CLASS | general | `L5_engines/retrieval_facade.py:class AccessResult:67-93` | integrations | `L5_engines/retrieval_facade.py:class AccessResult:69-95` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D831 | CLASS | general | `L5_engines/retrieval_facade.py:class PlaneInfo:97-115` | integrations | `L5_engines/retrieval_facade.py:class PlaneInfo:99-117` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D832 | CLASS | general | `L5_engines/retrieval_facade.py:class EvidenceInfo:119-145` | integrations | `L5_engines/retrieval_facade.py:class EvidenceInfo:121-147` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D833 | CLASS | general | `L5_engines/retrieval_facade.py:class RetrievalFacade:148-495` | integrations | `L5_engines/retrieval_facade.py:class RetrievalFacade:150-497` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D834 | CLASS | general | `L5_engines/retrieval_mediator.py:class MediationAction:59-64` | integrations | `L5_engines/retrieval_mediator.py:class MediationAction:60-65` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D835 | CLASS | general | `L5_engines/retrieval_mediator.py:class MediatedResult:68-78` | integrations | `L5_engines/retrieval_mediator.py:class MediatedResult:69-79` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D836 | CLASS | general | `L5_engines/retrieval_mediator.py:class PolicyCheckResult:82-87` | integrations | `L5_engines/retrieval_mediator.py:class PolicyCheckResult:83-88` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D837 | CLASS | general | `L5_engines/retrieval_mediator.py:class EvidenceRecord:91-102` | integrations | `L5_engines/retrieval_mediator.py:class EvidenceRecord:92-103` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D838 | CLASS | general | `L5_engines/retrieval_mediator.py:class MediationDeniedError:105-119` | integrations | `L5_engines/retrieval_mediator.py:class MediationDeniedError:106-120` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D839 | CLASS | general | `L5_engines/retrieval_mediator.py:class Connector:123-129` | integrations | `L5_engines/retrieval_mediator.py:class Connector:124-130` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D840 | CLASS | general | `L5_engines/retrieval_mediator.py:class ConnectorRegistry:133-142` | integrations | `L5_engines/retrieval_mediator.py:class ConnectorRegistry:134-143` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D841 | CLASS | general | `L5_engines/retrieval_mediator.py:class PolicyChecker:146-157` | integrations | `L5_engines/retrieval_mediator.py:class PolicyChecker:147-158` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D842 | CLASS | general | `L5_engines/retrieval_mediator.py:class EvidenceService:161-177` | integrations | `L5_engines/retrieval_mediator.py:class EvidenceService:162-178` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D843 | CLASS | general | `L5_engines/retrieval_mediator.py:class RetrievalMediator:180-424` | integrations | `L5_engines/retrieval_mediator.py:class RetrievalMediator:181-425` | 100.0% | DELETE_FROM_INTEGRATIONS |
| D844 | CLASS | incidents | `L5_engines/hallucination_detector.py:class HallucinationType:56-75` | policies | `L5_engines/hallucination_detector.py:class HallucinationType:55-74` | 100.0% | EXTRACT_TO_GENERAL |
| D845 | CLASS | incidents | `L5_engines/hallucination_detector.py:class HallucinationSeverity:78-84` | policies | `L5_engines/hallucination_detector.py:class HallucinationSeverity:77-83` | 100.0% | EXTRACT_TO_GENERAL |
| D846 | CLASS | incidents | `L5_engines/hallucination_detector.py:class HallucinationIndicator:88-112` | policies | `L5_engines/hallucination_detector.py:class HallucinationIndicator:87-111` | 100.0% | EXTRACT_TO_GENERAL |
| D847 | CLASS | incidents | `L5_engines/hallucination_detector.py:class HallucinationResult:116-163` | policies | `L5_engines/hallucination_detector.py:class HallucinationResult:115-162` | 100.0% | EXTRACT_TO_GENERAL |
| D848 | CLASS | incidents | `L5_engines/hallucination_detector.py:class HallucinationConfig:167-192` | policies | `L5_engines/hallucination_detector.py:class HallucinationConfig:166-191` | 100.0% | EXTRACT_TO_GENERAL |
| D849 | CLASS | incidents | `L5_engines/hallucination_detector.py:class HallucinationDetector:195-441` | policies | `L5_engines/hallucination_detector.py:class HallucinationDetector:194-440` | 100.0% | EXTRACT_TO_GENERAL |
| D850 | CLASS | integrations | `L5_vault/engines/service.py:class CredentialAccessRecord:45-55` | integrations | `L5_engines/service.py:class CredentialAccessRecord:44-54` | 100.0% | EXTRACT_TO_GENERAL |
| D851 | CLASS | integrations | `L5_vault/engines/service.py:class CredentialService:58-551` | integrations | `L5_engines/service.py:class CredentialService:57-550` | 100.0% | EXTRACT_TO_GENERAL |
| D852 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyChannel:49-57` | integrations | `L5_engines/channel_engine.py:class NotifyChannel:54-62` | 100.0% | EXTRACT_TO_GENERAL |
| D853 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyEventType:60-72` | integrations | `L5_engines/channel_engine.py:class NotifyEventType:65-77` | 100.0% | EXTRACT_TO_GENERAL |
| D854 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyChannelStatus:75-81` | integrations | `L5_engines/channel_engine.py:class NotifyChannelStatus:80-86` | 100.0% | EXTRACT_TO_GENERAL |
| D855 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyChannelError:84-112` | integrations | `L5_engines/channel_engine.py:class NotifyChannelError:89-117` | 100.0% | EXTRACT_TO_GENERAL |
| D856 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyDeliveryResult:116-141` | integrations | `L5_engines/channel_engine.py:class NotifyDeliveryResult:121-146` | 100.0% | EXTRACT_TO_GENERAL |
| D857 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyChannelConfig:145-228` | integrations | `L5_engines/channel_engine.py:class NotifyChannelConfig:150-233` | 100.0% | EXTRACT_TO_GENERAL |
| D858 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyChannelConfigResponse:232-249` | integrations | `L5_engines/channel_engine.py:class NotifyChannelConfigResponse:237-254` | 100.0% | EXTRACT_TO_GENERAL |
| D859 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotificationSender:252-262` | integrations | `L5_engines/channel_engine.py:class NotificationSender:257-267` | 100.0% | EXTRACT_TO_GENERAL |
| D860 | CLASS | integrations | `L5_notifications/engines/channel_engine.py:class NotifyChannelService:265-1025` | integrations | `L5_engines/channel_engine.py:class NotifyChannelService:270-1030` | 100.0% | EXTRACT_TO_GENERAL |
| D861 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpToolDefinition:77-85` | policies | `L5_engines/mcp_connector.py:class McpToolDefinition:71-79` | 100.0% | EXTRACT_TO_GENERAL |
| D862 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpConnectorConfig:89-100` | policies | `L5_engines/mcp_connector.py:class McpConnectorConfig:83-94` | 100.0% | EXTRACT_TO_GENERAL |
| D863 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpConnectorError:110-115` | policies | `L5_engines/mcp_connector.py:class McpConnectorError:113-118` | 100.0% | EXTRACT_TO_GENERAL |
| D864 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpApprovalRequiredError:118-123` | policies | `L5_engines/mcp_connector.py:class McpApprovalRequiredError:121-126` | 100.0% | EXTRACT_TO_GENERAL |
| D865 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpRateLimitExceededError:126-131` | policies | `L5_engines/mcp_connector.py:class McpRateLimitExceededError:129-134` | 100.0% | EXTRACT_TO_GENERAL |
| D866 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpSchemaValidationError:134-139` | policies | `L5_engines/mcp_connector.py:class McpSchemaValidationError:137-142` | 100.0% | EXTRACT_TO_GENERAL |
| D867 | CLASS | integrations | `L5_engines/mcp_connector.py:class McpConnectorService:142-423` | policies | `L5_engines/mcp_connector.py:class McpConnectorService:145-426` | 100.0% | EXTRACT_TO_GENERAL |
| D868 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class CheckResult:75-80` | logs | `L5_engines/audit_engine.py:class CheckResult:75-80` | 100.0% | EXTRACT_TO_GENERAL |
| D869 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class AuditCheck:89-101` | logs | `L5_engines/audit_engine.py:class AuditCheck:89-101` | 100.0% | EXTRACT_TO_GENERAL |
| D870 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class AuditInput:105-126` | logs | `L5_engines/audit_engine.py:class AuditInput:105-126` | 100.0% | EXTRACT_TO_GENERAL |
| D871 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class AuditResult:130-151` | logs | `L5_engines/audit_engine.py:class AuditResult:130-151` | 100.0% | EXTRACT_TO_GENERAL |
| D872 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class AuditChecks:159-568` | logs | `L5_engines/audit_engine.py:class AuditChecks:159-568` | 100.0% | EXTRACT_TO_GENERAL |
| D873 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class AuditService:576-725` | logs | `L5_engines/audit_engine.py:class AuditService:576-725` | 100.0% | EXTRACT_TO_GENERAL |
| D874 | CLASS | logs | `L5_support/CRM/engines/audit_engine.py:class RolloutGate:733-795` | logs | `L5_engines/audit_engine.py:class RolloutGate:733-795` | 100.0% | EXTRACT_TO_GENERAL |
| D875 | CLASS | logs | `L5_engines/audit_reconciler.py:class AuditReconciler:96-299` | logs | `L5_engines/reconciler.py:class AuditReconciler:95-298` | 100.0% | EXTRACT_TO_GENERAL |
| D876 | CLASS | logs | `L5_engines/completeness_checker.py:class CompletenessCheckResult:47-53` | logs | `L5_engines/export_completeness_checker.py:class CompletenessCheckResult:47-53` | 100.0% | EXTRACT_TO_GENERAL |
| D877 | CLASS | logs | `L5_engines/completeness_checker.py:class EvidenceCompletenessError:89-117` | logs | `L5_engines/export_completeness_checker.py:class EvidenceCompletenessError:89-117` | 100.0% | EXTRACT_TO_GENERAL |
| D878 | CLASS | logs | `L5_engines/completeness_checker.py:class CompletenessCheckResponse:121-144` | logs | `L5_engines/export_completeness_checker.py:class CompletenessCheckResponse:121-144` | 100.0% | EXTRACT_TO_GENERAL |
| D879 | CLASS | logs | `L5_engines/completeness_checker.py:class EvidenceCompletenessChecker:147-468` | logs | `L5_engines/export_completeness_checker.py:class EvidenceCompletenessChecker:147-468` | 100.0% | EXTRACT_TO_GENERAL |
| D880 | CLASS | logs | `L5_engines/mapper.py:class SOC2ControlMapper:91-255` | policies | `L5_engines/mapper.py:class SOC2ControlMapper:91-255` | 100.0% | EXTRACT_TO_GENERAL |
| D881 | CLASS | logs | `L5_engines/replay_determinism.py:class DeterminismLevel:68-89` | policies | `L5_engines/replay_determinism.py:class DeterminismLevel:68-89` | 100.0% | EXTRACT_TO_GENERAL |
| D882 | CLASS | logs | `L5_engines/replay_determinism.py:class ModelVersion:96-125` | policies | `L5_engines/replay_determinism.py:class ModelVersion:96-125` | 100.0% | EXTRACT_TO_GENERAL |
| D883 | CLASS | logs | `L5_engines/replay_determinism.py:class PolicyDecision:129-147` | policies | `L5_engines/replay_determinism.py:class PolicyDecision:129-147` | 100.0% | EXTRACT_TO_GENERAL |
| D884 | CLASS | logs | `L5_engines/replay_determinism.py:class ReplayMatch:153-159` | policies | `L5_engines/replay_determinism.py:class ReplayMatch:153-159` | 100.0% | EXTRACT_TO_GENERAL |
| D885 | CLASS | logs | `L5_engines/replay_determinism.py:class ReplayResult:163-197` | policies | `L5_engines/replay_determinism.py:class ReplayResult:163-197` | 100.0% | EXTRACT_TO_GENERAL |
| D886 | CLASS | logs | `L5_engines/replay_determinism.py:class CallRecord:204-236` | policies | `L5_engines/replay_determinism.py:class CallRecord:204-236` | 100.0% | EXTRACT_TO_GENERAL |
| D887 | CLASS | logs | `L5_engines/replay_determinism.py:class ReplayValidator:242-428` | policies | `L5_engines/replay_determinism.py:class ReplayValidator:242-428` | 100.0% | EXTRACT_TO_GENERAL |
| D888 | CLASS | logs | `L5_engines/replay_determinism.py:class ReplayContextBuilder:434-505` | policies | `L5_engines/replay_determinism.py:class ReplayContextBuilder:434-505` | 100.0% | EXTRACT_TO_GENERAL |
| D670 | CLASS | activity | `L5_engines/threshold_engine.py:class LLMRunEvaluator:305-457` | controls | `L6_drivers/llm_threshold_driver.py:class LLMRunEvaluator:291-441` | 98.7% | EXTRACT_TO_GENERAL |
| D671 | CLASS | activity | `L5_engines/threshold_engine.py:class LLMRunEvaluatorSync:541-612` | controls | `L6_drivers/llm_threshold_driver.py:class LLMRunEvaluatorSync:535-604` | 98.6% | EXTRACT_TO_GENERAL |
| D673 | CLASS | controls | `L6_drivers/circuit_breaker.py:class CircuitBreakerState:96-119` | controls | `L6_drivers/circuit_breaker_async.py:class CircuitBreakerState:91-114` | 95.8% | EXTRACT_TO_GENERAL |
| D560 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:_emit_governance_event():257-279` | general | `L5_engines/runtime_switch.py:_emit_governance_event():253-275` | 95.7% | DELETE_FROM_GENERAL |
| D544 | FUNCTION | controls | `L6_drivers/llm_threshold_driver.py:emit_and_persist_threshold_signal():771-822` | controls | `L6_drivers/threshold_driver.py:emit_and_persist_threshold_signal():327-380` | 94.3% | REVIEW_MERGE |
| D556 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:enter_degraded_mode():167-197` | general | `L5_engines/runtime_switch.py:enter_degraded_mode():163-193` | 93.5% | DELETE_FROM_GENERAL |
| D554 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:disable_governance_runtime():109-138` | general | `L5_engines/runtime_switch.py:disable_governance_runtime():105-134` | 93.3% | DELETE_FROM_GENERAL |
| D555 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:enable_governance_runtime():141-164` | general | `L5_engines/runtime_switch.py:enable_governance_runtime():137-160` | 91.7% | DELETE_FROM_GENERAL |
| D557 | FUNCTION | general | `L5_controls/drivers/runtime_switch.py:exit_degraded_mode():200-223` | general | `L5_engines/runtime_switch.py:exit_degraded_mode():196-219` | 91.7% | DELETE_FROM_GENERAL |
| D669 | CLASS | activity | `L5_engines/threshold_engine.py:class LLMRunThresholdResolver:205-297` | controls | `L6_drivers/llm_threshold_driver.py:class LLMRunThresholdResolver:192-283` | 84.3% | REVIEW_MERGE |
| D648 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationPriority:76-81` | integrations | `L3_adapters/notifications_base.py:class NotificationPriority:29-34` | 83.3% | REVIEW_MERGE |
| D650 | CLASS | integrations | `L3_adapters/notifications_base.py:class NotificationPriority:29-34` | integrations | `L5_engines/notifications_facade.py:class NotificationPriority:72-77` | 83.3% | REVIEW_MERGE |
| D543 | FUNCTION | controls | `L6_drivers/llm_threshold_driver.py:emit_threshold_signal_sync():708-763` | controls | `L6_drivers/threshold_driver.py:emit_threshold_signal_sync():256-324` | 81.6% | REVIEW_MERGE |
| D651 | CLASS | account | `L5_engines/notifications_facade.py:class NotificationStatus:84-90` | integrations | `L3_adapters/notifications_base.py:class NotificationStatus:37-43` | 71.4% | REVIEW_MERGE |
| D653 | CLASS | integrations | `L3_adapters/notifications_base.py:class NotificationStatus:37-43` | integrations | `L5_engines/notifications_facade.py:class NotificationStatus:80-86` | 71.4% | REVIEW_MERGE |
| D753 | CLASS | general | `L5_schemas/skill.py:class HttpMethod:72-81` | integrations | `L5_engines/http_connector.py:class HttpMethod:76-82` | 70.6% | DELETE_FROM_INTEGRATIONS |

---

## Mode 3: Block Similarity Duplicates

| ID | Domain A | File | Domain B | File | Similarity | Recommendation |
|----|----------|------|----------|------|-----------|----------------|
| D903 | logs | `L5_support/CRM/engines/audit_engine.py` | logs | `L5_engines/audit_engine.py` | 99.9% | LIKELY_EXACT_COPY |
| D916 | incidents | `L5_engines/hallucination_detector.py` | policies | `L5_engines/hallucination_detector.py` | 99.6% | LIKELY_EXACT_COPY |
| D920 | logs | `L5_engines/mapper.py` | policies | `L5_engines/mapper.py` | 99.6% | LIKELY_EXACT_COPY |
| D935 | integrations | `L5_vault/engines/service.py` | integrations | `L5_engines/service.py` | 99.5% | LIKELY_EXACT_COPY |
| D913 | general | `L5_engines/fatigue_controller.py` | policies | `L5_engines/fatigue_controller.py` | 99.4% | DELETE_FROM_POLICIES |
| D928 | general | `L5_engines/retrieval_facade.py` | integrations | `L5_engines/retrieval_facade.py` | 99.4% | DELETE_FROM_INTEGRATIONS |
| D929 | general | `L5_engines/retrieval_mediator.py` | integrations | `L5_engines/retrieval_mediator.py` | 99.4% | DELETE_FROM_INTEGRATIONS |
| D901 | general | `L5_engines/alert_log_linker.py` | incidents | `L5_engines/alert_log_linker.py` | 99.0% | DELETE_FROM_INCIDENTS |
| D909 | general | `L5_engines/control_registry.py` | logs | `L5_engines/control_registry.py` | 98.9% | DELETE_FROM_LOGS |
| D912 | general | `L5_lifecycle/drivers/execution.py` | integrations | `L6_drivers/execution.py` | 98.9% | DELETE_FROM_INTEGRATIONS |
| D926 | account | `L5_engines/profile.py` | policies | `L5_engines/profile.py` | 98.9% | LIKELY_EXACT_COPY |
| D905 | integrations | `L5_notifications/engines/channel_engine.py` | integrations | `L5_engines/channel_engine.py` | 98.8% | LIKELY_EXACT_COPY |
| D910 | general | `L5_controls/engines/degraded_mode_checker.py` | general | `L5_engines/degraded_mode_checker.py` | 98.8% | DELETE_FROM_GENERAL |
| D914 | general | `L4_runtime/engines/governance_orchestrator.py` | policies | `L5_engines/governance_orchestrator.py` | 98.8% | DELETE_FROM_POLICIES |
| D930 | general | `L5_ui/engines/rollout_projection.py` | policies | `L5_engines/rollout_projection.py` | 98.7% | DELETE_FROM_POLICIES |
| D902 | controls | `L5_engines/alerts_facade.py` | general | `L5_engines/alerts_facade.py` | 98.6% | DELETE_FROM_CONTROLS |
| D917 | general | `L5_support/CRM/engines/job_executor.py` | policies | `L5_engines/job_executor.py` | 98.5% | DELETE_FROM_POLICIES |
| D919 | general | `L5_engines/lifecycle_facade.py` | general | `L5_engines/lifecycle/lifecycle_facade.py` | 98.5% | DELETE_FROM_GENERAL |
| D906 | general | `L5_engines/compliance_facade.py` | logs | `L5_engines/compliance_facade.py` | 98.4% | DELETE_FROM_LOGS |
| D907 | general | `L4_runtime/engines/constraint_checker.py` | general | `L5_engines/constraint_checker.py` | 98.3% | DELETE_FROM_GENERAL |
| D927 | logs | `L5_engines/replay_determinism.py` | policies | `L5_engines/replay_determinism.py` | 98.3% | LIKELY_EXACT_COPY |
| D908 | general | `L5_workflow/contracts/engines/contract_engine.py` | general | `L5_engines/contract_engine.py` | 98.2% | DELETE_FROM_GENERAL |
| D922 | general | `L5_engines/monitors_facade.py` | integrations | `L5_engines/monitors_facade.py` | 98.1% | DELETE_FROM_INTEGRATIONS |
| D924 | general | `L4_runtime/engines/phase_status_invariants.py` | policies | `L5_engines/phase_status_invariants.py` | 98.1% | DELETE_FROM_POLICIES |
| D936 | account | `L5_support/CRM/engines/validator_engine.py` | policies | `L5_engines/validator_engine.py` | 98.0% | LIKELY_EXACT_COPY |
| D923 | account | `L5_engines/notifications_facade.py` | integrations | `L5_engines/notifications_facade.py` | 97.8% | LIKELY_EXACT_COPY |
| D918 | general | `L6_drivers/knowledge_plane.py` | general | `L5_lifecycle/drivers/knowledge_plane.py` | 97.6% | DELETE_FROM_GENERAL |
| D925 | general | `L4_runtime/engines/plan_generation_engine.py` | policies | `L5_engines/plan_generation_engine.py` | 97.4% | DELETE_FROM_POLICIES |
| D933 | general | `L4_runtime/facades/run_governance_facade.py` | policies | `L5_engines/run_governance_facade.py` | 97.1% | DELETE_FROM_POLICIES |
| D904 | general | `L5_engines/audit_store.py` | logs | `L6_drivers/audit_store.py` | 96.5% | DELETE_FROM_LOGS |
| D932 | activity | `L5_engines/run_governance_facade.py` | policies | `L5_engines/run_governance_facade.py` | 96.3% | LIKELY_EXACT_COPY |
| D921 | integrations | `L5_engines/mcp_connector.py` | policies | `L5_engines/mcp_connector.py` | 96.0% | LIKELY_EXACT_COPY |
| D931 | activity | `L5_engines/run_governance_facade.py` | general | `L4_runtime/facades/run_governance_facade.py` | 96.0% | DELETE_FROM_ACTIVITY |
| D911 | account | `L5_engines/email_verification.py` | api_keys | `L5_engines/email_verification.py` | 95.9% | LIKELY_EXACT_COPY |
| D934 | general | `L5_controls/drivers/runtime_switch.py` | general | `L5_engines/runtime_switch.py` | 91.7% | DELETE_FROM_GENERAL |
| D915 | general | `L5_controls/drivers/guard_write_driver.py` | incidents | `L6_drivers/guard_write_driver.py` | 84.0% | DELETE_FROM_INCIDENTS |

---

## Consolidation Candidates

| ID | Types | Max Sim | Canonical Location | Delete From | Recommendation |
|----|-------|---------|-------------------|-------------|----------------|
| C001 | BLOCK|CLASS|FUNCTION | 100.0% | `general/email_verification.py` | `account/L5_engines/email_verification.py,api_keys/L5_engines/email_verification.py` | EXTRACT_TO_GENERAL |
| C002 | CLASS | 83.3% | `general/notifications_facade.py` | `account/L5_engines/notifications_facade.py,integrations/L3_adapters/notifications_base.py` | REVIEW_MERGE |
| C003 | BLOCK|CLASS|FUNCTION | 100.0% | `general/notifications_facade.py` | `account/L5_engines/notifications_facade.py,integrations/L5_engines/notifications_facade.py` | EXTRACT_TO_GENERAL |
| C004 | BLOCK|CLASS|FUNCTION | 100.0% | `general/profile.py` | `account/L5_engines/profile.py,policies/L5_engines/profile.py` | EXTRACT_TO_GENERAL |
| C005 | BLOCK|CLASS | 100.0% | `general/validator_engine.py` | `account/L5_support/CRM/engines/validator_engine.py,policies/L5_engines/validator_engine.py` | EXTRACT_TO_GENERAL |
| C006 | FUNCTION | 100.0% | `general/user_write_driver.py` | `account/L6_drivers/user_write_driver.py,analytics/L6_drivers/cost_write_driver.py` | EXTRACT_TO_GENERAL |
| C007 | FUNCTION | 100.0% | `general/L5_controls/drivers/guard_write_driver.py` | `account/L6_drivers/user_write_driver.py` | DELETE_FROM_ACCOUNT |
| C008 | FUNCTION | 100.0% | `general/L5_utils/time.py` | `account/L6_drivers/user_write_driver.py` | DELETE_FROM_ACCOUNT |
| C009 | FUNCTION | 100.0% | `general/user_write_driver.py` | `account/L6_drivers/user_write_driver.py,incidents/L6_drivers/guard_write_driver.py` | EXTRACT_TO_GENERAL |
| C010 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L4_runtime/facades/run_governance_facade.py` | `activity/L5_engines/run_governance_facade.py` | DELETE_FROM_ACTIVITY |
| C011 | BLOCK|CLASS|FUNCTION | 100.0% | `general/run_governance_facade.py` | `activity/L5_engines/run_governance_facade.py,policies/L5_engines/run_governance_facade.py` | EXTRACT_TO_GENERAL |
| C012 | CLASS|FUNCTION | 100.0% | `general/threshold_engine.py` | `activity/L5_engines/threshold_engine.py,controls/L6_drivers/llm_threshold_driver.py` | EXTRACT_TO_GENERAL |
| C013 | FUNCTION | 100.0% | `general/L5_controls/drivers/guard_write_driver.py` | `analytics/L6_drivers/cost_write_driver.py` | DELETE_FROM_ANALYTICS |
| C014 | FUNCTION | 100.0% | `general/L5_utils/time.py` | `analytics/L6_drivers/cost_write_driver.py` | DELETE_FROM_ANALYTICS |
| C015 | FUNCTION | 100.0% | `general/cost_write_driver.py` | `analytics/L6_drivers/cost_write_driver.py,incidents/L6_drivers/guard_write_driver.py` | EXTRACT_TO_GENERAL |
| C016 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/alerts_facade.py` | `controls/L5_engines/alerts_facade.py` | DELETE_FROM_CONTROLS |
| C017 | CLASS | 100.0% | `general/circuit_breaker.py` | `controls/L6_drivers/circuit_breaker.py,controls/L6_drivers/circuit_breaker_async.py` | EXTRACT_TO_GENERAL |
| C018 | FUNCTION | 94.3% | `general/llm_threshold_driver.py` | `controls/L6_drivers/llm_threshold_driver.py,controls/L6_drivers/threshold_driver.py` | REVIEW_MERGE |
| C019 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `controls/L6_drivers/override_driver.py` | DELETE_FROM_CONTROLS |
| C020 | FUNCTION | 100.0% | `general/override_driver.py` | `controls/L6_drivers/override_driver.py,policies/L5_engines/policy_limits_engine.py` | EXTRACT_TO_GENERAL |
| C021 | FUNCTION | 100.0% | `general/override_driver.py` | `controls/L6_drivers/override_driver.py,policies/L5_engines/policy_rules_engine.py` | EXTRACT_TO_GENERAL |
| C022 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L4_runtime/engines/constraint_checker.py` | `general/L5_engines/constraint_checker.py` | DELETE_FROM_GENERAL |
| C023 | BLOCK|CLASS | 100.0% | `general/L4_runtime/engines/governance_orchestrator.py` | `policies/L5_engines/governance_orchestrator.py` | DELETE_FROM_POLICIES |
| C024 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L4_runtime/engines/phase_status_invariants.py` | `policies/L5_engines/phase_status_invariants.py` | DELETE_FROM_POLICIES |
| C025 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L4_runtime/engines/plan_generation_engine.py` | `policies/L5_engines/plan_generation_engine.py` | DELETE_FROM_POLICIES |
| C026 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L4_runtime/facades/run_governance_facade.py` | `policies/L5_engines/run_governance_facade.py` | DELETE_FROM_POLICIES |
| C027 | FUNCTION | 100.0% | `general/L5_controls/drivers/guard_write_driver.py` | `general/L5_utils/time.py` | DELETE_FROM_GENERAL |
| C028 | BLOCK|FUNCTION | 100.0% | `general/L5_controls/drivers/guard_write_driver.py` | `incidents/L6_drivers/guard_write_driver.py` | DELETE_FROM_INCIDENTS |
| C029 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_controls/drivers/runtime_switch.py` | `general/L5_engines/runtime_switch.py` | DELETE_FROM_GENERAL |
| C030 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_controls/engines/degraded_mode_checker.py` | `general/L5_engines/degraded_mode_checker.py` | DELETE_FROM_GENERAL |
| C031 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/alert_log_linker.py` | `incidents/L5_engines/alert_log_linker.py` | DELETE_FROM_INCIDENTS |
| C032 | CLASS|EXACT_FILE|FUNCTION | 100.0% | `general/L5_engines/audit_durability.py` | `general/L5_engines/durability.py` | DELETE_FROM_GENERAL |
| C033 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/audit_store.py` | `logs/L6_drivers/audit_store.py` | DELETE_FROM_LOGS |
| C034 | CLASS|FUNCTION | 100.0% | `general/L5_engines/audit_store.py` | `logs/L6_drivers/store.py` | DELETE_FROM_LOGS |
| C035 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/compliance_facade.py` | `logs/L5_engines/compliance_facade.py` | DELETE_FROM_LOGS |
| C036 | BLOCK|CLASS | 100.0% | `general/L5_workflow/contracts/engines/contract_engine.py` | `general/L5_engines/contract_engine.py` | DELETE_FROM_GENERAL |
| C037 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/control_registry.py` | `logs/L5_engines/control_registry.py` | DELETE_FROM_LOGS |
| C038 | CLASS | 100.0% | `general/L5_engines/cus_credential_service.py` | `integrations/L5_vault/engines/cus_credential_engine.py` | DELETE_FROM_INTEGRATIONS |
| C039 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/fatigue_controller.py` | `policies/L5_engines/fatigue_controller.py` | DELETE_FROM_POLICIES |
| C040 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `general/L5_engines/knowledge_lifecycle_manager.py` | DELETE_FROM_GENERAL |
| C041 | FUNCTION | 100.0% | `general/L5_engines/knowledge_lifecycle_manager.py` | `incidents/L5_engines/incident_engine.py` | DELETE_FROM_INCIDENTS |
| C042 | FUNCTION | 100.0% | `general/L5_engines/knowledge_lifecycle_manager.py` | `logs/L5_engines/mapper.py` | DELETE_FROM_LOGS |
| C043 | FUNCTION | 100.0% | `general/L5_engines/knowledge_lifecycle_manager.py` | `policies/L5_engines/lessons_engine.py` | DELETE_FROM_POLICIES |
| C044 | FUNCTION | 100.0% | `general/L5_engines/knowledge_lifecycle_manager.py` | `policies/L5_engines/mapper.py` | DELETE_FROM_POLICIES |
| C045 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/lifecycle_facade.py` | `general/L5_engines/lifecycle/lifecycle_facade.py` | DELETE_FROM_GENERAL |
| C046 | CLASS|EXACT_FILE | 100.0% | `general/L5_lifecycle/engines/base.py` | `general/L5_engines/lifecycle_stages_base.py` | DELETE_FROM_GENERAL |
| C047 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/monitors_facade.py` | `integrations/L5_engines/monitors_facade.py` | DELETE_FROM_INTEGRATIONS |
| C048 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/retrieval_facade.py` | `integrations/L5_engines/retrieval_facade.py` | DELETE_FROM_INTEGRATIONS |
| C049 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_engines/retrieval_mediator.py` | `integrations/L5_engines/retrieval_mediator.py` | DELETE_FROM_INTEGRATIONS |
| C050 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_lifecycle/drivers/execution.py` | `integrations/L6_drivers/execution.py` | DELETE_FROM_INTEGRATIONS |
| C051 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L6_drivers/knowledge_plane.py` | `general/L5_lifecycle/drivers/knowledge_plane.py` | DELETE_FROM_GENERAL |
| C052 | FUNCTION | 100.0% | `general/L5_lifecycle/drivers/knowledge_plane.py` | `integrations/L5_schemas/datasource_model.py` | DELETE_FROM_INTEGRATIONS |
| C053 | FUNCTION | 100.0% | `general/L5_lifecycle/drivers/knowledge_plane.py` | `integrations/L6_drivers/connector_registry.py` | DELETE_FROM_INTEGRATIONS |
| C054 | FUNCTION | 100.0% | `general/L5_schemas/agent.py` | `general/L5_schemas/artifact.py` | DELETE_FROM_GENERAL |
| C055 | FUNCTION | 100.0% | `general/L5_schemas/agent.py` | `general/L5_schemas/plan.py` | DELETE_FROM_GENERAL |
| C056 | FUNCTION | 100.0% | `general/L5_schemas/artifact.py` | `general/L5_schemas/plan.py` | DELETE_FROM_GENERAL |
| C057 | CLASS|FUNCTION | 100.0% | `general/L5_schemas/rac_models.py` | `logs/L5_schemas/audit_models.py` | DELETE_FROM_LOGS |
| C058 | CLASS|FUNCTION | 100.0% | `general/L5_schemas/rac_models.py` | `logs/L5_schemas/models.py` | DELETE_FROM_LOGS |
| C059 | CLASS | 70.6% | `general/L5_schemas/skill.py` | `integrations/L5_engines/http_connector.py` | DELETE_FROM_INTEGRATIONS |
| C060 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_support/CRM/engines/job_executor.py` | `policies/L5_engines/job_executor.py` | DELETE_FROM_POLICIES |
| C061 | BLOCK|CLASS|FUNCTION | 100.0% | `general/L5_ui/engines/rollout_projection.py` | `policies/L5_engines/rollout_projection.py` | DELETE_FROM_POLICIES |
| C062 | FUNCTION | 100.0% | `general/L5_utils/time.py` | `incidents/L6_drivers/guard_write_driver.py` | DELETE_FROM_INCIDENTS |
| C063 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `incidents/L5_engines/incident_engine.py` | DELETE_FROM_INCIDENTS |
| C064 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `logs/L5_engines/mapper.py` | DELETE_FROM_LOGS |
| C065 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `policies/L5_engines/lessons_engine.py` | DELETE_FROM_POLICIES |
| C066 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `policies/L5_engines/mapper.py` | DELETE_FROM_POLICIES |
| C067 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `policies/L5_engines/policy_limits_engine.py` | DELETE_FROM_POLICIES |
| C068 | FUNCTION | 100.0% | `general/L6_drivers/cross_domain.py` | `policies/L5_engines/policy_rules_engine.py` | DELETE_FROM_POLICIES |
| C069 | FUNCTION | 100.0% | `general/L6_drivers/knowledge_plane.py` | `integrations/L5_schemas/datasource_model.py` | DELETE_FROM_INTEGRATIONS |
| C070 | FUNCTION | 100.0% | `general/L6_drivers/knowledge_plane.py` | `integrations/L6_drivers/connector_registry.py` | DELETE_FROM_INTEGRATIONS |
| C071 | BLOCK|CLASS|FUNCTION | 100.0% | `general/hallucination_detector.py` | `incidents/L5_engines/hallucination_detector.py,policies/L5_engines/hallucination_detector.py` | EXTRACT_TO_GENERAL |
| C072 | FUNCTION | 100.0% | `general/incident_engine.py` | `incidents/L5_engines/incident_engine.py,logs/L5_engines/mapper.py` | EXTRACT_TO_GENERAL |
| C073 | FUNCTION | 100.0% | `general/incident_engine.py` | `incidents/L5_engines/incident_engine.py,policies/L5_engines/lessons_engine.py` | EXTRACT_TO_GENERAL |
| C074 | FUNCTION | 100.0% | `general/incident_engine.py` | `incidents/L5_engines/incident_engine.py,policies/L5_engines/mapper.py` | EXTRACT_TO_GENERAL |
| C075 | CLASS | 83.3% | `general/notifications_base.py` | `integrations/L3_adapters/notifications_base.py,integrations/L5_engines/notifications_facade.py` | REVIEW_MERGE |
| C076 | BLOCK|CLASS|FUNCTION | 100.0% | `general/channel_engine.py` | `integrations/L5_notifications/engines/channel_engine.py,integrations/L5_engines/channel_engine.py` | EXTRACT_TO_GENERAL |
| C077 | BLOCK|CLASS | 100.0% | `general/mcp_connector.py` | `integrations/L5_engines/mcp_connector.py,policies/L5_engines/mcp_connector.py` | EXTRACT_TO_GENERAL |
| C078 | BLOCK|CLASS | 100.0% | `general/service.py` | `integrations/L5_vault/engines/service.py,integrations/L5_engines/service.py` | EXTRACT_TO_GENERAL |
| C079 | FUNCTION | 100.0% | `general/datasource_model.py` | `integrations/L5_schemas/datasource_model.py,integrations/L6_drivers/connector_registry.py` | EXTRACT_TO_GENERAL |
| C080 | BLOCK|CLASS|FUNCTION | 100.0% | `general/audit_engine.py` | `logs/L5_support/CRM/engines/audit_engine.py,logs/L5_engines/audit_engine.py` | EXTRACT_TO_GENERAL |
| C081 | FUNCTION | 100.0% | `general/job_execution.py` | `logs/L6_drivers/job_execution.py,logs/L5_engines/audit_evidence.py` | EXTRACT_TO_GENERAL |
| C082 | CLASS|FUNCTION | 100.0% | `general/audit_reconciler.py` | `logs/L5_engines/audit_reconciler.py,logs/L5_engines/reconciler.py` | EXTRACT_TO_GENERAL |
| C083 | CLASS|FUNCTION | 100.0% | `general/completeness_checker.py` | `logs/L5_engines/completeness_checker.py,logs/L5_engines/export_completeness_checker.py` | EXTRACT_TO_GENERAL |
| C084 | FUNCTION | 100.0% | `general/mapper.py` | `logs/L5_engines/mapper.py,policies/L5_engines/lessons_engine.py` | EXTRACT_TO_GENERAL |
| C085 | BLOCK|CLASS|FUNCTION | 100.0% | `general/mapper.py` | `logs/L5_engines/mapper.py,policies/L5_engines/mapper.py` | EXTRACT_TO_GENERAL |
| C086 | BLOCK|CLASS | 100.0% | `general/replay_determinism.py` | `logs/L5_engines/replay_determinism.py,policies/L5_engines/replay_determinism.py` | EXTRACT_TO_GENERAL |
| C087 | CLASS|FUNCTION | 100.0% | `general/audit_models.py` | `logs/L5_schemas/audit_models.py,logs/L5_schemas/models.py` | EXTRACT_TO_GENERAL |
| C088 | CLASS|FUNCTION | 100.0% | `general/audit_store.py` | `logs/L6_drivers/audit_store.py,logs/L6_drivers/store.py` | EXTRACT_TO_GENERAL |
| C089 | FUNCTION | 100.0% | `general/lessons_engine.py` | `policies/L5_engines/lessons_engine.py,policies/L5_engines/mapper.py` | EXTRACT_TO_GENERAL |
| C090 | FUNCTION | 100.0% | `general/policy_limits_engine.py` | `policies/L5_engines/policy_limits_engine.py,policies/L5_engines/policy_rules_engine.py` | EXTRACT_TO_GENERAL |

---

## Recommendation Distribution

| Recommendation | Count |
|----------------|-------|
| DELETE_FROM_ACCOUNT | 2 |
| DELETE_FROM_ACTIVITY | 3 |
| DELETE_FROM_ANALYTICS | 2 |
| DELETE_FROM_CONTROLS | 9 |
| DELETE_FROM_GENERAL | 74 |
| DELETE_FROM_INCIDENTS | 17 |
| DELETE_FROM_INTEGRATIONS | 50 |
| DELETE_FROM_LOGS | 47 |
| DELETE_FROM_POLICIES | 71 |
| EXTRACT_TO_GENERAL | 132 |
| LIKELY_EXACT_COPY | 12 |
| REVIEW_MERGE | 7 |

---

*Report generated: 2026-01-27T14:39:26Z*
