# Error Taxonomy v1

Purpose: canonicalize error codes, categories, retryability hints, and suggested operator actions.
This file is the single source of truth for StructuredOutcome.code for failures.

## Structure
Each entry:
- code: machine code (ERR_... or OK_...)
- category: one of [transient, permanent, client, infra, policy, safety, third_party]
- retryable: boolean (whether runtime may retry automatically)
- severity: one of [info, warning, error, critical]
- suggested_actions: short list of actions for runtime/operator

---

## Success Codes

### OK
- category: success
- severity: info
- description: Generic success code

### OK_HTTP_CALL
- category: success
- severity: info
- description: HTTP call completed successfully

### OK_LLM_INVOKE
- category: success
- severity: info
- description: LLM invocation completed successfully

### OK_JSON_TRANSFORM
- category: success
- severity: info
- description: JSON transformation completed successfully

---

## Error Codes

### ERR_HTTP_TIMEOUT
- category: transient
- retryable: true
- severity: warning
- suggested_actions:
  - retry with backoff
  - if repeated, increase timeout for this endpoint or add circuit-breaker
  - record endpoint latency distribution

### ERR_HTTP_4XX
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - surface to operator / user with upstream response
  - check request payload & auth

### ERR_HTTP_400
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check request payload format
  - validate against expected schema

### ERR_HTTP_401
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check authentication credentials
  - refresh tokens if applicable

### ERR_HTTP_403
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check authorization permissions
  - verify resource access rights

### ERR_HTTP_404
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - verify resource URL
  - check if resource was deleted

### ERR_HTTP_429
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - respect Retry-After header if present
  - exponential backoff
  - consider rate limit strategy

### ERR_RATE_LIMIT_INTERNAL
- category: policy
- retryable: true
- severity: warning
- suggested_actions:
  - wait for rate limit window to reset
  - exponential backoff with jitter
  - check agent rate_limits configuration
  - surface limit details to operator (requests_per_minute, current_count)
- notes:
  - This is AOS internal rate limiting, NOT provider throttling (ERR_HTTP_429)
  - Applies per-agent or per-tenant based on configuration
  - Retry-After should be calculated from limiter state

### ERR_RATE_LIMIT_CONCURRENT
- category: policy
- retryable: true
- severity: warning
- suggested_actions:
  - wait for concurrent run slot to free
  - check max_concurrent_runs in agent profile
  - consider queueing strategy
- notes:
  - Triggered when agent exceeds max concurrent runs
  - Different from request rate limiting

### ERR_HTTP_5XX
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - retry with exponential backoff
  - if persistent, mark provider unhealthy and fail fast for subsequent calls

### ERR_HTTP_500
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - retry with backoff
  - log upstream error details

### ERR_HTTP_502
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - retry with backoff
  - check upstream gateway health

### ERR_HTTP_503
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - retry with backoff
  - respect Retry-After if present
  - service may be in maintenance

### ERR_HTTP_504
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - retry with backoff
  - upstream timeout - consider longer timeout

### ERR_DNS_FAILURE
- category: infra
- retryable: true
- severity: error
- suggested_actions:
  - retry with backoff
  - record DNS errors for alerting
  - verify hostname is correct

### ERR_CONNECTION_REFUSED
- category: infra
- retryable: true
- severity: error
- suggested_actions:
  - retry with backoff
  - check if service is running
  - verify port and host

### ERR_SSL_ERROR
- category: infra
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check certificate validity
  - verify SSL configuration

### ERR_LLM_RATE_LIMIT
- category: third_party
- retryable: true
- severity: warning
- suggested_actions:
  - respect Retry-After if present
  - route to alternative model if available
  - decrement budget estimate / alert operator

### ERR_LLM_INVALID_RESPONSE
- category: third_party
- retryable: false
- severity: error
- suggested_actions:
  - do not retry automatically
  - mark attempt as failed; surface to human
  - log full response for debugging

### ERR_LLM_CONTEXT_LENGTH
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - truncate input or use summarization
  - consider model with larger context

### ERR_LLM_CONTENT_FILTER
- category: safety
- retryable: false
- severity: warning
- suggested_actions:
  - do not retry
  - log content filter trigger
  - may need human review

### ERR_LLM_API_ERROR
- category: third_party
- retryable: true
- severity: error
- suggested_actions:
  - retry with backoff
  - check LLM provider status
  - consider fallback model

