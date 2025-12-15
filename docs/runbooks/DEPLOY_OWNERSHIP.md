# Deploy Ownership Protocol

**Last Updated:** 2025-12-09
**Applies To:** M10 and all future milestone deploys

---

## Purpose

Every production deploy must have a single owner responsible for the 48-hour stabilization window. This prevents "diffusion of responsibility" and ensures rapid response to issues.

---

## Rules

### 1. Single Owner Assigned Before Deploy

- **Who:** The person who merges the deploy PR is the default owner
- **Handoff:** Owner can hand off to another team member with explicit Slack message
- **No Gaps:** There must always be exactly one owner during the 48h window

### 2. 48-Hour Pager Window

| Hour | Owner Responsibility |
|------|---------------------|
| T+0 to T+4 | Active monitoring (check every 15 min) |
| T+4 to T+24 | Regular monitoring (check every 2 hours) |
| T+24 to T+48 | Maintenance monitoring (check every 4 hours) |

### 3. No Feature Work During Window

- Owner must NOT work on new features
- Only stability fixes, rollbacks, and monitoring
- If blocked by pager duty, escalate to get coverage

---

## Deploy Ownership Checklist

Copy this into your deploy PR:

```markdown
## Deploy Ownership

**Owner:** @username
**Deploy Time:** YYYY-MM-DD HH:MM UTC
**Window End:** YYYY-MM-DD HH:MM UTC (+48h)

### Pre-Deploy
- [ ] Staging report JSON attached (all P1 checks PASS)
- [ ] Rollback procedure documented
- [ ] Owner confirmed available for 48h

### T+0 (Deploy)
- [ ] Deploy completed successfully
- [ ] Health check passing
- [ ] Posted to #deploys channel

### T+4 (First Checkpoint)
- [ ] No critical alerts fired
- [ ] Error rate stable
- [ ] Dead letter count: ___

### T+24 (Day 1 Checkpoint)
- [ ] System stable for 24h
- [ ] Dead letter count: ___ (should be stable/decreasing)
- [ ] Synthetic traffic running (check `aos-dl stats`)

### T+48 (Handoff)
- [ ] Zero critical incidents
- [ ] Metrics baseline established
- [ ] Sign-off comment posted
- [ ] Owner responsibility released
```

---

## M10-Specific Monitoring

During M10 deploy ownership window:

### Every 4 Hours
```bash
# Check dead letter stats
aos-dl stats

# Check queue depth
aos-dl top --limit 5

# Check timer health
systemctl list-timers | grep m10
```

### Daily
```bash
# Review daily stats CSV
cat /var/log/m10/m10_stats_$(date +%Y-%m).csv | tail -5

# Check for replay candidates
aos-dl replay --dry-run
```

### Alert Response
| Alert | First Response |
|-------|---------------|
| M10QueueDepthCritical | Check consumer health, scale if needed |
| M10NoStreamConsumers | Restart worker, check logs |
| M10OutboxPendingCritical | Check outbox processor, DB connectivity |
| M10DeadLetterCritical | Run `aos-dl top`, investigate failures |
| M10MatviewVeryStale | Run `m10-maintenance.service` manually |

---

## Escalation Path

If owner is overwhelmed:

1. **Slack:** Post in #oncall with `@here ESCALATION: M10 deploy issue`
2. **Handoff:** Explicitly transfer ownership in thread
3. **Document:** Update PR with handoff timestamp

---

## Post-Mortem Requirement

If any of these occur during the 48h window:
- Critical alert fired
- Manual intervention required
- Rollback performed

**Then:** Owner must create a brief incident doc within 72h:
- What happened
- Root cause
- Preventive action

Location: `docs/incidents/YYYY-MM-DD-brief-description.md`

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                  DEPLOY OWNERSHIP RULES                      │
├─────────────────────────────────────────────────────────────┤
│ 1. ONE OWNER      → Single person responsible for 48h       │
│ 2. NO FEATURES    → Stability focus only during window      │
│ 3. CHECK CADENCE  → Every 15m→2h→4h as window progresses    │
│ 4. DOCUMENT       → Post-mortem if any incident occurs      │
│ 5. EXPLICIT END   → Sign-off comment releases ownership     │
└─────────────────────────────────────────────────────────────┘
```
