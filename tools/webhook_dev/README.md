# AOS Webhook Dev - Lightweight Local Receiver

Simple Flask-based webhook receiver for local development and quick debugging.

## Features

- **Zero dependencies** (just Flask + SQLite)
- **Web UI** with auto-refresh
- **Colorized console output**
- **JSON API**
- **Optional ngrok tunnel**

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
cd tools/webhook_dev
docker compose up -d

# Web UI: http://localhost:5000/
# Webhook: http://localhost:5000/webhook
```

### Option 2: Run directly

```bash
pip install flask
python app.py

# Web UI: http://localhost:5000/
```

### Option 3: With ngrok tunnel

```bash
# Set your ngrok auth token
export NGROK_AUTHTOKEN=your_token_here

# Start with tunnel profile
docker compose --profile tunnel up -d

# Get public URL from ngrok dashboard
open http://localhost:4040
```

## Usage

### Send test webhook

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "test", "value": 42}'
```

### Send Alertmanager-style alert

```bash
curl -X POST http://localhost:5000/webhook/alertmanager \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "CostSimV2Disabled",
      "severity": "P1"
    },
    "status": "firing"
  }]'
```

### View webhooks

```bash
# JSON API
curl http://localhost:5000/webhooks | jq .

# Filter by alertname
curl "http://localhost:5000/webhooks?alertname=CostSimV2Disabled"

# Get specific webhook
curl http://localhost:5000/webhooks/1
```

### Clear all webhooks

```bash
curl -X POST http://localhost:5000/clear
```

## Point AOS to this receiver

```bash
# Set Alertmanager URL
export ALERTMANAGER_URL=http://localhost:5000/webhook/alertmanager

# Run tests or services
python -m pytest tests/integration/
```

## Console Output

The receiver prints colorized output for each webhook:

```
[WEBHOOK #1] POST /webhook/alertmanager
  Content-Type: application/json
  Alert: CostSimV2Disabled (P1)
  Body: [{"labels": {"alertname": "CostSimV2Disabled"...
```

Colors:
- 🔴 Red: P1/critical
- 🟡 Yellow: P2/warning
- 🟢 Green: P3/other
