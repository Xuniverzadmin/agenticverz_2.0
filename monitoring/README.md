# NOVA Monitoring Setup

Prometheus + Grafana local dev setup for NOVA Agent Manager.

## Quick Start

1. Start all services:
```bash
docker compose up -d prometheus grafana backend db
```

2. Verify Prometheus is ready:
```bash
curl -s http://127.0.0.1:9090/-/ready
```

3. Verify Grafana is up:
```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login
# Should return 200
```

4. Access Grafana:
   - URL: http://127.0.0.1:3000
   - Username: admin
   - Password: admin
   - Dashboard: NOVA > NOVA Basic Dashboard (auto-provisioned)

## Architecture

All services use `network_mode: host` to avoid DNS issues with systemd-resolved/Tailscale.

- **Backend**: `127.0.0.1:8000` - Exposes `/metrics` endpoint
- **Prometheus**: `127.0.0.1:9090` - Scrapes backend metrics
- **Grafana**: `127.0.0.1:3000` - Visualizes metrics

## Metrics Exported

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `nova_runs_total` | Counter | `status`, `planner` | Total runs (started/succeeded/failed) |
| `nova_runs_failed_total` | Counter | - | Total permanently failed runs |
| `nova_skill_attempts_total` | Counter | `skill` | Skill execution attempts |
| `nova_skill_duration_seconds` | Histogram | `skill` | Skill execution duration |
| `nova_worker_pool_size` | Gauge | - | Configured worker concurrency |

## Grafana Provisioning

Dashboards are auto-imported from:
- `monitoring/grafana/provisioning/dashboards/files/`

Datasources are configured in:
- `monitoring/grafana/provisioning/datasources/datasource.yaml`

## Alertmanager

Alert rules are defined in `monitoring/rules/nova_alerts.yml`. Current alerts:
- **HighRunFailureRate**: >10% failure rate over 5 minutes
- **CriticalRunFailureRate**: >30% failure rate (critical)
- **NoRunsProcessed**: No runs in 15 minutes
- **SlowSkillExecution**: 95th percentile >30s
- **WorkerPoolDown**: Worker pool size is 0
- **BackendDown**: Backend not responding

Alertmanager config: `monitoring/alertmanager/config.yml`

Access Alertmanager: http://127.0.0.1:9093

## Security

All services bind to `127.0.0.1` only. Access via:
- SSH tunnel
- Tailscale
- VPN

Do NOT expose these ports to the public internet.
