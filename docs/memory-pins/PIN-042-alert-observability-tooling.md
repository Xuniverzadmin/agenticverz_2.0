# PIN-042: Alert & Observability Tooling

**Status:** COMPLETE
**Created:** 2025-12-06
**Category:** Operations / Observability
**Exclusivity:** Authoritative tooling for alert injection, SLO mapping, and E2E parsing

---

## Overview

Collection of CLI tools for testing and validating the AOS observability pipeline. These are the authoritative implementations - do not create duplicates.

---

## Tools

### 1. Synthetic Alert Injector

**File:** `tools/inject_synthetic_alert.py`

Injects test alerts into Alertmanager to verify the alerting pipeline.

```bash
# Inject cost overrun alert
python3 tools/inject_synthetic_alert.py --type cost_overrun --tenant acme

# Inject critical replay mismatch
python3 tools/inject_synthetic_alert.py --type replay_mismatch --severity critical

# List active alerts
python3 tools/inject_synthetic_alert.py --list

# Dry run (preview payload)
python3 tools/inject_synthetic_alert.py --type worker_unhealthy --dry-run

# Resolve an alert
python3 tools/inject_synthetic_alert.py --resolve --fingerprint abc123
```

**Alert Types:**
| Type | Alertname | Default Severity |
|------|-----------|------------------|
| cost_overrun | AOSCostOverrun | warning |
| rate_limit_breach | AOSRateLimitBreach | warning |
| replay_mismatch | AOSReplayMismatch | warning |
| worker_unhealthy | AOSWorkerUnhealthy | warning |
| custom | AOSCustomAlert | warning |

**Configuration:**
```bash
ALERTMANAGER_URL=http://localhost:9093
```

---

### 2. k6 SLO Mapper

**File:** `tools/k6_slo_mapper.py`

Maps k6 load test results to SLO compliance status.

```bash
# Basic compliance check
python3 tools/k6_slo_mapper.py load-tests/results/k6_results.json

# Strict mode (exit 1 on breach)
python3 tools/k6_slo_mapper.py results.json --strict

# Critical-only (ignore warnings)
python3 tools/k6_slo_mapper.py results.json --strict --critical-only

# JSON output for CI
python3 tools/k6_slo_mapper.py results.json --json

# Save report
python3 tools/k6_slo_mapper.py results.json --output slo_report.json
```

**SLO Definitions:**
| SLO | Threshold | Severity |
|-----|-----------|----------|
| p95 latency | < 500ms | critical |
| p99 latency | < 1000ms | warning |
| Error rate | < 1% | critical |
| Availability | > 99.5% | critical |
| Parity failures | < 0.1% | warning |

**Output Example:**
```
SLO Results:
  ✓ PASS p95 latency for /simulate endpoint
       Value: 245.00ms (threshold: < 500ms)
  ✗ FAIL [CRITICAL] Overall error rate
       Value: 2.50% (threshold: < 1%)
```

---

### 3. E2E Results Parser

**File:** `tools/e2e_results_parser.py`

Parses E2E test results and generates summary reports.

```bash
# Text summary
python3 tools/e2e_results_parser.py pytest_results.json

# Markdown report
python3 tools/e2e_results_parser.py results.json --output-format markdown

# JUnit XML input
python3 tools/e2e_results_parser.py results.xml

# GitHub Actions summary
python3 tools/e2e_results_parser.py results.json --github-summary

# Strict mode (exit 1 on failures)
python3 tools/e2e_results_parser.py results.json --strict
```

**Supported Formats:**
| Format | Extension | Auto-detected |
|--------|-----------|---------------|
| pytest-json | .json | Yes |
| JUnit XML | .xml | Yes |
| AOS Harness | .json | Yes |

**Output Fields:**
- Total/Passed/Failed/Skipped counts
- Pass rate percentage
- Failed tests list with messages
- Slowest tests
- Results by module
- Parity check summary (AOS harness)

---

## CI Integration

### k6 SLO in GitHub Actions

```yaml
- name: Run k6 load test
  run: k6 run load-tests/simulate_k6.js --out json=results.json

- name: Check SLO compliance
  run: python3 tools/k6_slo_mapper.py results.json --strict
```

### E2E in GitHub Actions

```yaml
- name: Run E2E tests
  run: pytest tests/e2e/ --json-report --json-report-file=results.json

- name: Parse results
  run: python3 tools/e2e_results_parser.py results.json --github-summary --strict
```

---

## Exclusivity Notes

These are the **authoritative** CLI tools for:
- Alert pipeline testing → `inject_synthetic_alert.py`
- Load test SLO mapping → `k6_slo_mapper.py`
- E2E result parsing → `e2e_results_parser.py`

Do not create alternative implementations. If new functionality is needed, extend these tools.

---

## Dependencies

```bash
pip install requests  # Alert injector
# No external deps for SLO mapper and E2E parser (stdlib only)
```

---

## Related

- PIN-037: Grafana Cloud Integration
- PIN-039: M8 Implementation Progress (parent)
- PIN-017: M4 Monitoring Infrastructure
