# hoc_models_monitor_config

| Field | Value |
|-------|-------|
| Path | `backend/app/models/monitor_config.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Define what signals to monitor during run execution

## Intent

**Role:** Define what signals to monitor during run execution
**Reference:** POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-005
**Callers:** policy/prevention_engine.py, api/policy_monitors.py

## Purpose

Monitor Configuration Model

---

## Classes

### `MonitorMetric(str, Enum)`
- **Docstring:** Metrics that can be monitored.

### `MonitorConfig(SQLModel)`
- **Docstring:** Monitor configuration that defines what signals to collect.
- **Methods:** allowed_rag_sources, allowed_rag_sources, enabled_metrics, is_metric_monitored, to_snapshot
- **Class Variables:** id: Optional[int], config_id: str, policy_id: str, tenant_id: str, monitor_token_usage: bool, monitor_token_per_step: bool, monitor_cost: bool, monitor_burn_rate: bool, burn_rate_window_seconds: int, monitor_rag_access: bool, allowed_rag_sources_json: Optional[str], monitor_latency: bool, monitor_step_count: bool, allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool, created_at: datetime, updated_at: datetime

### `MonitorConfigCreate(BaseModel)`
- **Docstring:** Request model for creating monitor config.
- **Class Variables:** policy_id: str, monitor_token_usage: bool, monitor_token_per_step: bool, monitor_cost: bool, monitor_burn_rate: bool, burn_rate_window_seconds: int, monitor_rag_access: bool, allowed_rag_sources: Optional[list[str]], monitor_latency: bool, monitor_step_count: bool, allow_prompt_logging: bool, allow_response_logging: bool, allow_pii_capture: bool, allow_secret_access: bool

### `MonitorConfigUpdate(BaseModel)`
- **Docstring:** Request model for updating monitor config.
- **Class Variables:** monitor_token_usage: Optional[bool], monitor_token_per_step: Optional[bool], monitor_cost: Optional[bool], monitor_burn_rate: Optional[bool], burn_rate_window_seconds: Optional[int], monitor_rag_access: Optional[bool], allowed_rag_sources: Optional[list[str]], monitor_latency: Optional[bool], monitor_step_count: Optional[bool], allow_prompt_logging: Optional[bool], allow_response_logging: Optional[bool], allow_pii_capture: Optional[bool], allow_secret_access: Optional[bool]

### `MonitorConfigResponse(BaseModel)`
- **Docstring:** Response model for monitor config.
- **Class Variables:** config_id: str, policy_id: str, tenant_id: str, enabled_metrics: list[str], burn_rate_window_seconds: int, allowed_rag_sources: list[str], inspection_constraints: dict, created_at: datetime, updated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

policy/prevention_engine.py, api/policy_monitors.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: MonitorMetric
      methods: []
    - name: MonitorConfig
      methods: [allowed_rag_sources, allowed_rag_sources, enabled_metrics, is_metric_monitored, to_snapshot]
    - name: MonitorConfigCreate
      methods: []
    - name: MonitorConfigUpdate
      methods: []
    - name: MonitorConfigResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
