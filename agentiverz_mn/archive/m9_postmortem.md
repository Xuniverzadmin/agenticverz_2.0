# M9 Failure Catalog Persistence Layer - Deployment Guide

**Status:** COMPLETE (2025-12-08)
**Tag:** m9.0.0
**Branch:** feature/m4.5-failure-catalog-integration

---

## What Changed

### Database Schema
- **failure_matches table** - Stores all failure events with catalog matching
- **failure_pattern_exports table** - Audit trail for R2 uploads
- **17 indexes** for query performance on tenant, error code, category, recovery status

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/failures` | GET | List failures with filters |
| `/api/v1/failures/{id}` | GET | Get failure details |
| `/api/v1/failures/stats` | GET | Aggregate statistics |
| `/api/v1/failures/unrecovered` | GET | Failures needing recovery |
| `/api/v1/failures/{id}/recovery` | PATCH | Mark recovery success/failure |

### Storage Integration
- Cloudflare R2 for durable storage of aggregation results
- Local fallback with automatic retry worker
- 90-day retention lifecycle

### Prometheus Metrics
| Metric | Type | Labels |
|--------|------|--------|
| `failure_match_hits_total` | Counter | error_code, category |
| `failure_match_misses_total` | Counter | error_code |
| `recovery_success_total` | Counter | recovery_mode, error_code |
| `recovery_failure_total` | Counter | recovery_mode, error_code |
| `failure_agg_r2_upload_attempt_total` | Counter | status |
| `failure_persist_dropped_total` | Counter | - |

---

## Monitoring Dashboards

### Primary Dashboard
**Location:** Grafana → M9 Failure Catalog

**Panels:**
1. **Hit Rate** - Percentage of failures matched to catalog
   - Alert threshold: < 70% over 10m
2. **Recovery Success Rate** - Percentage of successful recoveries
   - Alert threshold: < 50% over 30m
3. **Unmatched Failures** - Count of failures not in catalog
4. **Top Error Codes** - Bar chart of most frequent errors
5. **Recovery Attempts by Mode** - Breakdown of retry, fallback, manual

### Alert Rules
| Alert | Threshold | Severity |
|-------|-----------|----------|
| `FailureCatalogMissRateHigh` | miss_rate > 30% for 10m | Warning |
| `RecoverySuccessRateLow` | success_rate < 50% for 30m | Warning |
| `FailurePersistDropped` | dropped_total > 0 for 5m | Critical |
| `R2UploadFailed` | fallback_total increased | Warning |

---

## How to Mark Recovery via API

### Mark Recovery Success
```bash
curl -X PATCH "http://localhost:8000/api/v1/failures/{failure_id}/recovery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_succeeded": true,
    "recovered_by": "ops-team",
    "notes": "Manually resolved by restarting service"
  }'
```

### Mark Recovery Failed
```bash
curl -X PATCH "http://localhost:8000/api/v1/failures/{failure_id}/recovery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_succeeded": false,
    "recovered_by": "ops-team",
    "notes": "Requires code fix - escalating to dev"
  }'
```

### List Unrecovered Failures
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/failures/unrecovered?since_hours=24&limit=50"
```

---

## Verification Commands

### 1. Check Table Structure
```bash
PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\d+ failure_matches"
```

### 2. Run Synthetic Validation
```bash
cd /root/agenticverz2.0
python tools/generate_synthetic_failures.py --validate
```

### 3. Check Prometheus Metrics
```bash
curl 'http://localhost:9090/api/v1/query?query=failure_match_hits_total'
curl 'http://localhost:9090/api/v1/query?query=recovery_success_total'
```

### 4. Verify API Endpoints
```bash
curl -sS -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/failures/stats | jq .
```

### 5. Check R2 Upload Status
```bash
./scripts/ops/r2_verify.sh --list
```

---

## Rollback Procedure

### 1. Immediate Rollback (Feature Flag)
```bash
# Disable failure catalog in feature flags
curl -X PATCH "http://localhost:8000/api/v1/features/failure_catalog_m9" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": false}'
```

### 2. Kubernetes Rollback
```bash
kubectl rollout undo deployment/aos-backend -n aos-canary
```

### 3. Database Rollback (Last Resort)
```bash
# Restore from pre-M9 backup
pg_restore -h nova_db -U nova -d nova_aos /opt/backups/nova_aos_pre_m9.dump
```

---

## Contact List

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call | #aos-oncall Slack | PagerDuty |
| DB Lead | TBD | Slack DM |
| Backend Lead | TBD | Slack DM |
| Product | TBD | Email |

---

## Canary Deployment Checklist

### Pre-Canary
- [x] Migrations applied to staging
- [x] Synthetic validation passed (1000 events)
- [x] Prometheus metrics verified
- [x] Grafana dashboard imported
- [x] API endpoints tested
- [ ] DB backup taken
- [ ] Feature flags configured

### Canary (10% Traffic)
- [ ] Deploy to canary namespace
- [ ] Route 10% traffic via ingress weight
- [ ] Monitor for 24-48 hours

### Canary Success Criteria
- Miss rate ≤ 15% baseline
- Recovery success ≥ 60% baseline
- No dropped persistence events (failure_persist_dropped_total == 0)
- No critical alerts for 24h

### Production Promotion
- [ ] Canary success criteria met
- [ ] Aggregation JSON stored in R2
- [ ] Tenant backfill plan ready
- [ ] Secrets rotation validated
- [ ] Full production rollout

---

## Known Issues & Workarounds

### 1. tenant_id Nullable
**Issue:** tenant_id column is still nullable, allowing cross-tenant noise.
**Workaround:** Filter queries by tenant_id explicitly.
**Fix Timeline:** Next sprint - backfill + NOT NULL enforcement.

### 2. High Cardinality Labels
**Issue:** error_code label can have unbounded values.
**Workaround:** Prometheus relabel rules truncate long codes.
**Monitoring:** Watch `prometheus_tsdb_head_series` for growth.

### 3. Aggregation Durability
**Issue:** Local file fallback if R2 fails.
**Workaround:** Retry worker processes fallbacks every 15 minutes.
**Fix:** R2 integration complete (PIN-049).

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| m9.0.0 | 2025-12-07 | Initial release - persistence layer complete |
| m9.0.1 | 2025-12-08 | R2 durable storage integration |
