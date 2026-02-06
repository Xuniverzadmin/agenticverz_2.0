# hoc_cus_logs_L6_drivers_job_execution

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L6_drivers/job_execution.py` |
| Layer | L6 — Domain Driver |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Job execution support services (retry, progress, audit)

## Intent

**Role:** Job execution support services (retry, progress, audit)
**Reference:** PIN-470, GAP-156 (Retry), GAP-157 (Progress), GAP-158 (Audit)
**Callers:** JobQueueWorker, APSchedulerExecutor

## Purpose

Module: job_execution
Purpose: Job execution support services.

---

## Functions

### `_hash_value(value: Any) -> str`
- **Async:** No
- **Docstring:** Hash a value for audit purposes.
- **Calls:** encode, hexdigest, sha256, str

### `get_job_retry_manager() -> JobRetryManager`
- **Async:** No
- **Docstring:** Get the singleton JobRetryManager.
- **Calls:** JobRetryManager

### `get_job_progress_tracker() -> JobProgressTracker`
- **Async:** No
- **Docstring:** Get the singleton JobProgressTracker.
- **Calls:** JobProgressTracker

### `get_job_audit_emitter() -> JobAuditEmitter`
- **Async:** No
- **Docstring:** Get the singleton JobAuditEmitter.
- **Calls:** JobAuditEmitter

### `reset_job_execution_services() -> None`
- **Async:** No
- **Docstring:** Reset all singletons (for testing).

## Classes

### `RetryStrategy(str, Enum)`
- **Docstring:** Retry strategy types.

### `RetryConfig`
- **Docstring:** Configuration for job retry.
- **Class Variables:** max_retries: int, strategy: RetryStrategy, base_delay_seconds: int, max_delay_seconds: int, jitter_factor: float, retryable_errors: List[str]

### `RetryAttempt`
- **Docstring:** Record of a retry attempt.
- **Class Variables:** attempt_number: int, timestamp: str, delay_seconds: int, error: str, will_retry: bool, next_attempt_at: Optional[str]

### `JobRetryManager`
- **Docstring:** Manages job retry logic with configurable strategies.
- **Methods:** __init__, should_retry, calculate_delay, record_retry, get_retry_history, clear_history

### `ProgressStage(str, Enum)`
- **Docstring:** Standard progress stages.

### `ProgressUpdate`
- **Docstring:** A progress update for a job.
- **Methods:** to_dict
- **Class Variables:** job_id: str, percentage: float, stage: ProgressStage, message: Optional[str], current_step: Optional[int], total_steps: Optional[int], started_at: Optional[str], updated_at: str, eta_seconds: Optional[int], metadata: Dict[str, Any]

### `JobProgressTracker`
- **Docstring:** Tracks and reports job progress.
- **Methods:** __init__, start, update, complete, fail, get_progress, register_callback, _calculate_eta, _emit_progress, _get_publisher

### `JobAuditEventType(str, Enum)`
- **Docstring:** Types of job audit events.

### `JobAuditEvent`
- **Docstring:** Audit event for job execution.
- **Methods:** __post_init__, _compute_integrity_hash, to_dict, verify_integrity
- **Class Variables:** event_id: str, event_type: JobAuditEventType, job_id: str, tenant_id: str, timestamp: str, handler: Optional[str], attempt_number: int, duration_ms: Optional[int], error: Optional[str], payload_hash: Optional[str], result_hash: Optional[str], integrity_hash: Optional[str], previous_event_hash: Optional[str], metadata: Dict[str, Any]

### `JobAuditEmitter`
- **Docstring:** Emits audit events for job execution.
- **Methods:** __init__, _generate_event_id, emit_created, emit_started, emit_completed, emit_failed, emit_retried, _emit, _get_publisher

## Attributes

- `logger` (line 59)
- `_retry_manager: Optional[JobRetryManager]` (line 846)
- `_progress_tracker: Optional[JobProgressTracker]` (line 847)
- `_audit_emitter: Optional[JobAuditEmitter]` (line 848)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.events`, `random` |

## Callers

JobQueueWorker, APSchedulerExecutor

## Export Contract

```yaml
exports:
  functions:
    - name: get_job_retry_manager
      signature: "get_job_retry_manager() -> JobRetryManager"
    - name: get_job_progress_tracker
      signature: "get_job_progress_tracker() -> JobProgressTracker"
    - name: get_job_audit_emitter
      signature: "get_job_audit_emitter() -> JobAuditEmitter"
    - name: reset_job_execution_services
      signature: "reset_job_execution_services() -> None"
  classes:
    - name: RetryStrategy
      methods: []
    - name: RetryConfig
      methods: []
    - name: RetryAttempt
      methods: []
    - name: JobRetryManager
      methods: [should_retry, calculate_delay, record_retry, get_retry_history, clear_history]
    - name: ProgressStage
      methods: []
    - name: ProgressUpdate
      methods: [to_dict]
    - name: JobProgressTracker
      methods: [start, update, complete, fail, get_progress, register_callback]
    - name: JobAuditEventType
      methods: []
    - name: JobAuditEvent
      methods: [to_dict, verify_integrity]
    - name: JobAuditEmitter
      methods: [emit_created, emit_started, emit_completed, emit_failed, emit_retried]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
