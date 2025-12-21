# PIN-112: Compute Stickiness Scheduler

**Status:** COMPLETE
**Created:** 2025-12-20
**Category:** Ops Console / Automation
**Milestone:** M24 Phase-2.1

---

## Summary

Implemented a systemd timer to automatically run the compute-stickiness job every 15 minutes, ensuring the Ops Console always has fresh customer intelligence data.

---

## Problem

The compute-stickiness job needed to run periodically to keep the `ops_customer_segments` cache table populated with fresh data. Without automation:
- Ops Console would show stale or empty customer data
- Stickiness trends would not update
- Friction detection would lag behind real events

---

## Solution

### 1. Cron Script

**File:** `scripts/ops/compute_stickiness_cron.sh`

```bash
#!/bin/bash
# Compute Stickiness Cron Job
# Runs every 15 minutes via systemd timer

set -e

LOG_FILE="/var/log/aos/compute-stickiness.log"
API_BASE="${AOS_API_BASE:-http://localhost:8000}"
API_KEY="${AOS_API_KEY}"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
}

mkdir -p /var/log/aos

log "Starting compute-stickiness job..."

# Run compute-stickiness
RESPONSE=$(curl -s -X POST "$API_BASE/ops/jobs/compute-stickiness" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json")

STATUS=$(echo "$RESPONSE" | jq -r '.status // "error"')
MESSAGE=$(echo "$RESPONSE" | jq -r '.message // "No message"')

if [ "$STATUS" = "completed" ]; then
    log "SUCCESS: status=$STATUS, message=$MESSAGE"
else
    log "FAILED: status=$STATUS, message=$MESSAGE"
fi

# Also run silent churn detection
log "Running silent churn detection..."
CHURN_RESPONSE=$(curl -s -X POST "$API_BASE/ops/jobs/detect-silent-churn" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json")

CHURN_STATUS=$(echo "$CHURN_RESPONSE" | jq -r '.status // "error"')
CHURN_MESSAGE=$(echo "$CHURN_RESPONSE" | jq -r '.message // "No message"')

if [ "$CHURN_STATUS" = "completed" ]; then
    log "SUCCESS: status=$CHURN_STATUS, message=$CHURN_MESSAGE"
else
    log "FAILED: status=$CHURN_STATUS, message=$CHURN_MESSAGE"
fi

log "Compute-stickiness job completed."
```

### 2. Systemd Service

**File:** `/etc/systemd/system/aos-compute-stickiness.service`

```ini
[Unit]
Description=AOS Compute Stickiness Job
After=network.target docker.service
Wants=docker.service

[Service]
Type=oneshot
ExecStart=/root/agenticverz2.0/scripts/ops/compute_stickiness_cron.sh
User=root
Environment=AOS_API_BASE=http://localhost:8000
Environment=AOS_API_KEY=edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf

[Install]
WantedBy=multi-user.target
```

### 3. Systemd Timer

**File:** `/etc/systemd/system/aos-compute-stickiness.timer`

```ini
[Unit]
Description=Run AOS Compute Stickiness every 15 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target
```

---

## Installation

```bash
# Copy service and timer files
sudo cp /root/agenticverz2.0/scripts/ops/aos-compute-stickiness.service /etc/systemd/system/
sudo cp /root/agenticverz2.0/scripts/ops/aos-compute-stickiness.timer /etc/systemd/system/

# Make script executable
chmod +x /root/agenticverz2.0/scripts/ops/compute_stickiness_cron.sh

# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable aos-compute-stickiness.timer
sudo systemctl start aos-compute-stickiness.timer

# Verify timer is active
systemctl list-timers | grep aos-compute-stickiness
```

---

## Verification

```bash
# Check timer status
systemctl status aos-compute-stickiness.timer

# Check last run logs
cat /var/log/aos/compute-stickiness.log

# Manually trigger job
sudo systemctl start aos-compute-stickiness.service

# Watch for next run
systemctl list-timers aos-compute-stickiness.timer
```

---

## Log Output

```
[2025-12-20T19:22:37+01:00] Starting compute-stickiness job...
[2025-12-20T19:22:38+01:00] SUCCESS: status=completed, message=Stickiness computation completed
[2025-12-20T19:22:38+01:00] Running silent churn detection...
[2025-12-20T19:22:39+01:00] SUCCESS: status=completed, message=Silent churn detection completed
[2025-12-20T19:22:39+01:00] Compute-stickiness job completed.
```

---

## Schedule

| Event | Timing |
|-------|--------|
| First run after boot | 5 minutes |
| Recurring interval | 15 minutes |
| Accuracy tolerance | 1 minute |
| Persistent | Yes (catches up after downtime) |

---

## Jobs Executed

| Job | Endpoint | Purpose |
|-----|----------|---------|
| compute-stickiness | `POST /ops/jobs/compute-stickiness` | Refresh customer segments cache |
| detect-silent-churn | `POST /ops/jobs/detect-silent-churn` | Identify churning customers |

---

## Commits

- `c75e109` - feat(ops): Schedule compute-stickiness job to run every 15 minutes

---

## Related PINs

- [PIN-105](PIN-105-ops-console-founder-intelligence.md) - Ops Console Founder Intelligence
- [PIN-110](PIN-110-enhanced-compute-stickiness-job.md) - Enhanced Compute Stickiness Job
- [PIN-111](PIN-111-founder-ops-console-ui.md) - Founder Ops Console UI
