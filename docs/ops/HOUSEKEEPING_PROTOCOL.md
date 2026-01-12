# HOUSEKEEPING Protocol (HK-01)

**Version:** 1.0
**Status:** ACTIVE
**Trigger:** `do housekeeping`

---

## Purpose

Maintain **VPS health** by removing *stale, orphaned, or unused system resources* **without affecting live services or work state**.

Claude acts as a **system janitor under strict guardrails**.

---

## Domain

| Domain | Protocol | Scope |
|--------|----------|-------|
| **System Health** | HOUSEKEEPING (HK-01) | VPS resources only |

This protocol is **mutually exclusive** with SESSION_RECONCILE (SR-01).
Claude **must never cross domains** in a single invocation.

**Housekeeping must never unblock a failed session reconciliation.**

---

## Cleanup Tiers

| Tier | Risk Level | Approval | Actions |
|------|------------|----------|---------|
| **Tier-0** | None | Auto | Read-only scans |
| **Tier-1** | Safe | Auto | Stale file cleanup, cache clear |
| **Tier-2** | Risky | Required | Service restart, volume prune |

---

## Claude Responsibilities (MANDATORY)

### 1. Run Read-Only Scans First (Tier-0)

Claude **MUST** scan before any action:

- [ ] Disk usage (`df -h`)
- [ ] Memory pressure (`free -h`)
- [ ] Zombie processes (`ps aux`)
- [ ] Orphan containers (`docker ps -a`)
- [ ] Stale jobs/workers
- [ ] Docker system usage (`docker system df`)

### 2. Classify Cleanup by Tier

| Category | Tier | Auto-Execute |
|----------|------|--------------|
| Clear page cache | Tier-1 | Yes |
| Vacuum journal logs | Tier-1 | Yes |
| Clean /tmp files > 1 day | Tier-1 | Yes |
| Clean ~/.cache files > 7 days | Tier-1 | Yes |
| Kill stale test processes | Tier-1 | Yes |
| Remove stopped containers | Tier-1 | Yes |
| Prune dangling images | Tier-1 | Yes |
| Clear Docker build cache | Tier-1 | Yes |
| Remove orphan volumes | Tier-2 | **No - requires approval** |
| Restart unhealthy services | Tier-2 | **No - requires approval** |
| Prune all unused images | Tier-2 | **No - requires approval** |

### 3. Execute Only Tier-1 Actions Automatically

Claude **MUST NOT** execute Tier-2 without explicit user approval.

### 4. Protect Critical Services

Claude **MUST** verify these services before AND after cleanup:

| Service | Check Command | Expected |
|---------|---------------|----------|
| Frontend | `curl -s http://localhost:3000/health` | 200 |
| Backend API | `curl -s http://localhost:8000/health` | 200 |
| Database | `docker exec nova_db pg_isready` | ready |
| Worker | `docker ps \| grep nova_worker` | running |

If any service is unhealthy **BEFORE** cleanup → **REPORT, do not proceed**.
If any service becomes unhealthy **AFTER** cleanup → **ALERT immediately**.

### 5. Emit Artifact

Claude **MUST** create:

```
artifacts/housekeeping/HK-<timestamp>.yaml
```

---

## Claude Is Explicitly FORBIDDEN To

| Action | Reason |
|--------|--------|
| Touch application code | Domain violation |
| Build, deploy, or test | Domain violation (belongs to SR-01) |
| Commit or push git | Domain violation (belongs to SR-01) |
| Stop active containers | May disrupt services |
| Restart protected services | Tier-2 requires approval |
| Perform Tier-2 cleanup without approval | Risk of data loss |
| Delete application data | Irreversible |
| Modify configuration files | May break services |

---

## Success Condition

```yaml
services_protected: verified
no_active_work_disrupted: true
```

---

## Tier-1 Task Checklist

### Docker Cleanup
- [ ] Remove stopped containers: `docker container prune -f`
- [ ] Remove dangling images: `docker image prune -f`
- [ ] Clear build cache: `docker builder prune -af`

### System Memory
- [ ] Kill stale pytest processes: `pkill -f pytest`
- [ ] Clear page cache: `sync && echo 3 > /proc/sys/vm/drop_caches`
- [ ] Vacuum journal logs: `journalctl --vacuum-time=3d`

### Temp Files
- [ ] Clean /tmp: `find /tmp -type f -mtime +1 -delete`
- [ ] Clean cache: `find ~/.cache -type f -mtime +7 -delete`

### Health Verification
- [ ] Verify all protected services healthy
- [ ] Check disk usage < 80%
- [ ] Check memory available > 40%

---

## Tier-2 Tasks (Approval Required)

When Claude encounters Tier-2 cleanup opportunities:

```
TIER-2 APPROVAL REQUIRED

The following actions require explicit approval:

1. [ACTION] Remove orphan volumes (X volumes, Y MB)
2. [ACTION] Prune all unused images (X images, Y GB)
3. [ACTION] Restart unhealthy service: <name>

Reply with numbers to approve (e.g., "approve 1,2") or "skip all"
```

---

## Artifact Schema

### HK-<timestamp>.yaml

