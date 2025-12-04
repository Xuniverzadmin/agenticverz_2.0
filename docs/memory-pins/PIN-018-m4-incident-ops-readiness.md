# PIN-018: M4 Incident & Ops Readiness

**Serial:** PIN-018
**Title:** M4 Incident Response & Operational Readiness
**Category:** Operations / Incident Response
**Status:** COMPLETE
**Created:** 2025-12-02
**Updated:** 2025-12-02

---

## Executive Summary

This PIN documents the incident response infrastructure and operational readiness tools created to support M4 Workflow Engine maturity validation. These tools enable rapid incident response, self-certification without dedicated SRE, and sustainable golden file storage management.

---

## Deliverables

### 1. M4 Incident Playbook

**Path:** `docs/runbooks/m4-incident-playbook.md`

**Purpose:** Step-by-step incident response procedures with copy/paste commands.

**Incident Types Covered:**

| Type | Severity | First Action | Recovery Time |
|------|----------|--------------|---------------|
| Mismatch detected | P0 | Emergency stop → Capture → Analyze | Hours |
| Shadow process died | P1 | Check logs → Restart if clean | Minutes |
| Disk full | P1 | Archive golden → Clear tmp | Minutes |
| Stale logs (>30min) | P2 | Check process → Restart | Minutes |
| Webhook failures | P3 | Check network → Queue locally | Low priority |

**Key Sections:**
- Quick reference table
- Immediate actions (copy/paste commands)
- Analysis steps with specific commands
- Root cause categories (VOLATILE_LEAK, SEED_MISMATCH, UNSEEDED_RNG, etc.)
- Recovery procedures
- Post-incident checklist

---

### 2. Self-Sign Runbook Checklist

**Path:** Added to `docs/memory-pins/PIN-015-m4-validation-maturity-gates.md`

**Purpose:** Enable self-certification when dedicated SRE is unavailable.

**20-Item Checklist:**

| Section | Items | Checks |
|---------|-------|--------|
| Pre-Flight | 1-5 | Backend health, worker, Redis, PostgreSQL, Prometheus |
| Shadow Run Verification | 6-10 | Completion, cycles, mismatches, errors, golden files |
| Runbook Operations | 11-16 | Quick shadow, sanity check, emergency stop, golden diff |
| Alerting Verification | 17-20 | Prometheus rules, active alerts, Alertmanager, checkpoint DB |

**Certification Statement:**
1. 24-hour shadow simulation completed with 0 mismatches
2. All 20 checklist items executed and verified
3. Incident playbook reviewed and understood
4. Emergency stop procedures tested
5. Monitoring infrastructure operational

**Signature Block:** Formal sign-off template with evidence locations.

---

### 3. Golden Retention Script

**Path:** `scripts/ops/golden_retention.sh`

**Purpose:** Prevent disk exhaustion during long-running shadow simulations.

**Commands:**

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Show golden file usage | `./golden_retention.sh status` |
| `archive` | Compress & move old files | `./golden_retention.sh archive --days 1` |
| `cleanup` | Delete old files | `./golden_retention.sh cleanup --days 7 --force` |
| `verify` | Check archive integrity | `./golden_retention.sh verify` |
| `restore` | Restore from archive | `./golden_retention.sh restore /path/to/archive.tgz` |

**Options:**
- `--days N` - Retention period (default: 7)
- `--dry-run` - Show actions without executing
- `--force` - Skip confirmation prompts

**Environment Variables:**
- `ARCHIVE_DIR` - Archive location (default: `/root/archive/golden`)
- `RETENTION_DAYS` - Default retention period

**Monitored Directories:**
- `/tmp/shadow_simulation_*/golden`
- `/var/lib/aos/golden`

---

## Current State

### Shadow Run Progress (T+1h 10min)

| Metric | Value |
|--------|-------|
| Cycles | 138 |
| Workflows | ~1,242 |
| Replays | ~1,242 |
| Mismatches | **0** |
| Golden Files | 1,242 |
| Golden Size | 5.0M |
| Disk Usage | 14% |

### Storage Projections

