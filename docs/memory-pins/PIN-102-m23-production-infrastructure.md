# PIN-102: M23 Production Infrastructure Recommendations

**Status:** ACTIVE
**Created:** 2025-12-20
**Author:** Claude Opus 4.5
**Depends On:** PIN-100 (M23 AI Incident Console)
**Milestone:** M23

---

## Executive Summary

This PIN documents the production infrastructure requirements and recommendations for M23 AI Incident Console deployment. It covers database, cache, secrets, compute, CDN, and monitoring layers with specific configurations, cost estimates, and priority-based implementation roadmap.

**Target:** Production-ready infrastructure capable of handling 5+ enterprise customers with 99.9% uptime SLA.

---

## Current Infrastructure Stack

| Component | Service | Endpoint | Status |
|-----------|---------|----------|--------|
| **Database** | Neon PostgreSQL | `ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech` | ✅ Active |
| **Cache/Queue** | Upstash Redis | `apn1-picked-skink-35210.upstash.io:6379` | ✅ Active |
| **Secrets** | HashiCorp Vault | `http://127.0.0.1:8200` | ⚠️ Local only |
| **LLM** | OpenAI API | `api.openai.com` | ✅ Active |
| **Auth** | Clerk | Production keys in Vault | ✅ Active |
| **CDN/Proxy** | Cloudflare | SSL termination | ✅ Active |
| **Compute** | VPS (xuniverz) | Single node | ⚠️ No HA |

---

## Production URLs

| Service | URL | Status |
|---------|-----|--------|
| API | `api.agenticverz.com` | ✅ Active |
| Guard Console | `console.agenticverz.com/guard` | ⏳ Deploy |
| Operator Console | `ops.agenticverz.com` | ⏳ Deploy |
| Certificate Verify | `verify.agenticverz.com` | ⏳ Create |
| Landing | `agenticverz.com` | ✅ Active |

---

## Infrastructure Components

### 1. Database - Neon PostgreSQL

**Current Configuration:**
- Endpoint: `ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech`
- Region: ap-southeast-1 (Singapore)
- Connection: PgBouncer pooler (port 6432)
- Plan: Free tier (0.25 CU, 512MB storage)

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  PRODUCTION DATABASE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐     ┌─────────────────┐     ┌──────────┐ │
│  │ Backend │────▶│ Neon Pooler     │────▶│ Primary  │ │
│  │ (Read)  │     │ (PgBouncer)     │     │ Database │ │
│  └─────────┘     └─────────────────┘     └──────────┘ │
│                          │                     │       │
│                          ▼                     ▼       │
│                  ┌──────────────┐      ┌───────────┐  │
│                  │ Read Replica │      │ Auto      │  │
│                  │ (Analytics)  │      │ Backups   │  │
│                  └──────────────┘      └───────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Recommendations:**

| Item | Recommendation | Priority | Status |
|------|---------------|----------|--------|
| Connection Pooling | Use Neon's built-in pooler (6432) | P0 | ✅ Done |
| Read Replicas | Add for search/analytics queries | P1 | ⏳ Pending |
| Auto-scaling | Enable Neon autoscaling (0.25→4 CU) | P1 | ⏳ Pending |
| Point-in-Time Recovery | Enable 7-day PITR | P0 | ⏳ Pending |
| Connection Limits | Set `max_connections=100` per pooler | P1 | ⏳ Pending |

**Plan Upgrade Required:**
```bash
# Current: Free tier (0.25 CU, 512MB storage)
# Recommended: Pro tier ($19/month)
# - 1 CU compute
# - 10GB storage
# - Autoscaling (0.25-4 CU)
# - Read replicas
# - 7-day history (PITR)
```

---

### 2. Cache/Queue - Upstash Redis

**Current Configuration:**
- Endpoint: `apn1-picked-skink-35210.upstash.io:6379`
- Region: ap-northeast-1 (Tokyo)
- Plan: Free tier (256MB, 10K commands/day)

**Recommendations:**

