# Runbook: M4 Safety - Failure Catalog Integration

**Version:** 1.0.0
**Created:** 2025-12-03
**Owner:** Platform Team
**Status:** Pre-Integration (Feature Flagged)

---

## Overview

This runbook covers the safe deployment and rollback of the Failure Catalog integration (M4.5) and Cost Simulator integration (M5).

### Components

| Component | Path | Purpose |
|-----------|------|---------|
| Failure Catalog JSON | `backend/app/data/failure_catalog.json` | 54 error codes with recovery strategies |
| FailureCatalog Class | `backend/app/runtime/failure_catalog.py` | Offline matcher for error lookup |
| Cost Simulator | `backend/app/worker/simulate.py` | Pre-execution cost/feasibility check |
| Feature Flags | `backend/app/config/feature_flags.json` | Runtime toggles for integration |

---

## Pre-Integration Checklist

Before enabling integration:

- [ ] 24h shadow run completed with **0 mismatches**
- [ ] All unit tests passing (48+ tests)
- [ ] CI green for at least 1 full nightly run
- [ ] Preflight script passes: `./scripts/preflight_m4_signoff.sh`
- [ ] SRE approval obtained
- [ ] Rollback script tested on staging

---

## Feature Flags

### Flag Definitions

| Flag | Default | Purpose |
|------|---------|---------|
| `failure_catalog_runtime_integration` | `false` | Wire FailureCatalog to error classification |
| `cost_simulator_runtime_integration` | `false` | Wire CostSimulator to runtime.simulate() |

### Checking Flag Status

```bash
PYTHONPATH=backend python3 -c "
from app.config import is_flag_enabled
print('failure_catalog:', is_flag_enabled('failure_catalog_runtime_integration'))
print('cost_simulator:', is_flag_enabled('cost_simulator_runtime_integration'))
"
```

### Enabling Flags

Edit `backend/app/config/feature_flags.json`:

```json
{
  "flags": {
    "failure_catalog_runtime_integration": {
      "enabled": true,
      ...
    }
  }
}
```

Or via environment override:

```bash
export AOS_FEATURE_FAILURE_CATALOG=true
```

---

## Deployment Steps

### 1. Pre-Deployment Verification

```bash
# Verify M4 signoff
./scripts/preflight_m4_signoff.sh

# Run tests
cd backend
PYTHONPATH=. python3 -m pytest tests/test_failure_catalog.py tests/test_cost_simulator.py -v

# Check catalog-enum alignment
PYTHONPATH=. python3 -c "
from app.runtime.failure_catalog import FailureCatalog
from app.workflow.errors import WorkflowErrorCode
c = FailureCatalog()
enum_codes = set(code.value for code in WorkflowErrorCode)
catalog_codes = set(c.list_codes())
assert enum_codes == catalog_codes, 'Mismatch!'
print('Catalog alignment OK')
"
```

### 2. Canary Deployment (Staging)

1. Enable flag in staging environment only:
   ```json
   "environments": {
     "staging": {
       "failure_catalog_runtime_integration": true
     }
   }
   ```

2. Deploy to staging:
   ```bash
   docker compose -f docker-compose.staging.yml up -d backend
   ```

3. Monitor for 30 minutes:
   - Check `/metrics` for error rate changes
   - Verify `/healthz` returns 200
   - Check golden replay mismatch rate

### 3. Production Deployment

1. Enable flag in production:
   ```json
   "environments": {
     "production": {
       "failure_catalog_runtime_integration": true
     }
   }
   ```

2. Deploy:
   ```bash
   docker compose up -d backend worker
   ```

3. Monitor:
   - Grafana dashboard: `AOS / Error Rates`
   - Alert: `nova_workflow_error_total` rate increase

---

## Rollback Procedure

### Automated Rollback

```bash
./scripts/rollback_failure_catalog.sh
```

This will:
1. Disable feature flags
2. Restart services
3. Run smoke tests
4. Verify rollback success

### Manual Rollback

1. **Disable flags immediately:**
   ```bash
   # Edit feature_flags.json
   vim backend/app/config/feature_flags.json
   # Set enabled: false for both flags
   ```

2. **Restart services:**
   ```bash
   docker compose restart backend worker
   # or
   sudo systemctl restart nova-api nova-worker
   ```

3. **Verify health:**
   ```bash
   curl -s http://127.0.0.1:8000/healthz | jq .
   curl -s http://127.0.0.1:8000/metrics | grep nova_
   ```

4. **Check for errors:**
   ```bash
   docker compose logs backend --tail 100 | grep -i error
   ```

### Git Revert (Last Resort)

If flags don't resolve the issue:

```bash
# Find the integration commit
git log --oneline -10

# Revert it
git revert <commit-sha>
git push origin develop

# Redeploy
docker compose up -d --build backend
```

---

## Monitoring & Alerts

### Key Metrics to Watch

| Metric | Expected | Alert Threshold |
|--------|----------|-----------------|
| `nova_workflow_error_total` | Stable | >20% increase |
| `nova_workflow_step_duration_seconds` | Stable | >50% increase |
| `nova_golden_mismatch_total` | 0 | Any increase |

### Grafana Queries

```promql
# Error rate by code
sum(rate(nova_workflow_error_total[5m])) by (error_code)

# Mismatch detection
increase(nova_golden_mismatch_total[1h])

# Recovery suggestion usage
sum(nova_error_recovery_suggestion_total) by (recovery_mode)
```

### Alert Rules (Alertmanager)

```yaml
- alert: FailureCatalogIntegrationError
  expr: increase(nova_workflow_error_total{error_code="UNKNOWN_ERROR"}[5m]) > 5
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Increased unknown errors after catalog integration"
    runbook: "https://docs/runbooks/m4-safety-failure-catalog.md"
```

---

## Troubleshooting

### Issue: Catalog not loading

**Symptom:** Errors about missing catalog file

**Check:**
```bash
ls -la backend/app/data/failure_catalog.json
```

**Fix:** Ensure file exists and is valid JSON:
```bash
python3 -m json.tool backend/app/data/failure_catalog.json > /dev/null && echo "Valid"
```

### Issue: Code mismatch between enum and catalog

**Symptom:** `KeyError` when looking up error codes

**Check:**
```bash
PYTHONPATH=backend python3 -c "
from app.runtime.failure_catalog import FailureCatalog
from app.workflow.errors import WorkflowErrorCode
c = FailureCatalog()
for code in WorkflowErrorCode:
    if code.value not in c.list_codes():
        print(f'Missing: {code.value}')
"
```

**Fix:** Add missing codes to `failure_catalog.json`

### Issue: Feature flag not taking effect

**Symptom:** Integration code not running despite flag enabled

**Check:**
```bash
PYTHONPATH=backend python3 -c "
from app.config import is_flag_enabled, get_environment
print(f'Environment: {get_environment()}')
print(f'Flag enabled: {is_flag_enabled(\"failure_catalog_runtime_integration\")}')
"
```

**Fix:** Verify correct environment and reload flags:
```python
from app.config import reload_flags
reload_flags()
```

---

## Contact

- **On-Call:** #platform-oncall
- **Escalation:** Platform Lead
- **Documentation:** This runbook

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-12-03 | Initial creation | Platform Team |
