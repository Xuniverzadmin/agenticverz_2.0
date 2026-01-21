# SDK Attribution Alerts — Monitoring & Incident Response

**Status:** READY FOR IMPLEMENTATION
**Effective:** Post Phase-3 Rollout
**Reference:** SDK_ATTRIBUTION_ENFORCEMENT.md, ATTRIBUTION_ARCHITECTURE.md

---

## Purpose

This document defines **metrics, alert thresholds, and incident response procedures** for attribution enforcement monitoring. These signals ensure violations are detected, rollout is safe, and enforcement is auditable.

---

## 1. Prometheus Metrics (Canonical)

### SDK-Side Metrics

Emit from SDK before/during validation:

```python
# Python metric definitions (use prometheus_client or equivalent)

# Counter: Total attribution validation attempts
sdk_attribution_validations_total = Counter(
    "sdk_attribution_validations_total",
    "Total attribution validation attempts",
    labelnames=["enforcement_mode", "sdk_version", "origin_system"]
)

# Counter: Validation failures by error code
sdk_attribution_errors_total = Counter(
    "sdk_attribution_errors_total",
    "Attribution validation errors",
    labelnames=["error_code", "enforcement_mode", "origin_system"]
)

# Counter: Runs rejected due to attribution failure
sdk_attribution_rejects_total = Counter(
    "sdk_attribution_rejects_total",
    "Runs rejected by attribution enforcement",
    labelnames=["error_code", "origin_system"]
)

# Counter: Legacy override usage (soft mode only)
sdk_attribution_overrides_total = Counter(
    "sdk_attribution_overrides_total",
    "Legacy override flag usage in soft mode",
    labelnames=["origin_system", "agent_id"]
)

# Histogram: Validation latency (should be <1ms)
sdk_attribution_validation_duration_seconds = Histogram(
    "sdk_attribution_validation_duration_seconds",
    "Time spent validating attribution",
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01]
)
```

### Backend-Side Metrics

Emit from backend as defense-in-depth:

```python
# Counter: Runs created with legacy markers after enforcement date
runs_with_legacy_attribution_total = Counter(
    "runs_with_legacy_attribution_total",
    "Runs created with legacy-unknown attribution after enforcement",
    labelnames=["field", "origin_system"]
)

# Gauge: Current legacy bucket size (should be stable/shrinking)
runs_legacy_bucket_size = Gauge(
    "runs_legacy_bucket_size",
    "Total count of runs with legacy-unknown attribution"
)

# Counter: DB constraint violations (CHECK constraint failures)
runs_attribution_constraint_violations_total = Counter(
    "runs_attribution_constraint_violations_total",
    "Attribution CHECK constraint violations at DB level",
    labelnames=["constraint_name"]
)
```

---

## 2. Alert Rules (Prometheus/Alertmanager)

### Critical Alerts (Page Immediately)

```yaml
# alerting_rules.yml

groups:
  - name: attribution_enforcement
    rules:

      # ═══════════════════════════════════════════════════════════════════════
      # CRITICAL: Legacy bucket growing after enforcement (T₀)
      # This should NEVER happen after Phase 3 is complete
      # ═══════════════════════════════════════════════════════════════════════
      - alert: AttributionEnforcementBreach
        expr: |
          increase(runs_with_legacy_attribution_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "New runs entering legacy bucket after enforcement"
          description: |
            {{ $value }} runs were created with legacy attribution markers
            in the last 5 minutes. This indicates an enforcement bypass.

            Origin system: {{ $labels.origin_system }}
            Field: {{ $labels.field }}

            ACTION REQUIRED:
            1. Identify the producer (check origin_system label)
            2. Block or fix the producer immediately
            3. File incident for root cause analysis
          runbook_url: "https://docs.internal/runbooks/attribution-breach"

      # ═══════════════════════════════════════════════════════════════════════
      # CRITICAL: DB constraint violation
      # SDK bypass detected - someone is writing directly to DB
      # ═══════════════════════════════════════════════════════════════════════
      - alert: AttributionConstraintViolation
        expr: |
          increase(runs_attribution_constraint_violations_total[5m]) > 0
        for: 0m  # Immediate
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "DB-level attribution constraint violation"
          description: |
            A write attempted to bypass SDK validation and was blocked
            by database CHECK constraint.

            Constraint: {{ $labels.constraint_name }}

            ACTION REQUIRED:
            1. Check for rogue writers (direct DB access)
            2. Review SDK bypass attempts
            3. Consider revoking direct DB access
          runbook_url: "https://docs.internal/runbooks/db-constraint-violation"
```