| Item | Recommendation | Priority | Status |
|------|---------------|----------|--------|
| Region | Match Neon region (ap-southeast-1) | P2 | ⚠️ Mismatch |
| Eviction Policy | `noeviction` (fail on full) | P0 | ⏳ Pending |
| Persistence | Enable AOF (Append Only File) | P0 | ⏳ Pending |
| Max Memory | Upgrade to 256MB+ for production | P1 | ⏳ Pending |
| Global Replication | Add US region for latency | P2 | ⏳ Pending |

**Plan Upgrade Required:**
```bash
# Current: Free tier (256MB, 10K commands/day)
# Recommended: Pay-as-you-go ($0.20/100K commands)
# - Unlimited commands
# - Multi-region available
# - Persistence guaranteed
# - TLS encryption
```

**Configuration Script:**
```bash
# Set eviction policy via Upstash Console or CLI
upstash redis config set maxmemory-policy noeviction
upstash redis config set appendonly yes
```

---

### 3. Secrets Management - HashiCorp Vault

**Current Configuration:**
- Address: `http://127.0.0.1:8200`
- Storage: File-based (local)
- Unseal: Manual (requires human intervention after restart)
- Status: Single node, no HA

**Current Vault Paths:**
```
agenticverz/
├── app-prod          # AOS_API_KEY, MACHINE_SECRET_TOKEN
├── database          # POSTGRES_*, DATABASE_URL
├── database-prod     # Production Neon credentials
├── external-apis     # ANTHROPIC_API_KEY, OPENAI_API_KEY
├── external-integrations  # GitHub, Slack, PostHog tokens
├── keycloak-admin    # Keycloak admin credentials
├── llm               # LLM API keys
├── package-registry  # PyPI, npm tokens
└── r2-storage        # Cloudflare R2 credentials
```

**Production Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  VAULT HA ARCHITECTURE (Production)                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Option A: Self-Managed HA Cluster                      │
│  ┌──────────────────────────────────────────────┐      │
│  │           Vault Cluster (3 nodes)             │      │
│  │  ┌────────┐  ┌────────┐  ┌────────┐         │      │
│  │  │ Node 1 │  │ Node 2 │  │ Node 3 │         │      │
│  │  │ Active │  │Standby │  │Standby │         │      │
│  │  └────────┘  └────────┘  └────────┘         │      │
│  └──────────────────────────────────────────────┘      │
│                          │                              │
│                          ▼                              │
│                  ┌──────────────┐                      │
│                  │ Raft Storage │                      │
│                  │ (Integrated) │                      │
│                  └──────────────┘                      │
│                                                         │
│  Option B: HCP Vault (Recommended)                      │
│  ┌──────────────────────────────────────────────┐      │
│  │  HashiCorp Cloud Platform                     │      │
│  │  - Fully managed                              │      │
│  │  - Auto-unseal                                │      │
│  │  - HA built-in                                │      │
│  │  - $22/month                                  │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**Recommendations:**

| Item | Recommendation | Priority | Status |
|------|---------------|----------|--------|
| Auto-Unseal | Use AWS KMS or GCP Cloud KMS | P0 | ⏳ Critical |
| HA Mode | Deploy 3-node cluster OR use HCP Vault | P1 | ⏳ Pending |
| Audit Logging | Enable audit to file/syslog | P0 | ⏳ Pending |
| Secret Rotation | Automate 90-day rotation | P1 | ⏳ Pending |
| Backup | Daily snapshot to S3/R2 | P0 | ⏳ Pending |

**Auto-Unseal Configuration (AWS KMS):**
```hcl
# /etc/vault.d/vault.hcl
seal "awskms" {
  region     = "ap-southeast-1"
  kms_key_id = "alias/vault-unseal-key"
}

storage "raft" {
  path = "/opt/vault/data"
  node_id = "vault-1"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = false
  tls_cert_file = "/etc/vault.d/tls/vault.crt"
  tls_key_file  = "/etc/vault.d/tls/vault.key"
}

api_addr = "https://vault.agenticverz.com:8200"
cluster_addr = "https://vault.agenticverz.com:8201"
```

---

### 4. LLM Provider - OpenAI

**Current Configuration:**
- Model: `gpt-4o-mini` (cost-effective)
- API Key: Stored in Vault at `agenticverz/external-apis`
- Rate Limits: Default OpenAI tier

**Recommendations:**

