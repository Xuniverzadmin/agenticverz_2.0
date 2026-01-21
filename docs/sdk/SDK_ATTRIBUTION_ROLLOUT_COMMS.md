# Phase 3 Rollout Communications — Attribution Enforcement

**Status:** TEMPLATE READY
**Effective:** Pre-Rollout
**Reference:** SDK_ATTRIBUTION_ENFORCEMENT.md, SDK_ATTRIBUTION_ALERTS.md

---

## Purpose

This document provides **ready-to-use communication templates** for notifying internal teams, SDK consumers, and stakeholders about the attribution enforcement rollout.

---

## 1. Initial Announcement (Pre-Shadow Mode)

### Email / Slack Announcement

**Subject:** [ACTION REQUIRED] AOS SDK Attribution Enforcement — Phase 3 Rollout

---

**To:** All SDK Consumers, Service Owners, Platform Team

**Date:** [DATE]

---

**TL;DR:**
Starting [SHADOW_MODE_DATE], all runs created via the AOS SDK must include proper attribution (agent_id, actor_type, origin_system_id). We're rolling this out in phases to avoid disruption.

---

**What's Changing:**

Every run must now include:

| Field | Requirement | Example |
|-------|-------------|---------|
| `agent_id` | REQUIRED | `"agent-payment-processor"` |
| `actor_type` | REQUIRED | `"SYSTEM"`, `"HUMAN"`, or `"SERVICE"` |
| `origin_system_id` | REQUIRED | `"payment-service-v2"` |
| `actor_id` | Required if `actor_type=HUMAN` | `"user_12345"` |

---

**Rollout Timeline:**

| Phase | Date | Behavior |
|-------|------|----------|
| Shadow Mode | [SHADOW_DATE] | Violations logged, NOT rejected |
| Soft Fail | [SOFT_DATE] | Violations rejected (override available) |
| Hard Fail | [HARD_DATE] | All violations rejected, no overrides |

---

**What You Need To Do:**

1. **Check if you create runs via the SDK**
   - Search your code for `create_run`, `AOSClient`, or `/api/v1/runs`

2. **Update your run creation calls**
   ```python
   # Before (will fail after enforcement)
   client.create_run(goal="Process data")

   # After (compliant)
   client.create_run(
       goal="Process data",
       agent_id="my-agent-name",
       actor_type="SYSTEM",
       origin_system_id="my-service-name",
   )
   ```

3. **Test during shadow mode**
   - Watch for warnings in your logs
   - Fix any violations before soft fail

---

**Questions?**
- Slack: #aos-sdk-support
- Docs: [LINK TO SDK_ATTRIBUTION_ENFORCEMENT.md]
- Office Hours: [DATE/TIME]

---

**Why This Matters:**

Attribution enables:
- Cost accountability per agent
- Incident ownership tracking
- Governance compliance
- Accurate analytics

Runs without attribution cannot be trusted for business decisions.

---

### Slack Channel Post

```
:rotating_light: *Attribution Enforcement Rollout — Phase 3* :rotating_light:

Starting *[SHADOW_DATE]*, all AOS runs must include proper attribution.

*Timeline:*
• Shadow Mode: [SHADOW_DATE] (log only)
• Soft Fail: [SOFT_DATE] (reject with override)
• Hard Fail: [HARD_DATE] (no exceptions)

*Required fields:*
• `agent_id` — your agent's identifier
• `actor_type` — SYSTEM | HUMAN | SERVICE
• `origin_system_id` — your service name

*Action needed:*
1. Update your SDK calls
2. Watch for shadow mode warnings
3. Fix before soft fail

Docs: [LINK]
Questions: Reply here or #aos-sdk-support
```

---

## 2. Shadow Mode Start Notification

### Email / Slack

**Subject:** Attribution Enforcement — Shadow Mode Now Active

---

**Shadow mode is now live.**

Starting today, we're logging attribution violations (but NOT rejecting runs).

**What to check:**

1. Your service logs for `attribution_validation_failed` warnings
2. Dashboard: [LINK TO GRAFANA DASHBOARD]
3. Your runs in the "Shadow Violations" panel

**If you see violations:**
- Update your code before [SOFT_FAIL_DATE]
- Use the convenience methods: `create_system_run()`, `create_human_run()`

**Timeline reminder:**
- Today: Shadow mode (logging)
- [SOFT_DATE]: Soft fail (rejections begin)
- [HARD_DATE]: Hard fail (no overrides)

