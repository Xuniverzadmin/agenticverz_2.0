# PIN-243: L6 Platform Substrate Subdivision

**Status:** DESIGNED (Paper Only)
**Created:** 2025-12-30
**Category:** Architecture / Layer Governance
**Related:** PIN-240 (Seven-Layer Model), PIN-242 (Baseline Freeze)

---

## Purpose

L6 is currently **overloaded** with ~380 files spanning multiple concerns. This PIN defines **subdomains** to reduce cognitive load — **without moving any code yet**.

---

## L6 Subdivision Model

```
L6 — Platform Substrate
├── L6a — Auth & Identity
├── L6b — Data Persistence
├── L6c — Memory & Embeddings
├── L6d — Messaging & Events
├── L6e — Skills & Execution
├── L6f — Observability
└── L6g — Utilities & Helpers
```

---

## Subdomain Definitions

### L6a — Auth & Identity (13 files)

**Directory:** `app/auth/`

**Files:**
- `console_auth.py` — Console token verification
- `jwt_auth.py` — JWT handling
- `rbac.py` — RBAC core
- `rbac_engine.py` — Role-based access control engine
- `rbac_middleware.py` — FastAPI middleware
- `role_mapping.py` — Role definitions
- `tenant_auth.py` — Tenant authentication
- `tier_gating.py` — Tier/plan gating
- `clerk_provider.py` — Clerk OAuth
- `oauth_providers.py` — OAuth abstractions
- `oidc_provider.py` — OIDC support
- `shadow_audit.py` — Shadow mode audit

**Role:** Who can access what. Never knows about products or domain logic.

---

### L6b — Data Persistence (12+ files)

**Directories:** `app/models/`, `app/stores/`, `app/storage/`

**Files:**
- `db.py` — SQLModel engine, session management
- `db_async.py` — Async session support
- `db_helpers.py` — DB utilities
- `models/*.py` — All SQLModel definitions
- `stores/checkpoint_offload.py` — Checkpoint storage
- `stores/health.py` — Health checks for stores
- `storage/artifact.py` — Artifact storage (R2)

**Role:** How data is stored and retrieved. Schema is defined here, not usage.

---

### L6c — Memory & Embeddings (10 files)

**Directory:** `app/memory/`

**Files:**
- `memory_service.py` — Memory operations
- `vector_store.py` — pgvector operations
- `embedding_cache.py` — Embedding caching
- `embedding_metrics.py` — Embedding Prometheus metrics
- `iaec.py` — Instruction-Aware Embedding Composer
- `retriever.py` — Semantic retrieval
- `store.py` — Memory store abstraction
- `drift_detector.py` — Memory drift detection
- `update_rules.py` — Memory update rules

**Role:** Vector storage and semantic memory. Provides embedding infrastructure.

---

### L6d — Messaging & Events (6 files)

**Directories:** `app/events/`, `app/secrets/`

**Files:**
- `events/publisher.py` — Event publisher abstraction
- `events/redis_publisher.py` — Redis Pub/Sub
- `events/nats_adapter.py` — NATS adapter
- `secrets/vault_client.py` — HashiCorp Vault client
- `config/secrets.py` — Secret resolution

**Role:** How components communicate and access secrets.

---

### L6e — Skills & Execution (20+ files)

**Directory:** `app/skills/`

**Files:**
- `base.py` — Skill base class
- `executor.py` — Skill execution engine
- `registry.py`, `registry_v2.py` — Skill registration
- All skill implementations: `llm_invoke.py`, `http_call.py`, `email_send.py`, etc.
- `contracts/` — Skill contracts

**Role:** What capabilities exist and how to invoke them.

---

### L6f — Observability (3+ files)

**Files:**
- `metrics.py` — Prometheus metrics definitions
- `logging_config.py` — Logging setup
- `app/utils/metrics_helpers.py` — Metrics helpers

**Role:** How the system is monitored.

---

### L6g — Utilities & Helpers (15 files)

**Directory:** `app/utils/`

**Files:**
- `canonical_json.py` — Deterministic JSON
- `deterministic.py` — Determinism helpers
- `budget_tracker.py` — Budget tracking
- `rate_limiter.py` — Rate limiting
- `guard_cache.py` — Caching for guard
- `concurrent_runs.py` — Concurrency controls
- `idempotency.py` — Idempotency handling
- `input_sanitizer.py` — Input sanitization
- `runtime.py` — Runtime utilities (UUID, clock)
- `plan_inspector.py` — Plan validation
- `schema_parity.py` — Schema parity checks
- `webhook_verify.py` — Webhook verification

**Role:** Shared helpers that don't fit elsewhere. Keep this minimal.

---

## Subdivision Ownership Matrix

| Subdomain | File Count | Status |
|-----------|------------|--------|
| L6a — Auth & Identity | 13 | Well-bounded |
| L6b — Data Persistence | 12 | Well-bounded |
| L6c — Memory & Embeddings | 10 | Well-bounded |
| L6d — Messaging & Events | 6 | Well-bounded |
| L6e — Skills & Execution | 20+ | Needs review |
| L6f — Observability | 3 | Minimal, OK |
| L6g — Utilities | 15 | Watch for bloat |

---

## Cross-Subdomain Rules

1. **L6a (Auth) is called by all layers** — This is expected
2. **L6b (Data) is called by L4-L6** — Never by L1-L2
3. **L6c (Memory) is called by L4-L5** — Domain engines and workers
4. **L6d (Events) is called by L4-L5** — Publishing from execution
5. **L6e (Skills) is called by L5 only** — Workers execute skills
6. **L6f (Observability) can be called from anywhere** — Metrics are cross-cutting
7. **L6g (Utils) should be shrinking** — Move specialized utils to subdomains

---

## Future Considerations (NOT for now)

When/if we move to directory grouping:

```
backend/
└── l6_platform/
    ├── l6a_auth/
    ├── l6b_persistence/
    ├── l6c_memory/
    ├── l6d_messaging/
    ├── l6e_skills/
    ├── l6f_observability/
    └── l6g_utils/
```

**NOT TO BE DONE YET** — This is design documentation only.

---

## Mental Model

```
┌──────────────────────────────────────────────────────────────┐
│                    L6 — Platform Substrate                    │
├───────────────┬───────────────┬───────────────┬──────────────┤
│ L6a Auth      │ L6b Data      │ L6c Memory    │ L6d Events   │
│ (13 files)    │ (12 files)    │ (10 files)    │ (6 files)    │
├───────────────┼───────────────┼───────────────┴──────────────┤
│ L6e Skills    │ L6f Metrics   │ L6g Utils (SHRINK OVER TIME) │
│ (20+ files)   │ (3 files)     │ (15 files)                   │
└───────────────┴───────────────┴──────────────────────────────┘
```

---

## What This Enables

1. **Reduced cognitive load** — Understand L6 via 7 subdomains, not 380 files
2. **Clearer boundaries** — Know which subdomain to look in
3. **Future refactoring target** — If we ever split directories
4. **Import analysis** — Can detect subdomain violations

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial design. Paper only — no code moves. |
