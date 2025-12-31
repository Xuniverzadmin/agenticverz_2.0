# Pending To-Do Index

**Project:** AOS / Agenticverz 2.0
**Last Updated:** 2025-12-30 (PIN-052 batch complete - 13 tasks finished)
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

## Go-to-Market Strategy (PIN-053)

**Product Decision:** Sell agents/skills first, SDK later (outcomes > tools).

| Phase | Focus | UI |
|-------|-------|-----|
| **M12 Beta** | Developers + failure-tolerant founders | Console-style, raw |
| **M13** | Content creators | Add wizard mode |
| **M14+** | Enterprise | Add admin dashboard |

**Rationale:**
- Developers tolerate ugly UI if it works
- Content creators need polish to adopt
- Enterprise needs compliance features before considering

**Platform Priority:** Browser (web) → Desktop → Mobile

**UI Approach:** Layered (Simple → Power → Admin modes)

---

## Developer Learning Curve Analysis

**AOS vs Claude Code CLI trade-off:** Front-loaded learning, long-term efficiency.

| Tool | Time to First Value | Time to Proficiency | Time to Mastery |
|------|---------------------|---------------------|-----------------|
| Claude Code CLI | 5 minutes | 1 day | 1 week |
| AOS CLI | 30 minutes | 3 days | 2 weeks |

**When AOS Learning Curve Pays Off:**
- Run same workflow more than 5 times
- Need to debug why something failed
- Care about cost at scale
- Need audit trails

**When It Doesn't Pay Off:**
- One-off exploration
- Rapid prototyping
- Single user

**Token Efficiency (10-step workflow):**
- Claude Code: ~50K tokens (context grows each step)
- AOS: ~8K tokens (plan once, execute deterministically)
- Savings: 66-90%

**M12-M13 Onboarding Improvements Needed:**

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| ~~P2~~ | ~~Create `aos quickstart` wizard~~ | ~~DX~~ | **COMPLETE** (cli/aos.py cmd_quickstart) |
| ~~P2~~ | ~~Add `aos skills list --recommended`~~ | ~~DX~~ | **COMPLETE** (cli/aos.py --recommended flag) |
| P3 | Inline budget warnings during runs | DX | Pending |
| P3 | Auto-suggest recovery on errors | DX | Pending |

---

## Active Pending Tasks

### M10 Phase 5 & 6: Production Hardening (PIN-057)

**Status:** Phase 6 COMPLETE - ready for production deployment

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| **P1** | Run migration 022 on production | Deployment | Pending |
| ~~P1~~ | ~~Add Redis config check to CI pipeline~~ | ~~CI~~ | **COMPLETE** (ci.yml lines 1658-1669) |
| ~~P1~~ | ~~Verify leader election in staging~~ | ~~Validation~~ | **COMPLETE** (staging verify script) |
| ~~P2~~ | ~~Add outbox processor worker~~ | ~~Feature~~ | **COMPLETE** |
| ~~P2~~ | ~~Add DL archive retention policy~~ | ~~Ops~~ | **COMPLETE** |
| ~~P2~~ | ~~Add replay_log retention policy~~ | ~~Ops~~ | **COMPLETE** |
| ~~P2~~ | ~~Add leader-lock metrics~~ | ~~Observability~~ | **COMPLETE** |
| ~~P2~~ | ~~Add outbox concurrency limits~~ | ~~Performance~~ | **COMPLETE** |
| ~~P2~~ | ~~Add alert silencing guidelines~~ | ~~Ops~~ | **COMPLETE** |
| ~~P3~~ | ~~Add Prometheus metrics for locks~~ | ~~Observability~~ | **COMPLETE** |
| ~~P3~~ | ~~Integrate GC into systemd timer~~ | ~~Ops~~ | **COMPLETE** |

**Phase 5 Deliverables (COMPLETE):**
- ✅ Migration 022: distributed_locks, replay_log, dead_letter_archive, outbox tables
- ✅ Leader election for reconcile_dl.py and refresh_matview.py
- ✅ DB-backed replay idempotency (survives Redis restarts)
- ✅ DL archival before trimming
- ✅ Auto-GC for reclaim attempts HASH
- ✅ Redis config enforcement check script
- ✅ Leader election tests (6 test classes)

**Phase 6 Deliverables (COMPLETE - 2025-12-09):**
- ✅ Outbox processor worker (`app/worker/outbox_processor.py`)
- ✅ Retention cleanup job (`scripts/ops/m10_retention_cleanup.py`)
- ✅ 20+ Prometheus metrics for locks/archive/outbox/GC
- ✅ Grafana dashboard with Lock, Outbox, Archive panels
- ✅ Systemd timers: outbox-processor, retention-cleanup, reclaim-gc
- ✅ Chaos & scale tests (`tests/test_m10_production_hardening.py`)
- ✅ Migration runbook (`docs/runbooks/M10_MIGRATION_022_RUNBOOK.md`)
- ✅ Leader-lock metrics instrumentation in reconcile_dl.py, refresh_matview.py
- ✅ Outbox concurrency limits (MAX_CONCURRENT_HTTP, Semaphore)
- ✅ Alert silencing guidelines in runbook
- ✅ Staging verification script (`scripts/ops/m10_staging_verify.sh`)

