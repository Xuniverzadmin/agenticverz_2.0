# PIN-237: Codebase Purpose & Authority Registry - Full Survey

**Status:** COMPLETE
**Created:** 2025-12-29
**Updated:** 2025-12-29 (Wave 2-4 Complete, Product Mapping Added)
**Category:** Infrastructure / Governance
**Milestone:** Post-M29 - Registry Foundation
**Related PINs:** PIN-235 (Products-First Migration), PIN-236 (Customer Console Constitution)

---

## Summary

Conducted comprehensive codebase survey for `/root/agenticverz2.0/` following STRICT SURVEY MODE (transcription only, no decisions). Created canonical Codebase Purpose & Authority Registry with **113 registered artifacts** across 4 waves (including self-registered tooling).

---

## Deliverables

### Registry Infrastructure

| File | Purpose |
|------|---------|
| `/docs/codebase-registry/README.md` | Scope declaration |
| `/docs/codebase-registry/schema-v1.yaml` | Frozen v1 schema |
| `/docs/codebase-registry/SURVEY_REPORT.md` | Survey findings |
| `/docs/codebase-registry/SURVEY_BACKLOG.md` | Registration tracker |
| `/docs/codebase-registry/artifacts/*.yaml` | 113 artifact files |

### Registered Artifacts (113 Total)

| Layer | Type | Count |
|-------|------|-------|
| Backend | API Routes | 28 |
| Backend | Workers | 5 |
| Backend | Services | 24 |
| Frontend | Pages | 17 |
| SDK | Packages | 4 |
| Library | BudgetLLM | 9 |
| Operations | Scripts | 22 |
| **Total** | | **113** |

### Authority Level Distribution

| Level | Count | Description |
|-------|-------|-------------|
| observe | 24 | Read-only, no side effects |
| mutate | 20 | State modification |
| enforce | 10 | Policy enforcement |
| advise | 4 | Suggestions only |

### Product Mapping Analysis

| Category | Count | Percentage |
|----------|-------|------------|
| **Direct AI Console** | 31 | 28% |
| **Indirect (System-Wide)** | 81 | 72% |
| **Not Related (Product Builder)** | 1 | 1% |
| **Total** | 113 | 100% |

**1. Directly Mapped to AI Console (31 artifacts):**

| Category | Count | Examples |
|----------|-------|----------|
| Frontend Pages | 17 | OverviewPage, IncidentsPage, PoliciesPage, KeysPage |
| Backend Services | 13 | Cost Anomaly Detector, Evidence Report, Policy Proposal |
| Deployment Scripts | 1 | aos-console-deploy.sh |

**2. Indirectly Mapped - System-Wide Infrastructure (79 artifacts):**

| Category | Count | Purpose |
|----------|-------|---------|
| Backend API Routes | 19 | Core platform APIs (runtime, health, auth, policies) |
| Backend Services | 15 | Core services (memory, governance, jobs, messaging) |
| Workers | 5 | Run executor, policy enforcer, reconciliation |
| BudgetLLM Library | 9 | LLM budget, caching, safety, risk scoring |
| SDK Packages | 4 | Python SDK, JavaScript SDK |
| Operations Scripts | 21 | Preflight, postflight, stress tests, chaos, artifact_lookup, change_record |
| CI/CD Scripts | 8 | Validation, smoke tests, hygiene |

**3. Not Related to AI Console (1 artifact):**

| Artifact ID | Name | Product |
|-------------|------|---------|
| AOS-BE-API-WRK-001 | worker_routes.py | product-builder |

---

## Survey Scope

### Included (Registered)

- All backend API routes (`/backend/app/api/*.py`)
- Core workers (`/backend/app/worker/*.py`)
- Key services (memory, governance, credit, events)
- AI Console pages (17 per PIN-236 constitution)
- All SDK packages (Python + JavaScript)

### Registration Waves (All Complete)

| Wave | Category | Count | Status |
|------|----------|-------|--------|
| Wave 1 | Initial (API, Workers, Pages, SDK) | 58 | COMPLETE |
| Wave 2 | Backend Services | 20 | COMPLETE |
| Wave 3 | BudgetLLM Modules | 9 | COMPLETE |
| Wave 4 | Operations Scripts | 20 | COMPLETE |
| - | Frontend Components | 85+ | Not registered (page-level sufficient) |

---

## Classified Unregistered Artifacts

### Backend Services (25 files)

**Platform Core (3):**
- `worker_registry_service.py` - M21 worker discovery
- `tenant_service.py` - M21 tenant CRUD, quotas
- `worker_service.py` - M12 job item claiming

