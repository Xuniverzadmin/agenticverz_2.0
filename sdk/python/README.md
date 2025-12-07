# AOS SDK for Python

The official Python SDK for AOS (Agentic Operating System) - the most predictable, reliable, deterministic SDK for building machine-native agents.

## Installation

```bash
pip install aos-sdk
```

## Quick Start

```python
from aos_sdk import AOSClient

# Initialize client
client = AOSClient(
    api_key="your-api-key",
    base_url="http://localhost:8000"
)

# Check available capabilities
caps = client.get_capabilities()
print(f"Budget remaining: {caps['budget_remaining_cents']}c")
print(f"Available skills: {caps['skills_available']}")

# Simulate before executing
result = client.simulate([
    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
    {"skill": "llm_invoke", "params": {"prompt": "Summarize the response"}}
])

if result["feasible"]:
    print(f"Plan is feasible! Estimated cost: {result['estimated_cost_cents']}c")
else:
    print(f"Plan not feasible: {result['reason']}")
```

## Machine-Native Features

AOS is designed for agents to operate efficiently, not humans to babysit:

- **Queryable execution context** - Not log parsing
- **Capability contracts** - Not just tool lists
- **Structured outcomes** - Never throws exceptions
- **Failure as data** - Navigable, not opaque
- **Pre-execution simulation** - Know before you run

## API Reference

### AOSClient

```python
client = AOSClient(
    api_key="...",           # Optional, uses AOS_API_KEY env var
    base_url="http://...",   # Default: http://127.0.0.1:8000
    timeout=30               # Request timeout in seconds
)
```

### Machine-Native APIs

```python
# Simulate a plan before execution
result = client.simulate(plan=[...], budget_cents=1000)

# Query runtime state
budget = client.query("remaining_budget_cents")
attempts = client.query("what_did_i_try_already", run_id="...")

# List and describe skills
skills = client.list_skills()
skill = client.describe_skill("http_call")

# Get capabilities
caps = client.get_capabilities()
```

### Agent Workflow APIs

```python
# Create agent and execute goal
agent_id = client.create_agent("my-agent")
run_id = client.post_goal(agent_id, "Check the weather in London")
result = client.poll_run(agent_id, run_id, timeout=30)

# Memory recall
memories = client.recall(agent_id, "weather queries", k=5)
```

## CLI

The SDK includes a command-line interface:

```bash
# Check version
aos version

# Check server health
aos health

# Show capabilities
aos capabilities

# List skills
aos skills

# Describe a skill
aos skill http_call

# Simulate a plan
aos simulate '[{"skill": "http_call", "params": {"url": "https://example.com"}}]'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AOS_API_KEY` | API key for authentication | (none) |
| `AOS_BASE_URL` | Base URL for AOS server | `http://127.0.0.1:8000` |

## Requirements

- Python 3.8+
- `requests` or `httpx` (both supported)

## License

MIT License - see LICENSE file for details.
