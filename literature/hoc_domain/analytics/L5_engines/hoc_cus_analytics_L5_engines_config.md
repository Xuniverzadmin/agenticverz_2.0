# hoc_cus_analytics_L5_engines_config

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/config.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 configuration and feature flags

## Intent

**Role:** CostSim V2 configuration and feature flags
**Reference:** PIN-470
**Callers:** costsim engine, sandbox runner

## Purpose

Feature flags and configuration for CostSim V2 sandbox.

---

## Functions

### `get_config() -> CostSimConfig`
- **Async:** No
- **Docstring:** Get the global CostSim configuration.
- **Calls:** from_env

### `is_v2_sandbox_enabled() -> bool`
- **Async:** No
- **Docstring:** Check if V2 sandbox is enabled.  Returns False if:
- **Calls:** exists, get_config, warning

### `is_v2_disabled_by_drift() -> bool`
- **Async:** No
- **Docstring:** Check if V2 was auto-disabled due to drift.
- **Calls:** exists, get_config

### `get_commit_sha() -> str`
- **Async:** No
- **Docstring:** Get current git commit SHA.
- **Calls:** getenv, run, strip

## Classes

### `CostSimConfig`
- **Docstring:** Configuration for CostSim V2.
- **Methods:** from_env
- **Class Variables:** v2_sandbox_enabled: bool, auto_disable_enabled: bool, canary_enabled: bool, drift_threshold: float, drift_warning_threshold: float, schema_error_threshold: int, failure_threshold: int, auto_recover_enabled: bool, default_disable_ttl_hours: int, provenance_enabled: bool, provenance_compress: bool, disable_file_path: str, incident_dir: str, artifacts_dir: str, alertmanager_url: Optional[str], alertmanager_timeout_seconds: int, alertmanager_retry_attempts: int, alertmanager_retry_delay_seconds: float, instance_id: str, adapter_version: str, model_version: str, v2_table_prefix: str, use_db_circuit_breaker: bool

## Attributes

- `logger` (line 38)
- `_config: Optional[CostSimConfig]` (line 116)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `subprocess` |

## Callers

costsim engine, sandbox runner

## Export Contract

```yaml
exports:
  functions:
    - name: get_config
      signature: "get_config() -> CostSimConfig"
    - name: is_v2_sandbox_enabled
      signature: "is_v2_sandbox_enabled() -> bool"
    - name: is_v2_disabled_by_drift
      signature: "is_v2_disabled_by_drift() -> bool"
    - name: get_commit_sha
      signature: "get_commit_sha() -> str"
  classes:
    - name: CostSimConfig
      methods: [from_env]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
