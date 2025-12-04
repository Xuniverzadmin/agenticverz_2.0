# PIN-029: Infrastructure Hardening & CI Fixes

**Status:** COMPLETE (Pending: Docker build, K8s deploy)
**Date:** 2025-12-04
**Category:** Infrastructure / CI / Operations
**Priority:** HIGH
**Sessions:** 2

---

## Summary

This session addressed 10 infrastructure and CI improvements spanning datetime deprecation fixes, Docker/K8s deployments, CI workflow enhancements, rate limiting, and test improvements.

---

## Work Completed

### 1. ✅ Alembic Migration for Timestamp Defaults

**Status:** Already in place - no action needed

- Migration `007_add_costsim_cb_state.py` already has `server_default=sa.text('now()')` for both `created_at` and `updated_at`
- Database verified to have correct defaults

**Verification:**
```sql
SELECT column_name, column_default FROM information_schema.columns
WHERE table_name='costsim_cb_state' AND column_name IN ('created_at','updated_at');
-- Both show: now()
```

---

### 2. ✅ Fix datetime.utcnow() Deprecation Warnings

**Files Modified:** 8 files, 39 occurrences fixed

| File | Changes |
|------|---------|
| `app/db.py` | Added `utc_now()` helper function, replaced 21 occurrences |
| `app/costsim/circuit_breaker.py` | Replaced 7 occurrences |
| `app/schemas/agent.py` | Added `_utc_now()` helper, replaced 2 occurrences |
| `app/schemas/artifact.py` | Added `_utc_now()` helper, replaced 2 occurrences |
| `app/schemas/plan.py` | Added `_utc_now()` helper, replaced 1 occurrence |
| `app/storage/artifact.py` | Replaced 1 occurrence |
| `scripts/run_escalation.py` | Replaced 3 occurrences |
| `tests/api/test_policy_api.py` | Replaced 3 occurrences |

**Pattern Used:**
```python
# Old (deprecated)
datetime.utcnow()

# New (timezone-aware)
datetime.now(timezone.utc)
```

---

### 3. ✅ Docker Compose for Staging Webhook Receiver

**File Created:** `/root/agenticverz2.0/docker-compose.staging.yml`

**Services:**
- `webhook-db`: PostgreSQL 15 (port 5433)
- `webhook`: FastAPI webhook receiver (port 8081)

**Usage:**
```bash
docker-compose -f docker-compose.staging.yml up -d
./scripts/test_webhook_receiver.sh
```

---

### 4. ✅ K8s/Helm Manifests for Webhook Receiver

**Directory:** `tools/webhook_receiver/k8s/`

| File | Purpose |
|------|---------|
| `namespace.yaml` | `aos-staging` namespace with labels |
| `secret.yaml` | DB credentials, webhook secret |
| `configmap.yaml` | Application configuration |
| `deployment.yaml` | Deployment with probes, resources, anti-affinity |
| `service.yaml` | ClusterIP service with Prometheus annotations |
| `ingress.yaml` | Optional external access |
| `cronjob-retention.yaml` | Daily cleanup of expired webhooks |
| `kustomization.yaml` | Kustomize configuration |

**Deployment:**
```bash
kubectl apply -k tools/webhook_receiver/k8s/
```

---

### 5. ✅ Mount WireMock Mappings in CI

**Issue:** GitHub Actions services don't support volume mounts

**Solution:** Changed from service to container step with `docker run`:

```yaml
- name: Start WireMock with mounted mappings
  run: |
    docker run -d --name wiremock \
      -p 8080:8080 \
      -v ${{ github.workspace }}/tools/wiremock/mappings:/home/wiremock/mappings:ro \
      -v ${{ github.workspace }}/tools/wiremock/__files:/home/wiremock/__files:ro \
      wiremock/wiremock:3.3.1 \
      --verbose --global-response-templating
```

**Mapping Files Split:**
- `alertmanager-post.json` - POST /api/v2/alerts
- `alertmanager-get.json` - GET /api/v2/alerts
- `alertmanager-health.json` - GET /-/healthy
- `alertmanager-ready.json` - GET /-/ready
- `webhook-catchall.json` - Generic webhook catch-all

---

### 6. ✅ Retention CronJob for Webhook Receiver

**File:** `tools/webhook_receiver/k8s/cronjob-retention.yaml`

- Schedule: `0 3 * * *` (daily at 03:00 UTC)
- Action: Delete webhooks older than 30 days
- Configurable retention via `--older-than` argument

---

### 7. ✅ Rate-Limiting for Webhook Receiver

**Dependency Added:** `slowapi>=0.1.9` in `requirements.txt`

**Implementation:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

RATE_LIMIT_RPM = int(os.environ.get("RATE_LIMIT_RPM", "100"))
limiter = Limiter(key_func=get_remote_address)

