# Architecture Graph

**Generated:** 2026-01-02
**Source:** Declarative extraction from codebase
**Status:** FROZEN

---

## Layer Model (L8 → L1)

```
┌─────────────────────────────────────────────────────────────────┐
│ L1 — Product Experience (UI)                                     │
│      • Customer Console (console.agenticverz.com)               │
│      • Founder Console (founder.agenticverz.com)                │
│      • Ops Console (ops.agenticverz.com)                        │
│      Imports: L2 only                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│ L2 — Product APIs (34 files, 354 routes)                        │
│      • FastAPI routers                                          │
│      • Request/Response transformation                          │
│      • Auth middleware integration                              │
│      Imports: L3, L4, L6                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ L3 — Boundary Adapters (27 files)                               │
│      • Auth adapters (RBAC, JWT, API Key)                       │
│      • Middleware (rate limit, correlation)                     │
│      • External service wrappers                                │
│      Imports: L4, L6                                            │
│      Rule: < 200 LOC, no business logic                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ L4 — Domain Engines (165 files, 1130 components)                │
│      • Services (core business logic)                           │
│      • Skills (agent capabilities)                              │
│      • Policy, Memory, Routing, Learning engines                │
│      • Cost simulation, Agent governance                        │
│      Imports: L5, L6                                            │
│      Rule: Owns meaning, exports facades                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ L5 — Execution & Workers (24 files)                             │
│      • Worker runtime                                           │
│      • Background job execution                                 │
│      • Outbox processor                                         │
│      Imports: L6 only                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ L6 — Platform Substrate (76 files)                              │
│      • Database (PostgreSQL via SQLModel)                       │
│      • Redis (advisory cache)                                   │
│      • External services (LLM providers)                        │
│      • Models, Stores, Infra utilities                          │
│      Imports: None (terminal layer)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer Call Matrix

Imports between layers (count of module references):

| From → To | L2 | L3 | L4 | L5 | L6 |
|-----------|---:|---:|---:|---:|---:|
| **L2**    | 0  | 22 | 51 | 5  | 43 |
| **L3**    | 0  | 4  | 18 | 1  | 7  |
| **L4**    | 0  | 2  | 110| 10 | 45 |
| **L5**    | 0  | 0  | 25 | 1  | 21 |
| **L6**    | 0  | 10 | 6  | 0  | 21 |

**Observations:**
- L2 → L4: 51 calls (APIs call domain services)
- L4 → L4: 110 calls (domain services call each other)
- L4 → L6: 45 calls (domain uses platform)
- L6 → L3: 10 calls (platform uses adapters for external)

---

## L2 API Domains (354 routes)

### Core Product APIs

| Domain | Routes | Purpose |
|--------|-------:|---------|
| **agents** | 49 | Agent lifecycle, strategy, reputation |
| **policy_layer** | 37 | Constitutional policy management |
| **guard** | 18 | Incident detection and response |
| **integration** | 17 | Integration loop and checkpoints |
| **cost_intelligence** | 14 | Cost analytics and anomalies |
| **ops** | 14 | Founder operations dashboard |
| **tenants** | 14 | Multi-tenant management |
| **recovery** | 14 | M10 recovery suggestion engine |
| **workers** | 12 | Worker execution and streaming |
| **costsim** | 11 | Cost simulation V2 |

### Supporting APIs

| Domain | Routes | Purpose |
|--------|-------:|---------|
| **v1_killswitch** | 10 | Safety kill-switch controls |
| **embedding** | 10 | IAEC embedding composition |
| **onboarding** | 10 | Auth and signup flows |
| **traces** | 10 | Trace inspection and replay |
| **founder_actions** | 9 | Founder emergency actions |
| **runtime** | 9 | Machine-native runtime |
| **policy** | 6 | Policy evaluation |
| **health** | 5 | Health checks |
| **memory_pins** | 5 | Memory pin management |
| **rbac_api** | 5 | RBAC administration |

### Utility APIs

| Domain | Routes | Purpose |
|--------|-------:|---------|
| **customer_visibility** | 4 | Pre-run and outcome visibility |
| **founder_timeline** | 4 | Decision timeline |
| **status_history** | 4 | Status export |
| **cost_ops** | 4 | Cost operations |
| **cost_guard** | 3 | Cost guard incidents |
| **v1_proxy** | 3 | OpenAI-compatible proxy |
| **predictions** | 3 | C2 prediction plane |
| **discovery** | 2 | Discovery ledger |
| **feedback** | 2 | CARE feedback |

---

## Component Connection Graph

### Customer Journey: Submit and Monitor

```
L1: Customer Console
    ↓
