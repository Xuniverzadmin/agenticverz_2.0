# AOS Canary Runner

Automated feature flag canary deployment with smoke testing, Prometheus monitoring, and auto-rollback.

## Features

- **Atomic file operations**: Feature flag toggles use flock + temp-rename pattern (no partial writes)
- **Prometheus integration**: Range-based baseline averaging for stable comparisons
- **Smoke testing**: Runs configurable smoke scripts with timeout
- **Auto-rollback**: Reverts flags on threshold breach or smoke failure
- **Webhook alerting**: Slack/Discord/Teams notifications on rollback
- **Full provenance**: Reports include git SHA, branch, config hash, hostname, user

## Quick Start

```bash
# Install dependency
pip install pyyaml

# Dry-run (no changes)
python3 scripts/ops/canary/canary_runner.py \
  --config scripts/ops/canary/configs/m4_canary.yaml \
  --dry-run

# Real run with 5-minute watch
python3 scripts/ops/canary/canary_runner.py \
  --config scripts/ops/canary/configs/m4_canary.yaml \
  --watch 300

# For M4.5 flags, you need the signoff artifact first:
./scripts/ops/canary/generate_signoff.sh --check-only
```

## Files

```
scripts/ops/canary/
├── canary_runner.py          # Main runner script (atomic writes, provenance, alerting)
├── generate_signoff.sh       # Automated .m4_signoff generation with checks
├── CANARY_PLAYBOOK.md        # Operational playbook
├── README.md                 # This file
├── configs/
│   ├── m4_canary.yaml        # M4.5 failure catalog canary (requires signoff)
│   └── staging_soft_canary.yaml  # Soft capability enforcement (no signoff)
└── reports/
    └── latest_report.json    # Most recent canary report (with provenance)
```

## Usage

```
usage: canary_runner.py [-h] --config CONFIG [--report REPORT] [--dry-run]
                        [--watch SECONDS]

AOS Canary Runner - Feature flag, smoke test, metrics monitoring

options:
  -h, --help        show this help message and exit
  --config CONFIG   Path to canary config (YAML/JSON)
  --report REPORT   Output report path
  --dry-run         Show what would happen without changes
  --watch SECONDS   Watch metrics for N seconds after smoke test
```

## Config Format

```yaml
name: my-canary
environment: staging

feature_flags:
  - my_feature_flag

smoke:
  script: ./scripts/ops/canary_smoke_test.sh
  timeout_seconds: 60

prometheus:
  url: http://127.0.0.1:9090
  baseline_window_seconds: 300  # 5 min avg for stable comparison
  metrics:
    error_rate: sum(rate(nova_workflow_error_total[1m])) or vector(0)
    golden_mismatch: sum(nova_golden_mismatch_total) or vector(0)

thresholds:
  error_rate_delta_pct: 50.0
  latency_p95_delta_ms: 500.0

alerting:
  webhook_url: ""  # Or set CANARY_WEBHOOK_URL env var
```

## Signoff Generation

For flags with `requires_m4_signoff: true`, use the signoff script:

```bash
# Check if conditions are met (doesn't generate)
./scripts/ops/canary/generate_signoff.sh --check-only

# Generate signoff after shadow run completes
./scripts/ops/canary/generate_signoff.sh

# Force mode for CI (skips shadow run check)
./scripts/ops/canary/generate_signoff.sh --force
```

## Exit Codes

- `0`: Canary passed
- `1`: Canary failed (rollback may have been triggered)

## Report Provenance

Every report includes audit trail fields:

```json
{
  "git_sha": "efec21239e4c",
  "git_branch": "feature/m4.5-failure-catalog-integration",
  "config_hash": "f2a08a6528283bb3",
  "hostname": "vmi2788299",
  "user": "root",
  "baseline_window_seconds": 300
}
```

## See Also

- [CANARY_PLAYBOOK.md](./CANARY_PLAYBOOK.md) - Full operational playbook
- [canary_smoke_test.sh](../canary_smoke_test.sh) - Default smoke test script
- [rollback_failure_catalog.sh](../../rollback_failure_catalog.sh) - Rollback script
