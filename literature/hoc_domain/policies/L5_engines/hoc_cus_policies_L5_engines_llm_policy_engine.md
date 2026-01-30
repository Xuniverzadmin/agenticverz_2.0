# hoc_cus_policies_L5_engines_llm_policy_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/llm_policy_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

LLM policy and safety limits enforcement (pure logic)

## Intent

**Role:** LLM policy and safety limits enforcement (pure logic)
**Reference:** PIN-470, PIN-254 Phase B Fix
**Callers:** OpenAIAdapter (L3), TenantLLMConfig (L3), llm_invoke skills

## Purpose

L4 LLM Policy Engine - Domain Authority for LLM Safety and Cost Controls

---

## Functions

### `estimate_tokens(text: str) -> int`
- **Async:** No
- **Docstring:** Estimate token count for text (L4 domain function).  Uses rough approximation of 4 chars per token.
- **Calls:** len

### `estimate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> float`
- **Async:** No
- **Docstring:** Estimate cost in cents (L4 domain function).  Args:
- **Calls:** get

### `check_safety_limits(model: str, max_tokens: int, estimated_input_tokens: int, provider: str, max_tokens_limit: Optional[int], max_cost_cents_limit: Optional[float]) -> SafetyCheckResult`
- **Async:** No
- **Docstring:** Check safety limits before making LLM API call (L4 domain function).  L3 adapters must call this before invoking LLM APIs.
- **Calls:** SafetyCheckResult, check_and_record, estimate_cost_cents, get_instance, requests_remaining

### `is_model_allowed(model: str, tenant_allowed_models: Optional[List[str]]) -> bool`
- **Async:** No
- **Docstring:** Check if a model is allowed (L4 domain function).  Args:

### `is_expensive_model(model: str) -> bool`
- **Async:** No
- **Docstring:** Check if a model is classified as expensive (L4 domain function).

### `get_model_for_task(task_type: str, requested_model: Optional[str], tenant_allowed_models: Optional[List[str]], allow_expensive: bool) -> str`
- **Async:** No
- **Docstring:** Get appropriate model for a task type (L4 policy decision).  L3 TenantLLMConfig must delegate model selection to this function.
- **Calls:** get, is_expensive_model, is_model_allowed, warning

### `get_effective_model(requested_model: Optional[str], preferred_model: str, fallback_model: str, allowed_models: List[str]) -> str`
- **Async:** No
- **Docstring:** Get effective model based on request and tenant config (L4 policy decision).  L3 TenantLLMConfig.get_effective_model() must delegate to this.

## Classes

### `SafetyCheckResult`
- **Docstring:** Result of a safety limit check.
- **Class Variables:** allowed: bool, error_type: Optional[str], error_message: Optional[str], retryable: bool, details: Dict[str, Any]

### `LLMRateLimiter`
- **Docstring:** Sliding window rate limiter for LLM requests (L4 policy enforcement).
- **Methods:** get_instance, __init__, check_and_record, requests_remaining
- **Class Variables:** _instances: Dict[str, 'LLMRateLimiter']

## Attributes

- `logger` (line 47)
- `LLM_MAX_TOKENS_PER_REQUEST` (line 56)
- `LLM_MAX_COST_CENTS_PER_REQUEST` (line 59)
- `LLM_REQUESTS_PER_MINUTE` (line 62)
- `_allowed_models_str` (line 65)
- `LLM_ALLOWED_MODELS: Optional[List[str]]` (line 66)
- `DEFAULT_MODELS` (line 76)
- `FALLBACK_MODEL` (line 82)
- `SYSTEM_ALLOWED_MODELS: List[str]` (line 85)
- `EXPENSIVE_MODELS: List[str]` (line 93)
- `TASK_MODEL_POLICY: Dict[str, str]` (line 100)
- `LLM_COST_MODEL: Dict[str, Dict[str, float]]` (line 113)
- `__all__` (line 421)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

OpenAIAdapter (L3), TenantLLMConfig (L3), llm_invoke skills

## Export Contract

```yaml
exports:
  functions:
    - name: estimate_tokens
      signature: "estimate_tokens(text: str) -> int"
    - name: estimate_cost_cents
      signature: "estimate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> float"
    - name: check_safety_limits
      signature: "check_safety_limits(model: str, max_tokens: int, estimated_input_tokens: int, provider: str, max_tokens_limit: Optional[int], max_cost_cents_limit: Optional[float]) -> SafetyCheckResult"
    - name: is_model_allowed
      signature: "is_model_allowed(model: str, tenant_allowed_models: Optional[List[str]]) -> bool"
    - name: is_expensive_model
      signature: "is_expensive_model(model: str) -> bool"
    - name: get_model_for_task
      signature: "get_model_for_task(task_type: str, requested_model: Optional[str], tenant_allowed_models: Optional[List[str]], allow_expensive: bool) -> str"
    - name: get_effective_model
      signature: "get_effective_model(requested_model: Optional[str], preferred_model: str, fallback_model: str, allowed_models: List[str]) -> str"
  classes:
    - name: SafetyCheckResult
      methods: []
    - name: LLMRateLimiter
      methods: [get_instance, check_and_record, requests_remaining]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
