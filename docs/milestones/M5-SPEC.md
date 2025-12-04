# M5: Failure Catalog v1 Specification

**Version:** 0.1.0
**Status:** DRAFT (Pre-Implementation)
**Duration:** 1 week
**Depends On:** M4 Workflow Engine (COMPLETE)

---

## Objective

Create a structured failure catalog that:
1. Defines 50+ error codes with semantic meaning
2. Maps errors to categories (TRANSIENT, PERMANENT, RESOURCE, PERMISSION, VALIDATION)
3. Provides retry policies per error type
4. Offers recovery suggestions for each error
5. Integrates with workflow engine for structured error handling

---

## Deliverables

| Deliverable | Description | Location |
|-------------|-------------|----------|
| Failure Catalog Schema | JSON Schema for catalog structure | `backend/app/schemas/failure_catalog.schema.json` |
| Failure Catalog Data | Actual error definitions | `backend/app/runtime/failure_catalog.json` |
| FailureCatalog Class | Runtime lookup and matching | `backend/app/runtime/failure_catalog.py` |
| Recovery Mode Taxonomy | Strategy definitions | `backend/app/specs/recovery_modes.md` |
| Error Lookup Rules | Pattern matching logic | `backend/app/runtime/error_matcher.py` |
| Failure Analytics | Query utilities | `backend/app/runtime/failure_analytics.py` |
| Unit Tests | Catalog validation | `backend/tests/runtime/test_failure_catalog.py` |
| Integration Tests | Workflow integration | `backend/tests/integration/test_failure_handling.py` |

---

## Error Categories

### TRANSIENT
Temporary failures that may succeed on retry.

| Code | Description | Retry Policy |
|------|-------------|--------------|
| `TIMEOUT` | Operation timed out | Exponential backoff, 3 retries |
| `DNS_FAILURE` | DNS resolution failed | Exponential backoff, 3 retries |
| `CONNECTION_REFUSED` | Connection refused | Exponential backoff, 3 retries |
| `CONNECTION_RESET` | Connection reset by peer | Exponential backoff, 3 retries |
| `HTTP_500` | Internal server error | Exponential backoff, 3 retries |
| `HTTP_502` | Bad gateway | Exponential backoff, 3 retries |
| `HTTP_503` | Service unavailable | Exponential backoff, 5 retries |
| `HTTP_504` | Gateway timeout | Exponential backoff, 3 retries |
| `NETWORK_UNREACHABLE` | Network unreachable | Exponential backoff, 3 retries |
| `SSL_ERROR` | SSL/TLS error | Retry once, then abort |

### PERMANENT
Failures that will not succeed on retry.

| Code | Description | Retry Policy |
|------|-------------|--------------|
| `HTTP_400` | Bad request | No retry |
| `HTTP_401` | Unauthorized | No retry |
| `HTTP_403` | Forbidden | No retry |
| `HTTP_404` | Not found | No retry |
| `HTTP_405` | Method not allowed | No retry |
| `HTTP_410` | Gone | No retry |
| `HTTP_422` | Unprocessable entity | No retry |
| `INVALID_URL` | Malformed URL | No retry |
| `INVALID_JSON` | JSON parse error | No retry |
| `SCHEMA_VALIDATION_FAILED` | Schema validation error | No retry |

### RESOURCE
Resource limit or budget errors.

| Code | Description | Retry Policy |
|------|-------------|--------------|
| `RATE_LIMITED` | Rate limit exceeded | Wait and retry |
| `HTTP_429` | Too many requests | Wait for Retry-After |
| `BUDGET_EXCEEDED` | Budget limit reached | No retry |
| `QUOTA_EXCEEDED` | Quota exhausted | No retry |
| `MEMORY_LIMIT` | Memory limit exceeded | No retry |
| `DISK_FULL` | Disk space exhausted | No retry |
| `CONCURRENT_LIMIT` | Concurrency limit | Wait and retry |

### PERMISSION
Access control errors.