Questions? #aos-sdk-support

---

## 3. Soft Fail Transition Notice

### Email / Slack

**Subject:** [IMPORTANT] Attribution Enforcement — Soft Fail Mode Starting [DATE]

---

**As of [SOFT_FAIL_DATE], invalid attribution will cause run creation to FAIL.**

---

**What's changing:**

| Before (Shadow Mode) | After (Soft Fail) |
|---------------------|-------------------|
| Violations logged | Violations REJECTED |
| Runs still created | Runs NOT created |
| No impact | Your service may break |

---

**If you're not ready:**

You can temporarily use the override flag:

```bash
export AOS_ALLOW_ATTRIBUTION_LEGACY=true
```

**Warning:** Override usage is logged and must be removed by [HARD_FAIL_DATE].

---

**Status of your services:**

We've identified the following services with violations during shadow mode:

| Service | Violation Count | Status |
|---------|----------------|--------|
| [SERVICE_1] | [COUNT] | [FIXED/PENDING] |
| [SERVICE_2] | [COUNT] | [FIXED/PENDING] |

If your service is listed and you haven't fixed it, contact us immediately.

---

**Hard fail deadline:** [HARD_FAIL_DATE]

After this date, no overrides will be accepted.

---

## 4. Hard Fail Transition Notice

### Email / Slack

**Subject:** Attribution Enforcement — Hard Fail Mode Active

---

**As of today, all runs MUST have valid attribution. No exceptions.**

---

**What this means:**

- Missing `agent_id` → Run rejected
- Missing `actor_type` → Run rejected
- `HUMAN` without `actor_id` → Run rejected
- Legacy sentinel values (`legacy-unknown`) → Run rejected
- Override flag → **No longer honored**

---

**If your runs are failing:**

1. Check the error code in the response
2. Update your code per the [SDK docs](LINK)
3. Deploy immediately

**Common fixes:**

```python
# ATTR_AGENT_MISSING
→ Add agent_id="your-agent-name"

# ATTR_ACTOR_TYPE_MISSING
→ Add actor_type="SYSTEM" (or HUMAN/SERVICE)

# ATTR_ACTOR_ID_REQUIRED
→ Add actor_id="user_xyz" (for HUMAN actors)

# ATTR_ORIGIN_SYSTEM_MISSING
→ Add origin_system_id="your-service-name"
```

---

**Monitoring:**

We are actively monitoring for violations. Any runs entering the system with legacy markers will trigger an **immediate incident**.

Dashboard: [LINK]

---

## 5. Service-Specific Outreach

### Direct Message to Non-Compliant Service Owner

**Subject:** [URGENT] Your service [SERVICE_NAME] has attribution violations

---

Hi [NAME],

Your service **[SERVICE_NAME]** is creating runs without proper attribution.

**Violation details:**
- Error code: [ERROR_CODE]
- Violation count (last 24h): [COUNT]
- First seen: [TIMESTAMP]
- Most recent: [TIMESTAMP]

**Current phase:** [SHADOW/SOFT/HARD]

**Impact if not fixed:**
- Soft fail ([DATE]): Runs will be rejected
- Hard fail ([DATE]): No override available

---

**How to fix:**

```python
# Your current code (approximate):
client.create_run(goal="...")

# Required change:
client.create_run(
    goal="...",
    agent_id="[SUGGESTED_AGENT_ID]",
    actor_type="SYSTEM",  # or HUMAN/SERVICE
    origin_system_id="[SERVICE_NAME]",
)
```

---

**Need help?**
- Reply to this message
- Slack: #aos-sdk-support
- Office hours: [DATE/TIME]

Please confirm receipt and provide an ETA for the fix.

---

## 6. Post-Enforcement Status Update

### Weekly Rollout Status Email

**Subject:** Attribution Enforcement — Weekly Status Update [WEEK]

---

**Rollout Status: [PHASE]**

---

**Metrics Summary:**

| Metric | Value | Trend |
|--------|-------|-------|
| Validation success rate | [X]% | [UP/DOWN/STABLE] |
| Total violations (7d) | [COUNT] | [TREND] |
| Override usage | [COUNT] | [TREND] |
| Legacy bucket growth | [COUNT] | Should be 0 |

---

**Services Status:**