| Item | Recommendation | Priority | Status |
|------|---------------|----------|--------|
| Model Selection | gpt-4o-mini for cost | P0 | ✅ Done |
| Rate Limiting | Client-side retry with exponential backoff | P0 | ⏳ Pending |
| Fallback Provider | Anthropic Claude as backup | P1 | ⏳ Pending |
| Cost Tracking | Per-tenant token usage tracking | P0 | ⏳ Pending |
| Semantic Cache | Cache repeated queries (Redis) | P2 | ⏳ Pending |

**Cost Projection:**
```
gpt-4o-mini pricing:
- Input:  $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

Estimated usage (100K incidents/month):
- Avg tokens per incident: 500 input + 200 output
- Monthly input:  50M tokens = $7.50
- Monthly output: 20M tokens = $12.00
- Total: ~$20/month in API costs

With growth (500K incidents/month):
- Total: ~$100/month in API costs
```

**Fallback Configuration:**
```python
# backend/app/services/llm_service.py
LLM_PROVIDERS = [
    {
        "name": "openai",
        "model": "gpt-4o-mini",
        "priority": 1,
        "timeout": 30,
    },
    {
        "name": "anthropic",
        "model": "claude-3-haiku-20240307",
        "priority": 2,
        "timeout": 30,
    },
]
```

---

### 5. CDN/Edge - Cloudflare

**Current Configuration:**
- Proxy: Enabled (orange cloud)
- SSL: Full (Strict) with Origin Certificate
- WAF: Not enabled
- Rate Limiting: Not configured at edge

**Recommendations:**

| Item | Recommendation | Priority | Status |
|------|---------------|----------|--------|
| WAF | Enable Cloudflare WAF (OWASP rules) | P0 | ⏳ Pending |
| Rate Limiting | 100 req/min per IP at edge | P0 | ⏳ Pending |
| Cache | Cache static assets (console JS/CSS) | P1 | ⏳ Pending |
| DDoS Protection | Enabled by default | P0 | ✅ Done |
| Bot Management | Enable for API endpoints | P2 | ⏳ Pending |

**Cloudflare WAF Rules:**
```
Rule 1: Block known bad bots
Rule 2: Rate limit API endpoints (100/min)
Rule 3: Challenge suspicious IPs
Rule 4: Block requests without User-Agent
Rule 5: Geo-block high-risk countries (optional)
```

**Cache Rules:**
```
# Cache static assets
/*.js   - Cache 1 week
/*.css  - Cache 1 week
/*.png  - Cache 1 month
/*.ico  - Cache 1 month

# Never cache API
/api/*  - Bypass cache
/v1/*   - Bypass cache
```

---

### 6. Compute - Backend Hosting

**Current Configuration:**
- Platform: Single VPS (xuniverz server)
- Docker Compose deployment
- No auto-scaling
- No health checks from external

**Recommended Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│  PRODUCTION COMPUTE - FLY.IO (Recommended)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│            ┌─────────────────────────┐                 │
│            │    Cloudflare Edge      │                 │
│            │    (SSL + WAF + Cache)  │                 │
│            └───────────┬─────────────┘                 │
│                        │                                │
│            ┌───────────▼─────────────┐                 │
│            │     Fly.io Anycast      │                 │
│            │    (Global routing)     │                 │
│            └───────────┬─────────────┘                 │
│                        │                                │
│     ┌──────────────────┼──────────────────┐            │
│     │                  │                  │            │
│     ▼                  ▼                  ▼            │
│ ┌────────┐        ┌────────┐        ┌────────┐        │
│ │ SIN-1  │        │ SIN-2  │        │ HND-1  │        │
│ │ (Primary)       │ (Primary)       │ (Backup)        │
│ │ 2 CPU  │        │ 2 CPU  │        │ 2 CPU  │        │
│ │ 1GB RAM│        │ 1GB RAM│        │ 1GB RAM│        │
│ └────────┘        └────────┘        └────────┘        │
│                                                         │
│  Health checks: /health every 10s                      │
│  Auto-restart on failure                               │
│  Rolling deploys (zero downtime)                       │
└─────────────────────────────────────────────────────────┘
```

**Fly.io Configuration:**
```toml
# fly.toml
app = "agenticverz-api"
primary_region = "sin"

