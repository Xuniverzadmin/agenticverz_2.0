# AOS - Agentic Operating System

The most predictable, reliable, deterministic SDK for building machine-native agents.

```
Simulate → Execute → Recover
    in under 5 minutes
```

## What is AOS?

AOS is a runtime for building AI agents that are:

- **Deterministic** - Same input, same output, always
- **Replayable** - Test without re-executing
- **Contract-bound** - Skills declare their costs and limits
- **Observable** - Full telemetry, no hidden state
- **Failure-aware** - Errors are data, not exceptions

## Quick Start

### Install

```bash
# Python
pip install aos-sdk

# JavaScript/TypeScript
npm install @agenticverz/aos-sdk
```

### Configure

```bash
export AOS_API_KEY=your-api-key
export AOS_BASE_URL=http://localhost:8000
```

### Simulate → Execute

```python
from aos_sdk import AOSClient

client = AOSClient()

# Define your plan
plan = [
    {"skill": "http_call", "params": {"url": "https://api.example.com/data"}},
    {"skill": "json_transform", "params": {"query": ".results[0]"}}
]

# 1. Simulate first (check feasibility, estimate cost)
sim = client.simulate(plan, budget_cents=100)
print(f"Feasible: {sim['feasible']}, Cost: {sim['estimated_cost_cents']}c")

# 2. Execute only if feasible
if sim['feasible']:
    run = client.create_run(agent_id="my-agent", goal="fetch data", plan=plan)
    result = client.get_run(run['run_id'])
    print(result['outcome'])
```

## Examples

| Demo | Description | Run |
|------|-------------|-----|
| [BTC → Slack](./examples/btc_price_slack/) | Fetch price, notify Slack | `./examples/btc_price_slack/run.sh` |
| [JSON Transform](./examples/json_transform/) | Deterministic data transform | `./examples/json_transform/run.sh` |
| [HTTP Retry](./examples/http_retry/) | Failure handling with retry | `./examples/http_retry/run.sh` |

## Core Concepts

### Machine-Native Design

AOS is built for **agents to operate efficiently**, not humans to babysit:

```
Traditional Agent          AOS Agent
─────────────────          ─────────────────
Log parsing                Queryable state
Tool lists                 Capability contracts
Exceptions thrown          Structured outcomes
Opaque failures            Navigable failure catalog
Trial and error            Pre-execution simulation
```

### Skills

Skills are the building blocks of AOS plans:

| Skill | Purpose | Deterministic |
|-------|---------|---------------|
| `http_call` | External HTTP requests | No (external) |
| `json_transform` | Data transformation | Yes |
| `llm_invoke` | LLM completion | No (LLM) |
| `postgres_query` | Database queries | No (external) |
| `calendar_write` | Calendar events | No (external) |

### Structured Outcomes

Every execution returns a `StructuredOutcome`:

```json
{
  "success": true,
  "result": {"data": "..."},
  "cost_cents": 5,
  "duration_ms": 234,
  "deterministic_hash": "abc123..."
}
```

On failure:
```json
{
  "success": false,
  "error": {
    "code": "HTTP_503",
    "category": "transient",
    "catalog_match": "SERVICE_UNAVAILABLE",
    "recovery_suggestion": "RETRY_WITH_BACKOFF"
  }
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        AOS Runtime                       │
├──────────────┬──────────────┬──────────────┬────────────┤
│   Planner    │    Skills    │   Budget     │   RBAC     │
│  (Anthropic) │  (Registry)  │  (Enforcer)  │  (Engine)  │
├──────────────┴──────────────┴──────────────┴────────────┤
│                    Workflow Engine                       │
│            (Checkpoints, Policies, Recovery)             │
├─────────────────────────────────────────────────────────┤
│                    Observability                         │
│           (Prometheus, Grafana, Audit Logs)              │
├─────────────────────────────────────────────────────────┤
│                      PostgreSQL                          │
│              (Runs, Plans, Outcomes, Pins)               │
└─────────────────────────────────────────────────────────┘
```

## Documentation

| Document | Description |
|----------|-------------|
| [Quickstart](./docs/QUICKSTART.md) | Zero to first run in 5 minutes |
| [Auth Setup](./docs/AUTH_SETUP.md) | Keycloak token acquisition |
| [API Guide](./docs/API_WORKFLOW_GUIDE.md) | Full API reference |
| [Examples](./examples/) | Working demo scripts |

## SDKs

### Python SDK

```bash
pip install aos-sdk
```

```python
from aos_sdk import AOSClient

client = AOSClient(api_key="...", base_url="http://localhost:8000")

# Machine-native APIs
client.simulate(plan)           # Check feasibility
client.query("remaining_budget") # Query runtime state
client.get_capabilities()        # List skills + limits
client.describe_skill("http_call") # Skill details

# Agent workflow
client.create_agent("my-agent")
client.post_goal(agent_id, "do something")
client.poll_run(agent_id, run_id)
```

### JavaScript/TypeScript SDK

```bash
npm install @agenticverz/aos-sdk
```

```typescript
import { AOSClient } from '@agenticverz/aos-sdk';

const client = new AOSClient({ apiKey: '...', baseUrl: 'http://localhost:8000' });

// Machine-native APIs
await client.simulate(plan);
await client.query('remaining_budget');
await client.getCapabilities();
await client.describeSkill('http_call');

// Agent workflow
await client.createAgent('my-agent');
await client.postGoal(agentId, 'do something');
await client.pollRun(agentId, runId);
```

## CLI

```bash
# Show version
aos version

# Check server health
aos health

# List available skills
aos skills

# Describe a skill
aos skill http_call

# Simulate a plan
aos simulate '[{"skill": "http_call", "params": {"url": "..."}}]'
```

## Status

| Milestone | Status |
|-----------|--------|
| M0-M7 | ✅ Complete |
| M8 Demo + SDK | ✅ Complete |
| M9 Failure Persistence | Pending |
| M10 Recovery Engine | Pending |

See [Memory Pins](./docs/memory-pins/INDEX.md) for full project status.

## License

MIT

## Links

- [PyPI: aos-sdk](https://pypi.org/project/aos-sdk/)
- [npm: @agenticverz/aos-sdk](https://www.npmjs.com/package/@agenticverz/aos-sdk)
- [Documentation](./docs/)
- [Examples](./examples/)
