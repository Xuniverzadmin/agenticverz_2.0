# PIN-103: M23 Survival Stack ($60-80/month)

**Status:** ACTIVE
**Created:** 2025-12-20
**Author:** Claude Opus 4.5
**Supersedes:** PIN-102 (for pre-revenue phase)
**Milestone:** M23

---

## Executive Summary

This is the **minimum viable infrastructure** for M23 AI Incident Console. No vanity. No premature optimization. Just enough to demo, onboard first customers, and not lose data.

**Philosophy:** Tie infrastructure upgrades to revenue milestones, not theoretical best practices.

**Target Cost:** $60-80/month until first $500 MRR

---

## The Hard Truth

| What You Think You Need | What You Actually Need |
|------------------------|------------------------|
| 3-node Vault HA cluster | Fly.io secrets + `.env` |
| Read replicas | Single Neon endpoint |
| Multi-region Redis | Single-region Upstash |
| PagerDuty on-call | Slack webhook |
| Claude fallback | OpenAI only (for now) |
| 99.99% uptime SLA | "It works when I demo it" |

**Rule:** Don't build compliance theater before compliance pressure.

---

## Survival Stack Components

### 1. Database: Neon PostgreSQL Pro

**Cost:** $19/month

**What you get:**
- 1 compute unit (autoscales to 4 CU)
- 10GB storage
- 7-day point-in-time recovery (PITR)
- Connection pooling built-in

**Configuration:**
```
Endpoint: ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech
Region: ap-southeast-1 (Singapore)
Pooler: PgBouncer on port 6432
```

**Why this matters:**
- PITR = you can recover from "I deleted production data"
- Autoscaling = handles traffic spikes without config changes
- Pooler = no connection exhaustion during demos

**What to skip:**
- ❌ Read replicas (until analytics slows production)
- ❌ Manual connection tuning (defaults are fine)
- ❌ Multi-region (until US customers complain)

---

### 2. Cache: Upstash Redis (Pay-as-you-go)

**Cost:** ~$10-15/month (usage-based)

**What you get:**
- 256MB+ memory
- Persistence (AOF)
- TLS encryption
- REST API fallback

**Critical Configuration:**
```bash
# These are NON-NEGOTIABLE
maxmemory-policy: noeviction
appendonly: yes
```

**Why this matters:**
- `noeviction` = Redis fails loudly instead of silently dropping keys
- AOF = data survives Redis restart
- Without these, your determinism guarantee is a lie

**What to skip:**
- ❌ Multi-region replication
- ❌ Dedicated instance
- ❌ Redis clustering

---

### 3. Compute: Fly.io (2 Instances)

**Cost:** ~$15/month

**What you get:**
- 2× shared-cpu-2x (2 vCPU, 1GB RAM each)
- Rolling deploys (zero downtime)
- Health checks + auto-restart
- Anycast routing

**Configuration:**
```toml
# fly.toml
app = "agenticverz-api"
primary_region = "sin"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  min_machines_running = 2

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024

[[services.http_checks]]
  interval = "30s"
  timeout = "5s"
  path = "/health"
```

**Why this matters:**
- 2 instances = no single point of embarrassment
- Health checks = bad deploys don't stay broken
- Rolling deploys = you can ship during demos

**What to skip:**
- ❌ Multi-region (SIN only for now)
- ❌ Dedicated CPU (shared is fine)
- ❌ Auto-scaling policies (manual scale when needed)

---

### 4. CDN/Security: Cloudflare Pro

**Cost:** $20/month

**What you get:**
- WAF (OWASP rules)
- Rate limiting (100 req/min per IP)
- DDoS protection
- SSL/TLS termination
- Analytics

**Configuration:**
```
SSL Mode: Full (Strict)
WAF: Enabled (OWASP ruleset)
Rate Limiting: 100 requests/minute per IP
Cache: Static assets only (JS/CSS/images)
```