| Code | Description | Retry Policy |
|------|-------------|--------------|
| `PERMISSION_DENIED` | Access denied | No retry |
| `INSUFFICIENT_SCOPE` | Token scope insufficient | No retry |
| `TOKEN_EXPIRED` | Auth token expired | Refresh and retry |
| `TOKEN_REVOKED` | Auth token revoked | No retry |
| `IP_BLOCKED` | IP address blocked | No retry |
| `TENANT_SUSPENDED` | Tenant suspended | No retry |

### VALIDATION
Input/output validation errors.

| Code | Description | Retry Policy |
|------|-------------|--------------|
| `INVALID_INPUT` | Invalid input parameters | No retry |
| `MISSING_REQUIRED_FIELD` | Required field missing | No retry |
| `TYPE_MISMATCH` | Type validation failed | No retry |
| `RANGE_ERROR` | Value out of range | No retry |
| `FORMAT_ERROR` | Invalid format | No retry |
| `CONSTRAINT_VIOLATION` | Constraint violated | No retry |

### INTERNAL
Internal system errors.

| Code | Description | Retry Policy |
|------|-------------|--------------|
| `INTERNAL_ERROR` | Unexpected internal error | Log and abort |
| `ASSERTION_FAILED` | Assertion failure | Log and abort |
| `STATE_CORRUPTION` | State corruption detected | Log and abort |
| `CHECKPOINT_FAILED` | Checkpoint operation failed | Retry once |
| `GOLDEN_SIGNATURE_INVALID` | Golden file signature invalid | Log and abort |

---

## Recovery Mode Taxonomy

### RETRY_IMMEDIATE
Retry immediately without delay.

```python
config = {
    "max_retries": 1,
    "delay_ms": 0
}
```

### RETRY_EXPONENTIAL
Retry with exponential backoff.

```python
config = {
    "max_retries": 3,
    "base_delay_ms": 1000,
    "max_delay_ms": 30000,
    "multiplier": 2.0
}
```

### RETRY_WITH_JITTER
Retry with exponential backoff plus random jitter.

```python
config = {
    "max_retries": 3,
    "base_delay_ms": 1000,
    "max_delay_ms": 30000,
    "multiplier": 2.0,
    "jitter_factor": 0.25  # ±25%
}
```

### FALLBACK
Use fallback value or alternate path.

```python
config = {
    "fallback_value": null,
    "fallback_skill": "alternative_skill"
}
```

### CIRCUIT_BREAKER
Open circuit after threshold failures.

```python
config = {
    "failure_threshold": 5,
    "reset_timeout_ms": 60000,
    "half_open_requests": 1
}
```

### SKIP
Skip the failed step and continue.

```python
config = {
    "log_level": "WARNING",
    "emit_metric": true
}
```

### ABORT
Abort the workflow immediately.

```python
config = {
    "cleanup": true,
    "notify": true
}
```

### ESCALATE
Escalate to manual intervention.

```python
config = {
    "alert_channel": "critical",
    "timeout_ms": 3600000  # 1 hour
}
```

### CHECKPOINT_RESTORE
Restore from last checkpoint and retry.

```python
config = {
    "max_restore_attempts": 1,
    "checkpoint_age_limit_ms": 300000  # 5 min
}
```

---

## Lookup/Match Rules

### Error Matching Priority

1. **Exact Code Match** - Error code matches exactly
2. **HTTP Status Match** - HTTP status code matches
3. **Exception Type Match** - Exception class matches
4. **Message Pattern Match** - Error message matches regex
5. **Category Default** - Fall back to category default

### Matching Algorithm

```python
def match_error(error: Exception) -> ErrorDefinition:
    # 1. Exact code match
    if hasattr(error, 'code') and error.code in catalog.errors:
        return catalog.errors[error.code]

    # 2. HTTP status match
    if hasattr(error, 'status_code'):
        code = f"HTTP_{error.status_code}"
        if code in catalog.errors:
            return catalog.errors[code]

    # 3. Exception type match
    for error_def in catalog.errors.values():
        if error_def.exception_type == type(error).__name__:
            return error_def

    # 4. Message pattern match
    for error_def in catalog.errors.values():
        if error_def.message_pattern:
            if re.search(error_def.message_pattern, str(error)):
                return error_def

    # 5. Category default
    return catalog.get_default_error()
```

---

## API Design

### FailureCatalog Class

