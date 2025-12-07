# Pending To-Do Index

**Project:** AOS / Agenticverz 2.0
**Last Updated:** 2025-12-07
**Purpose:** Quick reference for all pending polishing and tech debt tasks

---

## How to Use This Index

1. Check this file at the start of polishing sessions
2. Pick tasks by priority (P1 > P2 > P3)
3. Mark tasks complete in the source PIN
4. Update this index when adding new pending items

---

## Priority Legend

| Priority | Meaning | Timeline |
|----------|---------|----------|
| **P1** | Address soon | Within 1-2 sessions |
| **P2** | Next sprint | Within 1-2 weeks |
| **P3** | Future | When bandwidth allows |

---

## Active Pending Tasks

### From PIN-047 (Polishing Tasks - 2025-12-07)

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| P1 | Reload Prometheus for new alerts | Ops | Pending |
| P1 | Verify embedding alerts in Alertmanager | Ops | Pending |
| P1 | Move GITHUB_TOKEN to Vault | Security | Pending |
| P1 | Move SLACK_MISMATCH_WEBHOOK to Vault | Security | Pending |
| P1 | Move POSTHOG_API_KEY to Vault | Security | Pending |
| P1 | Move RESEND_API_KEY to Vault | Security | Pending |
| P1 | Move TRIGGER_API_KEY to Vault | Security | Pending |
| P1 | Move CLOUDFLARE_API_TOKEN to Vault | Security | Pending |
| P2 | Create quota status API endpoint | Feature | Pending |
| P2 | Test quota exhaustion scenarios | Testing | Pending |
| P2 | Create embedding cost dashboard | Observability | Pending |
| P3 | Implement Anthropic Voyage backup | Resilience | Pending |
| P3 | Add embedding cache layer | Performance | Pending |
| P3 | Optimize HNSW index parameters | Performance | Pending |

### From PIN-036 (Infrastructure Pending - 2025-12-06)

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| P2 | S3/Object Storage for failure catalog | M9 Dep | Pending |
| P2 | Email transactional provider | M11 Dep | Pending |
| P3 | Demo screencast for landing page | Marketing | Pending |

### From PIN-029 (Infra Hardening - 2025-12-04)

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| P2 | Deploy worker buffering to production | Deployment | Pending |
| P2 | Verify TOCTOU fix in CI | Testing | Pending |

---

## Completed Tasks (Archive)

Move completed tasks here with completion date:

| Date | Task | PIN |
|------|------|-----|
| 2025-12-07 | Add OPENAI_API_KEY to Vault | PIN-046 |
| 2025-12-07 | Create embedding Prometheus alerts | PIN-046 |
| 2025-12-07 | Add daily quota guard | PIN-046 |
| 2025-12-07 | Complete embedding backfill (68/68) | PIN-046 |

---

## Quick Stats

| Category | P1 | P2 | P3 | Total |
|----------|----|----|----|----|
| Security | 6 | 0 | 0 | 6 |
| Ops | 2 | 0 | 0 | 2 |
| Feature | 0 | 1 | 0 | 1 |
| Testing | 0 | 1 | 0 | 1 |
| Observability | 0 | 1 | 0 | 1 |
| Performance | 0 | 0 | 2 | 2 |
| Resilience | 0 | 0 | 1 | 1 |
| Deployment | 0 | 1 | 0 | 1 |
| M9/M11 Deps | 0 | 2 | 0 | 2 |
| Marketing | 0 | 0 | 1 | 1 |
| **Total** | **8** | **6** | **4** | **18** |

---

## Session Workflow

When starting a polishing session:

```bash
# 1. Check this index
cat docs/memory-pins/PENDING-TODO-INDEX.md

# 2. Pick P1 tasks first
# 3. Work through tasks
# 4. Update source PIN with completion
# 5. Move to Completed Tasks section here
# 6. Commit changes
```

---

## Related Files

| File | Purpose |
|------|---------|
| `docs/memory-pins/INDEX.md` | Main PIN index |
| `docs/memory-pins/PIN-047-pending-polishing-tasks.md` | Current polishing backlog |
| `docs/memory-pins/PIN-036-infrastructure-pending.md` | Infrastructure dependencies |
| `agentiverz_mn/` | M8 working environment |