[env]
  LOG_LEVEL = "info"
  ENVIRONMENT = "production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 2

  [http_service.concurrency]
    type = "requests"
    soft_limit = 200
    hard_limit = 250

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = "10s"
    timeout = "5s"
    path = "/health"
    method = "GET"

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024

[metrics]
  port = 9090
  path = "/metrics"

[deploy]
  strategy = "rolling"
```

**Alternative Platforms:**

| Platform | Pros | Cons | Cost |
|----------|------|------|------|
| **Fly.io** (Recommended) | Simple, global, cheap | Less enterprise features | $10-20/mo |
| Railway.app | Even simpler | Slightly more expensive | $20-30/mo |
| AWS ECS Fargate | Enterprise, flexible | Complex setup | $30-50/mo |
| Google Cloud Run | Pay-per-request | Cold starts | $5-15/mo |

---

### 7. Monitoring & Observability

**Current Configuration:**
- Metrics: Grafana Cloud (agenticverz.grafana.net)
- Dashboards: M12/M18 multi-agent dashboard
- Alerts: Slack integration

**Recommended Stack:**
```
┌─────────────────────────────────────────────────────────┐
│  OBSERVABILITY STACK                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                 Grafana Cloud                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ Prometheus│ │   Loki   │ │  Tempo   │       │   │
│  │  │ (Metrics)│ │  (Logs)  │ │ (Traces) │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘       │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Alerting Pipeline                   │   │
│  │  Grafana → PagerDuty → On-Call Engineer         │   │
│  │  Grafana → Slack #alerts (non-critical)         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Status Page                         │   │
│  │  Better Uptime / Statuspage.io                  │   │
│  │  - Uptime monitoring (5 endpoints)              │   │
│  │  - Public status page                           │   │
│  │  - Incident communication                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Recommendations:**

| Component | Tool | Purpose | Priority |
|-----------|------|---------|----------|
| Metrics | Grafana Cloud | Application metrics | ✅ Done |
| Logs | Grafana Loki | Centralized logging | P1 |
| Traces | Grafana Tempo | Distributed tracing | P2 |
| Alerts | PagerDuty | On-call rotation | P1 |
| Uptime | Better Uptime | Status page + monitoring | P1 |

**Key Dashboards:**
1. **API Health** - Request rate, latency p50/p95/p99, error rate
2. **Incidents** - New incidents, resolution time, by severity
3. **LLM Costs** - Token usage, cost per tenant, model breakdown
4. **Infrastructure** - Database connections, Redis memory, Vault status

---

## Production Deployment Checklist

### P0 - Critical (Before Launch)

| Task | Description | Owner | Status |
|------|-------------|-------|--------|
| Neon PITR | Enable 7-day point-in-time recovery | DevOps | ⏳ |
| Neon Autoscaling | Enable 0.25-4 CU autoscaling | DevOps | ⏳ |
| Redis noeviction | Set maxmemory-policy noeviction | DevOps | ⏳ |
| Redis AOF | Enable append-only file persistence | DevOps | ⏳ |
| Vault Auto-Unseal | Configure AWS KMS or migrate to HCP | DevOps | ⏳ |
| Vault Audit | Enable audit logging | Security | ⏳ |
| Edge Rate Limits | Configure Cloudflare rate limiting | DevOps | ⏳ |
| WAF Rules | Enable OWASP WAF rules | Security | ⏳ |
| Secrets Migration | Move all .env secrets to Vault | Security | ⏳ |
| SSL Verification | Verify end-to-end TLS (no HTTP) | Security | ⏳ |
| Daily Backups | Configure Neon + Vault backup jobs | DevOps | ⏳ |

### P1 - Important (Week 1)

| Task | Description | Owner | Status |
|------|-------------|-------|--------|
| HA Compute | Deploy to Fly.io with 2+ instances | DevOps | ⏳ |
| Read Replicas | Add Neon read replica for analytics | DevOps | ⏳ |
| LLM Fallback | Configure Anthropic as backup | Backend | ⏳ |
| Centralized Logs | Ship logs to Grafana Loki | DevOps | ⏳ |
| PagerDuty | Configure on-call alerting | DevOps | ⏳ |
| Status Page | Set up Better Uptime / Statuspage | DevOps | ⏳ |

### P2 - Nice to Have (Month 1)

