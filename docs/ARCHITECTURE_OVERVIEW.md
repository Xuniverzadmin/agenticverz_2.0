# AOS Architecture Overview

**Version:** 1.0
**Last Updated:** 2025-12-13

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AOS ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           CLIENTS                                    │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │
│  │  │   Console    │  │  Python SDK  │  │    JS SDK    │              │    │
│  │  │   (React)    │  │              │  │              │              │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │    │
│  │         │                 │                  │                      │    │
│  │         └─────────────────┼──────────────────┘                      │    │
│  │                           │                                          │    │
│  │                    HTTPS / WebSocket                                 │    │
│  └───────────────────────────┼──────────────────────────────────────────┘    │
│                              │                                               │
│  ┌───────────────────────────▼──────────────────────────────────────────┐   │
│  │                      EDGE / PROXY                                     │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                        │   │
│  │   Cloudflare (CDN + WAF + DDoS) → Apache (TLS + Proxy)                │   │
│  │                                                                        │   │
│  └───────────────────────────┬───────────────────────────────────────────┘   │
│                              │                                               │
│  ┌───────────────────────────▼──────────────────────────────────────────┐   │
│  │                      BACKEND SERVICES                                 │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                        │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │                    FastAPI Application                         │    │   │
│  │  ├──────────────────────────────────────────────────────────────┤    │   │
│  │  │                                                                │    │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │    │   │
│  │  │  │  Auth/RBAC  │  │   Runtime   │  │  Cost Simulator V2  │   │    │   │
│  │  │  │   Module    │  │   Engine    │  │                     │   │    │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │    │   │
│  │  │                                                                │    │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │    │   │
│  │  │  │   Skills    │  │  Recovery   │  │      Workflow       │   │    │   │
│  │  │  │   Engine    │  │   Engine    │  │       Engine        │   │    │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │    │   │
│  │  │                                                                │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  │                              │                                        │   │
│  │  ┌───────────────────────────▼──────────────────────────────────┐    │   │
│  │  │                      Worker Process                            │    │   │
│  │  ├──────────────────────────────────────────────────────────────┤    │   │
│  │  │  ThreadPoolExecutor  │  Skill Executors  │  State Manager    │    │   │
│  │  └──────────────────────────────────────────────────────────────┘    │   │
│  │                                                                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│  ┌───────────────────────────▼──────────────────────────────────────────┐   │
│  │                      DATA LAYER                                       │   │
│  ├───────────────────────────────────────────────────────────────────────┤   │
│  │                                                                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │
│  │  │  PostgreSQL  │  │    Redis     │  │   Prometheus/Grafana     │   │   │
│  │  │  (via        │  │  (Cache +    │  │   (Observability)        │   │   │
│  │  │  PgBouncer)  │  │  Pub/Sub)    │  │                          │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │
│  │                                                                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Frontend: Console UI

**Technology:** React 18 + TypeScript + Vite

**Key Libraries:**
- TanStack Query - Server state management
- Zustand - Client state management
- Radix UI - Accessible components
- Tailwind CSS - Styling
- Recharts - Data visualization

**Structure:**
```
website/aos-console/console/
├── src/
│   ├── api/          # API client functions
│   ├── components/   # Reusable UI components
│   ├── pages/        # Page components
│   ├── stores/       # Zustand stores
│   ├── types/        # TypeScript definitions
│   ├── utils/        # Utilities (SSE, WebSocket)
│   └── lib/          # Third-party integrations
```

---

### Backend: FastAPI Application

**Technology:** Python 3.10 + FastAPI + SQLModel

**Key Modules:**

