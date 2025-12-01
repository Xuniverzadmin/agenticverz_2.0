# Error Contract Specification

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Status:** ACTIVE

---

## Overview

This document defines the error handling contract for AOS skills. All skills MUST follow these rules for error classification, retry policies, and deterministic error behavior.

---

## Error Categories

### Category Definitions

| Category | Code | Description | Retryable | Default Retry Budget |
|----------|------|-------------|-----------|---------------------|
| `TRANSIENT` | T | Temporary failures that may resolve | YES | 3 retries |
| `RATE_LIMIT` | R | Rate limiting from external services | YES | 3 retries with backoff |
| `CLIENT_ERROR` | C | Invalid request/input (4xx) | NO | 0 retries |
| `SERVER_ERROR` | S | Remote server failures (5xx) | YES | 2 retries |
| `AUTH_FAIL` | A | Authentication/authorization failure | NO | 0 retries |
| `NETWORK` | N | Network connectivity issues | YES | 3 retries |
| `VALIDATION` | V | Schema/input validation failure | NO | 0 retries |
| `RESOURCE` | X | Resource exhaustion (budget, quota) | CONDITIONAL | 0-1 retries |
| `TIMEOUT` | O | Operation timeout | YES | 2 retries |
| `PERMANENT` | P | Non-recoverable failures | NO | 0 retries |

### Category → Retryability Rules

```python
RETRYABLE_CATEGORIES = {
    "TRANSIENT": True,
    "RATE_LIMIT": True,
    "CLIENT_ERROR": False,
    "SERVER_ERROR": True,
    "AUTH_FAIL": False,
    "NETWORK": True,
    "VALIDATION": False,
    "RESOURCE": False,  # Conditional - depends on context
    "TIMEOUT": True,
    "PERMANENT": False,
}
```

---

## Error Code Mappings

### HTTP Status Code → Error Category

| HTTP Status | Error Code | Category | Retryable |
|-------------|------------|----------|-----------|
| 400 | `ERR_HTTP_400_BAD_REQUEST` | CLIENT_ERROR | NO |
| 401 | `ERR_HTTP_401_UNAUTHORIZED` | AUTH_FAIL | NO |
| 403 | `ERR_HTTP_403_FORBIDDEN` | AUTH_FAIL | NO |
| 404 | `ERR_HTTP_404_NOT_FOUND` | CLIENT_ERROR | NO |
| 408 | `ERR_HTTP_408_TIMEOUT` | TIMEOUT | YES |
| 409 | `ERR_HTTP_409_CONFLICT` | CLIENT_ERROR | NO |
| 422 | `ERR_HTTP_422_UNPROCESSABLE` | VALIDATION | NO |
| 429 | `ERR_HTTP_429_RATE_LIMITED` | RATE_LIMIT | YES |
| 500 | `ERR_HTTP_500_SERVER_ERROR` | SERVER_ERROR | YES |
| 502 | `ERR_HTTP_502_BAD_GATEWAY` | SERVER_ERROR | YES |
| 503 | `ERR_HTTP_503_UNAVAILABLE` | TRANSIENT | YES |
| 504 | `ERR_HTTP_504_GATEWAY_TIMEOUT` | TIMEOUT | YES |

### Network Error → Error Category

| Exception Type | Error Code | Category | Retryable |
|----------------|------------|----------|-----------|
| `ConnectionError` | `ERR_CONNECTION_REFUSED` | NETWORK | YES |
| `TimeoutError` | `ERR_TIMEOUT` | TIMEOUT | YES |
| `DNSError` | `ERR_DNS_FAILURE` | NETWORK | YES |
| `SSLError` | `ERR_SSL_ERROR` | NETWORK | NO |
| `SocketError` | `ERR_SOCKET_ERROR` | NETWORK | YES |

### LLM Provider Error → Error Category

| Provider Error | Error Code | Category | Retryable |
|----------------|------------|----------|-----------|
| Rate limited | `ERR_LLM_RATE_LIMITED` | RATE_LIMIT | YES |
| Context too long | `ERR_LLM_CONTEXT_LENGTH` | VALIDATION | NO |
| Invalid model | `ERR_LLM_INVALID_MODEL` | CLIENT_ERROR | NO |
| Content filtered | `ERR_LLM_CONTENT_FILTER` | PERMANENT | NO |
| API error | `ERR_LLM_API_ERROR` | TRANSIENT | YES |
| Auth failure | `ERR_LLM_AUTH_FAILURE` | AUTH_FAIL | NO |