### Warning Alerts (Investigate Soon)

```yaml
      # ═══════════════════════════════════════════════════════════════════════
      # WARNING: High rejection rate during rollout
      # Indicates SDK consumers not updated
      # ═══════════════════════════════════════════════════════════════════════
      - alert: AttributionRejectionRateHigh
        expr: |
          sum(rate(sdk_attribution_rejects_total[5m]))
          /
          sum(rate(sdk_attribution_validations_total[5m]))
          > 0.05
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Attribution rejection rate > 5%"
          description: |
            {{ $value | humanizePercentage }} of run creation attempts
            are being rejected due to attribution failures.

            Top error codes:
            {{ range query "topk(3, sum by (error_code) (rate(sdk_attribution_errors_total[5m])))" }}
              - {{ .Labels.error_code }}: {{ .Value | humanize }}
            {{ end }}

            This may indicate:
            - SDK consumers need updates
            - Rollout communication incomplete
            - Legitimate integration issues
          runbook_url: "https://docs.internal/runbooks/high-rejection-rate"

      # ═══════════════════════════════════════════════════════════════════════
      # WARNING: Override flag usage (soft mode only)
      # Should trend toward zero
      # ═══════════════════════════════════════════════════════════════════════
      - alert: AttributionOverrideUsage
        expr: |
          increase(sdk_attribution_overrides_total[1h]) > 10
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Legacy override flag being used"
          description: |
            {{ $value }} uses of AOS_ALLOW_ATTRIBUTION_LEGACY=true
            in the last hour.

            Origin systems using override:
            {{ range query "topk(5, sum by (origin_system) (increase(sdk_attribution_overrides_total[1h])))" }}
              - {{ .Labels.origin_system }}: {{ .Value | humanize }}
            {{ end }}

            ACTION: Contact these teams to complete migration.
          runbook_url: "https://docs.internal/runbooks/legacy-override"

      # ═══════════════════════════════════════════════════════════════════════
      # WARNING: Shadow mode finding violations
      # Pre-enforcement signal - fix before going hard
      # ═══════════════════════════════════════════════════════════════════════
      - alert: AttributionShadowViolations
        expr: |
          increase(sdk_attribution_errors_total{enforcement_mode="shadow"}[1h]) > 100
        for: 15m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Attribution violations detected in shadow mode"
          description: |
            {{ $value }} attribution violations logged in shadow mode.

            These would be REJECTED in hard enforcement mode.

            Top error codes:
            {{ range query "topk(3, sum by (error_code) (increase(sdk_attribution_errors_total{enforcement_mode='shadow'}[1h])))" }}
              - {{ .Labels.error_code }}: {{ .Value | humanize }}
            {{ end }}

            ACTION: Fix violations before enabling hard enforcement.
          runbook_url: "https://docs.internal/runbooks/shadow-violations"
```

### Info Alerts (Dashboard Only)

```yaml
      # ═══════════════════════════════════════════════════════════════════════
      # INFO: Enforcement mode tracking
      # ═══════════════════════════════════════════════════════════════════════
      - alert: AttributionEnforcementModeInfo
        expr: |
          count by (enforcement_mode) (
            sdk_attribution_validations_total
          ) > 0
        labels:
          severity: info
          team: platform
        annotations:
          summary: "SDK enforcement modes in use"
          description: |
            Current enforcement modes:
            {{ range query "count by (enforcement_mode) (sdk_attribution_validations_total)" }}
              - {{ .Labels.enforcement_mode }}: active
            {{ end }}
```

