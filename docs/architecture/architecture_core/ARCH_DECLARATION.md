# Architecture Declaration

**Version:** 1.0.0
**Generated:** 2026-01-02
**Status:** FROZEN
**Authority:** PIN-240 (Seven-Layer Codebase Mental Model)

---

## 1. Layer Model (Immutable)

The AOS architecture follows an 8-layer model. Layers 1-6 are runtime, 7-8 are operational.

| Layer | Name | Files | Components | Purpose |
|-------|------|------:|----------:|---------|
| L1 | Product Experience | - | - | Frontend consoles (external) |
| L2 | Product APIs | 34 | 693 | HTTP endpoints for L1 |
| L3 | Boundary Adapters | 27 | 98 | Auth, middleware, external wrappers |
| L4 | Domain Engines | 165 | 1130 | Business logic, system truth |
| L5 | Execution & Workers | 24 | 124 | Background job execution |
| L6 | Platform Substrate | 76 | 538 | DB, Redis, external services |
| L7 | Ops & Deployment | - | - | Systemd, Docker, infra |
| L8 | Catalyst / Meta | - | - | CI, tests, validators |

### Import Rules (Non-Negotiable)

| Layer | Allowed Imports |
|-------|-----------------|
| L1 | L2 only |
| L2 | L3, L4, L6 |
| L3 | L4, L6 |
| L4 | L5, L6 |
| L5 | L6 only |
| L6 | None (terminal) |

---

## 2. Component Inventory by Layer

### L2 — Product APIs (34 files, 354 routes)

Core API domains exposing functionality to frontends:

| Domain | File | Routes | Purpose |
|--------|------|-------:|---------|
| agents | api/agents.py | 49 | Agent CRUD, strategy, reputation |
| policy_layer | api/policy_layer.py | 37 | Constitutional governance |
| guard | api/guard.py | 18 | Incident detection |
| integration | api/integration.py | 17 | Integration loop |
| cost_intelligence | api/cost_intelligence.py | 14 | Cost analytics |
| ops | api/ops.py | 14 | Founder operations |
| tenants | api/tenants.py | 14 | Multi-tenant management |
| recovery | api/recovery.py | 14 | M10 recovery engine |
| workers | api/workers.py | 12 | Worker execution |
| runtime | api/runtime.py | 9 | Machine-native runtime |

### L3 — Boundary Adapters (27 files)

| Component | Purpose | Constraint |
|-----------|---------|------------|
| AuthMiddleware | RBAC context extraction | < 200 LOC |
| RateLimitMiddleware | Token bucket rate limiting | Stateless |
| CorrelationMiddleware | Request correlation IDs | Pass-through |
| IdentityAdapters | JWT/API Key extraction | No business logic |
| ExternalServiceAdapters | LLM provider wrappers | Retry-aware |

### L4 — Domain Engines (165 files)

Core business logic organized by domain:

| Domain | Files | Key Components |
|--------|------:|----------------|
| services | 45 | Core service implementations |
| skills | 25 | Agent skill definitions |
| costsim | 15 | Cost simulation V2 |
| agents | 13 | Agent lifecycle, SBA |
| memory | 10 | Memory pin management |
| policy | 7 | Policy evaluation |
| routing | 5 | CARE routing engine |
| learning | 5 | CARE-L learning |
| optimization | 2 | Optimization engines |

### L5 — Execution & Workers (24 files)

| Component | Purpose |
|-----------|---------|
| WorkerRuntime | Execution orchestration |
| SkillExecutor | Skill invocation |
| OutboxProcessor | Durable event delivery |
| JobScheduler | Background job scheduling |

### L6 — Platform Substrate (76 files)

| Category | Files | Components |
|----------|------:|------------|
| models | 25 | SQLModel definitions |
| stores | 20 | Data access layers |
| db | 15 | Database utilities |
| infra | 10 | Infrastructure utilities |
| utils | 6 | Platform utilities |

---

## 3. Stable Contracts

### 3.1 L2 API Contracts (Frontend-Facing)

These endpoints are **versioned** and **stable**. Breaking changes require major version bump.

#### Authentication (v1)
```
POST /api/v1/onboarding/login/{provider}  → TokenResponse
POST /api/v1/onboarding/refresh           → TokenResponse
GET  /api/v1/onboarding/me                → UserProfile
POST /api/v1/onboarding/logout            → void
```

