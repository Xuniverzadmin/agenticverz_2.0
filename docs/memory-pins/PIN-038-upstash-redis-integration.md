# PIN-038: Upstash Redis Integration

**Created:** 2025-12-06
**Status:** ACTIVE
**Category:** Infrastructure / Data Store

---

## Overview

AOS uses Upstash Redis for production idempotency, rate limiting, and caching. Upstash is a serverless Redis provider with per-request pricing and TLS encryption.

---

## Upstash Account

| Field | Value |
|-------|-------|
| **Database Name** | aos-production |
| **Region** | Global (edge-replicated) |
| **Provider** | Upstash |
| **Plan** | Pay-as-you-go |

---

## Connection Details

### Redis CLI (TLS)

```bash
redis-cli --tls -u 'rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379'
```

### Environment Variables

| Variable | Value |
|----------|-------|
| `REDIS_URL` | `rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379` |
| `UPSTASH_REDIS_REST_URL` | `https://on-sunbeam-19994.upstash.io` |
| `UPSTASH_REDIS_REST_TOKEN` | `AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ` |

**Note:** The `rediss://` scheme (with double 's') indicates TLS encryption.

---

## Configuration Files

### .env

**File:** `/root/agenticverz2.0/.env`

```bash
# Redis Configuration (Upstash - Production)
REDIS_URL=rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379
UPSTASH_REDIS_REST_URL=https://on-sunbeam-19994.upstash.io
UPSTASH_REDIS_REST_TOKEN=AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ
```

### docker-compose.yml

**File:** `/root/agenticverz2.0/docker-compose.yml`

```yaml
# Backend service
environment:
  REDIS_URL: ${REDIS_URL:-redis://localhost:6379/0}

# Worker service
environment:
  REDIS_URL: ${REDIS_URL:-redis://localhost:6379/0}
```

The `${REDIS_URL:-...}` syntax uses the env var with a localhost fallback for local dev.

---

## Usage in AOS

### Idempotency Store

**File:** `backend/app/traces/idempotency.py`

The idempotency store uses Redis for distributed deduplication:

```python
# Keys format: idempotency:{tenant_id}:{idempotency_key}
# TTL: 24 hours (configurable)
# Results: NEW, DUPLICATE, CONFLICT
```

### Rate Limiting

**File:** `backend/app/middleware/rate_limiter.py`

Token bucket rate limiter backed by Redis:

```python
# Keys format: ratelimit:{tenant_id}:{endpoint}
# Default: 100 requests/minute per tenant
```

### Memory Service

**File:** `backend/app/memory/memory_service.py`

Redis connection verified on startup:

```python
# Startup log: "redis_connected"
# Health check includes Redis ping
```

---

## Operations

### Test Connection

```bash
# Using redis-cli
redis-cli --tls -u 'rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379' PING
# Expected: PONG

# Using Python
python3 -c "
import redis
r = redis.from_url('rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379')
print(r.ping())
"
```

### Check Server Info

```bash
redis-cli --tls -u 'rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379' INFO server
# Look for: upstash_version, redis_version
```

### List All Keys

```bash
redis-cli --tls -u 'rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379' KEYS '*'
```

### Flush Database (CAUTION)

```bash
# Only use in development/testing
redis-cli --tls -u 'rediss://default:AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ@on-sunbeam-19994.upstash.io:6379' FLUSHDB
```

### Verify Container Uses Upstash

```bash
# Check env var in running container
docker exec nova_agent_manager env | grep REDIS_URL
# Expected: rediss://...@on-sunbeam-19994.upstash.io:6379

# Check startup logs
docker logs nova_agent_manager 2>&1 | grep redis_connected
```

---

## REST API (Alternative)

Upstash also provides a REST API for serverless environments:

```bash
# Using REST API
curl "https://on-sunbeam-19994.upstash.io/PING" \
  -H "Authorization: Bearer AU4aAAIncDIyOTA4MmIyNDE0ODI0NDk4OGYwOTE5MTU1OWNjNzdkNnAyMTk5OTQ"
```

**Use cases:**
- Edge functions (Vercel, Cloudflare Workers)
- Lambda/Cloud Functions without persistent connections
- Environments that can't use raw TCP

---

## Pricing

| Tier | Commands/Day | Price |
|------|--------------|-------|
| Free | 10,000 | $0 |
| Pay-as-you-go | Unlimited | $0.20 per 100K commands |

**Current usage:** Free tier sufficient for development and light production.

**Cost optimization:**
- Use TTL on all keys to prevent unbounded growth
- Batch operations where possible (MGET, MSET)
- Use REST API for serverless to avoid connection overhead

---

## Security

| Feature | Status |
|---------|--------|
| TLS Encryption | Enabled (`rediss://`) |
| Authentication | Password in URL |
| IP Allowlist | Not configured (Upstash allows all) |
| Audit Logs | Available in Upstash console |

**Best practices:**
- Never commit REDIS_URL to git (use .env)
- Rotate password periodically via Upstash console
- Monitor usage for anomalies

---

## Troubleshooting

### Connection refused

1. Verify URL uses `rediss://` (TLS) not `redis://`
2. Check password is correct
3. Verify network allows outbound 6379

### Container still using localhost

1. Check `docker-compose.yml` uses `${REDIS_URL:-...}` syntax
2. Verify `.env` file exists and has REDIS_URL
3. Recreate containers: `docker compose up -d backend worker`

### Slow operations

1. Check latency to Upstash region
2. Consider global replication if needed
3. Use REST API for serverless workloads

---

## Migration from Local Redis

If migrating from local Redis to Upstash:

1. **Update .env:**
   ```bash
   REDIS_URL=rediss://...@on-sunbeam-19994.upstash.io:6379
   ```

2. **Update docker-compose.yml:**
   ```yaml
   REDIS_URL: ${REDIS_URL:-redis://localhost:6379/0}
   ```

3. **Restart services:**
   ```bash
   docker compose up -d backend worker
   ```

4. **Verify:**
   ```bash
   docker exec nova_agent_manager env | grep REDIS_URL
   docker logs nova_agent_manager 2>&1 | grep redis_connected
   ```

---

## Related PINs

- PIN-037: Grafana Cloud Integration
- PIN-036: Infrastructure Pending Items
- PIN-017: M4 Monitoring Infrastructure
