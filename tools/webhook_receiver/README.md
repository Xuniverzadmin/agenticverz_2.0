# AOS Webhook Receiver

Production-style staging webhook capture service for AOS alerts and integrations.

## Features

- **Capture**: Receives webhooks at `/webhook` and `/webhook/<path>`
- **HMAC Validation**: Optional signature verification (X-Signature, X-Hub-Signature-256)
- **Authentication**: Bearer token authentication (X-Webhook-Token)
- **Storage**: PostgreSQL with configurable retention
- **Replay**: Replay webhooks to target URLs
- **Export**: JSON/NDJSON export for analysis
- **Metrics**: Prometheus-compatible metrics endpoint

## Quick Start

### Using Docker Compose (recommended)

```bash
cd tools/webhook_receiver
docker compose up -d
```

### Using uvicorn directly

```bash
pip install -r requirements.txt

DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos \
WEBHOOK_TOKEN=your-secret-token \
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://nova:novapass@localhost:6432/nova_aos` | PostgreSQL connection |
| `WEBHOOK_TOKEN` | (empty) | Auth token (empty = no auth) |
| `WEBHOOK_SECRET` | (empty) | HMAC secret for signature validation |
| `RETENTION_DAYS` | `30` | Days to retain webhooks |
| `MAX_BODY_SIZE` | `1048576` | Max body size (1MB) |

## API Endpoints

### Receive Webhooks

```bash
# Simple webhook
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: your-token" \
  -d '{"event": "test", "value": 42}'

# With path
curl -X POST http://localhost:8080/webhook/alertmanager \
  -H "Content-Type: application/json" \
  -d '[{"labels": {"alertname": "CostSimV2Disabled"}}]'
```

### Query Webhooks

```bash
# List all webhooks
curl http://localhost:8080/webhooks

# Filter by alertname
curl "http://localhost:8080/webhooks?alertname=CostSimV2Disabled"

# Filter by date range
curl "http://localhost:8080/webhooks?since=2024-01-01T00:00:00Z&until=2024-01-02T00:00:00Z"

# Get specific webhook
curl http://localhost:8080/webhooks/123

# Get raw body
curl http://localhost:8080/webhooks/123/raw
```

### Replay Webhooks

```bash
# Replay to target URL
curl -X POST "http://localhost:8080/webhooks/123/replay?target_url=http://my-service:8000/api/alerts"
```

### Export

```bash
# Export as JSON
curl "http://localhost:8080/webhooks/export?format=json&alertname=CostSimV2Disabled"

# Export as NDJSON (newline-delimited JSON)
curl "http://localhost:8080/webhooks/export?format=ndjson"
```

### Stats & Health

```bash
# Stats
curl http://localhost:8080/stats

# Health check
curl http://localhost:8080/health

# Prometheus metrics
curl http://localhost:8080/metrics
```

### Cleanup

```bash
# Delete expired webhooks
curl -X DELETE http://localhost:8080/webhooks/expired
```

## Integration with AOS

### Point Alertmanager to webhook receiver

In your Alertmanager config:

```yaml
receivers:
  - name: webhook-staging
    webhook_configs:
      - url: http://webhook-receiver:8080/webhook/alertmanager
        send_resolved: true
```

### Use in shadow runs

```bash
# Set Alertmanager URL to webhook receiver
export ALERTMANAGER_URL=http://localhost:8080/webhook/alertmanager

# Run shadow validation
./scripts/ops/canary/run_canary.sh
```

### Query captured alerts

```bash
# See all CostSim alerts
curl "http://localhost:8080/webhooks?alertname=CostSimV2Disabled"

# Export for analysis
curl "http://localhost:8080/webhooks/export?format=ndjson&alertname=CostSimV2Disabled" > alerts.ndjson
```

## Development

### Run tests

```bash
pytest tests/
```

### Initialize database manually

```python
from app.models import get_engine, init_db

engine = get_engine("postgresql://nova:novapass@localhost:6432/nova_aos")
init_db(engine)
```
