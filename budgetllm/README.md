# BudgetLLM

**Hard budget limits + prompt caching for LLM API calls.**

Your agent stops before you overspend.

## Features

- **Drop-in OpenAI Replacement** - Same API: `client.chat.completions.create()`
- **Hard Budget Limits** - Daily, monthly, and cumulative caps
- **Automatic Kill-Switch** - Stops all calls when limit exceeded
- **Manual Pause/Resume** - Emergency stop button
- **Prompt Caching** - Same prompt = free response from cache
- **Redis Support** - Shared state across processes

## Installation

```bash
pip install budgetllm

# With Redis support
pip install budgetllm[redis]
```

## Quick Start - Drop-in OpenAI Replacement

Change one import line to add budget protection:

```python
# Before:
# from openai import OpenAI
# client = OpenAI()

# After:
from budgetllm import Client as OpenAI
client = OpenAI(openai_key="sk-...", budget_cents=1000)  # $10 limit

# Same API works!
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Same response access
print(response["choices"][0]["message"]["content"])
print(response["usage"]["total_tokens"])

# Plus cost tracking
print(f"Cost: {response['cost_cents']} cents")
print(f"Cache hit: {response['cache_hit']}")
```

## Simple Shortcut

```python
from budgetllm import Client

client = Client(budget_cents=1000)  # $10 hard limit

# Shortcut syntax
response = client.chat("What is machine learning?")
print(response["choices"][0]["message"]["content"])
```

## Budget Enforcement

```python
from budgetllm import Client, BudgetExceededError

client = Client(
    openai_key="sk-...",
    budget_cents=100,         # $1 hard limit (never resets)
    daily_limit_cents=50,     # $0.50/day
    monthly_limit_cents=200,  # $2/month
    auto_pause=True,          # Raise exception when exceeded
)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except BudgetExceededError as e:
    print(f"Budget exceeded: {e.limit_type}")
    print(f"Spent: {e.spent} cents")
    print(f"Limit: {e.limit} cents")
```

## Manual Pause (Kill Switch)

```python
# Emergency stop
client.pause()

# Resume later
client.resume()

# Check status
if client.is_paused():
    print("Client is paused")
```

## Check Status

```python
status = client.get_status()

print(f"Daily spent: {status['budget']['daily']['spent_cents']} cents")
print(f"Daily remaining: {status['budget']['daily']['remaining_cents']} cents")
print(f"Cache hits: {status['cache']['hits']}")
print(f"Cache savings: {status['cache']['savings_cents']} cents")
```

## Prompt Caching

Same prompt + same model = cached response (free).

```python
# First call - costs money
r1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)
print(r1["cost_cents"])  # e.g., 0.05

# Second call - free from cache
r2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)
print(r2["cost_cents"])  # 0.0
print(r2["cache_hit"])   # True
```

Disable cache for a single call:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
    enable_cache=False,
)
```

## All OpenAI Parameters Supported

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"},
    ],
    temperature=0.7,
    max_tokens=100,
    top_p=0.9,
    frequency_penalty=0.5,
    presence_penalty=0.5,
    stop=["\n"],
)
```

## Response Format

Responses match OpenAI's exact structure with BudgetLLM additions:

```python
{
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "total_tokens": 18
    },
    # BudgetLLM additions:
    "cost_cents": 0.05,
    "cache_hit": False
}
```

## Redis Support

Share budget state and cache across processes:

```python
client = Client(
    openai_key="sk-...",
    budget_cents=1000,
    redis_url="redis://localhost:6379/0",
)
```

## Advanced: Direct Components

```python
from budgetllm import BudgetTracker, PromptCache, MemoryBackend

# Budget tracker only
tracker = BudgetTracker(
    daily_limit_cents=500,
    monthly_limit_cents=2000,
    hard_limit_cents=5000,
    auto_pause=True,
)

tracker.record_cost(50)  # Record 50 cents
tracker.check_limits()   # Raises if exceeded

# Cache only
backend = MemoryBackend(max_size=1000, default_ttl=3600)
cache = PromptCache(backend=backend)

cache.set(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    response={"content": "Hi there!"},
    cost_cents=0.05,
)

cached = cache.get(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## API Reference

### Client

```python
Client(
    openai_key: str = None,          # OpenAI API key (or OPENAI_API_KEY env)
    budget_cents: int = None,        # Hard limit (never resets)
    daily_limit_cents: int = None,   # Daily limit
    monthly_limit_cents: int = None, # Monthly limit
    cache_enabled: bool = True,      # Enable prompt caching
    cache_ttl: int = 3600,           # Cache TTL in seconds
    redis_url: str = None,           # Redis URL for shared state
    auto_pause: bool = True,         # Raise exception when exceeded
)

# OpenAI-compatible method
client.chat.completions.create(
    messages: list,
    model: str = "gpt-4o-mini",
    temperature: float = None,
    max_tokens: int = None,
    top_p: float = None,
    frequency_penalty: float = None,
    presence_penalty: float = None,
    stop: str | list = None,
    **kwargs
) -> dict

# Shortcut
client.chat(prompt: str, model: str = "gpt-4o-mini", **kwargs) -> dict

# Control methods
client.get_status() -> dict
client.pause()
client.resume()
client.is_paused() -> bool
client.reset()  # Clear all counters (for testing)
```

### BudgetTracker

```python
BudgetTracker(
    daily_limit_cents: int = None,
    monthly_limit_cents: int = None,
    hard_limit_cents: int = None,
    auto_pause: bool = True,
)

tracker.record_cost(cents: int)
tracker.check_limits() -> bool  # Raises BudgetExceededError if exceeded
tracker.pause()
tracker.resume()
tracker.is_paused() -> bool
tracker.get_status() -> dict
tracker.get_daily_spend() -> int
tracker.reset_all()
```

### PromptCache

```python
PromptCache(
    backend: CacheBackend,
    enabled: bool = True,
    default_ttl: int = 3600,
)

cache.get(model, messages, temperature, system_prompt) -> dict | None
cache.set(model, messages, response, cost_cents, temperature, system_prompt, ttl)
cache.invalidate(model, messages, temperature, system_prompt) -> bool
cache.get_stats() -> dict
cache.reset_stats()
```

## Pricing Reference

Costs per 1M tokens (approximate, Dec 2024):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |
| claude-3.5-sonnet | $3.00 | $15.00 |
| claude-3.5-haiku | $0.80 | $4.00 |

## License

MIT
