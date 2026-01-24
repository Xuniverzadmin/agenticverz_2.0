# DIRECTORY REORGANIZATION INVENTORY

**Generated:** $(date +%Y-%m-%d)
**Total Files:** 167

## Summary by Type

| Type | Count | Pattern |
|------|-------|---------|
| Facades | 26 | *facade*.py |
| Engines | 14 | *engine*.py |
| Drivers | 2 | *driver*.py |
| Services | 45 | *service*.py |
| Other | 80 | Various |

---

## ALREADY COPIED TO HOUSEOFCARDS (31 files)

### Customer Facades (12)
- [x] overview_facade.py → customer/overview/facades/
- [x] activity_facade.py → customer/activity/facades/
- [x] incidents_facade.py → customer/incidents/facades/
- [x] policies_facade.py → customer/policies/facades/
- [x] logs_facade.py → customer/logs/facades/
- [x] analytics_facade.py → customer/analytics/facades/
- [x] accounts_facade.py → customer/account/facades/
- [x] integrations_facade.py → customer/integrations/facades/
- [x] api_keys_facade.py → customer/api_keys/facades/
- [x] governance/facade.py → customer/policies/facades/governance_facade.py
- [x] governance/run_governance_facade.py → customer/policies/facades/

### Customer Drivers (2)
- [x] incidents/incident_driver.py → customer/incidents/drivers/
- [x] policy/policy_driver.py → customer/policies/drivers/

### Customer Engines (10)
- [x] plan_generation_engine.py → customer/activity/engines/
- [x] cost_model_engine.py → customer/analytics/engines/
- [x] recovery_evaluation_engine.py → customer/incidents/engines/
- [x] recovery_rule_engine.py → customer/incidents/engines/
- [x] budget_enforcement_engine.py → customer/policies/engines/
- [x] claim_decision_engine.py → customer/policies/engines/
- [x] governance/eligibility_engine.py → customer/policies/engines/
- [x] policy/lessons_engine.py → customer/policies/engines/
- [x] llm_policy_engine.py → customer/policies/engines/
- [x] policy_graph_engine.py → customer/policies/engines/

### Internal (3)
- [x] recovery_matcher.py → internal/recovery/engines/
- [x] orphan_recovery.py → internal/recovery/engines/
- [x] recovery_write_service.py → internal/recovery/drivers/

### Founder (5)
- [x] ops/facade.py → founder/ops/facades/ops_facade.py
- [x] ops/error_store.py → founder/ops/engines/
- [x] ops_incident_service.py → founder/ops/engines/
- [x] ops_write_service.py → founder/ops/drivers/
- [x] ops_domain_models.py → founder/ops/schemas/

---

## PENDING CLASSIFICATION (136 files)

### Unclassified Facades (14)
- [ ] alerts/facade.py
- [ ] compliance/facade.py
- [ ] connectors/facade.py
- [ ] controls/facade.py
- [ ] datasources/facade.py
- [ ] detection/facade.py
- [ ] evidence/facade.py
- [ ] lifecycle/facade.py
- [ ] limits/facade.py
- [ ] monitors/facade.py
- [ ] notifications/facade.py
- [ ] observability/trace_facade.py
- [ ] retrieval/facade.py
- [ ] scheduler/facade.py

### Unclassified Engines (4)
- [ ] ai_console_panel_adapter/ai_console_panel_engine.py
- [ ] ai_console_panel_adapter/panel_verification_engine.py
- [ ] ai_console_panel_adapter/validator_engine.py
- [ ] incidents/incident_engine.py

### Unclassified Services (45)
(See full list in raw inventory)

### Other Files (80)
(See full list in raw inventory)

---

## CLASSIFICATION NEEDED

Files must be mapped to:
- **Audience:** customer | internal | founder
- **Domain:** overview | activity | incidents | policies | logs | analytics | account | integrations | api_keys | general | agent | recovery | ops
- **Role:** facades | drivers | engines | schemas