**Why this matters:**
- WAF = basic protection against script kiddies
- Rate limiting = one bad actor can't DoS your demo
- It's $20/month insurance

**What to skip:**
- ❌ Bot Management ($$$)
- ❌ Argo Smart Routing
- ❌ Workers (unless you need edge logic)

---

### 5. Secrets: Fly.io Secrets (Not Vault)

**Cost:** $0

**What you get:**
- Encrypted at rest
- Available as environment variables
- No ops overhead

**Configuration:**
```bash
# Set secrets via Fly CLI
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set REDIS_URL="redis://..."
fly secrets set OPENAI_API_KEY="sk-..."
fly secrets set AOS_API_KEY="..."
fly secrets set CLERK_SECRET_KEY="sk_live_..."
```

**Why this matters:**
- Zero ops overhead
- No unsealing, no HA, no audit log management
- Good enough until SOC2 customer demands Vault

**What to skip:**
- ❌ HashiCorp Vault (until compliance requirement)
- ❌ AWS Secrets Manager
- ❌ Any "enterprise" secrets solution

**Migration path:** When you get a SOC2 customer requirement, migrate to HCP Vault ($22/month managed) in one afternoon.

---

### 6. LLM: OpenAI Only

**Cost:** ~$20-30/month (usage-based)

**What you get:**
- gpt-4o-mini for all operations
- $0.15/1M input, $0.60/1M output
- 99.9% uptime (historically)

**Configuration:**
```python
# Single provider, no fallback complexity
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"
LLM_TIMEOUT = 30  # seconds
LLM_MAX_RETRIES = 3
```

**Why this matters:**
- One provider = simpler debugging
- gpt-4o-mini = cost-effective for classification/summarization
- Retries handle transient failures

**What to skip:**
- ❌ Anthropic fallback (until OpenAI outage costs you a deal)
- ❌ Semantic caching (until costs exceed $100/month)
- ❌ Self-hosted models

---

### 7. Monitoring: Grafana Cloud Free + Slack

**Cost:** $0

**What you get:**
- 10,000 series metrics (free tier)
- 50GB logs/month (free tier)
- Unlimited dashboards

**Configuration:**
```yaml
# One alert rule only
- alert: SystemDown
  expr: up == 0
  for: 2m
  annotations:
    summary: "Agenticverz API is DOWN"
  labels:
    severity: critical
    notify: slack
```

**Why this matters:**
- You need to know when it's broken
- You don't need to know everything else (yet)

**What to skip:**
- ❌ PagerDuty ($21/month)
- ❌ On-call rotation (you ARE the on-call)
- ❌ Complex alert rules (one "it's down" alert is enough)
- ❌ Distributed tracing (Tempo)

---

## Total Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|-------------|
| Database | Neon Pro | $19 |
| Cache | Upstash Redis | ~$12 |
| Compute | Fly.io (2×) | ~$15 |
| CDN/WAF | Cloudflare Pro | $20 |
| Secrets | Fly.io Secrets | $0 |
| LLM | OpenAI API | ~$25 |
| Monitoring | Grafana Cloud Free | $0 |
| **Total** | | **~$91/month** |

**Actual range:** $70-100/month depending on usage

---

## What This Stack Can Handle

| Metric | Capacity |
|--------|----------|
| Concurrent users | ~100 |
| Requests/second | ~50 |
| Incidents/month | ~50,000 |
| Data storage | 10GB |
| Uptime target | 99.5% |

**This is enough for:**
- 5-10 early customers
- Demo presentations
- First $5K MRR

---

## What's Explicitly OUT

| Item | Why It's Out | When to Add |
|------|-------------|-------------|
| Vault HA | Ops theater | SOC2 customer requirement |
| Read replicas | No analytics load | Analytics slows production |
| Multi-region | No US customers | US customer complains about latency |
| Claude fallback | Complexity | OpenAI outage during important demo |
| PagerDuty | You are the pager | SLA commitments to customers |
| Kubernetes | Massive overkill | Never (Fly.io scales further than you think) |

