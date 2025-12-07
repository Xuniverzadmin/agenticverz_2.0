# BTC Price to Slack Demo

Fetches the current Bitcoin price and sends a notification to Slack.

Demonstrates the **machine-native workflow**:
1. **Simulate** - Check feasibility before execution
2. **Execute** - Run with budget constraints
3. **Recover** - Handle failures gracefully

## Quick Start

```bash
# Install SDK
pip install aos-sdk

# Set environment
export AOS_API_KEY=your-api-key
export AOS_BASE_URL=http://localhost:8000
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Run demo
python demo.py
```

## What It Does

1. **Creates a 3-step plan:**
   - Fetch BTC price from CoinGecko API
   - Extract USD value with json_transform
   - POST result to Slack webhook

2. **Simulates the plan:**
   - Checks if all skills are available
   - Validates budget is sufficient
   - Identifies risks (rate limits, timeouts)

3. **Executes only if feasible:**
   - Creates a tracked run
   - Returns structured outcome
   - Handles errors with catalog matching

## Expected Output

```
============================================================
AOS Demo: BTC Price -> Slack Notification
============================================================

Configuration:
  API URL: http://127.0.0.1:8000
  BTC API: https://api.coingecko.com/api/v3/simple/price...
  Slack: https://hooks.slack.com/services/...

Plan created with 3 steps:
  1. [http_call] Fetch current BTC price from CoinGecko
  2. [json_transform] Extract USD price from response
  3. [http_call] Send price to Slack webhook

=== SIMULATION PHASE ===
Budget: 100 cents
Steps: 3

Simulation Result:
  Feasible: True
  Estimated Cost: 3 cents

=== EXECUTION PHASE ===
Run created: run_abc123
Waiting for execution...

Execution Result:
  Status: succeeded
  Success: True
  Result: {"slack_response": "ok"}

[SUCCESS] BTC price sent to Slack!
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| `AOS_API_KEY not set` | Export your API key |
| `Connection refused` | Check AOS_BASE_URL |
| `Simulation failed: budget` | Increase budget_cents |
| `Slack 400 error` | Check SLACK_WEBHOOK_URL |

## Files

- `demo.py` - Main demo script
- `run.sh` - Shell wrapper for Linux/macOS
- `README.md` - This file
