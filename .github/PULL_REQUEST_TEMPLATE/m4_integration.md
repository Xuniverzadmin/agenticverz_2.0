## M4.5 Failure Catalog & Cost Simulator Integration

### Summary

This PR adds the failure catalog and cost simulator infrastructure for M4.5/M5, **feature-flagged and NOT wired to runtime**.

**Components:**
- `FailureCatalog`: 54 error codes (1:1 with `WorkflowErrorCode` enum)
- `CostSimulator`: Pre-execution budget/feasibility checker
- Feature flags (all default `false`)
- Preflight/rollback scripts
- CI validation job

### Changes

| File | Purpose |
|------|---------|
| `backend/app/data/failure_catalog.json` | 54 error codes, 11 categories, 10 recovery modes |
| `backend/app/runtime/failure_catalog.py` | FailureCatalog class with matcher |
| `backend/app/worker/simulate.py` | CostSimulator class |
| `backend/app/config/feature_flags.json` | Runtime feature toggles |
| `backend/app/config/__init__.py` | Flag accessor module |
| `backend/tests/test_failure_catalog.py` | 26 tests |
| `backend/tests/test_cost_simulator.py` | 22 tests |
| `scripts/preflight_m4_signoff.sh` | M4 signoff gate |
| `scripts/rollback_failure_catalog.sh` | Rollback procedure |
| `scripts/ci/check_catalog_metrics.py` | Metric label validator |
| `.github/workflows/m4-ci.yml` | M4.5 validation job |
| `docs/runbooks/m4-safety-failure-catalog.md` | Deployment runbook |

### Test Results

```
tests/test_failure_catalog.py: 26 passed
tests/test_cost_simulator.py: 22 passed
Total: 48 passed
```

---

## ⚠️ SIGNOFF CHECKLIST (DO NOT MERGE UNTIL ALL COMPLETE)

### Pre-Merge Gates

- [ ] **24h shadow run complete with 0 mismatches**
  - Shadow run dir: `/tmp/shadow_simulation_YYYYMMDD_HHMMSS`
  - Cycles required: 2,880+ (24h @ 30s interval)
  - Mismatch count: **must be 0**
  - Attach: `shadow_run_report.txt`

- [ ] **CI full test pass**
  - M4 CI workflow green
  - M4.5 validation job green
  - All 48 new tests passing

- [ ] **Catalog/enum 1:1 mapping verified**
  ```bash
  PYTHONPATH=backend python3 -c "
  import json
  from app.workflow.errors import WorkflowErrorCode
  catalog = json.load(open('backend/app/data/failure_catalog.json'))
  assert set(catalog['errors'].keys()) == set(c.value for c in WorkflowErrorCode)
  print('✓ 1:1 mapping verified')
  "
  ```

- [ ] **Metric labels validated**
  ```bash
  python3 scripts/ci/check_catalog_metrics.py
  ```
  Attach: `metrics_labels_validation.txt`

- [ ] **Rollback script tested on staging**
  ```bash
  bash scripts/rollback_failure_catalog.sh --dry-run --force
  ```
  Attach: `rollback_dryrun.txt`

- [ ] **Feature flags default to false verified**
  ```bash
  python3 -c "
  import json
  flags = json.load(open('backend/app/config/feature_flags.json'))
  for name, cfg in flags['flags'].items():
      assert not cfg['enabled'], f'{name} should be false'
  print('✓ All flags default false')
  "
  ```

### Artifacts Required

| Artifact | Status |
|----------|--------|
| Shadow run report (24h, 0 mismatches) | ⬜ Pending |
| Metric labels validation output | ⬜ Pending |
| Rollback dry-run output | ⬜ Pending |
| CI workflow run URL | ⬜ Pending |

### Approvals Required

- [ ] **SRE Lead** (`@sre-lead`)
- [ ] **QA Lead** (`@qa-lead`)
- [ ] **Platform Architect** (`@platform-arch`)

---

## Post-Merge: Canary Enablement Plan

**DO NOT enable feature flags until all staging validation complete.**

### Staging Canary (after merge)

1. Enable flag in staging only:
   ```bash
   jq '.environments.staging.failure_catalog_runtime_integration = true' \
     backend/app/config/feature_flags.json > tmp && mv tmp backend/app/config/feature_flags.json
   ```

2. Deploy to staging, monitor 30m:
   - `/healthz` returns 200
   - `nova_workflow_error_total` stable
   - `nova_golden_mismatch_total` = 0

3. Run targeted golden replays:
   ```bash
   PYTHONPATH=backend python3 -m pytest tests/workflow/test_golden_lifecycle.py -v
   ```

4. If stable 24h → proceed to production canary (1% traffic)

### Rollback Trigger

Execute rollback if ANY of:
- `nova_golden_mismatch_total` increases
- Error rate delta > 10%
- `/healthz` fails
- Any P0/P1 incident

```bash
bash scripts/rollback_failure_catalog.sh --force
```

---

## Related

- Runbook: `docs/runbooks/m4-safety-failure-catalog.md`
- Shadow run script: `scripts/stress/run_shadow_simulation.sh`
- Feature flags spec: `backend/app/config/feature_flags.json`
