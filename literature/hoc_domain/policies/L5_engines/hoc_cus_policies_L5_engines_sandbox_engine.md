# hoc_cus_policies_L5_engines_sandbox_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/sandbox_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

High-level sandbox engine with policy enforcement (pure business logic)

## Intent

**Role:** High-level sandbox engine with policy enforcement (pure business logic)
**Reference:** PIN-470, GAP-174 (Execution Sandboxing)
**Callers:** Runtime, API routes, Skill executors

## Purpose

Sandbox Service (GAP-174)

---

## Classes

### `SandboxPolicy`
- **Docstring:** Policy for sandbox execution.
- **Methods:** to_resource_limits, to_dict
- **Class Variables:** policy_id: str, name: str, isolation_level: IsolationLevel, network_policy: NetworkPolicy, max_cpu_seconds: float, max_memory_mb: int, max_wall_time_seconds: float, max_processes: int, max_file_size_mb: int, allowed_languages: Set[str], max_executions_per_minute: int, max_executions_per_hour: int, allow_network: bool, allow_file_write: bool, require_approval: bool

### `ExecutionRequest`
- **Docstring:** Request to execute code in a sandbox.
- **Class Variables:** code: str, language: str, policy_id: Optional[str], environment: Optional[Dict[str, str]], files: Optional[Dict[str, bytes]], tenant_id: Optional[str], user_id: Optional[str], run_id: Optional[str], metadata: Dict[str, Any]

### `ExecutionRecord`
- **Docstring:** Record of a sandbox execution for audit.
- **Methods:** to_dict
- **Class Variables:** record_id: str, sandbox_id: str, tenant_id: Optional[str], user_id: Optional[str], run_id: Optional[str], language: str, code_hash: str, policy_id: str, status: SandboxStatus, exit_code: Optional[int], wall_time_seconds: Optional[float], created_at: datetime, completed_at: Optional[datetime], error_message: Optional[str]

### `SandboxService`
- **Docstring:** High-level sandbox service.
- **Methods:** __init__, _setup_default_policies, _get_executor, execute, _get_policy, _check_quota, _track_execution, define_policy, get_policy, list_policies, get_execution_records, get_execution_stats

## Attributes

- `logger` (line 47)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sandbox_executor` |

## Callers

Runtime, API routes, Skill executors

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SandboxPolicy
      methods: [to_resource_limits, to_dict]
    - name: ExecutionRequest
      methods: []
    - name: ExecutionRecord
      methods: [to_dict]
    - name: SandboxService
      methods: [execute, define_policy, get_policy, list_policies, get_execution_records, get_execution_stats]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
