# Webhook Receiver Deployment Guide

## Prerequisites

- Docker and Docker Compose (for local/staging)
- Kubernetes cluster with kubectl access (for K8s deployment)
- Container registry access (for K8s deployment)

---

## Option 1: Local Docker Compose

### Quick Start

```bash
# From repo root
docker-compose -f docker-compose.staging.yml up -d

# Verify
./scripts/test_webhook_receiver.sh
```

### Stop

```bash
docker-compose -f docker-compose.staging.yml down
```

---

## Option 2: Kubernetes Deployment

### Step 1: Build and Push Image

```bash
# Build image
docker build -t <REGISTRY>/webhook-receiver:staging \
  -f tools/webhook_receiver/Dockerfile tools/webhook_receiver/

# Push to registry
docker push <REGISTRY>/webhook-receiver:staging
```

### Step 2: Update Image Reference

Edit `tools/webhook_receiver/k8s/deployment.yaml`:

```yaml
containers:
  - name: webhook
    image: <REGISTRY>/webhook-receiver:staging  # <-- Update this
```

### Step 3: Create Secrets (DO NOT COMMIT)

```bash
# Create namespace
kubectl create ns aos-staging || true

# Create secrets (replace with real values)
kubectl -n aos-staging create secret generic webhook-secret \
  --from-literal=DATABASE_URL="postgresql://webhook:PASSWORD@webhook-db:5432/webhook" \
  --from-literal=WEBHOOK_SECRET="$(openssl rand -hex 32)" \
  --from-literal=RATE_LIMIT_RPM="100"
```

**For production, use:**
- SealedSecrets: `kubeseal < secret.yaml > sealed-secret.yaml`
- External Secrets Operator: Configure ExternalSecret CRD
- HashiCorp Vault: Use vault-secrets-operator

### Step 4: Deploy

```bash
# Apply all manifests
kubectl apply -k tools/webhook_receiver/k8s/

# Watch rollout
kubectl -n aos-staging rollout status deployment/webhook-receiver
```

### Step 5: Verify

```bash
# Check pods
kubectl -n aos-staging get pods -l app=webhook-receiver

# Check logs
kubectl -n aos-staging logs -l app=webhook-receiver --tail=100

# Port-forward for local testing
kubectl -n aos-staging port-forward svc/webhook-receiver 8081:80 &

# Test endpoints
curl -X POST http://localhost:8081/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

curl http://localhost:8081/webhook/list | jq .
curl http://localhost:8081/health
curl http://localhost:8081/metrics
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection string |
| `WEBHOOK_SECRET` | `""` | HMAC secret for signature validation |
| `RATE_LIMIT_RPM` | `100` | Requests per minute per IP |
| `RETENTION_DAYS` | `30` | Days to keep webhooks before cleanup |
| `MAX_BODY_SIZE` | `1048576` | Max request body size (bytes) |

### Ingress/TLS

Edit `tools/webhook_receiver/k8s/ingress.yaml`:

1. Update `host` with your domain
2. Configure TLS:
   - For cert-manager: Add `cert-manager.io/cluster-issuer` annotation
   - For manual: Create TLS secret and reference in `spec.tls`

```yaml
spec:
  tls:
    - hosts:
        - webhooks.your-domain.com
      secretName: webhook-tls
```

---

## Monitoring

### Prometheus

Add to your Prometheus config (see `prometheus/scrape-config.yaml`):

```yaml
scrape_configs:
  - job_name: 'webhook-receiver'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: [aos-staging]
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: webhook-receiver
```

### Grafana

Import dashboard from `grafana/webhook-receiver-dashboard.json`:

```bash
# Via API
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @tools/webhook_receiver/grafana/webhook-receiver-dashboard.json \
  http://localhost:3000/api/dashboards/db
```

---

## Retention CronJob

The retention CronJob runs daily at 03:00 UTC to delete webhooks older than 30 days.

### Manual Run

```bash
# Run cleanup job manually
kubectl -n aos-staging create job --from=cronjob/webhook-retention cleanup-manual

# Check job status
kubectl -n aos-staging get jobs
kubectl -n aos-staging logs job/cleanup-manual
```

---

## Troubleshooting

### Pod CrashLooping

```bash
# Check logs
kubectl -n aos-staging logs -l app=webhook-receiver --previous

# Common issues:
# - DATABASE_URL not set or invalid
# - Database not reachable
# - Secret not created
```

### Rate Limiting

```bash
# Check current rate limit hits
curl http://localhost:8081/metrics | grep rate_limit

# Adjust limit
kubectl -n aos-staging patch secret webhook-secret \
  -p '{"stringData":{"RATE_LIMIT_RPM":"200"}}'

# Restart to pick up new config
kubectl -n aos-staging rollout restart deployment/webhook-receiver
```

### Database Connection

```bash
# Test database connectivity from pod
kubectl -n aos-staging exec -it deploy/webhook-receiver -- \
  python -c "from app.models import get_engine; print(get_engine())"
```

---

## Security Checklist

- [ ] WEBHOOK_SECRET is a strong random value (32+ bytes)
- [ ] DATABASE_URL uses TLS (`?sslmode=require`)
- [ ] Secrets not committed to git
- [ ] Ingress has TLS enabled
- [ ] Network policies restrict pod communication
- [ ] Resource limits set appropriately
- [ ] Pod security context is non-root
