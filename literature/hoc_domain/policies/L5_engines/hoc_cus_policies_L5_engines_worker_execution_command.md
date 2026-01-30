# hoc_cus_policies_L5_engines_worker_execution_command

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/worker_execution_command.py` |
| Layer | L4 — Domain Engine (Command Facade) |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Worker execution authorization and delegation

## Intent

**Role:** Worker execution authorization and delegation
**Reference:** PIN-258 Phase F-3 Workers Cluster
**Callers:** workers_adapter.py (L3)

## Purpose

Worker Execution Command (L4)

---

## Functions

### `calculate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> int`
- **Async:** No
- **Docstring:** Calculate LLM cost in cents.  This L4 command delegates to L5 cost calculation.
- **Calls:** calculate_llm_cost_cents

### `get_brand_schema_types()`
- **Async:** No
- **Docstring:** Get brand schema types from L5.  L4 → L5 is an allowed import per layer rules.

### `convert_brand_request(brand_req) -> Any`
- **Async:** No
- **Docstring:** Convert API brand request to BrandSchema.  This L4 command handles the conversion logic using L5 schemas.
- **Calls:** AudienceSegment, BrandSchema, ForbiddenClaim, ToneLevel, ToneRule, VisualIdentity, append, get_brand_schema_types

### `async execute_worker(task: str, brand: Optional[Any], budget: Optional[int], strict_mode: bool, depth: int, run_id: Optional[str], event_bus: Optional[Any]) -> WorkerExecutionResult`
- **Async:** Yes
- **Docstring:** Execute Business Builder Worker.  This L4 command authorizes and delegates execution to L5.
- **Calls:** BusinessBuilderWorker, WorkerExecutionResult, getattr, run

### `async replay_execution(replay_token: str, run_id: str) -> ReplayResult`
- **Async:** Yes
- **Docstring:** Replay a previous execution.  This L4 command authorizes and delegates replay to L5.
- **Calls:** ReplayResult, replay

## Classes

### `WorkerExecutionResult`
- **Docstring:** Result from worker execution command.
- **Class Variables:** success: bool, run_id: str, status: str, artifacts: Optional[Dict[str, Any]], replay_token: Optional[str], cost_report: Optional[Dict[str, Any]], policy_violations: Optional[List[Dict[str, Any]]], recovery_log: Optional[List[Dict[str, Any]]], drift_metrics: Optional[Dict[str, Any]], execution_trace: Optional[List[Dict[str, Any]]], routing_decisions: Optional[List[Dict[str, Any]]], error: Optional[str], total_tokens_used: Optional[int], total_latency_ms: Optional[int]

### `ReplayResult`
- **Docstring:** Result from replay command.
- **Class Variables:** success: bool, run_id: str, status: str, artifacts: Optional[Dict[str, Any]], replay_token: Optional[str], cost_report: Optional[Dict[str, Any]], policy_violations: Optional[List[Dict[str, Any]]], recovery_log: Optional[List[Dict[str, Any]]], drift_metrics: Optional[Dict[str, Any]], execution_trace: Optional[List[Dict[str, Any]]], error: Optional[str], total_tokens_used: Optional[int], total_latency_ms: Optional[int]

## Attributes

- `__all__` (line 341)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.worker.runner`, `app.workers.business_builder.schemas.brand`, `app.workers.business_builder.worker` |

## Callers

workers_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: calculate_cost_cents
      signature: "calculate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> int"
    - name: get_brand_schema_types
      signature: "get_brand_schema_types()"
    - name: convert_brand_request
      signature: "convert_brand_request(brand_req) -> Any"
    - name: execute_worker
      signature: "async execute_worker(task: str, brand: Optional[Any], budget: Optional[int], strict_mode: bool, depth: int, run_id: Optional[str], event_bus: Optional[Any]) -> WorkerExecutionResult"
    - name: replay_execution
      signature: "async replay_execution(replay_token: str, run_id: str) -> ReplayResult"
  classes:
    - name: WorkerExecutionResult
      methods: []
    - name: ReplayResult
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