```
backend/app/
├── api/              # REST API routers
│   ├── agents.py     # Agent CRUD
│   ├── jobs.py       # Job management
│   ├── runtime.py    # Simulate, query, capabilities
│   └── recovery.py   # Failure recovery
├── auth/             # Authentication & RBAC
│   ├── rbac.py       # Role-based access control
│   └── middleware.py # Auth middleware
├── skills/           # Skill implementations
│   ├── http_call.py
│   ├── llm_invoke.py
│   ├── json_transform.py
│   ├── fs_read.py
│   ├── fs_write.py
│   ├── webhook_send.py
│   └── email_send.py
├── worker/           # Execution engine
│   └── runtime/      # Machine-native runtime
├── workflow/         # Workflow orchestration
├── costsim/          # Cost simulation V2
└── main.py           # Application entry point
```

---

### Worker Process

**Purpose:** Execute skill plans asynchronously

**Components:**
- **ThreadPoolExecutor:** Concurrent skill execution
- **State Manager:** Track execution state
- **Skill Executors:** Individual skill implementations

**Execution Flow:**
```
Plan Submitted
      │
      ▼
┌─────────────────┐
│ Validate Plan   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Acquire Budget  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Execute Step 1  │────►│ Record Result   │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Execute Step 2  │────►│ Record Result   │
└────────┬────────┘     └─────────────────┘
         │
         ▼
        ...
         │
         ▼
┌─────────────────┐
│ Finalize Run    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Release Budget  │
└─────────────────┘
```

---

### Data Layer

#### PostgreSQL (via PgBouncer)
- **Port:** 5433 (direct), 6432 (pooler)
- **Purpose:** Primary data store
- **Tables:** agents, jobs, runs, blackboard, transactions

#### Redis
- **Port:** 6379
- **Purpose:**
  - Cache layer
  - Pub/Sub for real-time events
  - Rate limiting counters
  - Session storage

#### Prometheus + Grafana
- **Ports:** 9090 (Prometheus), 3000 (Grafana)
- **Purpose:** Metrics collection and visualization

---

## API Architecture

### Request Flow

```
Client Request
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                    Cloudflare Edge                       │
│  • DDoS Protection                                       │
│  • WAF Rules                                             │
│  • SSL/TLS                                               │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    Apache Proxy                          │
│  • Origin SSL                                            │
│  • Request Routing                                       │
│  • Load Balancing                                        │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Middleware Stack                      │   │
│  ├──────────────────────────────────────────────────┤   │
│  │  • CORS                                           │   │
│  │  • Authentication (X-API-Key or Bearer)           │   │
│  │  • RBAC Authorization                             │   │
│  │  • Rate Limiting                                  │   │
│  │  • Request Logging                                │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                                │
│                         ▼                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Route Handler                         │   │
│  │  • Input Validation (Pydantic)                    │   │
│  │  • Business Logic                                 │   │
│  │  • Database Operations                            │   │
│  │  • Response Serialization                         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/health` | GET | Health check | None |
| `/api/v1/runtime/capabilities` | GET | List skills | Required |
| `/api/v1/runtime/simulate` | POST | Plan simulation | Required |
| `/api/v1/runtime/query` | POST | State query | Required |
| `/api/v1/agents` | GET/POST | Agent CRUD | Required |
| `/api/v1/runs` | GET/POST | Run management | Required |
| `/api/v1/recovery/stats` | GET | Recovery stats | Required |

---

## Machine-Native Design

### Core Principles

1. **Queryable State**
   - No log parsing required
   - Structured state queries
   - Real-time status endpoints

2. **Capability Contracts**
   - Skills declare capabilities
   - Cost estimates upfront
   - Rate limits exposed

3. **Structured Outcomes**
   - Never throws (returns structured errors)
   - Failure as data
   - Navigable error chains

4. **Pre-execution Simulation**
   - Cost estimation before commit
   - Feasibility checking
   - Risk assessment

### Example: Simulation API

```python
# Request
POST /api/v1/runtime/simulate
{
  "plan": [
    {"skill": "http_call", "params": {"url": "..."}},
    {"skill": "llm_invoke", "params": {"prompt": "..."}}
  ],
  "budget_cents": 100
}

# Response (Machine-Readable)
{
  "feasible": true,
  "estimated_cost_cents": 5,
  "estimated_duration_ms": 2500,
  "step_estimates": [
    {"skill_id": "http_call", "estimated_cost_cents": 0, "estimated_latency_ms": 500},
    {"skill_id": "llm_invoke", "estimated_cost_cents": 5, "estimated_latency_ms": 2000}
  ],
  "budget_remaining_cents": 95,
  "budget_sufficient": true,
  "risks": []
}
```

