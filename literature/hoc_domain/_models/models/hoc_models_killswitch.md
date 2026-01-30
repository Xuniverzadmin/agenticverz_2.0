# hoc_models_killswitch

| Field | Value |
|-------|-------|
| Path | `backend/app/models/killswitch.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Killswitch data models

## Intent

**Role:** Killswitch data models
**Reference:** Killswitch System
**Callers:** killswitch API, services

## Purpose

M22 KillSwitch Models

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** _None_
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** _None_
- **Calls:** str, uuid4

## Classes

### `EntityType(str, Enum)`
- **Docstring:** _None_

### `TriggerType(str, Enum)`
- **Docstring:** _None_

### `IncidentSeverity(str, Enum)`
- **Docstring:** _None_

### `IncidentStatus(str, Enum)`
- **Docstring:** _None_

### `IncidentLifecycleState(str, Enum)`
- **Docstring:** Canonical lifecycle state for incidents (PIN-412).

### `IncidentCauseType(str, Enum)`
- **Docstring:** Normalized cause semantics for incidents (PIN-412).

### `GuardrailAction(str, Enum)`
- **Docstring:** _None_

### `GuardrailCategory(str, Enum)`
- **Docstring:** _None_

### `KillSwitchState(SQLModel)`
- **Docstring:** Track freeze state for tenants and API keys.
- **Methods:** freeze, unfreeze
- **Class Variables:** id: str, entity_type: str, entity_id: str, tenant_id: str, is_frozen: bool, frozen_at: Optional[datetime], frozen_by: Optional[str], freeze_reason: Optional[str], unfrozen_at: Optional[datetime], unfrozen_by: Optional[str], auto_triggered: bool, trigger_type: Optional[str], created_at: datetime, updated_at: datetime

### `ProxyCall(SQLModel)`
- **Docstring:** Log of OpenAI proxy calls for replay and analysis.
- **Methods:** hash_request, hash_response, set_policy_decisions, get_policy_decisions
- **Class Variables:** id: str, tenant_id: str, api_key_id: Optional[str], user_id: Optional[str], endpoint: str, model: str, request_hash: str, request_json: str, response_hash: Optional[str], response_json: Optional[str], status_code: Optional[int], error_code: Optional[str], input_tokens: int, output_tokens: int, cost_cents: Decimal, policy_decisions_json: Optional[str], was_blocked: bool, block_reason: Optional[str], latency_ms: Optional[int], upstream_latency_ms: Optional[int], replay_eligible: bool, replayed_from_id: Optional[str], created_at: datetime

### `Incident(SQLModel)`
- **Docstring:** Auto-grouped failure incidents.
- **Methods:** get_inflection_context, set_inflection_context, set_inflection_point, add_related_call, get_related_call_ids, resolve, acknowledge
- **Class Variables:** id: str, tenant_id: str, title: str, severity: str, status: str, trigger_type: str, trigger_value: Optional[str], calls_affected: int, cost_delta_cents: Decimal, error_rate: Optional[Decimal], auto_action: Optional[str], action_details_json: Optional[str], started_at: datetime, ended_at: Optional[datetime], duration_seconds: Optional[int], related_call_ids_json: Optional[str], killswitch_id: Optional[str], created_at: datetime, updated_at: datetime, resolved_at: Optional[datetime], resolved_by: Optional[str], source_run_id: Optional[str], source_type: Optional[str], category: Optional[str], description: Optional[str], error_code: Optional[str], error_message: Optional[str], impact_scope: Optional[str], affected_agent_id: Optional[str], affected_count: int, resolution_notes: Optional[str], escalated: bool, escalated_at: Optional[datetime], escalated_to: Optional[str], is_synthetic: bool, synthetic_scenario_id: Optional[str], lifecycle_state: str, llm_run_id: Optional[str], cause_type: str, resolution_method: Optional[str], cost_impact: Optional[Decimal], inflection_step_index: Optional[int], inflection_timestamp: Optional[datetime], inflection_context_json: Optional[str]

### `IncidentEvent(SQLModel)`
- **Docstring:** Timeline events within an incident.
- **Methods:** set_data, get_data
- **Class Variables:** id: str, incident_id: str, event_type: str, description: str, data_json: Optional[str], created_at: datetime

### `DefaultGuardrail(SQLModel)`
- **Docstring:** Read-only default policy pack.
- **Methods:** get_rule_config, evaluate
- **Class Variables:** id: str, name: str, description: Optional[str], category: str, rule_type: str, rule_config_json: str, action: str, is_enabled: bool, is_default: bool, priority: int, version: str, created_at: datetime

### `KillSwitchStatus(BaseModel)`
- **Docstring:** Response schema for kill switch status.
- **Class Variables:** entity_type: str, entity_id: str, is_frozen: bool, frozen_at: Optional[datetime], frozen_by: Optional[str], freeze_reason: Optional[str], auto_triggered: bool, trigger_type: Optional[str]

### `KillSwitchAction(BaseModel)`
- **Docstring:** Request schema for kill switch actions.
- **Class Variables:** reason: str, actor: Optional[str]

### `IncidentSummary(BaseModel)`
- **Docstring:** Summary view of an incident.
- **Class Variables:** id: str, title: str, severity: str, status: str, trigger_type: str, calls_affected: int, cost_delta_cents: float, started_at: datetime, ended_at: Optional[datetime], duration_seconds: Optional[int]

### `IncidentDetail(BaseModel)`
- **Docstring:** Detailed view of an incident with timeline.
- **Class Variables:** id: str, title: str, severity: str, status: str, trigger_type: str, trigger_value: Optional[str], calls_affected: int, cost_delta_cents: float, error_rate: Optional[float], auto_action: Optional[str], started_at: datetime, ended_at: Optional[datetime], duration_seconds: Optional[int], timeline: List[Dict[str, Any]]

### `GuardrailSummary(BaseModel)`
- **Docstring:** Summary of active guardrails.
- **Class Variables:** id: str, name: str, description: Optional[str], category: str, action: str, is_enabled: bool, priority: int

### `ProxyCallSummary(BaseModel)`
- **Docstring:** Summary of a proxy call.
- **Class Variables:** id: str, endpoint: str, model: str, status_code: Optional[int], was_blocked: bool, cost_cents: float, input_tokens: int, output_tokens: int, latency_ms: Optional[int], created_at: datetime, replay_eligible: bool

### `ProxyCallDetail(BaseModel)`
- **Docstring:** Detailed view of a proxy call for replay.
- **Class Variables:** id: str, endpoint: str, model: str, request_hash: str, request_body: Dict[str, Any], response_body: Optional[Dict[str, Any]], status_code: Optional[int], error_code: Optional[str], was_blocked: bool, block_reason: Optional[str], policy_decisions: List[Dict[str, Any]], cost_cents: float, input_tokens: int, output_tokens: int, latency_ms: Optional[int], replay_eligible: bool, created_at: datetime

### `ReplayRequest(BaseModel)`
- **Docstring:** Request to replay a call.
- **Class Variables:** dry_run: bool

### `ReplayResult(BaseModel)`
- **Docstring:** Result of a replay operation.
- **Class Variables:** original_call_id: str, replay_call_id: Optional[str], dry_run: bool, same_result: bool, diff: Optional[Dict[str, Any]], enforcement_message: str

### `DemoSimulationRequest(BaseModel)`
- **Docstring:** Request to simulate an incident.
- **Class Variables:** scenario: str

### `DemoSimulationResult(BaseModel)`
- **Docstring:** Result of a demo simulation.
- **Class Variables:** incident_id: str, scenario: str, timeline: List[Dict[str, Any]], cost_saved_cents: float, action_taken: str, message: str, is_demo: bool, demo_warning: str, before: Optional[Dict[str, Any]], after: Optional[Dict[str, Any]], without_killswitch: Optional[Dict[str, Any]]

## Attributes

- `GROUPING_WINDOW_SECONDS` (line 113)
- `GROUPING_MIN_ERRORS` (line 114)
- `GROUPING_ERROR_RATE_THRESHOLD` (line 115)
- `GROUPING_COST_SPIKE_MULTIPLIER` (line 116)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

killswitch API, services

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: EntityType
      methods: []
    - name: TriggerType
      methods: []
    - name: IncidentSeverity
      methods: []
    - name: IncidentStatus
      methods: []
    - name: IncidentLifecycleState
      methods: []
    - name: IncidentCauseType
      methods: []
    - name: GuardrailAction
      methods: []
    - name: GuardrailCategory
      methods: []
    - name: KillSwitchState
      methods: [freeze, unfreeze]
    - name: ProxyCall
      methods: [hash_request, hash_response, set_policy_decisions, get_policy_decisions]
    - name: Incident
      methods: [get_inflection_context, set_inflection_context, set_inflection_point, add_related_call, get_related_call_ids, resolve, acknowledge]
    - name: IncidentEvent
      methods: [set_data, get_data]
    - name: DefaultGuardrail
      methods: [get_rule_config, evaluate]
    - name: KillSwitchStatus
      methods: []
    - name: KillSwitchAction
      methods: []
    - name: IncidentSummary
      methods: []
    - name: IncidentDetail
      methods: []
    - name: GuardrailSummary
      methods: []
    - name: ProxyCallSummary
      methods: []
    - name: ProxyCallDetail
      methods: []
    - name: ReplayRequest
      methods: []
    - name: ReplayResult
      methods: []
    - name: DemoSimulationRequest
      methods: []
    - name: DemoSimulationResult
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
