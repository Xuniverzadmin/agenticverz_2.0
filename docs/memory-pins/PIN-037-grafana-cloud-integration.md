# PIN-037: Grafana Cloud Integration

**Created:** 2025-12-06
**Status:** ACTIVE
**Category:** Infrastructure / Observability

---

## Overview

AOS metrics and dashboards are hosted on Grafana Cloud, providing centralized observability without self-hosting overhead.

---

## Grafana Cloud Account

| Field | Value |
|-------|-------|
| **URL** | https://agenticverz.grafana.net |
| **Organization** | agenticverz |
| **Region** | ap-south-1 (Mumbai) |
| **Plan** | Free tier |

---

## Authentication

### Dashboard Access (Service Token)

| Field | Value |
|-------|-------|
| **Token Name** | aos-dashboards |
| **Scope** | Dashboard read/write |
| **Token** | `glsa_1t9wgBRb3qnmY6ZZyTjuKYi3S4Gm0h9D_0548c60a` |

**Usage:**
```bash
# Upload dashboard
curl -X POST https://agenticverz.grafana.net/api/dashboards/db \
  -H "Authorization: Bearer glsa_1t9wgBRb3qnmY6ZZyTjuKYi3S4Gm0h9D_0548c60a" \
  -H "Content-Type: application/json" \
  -d @dashboard.json
```

### Metrics API (Prometheus Remote Write)

| Field | Value |
|-------|-------|
| **Token Name** | agenticverz-metrics |
| **Scope** | metrics:read, metrics:write |
| **Username** | 2846553 |
| **Password/Token** | `glc_eyJvIjoiMTYxMDE5MiIsIm4iOiJhZ2VudGljdmVyei1tZXRyaWNzLWFnZW50aWN2ZXJ6LW1ldHJpY3MiLCJrIjoiMDF6UGMwR3NKSHEwamVvOUkxNjQxemc2IiwibSI6eyJyIjoicHJvZC1hcC1zb3V0aC0xIn19` |

**Prometheus Remote Write URL:**
```
https://prometheus-prod-43-prod-ap-south-1.grafana.net/api/prom/push
```

---

## Prometheus Configuration

**File:** `/root/agenticverz2.0/monitoring/prometheus.yml`

```yaml
remote_write:
  - url: https://prometheus-prod-43-prod-ap-south-1.grafana.net/api/prom/push
    basic_auth:
      username: "2846553"
      password: "glc_eyJvIjoiMTYxMDE5MiIsIm4iOiJhZ2VudGljdmVyei1tZXRyaWNzLWFnZW50aWN2ZXJ6LW1ldHJpY3MiLCJrIjoiMDF6UGMwR3NKSHEwamVvOUkxNjQxemc2IiwibSI6eyJyIjoicHJvZC1hcC1zb3V0aC0xIn19"
    write_relabel_configs:
      # Only send AOS-related metrics to reduce cardinality
      - source_labels: [__name__]
        regex: "aos_.*|nova_.*|rbac_.*|process_.*|python_.*|up"
        action: keep
```

**Metric filtering:** Only AOS-prefixed metrics are sent to Grafana Cloud to stay within free tier limits.

---

## Dashboards

### AOS Traces Dashboard (v2)

| Field | Value |
|-------|-------|
| **URL** | https://agenticverz.grafana.net/d/aos-traces-v2/aos-traces-and-determinism-v2 |
| **UID** | aos-traces-v2 |
| **File** | `/root/agenticverz2.0/monitoring/grafana/aos_traces_dashboard_v2.json` |

**Panels (11):**
1. Traces Simulated (rate)
2. Traces Stored (rate)
3. Request Latency (p95/p50)
4. Replay Mismatches (rate) - with alert
5. Trace Store p95 Latency - with alert
6. Parity Status (gauge) - with alert
7. Idempotency Results (pie chart)
8. Replay Enforcement by Behavior (pie chart)
9. Parity Failures (24h)
10. Trace Size Distribution
11. Steps Per Trace

**Built-in Alerts:**
- High Replay Mismatch Rate (>0.1/s for 2m)
- Trace Store Latency High (>0.75s p95 for 5m)
- Parity Check Failure (any failure for 1m)

### AOS Traces Dashboard (v1)

| Field | Value |
|-------|-------|
| **URL** | https://agenticverz.grafana.net/d/aos-traces-m8/aos-traces-dashboard |
| **UID** | aos-traces-m8 |
| **File** | `/root/agenticverz2.0/monitoring/grafana/aos_traces_dashboard.json` |

---

## Datasource

| Field | Value |
|-------|-------|
| **Name** | grafanacloud-prom |
| **Type** | Prometheus |
| **UID** | grafanacloud-prom |

All dashboard panels use this datasource UID.

---

## Alerting (Slack Integration)

Grafana Cloud alerts route to Slack:

| Field | Value |
|-------|-------|
| **Channel** | #test-1-aos |
| **Webhook** | Configured in Grafana Cloud contact points |

---

## Operations

### Upload/Update Dashboard

```bash
# Read dashboard JSON
cat /root/agenticverz2.0/monitoring/grafana/aos_traces_dashboard_v2.json | \
  jq '{dashboard: ., overwrite: true}' | \
  curl -X POST https://agenticverz.grafana.net/api/dashboards/db \
    -H "Authorization: Bearer glsa_1t9wgBRb3qnmY6ZZyTjuKYi3S4Gm0h9D_0548c60a" \
    -H "Content-Type: application/json" \
    -d @-
```

### Verify Metrics Flowing

```bash
# Query a metric
curl -s "https://agenticverz.grafana.net/api/datasources/proxy/uid/grafanacloud-prom/api/v1/query?query=up" \
  -H "Authorization: Bearer glsa_1t9wgBRb3qnmY6ZZyTjuKYi3S4Gm0h9D_0548c60a" | jq
```

### Restart Prometheus (after config change)

```bash
docker compose restart prometheus
```

---

## Free Tier Limits

| Resource | Limit | Current Usage |
|----------|-------|---------------|
| Metrics | 10,000 series | ~50 series (filtered) |
| Logs | 50GB/month | Not used |
| Traces | 50GB/month | Not used |
| Dashboards | Unlimited | 2 |
| Alerts | Unlimited | 3 |

**Cost:** $0 (free tier sufficient for current usage)

---

## Troubleshooting

### Metrics not appearing

1. Check Prometheus logs: `docker logs nova_prometheus 2>&1 | tail -20`
2. Verify remote_write config has correct credentials
3. Check metric filter regex allows the metric name
4. Verify Prometheus can reach Grafana Cloud: `curl -I https://prometheus-prod-43-prod-ap-south-1.grafana.net`

### Dashboard upload fails

1. Verify service token has dashboard write scope
2. Check JSON is valid: `jq . dashboard.json`
3. Ensure `overwrite: true` is set for updates

---

## Related PINs

- PIN-017: M4 Monitoring Infrastructure (local Prometheus/Grafana)
- PIN-038: Upstash Redis Integration
- PIN-036: Infrastructure Pending Items