### ERR_VALIDATION_FAILED
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - return structured validation errors to caller
  - fail the run early
  - include field-level error details

### ERR_SCHEMA_MISMATCH
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - validate input against expected schema
  - surface schema diff to operator

### ERR_POLICY_VIOLATION
- category: policy
- retryable: false
- severity: critical
- suggested_actions:
  - stop execution
  - surface policy violation to operator
  - include relevant policy id and reason

### ERR_BUDGET_EXCEEDED
- category: policy
- retryable: false
- severity: critical
- suggested_actions:
  - stop execution immediately
  - notify operator of budget exhaustion
  - do not attempt any more billable operations

### ERR_QUOTA_EXCEEDED
- category: policy
- retryable: false
- severity: error
- suggested_actions:
  - stop execution
  - wait for quota reset or request increase
  - surface quota details to operator

### ERR_PERMISSION_DENIED
- category: policy
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check agent permissions
  - verify skill is in allowed_operations

### ERR_SAFETY_REJECTED
- category: safety
- retryable: false
- severity: critical
- suggested_actions:
  - do not retry
  - escalate to human review if configured
  - log rejection reason

### ERR_PROMPT_INJECTION
- category: safety
- retryable: false
- severity: critical
- suggested_actions:
  - do not retry
  - log full input for security review
  - alert security team

### ERR_INTERNAL
- category: infra
- retryable: true
- severity: error
- suggested_actions:
  - retry with backoff
  - collect debug trace; alert SRE if frequent
  - include stack trace in details

### ERR_STORAGE_QUOTA_EXCEEDED
- category: infra
- retryable: false
- severity: error
- suggested_actions:
  - surface to operator
  - provide cleanup instructions
  - check storage usage

### ERR_SKILL_NOT_FOUND
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - verify skill_id exists in registry
  - check skill version

### ERR_SKILL_DISABLED
- category: policy
- retryable: false
- severity: warning
- suggested_actions:
  - do not retry
  - check why skill was disabled
  - use alternative skill if available

### ERR_SERIALIZATION_FAILED
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check data types are JSON-serializable
  - validate output format

### ERR_DESERIALIZATION_FAILED
- category: client
- retryable: false
- severity: error
- suggested_actions:
  - do not retry
  - check response format
  - validate against expected schema

### ERR_TIMEOUT
- category: transient
- retryable: true
- severity: warning
- suggested_actions:
  - retry with backoff
  - consider increasing timeout
  - check for slow operations

### ERR_UNKNOWN
- category: infra
- retryable: false
- severity: error
- suggested_actions:
  - log full error details
  - investigate root cause
  - add specific error code if pattern emerges

---

## Guiding Rules

1. **Codes must be stable:** once a code is emitted in production, do not change semantic meaning.

2. **Retryability is orthogonal to severity.** E.g., transient but critical errors can still be retried.

3. **Small, precise codes beat huge, catch-all codes.** Prefer ERR_HTTP_429 to a generic ERR_THROTTLE.

4. **Include upstream hints** in StructuredOutcome.details (e.g., upstream_status, retry_after, provider_name).

5. **Failure catalog** (M5) should seed from these codes and map code → {category, retryable, suggestions}.

6. **New codes require changelog entry.** Document when added and why.

---

## Category Definitions

| Category | Description | Typical Retryable |
|----------|-------------|-------------------|
| transient | Temporary failure, may resolve | Yes |
| permanent | Will not resolve without change | No |
| client | Caller error (bad input, auth) | No |
| infra | Internal infrastructure issue | Sometimes |
| policy | Policy/budget/quota violation | No |
| safety | Safety/security rejection | No |
| third_party | External service issue | Sometimes |
| success | Operation completed | N/A |

---

## Severity Definitions

| Severity | Description | Alert Level |
|----------|-------------|-------------|
| info | Normal operation | None |
| warning | Degraded but recoverable | Low |
| error | Failure requiring attention | Medium |
| critical | Immediate attention needed | High |

---

## Changelog

| Date | Code | Change |
|------|------|--------|
| 2025-12-01 | ERR_RATE_LIMIT_INTERNAL | Added internal rate limiting error |
| 2025-12-01 | ERR_RATE_LIMIT_CONCURRENT | Added concurrent runs limit error |
| 2025-12-01 | * | Initial taxonomy v1 |