| Time | Est. Cycles | Est. Golden Files | Est. Size |
|------|-------------|-------------------|-----------|
| T+6h | ~720 | ~6,500 | ~26M |
| T+12h | ~1,440 | ~13,000 | ~52M |
| T+24h | ~2,880 | ~26,000 | ~104M |

**Recommendation:** Run `golden_retention.sh archive --days 1` at T+12h if disk exceeds 50%.

---

## Operational Workflows

### Pre-Shadow Run

```bash
# 1. Verify infrastructure
curl -s http://localhost:8000/health | jq .status
redis-cli ping
docker ps | grep -E "worker|backend"

# 2. Check disk space
df -h /tmp /var/lib/aos

# 3. Start monitoring daemon
./scripts/stress/shadow_monitor_daemon.sh start
```

### During Shadow Run

```bash
# Quick status (every 1-2 hours)
./scripts/stress/shadow_debug.sh full

# Detailed check (every 4 hours)
./scripts/stress/shadow_sanity_check.sh

# Storage check (every 6 hours)
./scripts/ops/golden_retention.sh status
```

### Post-Shadow Run

```bash
# 1. Verify completion
grep "Shadow simulation complete" /var/lib/aos/shadow_24h_*.log

# 2. Run self-sign checklist
# (Execute all 20 items in PIN-015)

# 3. Archive golden files
./scripts/ops/golden_retention.sh archive --days 0

# 4. Generate summary
python3 scripts/stress/golden_diff_debug.py \
    --summary-dir /tmp/shadow_simulation_*/golden \
    --output /root/reports/m4-shadow-summary.json

# 5. Complete sign-off in PIN-015
```

### Incident Response

```bash
# On any P0/P1 alert:
./scripts/ops/disable-workflows.sh enable

# Capture evidence
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p /root/reports/m4-incident-$TIMESTAMP
cp /var/lib/aos/shadow_*.log /root/reports/m4-incident-$TIMESTAMP/

# Follow playbook: docs/runbooks/m4-incident-playbook.md
```

---

## File Inventory

| File | Size | Purpose |
|------|------|---------|
| `docs/runbooks/m4-incident-playbook.md` | 8.5K | Incident response procedures |
| `scripts/ops/golden_retention.sh` | 4.2K | Golden file storage management |
| PIN-015 additions | +3.5K | Self-sign checklist & signature block |

---

## Acceptance Criteria

### M4 Sign-Off Requirements

| Requirement | Status | Evidence |
|-------------|--------|----------|
| 24h shadow run completes | PENDING | Shadow log |
| 0 mismatches | PENDING | Shadow log grep |
| 20/20 checklist items pass | PENDING | PIN-015 checklist |
| Incident playbook reviewed | COMPLETE | This PIN |
| Emergency stop tested | PENDING | Checklist item 13-15 |
| Monitoring operational | COMPLETE | Daemon PID 790726 |

### Definition of Done

- [ ] Shadow run completes 24 hours
- [ ] Final mismatch count = 0
- [ ] Self-sign checklist executed (20/20)
- [ ] Signature block completed in PIN-015
- [ ] Golden files archived
- [ ] Summary report generated

---

## Risk Mitigation

| Risk | Mitigation | Status |
|------|------------|--------|
| Disk exhaustion | Golden retention script | IMPLEMENTED |
| Missed alerts | Monitor daemon + cron | IMPLEMENTED |
| No SRE available | Self-sign checklist | IMPLEMENTED |
| Incident confusion | Playbook with commands | IMPLEMENTED |
| Storage growth | Projections + monitoring | DOCUMENTED |

---

## Related Documents

- [PIN-015](PIN-015-m4-validation-maturity-gates.md) - Validation Gates + Self-Sign Checklist
- [PIN-016](PIN-016-m4-ops-tooling-runbook.md) - Ops Tooling
- [PIN-017](PIN-017-m4-monitoring-infrastructure.md) - Monitoring Infrastructure
- [M4 Incident Playbook](../runbooks/m4-incident-playbook.md) - Incident Response
- [M4 Runbook](../runbooks/m4-workflow-engine.md) - Operations Guide

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-02 | Initial creation documenting incident/ops readiness |
