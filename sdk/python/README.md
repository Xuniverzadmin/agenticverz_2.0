# AOS SDK for Python

The official Python SDK for AOS (Agentic Operating System) - the most predictable, reliable, deterministic SDK for building machine-native agents.

## Why AOS?

Building production agents is hard. AOS solves four problems that matter:

| Pillar | Problem | AOS Solution |
|--------|---------|--------------|
| **Cost** | LLM calls drain budgets unexpectedly | Pre-execution simulation, budget caps, cost alerts |
| **Incident** | Agents fail silently or cryptically | Structured failure catalog, replay verification, evidence trails |
| **Self-Heal** | Manual intervention for every failure | Recovery engine, circuit breakers, scoped execution |
| **Governance** | No control over what agents do | Strategy bounds, policy enforcement, RBAC |

## Installation

```bash
pip install aos-sdk
```

## Quick Start

```bash
# Initialize AOS in your project
aos init --api-key=YOUR_API_KEY

# Verify installation
aos health

# You're ready to build agents
```

### Python Client

```python
from aos_sdk import AOSClient

# Initialize client (uses .aos/config.json or env vars)
client = AOSClient()

# Check available capabilities
caps = client.get_capabilities()
print(f"Budget remaining: {caps['budget_remaining_cents']}c")
print(f"Available skills: {caps['skills_available']}")

# Simulate before executing (Cost pillar: know your costs upfront)
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

## Determinism Support

AOS guarantees reproducible agent behavior:

```python
from aos_sdk import RuntimeContext, Trace

# Create deterministic context
ctx = RuntimeContext(seed=42)

# Execute with trace capture
result = client.simulate(plan, seed=42)

# Save trace for replay verification (Incident pillar: evidence trail)
trace = Trace.from_result(result, ctx)
trace.save("execution.trace.json")

# Later: verify execution was deterministic
original = Trace.load("execution.trace.json")
replay = Trace.load("replay.trace.json")
diff = diff_traces(original, replay)
assert diff["match"], f"Non-deterministic: {diff['summary']}"
```

## API Reference

### AOSClient

```python
client = AOSClient(
    api_key="...",           # Optional, uses AOS_API_KEY env var or .aos/config.json
    base_url="http://...",   # Default: http://127.0.0.1:8000
    timeout=30               # Request timeout in seconds
)
```

### Machine-Native APIs

```python
# Simulate a plan before execution (Cost pillar)
result = client.simulate(plan=[...], budget_cents=1000)

# Query runtime state
budget = client.query("remaining_budget_cents")
attempts = client.query("what_did_i_try_already", run_id="...")

# List and describe skills
skills = client.list_skills()
skill = client.describe_skill("http_call")

# Get capabilities (Governance pillar: know your bounds)
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

The SDK includes a command-line interface for project setup and debugging:

```bash
# Initialize AOS in your project
aos init                     # Create .aos/ directory with config
aos init --api-key=xxx       # Set API key during init
aos init --base-url=xxx      # Set custom server URL

# Check installation and server health
aos health                   # Shows SDK version, config status, server health

# Explore capabilities
aos version                  # Show SDK version
aos capabilities             # Show runtime capabilities
aos skills                   # List available skills
aos skill http_call          # Describe a skill

# Simulate plans (with determinism support)
aos simulate '[...]'         # Simulate a plan
aos simulate '[...]' --seed=42 --save-trace=trace.json

# Replay and compare traces (Incident pillar)
aos replay trace.json        # Replay a saved trace
aos diff trace1.json trace2.json  # Compare two traces
```

## Configuration

After running `aos init`, your project will have:

```
.aos/
├── config.json    # API key and settings
├── example.json   # Example simulate payload
└── traces/        # Saved execution traces
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AOS_API_KEY` | API key for authentication | (from .aos/config.json) |
| `AOS_BASE_URL` | Base URL for AOS server | `http://127.0.0.1:8000` |

## Requirements

- Python 3.8+
- `requests` or `httpx` (both supported)

## License

MIT License - see LICENSE file for details.
