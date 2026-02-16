# Failure Injection Matrix V1

**Created:** 2026-02-16
**Purpose:** Maps fault scenarios to expected safety outcomes for L6 driver layer.

## Scenario Matrix

| ID | Fault Type | Injected At | Expected Behavior | Severity | Test Reference |
|----|-----------|------------|-------------------|----------|---------------|
| FI-001 | RuntimeError | L6 driver method | Structured error, transaction rollback | CRITICAL | test_driver_exception_returns_safe_error |
| FI-002 | TimeoutError | L6 driver method | Safe fallback, no partial state | HIGH | test_driver_timeout_returns_safe_fallback |
| FI-003 | Stale Read | L6 driver query | Staleness detected via sequence_no | MEDIUM | test_stale_read_detected_by_sequence_check |
| FI-004 | ConnectionRefusedError | L6 driver connection | Service unavailable response | CRITICAL | test_connection_refused_returns_service_unavailable |
| FI-005 | Partial Write | L6 driver write | Transaction rollback, consistent state | CRITICAL | test_partial_write_does_not_corrupt_state |
| FI-006 | Null Result | L6 driver query | Graceful handling, empty response | MEDIUM | test_null_result_from_driver_handled_gracefully |
| FI-007 | IntegrityError (duplicate) | L6 driver insert | Conflict error response | HIGH | test_duplicate_key_error_returns_conflict |
| FI-008 | Serialization Error | L6 driver transaction | Retryable error marker | HIGH | test_serialization_error_retryable |

## Safety Contract

All L6 driver faults MUST result in:
1. Transaction rollback (no partial state persisted)
2. Structured error response (not raw exception propagation)
3. Logging with fault type and context
4. Safe flag indicating the system is in a known-good state

## Escalation Rules

- CRITICAL faults: must be logged as incidents
- HIGH faults: must be logged with alert context
- MEDIUM faults: informational logging only
