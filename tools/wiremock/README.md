# WireMock for AOS CI

Deterministic HTTP mocking for integration tests and CI pipelines.

## Features

- **Alertmanager stubs**: Mock `/api/v2/alerts` endpoints
- **Webhook stubs**: Generic webhook receivers
- **Request recording**: Capture and replay requests
- **Response templating**: Dynamic responses based on request data

## Quick Start

### Local Development

```bash
cd tools/wiremock
docker compose up -d

# Admin UI: http://localhost:8080/__admin/
# Check mappings: http://localhost:8080/__admin/mappings
```

### Run tests with WireMock

```bash
# Start WireMock
docker compose up -d

# Point tests to WireMock
export ALERTMANAGER_URL=http://localhost:8080/api/v2/alerts

# Run tests
cd backend
PYTHONPATH=. pytest tests/integration/test_circuit_breaker.py -v
```

## Pre-configured Mappings

### Alertmanager (`mappings/alertmanager-alerts.json`)

| Method | URL | Response |
|--------|-----|----------|
| POST | `/api/v2/alerts*` | 200 OK |
| GET | `/api/v2/alerts*` | 200 [] |
| GET | `/-/healthy` | 200 OK |
| GET | `/-/ready` | 200 OK |

### Generic Webhooks (`mappings/webhook-generic.json`)

| Method | URL | Response |
|--------|-----|----------|
| POST | `/webhook*` | 200 OK |
| POST | `/services/*` (Slack) | 200 ok |
| POST | `/v2/enqueue` (PagerDuty) | 202 Accepted |

## API Reference

### Check received requests

```bash
# List all requests
curl http://localhost:8080/__admin/requests | jq .

# Count requests
curl http://localhost:8080/__admin/requests | jq '.requests | length'

# Filter by URL
curl http://localhost:8080/__admin/requests | jq '.requests[] | select(.request.url | contains("alerts"))'
```

### Add mapping dynamically

```bash
curl -X POST http://localhost:8080/__admin/mappings \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "method": "POST",
      "url": "/custom/endpoint"
    },
    "response": {
      "status": 201,
      "jsonBody": {"id": "12345"}
    }
  }'
```

### Reset state

```bash
# Clear all requests
curl -X POST http://localhost:8080/__admin/requests/reset

# Clear all mappings
curl -X POST http://localhost:8080/__admin/mappings/reset
```

## CI Integration

The GitHub Actions workflow (`ci.yml`) includes a `costsim-wiremock` job that:

1. Starts WireMock as a service
2. Configures Alertmanager stubs
3. Runs integration tests against WireMock
4. Verifies requests were received

See `.github/workflows/ci.yml` for the full configuration.

## Adding New Mappings

1. Create a JSON file in `mappings/`
2. Follow the WireMock mapping format:

```json
{
  "mappings": [
    {
      "id": "unique-id",
      "name": "Description",
      "request": {
        "method": "POST",
        "urlPattern": "/path.*"
      },
      "response": {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "jsonBody": {"status": "ok"}
      }
    }
  ]
}
```

3. Restart WireMock or POST to `/__admin/mappings`

## Resources

- [WireMock Documentation](https://wiremock.org/docs/)
- [WireMock Docker Hub](https://hub.docker.com/r/wiremock/wiremock)
- [Request Matching](https://wiremock.org/docs/request-matching/)
- [Response Templating](https://wiremock.org/docs/response-templating/)
