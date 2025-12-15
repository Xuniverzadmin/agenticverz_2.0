# PIN-049: Cloudflare R2 Durable Storage Integration

**Status:** COMPLETE
**Created:** 2025-12-08
**Category:** Infrastructure / Storage
**Priority:** P1 (M9 Requirement)

---

## Summary

Implemented durable object storage for failure pattern aggregation using Cloudflare R2 (S3-compatible). The aggregation job now writes `candidate_failure_patterns.json` to R2 with automatic local fallback, retries, verification, and Prometheus metrics.

---

## Implementation Details

### Components Created

| Component | Path | Purpose |
|-----------|------|---------|
| Storage Helper | `backend/app/jobs/storage.py` | R2 upload with retries, fallback, metrics |
| DB Migration | `backend/alembic/versions/016_create_failure_pattern_exports.py` | Audit table for exports |
| Retry Worker | `scripts/ops/retry_r2_fallbacks.sh` | Retry failed local fallbacks |
| Verify Script | `scripts/ops/r2_verify.sh` | Check R2 connectivity and list objects |
| Lifecycle Script | `scripts/ops/r2_lifecycle.sh` | Configure retention rules |
| Cleanup Script | `scripts/ops/r2_cleanup.sh` | Delete test/old objects from R2 |
| CI Workflow | `.github/workflows/failure-aggregation.yml` | Nightly aggregation job |
| Aggregation Service | `deploy/systemd/agenticverz-failure-aggregation.service` | Systemd service for aggregation |
| Aggregation Timer | `deploy/systemd/agenticverz-failure-aggregation.timer` | Timer for 02:00 UTC daily |
| Retry Service | `deploy/systemd/agenticverz-r2-retry.service` | Systemd service for retry worker |
| Retry Timer | `deploy/systemd/agenticverz-r2-retry.timer` | Timer for every 15 minutes |

### Environment Variables

```bash
# Required for R2 uploads
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET=candidate-failure-patterns
R2_ENDPOINT=https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com

# Optional configuration
R2_UPLOAD_PREFIX=failure_patterns  # default
R2_RETENTION_DAYS=90               # default
R2_MAX_RETRIES=5                   # default
AGG_LOCAL_FALLBACK=/opt/agenticverz/state/fallback-uploads
```

### Object Key Format

```
{prefix}/YYYY/MM/DD/candidates_{timestamp}_{sha12}.json

Example:
failure_patterns/2025/12/08/candidates_20251208T023015Z_a1b2c3d4e5f6.json
```

### Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `failure_agg_r2_upload_attempt_total` | Counter | Total upload attempts (labels: status) |
| `failure_agg_r2_upload_duration_seconds` | Histogram | Upload duration |
| `failure_agg_r2_upload_fallback_total` | Counter | Fallback to local storage |
| `failure_agg_r2_retry_success_total` | Counter | Successful retries |
| `failure_agg_r2_upload_bytes_total` | Counter | Total bytes uploaded |

### Database Schema

```sql
CREATE TABLE failure_pattern_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    s3_key TEXT NOT NULL,           -- R2 key or local path
    uploaded_at TIMESTAMPTZ DEFAULT now(),
    uploader TEXT,                  -- 'failure_aggregation_job'
    size_bytes BIGINT,
    sha256 TEXT,
    status TEXT NOT NULL,           -- uploaded|fallback_local|retrying|failed
    notes TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Usage

### Run Aggregation Manually

```bash
cd /root/agenticverz2.0/backend

# Full run with R2 upload
PYTHONPATH=. python -m app.jobs.failure_aggregation

# Skip R2 upload (local only)
PYTHONPATH=. python -m app.jobs.failure_aggregation --skip-r2

# Custom parameters
PYTHONPATH=. python -m app.jobs.failure_aggregation --days 14 --min-occurrences 5 --json
```

### Verify R2 Configuration

```bash
# Check connectivity
./scripts/ops/r2_verify.sh

# List recent uploads
./scripts/ops/r2_verify.sh --list

# Get object metadata
./scripts/ops/r2_verify.sh --head failure_patterns/2025/12/08/candidates_xxx.json
```

### Configure Lifecycle Rules

```bash
# Apply 90-day retention (default)
./scripts/ops/r2_lifecycle.sh --apply

# Custom retention
./scripts/ops/r2_lifecycle.sh --apply --days 180

