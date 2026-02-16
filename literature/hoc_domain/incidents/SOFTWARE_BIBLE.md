# Incidents — Software Bible

**Domain:** incidents  
**L2 Features:** 22  
**Scripts:** 27  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for incidents is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/incidents/incidents_fac.py
- L2 public boundary module for domain-scoped facade entry is present at:
- backend/app/hoc/api/cus/incidents/incidents_public.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> incidents_public.py -> L4 registry.execute(...)
- Current status: incidents_public.py remains scaffold-only (no behavior change yet); existing domain routers stay active during incremental rollout.

## Reality Delta (2026-02-08)

- Execution topology: incidents L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5 gaps).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain incidents --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0` (incidents entry modules are no longer orphaned).
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.
- Run-scoped incident reads are served via `IncidentRunReadDriver` (async, `source_run_id`).
- Incident audit ledger events now embed `run_id` for governance log scoping.

**Strict T0 invariant:** incidents `L6_drivers/` contain no `hoc_spine` imports; any cross-domain coordination (e.g., ack emission) is wired at L4.

**Legacy note:** References to `prevention_engine` and `incident_severity_engine` in historical sections below are legacy; current incidents domain uses `policy_violation_engine` + `recovery_rule_engine`, and severity logic lives in `L5_schemas/severity_policy.py`.

## Reality Delta (2026-02-11)

- Canonical UC alignment now includes `UC-007`, `UC-011`, and `UC-012` (incident lifecycle, resolution/postmortem, recurrence grouping).
- Architecture status for incident-aligned UCs is now `GREEN` in canonical usecase registry/linkage docs.
- Storage contracts for resolution and recurrence fields are in place and validated via UC-MON storage verifier.

## Reality Delta (2026-02-12)

- Incidents expansion pack `UC-029..UC-031` is now architecture `GREEN`:
- recovery-rule evaluation lifecycle (`UC-029`)
- policy-violation truth pipeline (`UC-030`)
- pattern + postmortem learnings lifecycle (`UC-031`)
- Canonical registry/linkage reflects closure with per-UC evidence sections.
- Production readiness for these UCs is tracked separately in `backend/app/hoc/docs/architecture/usecases/PROD_READINESS_TRACKER.md`.

## Reality Delta (2026-02-12, Wave-2 Script Coverage Audit)

- Wave-2 script coverage (`analytics + incidents + activity`) has been independently audited and reconciled.
- Incidents core-scope classification is complete:
- `24` scripts marked `UC_LINKED`
- `13` scripts marked `NON_UC_SUPPORT`
- Core incidents residual is `0` in Wave-2 target scope.
- Deterministic gates remain clean post-wave and governance suite now runs `219` passing tests in `test_uc018_uc032_expansion.py`.
- Canonical audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md`

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Script Role | Canonical Function | Role | Decisions | Callers | Status |
|--------|-------|-------------|--------------------|----- |-----------|---------|--------|
| anomaly_bridge | L5 | PATTERN_ANALYSIS | `AnomalyIncidentBridge.ingest` | CANONICAL | 3 | L5:cost_anomaly_detector, incident_aggregator, recovery_rule_engine | YES |
| export_engine | L5 | EXPORT | `ExportEngine.export_evidence` | CANONICAL | 1 | L4:incidents_bridge | YES |
| hallucination_detector | L5 | DETECTION | `HallucinationDetector.detect` | CANONICAL | 6 | ?:hallucination_hook | ?:__init__, recovery_rule_engine | YES |
| incident_engine | L5 | DECISION_ENGINE | `IncidentEngine.create_incident_for_run` | CANONICAL | 6 | ?:hallucination_detector | L5:hallucination_detector | ?:inject_synthetic, recovery_rule_engine | YES |
| incident_pattern | L5 | PATTERN_ANALYSIS | `IncidentPatternService._detect_cascade_failures` | INTERNAL | 0 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| incident_read_engine | L5 | READ_SERVICE | `IncidentReadService.__init__` | WRAPPER | 0 | L5:customer_incidents_adapter | L3:customer_incidents_adapter, recovery_rule_engine | INTERFACE |
| incident_write_engine | L5 | WRITE_SERVICE | `IncidentWriteService.resolve_incident` | CANONICAL | 2 | ?:incident_write_service | L5:customer_incidents_adapter | L3:customer_incidents_adapter, recovery_rule_engine | YES |
| incidents_facade | L5 | FACADE | `IncidentsFacade.list_active_incidents` | CANONICAL | 6 | ?:incidents | L4:incidents_handler | ?:learning_insight_result | ?:recurrence_group_result | ?:recurrence_analysis_result | ?:resolution_summary_result | ?:pattern_match_result | ?:learnings_result | ?:pattern_detection_result | YES |
| policy_violation_engine | L5 | POLICY | `create_policy_evaluation_sync` | CANONICAL | 5 | recovery_rule_engine | YES |
| postmortem | L5 | ANALYSIS | `PostMortemService.get_category_learnings` | CANONICAL | 1 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| recovery_rule_engine | L5 | RECOVERY | `RecoveryRuleEngine.evaluate` | CANONICAL | 4 | ?:recovery | ?:failure_intelligence | ?:failure_classification_engine | ?:recovery_evaluation_engine | L5:recovery_evaluation_engine | L2:recovery | ?:test_m10_recovery_enhanced, hallucination_detector | FACADE_PATTERN |
| recurrence_analysis | L5 | PATTERN_ANALYSIS | `RecurrenceAnalysisService.analyze_recurrence` | INTERNAL | 0 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| semantic_failures | L5 | DETECTION | `get_failure_info` | LEAF | 0 | ?:semantic_validator | ?:__init__ | YES |
| cost_guard_driver | L6 | PERSISTENCE | `CostGuardDriver.get_spend_totals` | CANONICAL | 0 | L4:incidents_handler | YES |
| export_bundle_driver | L6 | PERSISTENCE | `ExportBundleService.create_evidence_bundle` | CANONICAL | 4 | L4:incidents_handler (incidents.export), recovery_rule_engine | YES |
| incident_aggregator | L6 | AGGREGATION | `IncidentAggregator._add_call_to_incident` | SUPERSET | 3 | L5:policy_violation_engine, anomaly_bridge, policy_violation_engine +1 | YES |
| incident_driver | L6 | ORCHESTRATION | `IncidentDriver.create_incident_for_run` | CANONICAL | 1 | L4:transaction_coordinator | YES |
| incident_pattern_driver | L6 | PERSISTENCE | `IncidentPatternDriver.fetch_cascade_failures` | LEAF | 0 | L5:incident_pattern, incident_pattern, recovery_rule_engine | YES |
| incident_read_driver | L6 | PERSISTENCE | `IncidentReadDriver.count_incidents_since` | LEAF | 0 | L6:__init__ | L5:incident_read_engine, incident_read_engine, recovery_rule_engine | YES |
| incident_run_read_driver | L6 | PERSISTENCE | `IncidentRunReadDriver.fetch_incidents_by_run_id` | LEAF | 0 | L4:run_evidence_coordinator | YES |
| incident_write_driver | L6 | PERSISTENCE | `IncidentWriteDriver.fetch_incidents_by_run_id` | LEAF | 0 | ?:incident_write_engine | L6:__init__ | L5:incident_write_engine | L5:incident_engine | L5:anomaly_bridge, anomaly_bridge, incident_engine +2 | YES |
| incidents_facade_driver | L6 | FACADE | `IncidentsFacadeDriver.fetch_active_incidents` | CANONICAL | 7 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| lessons_driver | L6 | PERSISTENCE | `LessonsDriver.fetch_debounce_count` | LEAF | 1 | L5:lessons_engine, recovery_rule_engine | YES |
| llm_failure_driver | L6 | PERSISTENCE | `LLMFailureDriver.fetch_contamination_check` | LEAF | 0 | recovery_rule_engine | YES |
| policy_violation_driver | L6 | PERSISTENCE | `PolicyViolationDriver.fetch_incident_by_violation` | LEAF | 0 | L5:policy_violation_engine, policy_violation_engine, recovery_rule_engine | YES |
| postmortem_driver | L6 | PERSISTENCE | `PostMortemDriver.fetch_category_stats` | LEAF | 1 | L5:postmortem, postmortem, recovery_rule_engine | YES |
| recurrence_analysis_driver | L6 | PERSISTENCE | `RecurrenceAnalysisDriver.fetch_recurrence_for_category` | LEAF | 1 | ?:incidents_facade | ?:__init__ | L5:recurrence_analysis, recovery_rule_engine, recurrence_analysis | YES |