### JSON Transform Error → Error Category

| Error Type | Error Code | Category | Retryable |
|------------|------------|----------|-----------|
| Invalid JSON | `ERR_JSON_INVALID` | VALIDATION | NO |
| Invalid path | `ERR_JSON_PATH_INVALID` | VALIDATION | NO |
| Schema mismatch | `ERR_JSON_SCHEMA_MISMATCH` | VALIDATION | NO |
| Transform failed | `ERR_JSON_TRANSFORM_FAILED` | PERMANENT | NO |
| Depth exceeded | `ERR_JSON_DEPTH_EXCEEDED` | VALIDATION | NO |
| Size exceeded | `ERR_JSON_SIZE_EXCEEDED` | VALIDATION | NO |

---

## Retry Policy

### Default Retry Configuration

```python
DEFAULT_RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay_ms": 100,
    "max_delay_ms": 5000,
    "backoff_multiplier": 2.0,
    "jitter_enabled": True,
    "jitter_range": 0.1,  # ±10% jitter
}
```

### Deterministic Retry Behavior

For **deterministic** planners/skills, retry behavior MUST be seeded:

```python
def compute_retry_delay(
    attempt: int,
    config: RetryConfig,
    seed: Optional[int] = None
) -> int:
    """
    Compute deterministic retry delay.

    Args:
        attempt: Current retry attempt (0-indexed)
        config: Retry configuration
        seed: Optional seed for deterministic jitter

    Returns:
        Delay in milliseconds
    """
    base_delay = min(
        config.initial_delay_ms * (config.backoff_multiplier ** attempt),
        config.max_delay_ms
    )

    if config.jitter_enabled:
        if seed is not None:
            # Deterministic jitter using seed
            import hashlib
            jitter_hash = hashlib.sha256(f"{seed}:{attempt}".encode()).digest()
            jitter_value = int.from_bytes(jitter_hash[:4], 'big') / (2**32)
        else:
            # Non-deterministic jitter
            import random
            jitter_value = random.random()

        jitter_range = base_delay * config.jitter_range
        base_delay += jitter_range * (2 * jitter_value - 1)

    return int(base_delay)
```

### Category-Specific Retry Limits

| Category | Max Retries | Initial Delay | Max Delay | Backoff |
|----------|-------------|---------------|-----------|---------|
| TRANSIENT | 3 | 100ms | 5000ms | 2.0x |
| RATE_LIMIT | 3 | 1000ms | 30000ms | 2.0x |
| SERVER_ERROR | 2 | 500ms | 10000ms | 2.0x |
| TIMEOUT | 2 | 200ms | 5000ms | 1.5x |
| NETWORK | 3 | 100ms | 5000ms | 2.0x |

---

## Error Response Structure

### StructuredOutcome Error Format

All skills MUST return errors using `StructuredOutcome`:

```python
@dataclass
class ErrorInfo:
    """Structured error information."""
    code: str              # Error code from error_taxonomy.md
    message: str           # Human-readable message
    category: str          # Error category (TRANSIENT, PERMANENT, etc.)
    retryable: bool        # Whether retry may succeed
    details: Dict[str, Any] = field(default_factory=dict)
    retry_after_ms: Optional[int] = None  # Suggested retry delay
    upstream_status: Optional[int] = None  # HTTP status if applicable
    provider: Optional[str] = None         # Provider name if applicable

# Example error response
StructuredOutcome.failure(
    code="ERR_HTTP_429_RATE_LIMITED",
    message="Rate limit exceeded for api.example.com",
    category="RATE_LIMIT",
    retryable=True,
    details={
        "upstream_status": 429,
        "rate_limit_remaining": 0,
        "rate_limit_reset": "2025-12-01T12:00:00Z",
        "provider": "example_api"
    },
    retry_after_ms=60000
)
```

### Required Error Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | YES | Error code from error_taxonomy |
| `message` | string | YES | Human-readable description |
| `category` | string | YES | Error category |
| `retryable` | bool | YES | Whether retry may help |
| `details` | dict | NO | Additional context |
| `retry_after_ms` | int | NO | Suggested retry delay |