#### Worker Execution (v1)
```
POST /api/v1/workers/run                  → RunAccepted
GET  /api/v1/workers/runs/{run_id}        → RunStatus
GET  /api/v1/workers/stream/{run_id}      → SSE Stream
DELETE /api/v1/workers/runs/{run_id}      → void
```

#### Incidents (v1)
```
GET  /api/v1/guard/incidents              → IncidentList
GET  /api/v1/guard/incidents/{id}         → IncidentDetail
POST /api/v1/guard/incidents/{id}/ack     → void
GET  /api/v1/guard/incidents/{id}/timeline → Timeline
```

#### Cost Intelligence (v1)
```
GET  /api/v1/cost-intelligence/dashboard  → CostDashboard
GET  /api/v1/cost-intelligence/summary    → CostSummary
GET  /api/v1/cost-intelligence/anomalies  → AnomalyList
```

#### Recovery (v1 - M10)
```
GET  /api/v1/recovery/candidates          → CandidateList
GET  /api/v1/recovery/candidates/{id}     → CandidateDetail
POST /api/v1/recovery/approve             → RecoveryResult
GET  /api/v1/recovery/scopes/{incident_id} → ScopeList
```

### 3.2 L6 Infra Contracts

Infrastructure dependencies with conformance levels:

| Component | State | Conformance | Obligation |
|-----------|-------|-------------|------------|
| PostgreSQL | WIRED | C3 (Production) | Primary truth store |
| Redis | WIRED | C2 (Prod-Equivalent) | Advisory cache only |
| Anthropic LLM | WIRED | C3 (Production) | Skill execution |
| OpenAI | WIRED | C3 (Production) | Embedding, proxy |
| R2 Storage | WIRED | C3 (Production) | Durable artifacts |

---

## 4. Non-Contract Internals

These components are **internal** and may change without notice:

### L4 Internal Services
- CARERoutingEngine (routing algorithm)
- DriftDetectionEngine (SBA drift)
- ReputationCalculator (agent scoring)
- CostAggregator (cost rollup logic)

### L5 Internal Workers
- OutboxProcessor (delivery mechanics)
- CacheWarmer (precomputation)
- MetricsCollector (observability)

### L6 Internal Utilities
- ConnectionPool management
- Query optimization
- Cache eviction strategies

---

## 5. Change Rules

### 5.1 Changes Requiring New Obligation

| Change Type | Required Artifact |
|-------------|-------------------|
| New L6 table | Migration + INFRA_OBLIGATION_REGISTRY entry |
| New retry policy | RETRY_POLICY_REGISTRY entry |
| New DLQ target | DLQ_REGISTRY entry |
| New external service | INFRA_REGISTRY entry |

### 5.2 Changes Requiring PIN Documentation

| Change Type | Required Artifact |
|-------------|-------------------|
| New L2 route | PIN documenting API contract |
| New L4 domain | PIN documenting domain boundaries |
| Layer boundary change | PIN with ratification |
| Breaking API change | PIN with migration guide |

### 5.3 Changes Allowed Freely

| Change Type | Constraint |
|-------------|------------|
| L4 → L4 internal calls | Must not create cycles |
| L5 worker optimizations | Must preserve semantics |
| L6 query optimizations | Must not change results |
| Internal caching | Must not affect correctness |

---

## 6. Validation

This declaration is validated by:

| Validator | Purpose | Frequency |
|-----------|---------|-----------|
| BLCA (layer_validator.py) | Import boundary enforcement | Every commit |
| Component Inventory | Layer coverage | On demand |
| Route Registration | API completeness | CI |
| Infra Registry | Dependency truth | CI |

**Last Validation:** 2026-01-02
- Files scanned: 639
- Violations: 0
- Status: CLEAN

---

## 7. Architecture Invariants

### INV-001: Layer Isolation
> No layer may import from a higher layer.

### INV-002: L4 Owns Meaning
> All business logic resides in L4. L2 and L3 are pass-through.

### INV-003: L6 Is Terminal
> L6 has no dependencies on application code.

### INV-004: L3 Is Thin
> Adapters must be < 200 LOC with no business logic.

### INV-005: Single Source of Truth
> PostgreSQL is the only truth store. Redis is advisory.

---

## 8. Version History

| Date | Version | Change |
|------|---------|--------|
| 2026-01-02 | 1.0.0 | Initial declaration from codebase extraction |