---

## 3. Thresholds by Rollout Phase

### Shadow Mode (Step 1)

| Metric | Threshold | Action |
|--------|-----------|--------|
| `sdk_attribution_errors_total{enforcement_mode="shadow"}` | > 100/hour | Investigate producers |
| Any error code | > 10% of total | Prioritize that error type |
| Validation latency p99 | > 5ms | Investigate SDK performance |

**Success Criteria for Moving to Soft Fail:**
- All producers identified
- Error rate < 1% of validations
- No unexplained violations

### Soft Fail Mode (Step 2)

| Metric | Threshold | Action |
|--------|-----------|--------|
| `sdk_attribution_rejects_total` | > 5% of attempts | Contact producers |
| `sdk_attribution_overrides_total` | > 0 after 7 days | Escalate to team leads |
| Override usage by single origin | > 50/day | Block that system |

**Success Criteria for Moving to Hard Fail:**
- Override usage at zero
- Rejection rate < 0.1%
- No new violations for 72 hours

### Hard Fail Mode (Step 3)

| Metric | Threshold | Action |
|--------|-----------|--------|
| `runs_with_legacy_attribution_total` | > 0 | **PAGE IMMEDIATELY** |
| `sdk_attribution_rejects_total` | > 0.1% | Warning, investigate |
| `runs_attribution_constraint_violations_total` | > 0 | **PAGE IMMEDIATELY** |

**Steady State Criteria:**
- Legacy bucket size stable (no growth)
- Rejection rate < 0.01%
- Zero constraint violations

---

## 4. Grafana Dashboard Panels

### Row 1: Enforcement Health

```json
{
  "title": "Attribution Enforcement Overview",
  "panels": [
    {
      "title": "Enforcement Mode Distribution",
      "type": "piechart",
      "targets": [
        {
          "expr": "sum by (enforcement_mode) (sdk_attribution_validations_total)"
        }
      ]
    },
    {
      "title": "Validation Success Rate",
      "type": "stat",
      "targets": [
        {
          "expr": "1 - (sum(rate(sdk_attribution_errors_total[5m])) / sum(rate(sdk_attribution_validations_total[5m])))"
        }
      ],
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "red", "value": 0},
          {"color": "yellow", "value": 0.95},
          {"color": "green", "value": 0.99}
        ]
      }
    },
    {
      "title": "Legacy Bucket After T₀",
      "type": "stat",
      "targets": [
        {
          "expr": "increase(runs_with_legacy_attribution_total[24h])"
        }
      ],
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": 0},
          {"color": "red", "value": 1}
        ]
      }
    }
  ]
}
```

### Row 2: Error Breakdown

```json
{
  "title": "Attribution Errors",
  "panels": [
    {
      "title": "Errors by Code (Rate)",
      "type": "timeseries",
      "targets": [
        {
          "expr": "sum by (error_code) (rate(sdk_attribution_errors_total[5m]))",
          "legendFormat": "{{ error_code }}"
        }
      ]
    },
    {
      "title": "Top Violating Origin Systems",
      "type": "table",
      "targets": [
        {
          "expr": "topk(10, sum by (origin_system) (increase(sdk_attribution_errors_total[24h])))"
        }
      ]
    },
    {
      "title": "Rejects vs Overrides",
      "type": "timeseries",
      "targets": [
        {
          "expr": "sum(rate(sdk_attribution_rejects_total[5m]))",
          "legendFormat": "Rejects"
        },
        {
          "expr": "sum(rate(sdk_attribution_overrides_total[5m]))",
          "legendFormat": "Overrides"
        }
      ]
    }
  ]
}
```