## Uncalled Functions

Functions with no internal or external callers detected, classified by analysis.

| Function | Classification | Reason |
|----------|----------------|--------|
| `policy_violation_engine.PolicyViolationService.check_policy_enabled` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.PolicyViolationService.verify_violation_truth` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.create_policy_evaluation_sync` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.handle_policy_evaluation_for_run` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.handle_policy_violation` | **PENDING** (PIN-470) | Design-ahead infrastructure |

## Facade Patterns (same noun, different roles — NOT duplicates)

These scripts share a noun but serve structurally distinct roles.

- `incident_driver` (ORCHESTRATION) — canonical: `IncidentDriver.create_incident_for_run` (CANONICAL)
- `incident_engine` (DECISION_ENGINE) — canonical: `IncidentEngine.create_incident_for_run` (CANONICAL)
- `prevention_engine` (POLICY) — canonical: `PreventionEngine.evaluate` (CANONICAL)
- `recovery_rule_engine` (RECOVERY) — canonical: `RecoveryRuleEngine.evaluate` (CANONICAL)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 22 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### GET /active
```
L2:incidents.list_active_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /by-run/{run_id}
```
L2:incidents.get_incidents_for_run → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /cost-impact
```
L2:incidents.analyze_cost_impact → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /explained
```
L2:cost_guard.get_cost_explained → L4:incidents_handler → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical
```
L2:incidents.list_historical_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical/cost-trend
```
L2:incidents.get_historical_cost_trend → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical/distribution
```
L2:incidents.get_historical_distribution → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical/trend
```
L2:incidents.get_historical_trend → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /incidents
```
L2:cost_guard.get_cost_incidents → L4:incidents_handler → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /metrics
```
L2:incidents.get_incident_metrics → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /patterns
```
L2:incidents.detect_patterns → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /recurring
```
L2:incidents.analyze_recurrence → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /resolved
```
L2:incidents.list_resolved_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /summary
```
L2:cost_guard.get_cost_summary → L4:incidents_handler → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}
```
L2:incidents.get_incident_detail → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}/evidence
```
L2:incidents.get_incident_evidence → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}/learnings
```
L2:incidents.get_incident_learnings → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}/proof
```
L2:incidents.get_incident_proof → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### POST /{incident_id}/export/evidence
```
L2:incidents.export_evidence → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### POST /{incident_id}/export/executive-debrief
```
L2:incidents.export_executive_debrief → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### POST /{incident_id}/export/soc2
```
L2:incidents.export_soc2 → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### list_incidents
```
L2:incidents.list_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `AnomalyIncidentBridge.ingest` | anomaly_bridge | CANONICAL | 3 | 5 | no | anomaly_bridge:AnomalyIncidentBridge._check_existing_inciden |
| `CompositeRule.evaluate` | recovery_rule_engine | SUPERSET | 2 | 6 | no | hallucination_detector:HallucinationIndicator.to_dict | prev |
| `ContentAccuracyValidatorV2.validate` | prevention_engine | SUPERSET | 4 | 8 | no | prevention_engine:ContentAccuracyValidatorV2._extract_claim  |
| `ExportBundleService.create_evidence_bundle` | export_bundle_driver | CANONICAL | 4 | 1 | no | export_bundle_driver:ExportBundleService._compute_bundle_has |
| `ExportBundleService.create_executive_debrief` | export_bundle_driver | SUPERSET | 4 | 1 | no | export_bundle_driver:ExportBundleService._assess_business_im |
| `HallucinationDetector.detect` | hallucination_detector | CANONICAL | 6 | 10 | no | hallucination_detector:HallucinationDetector._detect_contrad |
| `HallucinationValidator.validate` | prevention_engine | SUPERSET | 2 | 3 | no | prevention_engine:HallucinationValidator._claim_in_context |
| `IncidentAggregator._add_call_to_incident` | incident_aggregator | SUPERSET | 3 | 7 | yes | incident_aggregator:IncidentAggregator._add_incident_event | |
| `IncidentAggregator.get_or_create_incident` | incident_aggregator | SUPERSET | 2 | 7 | no | anomaly_bridge:AnomalyIncidentBridge._create_incident | inci |
| `IncidentAggregator.resolve_stale_incidents` | incident_aggregator | SUPERSET | 2 | 10 | yes | incident_aggregator:IncidentAggregator._add_incident_event |
| `IncidentDriver.create_incident_for_run` | incident_driver | CANONICAL | 1 | 6 | no | incident_driver:IncidentDriver._emit_ack | incident_engine:I |
| `IncidentEngine._get_driver` | incident_engine | SUPERSET | 3 | 4 | no | incident_write_driver:get_incident_write_driver |
| `IncidentEngine.check_and_create_incident` | incident_engine | SUPERSET | 2 | 4 | no | incident_engine:IncidentEngine._extract_error_code | inciden |
| `IncidentEngine.create_incident_for_failed_run` | incident_engine | SUPERSET | 3 | 1 | no | incident_engine:IncidentEngine._check_policy_suppression | i |
| `IncidentEngine.create_incident_for_run` | incident_engine | CANONICAL | 6 | 1 | no | incident_engine:IncidentEngine._check_policy_suppression | i |
| `IncidentSeverityEngine.should_escalate` | incident_severity_engine | SUPERSET | 2 | 3 | no | incident_severity_engine:IncidentSeverityEngine.calculate_se |
| `IncidentWriteService.resolve_incident` | incident_write_engine | CANONICAL | 2 | 6 | no | incident_write_driver:IncidentWriteDriver.create_incident_ev |
| `IncidentsFacade.get_metrics` | incidents_facade | SUPERSET | 2 | 7 | no | incidents_facade_driver:IncidentsFacadeDriver.fetch_metrics_ |
| `IncidentsFacade.list_active_incidents` | incidents_facade | CANONICAL | 6 | 13 | no | incidents_facade:IncidentsFacade._snapshot_to_summary | inci |
| `IncidentsFacade.list_historical_incidents` | incidents_facade | SUPERSET | 3 | 11 | no | incidents_facade:IncidentsFacade._snapshot_to_summary | inci |
| `IncidentsFacade.list_resolved_incidents` | incidents_facade | SUPERSET | 6 | 13 | no | incidents_facade:IncidentsFacade._snapshot_to_summary | inci |
| `IncidentsFacadeDriver.fetch_active_incidents` | incidents_facade_driver | CANONICAL | 7 | 17 | yes | incidents_facade_driver:IncidentsFacadeDriver._to_snapshot |
| `IncidentsFacadeDriver.fetch_historical_incidents` | incidents_facade_driver | SUPERSET | 4 | 14 | yes | incidents_facade_driver:IncidentsFacadeDriver._to_snapshot |
| `IncidentsFacadeDriver.fetch_resolved_incidents` | incidents_facade_driver | SUPERSET | 7 | 17 | yes | incidents_facade_driver:IncidentsFacadeDriver._to_snapshot |
| `LLMFailureService._verify_no_contamination` | llm_failure_engine | SUPERSET | 3 | 4 | no | llm_failure_driver:LLMFailureDriver.fetch_contamination_chec |
| `LLMFailureService.persist_failure_and_mark_run` | llm_failure_engine | CANONICAL | 1 | 7 | no | llm_failure_engine:LLMFailureService._capture_evidence | llm |
| `PolicyViolationService.create_incident_from_violation` | policy_violation_engine | SUPERSET | 3 | 7 | no | incident_aggregator:IncidentAggregator.get_or_create_inciden |
| `PolicyViolationService.persist_violation_and_create_incident` | policy_violation_engine | SUPERSET | 3 | 7 | no | policy_violation_engine:PolicyViolationService.check_inciden |
| `PolicyViolationService.persist_violation_fact` | policy_violation_engine | SUPERSET | 4 | 8 | no | policy_violation_driver:PolicyViolationDriver.insert_violati |
| `PostMortemService.get_category_learnings` | postmortem_engine | CANONICAL | 1 | 11 | no | postmortem_driver:PostMortemDriver.fetch_category_stats | po |
| `PreventionEngine.evaluate` | prevention_engine | CANONICAL | 6 | 14 | no | prevention_engine:BaseValidator.validate | prevention_engine |
| `RecoveryRuleEngine.evaluate` | recovery_rule_engine | CANONICAL | 4 | 11 | no | prevention_engine:PreventionEngine.evaluate | recovery_rule_ |
| `create_incident_from_violation` | prevention_engine | SUPERSET | 2 | 4 | no | prevention_engine:_create_incident_with_service |
| `create_policy_evaluation_sync` | policy_violation_engine | CANONICAL | 5 | 10 | no | policy_violation_driver:insert_policy_evaluation_sync |
| `handle_policy_evaluation_for_run` | policy_violation_engine | SUPERSET | 3 | 3 | no | policy_violation_engine:create_policy_evaluation_record |

