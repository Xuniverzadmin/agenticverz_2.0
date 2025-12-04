# AOS Operations Runbook

## Overview

This runbook provides operational procedures for the AOS (Agentic Operating System) backend.

## Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  AOS Backend (FastAPI)                  │
│  - /health             Health checks                    │
│  - /health/determinism Determinism status               │
│  - /health/adapters    LLM adapter status               │
│  - /metrics            Prometheus metrics               │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
│  PostgreSQL  │ │  Redis  │ │   Claude    │
│   (State)    │ │ (Cache) │ │    API      │
└──────────────┘ └─────────┘ └─────────────┘
```

## Health Checks

### Basic Health
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", ...}`

### Readiness (K8s)
```bash
curl http://localhost:8000/health/ready
```
Expected: `{"ready": true, "checks": {...}}`

### Determinism Status
```bash
curl http://localhost:8000/health/determinism
```
Shows last replay hash, drift detection status.

---

## Emergency Procedures

### 1. Disable LLM Adapters

**Symptom:** High error rates from LLM calls, rate limiting, unexpected costs.

**Action:**
```bash
# Set environment variable to disable live adapters
export DISABLE_LIVE_ADAPTERS=true

# Restart backend
docker compose restart backend

# Verify
curl http://localhost:8000/health/adapters
# Should show stub adapter only
```

**Rollback:**
```bash
unset DISABLE_LIVE_ADAPTERS
docker compose restart backend
```

### 2. Enable Deterministic Fallback

**Symptom:** Nondeterministic outputs breaking workflows.

**Action:**
```bash
# Force all LLM calls to use stub adapter
export FORCE_STUB_ADAPTER=true
docker compose restart backend
```

**Verification:**
```bash
# Run determinism test
cd backend
PYTHONPATH=. python -m pytest tests/skills/test_m3_integration.py -v -k deterministic
```

### 3. Registry Rollback

**Symptom:** Skill registration failures, corrupted registry.

**Action:**
```bash
# Clear in-memory registry (restarts clean)
docker compose restart backend

# If using persistent registry, restore from backup
psql -h localhost -p 5433 -U nova -d nova_aos < backup/skills_registry.sql
```

### 4. Worker Recovery

**Symptom:** Workers stuck, high pending queue.

**Action:**
```bash
# Check worker status
docker compose logs worker --tail 100

# Force restart workers
docker compose restart worker

# If persistent, clear stuck jobs
redis-cli -h localhost FLUSHDB  # WARNING: Clears all queued work
```

---

## Monitoring

### Key Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| `aos_llm_latency_p99` | > 30s | Check rate limits |
| `aos_llm_error_rate` | > 5% | Check adapter health |
| `aos_skill_execution_time_p99` | > 10s | Profile skill |
| `aos_registry_size` | > 10k | Audit skill explosion |
| `aos_determinism_drift` | > 0 | Investigate replay diff |

### Prometheus Queries

```promql
# LLM error rate (5min)
rate(aos_llm_errors_total[5m]) / rate(aos_llm_calls_total[5m])

# Skill execution latency p99
histogram_quantile(0.99, rate(aos_skill_duration_seconds_bucket[5m]))

# Registry operations per second
rate(aos_registry_operations_total[1m])
```

### Grafana Dashboards

1. **AOS Overview** - High-level service health
2. **LLM Costs** - Token usage, cost per workflow
3. **Determinism** - Replay hashes, drift alerts
4. **Skills Performance** - Per-skill latency, error rates

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
```

### Rate Limit Configuration

```python
# Environment variables
CLAUDE_RATE_LIMIT_RPM=60
CLAUDE_RATE_LIMIT_TPM=100000
```

---

## Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
export LOG_SKILL_PARAMS=true  # WARNING: May log sensitive data
docker compose restart backend
```

### Trace a Request

```bash
# Get request ID from logs
grep "request_id=abc123" /var/log/aos/backend.log

# Or use structured logging
docker compose logs backend | jq 'select(.request_id == "abc123")'
```

### Replay a Workflow

```bash
cd backend
PYTHONPATH=. python -c "
from tests.golden.replay import replay_workflow
result = replay_workflow('workflow_data_extraction.json')
print(f'Hash: {result.content_hash()}')
"
```

---

## Security

### Rotate API Keys

```bash
# Generate new key
NEW_KEY=$(openssl rand -hex 32)

# Update in secrets manager
aws secretsmanager update-secret --secret-id aos/anthropic-key --secret-string "$NEW_KEY"

# Rolling restart (zero downtime)
docker compose up -d --no-deps backend
```

### Audit Log Review

```bash
# Check for unusual patterns
grep "ERR_LLM_AUTH_FAILED" /var/log/aos/backend.log | wc -l

# Review high-cost operations
grep "cost_cents" /var/log/aos/backend.log | sort -t: -k2 -rn | head -20
```

---

## Backup & Recovery

### Database Backup

```bash
# Automated backup (add to cron)
pg_dump -h localhost -p 5433 -U nova nova_aos > backup/aos_$(date +%Y%m%d).sql

# Verify backup
psql -h localhost -p 5433 -U nova -d nova_aos -c "SELECT COUNT(*) FROM skills;"
```

### Registry Export

```bash
# Export skill registry
cd backend
PYTHONPATH=. python -c "
from app.skills import list_skills, get_skill
import json
registry = {s: {'version': get_skill(s).VERSION} for s in list_skills()}
print(json.dumps(registry, indent=2))
" > backup/registry_$(date +%Y%m%d).json
```

---

## Contacts

| Role | Contact | When |
|------|---------|------|
| On-call Engineer | PagerDuty | Service down |
| Platform Lead | Slack #aos-platform | Architecture questions |
| Security | security@example.com | Auth/secrets issues |

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-01 | AOS Team | Initial runbook |