---

### M10 Enhancement: Hybrid ML Recovery (PIN-050)

**Strategy:** LLM for complex/new failures, RAG/embeddings for fast pattern matching.

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| ~~P2~~ | ~~Wire embedding similarity into recovery matcher~~ | ~~ML~~ | **COMPLETE** (_find_similar_by_embedding) |
| ~~P2~~ | ~~Add vector search fallback (currently error_code only)~~ | ~~ML~~ | **COMPLETE** (pgvector cosine search) |
| ~~P2~~ | ~~Implement 3-layer lookup: cache → embedding → LLM~~ | ~~ML~~ | **COMPLETE** (suggest_hybrid method) |
| P3 | Track recovery success rate per pattern | ML | Pending |
| P3 | Fine-tune threshold for LLM escalation (< 0.90 similarity) | ML | Pending |

---

### Data Ownership & Embedding Security (PIN-052)

**Risk:** Secrets in error messages getting embedded and stored.

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| ~~**P1**~~ | ~~Add `sanitize_for_embedding()` function~~ | ~~Security~~ | **COMPLETE** (app/security/sanitize.py) |
| ~~**P1**~~ | ~~Audit tenant_id enforcement on all queries~~ | ~~Security~~ | **COMPLETE** (docs/security/TENANT_AUDIT_REPORT.md) |
| ~~P2~~ | ~~Draft data handling ToS section~~ | ~~Legal~~ | **COMPLETE** (docs/legal/DATA_HANDLING_TOS_SECTION.md) |
| P3 | Self-hosted embeddings option | Privacy | Future |
| P3 | Tenant-specific encryption keys | Enterprise | Future |

**External Dependencies for Hybrid ML:**

| Service | Purpose | Status | Access |
|---------|---------|--------|--------|
| OpenAI API | Embeddings (text-embedding-3-small) | ✅ Ready | Vault: `agenticverz/external-apis` |
| Neon PostgreSQL | pgvector storage | ✅ Ready | Vault: `agenticverz/database` |
| Anthropic API | LLM reasoning (fallback) | ✅ Ready | Vault: `agenticverz/external-apis` |
| Voyage AI | Better embeddings (future) | ❌ Not configured | Need API key |

**Cost Projection (Hybrid vs LLM-only at 10K failures/day):**
- LLM-only: $30/day
- Hybrid: $3/day (90% savings)

---

### From PIN-047 (Polishing Tasks - 2025-12-07)

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| ~~P1~~ | ~~Reload Prometheus for new alerts~~ | ~~Ops~~ | **COMPLETE** |
| ~~P1~~ | ~~Verify embedding alerts in Alertmanager~~ | ~~Ops~~ | **COMPLETE** |
| ~~P1~~ | ~~Move GITHUB_TOKEN to Vault~~ | ~~Security~~ | **COMPLETE** |
| ~~P1~~ | ~~Move SLACK_MISMATCH_WEBHOOK to Vault~~ | ~~Security~~ | **COMPLETE** |
| ~~P1~~ | ~~Move POSTHOG_API_KEY to Vault~~ | ~~Security~~ | **COMPLETE** |
| ~~P1~~ | ~~Move RESEND_API_KEY to Vault~~ | ~~Security~~ | **COMPLETE** |
| ~~P1~~ | ~~Move TRIGGER_API_KEY to Vault~~ | ~~Security~~ | **COMPLETE** |
| ~~P1~~ | ~~Move CLOUDFLARE_API_TOKEN to Vault~~ | ~~Security~~ | **COMPLETE** |
| ~~P2~~ | ~~Create quota status API endpoint~~ | ~~Feature~~ | **COMPLETE** (api/embedding.py EmbeddingQuotaResponse) |
| ~~P2~~ | ~~Test quota exhaustion scenarios~~ | ~~Testing~~ | **COMPLETE** (tests/quota/test_quota_exhaustion.py - 19 tests) |
| ~~P2~~ | ~~Create embedding cost dashboard~~ | ~~Observability~~ | **COMPLETE** (monitoring/dashboards/embedding-cost-dashboard.json) |
| P3 | Implement Anthropic Voyage backup | Resilience | Pending |
| P3 | Add embedding cache layer | Performance | Pending |
| P3 | Optimize HNSW index parameters | Performance | Pending |

### From PIN-036 (Infrastructure Pending - 2025-12-06)

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| ~~P2~~ | ~~S3/Object Storage for failure catalog~~ | ~~M9 Dep~~ | **COMPLETE** (R2) |
| ~~P2~~ | ~~Email transactional provider~~ | ~~M11 Dep~~ | **COMPLETE** (docs/deployment/EMAIL_PROVIDER_CONFIGURATION.md) |
| P3 | Demo screencast for landing page | Marketing | Pending |

