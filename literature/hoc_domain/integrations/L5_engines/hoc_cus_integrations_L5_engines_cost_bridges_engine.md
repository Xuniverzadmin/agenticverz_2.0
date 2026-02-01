# hoc_cus_integrations_L5_engines_cost_bridges_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/cost_bridges_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost-related integration bridges (cost loop business logic)

## Intent

**Role:** Cost-related integration bridges (cost loop business logic)
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** cost services, workers

## Purpose

M27 Cost Loop Integration Bridges

---

## Classes

### `AnomalyType(str, Enum)`
- **Docstring:** Types of cost anomalies.

### `AnomalySeverity(str, Enum)`
- **Docstring:** Severity levels for cost anomalies.

### `CostAnomaly`
- **Docstring:** Detected cost anomaly from M26 Cost Intelligence.
- **Methods:** create, to_dict
- **Class Variables:** id: str, tenant_id: str, anomaly_type: AnomalyType, severity: AnomalySeverity, entity_type: str, entity_id: str, current_value_cents: int, expected_value_cents: int, deviation_pct: float, message: str, detected_at: datetime, metadata: dict[str, Any]

### `CostLoopBridge`
- **Docstring:** Bridge C1: Cost Anomaly → Incident (MANDATORY GOVERNANCE).
- **Methods:** __init__, on_anomaly_detected, _map_severity_to_incident_severity

### `CostPatternMatcher`
- **Docstring:** Bridge C2: Match cost anomalies to failure patterns.
- **Methods:** __init__, match_cost_pattern, _build_signature, _hash_signature, _deviation_bucket, _find_predefined_match, _calculate_confidence

### `CostRecoveryGenerator`
- **Docstring:** Bridge C3: Generate recovery suggestions for cost anomalies.
- **Methods:** __init__, generate_recovery
- **Class Variables:** RECOVERY_STRATEGIES: dict[str, list[dict[str, Any]]]

### `CostPolicyGenerator`
- **Docstring:** Bridge C4: Generate policies from cost recoveries.
- **Methods:** __init__, generate_policy
- **Class Variables:** POLICY_TEMPLATES: dict[str, dict[str, Any]]

### `CostRoutingAdjuster`
- **Docstring:** Bridge C5: Adjust CARE routing based on cost policies.
- **Methods:** __init__, on_cost_policy_created, _create_model_routing_adjustment, _create_rate_limit_adjustment, _create_budget_block_adjustment, _create_token_limit_adjustment, _create_throttle_adjustment, _create_notify_adjustment, _create_review_adjustment, _create_escalation_adjustment

### `CostEstimationProbe`
- **Docstring:** CARE probe that estimates request cost before execution.
- **Methods:** __init__, probe, _calculate_cost, _find_cheaper_model
- **Class Variables:** MODEL_COSTS: dict[str, dict[str, float]]

### `CostLoopOrchestrator`
- **Docstring:** Orchestrates the full M27 cost loop:
- **Methods:** __init__, process_anomaly

## Attributes

- `logger` (line 54)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.hoc.cus.hoc_spine.orchestrator`, `schemas.loop_events` |

## Callers

cost services, workers

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: AnomalyType
      methods: []
    - name: AnomalySeverity
      methods: []
    - name: CostAnomaly
      methods: [create, to_dict]
    - name: CostLoopBridge
      methods: [on_anomaly_detected]
    - name: CostPatternMatcher
      methods: [match_cost_pattern]
    - name: CostRecoveryGenerator
      methods: [generate_recovery]
    - name: CostPolicyGenerator
      methods: [generate_policy]
    - name: CostRoutingAdjuster
      methods: [on_cost_policy_created]
    - name: CostEstimationProbe
      methods: [probe]
    - name: CostLoopOrchestrator
      methods: [process_anomaly]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
