# AOS Canary Playbook

## Purpose

Run controlled feature flag enablement with automated smoke testing, Prometheus metric monitoring, and automatic rollback on threshold breach.

## Quick Start

```bash
# Dry-run (no changes made)
python scripts/ops/canary/canary_runner.py \
  --config scripts/ops/canary/configs/m4_canary.yaml \
  --dry-run

# Real run with 5-minute watch window
python scripts/ops/canary/canary_runner.py \
  --config scripts/ops/canary/configs/m4_canary.yaml \
  --watch 300
```

## Prerequisites

1. **Shadow run complete**: `.m4_signoff` must exist for flags that require it
2. **Services healthy**: `nova_agent_manager`, `nova_worker`, `nova_prometheus` running
3. **PyYAML installed**: `pip install pyyaml`

```bash
# Verify prerequisites
docker ps | grep nova
ls -la .m4_signoff
python3 -c "import yaml; print('PyYAML OK')"
```

## Workflow Steps

### 1. Pre-Canary Checks

```bash
# Verify current flag status
cat backend/app/config/feature_flags.json | jq '.flags | to_entries[] | "\(.key): \(.value.enabled)"'

# Verify shadow run status
python3 -c "
import json, glob
reports = sorted(glob.glob('/tmp/shadow_simulation_*/reports/cycle_*.json'))
if reports:
    with open(reports[-1]) as f:
        data = json.load(f)
    print(f'Latest cycle: {len(reports)}, Mismatches: {data[\"shadow\"][\"mismatches\"]}')
"

# Check baseline metrics
curl -s 'http://127.0.0.1:9090/api/v1/query?query=sum(nova_golden_mismatch_total)' | jq '.data.result[0].value[1]'
```

### 2. Run Canary

```bash
# Option A: Single run (quick validation)
python scripts/ops/canary/canary_runner.py \
  --config scripts/ops/canary/configs/m4_canary.yaml

# Option B: Watch mode (recommended for production flags)
python scripts/ops/canary/canary_runner.py \
  --config scripts/ops/canary/configs/m4_canary.yaml \
  --watch 300 \
  --report scripts/ops/canary/reports/canary_$(date +%Y%m%d_%H%M%S).json
```

### 3. Interpret Results

**Success output:**
```
[INFO] ============================================================
[INFO]          CANARY PASSED
[INFO] ============================================================
```

**Failure output:**
```
[ERROR] ============================================================
[ERROR]          CANARY FAILED
[WARN]          Rollback reason: golden_mismatch increased: 0 -> 1
[INFO] ============================================================
```

### 4. Review Report

```bash
cat scripts/ops/canary/reports/latest_report.json | jq '{
  success: .success,
  rollback_triggered: .rollback_triggered,
  rollback_reason: .rollback_reason,
  smoke_returncode: .smoke_returncode,
  metrics_delta: .metrics_delta
}'
```

## Rollback Triggers

| Condition | Threshold | Action |
|-----------|-----------|--------|
| `golden_mismatch` increases | Any (>0) | **Immediate rollback** |
| `error_rate` delta | >50% | Rollback |
| `latency_p95` delta | >500ms | Rollback |
| Smoke test fails | exit !=0 | Rollback |
| Prometheus unavailable | N/A | Continue (warn) |

## Manual Rollback

If automatic rollback fails or you need to rollback manually:

```bash
# Option 1: Use rollback script
bash scripts/rollback_failure_catalog.sh --force

# Option 2: Manually disable flags
jq '.flags.failure_catalog_runtime_integration.enabled = false |
    .flags.cost_simulator_runtime_integration.enabled = false |
    .environments.staging.failure_catalog_runtime_integration = false |
    .environments.staging.cost_simulator_runtime_integration = false' \
  backend/app/config/feature_flags.json > tmp && mv tmp backend/app/config/feature_flags.json

# Option 3: Restart services to pick up changes
docker restart nova_agent_manager nova_worker
```

## Canary Configs

| Config | Purpose | Signoff Required |
|--------|---------|------------------|
| `m4_canary.yaml` | Full M4.5 catalog integration | Yes |
| `staging_soft_canary.yaml` | Soft capability enforcement | No |

## Thresholds Guidance

### Conservative (Production)
```yaml
thresholds:
  error_rate_delta_pct: 10.0
  latency_p95_delta_ms: 100.0
```

### Moderate (Staging)
```yaml
thresholds:
  error_rate_delta_pct: 50.0
  latency_p95_delta_ms: 500.0
```

### Permissive (Development)
```yaml
thresholds:
  error_rate_delta_pct: 100.0
  latency_p95_delta_ms: 1000.0
```

## Troubleshooting

### Smoke test timeout
```bash
# Increase timeout in config
smoke:
  timeout_seconds: 180

# Or run smoke test directly to debug
./scripts/ops/canary_smoke_test.sh --verbose
```

### Prometheus query errors
```bash
# Verify Prometheus is accessible
curl -s 'http://127.0.0.1:9090/api/v1/query?query=up'

# Check if nova metrics exist
curl -s 'http://127.0.0.1:9090/api/v1/label/__name__/values' | jq '.data | map(select(startswith("nova_")))'
```

### Flag toggle failures
```bash
# Check file permissions
ls -la backend/app/config/feature_flags.json

# Verify JSON is valid
python3 -c "import json; json.load(open('backend/app/config/feature_flags.json'))"
```

## Integration with CI

```yaml
# .github/workflows/canary.yml
name: Canary Deploy
on:
  workflow_dispatch:
    inputs:
      config:
        description: 'Canary config file'
        required: true
        default: 'scripts/ops/canary/configs/staging_soft_canary.yaml'
      watch_seconds:
        description: 'Watch duration'
        required: false
        default: '300'

jobs:
  canary:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Run Canary
        run: |
          python scripts/ops/canary/canary_runner.py \
            --config ${{ github.event.inputs.config }} \
            --watch ${{ github.event.inputs.watch_seconds }} \
            --report canary_report.json
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: canary-report
          path: canary_report.json
```

## Security Notes

- Never commit secrets to canary configs
- Feature flags are file-based (no external API)
- Reports may contain stdout/stderr - review before sharing
- Canary runner can toggle production flags - treat as privileged
