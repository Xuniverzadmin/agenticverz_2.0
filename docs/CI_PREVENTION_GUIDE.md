# CI Prevention Guide: Fool-Proof Consistency Mechanisms

**Created:** 2025-12-07
**Status:** Active
**Related:** PIN-045, RCA-CI-FIXES-2025-12-07.md

---

## Overview

This guide documents the prevention mechanisms put in place to avoid the CI failures experienced on 2025-12-07. These mechanisms operate at multiple layers to catch issues before they reach CI.

---

## Prevention Layers

### Layer 1: Pre-Commit Checks

**Script:** `scripts/ops/ci_consistency_check.sh --quick`

Run before every commit to catch obvious issues:

```bash
# Add to pre-commit hook
./scripts/ops/ci_consistency_check.sh --quick
```

**What it checks:**
- CI workflow has required environment variables
- No `|| true` on critical commands
- Worker processes have PYTHONUNBUFFERED
- Git working directory status

### Layer 2: Pre-Push Checks

**Script:** `scripts/ops/ci_consistency_check.sh`

Run before every push to remote:

```bash
# Add to pre-push hook
./scripts/ops/ci_consistency_check.sh
```

**What it checks:**
- All Layer 1 checks
- WireMock mappings exist
- Test infrastructure patterns
- Service connectivity matrix
- Code patterns (atomic operations, async safety)

### Layer 3: CI Self-Verification

The CI workflow itself includes verification steps:

```yaml
# Redis connectivity check
- name: Verify Redis connectivity
  run: |
    timeout 5 bash -c 'until echo PING | nc -q 1 localhost 6379 | grep -q PONG; do sleep 1; done'

# Worker startup verification
- name: Verify worker is running
  run: |
    sleep 5
    ps aux | grep -q "[w]orker.pool" || exit 1
```

### Layer 4: Automated Regression Tests

Add these tests to catch specific patterns:

```python
# tests/test_concurrency_race.py
def test_concurrent_slot_acquisition_atomic():
    """Verify no race condition in concurrent slot acquisition."""
    import concurrent.futures
    from app.utils.concurrent_runs import ConcurrentRunsLimiter

    limiter = ConcurrentRunsLimiter(fail_open=False)
    test_key = f"race-test-{uuid.uuid4().hex[:8]}"
    max_slots = 2
    acquired = []

    def try_acquire():
        token = limiter.acquire(test_key, max_slots=max_slots)
        if token:
            acquired.append(token)
        return token

    # Try to acquire 10 slots concurrently, only 2 should succeed
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_acquire) for _ in range(10)]
        concurrent.futures.wait(futures)

    assert len(acquired) == max_slots, f"Race condition: {len(acquired)} slots acquired"
```

---

## Service Connectivity Matrix

Always know which service is used in which environment:

| Service | CI (localhost) | Local Dev | Production |
|---------|----------------|-----------|------------|
| PostgreSQL | 5432 (container) | 5433 (docker) | Neon (cloud) |
| Redis | 6379 (container) | 6379 (docker) | Upstash (cloud) |
| WireMock | 8080 (container) | 8080 (docker) | N/A |
| Backend | 8000 (started) | 8000 (docker) | Cloud Run |

**Rule:** CI jobs must explicitly set service URLs to avoid using production secrets:

```yaml
env:
  REDIS_URL: redis://localhost:6379/0  # EXPLICIT - don't rely on secrets
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
```

---

## Environment Variable Checklist

Before adding a new environment variable:

1. **Add to `.env.example`** - Document with comment
2. **Add to CI workflow** - Explicit value for CI environment
3. **Add to docker-compose.yml** - For local development
4. **Add to deployment manifests** - K8s ConfigMap/Secret

Example:
```bash
# .env.example
NEW_SERVICE_URL=  # Required: URL for new service, see docs/setup.md
```

---

## Worker Process Requirements

All background Python processes must:

1. **Use unbuffered output:**
   ```yaml
   env:
     PYTHONUNBUFFERED: "1"
   run: python -u -m app.worker.pool
   ```

2. **Have health endpoint:**
   ```python
   @app.get("/worker/health")
   def worker_health():
       return {"status": "ok", "active_runs": len(active_runs)}
   ```

3. **Log startup confirmation:**
   ```python
   logger.info("worker_started", extra={"pid": os.getpid()})
   ```

4. **Be verifiable in CI:**
   ```yaml
   - name: Verify worker running
     run: |
       sleep 5
       if ! ps aux | grep -q "[w]orker"; then
         cat worker.log
         exit 1
       fi
   ```

---

## Atomic Operation Requirements

Any Redis operation that involves check-then-modify must use atomic Lua scripts:

**Wrong (race condition):**
```python
current = client.zcard(key)
if current < limit:
    client.zadd(key, {token: timestamp})
```

**Right (atomic):**
```lua
local current = redis.call('ZCARD', key)
if current < limit then
    redis.call('ZADD', key, timestamp, token)
    return 1
end
return 0
```

---

## Quick Reference Commands

```bash
# Run full consistency check
./scripts/ops/ci_consistency_check.sh

# Run quick pre-commit check
./scripts/ops/ci_consistency_check.sh --quick

# Test Redis connectivity
echo PING | nc -q 1 localhost 6379

# Test PostgreSQL connectivity
pg_isready -h localhost -p 5432

# Check worker status
ps aux | grep worker

# View last CI run
gh run list --limit 1

# Retry failed CI
gh run rerun <run-id>
```

---

## Git Hook Setup

### Pre-commit hook (`.git/hooks/pre-commit`):

```bash
#!/bin/bash
./scripts/ops/ci_consistency_check.sh --quick
```

### Pre-push hook (`.git/hooks/pre-push`):

```bash
#!/bin/bash
./scripts/ops/ci_consistency_check.sh
```

Make hooks executable:
```bash
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
```

---

## Incident Response

If CI fails unexpectedly:

1. **Check service connectivity first:**
   - Is Redis reachable?
   - Is PostgreSQL reachable?
   - Is the worker running?

2. **Check for environment variable issues:**
   - Are secrets overriding Docker service URLs?
   - Is REDIS_URL explicitly set?

3. **Check process observability:**
   - Are logs being written?
   - Is PYTHONUNBUFFERED set?

4. **Check for race conditions:**
   - Is the test flaky?
   - Does it involve concurrent access?

5. **Document in RCA:**
   - Create RCA report
   - Update PIN-045 or create new PIN
   - Add regression test

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-07 | Initial creation after CI fixes session |
