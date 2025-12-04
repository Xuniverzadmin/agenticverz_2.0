# AOS Tabletop Drill: Registry Regression + LLM Auth Failure

## Overview

**Duration:** 60-90 minutes
**Participants:** DevOps (executor), SRE (obs/metrics), Product/PM (impact owner), On-call dev

## Scenario

**Incident start:** 02:12 UTC

**Symptoms detected:**
- Nightly registry benchmark shows p50 jump from 2.6ms to 12s
- LLM adapter live tests returning 401 Unauthorized
- Cost alerts show 0 spend (no successful LLM calls)

## Phase 1: Triage (10 min)

### Actions

1. **Pull benchmark artifacts:**
   ```bash
   # Download from CI
   gh run download <run-id> -n benchmark-results
   cat benchmark_results.json | jq '.stats'
   ```

2. **Check CI logs:**
   ```bash
   gh run view <run-id> --log
   ```

3. **Confirm regression:**
   - p50: expected <5ms, actual: 12s
   - p90: expected <10ms, actual: 15s
   - p99: expected <20ms, actual: 18s

### Questions to answer:
- [ ] Is this a real regression or flaky test?
- [ ] When did it start? (last green build)
- [ ] What changed between last green and first red?

## Phase 2: Detection (5 min)

### Actions

1. **Check metrics endpoint:**
   ```bash
   curl -s http://localhost:8000/metrics | grep aos_
   ```

2. **Check cost tracker alerts:**
   ```bash
   curl -s http://localhost:8000/health/costs | jq
   ```

3. **Check adapter health:**
   ```bash
   curl -s http://localhost:8000/health/adapters
   ```

### Expected findings:
- `aos_llm_errors_total{code="401"}` increasing
- `aos_llm_latency_p99` unchanged (no calls completing)
- Cost spend: $0 (all calls failing)

## Phase 3: Containment (10 min)

### Option A: Set registry to read-only

```bash
# API call (if implemented)
curl -XPOST -H "Authorization: Bearer $OPS_TOKEN" \
  http://localhost:8000/ops/registry/read-only

# Or environment variable
export REGISTRY_READ_ONLY=true
docker compose restart backend
```

### Option B: Toggle adapter to fallback (stub)

```bash
# Disable live adapter
export FORCE_STUB_ADAPTER=true
docker compose restart backend

# Verify stub is active
curl -s http://localhost:8000/health/adapters
# Should show: {"active": "stub", "live_disabled": true}
```

### Option C: Full rollback

```bash
# Roll back to previous known-good deploy
git checkout <last-good-sha>
docker compose up -d --build
```

## Phase 4: Mitigation (15 min)

### Registry investigation

1. **Check DB/worker logs:**
   ```bash
   docker compose logs backend --tail 500 | grep -i registry
   docker compose logs worker --tail 500 | grep -i error
   ```

2. **Run local benchmark on pinned runner:**
   ```bash
   cd backend
   python scripts/benchmark_registry.py
   ```

3. **Restore registry snapshot if corrupted:**
   ```bash
   /root/agenticverz2.0/scripts/restore_registry.sh \
     /root/agenticverz2.0/backups/registry-YYYYMMDD.sql
   ```

### LLM auth investigation

1. **Test API key manually:**
   ```bash
   curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages \
     -d '{"model": "claude-sonnet-4-20250514", "max_tokens": 1, "messages": [{"role": "user", "content": "Hi"}]}'
   ```

2. **Check for key rotation:**
   - Was the API key rotated?
   - Is the secret manager up to date?

3. **Rotate key if compromised:**
   ```bash
   NEW_KEY=$(openssl rand -hex 32)
   aws secretsmanager update-secret \
     --secret-id aos/anthropic-key \
     --secret-string "$NEW_KEY"
   docker compose restart backend
   ```

## Phase 5: Post-mortem (20 min)

### Timeline capture

| Time | Event | Actor |
|------|-------|-------|
| 02:12 | Nightly CI failed | CI |
| 02:15 | Alert triggered | PagerDuty |
| 02:20 | On-call acknowledged | DevOps |
| ... | ... | ... |

### Root cause analysis

**Proximate cause:** _________
**Contributing factors:** _________
**Detection gap:** _________

### Action items

| Action | Owner | Due |
|--------|-------|-----|
| Add test for X | Dev | 1 week |
| Improve monitoring for Y | SRE | 2 weeks |
| Document Z | DevOps | 1 week |

### Metrics to track

- Time to detection (TTD): ___ minutes
- Time to mitigation (TTM): ___ minutes
- Time to resolution (TTR): ___ minutes
- Customer impact: None / Low / Medium / High

## Deliverables

- [ ] Incident ticket created (JIRA/GitHub issue)
- [ ] Runbook updated with lessons learned
- [ ] Follow-up tests identified
- [ ] Monitoring improvements scheduled

---

## Drill Execution Log

**Date:** _______________
**Participants:**
- DevOps: _____________
- SRE: _____________
- Product: _____________
- On-call: _____________

**Drill started:** _______________
**Drill completed:** _______________

### Notes from drill:
```
[Add observations, improvements, and action items here]
```

### Runbook changes needed:
- [ ] _____________
- [ ] _____________
- [ ] _____________

### Sign-off:
- [ ] DevOps lead
- [ ] SRE lead
- [ ] Product owner
