# PIN-068: M13 Prompt Caching Implementation

**Date:** 2025-12-14
**Status:** COMPLETE
**Version:** 1.0.0
**Category:** Feature / Cost Optimization

---

## Summary

Implemented in-memory prompt caching for `llm_invoke` skill to reduce LLM API costs by reusing responses for identical requests.

---

## Problem Statement

Every LLM call costs money. Many agent workflows make repeated identical calls:
- Retry loops with same prompt
- Template-based generation with same parameters
- Testing/debugging with repeated requests

Without caching, each call incurs full API cost even when the response would be identical.

---

## Solution

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      llm_invoke.execute()                    │
├─────────────────────────────────────────────────────────────┤
│  1. Parse input params                                       │
│  2. Generate cache key (SHA256)                              │
│  3. Check cache ──────────────┬── HIT ──► Return cached      │
│                               │           (cost=0, metrics)  │
│                               ▼                              │
│                            MISS                              │
│  4. Call LLM API                                             │
│  5. Store in cache                                           │
│  6. Return response (cost>0)                                 │
└─────────────────────────────────────────────────────────────┘
```

### Cache Key Generation

Keys are SHA256 hashes of normalized request parameters:

```python
key_parts = [
    f"provider:{provider}",      # anthropic, openai, local
    f"model:{model}",            # claude-3-5-haiku, gpt-4o, etc.
    f"system:{system_prompt}",   # system prompt if any
    f"temp:{temperature}",       # affects output randomness
    f"messages:{json.dumps(messages, sort_keys=True)}",
]
```

**Note:** `max_tokens` is excluded because it doesn't affect semantic content.

### Cache Features

| Feature | Default | Env Var |
|---------|---------|---------|
| TTL | 1 hour | `LLM_CACHE_TTL_SECONDS` |
| Max size | 1000 entries | `LLM_CACHE_MAX_SIZE` |
| Enabled | true | `LLM_CACHE_ENABLED` |

- **LRU eviction**: Oldest accessed entry evicted when at capacity
- **Thread-safe**: Mutex lock protects cache operations
- **Per-request control**: `enable_cache: false` bypasses cache

---

## Files Changed

| File | Change |
|------|--------|
| `backend/app/skills/llm_invoke.py` | Added `PromptCache` class, cache integration |
| `backend/app/schemas/skill.py` | Added `enable_cache` input, `cache_hit` output |
| `backend/tests/test_m13_prompt_cache.py` | 23 tests for cache functionality |

---

## API Changes

### Input Schema (LLMInvokeInput)

```python
enable_cache: bool = Field(
    default=True,
    description="Enable prompt caching for cost savings"
)
```

### Output Schema (LLMInvokeOutput)

```python
cache_hit: bool = Field(
    default=False,
    description="Whether response was served from cache"
)
```

### Example Response (Cache Hit)

```json
{
  "status": "ok",
  "result": {
    "response_text": "Hello there!",
    "cache_hit": true,
    "cost_cents": 0.0
  },
  "side_effects": {
    "tokens_used": 0,
    "cost_cents": 0.0,
    "cache_hit": true,
    "saved_cents": 0.0036
  }
}
```

---

## Prometheus Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_cache_hits_total` | Counter | provider, model | Total cache hits |
| `llm_cache_misses_total` | Counter | provider, model | Total cache misses |
| `llm_cache_savings_cents` | Counter | provider, model | Estimated cost savings |
| `llm_cache_size` | Gauge | - | Current cache entries |
| `llm_cache_evictions_total` | Counter | - | Entries evicted (TTL/LRU) |

---

## Test Results

```
23 passed in 3.61s

TestCacheKeyGeneration: 4 passed
TestCacheGetSet: 3 passed
TestCacheTTL: 1 passed
TestCacheLRUEviction: 1 passed
TestCacheStats: 2 passed
TestLLMInvokeCacheIntegration: 4 passed
TestGlobalCacheConfiguration: 2 passed
TestM13AcceptanceCriteria: 6 passed
```

---

## Live Verification

```
FIRST CALL - Cache MISS
  Response: "Hello there!"
  Cost: 0.0036 cents
  Cache hit: False

SECOND CALL - Cache HIT
  Response: "Hello there!" (from cache)
  Cost: 0.0 cents (FREE!)
  Saved: 0.0036 cents
  Cache hit: True
```

---

## Cost Savings Value Proposition

| Scenario | Without Cache | With Cache | Savings |
|----------|---------------|------------|---------|
| 10 identical calls | 10x cost | 1x cost | 90% |
| Retry loop (5 retries) | 5x cost | 1x cost | 80% |
| Template batch (100 items, 10 unique) | 100x cost | 10x cost | 90% |

---

## Configuration

### Environment Variables

```bash
# Cache TTL in seconds (default: 3600 = 1 hour)
LLM_CACHE_TTL_SECONDS=3600

# Maximum cache entries (default: 1000)
LLM_CACHE_MAX_SIZE=1000

# Enable/disable cache globally (default: true)
LLM_CACHE_ENABLED=true
```

### Per-Request Control

```python
# Disable cache for this specific call
await skill.execute({
    "provider": "anthropic",
    "model": "claude-3-5-haiku",
    "messages": [...],
    "enable_cache": False  # Force fresh API call
})
```

---

## Limitations

1. **In-memory only**: Cache is per-process, not shared across workers
2. **No semantic matching**: Only exact matches are cached
3. **Temperature sensitivity**: Different temperatures = different cache keys
4. **No persistence**: Cache lost on restart

### Future Enhancements (Not Implemented)

- Redis-backed shared cache
- Semantic similarity matching
- Cache warming from logs
- Persistent cache across restarts

---

## Related PINs

- PIN-033: M8-M14 Machine-Native Realignment Roadmap
- PIN-067: M13 Iterations Cost Calculator Fix

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | Claude | Initial implementation |
