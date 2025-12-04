# AOS Grafana Dashboards

Operational dashboards for AOS (Agentic Operating System).

## Dashboards

| Dashboard | File | Description |
|-----------|------|-------------|
| AOS Overview | `aos_overview.json` | High-level system health: run rates, worker pool, failure rates, skill duration |
| LLM Spend | `llm_spend.json` | Cost tracking: total spend, per-model costs, token usage, latency |
| Determinism & Replay | `determinism_replay.json` | Replay test results, determinism violations, golden file matches |

## Import Instructions

### Via Grafana UI

1. Open Grafana at http://localhost:3000
2. Go to **Dashboards** > **Import**
3. Upload JSON file or paste contents
4. Select Prometheus datasource
5. Click **Import**

### Via Provisioning

Add to `grafana/provisioning/dashboards/`:

```yaml
apiVersion: 1

providers:
  - name: 'AOS'
    orgId: 1
    folder: 'AOS'
    type: file
    options:
      path: /var/lib/grafana/dashboards/aos
```

Then copy JSON files to `/var/lib/grafana/dashboards/aos/`.

## Required Prometheus Metrics

These dashboards expect the following metrics from the AOS backend:

### Run Metrics
- `nova_runs_total` - Total runs counter
- `nova_runs_failed_total` - Failed runs counter
- `nova_worker_pool_size` - Current worker pool size

### Skill Metrics
- `nova_skill_attempts_total{skill, status}` - Skill execution attempts
- `nova_skill_duration_seconds_bucket` - Skill duration histogram

### LLM Metrics
- `nova_llm_invocations_total{provider, model, status}` - LLM invocation counter
- `nova_llm_cost_cents_total{provider, model}` - Cost in cents
- `nova_llm_tokens_total{provider, model, type}` - Token usage
- `nova_llm_duration_seconds_bucket{provider, model}` - LLM latency histogram

### Determinism Metrics
- `nova_replay_tests_total{status}` - Replay test results
- `nova_determinism_violations_total{skill, violation_type}` - Determinism violations
- `nova_golden_file_matches_total{skill, test}` - Golden file match results

## Alerting

Dashboard thresholds:
- **Failure Rate**: Yellow > 80%, Red > 95%
- **LLM Spend (24h)**: Yellow > $50, Red > $100
- **Replay Pass Rate**: Yellow < 95%, Red < 100%
- **Determinism Violations**: Any violation triggers red