# Show current rules
./scripts/ops/r2_lifecycle.sh --show
```

### Retry Failed Uploads

```bash
# Process pending fallbacks
./scripts/ops/retry_r2_fallbacks.sh

# Dry run
./scripts/ops/retry_r2_fallbacks.sh --dry-run

# Limit to 10 files
./scripts/ops/retry_r2_fallbacks.sh --max 10
```

### Cron Configuration

Add to `scripts/ops/cron/aos-maintenance.cron`:

```cron
# Failure aggregation (nightly at 2am)
0 2 * * * cd /root/agenticverz2.0/backend && PYTHONPATH=. python -m app.jobs.failure_aggregation >> /var/log/aos/aggregation.log 2>&1

# R2 fallback retry (every 15 minutes)
*/15 * * * * /root/agenticverz2.0/scripts/ops/retry_r2_fallbacks.sh >> /var/log/aos/r2_retry.log 2>&1
```

### Systemd Deployment (Recommended)

Copy systemd units and enable timers:

```bash
# Copy units
sudo cp deploy/systemd/agenticverz-failure-aggregation.* /etc/systemd/system/
sudo cp deploy/systemd/agenticverz-r2-retry.* /etc/systemd/system/

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable --now agenticverz-failure-aggregation.timer
sudo systemctl enable --now agenticverz-r2-retry.timer

# Verify timers
sudo systemctl list-timers --all | grep agenticverz
```

Units provided:
- `agenticverz-failure-aggregation.service` - Nightly aggregation job
- `agenticverz-failure-aggregation.timer` - Runs at 02:00 UTC daily
- `agenticverz-r2-retry.service` - Fallback retry worker
- `agenticverz-r2-retry.timer` - Runs every 15 minutes

### Cleanup Test Objects

```bash
# Dry run - list objects to delete
./scripts/ops/r2_cleanup.sh --dry-run --test-only

# Delete today's test uploads
./scripts/ops/r2_cleanup.sh --test-only --force

# Delete objects older than 30 days
./scripts/ops/r2_cleanup.sh --older-than 30

# Delete specific prefix
./scripts/ops/r2_cleanup.sh --prefix failure_patterns/2025/12/08
```

---

## Rollout Checklist

- [x] Add env vars to `.env` / `.env.example`
- [x] Create R2 bucket in Cloudflare dashboard
- [x] Generate R2 API tokens with read/write permissions
- [x] Store credentials in Vault: `agenticverz/r2-storage`
- [x] Run migration: `alembic upgrade head`
- [x] Test local aggregation: `python -m app.jobs.failure_aggregation --json`
- [x] Verify R2 upload: `./scripts/ops/r2_verify.sh --list`
- [x] Create systemd units for aggregation and retry
- [ ] Configure lifecycle rules: `./scripts/ops/r2_lifecycle.sh --apply`
- [ ] Add secrets to GitHub Actions (see table below)
- [ ] Enable systemd timers (or cron jobs)

---

## GitHub Actions Secrets Required

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | R2 API token ID |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret |
| `R2_ENDPOINT` | R2 endpoint URL |
| `R2_BUCKET` | Bucket name (optional, defaults to `candidate-failure-patterns`) |

---

## Architecture Notes

### Retry Logic

1. **Primary:** Upload to R2 with tenacity retry (5 attempts, exponential backoff)
2. **Fallback:** Write to local directory on failure
3. **Recovery:** Retry worker processes fallback files periodically
4. **Audit:** All operations recorded in `failure_pattern_exports` table

### Failure Modes

| Scenario | Behavior |
|----------|----------|
| R2 not configured | Skip upload, local file only |
| R2 upload fails | Retry 5x with backoff, then fallback local |
| Local fallback dir missing | Auto-create directory |
| DB record fails | Log warning, continue |

### Security

- R2 credentials stored in Vault, not plaintext
- Object metadata includes SHA256 for verification
- Lifecycle rules auto-expire old patterns
- No public access to R2 bucket

---

## Related PINs

- **PIN-048:** M9 Failure Catalog Persistence (parent feature)
- **PIN-036:** Infrastructure Pending Items (R2 was listed as P1)
- **PIN-034:** HashiCorp Vault Secrets (credential storage)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-08 | Initial implementation complete |
| 2025-12-08 | Added Vault integration for credentials |
| 2025-12-08 | Created systemd units for scheduled execution |
| 2025-12-08 | Added R2 cleanup script for test objects |
| 2025-12-08 | End-to-end verification complete |
