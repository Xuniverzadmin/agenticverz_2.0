# AOS Quickstart

From zero to first working demo in under 10 minutes.

## Prerequisites

- Python 3.8+ or Node.js 18+
- An AOS API key
- Network access to AOS server

## Step 1: Install SDK (1 minute)

### Python

```bash
pip install aos-sdk
```

### JavaScript/TypeScript

```bash
npm install @agenticverz/aos-sdk
```

Verify installation:

```bash
# Python
aos version

# Node
node -e "const {VERSION} = require('@agenticverz/aos-sdk'); console.log(VERSION)"
```

## Step 2: Configure (30 seconds)

```bash
# Required: Your API key
export AOS_API_KEY=your-api-key

# Optional: Server URL (default: http://127.0.0.1:8000)
export AOS_BASE_URL=http://localhost:8000
```

## Step 3: Check Connection (30 seconds)

```bash
# CLI
aos health

# Expected output:
# {
#   "status": "healthy",
#   "version": "1.0.0"
# }
```

## Step 4: List Available Skills (1 minute)

```bash
aos skills

# Expected output:
# {
#   "skills": [
#     {"id": "http_call", "version": "1.0.0"},
#     {"id": "json_transform", "version": "1.0.0"},
#     {"id": "llm_invoke", "version": "1.0.0"},
#     ...
#   ],
#   "count": 5
# }
```

## Step 5: Simulate a Plan (2 minutes)

Before executing anything, **simulate first**:

```bash
aos simulate '[
  {"skill": "http_call", "params": {"url": "https://httpbin.org/get"}}
]'

# Expected output:
# {
#   "feasible": true,
#   "estimated_cost_cents": 1,
#   "risks": []
# }
```

## Step 6: Run a Demo (3 minutes)

```bash
cd examples/json_transform
./run.sh
```

Expected output:

```
============================================================
AOS Demo: JSON Transform (Deterministic)
============================================================

Input Data:
{
  "users": [
    {"id": 1, "name": "Alice", ...}
  ]
}

=== SIMULATION ===
Simulation Result:
  Feasible: True
  Estimated Cost: 1 cents

=== EXECUTION ===
Run created: run_abc123
Execution Status: succeeded

Transformed Output:
[
  {"contact": "alice@example.com", "label": "Alice"}
]

[SUCCESS] JSON transform completed!
```

## Step 7: Write Your First Agent (5 minutes)

Create `my_first_agent.py`:

```python
from aos_sdk import AOSClient

# Initialize client
client = AOSClient()

# Define a simple plan
plan = [
    {
        "skill": "http_call",
        "params": {
            "method": "GET",
            "url": "https://httpbin.org/json"
        }
    },
    {
        "skill": "json_transform",
        "params": {
            "query": ".slideshow.title"
        }
    }
]

# Step 1: Simulate
print("Simulating plan...")
sim = client.simulate(plan, budget_cents=100)
print(f"Feasible: {sim['feasible']}")
print(f"Estimated cost: {sim['estimated_cost_cents']} cents")

if not sim['feasible']:
    print("Plan not feasible, aborting")
    exit(1)

# Step 2: Execute
print("\nExecuting plan...")
run = client.create_run(
    agent_id="my-first-agent",
    goal="Fetch and transform JSON",
    plan=plan
)

run_id = run.get('run_id') or run.get('id')
print(f"Run ID: {run_id}")

# Step 3: Get result
result = client.get_run(run_id)
print(f"\nResult: {result.get('outcome', {}).get('result')}")
```

Run it:

```bash
python my_first_agent.py
```

## What's Next?

### More Examples

- [BTC Price to Slack](../examples/btc_price_slack/) - External APIs + webhooks
- [HTTP Retry](../examples/http_retry/) - Failure handling + recovery

### Core Concepts

- **Simulate first** - Always check feasibility before execution
- **Structured outcomes** - Results are typed, never exceptions
- **Failure catalog** - Errors are matched to known patterns
- **Budget enforcement** - Never exceed your limits

### Documentation

- [Auth Setup](./AUTH_SETUP.md) - Keycloak token acquisition
- [API Guide](./API_WORKFLOW_GUIDE.md) - Full API reference
- [Architecture](./memory-pins/PIN-005-machine-native-architecture.md) - Design philosophy

## Troubleshooting

### `aos: command not found`

```bash
# Ensure pip scripts are in PATH
pip show aos-sdk  # Find location
export PATH=$PATH:~/.local/bin
```

### `Connection refused`

Check server is running:
```bash
curl http://localhost:8000/health
```

### `Unauthorized (401)`

Check API key:
```bash
echo $AOS_API_KEY  # Should not be empty
```

### `Simulation failed`

Server may be starting up. Wait 5 seconds and retry.

### SDK not found

```bash
# Reinstall
pip uninstall aos-sdk
pip install aos-sdk
```

## Summary

| Step | Action | Time |
|------|--------|------|
| 1 | Install SDK | 1 min |
| 2 | Set API key | 30 sec |
| 3 | Test connection | 30 sec |
| 4 | List skills | 1 min |
| 5 | Simulate plan | 2 min |
| 6 | Run demo | 3 min |
| 7 | Write agent | 5 min |
| **Total** | | **~10 min** |

You're now ready to build machine-native agents with AOS!
