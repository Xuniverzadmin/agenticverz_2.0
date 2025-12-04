# Webhook Receiver Operations Runbook

This runbook covers operational procedures for the AOS Webhook Receiver service.

## Service Overview

The webhook receiver accepts incoming webhooks (primarily from Alertmanager) and forwards them to the AOS backend for processing. It provides:

- Per-IP and per-tenant rate limiting (Redis-backed)
- HMAC signature validation
- Prometheus metrics for monitoring
- Fail-open behavior when Redis is unavailable

## Architecture

```
                         ┌─────────────────┐
                         │  Alertmanager   │
                         └────────┬────────┘
                                  │ POST /webhook
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌───────────┐    ┌────────────────────┐    ┌────────────┐ │
│  │  Ingress  │───▶│  Webhook Receiver  │◀──▶│   Redis    │ │
│  └───────────┘    └─────────┬──────────┘    └────────────┘ │
│                             │                               │
│                             ▼                               │
│                    ┌────────────────┐                       │
│                    │  AOS Backend   │                       │
│                    └────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (returns 200 if healthy) |
| `/ready` | GET | Readiness check (includes Redis connectivity) |
| `/metrics` | GET | Prometheus metrics |
| `/webhook` | POST | Main webhook ingestion endpoint |
| `/webhook/alertmanager` | POST | Alertmanager-specific webhook format |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `RATE_LIMIT_RPM` | `100` | Requests per minute limit |
| `HMAC_SECRET` | (required) | Secret for HMAC validation |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ENVIRONMENT` | `production` | Environment name for metrics labels |

### Kubernetes Secrets

Required secret: `webhook-secret`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: webhook-secret
type: Opaque
stringData:
  REDIS_URL: "redis://redis:6379/0"
  HMAC_SECRET: "your-secret-here"
```

## Monitoring

### Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `webhooks_received_total` | Counter | Total webhooks received (labels: path, status) |
| `webhook_rate_limit_exceeded_total` | Counter | Rate limit rejections (labels: limit_type) |
| `webhook_rate_limit_redis_connected` | Gauge | Redis connection status (1=connected) |
| `webhook_rate_limit_redis_errors_total` | Counter | Redis operation errors |
| `webhook_rate_limit_allowed_total` | Counter | Requests allowed by rate limiter |

### Grafana Dashboard

Dashboard: "Webhook Receiver" (UID: `webhook-receiver`)

Key panels:
1. Request rate (webhooks/min)
2. Error rate by status code
3. Rate limit rejections
4. Redis connection status
5. P50/P95/P99 latency

### Alerting Rules

Configure in Alertmanager for:

1. **WebhookReceiverDown** - Service unavailable
   ```yaml
   - alert: WebhookReceiverDown
     expr: up{job="webhook-receiver"} == 0
     for: 2m
     labels:
       severity: critical
   ```

2. **WebhookHighRateLimitRejects** - Too many rate limit rejections
   ```yaml
   - alert: WebhookHighRateLimitRejects
     expr: rate(webhook_rate_limit_exceeded_total[5m]) > 10
     for: 5m
     labels:
       severity: warning
   ```

3. **WebhookRedisDisconnected** - Redis unavailable (fail-open mode)
   ```yaml
   - alert: WebhookRedisDisconnected
     expr: webhook_rate_limit_redis_connected == 0
     for: 5m
     labels:
       severity: warning
   ```

## Operational Procedures

### Deploy New Version

```bash
# Build and push image (or wait for CI)
IMAGE_SHA=$(git rev-parse --short=12 HEAD)

# Deploy to staging
IMAGE_SHA=${IMAGE_SHA} ./tools/webhook_receiver/deploy-staging.sh

# Verify deployment
kubectl -n aos-staging rollout status deployment/webhook-receiver
```

### Check Service Health

```bash
# Via kubectl
kubectl -n aos-staging exec -it deploy/webhook-receiver -- curl -s localhost:8080/health

# Via port-forward
kubectl -n aos-staging port-forward svc/webhook-receiver 8081:80 &
curl -s http://localhost:8081/health
curl -s http://localhost:8081/ready
```

### View Logs

```bash
# Recent logs
kubectl -n aos-staging logs -l app=webhook-receiver --tail=100

# Follow logs
kubectl -n aos-staging logs -f -l app=webhook-receiver

# Search for errors
kubectl -n aos-staging logs -l app=webhook-receiver | grep -i error
```

### Check Rate Limiter Status

```bash
# Via Redis CLI
kubectl -n aos-staging exec -it deploy/redis -- redis-cli

# List rate limit keys
KEYS rl:*

# Check specific tenant count
GET rl:tenant:my-tenant:<window>

# Check specific IP count
GET rl:ip:1.2.3.4:<window>
```

### Reset Rate Limits

If a legitimate user is rate-limited, reset their counters:

```bash
# Get current window
WINDOW=$(($(date +%s) / 60))