```python
class FailureCatalog:
    """Structured error code registry with recovery strategies."""

    def __init__(self, catalog_path: str = None):
        """Load catalog from JSON file."""

    def get_error(self, code: str) -> Optional[ErrorDefinition]:
        """Look up error by code."""

    def match_error(self, error: Exception) -> ErrorDefinition:
        """Match exception to error definition."""

    def get_recovery_mode(self, error: ErrorDefinition) -> RecoveryMode:
        """Get recovery mode for error."""

    def is_retryable(self, error: ErrorDefinition) -> bool:
        """Check if error is retryable."""

    def get_retry_policy(self, error: ErrorDefinition) -> RetryPolicy:
        """Get retry policy for error."""

    def get_suggestions(self, error: ErrorDefinition) -> List[str]:
        """Get recovery suggestions for error."""

    def register_error(self, error_def: ErrorDefinition) -> None:
        """Register a new error definition."""

    def to_prometheus_labels(self, error: ErrorDefinition) -> Dict[str, str]:
        """Get Prometheus metric labels."""
```

### Integration Points

```python
# In WorkflowEngine
def handle_step_error(self, error: Exception, step: WorkflowStep):
    error_def = self.failure_catalog.match_error(error)
    recovery_mode = self.failure_catalog.get_recovery_mode(error_def)

    if recovery_mode.strategy == "RETRY_EXPONENTIAL":
        return self.retry_with_backoff(step, error_def)
    elif recovery_mode.strategy == "ABORT":
        return self.abort_workflow(error_def)
    # ... etc
```

---

## Failure Analytics

### Query Utilities

```python
class FailureAnalytics:
    """Utilities for analyzing failure patterns."""

    def get_error_distribution(self,
        time_range: TimeRange
    ) -> Dict[str, int]:
        """Get error code distribution."""

    def get_category_breakdown(self,
        time_range: TimeRange
    ) -> Dict[str, int]:
        """Get error category breakdown."""

    def get_retry_success_rate(self,
        error_code: str,
        time_range: TimeRange
    ) -> float:
        """Get retry success rate for error code."""

    def get_recovery_effectiveness(self,
        recovery_mode: str,
        time_range: TimeRange
    ) -> Dict[str, Any]:
        """Get recovery mode effectiveness metrics."""

    def identify_flapping_errors(self,
        threshold: int = 5,
        window_ms: int = 60000
    ) -> List[str]:
        """Identify errors that flap frequently."""
```

---

## Test Strategy

### Unit Tests (No Runtime)

```python
# test_failure_catalog.py
def test_catalog_schema_valid():
    """Validate catalog against JSON schema."""

def test_all_codes_unique():
    """Ensure all error codes are unique."""

def test_all_categories_defined():
    """Ensure all referenced categories exist."""

def test_recovery_modes_valid():
    """Validate recovery mode configurations."""

def test_error_matching_priority():
    """Test error matching priority order."""
```

### Integration Tests (After M5 Implementation)

```python
# test_failure_handling.py
def test_transient_error_retry():
    """Test retry behavior for transient errors."""

def test_permanent_error_no_retry():
    """Test abort behavior for permanent errors."""

def test_rate_limit_backoff():
    """Test rate limit handling with backoff."""
```

---

## Acceptance Criteria

| Criterion | Requirement |
|-----------|-------------|
| Error codes | ≥50 defined |
| Categories | 6 (TRANSIENT, PERMANENT, RESOURCE, PERMISSION, VALIDATION, INTERNAL) |
| Recovery modes | ≥9 defined |
| Schema validation | All errors pass schema |
| Lookup performance | <1ms per lookup |
| Test coverage | ≥90% for catalog module |

---

## Non-Goals (Out of Scope for M5)

- Circuit breaker runtime implementation
- Distributed rate limiting
- Error aggregation service
- External error reporting (Sentry, etc.)
- ML-based error prediction

---

## Related Documents

- [PIN-008](../memory-pins/PIN-008-v1-milestone-plan-full.md) - v1 Milestone Plan
- [Error Taxonomy](../specs/error_taxonomy.md) - M0 Error Taxonomy
- [M4 Completion](../memory-pins/PIN-013-m4-workflow-engine-completion.md) - M4 Status
