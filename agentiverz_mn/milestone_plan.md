# M8-M14 Machine-Native Realignment - Milestone Plan

**Source:** PIN-033
**Status:** APPROVED
**Created:** 2025-12-05

---

## Timeline Summary

```
Week 1-2:   M8 (Demo + SDK + Auth)
Week 3-4:   M9 (Failure Persistence)
Week 5-6:   M10 (Recovery API + CLI)
Week 5-8:   M11 (Skill Expansion) [parallel with M10]
Week 9-10:  M12 (Beta Rollout)
Week 11-14: M13 (Console UI)
Month 4-7:  M14+ (Self-Improving Loop)
```

---

## Milestone Overview

| Milestone | Scope | Duration | Dependencies |
|-----------|-------|----------|--------------|
| **M8** | Demo + SDK Packaging + Auth Integration | 2 weeks | PIN-009 |
| **M9** | Failure Catalog v2 + Persistence + Metrics | 2 weeks | M8 |
| **M10** | Recovery Suggestion Engine (API + CLI) | 1.5 weeks | M9 |
| **M11** | Skill Expansion (KV, FS, Notifications) | 3 weeks | M8 |
| **M12** | Beta Rollout + Docs + Security | 2 weeks | M8, M9, M10, M11 |
| **M13** | Console UI + Recovery Review UI | 4 weeks | M12 |
| **M14+** | Self-Improving Loop | 2-4 months | M13 + 3mo production data |

---

## M8 — Demo + SDK Packaging + Auth Integration (2 Weeks)

### Acceptance Criteria

- [ ] RBAC uses REAL auth provider (no stub)
- [ ] `pip install aos-sdk` works
- [ ] `npm install @aos/sdk` works
- [ ] Running `python examples/btc_price_slack.py` works out-of-the-box
- [ ] Screencast recorded + added to repo
- [ ] New user can install + run examples in <10 minutes

### Key Activities

1. **Auth Integration** - Deploy real identity provider, wire AUTH_SERVICE_URL
2. **Python SDK** - pyproject.toml, PyPI publish
3. **JS/TS SDK** - package.json, TypeScript types, npm publish
4. **Demo** - BTC→Slack, JSON transform, HTTP retry demos
5. **Docs** - README, Quickstart, Demo links

---

## M9 — Failure Catalog v2 + Persistence (2 Weeks)

### Acceptance Criteria

- [ ] `failure_matches` table exists with Alembic migration
- [ ] All failure paths persist structured entries
- [ ] Dashboard shows failure patterns properly
- [ ] At least 5 unique catalog matches recorded during test traffic
- [ ] Aggregation job produces candidate JSON
- [ ] Metrics visible in Prometheus

### Key Activities

1. Create `failure_matches` table + migration
2. Modify `failure_catalog.match()` to persist
3. Add Prometheus metrics (hits, misses, recovery success)
4. Create nightly aggregation job
5. Add Grafana panels

---

## M10 — Recovery Suggestion Engine (1.5 Weeks)

### Acceptance Criteria

- [ ] Recovery API suggests corrections for at least 5 catalog entries
- [ ] CLI can list + approve suggestions
- [ ] `recovery_candidates` table populates
- [ ] Confidence scores vary based on historical data
- [ ] NO UI element (UI comes in M13)

### Key Activities

1. `POST /api/v1/recovery/suggest` endpoint
2. Confidence scoring model
3. `recovery_candidates` table
4. CLI commands: `aos recovery candidates/approve/reject`

---

## M11 — Skill Expansion (3 Weeks)

### Acceptance Criteria

- [ ] 3+ new skills available in registry
- [ ] Can build a 5-step workflow using new skills
- [ ] All skills deterministic under replay
- [ ] No escaping sandbox path in FS skill
- [ ] Slack/Email/Webhook send successfully in tests

### New Skills

1. **kv_store** - GET, SET, DELETE, EXISTS with TTL
2. **fs** - read, write, delete, list (sandboxed)
3. **slack_send** - Webhook + structured messages
4. **email_send** - SMTP + templates
5. **webhook_send** - Generic webhook + HMAC signing

---

## M12 — Beta Rollout (2 Weeks)

### Acceptance Criteria

- [ ] 10 users onboarded
- [ ] All used SDK successfully
- [ ] All can run demo flows
- [ ] No auth bypass or RBAC regression
- [ ] Complete documentation published

### Key Activities

1. Security review + audit
2. Complete documentation suite
3. User onboarding (10 beta users)
4. SLO definitions + alert routes

---

## M13 — Console UI (4 Weeks)

### Acceptance Criteria

- [ ] UI loads from browser
- [ ] Recovery suggestions reviewed visually
- [ ] Operators can accept/reject patterns
- [ ] No sensitive data visible to wrong roles
- [ ] Failure analytics functional

### Key Activities

1. Frontend framework (React/Svelte)
2. Recovery review UI
3. Failure analytics dashboard

---

## M14+ — Self-Improving Loop (2-4 Months)

### Prerequisites

- [ ] 3+ months of production failure data
- [ ] Stable recovery suggestion patterns
- [ ] Console UI for human oversight

### Acceptance Criteria

- [ ] System reduces failure rate over time
- [ ] Planner improves success rate without manual edits
- [ ] Drift alerts highlight regressions

---

## Success Metrics

| Milestone | Key Metric |
|-----------|------------|
| M8 | SDK installs from PyPI/npm |
| M9 | Failure match rate >80% |
| M10 | Recovery suggestions accepted >50% |
| M11 | 3+ workflows using new skills |
| M12 | 10 active beta users |
| M13 | Operators using console daily |
| M14+ | 10-20% failure rate reduction |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Auth provider setup delayed | Medium | High | Start M8 Day 1 with auth |
| TypeScript SDK takes longer | Medium | Medium | Parallel track, can defer npm |
| Insufficient failure data for M14 | High | Medium | Accept longer data collection |
| Console UI scope creep | High | Medium | Strict MVP scope |
| Beta user adoption slow | Medium | Low | Focus on 5 committed users |
