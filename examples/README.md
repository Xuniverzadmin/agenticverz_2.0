# AOS Examples

Practical demos of the Agentic Operating System (AOS).

## Available Demos

| Demo | Description | Time |
|------|-------------|------|
| [btc_price_slack](./btc_price_slack/) | Fetch BTC price, send to Slack | 2 min |
| [json_transform](./json_transform/) | Deterministic data transformation | 1 min |
| [http_retry](./http_retry/) | Failure handling with retry/fallback | 2 min |

## Prerequisites

```bash
# Install Python SDK
pip install aos-sdk

# Set API key
export AOS_API_KEY=your-api-key

# Optional: custom server URL
export AOS_BASE_URL=http://localhost:8000
```

## Quick Start

```bash
# Run any demo
cd btc_price_slack && ./run.sh

# Or with Python directly
python btc_price_slack/demo.py
```

## Machine-Native Concepts Demonstrated

### 1. Simulate Before Execute

Every demo shows the **simulate → execute** pattern:
- Check feasibility before committing resources
- Know the cost before paying it
- See risks before encountering them

### 2. Structured Outcomes

Failures are **data, not exceptions**:
- Error codes from taxonomy
- Catalog matching for known issues
- Recovery suggestions included

### 3. Determinism

Pure skills like `json_transform` are **fully deterministic**:
- Same input → same output
- Safe for replay testing
- Exact cost prediction

## Demo Details

### BTC Price to Slack
Shows end-to-end workflow:
1. HTTP GET → external API
2. JSON transform → extract value
3. HTTP POST → Slack webhook
4. Retry on failure

### JSON Transform
Shows pure transformation:
1. Define transform query
2. Simulate (instant, no cost)
3. Execute (deterministic result)
4. Verify with replay

### HTTP Retry
Shows failure handling:
1. Primary endpoint (fails intentionally)
2. Retry with backoff
3. Fallback to secondary
4. Structured error outcome

## Running All Demos

```bash
# Run all demos in sequence
for demo in btc_price_slack json_transform http_retry; do
    echo "=== Running $demo ==="
    cd $demo && ./run.sh && cd ..
    echo ""
done
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `aos-sdk not found` | `pip install aos-sdk` |
| `Connection refused` | Check `AOS_BASE_URL` |
| `Unauthorized` | Check `AOS_API_KEY` |
| `Simulation failed` | Server may be starting up |