---

## Revenue-Gated Upgrades

### $0 → $500 MRR: Survival Stack (This PIN)
- Everything above
- ~$80/month infra cost
- You handle incidents manually

### $500 → $2K MRR: Growth Stack
Add:
- HCP Vault ($22/month) — for compliance-conscious customers
- Better Uptime status page ($20/month) — customer confidence
- Anthropic fallback — reliability insurance
- **New cost:** ~$130/month

### $2K → $10K MRR: Scale Stack
Add:
- Neon read replica — analytics separation
- Multi-region Redis — US expansion
- PagerDuty — on-call rotation
- Dedicated Fly.io CPU — consistent performance
- **New cost:** ~$300/month

### $10K+ MRR: Enterprise Stack
Add:
- SOC2 Type II audit
- Dedicated infrastructure review
- 99.9% SLA commitments
- **New cost:** $500-1000/month + audit costs

---

## Deployment Checklist

### Day 1 (4 hours)

- [ ] Upgrade Neon to Pro ($19/month)
- [ ] Enable Neon PITR (Settings → Point-in-time recovery)
- [ ] Verify Upstash `noeviction` + AOF enabled
- [ ] Deploy to Fly.io with 2 instances
- [ ] Migrate secrets to `fly secrets set`
- [ ] Enable Cloudflare Pro + WAF

### Day 2 (2 hours)

- [ ] Configure Grafana Cloud free tier
- [ ] Create single "system down" alert → Slack
- [ ] Test full deploy cycle (push → build → deploy)
- [ ] Verify health check endpoint works

### Day 3 (1 hour)

- [ ] Run demo end-to-end
- [ ] Document any friction points
- [ ] Update runbook for common issues

---

## Failure Scenarios

### What breaks first?

| Scenario | Impact | Recovery |
|----------|--------|----------|
| Fly.io instance dies | 0s downtime (other instance) | Automatic |
| Redis restart | ~30s blip, no data loss (AOF) | Automatic |
| Neon maintenance | ~30s blip | Automatic |
| OpenAI outage | LLM features unavailable | Wait or add fallback |
| You push bad code | Rolling deploy catches it | Rollback: `fly deploy --image previous` |

### What you can't survive (yet)

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Neon region failure | Full outage | Accept risk (rare) |
| Upstash region failure | Full outage | Accept risk (rare) |
| Your laptop dies | Can't deploy | Keep secrets in password manager |

**Risk acceptance:** Regional cloud failures are rare enough that the $200+/month for multi-region isn't justified pre-revenue.

---

## Migration from Current State

### Current → Survival Stack

| Component | Current | Target | Action |
|-----------|---------|--------|--------|
| Database | Neon Free | Neon Pro | Upgrade in console |
| Redis | Upstash Free | Upstash Paid | Already pay-as-you-go |
| Compute | VPS | Fly.io | Deploy new, DNS switch |
| Secrets | Local Vault | Fly.io Secrets | `fly secrets set` |
| CDN | Cloudflare Free | Cloudflare Pro | Upgrade in console |

### Migration Order

1. **Neon upgrade** (5 min, no downtime)
2. **Fly.io deploy** (30 min, parallel to VPS)
3. **DNS switch** (5 min, Cloudflare)
4. **Verify** (15 min)
5. **Decommission VPS** (after 48h stable)

---

## The One Rule

> **Don't optimize infrastructure until infrastructure is the bottleneck.**

Your bottleneck right now is:
- ❌ Not database performance
- ❌ Not Redis throughput
- ❌ Not multi-region latency
- ✅ **Getting the first paying customer**

Build for that.

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-100 | M23 specification (parent) |
| PIN-102 | Full infrastructure spec (use after $2K MRR) |
| PIN-096 | M22 KillSwitch (product foundation) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-20 | Initial survival stack created based on founder-stage feedback |

---

*PIN-103: M23 Survival Stack — Build for revenue, not scale.*