| Service | Status | Notes |
|---------|--------|-------|
| [SERVICE_1] | Compliant | Fixed [DATE] |
| [SERVICE_2] | Compliant | Fixed [DATE] |
| [SERVICE_3] | Using Override | Deadline [DATE] |
| [SERVICE_4] | Violations | Escalated |

---

**Upcoming Milestones:**

- [DATE]: Soft fail begins
- [DATE]: Override flag disabled
- [DATE]: Hard fail enforcement complete

---

**Action Items:**

- [TEAM_1]: Complete migration by [DATE]
- [TEAM_2]: Remove override flag by [DATE]
- Platform: Monitor legacy bucket for breaches

---

## 7. Incident Communication (If Enforcement Breach)

### Incident Notification

**Subject:** [INCIDENT] Attribution Enforcement Breach Detected

**Severity:** P1 (Critical)

---

**Summary:**
New runs with legacy attribution markers detected after enforcement date.

**Details:**
- First detection: [TIMESTAMP]
- Affected runs: [COUNT]
- Origin system: [ORIGIN_SYSTEM_ID]
- Agent: [AGENT_ID]

**Impact:**
- Analytics integrity compromised
- LIVE-O5 "By Agent" data polluted
- Governance violation

**Immediate Actions Taken:**
1. [ACTION_1]
2. [ACTION_2]

**Root Cause:** [PENDING/IDENTIFIED]

**Resolution Status:** [IN PROGRESS/RESOLVED]

---

**Timeline:**
- [TIME]: Breach detected
- [TIME]: On-call paged
- [TIME]: Source identified
- [TIME]: Remediation started
- [TIME]: Breach stopped

---

**Follow-up Required:**
- [ ] Root cause analysis
- [ ] Runbook update
- [ ] Additional guardrails

---

## 8. FAQ for Consumers

### Common Questions

**Q: Why do I need to change my code?**
A: Attribution enables cost accountability, incident ownership, and governance compliance. Without it, we cannot determine who or what created a run.

**Q: What if I don't know my agent_id?**
A: Use a descriptive identifier for the software component creating runs. Examples: `"payment-processor"`, `"report-generator"`, `"user-assistant"`.

**Q: What's the difference between SYSTEM and SERVICE?**
A:
- `SYSTEM`: Automated processes (cron jobs, schedulers, policy triggers)
- `SERVICE`: Service-to-service calls (internal APIs, workers calling other services)
- `HUMAN`: User-initiated actions (requires actor_id)

**Q: Can I use the same agent_id for different services?**
A: No. Each distinct software component should have its own agent_id for accurate attribution.

**Q: What if my automation runs on behalf of a user?**
A: If a user explicitly triggers the action, use `actor_type="HUMAN"` with their `actor_id`. If it's scheduled or automated (even if configured by a user), use `actor_type="SYSTEM"`.

**Q: The override flag isn't working anymore. What do I do?**
A: After hard fail, overrides are disabled. You must update your code. Contact #aos-sdk-support for urgent assistance.

**Q: How do I test my changes?**
A: During shadow mode, create test runs and check logs for `attribution_validation_failed` warnings. If none appear, you're compliant.

---

## 9. Calendar of Communications

| Date | Event | Communication |
|------|-------|---------------|
| T-14 days | Initial announcement | Section 1 |
| T-0 | Shadow mode starts | Section 2 |
| T+7 days | Shadow mode status | Section 6 |
| T+14 days | Soft fail warning | Section 3 |
| T+21 days | Soft fail starts | Direct outreach (Section 5) |
| T+28 days | Hard fail warning | Section 4 |
| T+35 days | Hard fail active | Section 4 |
| Weekly | Status updates | Section 6 |
| As needed | Incidents | Section 7 |

---

## 10. Communication Channels

| Channel | Purpose | Owner |
|---------|---------|-------|
| #aos-sdk-support | Questions, help requests | Platform Team |
| #aos-announcements | Official announcements | Platform Lead |
| Email: sdk-updates@ | Formal notifications | Platform Team |
| Grafana Dashboard | Real-time status | Self-serve |
| Office Hours | Live Q&A | [SCHEDULE] |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `SDK_ATTRIBUTION_ENFORCEMENT.md` | Technical implementation |
| `SDK_ATTRIBUTION_ALERTS.md` | Monitoring and alerts |
| `ATTRIBUTION_ARCHITECTURE.md` | Contract chain |
| `LEGACY_DATA_DISCLAIMER_SPEC.md` | Legacy handling |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