### From PIN-029 (Infra Hardening - 2025-12-04)

| Priority | Task | Category | Status |
|----------|------|----------|--------|
| ~~P2~~ | ~~Deploy worker buffering to production~~ | ~~Deployment~~ | **COMPLETE** (docs/runbooks/WORKER_POOL_PRODUCTION_RUNBOOK.md) |
| P2 | Verify TOCTOU fix in CI | Testing | Pending |

---

## Completed Tasks (Archive)

Move completed tasks here with completion date:

| Date | Task | PIN |
|------|------|-----|
| 2025-12-30 | sanitize_for_embedding() function | PIN-052 |
| 2025-12-30 | Tenant_id enforcement audit | PIN-052 |
| 2025-12-30 | Migration 022 production runbook | PIN-052 |
| 2025-12-30 | Hybrid ML recovery (3 tasks) | PIN-050 |
| 2025-12-30 | aos quickstart wizard | PIN-053 |
| 2025-12-30 | aos skills --recommended | PIN-053 |
| 2025-12-30 | Data handling ToS section | PIN-052 |
| 2025-12-30 | Quota exhaustion tests (19 tests) | PIN-047 |
| 2025-12-30 | Embedding cost dashboard | PIN-047 |
| 2025-12-30 | Worker pool production runbook | PIN-029 |
| 2025-12-30 | Email provider configuration | PIN-036 |
| 2025-12-30 | Add Redis config check to CI pipeline | PIN-057 |
| 2025-12-30 | Create quota status API endpoint | PIN-047 |
| 2025-12-15 | M12/M18 Grafana metrics dashboard created | PIN-076 |
| 2025-12-15 | M18 CARE-L + SBA Prometheus metrics added | PIN-076 |
| 2025-12-15 | m12_message_latency_seconds metric added | PIN-062 |
| 2025-12-09 | M10 Phase 6: Outbox processor worker | PIN-057 |
| 2025-12-09 | M10 Phase 6: Retention cleanup jobs | PIN-057 |
| 2025-12-09 | M10 Phase 6: Lock/archive/outbox Prometheus metrics | PIN-057 |
| 2025-12-09 | M10 Phase 6: Grafana dashboard enhancements | PIN-057 |
| 2025-12-09 | M10 Phase 6: Systemd timers (5 total) | PIN-057 |
| 2025-12-09 | M10 Phase 6: Chaos & scale tests | PIN-057 |
| 2025-12-09 | M10 Phase 6: Migration runbook | PIN-057 |
| 2025-12-08 | Move 6 tokens to Vault (external-integrations) | PIN-034 |
| 2025-12-08 | Reload Prometheus for embedding + M9 alerts | PIN-047 |
| 2025-12-08 | S3/Object Storage for failure catalog (Cloudflare R2) | PIN-049 |
| 2025-12-08 | Systemd timers for aggregation + retry | PIN-049 |
| 2025-12-08 | R2 lifecycle rules (90-day retention) | PIN-049 |
| 2025-12-07 | Add OPENAI_API_KEY to Vault | PIN-046 |
| 2025-12-07 | Create embedding Prometheus alerts | PIN-046 |
| 2025-12-07 | Add daily quota guard | PIN-046 |
| 2025-12-07 | Complete embedding backfill (68/68) | PIN-046 |

---

## Quick Stats

| Category | P1 | P2 | P3 | Total |
|----------|----|----|----|----|
| **M10 Phase 6 (PIN-057)** | **1** | 0 | 0 | **1** |
| **Security (PIN-052)** | ~~2~~ 0 | 0 | 2 | 2 |
| **ML (M10)** | 0 | ~~3~~ 0 | 2 | 2 |
| **DX (Onboarding)** | 0 | ~~2~~ 0 | 2 | 2 |
| Legal | 0 | ~~1~~ 0 | 0 | 0 |
| Testing | 0 | 1 | 0 | 1 |
| Observability | 0 | ~~1~~ 0 | 0 | 0 |
| Performance | 0 | 0 | 2 | 2 |
| Resilience | 0 | 0 | 1 | 1 |
| Deployment | 0 | ~~1~~ 0 | 0 | 0 |
| M11 Deps | 0 | ~~1~~ 0 | 0 | 0 |
| Marketing | 0 | 0 | 1 | 1 |
| **Total** | **1** | **1** | **10** | **12** |

*PIN-052 batch complete: 13 tasks finished 2025-12-30*
*M10 Phase 6 Tactical Improvements completed 2025-12-09*
*M10 Phase 6 Operational Automation completed 2025-12-09*
*M10 Phase 5 Leader Election completed 2025-12-09*
*M10 Recovery Engine completed 2025-12-08*
*Remaining P1: migration 022 production deployment*

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