---

## Security Architecture

### Authentication Flow

```
┌─────────────────┐         ┌─────────────────┐
│     Client      │         │    Backend      │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │  Request + X-API-Key      │
         │ ─────────────────────────►│
         │                           │
         │                    ┌──────▼──────┐
         │                    │ Validate    │
         │                    │ API Key     │
         │                    └──────┬──────┘
         │                           │
         │                    ┌──────▼──────┐
         │                    │ Check RBAC  │
         │                    │ Permissions │
         │                    └──────┬──────┘
         │                           │
         │     Response              │
         │ ◄─────────────────────────│
         │                           │
```

### RBAC Model

```
Roles:
├── viewer
│   └── Can: read agents, jobs, stats
├── operator
│   └── Can: viewer + execute, simulate
└── admin
    └── Can: operator + create, delete, configure
```

### Security Measures
- API keys hashed at rest
- HTTPS enforced (Cloudflare Origin certs)
- CORS restricted to allowed origins
- Rate limiting per API key
- Input validation on all endpoints
- SQL injection prevention (SQLModel/SQLAlchemy)
- XSS prevention (React escaping)

---

## Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────────────────────────┐
│                    Production Server                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │              Docker Compose Stack                │   │
│   ├─────────────────────────────────────────────────┤   │
│   │                                                  │   │
│   │  ┌────────────┐  ┌────────────┐  ┌──────────┐  │   │
│   │  │  Backend   │  │   Worker   │  │ PgBouncer│  │   │
│   │  │   :8000    │  │            │  │  :6432   │  │   │
│   │  └────────────┘  └────────────┘  └──────────┘  │   │
│   │                                                  │   │
│   │  ┌────────────┐  ┌────────────┐  ┌──────────┐  │   │
│   │  │ PostgreSQL │  │   Redis    │  │Prometheus│  │   │
│   │  │   :5433    │  │   :6379    │  │  :9090   │  │   │
│   │  └────────────┘  └────────────┘  └──────────┘  │   │
│   │                                                  │   │
│   │  ┌────────────┐  ┌────────────┐                │   │
│   │  │  Grafana   │  │Alertmanager│                │   │
│   │  │   :3000    │  │   :9093    │                │   │
│   │  └────────────┘  └────────────┘                │   │
│   │                                                  │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
│   ┌─────────────────────────────────────────────────┐   │
│   │              Apache HTTP Server                  │   │
│   │  • VirtualHost: agenticverz.com                 │   │
│   │  • SSL: Cloudflare Origin Certificate           │   │
│   │  • Proxy: /api → localhost:8000                 │   │
│   │  • Static: /console → dist/                     │   │
│   └─────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Framework | FastAPI | Async, type hints, OpenAPI |
| ORM | SQLModel | Pydantic + SQLAlchemy combined |
| Frontend Framework | React | Component model, ecosystem |
| State Management | Zustand | Simple, TypeScript-first |
| Server State | TanStack Query | Caching, deduplication |
| Styling | Tailwind CSS | Utility-first, rapid dev |
| Database | PostgreSQL | Reliability, JSON support |
| Cache | Redis | Speed, Pub/Sub support |
| Container | Docker Compose | Development parity |
| CDN/WAF | Cloudflare | DDoS protection, edge caching |
| Proxy | Apache | Mature, SSL, easy config |

---

## Further Reading

- [AOS Test Handbook](./AOS_TEST_HANDBOOK.md)
- [Error Playbook](./ERROR_PLAYBOOK.md)
- [User Journey](./USER_JOURNEY.md)
- [Beta Instructions](./BETA_INSTRUCTIONS.md)
- [API Workflow Guide](./API_WORKFLOW_GUIDE.md)