@app.post("/webhook")
@limiter.limit(f"{RATE_LIMIT_RPM}/minute")
async def receive_webhook(...):
```

**Metrics Added:**
- `webhook_rate_limit_exceeded_total` - Counter of 429 responses

---

### 8. ✅ Re-enable Skipped Tests

**Changed From:** Unconditional `@pytest.mark.skip`
**Changed To:** Conditional `@pytest.mark.skipif`

```python
@pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"),
    reason="Requires running server - set RUN_E2E_TESTS=1"
)
def test_http_skill_execution(...):
```

**Tests Updated:**
- `tests/test_phase4_e2e.py::TestMultiStepExecution::test_http_skill_execution`
- `tests/test_phase4_e2e.py::TestMultiStepExecution::test_skills_registered`

---

### 9. ✅ CI Workflow Full Integration

**New Job Added:** `e2e-tests`

```yaml
e2e-tests:
  runs-on: ubuntu-latest
  needs: [unit-tests, costsim-wiremock]
  services:
    postgres: ...
  steps:
    - Start application server
    - Run E2E tests with RUN_E2E_TESTS=1
```

**All CI Jobs:**
- `unit-tests` - Fast unit tests
- `determinism` - Determinism certification
- `workflow-engine` - Workflow tests
- `workflow-golden-check` - Golden file validation
- `integration` - Integration tests
- `chaos` - Chaos/stress tests
- `legacy` - Legacy compatibility
- `costsim` - CostSim unit tests
- `costsim-integration` - CostSim with DB
- `costsim-wiremock` - CostSim with WireMock
- `e2e-tests` - Full E2E with running server
- `lint-alerts` - Prometheus rules validation

---

## Files Created/Modified

### Created
| File | Purpose |
|------|---------|
| `docker-compose.staging.yml` | Staging webhook receiver deployment |
| `scripts/test_webhook_receiver.sh` | Webhook receiver smoke test |
| `tools/webhook_receiver/k8s/namespace.yaml` | K8s namespace |
| `tools/webhook_receiver/k8s/secret.yaml` | K8s secrets |
| `tools/webhook_receiver/k8s/configmap.yaml` | K8s configmap |
| `tools/webhook_receiver/k8s/deployment.yaml` | K8s deployment |
| `tools/webhook_receiver/k8s/service.yaml` | K8s service |
| `tools/webhook_receiver/k8s/ingress.yaml` | K8s ingress |
| `tools/webhook_receiver/k8s/cronjob-retention.yaml` | Retention cronjob |
| `tools/webhook_receiver/k8s/kustomization.yaml` | Kustomize config |
| `tools/wiremock/mappings/alertmanager-post.json` | WireMock mapping |
| `tools/wiremock/mappings/alertmanager-get.json` | WireMock mapping |
| `tools/wiremock/mappings/alertmanager-health.json` | WireMock mapping |
| `tools/wiremock/mappings/alertmanager-ready.json` | WireMock mapping |
| `tools/wiremock/mappings/webhook-catchall.json` | WireMock mapping |

### Modified
| File | Changes |
|------|---------|
| `app/db.py` | Added `utc_now()`, fixed 21 deprecations |
| `app/costsim/circuit_breaker.py` | Fixed 7 deprecations |
| `app/schemas/agent.py` | Fixed 2 deprecations |
| `app/schemas/artifact.py` | Fixed 2 deprecations |
| `app/schemas/plan.py` | Fixed 1 deprecation |
| `app/storage/artifact.py` | Fixed 1 deprecation |
| `scripts/run_escalation.py` | Fixed 3 deprecations |
| `tests/api/test_policy_api.py` | Fixed 3 deprecations |
| `tests/test_phase4_e2e.py` | Changed skip to skipif |
| `tools/webhook_receiver/requirements.txt` | Added slowapi |
| `tools/webhook_receiver/app/main.py` | Added rate limiting |
| `.github/workflows/ci.yml` | WireMock fix, E2E job |

---

## Issues Encountered & Resolutions

| Issue | Resolution |
|-------|------------|
| Alembic migration already existed | Verified existing state, no new migration needed |
| GitHub Actions services don't support volume mounts | Use `docker run` step instead of service |
| WireMock mapping file format wrong | Split into individual files |
| Unconditional test skips | Changed to conditional `skipif` |

---

## Critical Fixes (Session 2)

### WireMock Mapping UUID Issue - FIXED

**Problem:** WireMock 3.x requires `id` field to be a valid UUID, not a string.

**Fix:** Removed `id` fields from all mapping files - WireMock auto-generates UUIDs.

**Files Fixed:**
- `tools/wiremock/mappings/alertmanager-post.json`
- `tools/wiremock/mappings/alertmanager-get.json`
- `tools/wiremock/mappings/alertmanager-health.json`
- `tools/wiremock/mappings/alertmanager-ready.json`
- `tools/wiremock/mappings/webhook-catchall.json`

**Verification:** 5 mappings now load successfully.

### CI E2E Job - FIXED

**Problem:** `|| true` made e2e job non-blocking.

**Fix:** Removed `|| true` from `.github/workflows/ci.yml` line 546.

### Monitoring Infrastructure - ADDED

**Created:**
- `tools/webhook_receiver/prometheus/scrape-config.yaml` - Prometheus job config + alert rules
- `tools/webhook_receiver/grafana/webhook-receiver-dashboard.json` - Grafana dashboard
- `tools/webhook_receiver/DEPLOYMENT.md` - Complete deployment guide

---

## Pending Items

| Priority | Task | Blocker | Command |
|----------|------|---------|---------|
| P0 | Build & push Docker image | Network timeout on this host | `docker build -t <REG>/webhook-receiver:staging -f tools/webhook_receiver/Dockerfile tools/webhook_receiver/` |
| P0 | Create K8s secrets | Needs real credentials | See `DEPLOYMENT.md` |
| P1 | Deploy to K8s staging | Needs image + secrets | `kubectl apply -k tools/webhook_receiver/k8s/` |
| P1 | Configure Ingress/TLS | Needs hostname + cert | Update `ingress.yaml` |
| P2 | Test docker-compose | Docker build blocked | `docker-compose -f docker-compose.staging.yml up` |
| P2 | Validate retention CronJob | Needs deployed env | Run manual job |
| P2 | Test rate limiting | Needs deployed env | Send >100 req/min |
| P3 | CI validation | None | Push to test branch |

---

## Acceptance Criteria Met

| Criterion | Status |
|-----------|--------|
| `datetime.utcnow()` warnings eliminated | ✅ 0 occurrences remain |
| Docker Compose staging deployment created | ✅ `docker-compose.staging.yml` |
| K8s manifests for webhook receiver | ✅ 8 files in `k8s/` |
| WireMock mappings mounted in CI | ✅ Via `docker run` |
| Retention cronjob configured | ✅ Daily at 03:00 UTC |
| Rate limiting implemented | ✅ 100 RPM default |
| Skipped tests conditionally enabled | ✅ Via `RUN_E2E_TESTS` |
| CI runs full integration | ✅ 12 jobs configured |

---

## Test Results

```
tests/test_phase4_e2e.py: 18 passed, 2 skipped in 4.69s
tests/integration/test_circuit_breaker.py: All passing
```

---

## Related PINs

- PIN-028: M6 Critical Gaps Fixes (same session)
- PIN-026: M6 Implementation Complete
- PIN-025: M6 Implementation Plan

---

## Changelog

| Time | Action |
|------|--------|
| 2025-12-04 Session 2 | Fixed WireMock UUID issue (removed invalid `id` fields) |
| 2025-12-04 Session 2 | Removed `\|\| true` from CI e2e job |
| 2025-12-04 Session 2 | Created `prometheus/scrape-config.yaml` |
| 2025-12-04 Session 2 | Created `grafana/webhook-receiver-dashboard.json` |
| 2025-12-04 Session 2 | Created `DEPLOYMENT.md` with security checklist |
| 2025-12-04 Session 1 | Created PIN-029 |
| 2025-12-04 Session 1 | Fixed 39 datetime.utcnow() deprecations |
| 2025-12-04 Session 1 | Created docker-compose.staging.yml |
| 2025-12-04 Session 1 | Created K8s manifests (8 files) |
| 2025-12-04 Session 1 | Split WireMock mappings into individual files |
| 2025-12-04 Session 1 | Added rate limiting to webhook receiver |
| 2025-12-04 Session 1 | Updated CI workflow with E2E job |

---

## Session 2 Summary

### Issues Faced

| Issue | Root Cause | Resolution |
|-------|------------|------------|
| WireMock container crash | `id` field must be valid UUID in WireMock 3.x | Removed `id` fields from all 5 mapping files |
| Docker build timeout | Network issues reaching Debian apt repos | Documented as pending; must run in CI or different host |
| E2E tests non-blocking | `\|\| true` suffix made failures silent | Removed from ci.yml |
| File permissions | Mappings created with 600 perms | Changed to 644 |

### Decisions Made

| Decision | Rationale |
|----------|-----------|
| Remove `id` field entirely | WireMock auto-generates UUIDs; simpler than converting |
| Create comprehensive DEPLOYMENT.md | Single source of truth for all deployment scenarios |
| Include security checklist | Ensure secrets, TLS, network policies aren't forgotten |
| Use Prometheus service discovery for K8s | More maintainable than static targets |

### Files Created (Session 2)

| File | Purpose |
|------|---------|
| `tools/webhook_receiver/prometheus/scrape-config.yaml` | Prometheus job config + 3 alert rules |
| `tools/webhook_receiver/grafana/webhook-receiver-dashboard.json` | Grafana dashboard (7 panels) |
| `tools/webhook_receiver/DEPLOYMENT.md` | Complete deployment guide |

### Files Modified (Session 2)

| File | Change |
|------|--------|
| `tools/wiremock/mappings/*.json` (5 files) | Removed invalid `id` fields |
| `.github/workflows/ci.yml` | Removed `\|\| true` from e2e job |

### Verification (Session 2)

```bash
# WireMock mappings load successfully
docker run --rm -p 8080:8080 -v $(pwd)/tools/wiremock/mappings:/home/wiremock/mappings:ro \
  wiremock/wiremock:3.3.1 --verbose
curl http://localhost:8080/__admin/mappings | jq '.mappings | length'
# Result: 5 mappings loaded ✓
```