## Wrapper Inventory

_85 thin delegation functions._

- `anomaly_bridge.AnomalyIncidentBridge.__init__` → incident_write_driver:get_incident_write_driver
- `anomaly_bridge.AnomalyIncidentBridge._build_incident_insert_sql` → ?
- `anomaly_bridge.AnomalyIncidentBridge._check_existing_incident` → ?
- `anomaly_bridge.AnomalyIncidentBridge._meets_severity_threshold` → ?
- `prevention_engine.BaseValidator.validate` → ?
- `prevention_engine.BudgetValidator.__init__` → ?
- `prevention_engine.ContentAccuracyValidatorV2.__init__` → ?
- `recovery_rule_engine.EvaluationResult.to_dict` → hallucination_detector:HallucinationIndicator.to_dict
- `export_bundle_driver.ExportBundleService.__init__` → ?
- `export_bundle_driver.ExportBundleService._assess_business_impact` → ?
- `export_bundle_driver.ExportBundleService._generate_attestation` → ?
- `export_bundle_driver.ExportBundleService._generate_incident_summary` → ?
- `export_bundle_driver.ExportBundleService._generate_recommendations` → ?
- `hallucination_detector.HallucinationIndicator.to_dict` → ?
- `prevention_engine.HallucinationValidator.__init__` → ?
- `recovery_rule_engine.HistoricalPatternRule.__init__` → anomaly_bridge:AnomalyIncidentBridge.__init__
- `incident_driver.IncidentDriver.__init__` → ?
- `incident_driver.IncidentDriver.check_and_create_incident` → incident_engine:IncidentEngine.check_and_create_incident
- `incident_driver.IncidentDriver.get_incidents_for_run` → incident_engine:IncidentEngine.get_incidents_for_run
- `incident_engine.IncidentEngine.__init__` → ?
- `incident_aggregator.IncidentKey.__hash__` → ?
- `incident_pattern_driver.IncidentPatternDriver.__init__` → ?
- `incident_pattern_engine.IncidentPatternService.__init__` → incident_pattern_driver:get_incident_pattern_driver
- `incident_read_driver.IncidentReadDriver.__init__` → ?
- `incident_read_engine.IncidentReadService.__init__` → incident_read_driver:get_incident_read_driver
- `incident_read_engine.IncidentReadService.count_incidents_since` → incident_read_driver:IncidentReadDriver.count_incidents_since
- `incident_read_engine.IncidentReadService.get_incident` → incident_read_driver:IncidentReadDriver.get_incident
- `incident_read_engine.IncidentReadService.get_incident_events` → incident_read_driver:IncidentReadDriver.get_incident_events
- `incident_read_engine.IncidentReadService.get_last_incident` → incident_read_driver:IncidentReadDriver.get_last_incident
- `incident_read_engine.IncidentReadService.list_incidents` → incident_read_driver:IncidentReadDriver.list_incidents
- _...and 55 more_

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `incident_write_engine` | Removed cross-domain `AuditLedgerService` import. Accepts `audit: Any = None` via dependency injection from L4 handler. | PIN-504 Phase 2 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `incidents_handler.py` | `IncidentsQueryHandler`: Replaced `getattr()` dispatch with explicit map (10 methods). `IncidentsExportHandler`: Replaced `getattr()` dispatch with explicit map (3 methods). `IncidentsWriteHandler`: Replaced `getattr()` dispatch with explicit map (3 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-507 Law 0 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `incident_write_engine` (legacy `app/services/`) | Import `AuditLedgerService` rewired from abolished `app.services.logs.audit_ledger_service` → `app.hoc.cus.logs.L5_engines.audit_ledger_engine`. Transitional `services→hoc` dependency documented at import site. Permanent fix: migrate `incident_write_engine.py` to `hoc/cus/incidents/L5_engines/`. | PIN-507 Law 0 |
| `L6_drivers/export_bundle_driver.py` | L6→L7 boundary fix: `Incident` import moved from `app.db` → `app.models.killswitch`. L6 drivers must not import L7 models via `app.db` (HOC Topology V2.0.0). | PIN-507 Law 0 |

## PIN-507 Law 1 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `incident_severity_engine` | All severity logic moved to `incidents/L5_schemas/severity_policy.py`. File is now a tombstone with re-exports for backward compat. | PIN-507 Law 1 |
| `incident_aggregator` | Import changed from `L5_engines.incident_severity_engine` → `L5_schemas.severity_policy`. L6→L5 engine reach eliminated. | PIN-507 Law 1 |
| **NEW** `L5_schemas/severity_policy.py` | Created: `IncidentSeverityEngine`, `SeverityConfig`, `TRIGGER_SEVERITY_MAP`, `DEFAULT_SEVERITY`, `generate_incident_title`. Canonical home for severity policy logic. | PIN-507 Law 1 |

## PIN-508 Refactoring (2026-02-01)

### Phase 1B: anomaly_bridge Driver Extraction

| Script | Change | Reference |
|--------|--------|-----------|
| `anomaly_bridge.py` | Constructor now accepts `IncidentWriteDriver` instance instead of session. Methods `_build_incident_insert_sql()` and `_create_incident()` removed — SQL moved to driver. Factory `get_anomaly_incident_bridge(session)` creates driver internally. | PIN-508 Phase 1B |
| `incident_write_driver.py` | New method `insert_incident_from_anomaly(incident_dict: Dict)` added. Handles full SQL INSERT + IncidentEvent creation for anomaly bridge. | PIN-508 Phase 1B |

### Phase 4B: incident_severity_engine Deletion

| Script | Change | Reference |
|--------|--------|-----------|
| `incident_severity_engine.py` | **DELETED** (TOMBSTONE only). Logic extracted by PIN-507 Law 1 to `L5_schemas/severity_policy.py`. Zero current dependents. | PIN-508 Phase 4B |

## PIN-510 Phase 1C — CostAnomalyFact Extraction (2026-02-01)

- `CostAnomalyFact` dataclass extracted from `anomaly_bridge.py` to `hoc/cus/hoc_spine/schemas/anomaly_types.py`
- Backward-compat re-export remains in `anomaly_bridge.py` (TOMBSTONE)
- New L4 coordinator `anomaly_incident_coordinator.py` owns analytics→incidents sequencing
- Reference: `docs/memory-pins/PIN-510-domain-remediation-queue.md`

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Topology Completion & Hygiene (2026-02-01)

### Phase 3 — L1 Protocol Re-wiring (hoc_spine)

Protocol-based dependency injection replacing `NotImplementedError("pending L1 re-wiring")` stubs in L4 spine code. Production paths via `app/services/` remain unchanged; these enable future HOC-only cutover.

**New shared artifact:**

| File | Purpose | Reference |
|------|---------|-----------|
| **NEW** `hoc_spine/schemas/protocols.py` | 6 Protocol interfaces: `LessonsEnginePort`, `PolicyEvaluationPort`, `TraceFacadePort`, `ConnectorLookupPort`, `ValidatorVerdictPort`, `EligibilityVerdictPort` | PIN-513 Phase 3 |

**L4 spine files modified:**

| File | Change | Reference |
|------|--------|-----------|
| `hoc_spine/orchestrator/run_governance_facade.py` | Added `lessons_engine: LessonsEnginePort` and `policy_evaluator: PolicyEvaluationPort` constructor injection. Replaced 2 `NotImplementedError` stubs with delegation. | PIN-513 Phase 3A/3B |
| `hoc_spine/drivers/transaction_coordinator.py` | Added `incident_driver` and `trace_facade: TraceFacadePort` constructor injection. Replaced 2 stubs with delegation. | PIN-513 Phase 3C/3D |
| `hoc_spine/orchestrator/lifecycle/drivers/execution.py` | Added `connector_lookup: ConnectorLookupPort` to `DataIngestionExecutor` and `IndexingExecutor`. Replaced 2 connector stubs. | PIN-513 Phase 3E |
| `hoc_spine/authority/contracts/contract_engine.py` | Replaced broken cross-domain L5 imports (`ValidatorVerdict`, `EligibilityVerdict`) with Protocol aliases. Created local proxy classes for `.value` attribute compatibility. | PIN-513 Phase 3F |
| `hoc_spine/consequences/adapters/export_bundle_adapter.py` | Fixed broken `ExportBundleStore` import — now requires store injection via constructor. | PIN-513 Phase 3 |
| `hoc_spine/orchestrator/__init__.py` | Replaced all `BROKEN INTENTIONALLY` and `TODO(L1)` comments with PIN-513 references. Updated `__all__` comments. | PIN-513 Phase 3 |

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

| File | Change | Reference |
|------|--------|-----------|
| `fdr/incidents/engines/ops_incident_service.py:40` | Import swapped: `app.services.ops_domain_models` → `app.hoc.fdr.ops.schemas.ops_domain_models` (OpsIncident, OpsIncidentCategory, OpsSeverity) | PIN-513 Phase 7, Step 3a |
| `api/fdr/incidents/ops.py:1482` | Import swapped: `app.services.ops` → `app.hoc.fdr.ops.facades.ops_facade` | PIN-513 Phase 7, Step 6 |

**Impact:** 2 imports fully severed. Zero TRANSITIONAL tags remain in incidents domain.

## PIN-513 Phase 8 — Zero-Caller Wiring (2026-02-01)

| Component | L4 Owner | Action |
|-----------|----------|--------|
| `integrity_driver` (logs L6) | `incidents/L5_engines/export_engine.py` | Added `export_with_integrity()` method — generates export bundle then attaches integrity evaluation via `compute_integrity_v2(run_id)` from logs L6 driver |

## PIN-513 Phase 9 — Batch 1B Wiring (2026-02-01)

- Created `hoc_spine/orchestrator/handlers/run_governance_handler.py` (L4 handler)
- Wired 3 previously orphaned L5 symbols from `policy_violation_engine.py`:
  - `handle_policy_evaluation_for_run` → `RunGovernanceHandler.evaluate_run()`
  - `handle_policy_violation` → `RunGovernanceHandler.report_violation()`
  - `create_policy_evaluation_record` → `RunGovernanceHandler.create_evaluation()`
- Reclassified `create_policy_evaluation_sync` as already WIRED (via RunGovernanceFacade → worker runner)
- All 4 CSV entries resolved: 3 WIRED, 1 RECLASSIFIED

### PIN-513 Phase 9 Batch 5 Amendment (2026-02-01)

**CI invariant hardening — incidents domain impact:**

- Check 29 freezes 3 `int/` driver files: `hallucination_hook.py`, `failure_classification_engine.py`, `tenant_config.py` (import incidents L5_engines)
- No incidents-owned files appear in allowlists — incidents is a *target* of frozen cross-domain imports, not a *source*

**Total CI checks:** 30 system-wide.