**Cost & Anomaly (1):**
- `cost_anomaly_detector.py` - M29 anomaly detection

**Evidence & Incidents (3):**
- `evidence_report.py` - Legal-grade PDF export
- `incident_aggregator.py` - Anti-explosion grouping
- `event_emitter.py` - PIN-105 ops events

**Failure & Recovery (6):**
- `llm_failure_service.py` - S4 failure truth
- `orphan_recovery.py` - PB-S2 crash recovery
- `pattern_detection.py` - PB-S3 pattern detection
- `prediction.py` - PB-S5 advisory predictions
- `recovery_rule_engine.py` - M10 rule evaluation
- `recovery_matcher.py` - M10 pattern matching

**Security & Verification (4):**
- `certificate.py` - M23 cryptographic evidence
- `policy_violation_service.py` - S3 violations
- `replay_determinism.py` - Determinism validation
- `email_verification.py` - OTP verification

**Multi-Agent Coordination (7):**
- `credit_service.py` - M12 credit billing
- `governance_service.py` - M15 LLM governance
- `job_service.py` - M12 job lifecycle
- `message_service.py` - M12 P2P messaging
- `blackboard_service.py` - M12 shared state
- `registry_service.py` - M12 agent registry
- `invoke_audit_service.py` - M12.1 audit trail

### BudgetLLM Module (12 files)

**Core (7):**
- `budget.py` - Budget enforcement with limits
- `cache.py` - Prompt caching
- `client.py` - OpenAI-compatible client
- `safety.py` - Safety governance controller
- `output_analysis.py` - Risk signal detection
- `prompt_classifier.py` - Prompt categorization
- `risk_formula.py` - Risk scoring

**Backends (2):**
- `memory.py` - In-memory cache backend
- `redis.py` - Redis cache backend

**Package (3):**
- `__init__.py` - Package exports
- `core/__init__.py` - Core exports
- `backends/__init__.py` - Backend exports

### Scripts (180+ files)

| Category | Location | Count | Purpose |
|----------|----------|-------|---------|
| CI/CD | `scripts/ci/` | 35 | Phase guardrails, validation |
| Operations | `scripts/ops/` | 96 | Maintenance, deployment, monitoring |
| Stress Testing | `scripts/stress/` | 13 | Load testing, determinism |
| Smoke Testing | `scripts/smoke/` | 2 | Quick validation |
| Chaos Engineering | `scripts/chaos/` | 3 | Fault injection |
| Deployment | `scripts/deploy/` | 6 | Service deployment |
| Verification | `scripts/verification/` | 10 | Phase certification |
| Tools | `scripts/tools/` | 1 | Utilities |
| Root Level | `scripts/` | 12 | Core operations |

---

## Schema v1 (FROZEN)

```yaml
artifact_id: AOS-<LAYER>-<TYPE>-<DOMAIN>-<SEQ>
name: <filename>
type: api-route | service | worker | page | sdk-package | script
status: active | deprecated | planned
owner: backend | frontend | sdk | ops
purpose: <description>
authority_level: observe | advise | enforce | mutate
execution_surface: server | client | cli
traceability:
  product: system-wide | ai-console | product-builder
  console: customer | founder | internal | external
  domain: <domain-code>
  subdomain: <subdomain>
  order_depth: O1-O5
responsibility: |
  <endpoint list or function descriptions>
dependencies:
  - <dependency list>
```

---

## Completion Summary

All registration waves completed:

| Wave | Artifacts | Date |
|------|-----------|------|
| Wave 1 | 58 artifacts | 2025-12-29 |
| Wave 2 | 20 services | 2025-12-29 |
| Wave 3 | 9 BudgetLLM modules | 2025-12-29 |
| Wave 4 | 20 scripts | 2025-12-29 |
| **Total** | **113 artifacts** | |

### Maintenance Guidelines

1. New artifacts should be registered following schema-v1
2. Registry should be synchronized on significant code changes
3. Human approval required for new registrations

---

## Governance Notes

- **STRICT SURVEY MODE:** No decisions, fixes, or recommendations made
- **Schema v1 FROZEN:** No schema changes without explicit approval
- **Transcription Only:** All entries derived from source code observation
- **Human Review Required:** Registry additions require human approval

---

## References

- Survey Report: `/docs/codebase-registry/SURVEY_REPORT.md`
- Survey Backlog: `/docs/codebase-registry/SURVEY_BACKLOG.md`
- Schema: `/docs/codebase-registry/schema-v1.yaml`
- Artifacts: `/docs/codebase-registry/artifacts/`