### Row 3: Legacy Bucket Tracking

```json
{
  "title": "Legacy Attribution",
  "panels": [
    {
      "title": "Legacy Bucket Size (Total)",
      "type": "stat",
      "targets": [
        {
          "expr": "runs_legacy_bucket_size"
        }
      ]
    },
    {
      "title": "Legacy Bucket Trend",
      "type": "timeseries",
      "targets": [
        {
          "expr": "runs_legacy_bucket_size",
          "legendFormat": "Total legacy runs"
        }
      ],
      "description": "Should be stable or decreasing after enforcement"
    },
    {
      "title": "New Legacy Entries (Should Be Zero)",
      "type": "timeseries",
      "targets": [
        {
          "expr": "increase(runs_with_legacy_attribution_total[1h])",
          "legendFormat": "New legacy runs"
        }
      ],
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": 0},
          {"color": "red", "value": 1}
        ]
      }
    }
  ]
}
```

---

## 5. Incident Response Procedures

### Severity 1: Enforcement Breach (Page)

**Trigger:** `AttributionEnforcementBreach` or `AttributionConstraintViolation`

**Response Time:** 15 minutes

**Procedure:**

1. **Identify the source**
   ```bash
   # Query for recent legacy runs
   psql "$DATABASE_URL" -c "
     SELECT origin_system_id, agent_id, COUNT(*), MAX(created_at)
     FROM runs
     WHERE agent_id = 'legacy-unknown'
       AND created_at > NOW() - INTERVAL '1 hour'
     GROUP BY origin_system_id, agent_id
     ORDER BY COUNT(*) DESC;
   "
   ```

2. **Block the producer**
   - If API key: Revoke immediately
   - If service: Contact on-call for that service
   - If direct DB: Revoke write access

3. **Assess blast radius**
   - How many runs affected?
   - Which agents/tenants impacted?
   - Any downstream effects (incidents, policies)?

4. **Remediate**
   - If fixable: Update the producer's SDK
   - If unfixable: Block permanently

5. **Post-incident**
   - File incident report
   - Update runbook if new pattern
   - Consider additional guardrails

### Severity 2: High Rejection Rate (Warning)

**Trigger:** `AttributionRejectionRateHigh`

**Response Time:** 4 hours

**Procedure:**

1. **Identify top offenders**
   ```promql
   topk(5, sum by (origin_system) (rate(sdk_attribution_rejects_total[1h])))
   ```

2. **Contact teams**
   - Slack: #aos-sdk-consumers
   - Email: sdk-updates@company.com

3. **Provide guidance**
   - Link to SDK_ATTRIBUTION_ENFORCEMENT.md
   - Offer migration support

4. **Track progress**
   - Create ticket for each origin_system
   - Set SLA for migration completion

---

## 6. Rollout Checklist (Pre-Hard-Fail)

Before enabling **hard fail** mode:

| Check | Command | Expected |
|-------|---------|----------|
| Shadow violations | `sum(increase(sdk_attribution_errors_total{enforcement_mode="shadow"}[24h]))` | < 10 |
| Override usage | `sum(increase(sdk_attribution_overrides_total[24h]))` | 0 |
| Legacy bucket growth | `increase(runs_with_legacy_attribution_total[24h])` | 0 |
| Rejection rate | `rate(sdk_attribution_rejects_total[1h]) / rate(sdk_attribution_validations_total[1h])` | < 0.001 |
| All producers identified | Manual check | Yes |
| Teams notified | Manual check | Yes |
| Rollback plan documented | Manual check | Yes |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `SDK_ATTRIBUTION_ENFORCEMENT.md` | Implementation guide |
| `ATTRIBUTION_ARCHITECTURE.md` | Contract chain |
| `ATTRIBUTION_FAILURE_MODE_MATRIX.md` | Blast radius |
| `SDK_ATTRIBUTION_ROLLOUT_COMMS.md` | Team notification |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