L2: POST /api/v1/workers/run
    ↓
L3: AuthMiddleware → ActorContext extraction
    ↓
L4: WorkerService.submit_run()
    ├── L4: PolicyService.evaluate_pre_run()
    ├── L4: BudgetService.check_budget()
    └── L4: AgentService.validate_agent()
        ↓
L5: WorkerRuntime.execute()
    ├── L4: SkillExecutor.invoke()
    └── L6: TraceStore.persist_trace()
        ↓
L6: PostgreSQL (runs, traces, costs)
```

### Founder Journey: Incident Response

```
L1: Founder Console
    ↓
L2: GET /api/v1/guard/incidents
    ↓
L4: IncidentService.list_incidents()
    ↓
L6: incident_store.query()

L2: POST /api/v1/killswitch/tenant
    ↓
L4: KillswitchService.freeze_tenant()
    ├── L6: tenant_store.update_status()
    └── L6: audit_store.log_action()
```

### Recovery Flow (M10)

```
L2: GET /api/v1/recovery/candidates
    ↓
L4: RecoveryService.get_candidates()
    ├── L4: RecoveryCatalogService.match_failure()
    └── L6: recovery_candidate_store.query()

L2: POST /api/v1/recovery/approve
    ↓
L4: RecoveryService.approve_recovery()
    ├── L4: RecoveryExecutor.execute_action()
    ├── L6: outbox.publish_event()
    └── L5: OutboxProcessor.deliver()
```

---

## Stable Contracts (L2 → L1)

These APIs are **frontend-facing** and must not change without versioning:

### Authentication
- `POST /api/v1/onboarding/login/{provider}`
- `POST /api/v1/onboarding/refresh`
- `GET /api/v1/onboarding/me`

### Core Operations
- `POST /api/v1/workers/run` — Submit execution
- `GET /api/v1/workers/runs/{run_id}` — Get run status
- `GET /api/v1/workers/stream/{run_id}` — SSE stream

### Incidents
- `GET /api/v1/guard/incidents` — List incidents
- `GET /api/v1/guard/incidents/{id}` — Get incident detail
- `POST /api/v1/guard/incidents/{id}/acknowledge` — Acknowledge

### Cost Intelligence
- `GET /api/v1/cost-intelligence/dashboard` — Cost dashboard
- `GET /api/v1/cost-intelligence/summary` — Cost summary

### Recovery (M10)
- `GET /api/v1/recovery/candidates` — Recovery candidates
- `POST /api/v1/recovery/approve` — Approve recovery

---

## Internal Mechanics (Not for Frontend)

These components are **internal** and may evolve:

- `L5: OutboxProcessor` — Delivery mechanics
- `L4: CARERoutingEngine` — Agent routing internals
- `L4: DriftDetectionEngine` — SBA drift detection
- `L6: advisory_cache` — Redis caching layer
- Worker pool management
- Background job scheduling

---

## Change Rules

### Requires New Obligation
- New L6 table or store
- New retry policy
- New DLQ target
- New external service integration

### Requires PIN Documentation
- New L2 route (API surface change)
- New L4 domain engine
- Layer boundary change

### May Evolve Freely
- Internal L4 → L4 calls
- L5 worker optimizations
- L6 query optimizations
- Internal caching strategies

---

## Validation

This graph is validated by:
- `scripts/ops/layer_validator.py` (BLCA)
- Component inventory extraction (no UNKNOWN layers)
- Route registration verification

**Last Validation:** 2026-01-02 — 0 violations