| Task | Description | Owner | Status |
|------|-------------|-------|--------|
| Multi-region | Add US West compute + Redis | DevOps | ⏳ |
| Semantic Cache | Cache LLM responses in Redis | Backend | ⏳ |
| Bot Protection | Enable Cloudflare Bot Management | Security | ⏳ |
| Distributed Tracing | Configure Grafana Tempo | DevOps | ⏳ |

---

## Cost Estimate

### Monthly Production Costs

| Service | Tier | Monthly Cost | Notes |
|---------|------|-------------|-------|
| Neon PostgreSQL | Pro | $19 | 1 CU, 10GB, autoscale |
| Upstash Redis | Pay-as-you-go | ~$20 | Based on usage |
| Fly.io | 2× shared-cpu-2x | ~$20 | 2 instances, SIN region |
| OpenAI API | Pay-as-you-go | ~$30 | gpt-4o-mini, 100K incidents |
| Cloudflare | Pro | $20 | WAF, analytics, rate limiting |
| Grafana Cloud | Free | $0 | Free tier sufficient |
| Better Uptime | Starter | $20 | Status page, 5 monitors |
| **Subtotal** | | **$129** | |

### Optional Add-ons

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| HCP Vault | $22 | Replaces self-managed Vault |
| PagerDuty | $21 | On-call management |
| Anthropic Fallback | ~$10 | Backup LLM provider |
| **With Add-ons** | **$182** | |

### Cost Scaling

| Scale | Incidents/month | Estimated Cost |
|-------|-----------------|----------------|
| Startup | 10K | $100 |
| Growth | 100K | $150 |
| Scale | 500K | $300 |
| Enterprise | 1M+ | $500+ |

---

## Security Checklist

### Authentication & Authorization

- [ ] Clerk production keys configured
- [ ] API keys rotated (90-day policy)
- [ ] RBAC enforced on all endpoints
- [ ] Machine tokens have minimal permissions

### Data Protection

- [ ] TLS 1.3 everywhere (no HTTP)
- [ ] Database encryption at rest (Neon default)
- [ ] Secrets in Vault (not .env)
- [ ] PII data handling documented

### Infrastructure Security

- [ ] WAF enabled at edge
- [ ] Rate limiting at edge AND app layer
- [ ] No public database access
- [ ] Vault audit logging enabled
- [ ] SSH keys rotated

### Compliance Readiness

- [ ] SOC2 Type II controls documented
- [ ] Data retention policy (90 days default)
- [ ] Incident response runbook
- [ ] Backup restoration tested

---

## Disaster Recovery

### RTO/RPO Targets

| Scenario | RTO | RPO |
|----------|-----|-----|
| Single instance failure | 30 seconds | 0 (HA) |
| Database failure | 5 minutes | 1 hour (PITR) |
| Region failure | 30 minutes | 1 hour |
| Complete outage | 2 hours | 24 hours |

### Backup Schedule

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| Neon Database | Continuous | 7 days | Neon (built-in) |
| Vault Secrets | Daily | 30 days | Cloudflare R2 |
| Application Logs | Continuous | 30 days | Grafana Loki |
| Configuration | On change | Forever | Git |

### Recovery Procedures

1. **Database Recovery:**
   ```bash
   # Neon point-in-time recovery via console
   # Select timestamp, create new branch, promote to main
   ```

2. **Vault Recovery:**
   ```bash
   # Restore from R2 backup
   aws s3 cp s3://vault-backups/latest.snap /tmp/
   vault operator raft snapshot restore /tmp/latest.snap
   ```

3. **Application Recovery:**
   ```bash
   # Fly.io automatic recovery
   # If manual needed:
   fly deploy --image ghcr.io/agenticverz/api:latest
   ```

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-100 | M23 specification (parent) |
| PIN-096 | M22 KillSwitch (foundation) |
| PIN-098 | M22.1 UI Console (frontend) |
| PIN-034 | Vault Secrets Management |
| PIN-066 | External API Keys |
| PIN-037 | Grafana Cloud Integration |
| PIN-038 | Upstash Redis Integration |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-20 | Initial PIN created with full infrastructure spec |

---

*PIN-102: M23 Production Infrastructure Recommendations*
