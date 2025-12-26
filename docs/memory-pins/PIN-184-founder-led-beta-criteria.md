# PIN-184: Founder-Led Beta - Success/Failure Criteria

**Status:** ACTIVE
**Category:** Operations / Beta / Exit Criteria
**Created:** 2025-12-26
**Milestone:** Runtime v1 Beta
**Related PINs:** PIN-183 (Feature Freeze), PIN-167 (Human Testing)

---

## Declaration

This document defines the exit criteria for Founder-Led Beta.

**Beta is NOT:**
- A time period (no "2 weeks")
- A feature list (feature freeze in effect)
- A polish phase (no dashboards, insights, automation)

**Beta IS:**
- Exposure to real usage patterns
- Observation of failure modes
- Validation of trust assumptions
- Collection of surfacing defects

---

## Beta Parameters

| Parameter | Value |
|-----------|-------|
| User count | 3-7 real users |
| User type | Founders/CTOs with real workloads |
| Duration | Until exit criteria met |
| Feature changes | Bug fixes only (per PIN-183) |
| Surfacing changes | Allowed (UI/docs, not semantics) |

---

## Success Criteria (ALL must pass)

### S1: Trust Formation

> Users can explain system behavior to a colleague without code access.

| Check | Method | Pass Condition |
|-------|--------|----------------|
| Post-run mental model | Interview | User correctly predicts next run behavior 80%+ |
| Failure explanation | Incident review | User identifies root cause without founder help |
| Boundary awareness | Question: "What can't this system do?" | User lists at least 2 true limitations |

**Evidence Required:**
- 3+ users pass all 3 checks
- No user claims capability system doesn't have

---

### S2: Failure Surfacing

> Failures become visible, not hidden.

| Check | Method | Pass Condition |
|-------|--------|----------------|
| Error visibility | Inject failure | Error appears in customer console within 60s |
| Budget violation | Exceed budget by 2x | Warning visible in CustomerLimitsPage |
| Policy violation | Trigger content policy | Incident created with clear explanation |
| Rate limit hit | Exhaust rate limit | UI shows remaining = 0, next reset time |

**Evidence Required:**
- All 4 failure types surface correctly
- No silent failures in 100+ runs

---

### S3: Contract Compliance

> All 4 contracts exercised without violation.

| Contract | Observable Effect | Pass Condition |
|----------|-------------------|----------------|
| PRE-RUN | CustomerRunsPage shows intent before execution | Intent visible for 90%+ runs |
| CONSTRAINT | CustomerLimitsPage shows active constraints | Constraints match declared budget |
| DECISION | FounderTimelinePage shows decision chain | Decisions traceable to outcomes |
| OUTCOME | CustomerRunsPage shows reconciled result | Outcome matches intent for success cases |

**Evidence Required:**
- 0 contract violations in 100+ runs
- Manual audit of 10 random runs confirms compliance

---

### S4: Operational Stability

> System runs reliably under real load.

| Metric | Threshold | Measurement |
|--------|-----------|-------------|
| Uptime | 99%+ | Over beta period |
| API latency p95 | <2s | Prometheus metrics |
| Error rate | <5% | Failed runs / total runs |
| Cost accuracy | ±20% | Estimated vs actual cost |

**Evidence Required:**
- Prometheus dashboard showing thresholds met
- No P0 incidents during beta

---

## Failure Criteria (ANY triggers fail)

### F1: Trust Violation

| Condition | Trigger |
|-----------|---------|
| User believed system could do X | System cannot do X |
| User couldn't explain failure | After viewing all available UI |
| Magic behavior accepted | User says "I don't know why but it works" |

**Response:** Document trust gap, add to P0 surfacing fixes

---

### F2: Hidden Failure

| Condition | Trigger |
|-----------|---------|
| Failure not visible in console | >60s after occurrence |
| User unaware of budget/rate issue | Until founder tells them |
| Error message meaningless | User cannot act on error |

**Response:** Document surfacing gap, fix before continuing

---

### F3: Contract Violation

| Condition | Trigger |
|-----------|---------|
| Run started without PRE-RUN declaration | Any occurrence |
| Constraint violated silently | Budget/rate exceeded without warning |
| Decision invisible | CARE/Recovery acted but not shown |
| Outcome unexplained | Final state cannot be traced to intent |

**Response:** Immediate beta pause, contract fix required

---

### F4: Operational Failure

| Condition | Trigger |
|-----------|---------|
| Downtime >1% | Cumulative over beta |
| P95 latency >5s | Sustained over 1 hour |
| Error rate >10% | Sustained over 1 hour |
| Cost accuracy >50% off | For any run |

**Response:** Investigate root cause, fix before resuming

---

## Beta Phases

### Phase 1: Onboarding (Users 1-2)

**Focus:** Can users onboard without founder hand-holding?

| Checkpoint | Evidence |
|------------|----------|
| API key creation | User creates key via CustomerKeysPage |
| First run | User creates workflow without Slack support |
| First incident | User investigates without code access |

**Exit:** 2 users complete first run independently

---

### Phase 2: Steady State (Users 3-5)

**Focus:** Does system behave predictably over time?

| Checkpoint | Evidence |
|------------|----------|
| 50+ runs across users | Prometheus data |
| 0 P0 incidents | Alert history |
| Users form correct habits | Interview |

**Exit:** 50 runs, 0 hidden failures

---

### Phase 3: Stress (Users 5-7)

**Focus:** How does system behave at edges?

| Checkpoint | Evidence |
|------------|----------|
| Budget exhaustion | User hits budget, system responds correctly |
| Rate limit exhaustion | User hits rate limit, system responds correctly |
| Concurrent usage | 3+ users active simultaneously |

**Exit:** All edge cases surface correctly

---

## Post-Beta Promotion Rules

### Promotion Checklist

- [ ] All 4 Success Criteria (S1-S4) passed
- [ ] 0 Failure Criteria (F1-F4) triggered
- [ ] All 3 Beta Phases completed
- [ ] PIN-184 signed off by founder

### What Unlocks After Beta

1. **Public Documentation** - API docs, getting started
2. **Self-Service Onboarding** - Without founder involvement
3. **Pricing Activation** - Billing enabled
4. **Marketing** - Can publicly reference product

### What Does NOT Unlock

- New features (feature freeze continues)
- Dashboards, insights, automation
- AI recommendations
- Customer recovery controls

---

## Observation Template

For each beta user, record:

```markdown
## Beta User: [Name/Company]

**Onboarded:** [Date]
**First Run:** [Date]
**Total Runs:** [Count]

### Trust Checks
- Mental model accuracy: PASS/FAIL
- Failure explanation: PASS/FAIL
- Boundary awareness: PASS/FAIL

### Failures Observed
- [List any hidden failures]
- [List any trust violations]

### Contract Compliance
- PRE-RUN visible: YES/NO
- CONSTRAINT shown: YES/NO
- DECISION traceable: YES/NO
- OUTCOME reconciled: YES/NO

### Quotes
> "[User verbatim quote about system]"

### Issues Found
- [Issue 1]
- [Issue 2]
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Initial creation after Runtime v1 feature freeze |