# Reset IP limit
kubectl -n aos-staging exec -it deploy/redis -- \
  redis-cli DEL "rl:ip:1.2.3.4:${WINDOW}"

# Reset tenant limit
kubectl -n aos-staging exec -it deploy/redis -- \
  redis-cli DEL "rl:tenant:tenant-id:${WINDOW}"
```

### Scale Deployment

```bash
# Scale up for high traffic
kubectl -n aos-staging scale deployment/webhook-receiver --replicas=3

# Scale down during quiet periods
kubectl -n aos-staging scale deployment/webhook-receiver --replicas=1
```

### Restart Service

```bash
# Rolling restart
kubectl -n aos-staging rollout restart deployment/webhook-receiver

# Wait for completion
kubectl -n aos-staging rollout status deployment/webhook-receiver
```

## Troubleshooting

### High Rate Limit Rejections

**Symptoms:**
- `webhook_rate_limit_exceeded_total` increasing rapidly
- Alertmanager reports webhook delivery failures

**Investigation:**
1. Check which limit type is being hit:
   ```bash
   curl -s http://localhost:8081/metrics | grep rate_limit_exceeded
   ```

2. Check if it's a single tenant or IP:
   ```bash
   kubectl -n aos-staging exec -it deploy/redis -- redis-cli KEYS "rl:*"
   ```

**Resolution:**
- If legitimate traffic, increase `RATE_LIMIT_RPM`
- If attack, block the IP at ingress level
- If single tenant overwhelming, contact tenant to throttle

### Redis Connection Issues

**Symptoms:**
- `webhook_rate_limit_redis_connected` = 0
- Logs show "Redis connection failed"
- Service running in fail-open mode

**Investigation:**
1. Check Redis pod status:
   ```bash
   kubectl -n aos-staging get pods -l app=redis
   ```

2. Test connectivity:
   ```bash
   kubectl -n aos-staging exec -it deploy/webhook-receiver -- \
     nc -zv redis 6379
   ```

3. Check Redis logs:
   ```bash
   kubectl -n aos-staging logs -l app=redis
   ```

**Resolution:**
- Restart Redis if hung
- Check Redis memory usage (`INFO memory`)
- Verify network policies allow traffic

### High Latency

**Symptoms:**
- Webhook processing latency > 1s
- Alertmanager timeout errors

**Investigation:**
1. Check pod resource usage:
   ```bash
   kubectl -n aos-staging top pods -l app=webhook-receiver
   ```

2. Check for Redis slowlog:
   ```bash
   kubectl -n aos-staging exec -it deploy/redis -- redis-cli SLOWLOG GET 10
   ```

3. Check backend response times in logs

**Resolution:**
- Scale up replicas if CPU-bound
- Increase resource limits if throttled
- Investigate backend bottlenecks

### Webhook Validation Failures

**Symptoms:**
- 401 Unauthorized responses
- Logs show "HMAC validation failed"

**Investigation:**
1. Verify secret matches between Alertmanager and webhook receiver:
   ```bash
   kubectl -n aos-staging get secret webhook-secret -o jsonpath='{.data.HMAC_SECRET}' | base64 -d
   ```

2. Check Alertmanager webhook configuration

**Resolution:**
- Regenerate and sync HMAC secret
- Verify header name matches (`X-Webhook-Signature`)

## Maintenance

### Log Rotation

Container logs are managed by Kubernetes. Ensure log driver limits are configured in containerd/docker.

### Redis Maintenance

1. **Memory monitoring**: Keep used_memory below 80% of maxmemory
2. **Key expiration**: Rate limit keys expire automatically after window
3. **Backup**: Not required (ephemeral rate limit data)

### Certificate Renewal

TLS certificates managed by cert-manager. Monitor expiration with:
```bash
kubectl -n aos-staging get certificate
```

## Emergency Procedures

### Complete Service Failure

1. Check pod status and events:
   ```bash
   kubectl -n aos-staging describe deployment/webhook-receiver
   kubectl -n aos-staging get events --sort-by=.lastTimestamp
   ```

2. Roll back to previous version:
   ```bash
   kubectl -n aos-staging rollout undo deployment/webhook-receiver
   ```

3. If ingress issue, check ingress controller:
   ```bash
   kubectl -n ingress-nginx logs -l app=ingress-nginx
   ```

### DDoS / Abuse

1. Enable strict rate limiting:
   ```bash
   kubectl -n aos-staging set env deployment/webhook-receiver RATE_LIMIT_RPM=10
   ```

2. Block offending IPs at ingress:
   ```yaml
   metadata:
     annotations:
       nginx.ingress.kubernetes.io/denylist-source-range: "1.2.3.4/32"
   ```

3. If necessary, scale to 0 temporarily:
   ```bash
   kubectl -n aos-staging scale deployment/webhook-receiver --replicas=0
   ```

## Contacts

- **On-call**: Check PagerDuty rotation
- **Escalation**: #aos-incidents Slack channel
- **Repository**: github.com/aos/agenticverz2.0

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-XX | Initial runbook |