---

## Idempotency Rules

### Idempotent Operations

Skills MUST declare idempotency in their descriptor:

```python
SkillDescriptor(
    skill_id="skill.http_call",
    idempotent=True,  # GET, HEAD, OPTIONS, PUT (if replacing)
    # ...
)
```

### Non-Idempotent Operations

For non-idempotent operations (POST, DELETE, etc.), callers MUST provide idempotency key:

```python
# Caller provides idempotency key
params = {
    "url": "https://api.example.com/orders",
    "method": "POST",
    "body": {"item": "widget"},
    "idempotency_key": "order-123-attempt-1"  # REQUIRED
}

# Skill validates idempotency key
if not params.get("method", "GET") in ["GET", "HEAD", "OPTIONS"]:
    if "idempotency_key" not in params:
        return StructuredOutcome.failure(
            code="ERR_MISSING_IDEMPOTENCY_KEY",
            message="Non-idempotent operation requires idempotency_key",
            category="VALIDATION",
            retryable=False
        )
```

### Idempotency Key Requirements

1. Key MUST be unique per logical operation
2. Key SHOULD include attempt number if retrying
3. Key format: `{operation}-{id}-attempt-{n}`
4. Skills SHOULD cache results by idempotency key
5. Cache TTL: 24 hours minimum

---

## Terminal vs Retryable Errors

### Terminal (No Retry)

Errors that will NEVER succeed on retry:

- `ERR_HTTP_400_BAD_REQUEST` - Invalid request format
- `ERR_HTTP_401_UNAUTHORIZED` - Authentication required
- `ERR_HTTP_403_FORBIDDEN` - Permission denied
- `ERR_HTTP_404_NOT_FOUND` - Resource doesn't exist
- `ERR_VALIDATION_FAILED` - Input doesn't match schema
- `ERR_JSON_INVALID` - Input is not valid JSON
- `ERR_LLM_CONTENT_FILTER` - Content rejected by safety filter
- `ERR_BUDGET_EXCEEDED` - Hard budget limit reached

### Retryable (May Succeed)

Errors that MAY succeed on retry:

- `ERR_HTTP_429_RATE_LIMITED` - Wait and retry
- `ERR_HTTP_503_UNAVAILABLE` - Service temporarily down
- `ERR_TIMEOUT` - Operation timed out
- `ERR_CONNECTION_REFUSED` - Network glitch
- `ERR_LLM_RATE_LIMITED` - Provider throttling
- `ERR_DNS_FAILURE` - DNS lookup failed

### Conditional (Context-Dependent)

Errors where retry depends on context:

- `ERR_RESOURCE_EXHAUSTED` - If budget can be increased
- `ERR_HTTP_500_SERVER_ERROR` - May be transient or permanent
- `ERR_LLM_API_ERROR` - Depends on underlying cause

---

## Error Handling Examples

### http_call Error Handling

```python
async def execute(params: Dict[str, Any]) -> StructuredOutcome:
    try:
        response = await httpx_client.request(
            method=params["method"],
            url=params["url"],
            **kwargs
        )

        if response.status_code >= 400:
            return _map_http_error(response)

        return StructuredOutcome.success(
            result={
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if is_json(response) else response.text
            }
        )

    except httpx.TimeoutException:
        return StructuredOutcome.failure(
            code="ERR_TIMEOUT",
            message="HTTP request timed out",
            category="TIMEOUT",
            retryable=True,
            details={"url": params["url"], "timeout_ms": params.get("timeout_ms", 30000)}
        )

    except httpx.ConnectError as e:
        return StructuredOutcome.failure(
            code="ERR_CONNECTION_REFUSED",
            message=f"Failed to connect: {e}",
            category="NETWORK",
            retryable=True,
            details={"url": params["url"]}
        )

def _map_http_error(response) -> StructuredOutcome:
    """Map HTTP status to error category."""
    status = response.status_code

    ERROR_MAP = {
        400: ("ERR_HTTP_400_BAD_REQUEST", "CLIENT_ERROR", False),
        401: ("ERR_HTTP_401_UNAUTHORIZED", "AUTH_FAIL", False),
        403: ("ERR_HTTP_403_FORBIDDEN", "AUTH_FAIL", False),
        404: ("ERR_HTTP_404_NOT_FOUND", "CLIENT_ERROR", False),
        429: ("ERR_HTTP_429_RATE_LIMITED", "RATE_LIMIT", True),
        500: ("ERR_HTTP_500_SERVER_ERROR", "SERVER_ERROR", True),
        502: ("ERR_HTTP_502_BAD_GATEWAY", "SERVER_ERROR", True),
        503: ("ERR_HTTP_503_UNAVAILABLE", "TRANSIENT", True),
        504: ("ERR_HTTP_504_GATEWAY_TIMEOUT", "TIMEOUT", True),
    }

    code, category, retryable = ERROR_MAP.get(
        status,
        (f"ERR_HTTP_{status}", "SERVER_ERROR" if status >= 500 else "CLIENT_ERROR", status >= 500)
    )

    return StructuredOutcome.failure(
        code=code,
        message=f"HTTP {status}: {response.reason_phrase}",
        category=category,
        retryable=retryable,
        details={
            "upstream_status": status,
            "upstream_body": response.text[:1000],
            "url": str(response.url)
        },
        retry_after_ms=int(response.headers.get("Retry-After", 0)) * 1000 or None
    )
```

