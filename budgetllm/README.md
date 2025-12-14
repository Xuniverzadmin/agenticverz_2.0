# BudgetLLM

**Hard budget limits + prompt caching for LLM API calls.**

Your agent stops before you overspend.

[![PyPI version](https://badge.fury.io/py/budgetllm.svg)](https://pypi.org/project/budgetllm/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why BudgetLLM?

| Problem | BudgetLLM Solution |
|---------|-------------------|
| Surprise $500 OpenAI bill | Hard budget cap - stops at $10 |
| Agent loops burning money | Auto kill-switch on limit |
| Paying for repeated prompts | Prompt caching - same question = free |
| No visibility until month-end | Real-time spend tracking |
| Complex observability tools | One import line change |

**Helicone shows you spent $500. BudgetLLM stops you at $100.**

## Features

- **Drop-in OpenAI Replacement** - Same API: `client.chat.completions.create()`
- **Hard Budget Limits** - Daily, monthly, and cumulative caps
- **Automatic Kill-Switch** - Stops all calls when limit exceeded
- **Manual Pause/Resume** - Emergency stop button
- **Prompt Caching** - Same prompt = free response from cache
- **Redis Support** - Shared state across processes (optional)

## Installation

```bash
pip install budgetllm

# With Redis support (for multi-process/distributed)
pip install budgetllm[redis]
```

## Quick Start - Drop-in OpenAI Replacement

Change **one import line** to add budget protection:

```python
# BEFORE (standard OpenAI):
# from openai import OpenAI
# client = OpenAI()

# AFTER (with budget protection):
from budgetllm import Client as OpenAI

client = OpenAI(
    openai_key="sk-...",      # or set OPENAI_API_KEY env var
    budget_cents=1000,        # $10 hard limit
)

# Same API - works exactly like OpenAI
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Same response structure
print(response["choices"][0]["message"]["content"])
print(response["usage"]["total_tokens"])

# BONUS: Cost tracking built-in
print(f"Cost: {response['cost_cents']} cents")
print(f"Cache hit: {response['cache_hit']}")
```

## Shortcut Syntax

For quick scripts:

```python
from budgetllm import Client

client = Client(budget_cents=1000)
response = client.chat("What is machine learning?")
print(response["choices"][0]["message"]["content"])
```

---

## Budget Behavior

### How Limits Work

```python
from budgetllm import Client, BudgetExceededError

client = Client(
    budget_cents=100,          # Hard cap: $1 total (never resets)
    daily_limit_cents=50,      # Daily cap: $0.50/day (resets midnight)
    monthly_limit_cents=500,   # Monthly cap: $5/month (resets 1st)
    auto_pause=True,           # Raise exception when exceeded
)
```

| Limit Type | Behavior | Resets |
|------------|----------|--------|
| `budget_cents` | Cumulative hard cap | Never |
| `daily_limit_cents` | Per-day spend limit | Midnight UTC |
| `monthly_limit_cents` | Per-month spend limit | 1st of month |

### What Happens When Exceeded

```python
from budgetllm import Client, BudgetExceededError

client = Client(budget_cents=1, auto_pause=True)  # $0.01 limit

try:
    # This will likely exceed the tiny budget
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Write a poem"}]
    )
except BudgetExceededError as e:
    print(f"Limit type: {e.limit_type}")  # "daily", "monthly", or "hard"
    print(f"Amount spent: {e.spent} cents")
    print(f"Limit was: {e.limit} cents")

    # Handle gracefully
    if e.limit_type == "daily":
        print("Try again tomorrow!")
    elif e.limit_type == "hard":
        print("Budget exhausted. Upgrade required.")
```

### Soft Mode (No Exceptions)

```python
client = Client(budget_cents=100, auto_pause=False)

# Returns False instead of raising exception
if not client.budget.check_limits():
    print("Budget exceeded - handle gracefully")
```

---

## Cache Behavior

### How Caching Works

BudgetLLM caches responses based on:
- **Model** (gpt-4o-mini vs gpt-4o)
- **Messages** (exact content match)
- **Temperature** (if specified)

```python
# First call - hits OpenAI API, costs money
r1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)
print(r1["cost_cents"])   # e.g., 0.05
print(r1["cache_hit"])    # False

# Second identical call - returns cached response, FREE
r2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)
print(r2["cost_cents"])   # 0.0
print(r2["cache_hit"])    # True
```

### Cache Miss Triggers

These cause a cache **miss** (new API call):

```python
# Different message content
client.chat("What is Python?")  # MISS
client.chat("What is Java?")    # MISS (different question)

# Different model
client.chat("What is Python?", model="gpt-4o-mini")  # MISS
client.chat("What is Python?", model="gpt-4o")       # MISS (different model)

# Different temperature
client.chat.completions.create(messages=[...], temperature=0.5)  # MISS
client.chat.completions.create(messages=[...], temperature=0.7)  # MISS
```

### Disable Cache Per-Call

```python
# Force fresh response (bypass cache)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What time is it?"}],
    enable_cache=False,  # Always hits API
)
```

### Cache Statistics

```python
status = client.get_status()

print(f"Cache hits: {status['cache']['hits']}")
print(f"Cache misses: {status['cache']['misses']}")
print(f"Hit rate: {status['cache']['hit_rate_pct']}%")
print(f"Money saved: ${status['cache']['savings_cents'] / 100:.2f}")
```

---

## Error Handling

### All Error Types

```python
from budgetllm import Client, BudgetExceededError

client = Client(budget_cents=100)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}]
    )
except BudgetExceededError as e:
    # Budget/limit exceeded
    if e.limit_type == "paused":
        print("Client manually paused - call client.resume()")
    elif e.limit_type == "daily":
        print(f"Daily limit hit: {e.spent}/{e.limit} cents")
    elif e.limit_type == "monthly":
        print(f"Monthly limit hit: {e.spent}/{e.limit} cents")
    elif e.limit_type == "hard":
        print(f"Hard budget exhausted: {e.spent}/{e.limit} cents")

except ValueError as e:
    # Missing required parameters
    print(f"Invalid request: {e}")

except Exception as e:
    # OpenAI API errors pass through
    print(f"API error: {e}")
```

### Graceful Degradation Pattern

```python
def safe_llm_call(prompt: str, fallback: str = "Service unavailable"):
    """Call LLM with graceful fallback."""
    try:
        response = client.chat(prompt)
        return response["choices"][0]["message"]["content"]
    except BudgetExceededError:
        return fallback
    except Exception as e:
        print(f"LLM error: {e}")
        return fallback

# Usage
answer = safe_llm_call("What is 2+2?", fallback="4")
```

---

## Redis Backend (Multi-Process)

By default, BudgetLLM uses in-memory storage (single process only).

For **production deployments** with multiple workers:

```python
client = Client(
    openai_key="sk-...",
    budget_cents=1000,
    redis_url="redis://localhost:6379/0",  # Shared state
)
```

### What Redis Enables

| Feature | In-Memory | Redis |
|---------|-----------|-------|
| Budget tracking | Per-process | Shared across all processes |
| Prompt cache | Per-process | Shared across all processes |
| Kill switch | Per-process | Global stop |

### Redis Configuration

```python
# Local Redis
client = Client(redis_url="redis://localhost:6379/0")

# Redis with auth
client = Client(redis_url="redis://:password@host:6379/0")

# Redis cluster (Upstash, etc.)
client = Client(redis_url="rediss://default:token@host:6379")
```

---

## Manual Controls

### Kill Switch (Emergency Stop)

```python
# STOP all API calls immediately
client.pause()

# All calls now raise BudgetExceededError with limit_type="paused"
try:
    client.chat("Hello")
except BudgetExceededError as e:
    print(e.limit_type)  # "paused"

# Resume operations
client.resume()
```

### Check Current Status

```python
status = client.get_status()

# Budget info
print(f"Daily spent: {status['budget']['daily']['spent_cents']} cents")
print(f"Daily remaining: {status['budget']['daily']['remaining_cents']} cents")
print(f"Monthly spent: {status['budget']['monthly']['spent_cents']} cents")
print(f"Total spent: {status['budget']['total']['spent_cents']} cents")
print(f"Paused: {status['budget']['paused']}")

# Cache info
print(f"Cache hits: {status['cache']['hits']}")
print(f"Savings: {status['cache']['savings_cents']} cents")
```

---

## Common Patterns

### Agent with Budget Guard

```python
from budgetllm import Client, BudgetExceededError

client = Client(
    budget_cents=500,       # $5 max for this agent run
    daily_limit_cents=100,  # $1/day safety net
)

def run_agent(task: str, max_iterations: int = 10):
    """Run agent with automatic budget protection."""
    for i in range(max_iterations):
        try:
            response = client.chat(f"Step {i+1}: {task}")
            result = response["choices"][0]["message"]["content"]

            if "DONE" in result:
                return result

        except BudgetExceededError as e:
            return f"Agent stopped: budget exceeded ({e.limit_type})"

    return "Max iterations reached"
```

### Batch Processing with Cost Tracking

```python
def process_batch(items: list[str]) -> dict:
    """Process items with cost tracking."""
    results = []
    total_cost = 0
    cache_hits = 0

    for item in items:
        response = client.chat(f"Process: {item}")
        results.append(response["choices"][0]["message"]["content"])
        total_cost += response["cost_cents"]
        if response["cache_hit"]:
            cache_hits += 1

    return {
        "results": results,
        "total_cost_cents": total_cost,
        "cache_hits": cache_hits,
        "cache_rate": cache_hits / len(items) * 100,
    }
```

---

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

---

## API Reference

### Client

```python
Client(
    openai_key: str = None,          # OpenAI API key (or OPENAI_API_KEY env)
    budget_cents: int = None,        # Hard limit (never resets)
    daily_limit_cents: int = None,   # Daily limit (resets midnight)
    monthly_limit_cents: int = None, # Monthly limit (resets 1st)
    cache_enabled: bool = True,      # Enable prompt caching
    cache_ttl: int = 3600,           # Cache TTL in seconds
    redis_url: str = None,           # Redis URL for shared state
    auto_pause: bool = True,         # Raise exception when exceeded
)

# OpenAI-compatible method
client.chat.completions.create(
    messages: list,                  # Required
    model: str = "gpt-4o-mini",
    temperature: float = None,
    max_tokens: int = None,
    top_p: float = None,
    frequency_penalty: float = None,
    presence_penalty: float = None,
    stop: str | list = None,
    enable_cache: bool = None,       # Override cache for this call
    **kwargs
) -> dict

# Shortcut
client.chat(prompt: str, model: str = "gpt-4o-mini", **kwargs) -> dict

# Control methods
client.get_status() -> dict
client.pause() -> None
client.resume() -> None
client.is_paused() -> bool
client.reset() -> None  # Clear all counters (testing only)
```

### BudgetExceededError

```python
except BudgetExceededError as e:
    e.limit_type  # "daily" | "monthly" | "hard" | "paused"
    e.spent       # Amount spent (cents)
    e.limit       # Limit that was exceeded (cents)
    str(e)        # Human-readable message
```

---

## Pricing Reference

Costs per 1M tokens (approximate, Dec 2024):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |

---

## License

MIT - Use it, fork it, ship it.

---

## Links

- [GitHub](https://github.com/agenticverz/budgetllm)
- [PyPI](https://pypi.org/project/budgetllm/)
- [Issues](https://github.com/agenticverz/budgetllm/issues)