```yaml
schema_version: "1.0"
protocol: "HK-01"
id: "HK-<timestamp>"
timestamp: "<ISO-8601>"
triggered_by: "user"

scans:
  disk:
    total_gb: <float>
    used_gb: <float>
    available_gb: <float>
    usage_percent: <int>
  memory:
    total_gb: <float>
    used_gb: <float>
    available_gb: <float>
  docker:
    images_count: <int>
    images_size_gb: <float>
    containers_count: <int>
    volumes_count: <int>
    build_cache_mb: <float>

services_pre_check:
  frontend: "healthy|unhealthy|skipped"
  backend: "healthy|unhealthy|skipped"
  database: "healthy|unhealthy|skipped"
  worker: "healthy|unhealthy|skipped"

tier_1_actions:
  containers_removed: <int>
  images_pruned: <int>
  build_cache_cleared_mb: <float>
  processes_killed: <int>
  page_cache_cleared: true|false
  journal_vacuumed: true|false
  tmp_files_cleaned: <int>
  cache_files_cleaned: <int>

tier_2_actions:
  requested: []
  approved: []
  executed: []
  skipped: []

services_post_check:
  frontend: "healthy|unhealthy"
  backend: "healthy|unhealthy"
  database: "healthy|unhealthy"
  worker: "healthy|unhealthy"

space_reclaimed:
  docker_mb: <float>
  system_mb: <float>
  total_mb: <float>

result:
  services_protected: true|false
  no_active_work_disrupted: true|false
  success: true|false
  notes: "<any warnings or issues>"
```

---

## Failure Handling

| Condition | Claude Action |
|-----------|---------------|
| Service unhealthy before cleanup | REPORT, do not proceed |
| Service unhealthy after cleanup | ALERT immediately |
| Disk critically full (>95%) | Request Tier-2 approval |
| Unknown process consuming resources | REPORT, do not kill |

---

## Integration with Session Reconciliation

Housekeeping **does not affect exit eligibility**.

| Scenario | Correct Action |
|----------|----------------|
| Session dirty + system healthy | Run SR-01, not HK-01 |
| Session clean + system unhealthy | Run HK-01 |
| Both needed | Run HK-01 first, then SR-01 |

---

## Artifact Freshness Rules (TODO-05)

**Status:** MANDATORY
**Effective:** 2026-01-12

### HK Artifact Freshness

| Rule | Requirement |
|------|-------------|
| HK-FRESH-001 | HK artifacts must be ≤ 24 hours old for exit eligibility |
| HK-FRESH-002 | Stale HK artifacts trigger exit block, not silent accept |
| HK-FRESH-003 | If HK artifact is missing, exit is BLOCKED |

### Freshness Threshold

Default: **24 hours**

An HK artifact is considered **fresh** if:

```
(current_time - artifact_timestamp) ≤ 24 hours
```

This threshold can be configured via `--hk-max-age` flag in session_exit.py.

### Exit Gate Integration

The session exit gate enforces HK freshness:

```python
# session_exit.py - check_hk_freshness()
# Default: 24 hours
# Configurable: --hk-max-age HOURS
```

### Stale Artifact Handling

If a stale HK artifact is detected:

```
HK ARTIFACT STALE WARNING

HK artifact: <path>
Age: <age>h (max allowed: <threshold>h)

STATUS: EXIT_BLOCKED
ACTION REQUIRED: Run 'do housekeeping' to create fresh artifact
```

**Never silently accept stale HK artifacts for exit decisions.**

---

## Non-Goals (Protocol Lock) (TODO-06)

**Status:** LOCKED
**Effective:** 2026-01-12

This section documents what HOUSEKEEPING (HK-01) **will NEVER do**.
These are architectural constraints, not temporary limitations.

### Never-Goals

| Non-Goal | Rationale |
|----------|-----------|
| Auto-schedule housekeeping | Housekeeping is human-triggered only |
| Execute Tier-2 without token | Token-based approval is mandatory |
| Cross into SR-01 domain | Domain separation is absolute |
| Affect session exit eligibility | HK status is independent of SR status |
| Write to session state file | Only session_reconcile.py may write |
| Delete application data | Irreversible actions forbidden |
| Stop protected services without approval | Service protection is paramount |
| Infer cleanup needs | All actions must be scan-driven |
| Silent cleanup | All actions must be logged and auditable |

### Why These Are Locked

1. **Human-Triggered Only**: Automated housekeeping could interfere with active work.

2. **Tier-2 Token Approval**: Risky actions require explicit, traceable human consent.

3. **Domain Separation**: Mixing system health and work state creates ambiguous authority.

4. **Exit Independence**: Housekeeping freshness is advisory for exit, not blocking for reconciliation.

5. **Session State Protection**: Single-writer pattern prevents race conditions and corruption.

6. **Service Protection**: Critical services must never be affected without explicit approval.

### Forbidden Auto-Schedule Scenarios

Claude will **NEVER**:

- Schedule housekeeping based on disk pressure
- Auto-run housekeeping before session exit
- Trigger housekeeping from failed tests
- Chain housekeeping to reconciliation automatically

**Human trigger is the only valid trigger.**

### Evolution Disclaimer

These non-goals may only be changed via:

1. Explicit human approval in session
2. Amendment to this document
3. Update to CLAUDE_AUTHORITY.md Section 11

**Undocumented evolution is forbidden.**

---

## References

- CLAUDE_AUTHORITY.md - Authority model
- SESSION_RECONCILE_PROTOCOL.md - Work state (separate domain)