### llm_invoke Error Handling

```python
async def execute(params: Dict[str, Any]) -> StructuredOutcome:
    try:
        response = await client.messages.create(
            model=params["model"],
            messages=params["messages"],
            max_tokens=params.get("max_tokens", 1024)
        )

        return StructuredOutcome.success(
            result={
                "content": response.content[0].text,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "finish_reason": response.stop_reason
            }
        )

    except anthropic.RateLimitError as e:
        return StructuredOutcome.failure(
            code="ERR_LLM_RATE_LIMITED",
            message="Anthropic rate limit exceeded",
            category="RATE_LIMIT",
            retryable=True,
            details={"provider": "anthropic", "model": params["model"]},
            retry_after_ms=60000
        )

    except anthropic.BadRequestError as e:
        if "context_length" in str(e).lower():
            return StructuredOutcome.failure(
                code="ERR_LLM_CONTEXT_LENGTH",
                message="Input exceeds model context length",
                category="VALIDATION",
                retryable=False,
                details={"provider": "anthropic", "model": params["model"]}
            )
        return StructuredOutcome.failure(
            code="ERR_LLM_API_ERROR",
            message=str(e),
            category="CLIENT_ERROR",
            retryable=False
        )
```

---

## Determinism Contract

### Error Determinism Rules

1. **Error codes MUST be deterministic** - Same error condition → Same error code
2. **Error categories MUST be deterministic** - Same error code → Same category
3. **Retryability MUST be deterministic** - Same error code → Same retryable flag
4. **Error messages MAY vary** - Messages can include runtime context
5. **Details MAY vary** - Timestamps, request IDs can change

### Replay-Safe Error Fields

| Field | Deterministic | Notes |
|-------|---------------|-------|
| `code` | YES | Must match exactly |
| `category` | YES | Must match exactly |
| `retryable` | YES | Must match exactly |
| `message` | NO | Can vary |
| `details` | PARTIAL | Keys deterministic, some values can vary |
| `retry_after_ms` | NO | Can vary based on external headers |

---

## CI Enforcement

### Error Contract Tests

CI MUST verify:

1. All skills return `StructuredOutcome` for errors
2. Error codes match `error_taxonomy.md`
3. Error categories are valid
4. Retryability matches category rules
5. Terminal errors have `retryable=False`
6. Rate limit errors include `retry_after_ms` when available

### Test Pattern

```python
def test_skill_returns_structured_errors():
    """All error paths must return StructuredOutcome."""
    outcome = skill.execute(invalid_params)

    assert outcome.ok is False
    assert outcome.error is not None
    assert "code" in outcome.error
    assert "category" in outcome.error
    assert "retryable" in outcome.error

    # Verify code matches taxonomy
    assert outcome.error["code"] in VALID_ERROR_CODES

    # Verify category is valid
    assert outcome.error["category"] in VALID_CATEGORIES
```

---

## References

- `app/specs/error_taxonomy.md` - Complete error code list
- `app/specs/determinism_and_replay.md` - Determinism rules
- `app/worker/runtime/core.py` - StructuredOutcome implementation
