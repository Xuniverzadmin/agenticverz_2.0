# AOS Demos

Complete list of example demos with descriptions and requirements.

## Available Demos

| Demo | Location | Description | Difficulty |
|------|----------|-------------|------------|
| BTC → Slack | `examples/btc_price_slack/` | External API + webhook | Beginner |
| JSON Transform | `examples/json_transform/` | Pure deterministic | Beginner |
| HTTP Retry | `examples/http_retry/` | Failure handling | Intermediate |

## Demo 1: BTC Price to Slack

**Location:** `examples/btc_price_slack/`

**What it demonstrates:**
- Multi-step workflow (3 skills chained)
- External HTTP calls
- Webhook notifications
- Pre-execution simulation
- Budget constraints

**Prerequisites:**
- AOS API key
- Slack webhook URL (optional for real execution)

**Run:**
```bash
cd examples/btc_price_slack
./run.sh
```

**Expected duration:** 2 minutes

---

## Demo 2: JSON Transform

**Location:** `examples/json_transform/`

**What it demonstrates:**
- Pure deterministic transformation
- Replay guarantees (same input → same output)
- Zero-cost simulation (no external calls)
- Structured data pipelines

**Prerequisites:**
- AOS API key only

**Run:**
```bash
cd examples/json_transform
./run.sh

# Verify determinism
./run.sh --check-determinism
```

**Expected duration:** 1 minute

---

## Demo 3: HTTP Retry

**Location:** `examples/http_retry/`

**What it demonstrates:**
- Transient failure handling
- Retry with exponential backoff
- Fallback to secondary endpoint
- Structured error outcomes
- Failure catalog matching

**Prerequisites:**
- AOS API key
- Internet access (uses httpbin.org)

**Run:**
```bash
cd examples/http_retry
./run.sh

# Show failure catalog
./run.sh --catalog
```

**Expected duration:** 2 minutes

---

## Running All Demos

```bash
cd /root/agenticverz2.0

# Sequential run
for demo in btc_price_slack json_transform http_retry; do
    echo "========================================"
    echo "Running: $demo"
    echo "========================================"
    cd examples/$demo
    ./run.sh
    cd ../..
    echo ""
done
```

## Demo Requirements Matrix

| Demo | AOS Server | API Key | External Network | Slack |
|------|------------|---------|------------------|-------|
| btc_price_slack | Required | Required | Required | Optional |
| json_transform | Required | Required | No | No |
| http_retry | Required | Required | Required | No |

## Writing Your Own Demo

Template structure:

```
examples/my_demo/
├── demo.py        # Main Python script
├── run.sh         # Shell wrapper
└── README.md      # Documentation
```

Demo script pattern:

```python
from aos_sdk import AOSClient

def main():
    client = AOSClient()

    # 1. Create plan
    plan = [...]

    # 2. Simulate
    sim = client.simulate(plan)
    if not sim['feasible']:
        return 1

    # 3. Execute
    run = client.create_run(...)
    result = client.get_run(run['run_id'])

    # 4. Report
    print(result['outcome'])
    return 0

if __name__ == "__main__":
    exit(main())
```

## Troubleshooting

### Demo won't start

```bash
# Check SDK installed
aos version

# Check server connection
aos health

# Check API key
echo $AOS_API_KEY
```

### Simulation fails

- Server may be starting up
- Wait 5 seconds and retry
- Check `AOS_BASE_URL`

### Execution hangs

- Check network connectivity
- External APIs may be slow
- Increase timeout if needed

### Slack notification not received

- Verify `SLACK_WEBHOOK_URL`
- Check Slack app permissions
- Try curl test first:
  ```bash
  curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"test"}'
  ```
