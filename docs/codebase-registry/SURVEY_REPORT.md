# Codebase Survey Report

**Survey Date:** 2025-12-29
**Schema Version:** v1 (FROZEN)
**Scope:** `/root/agenticverz2.0/`
**Survey Mode:** STRICT (transcription only, no decisions)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Artifacts Registered** | 111 |
| **Backend API Routes** | 28 |
| **Backend Services** | 24 |
| **Backend Workers** | 5 |
| **Frontend Pages** | 17 |
| **SDK Packages** | 4 |
| **BudgetLLM Modules** | 9 |
| **Operations Scripts** | 20 |
| **Library Modules** | 4 (SDK) |

---

## Breakdown by Layer

| Layer | Code | Count | Description |
|-------|------|-------|-------------|
| Backend | BE | 57 | API routes, services, workers |
| Frontend | FE | 17 | AI Console pages |
| SDK | SDK | 4 | Python and JavaScript SDKs |
| Library | LIB | 9 | BudgetLLM modules |
| Operations | OP | 20 | Scripts and tools |
| **Total** | | **111** | |

---

## Breakdown by Type

| Type | Count | Description |
|------|-------|-------------|
| api-route | 28 | FastAPI routers with HTTP endpoints |
| service | 24 | Backend business logic services |
| worker | 5 | Background processing workers |
| page | 17 | Frontend React pages |
| sdk-package | 4 | Client SDK packages |
| library | 9 | BudgetLLM modules |
| script | 20 | Operations scripts |
| **Total** | **111** | |

---

## Breakdown by Authority Level

| Authority Level | Count | Description |
|-----------------|-------|-------------|
| observe | 24 | Read-only, no side effects |
| advise | 4 | Suggestions without enforcement |
| enforce | 10 | Mandatory policy enforcement |
| mutate | 20 | State modification capability |
| **Total** | **58** | |

---

## Breakdown by Product

| Product | Count | Description |
|---------|-------|-------------|
| system-wide | 36 | Cross-product infrastructure |
| ai-console | 18 | AI Console specific |
| product-builder | 1 | Product Builder specific |
| external | 4 | SDK (external clients) |
| **Total** | **59** | (includes 1 overlap) |

---

## Breakdown by Console

| Console | Count | Description |
|---------|-------|-------------|
| customer | 26 | Customer-facing endpoints/pages |
| founder | 14 | Founder Ops Console |
| internal | 9 | Internal workers/services |
| external | 4 | SDK packages |
| all | 1 | Cross-console (legacy routes) |
| **Total** | **54** | (excludes 4 with different traceability) |

---

## Backend API Routes (28)

| Artifact ID | File | Purpose | Authority |
|-------------|------|---------|-----------|
| AOS-BE-API-HLT-001 | health.py | Health checks, K8s probes | observe |
| AOS-BE-API-TNT-001 | tenants.py | Tenant CRUD, API keys, quotas | enforce |
| AOS-BE-API-TRC-001 | traces.py | Trace storage, comparison, mismatch | observe |
| AOS-BE-API-GRD-001 | guard.py | Customer Console guard API | enforce |
| AOS-BE-API-OPS-001 | ops.py | Founder Ops Console | observe |
| AOS-BE-API-RTM-001 | runtime.py | Machine-native runtime | mutate |
| AOS-BE-API-POL-001 | policy.py | Policy evaluation | enforce |
| AOS-BE-API-KSW-001 | v1_killswitch.py | Kill-switch controls | enforce |
| AOS-BE-API-RCV-001 | recovery.py | M10 recovery suggestions | advise |
| AOS-BE-API-CST-001 | cost_intelligence.py | M26 cost tracking | observe |
| AOS-BE-API-ONB-001 | onboarding.py | M24 OAuth/email verification | mutate |
| AOS-BE-API-INT-001 | integration.py | M25 integration loop | enforce |
| AOS-BE-API-FND-001 | founder_actions.py | Founder action paths | enforce |
| AOS-BE-API-PRD-001 | predictions.py | PB-S5 predictions (read-only) | observe |
| AOS-BE-API-FBK-001 | feedback.py | PB-S3 pattern feedback | observe |
| AOS-BE-API-WRK-001 | workers.py | Business Builder Worker | mutate |
| AOS-BE-API-EMB-001 | embedding.py | Embedding quota/config | observe |
| AOS-BE-API-STH-001 | status_history.py | M6 status history audit | observe |
| AOS-BE-API-MEM-001 | memory_pins.py | M7 memory pins | mutate |
| AOS-BE-API-DSC-001 | discovery.py | Discovery ledger signals | observe |
| AOS-BE-API-FTL-001 | founder_timeline.py | Founder timeline view | observe |
| AOS-BE-API-CSM-001 | costsim.py | CostSim V2 sandbox | advise |
| AOS-BE-API-CVS-001 | customer_visibility.py | Customer pre/post visibility | observe |
| AOS-BE-API-RBC-001 | rbac_api.py | RBAC management | enforce |
| AOS-BE-API-COP-001 | cost_ops.py | Ops Console cost intelligence | observe |
| AOS-BE-API-LGC-001 | legacy_routes.py | Legacy 410 Gone handlers | enforce |
| AOS-BE-API-PLY-001 | policy_layer.py | M19 policy layer | enforce |
| AOS-BE-API-PPR-001 | policy_proposals.py | PB-S4 policy proposals | observe |

---

## Backend Workers (5)

| Artifact ID | File | Purpose | Authority |
|-------------|------|---------|-----------|
| AOS-BE-WKR-POL-001 | pool.py | Worker pool, run dispatch | mutate |
| AOS-BE-WKR-RUN-001 | runner.py | Run execution with retry | mutate |
| AOS-BE-WKR-RCE-001 | recovery_evaluator.py | M10 recovery evaluation | advise |
| AOS-BE-WKR-OBX-001 | outbox_processor.py | Transactional outbox | mutate |
| AOS-BE-WKR-RCC-001 | recovery_claim_worker.py | Recovery claim processing | mutate |

---

## Backend Services (4)

| Artifact ID | File | Purpose | Authority |
|-------------|------|---------|-----------|
| AOS-BE-SVC-MEM-001 | memory_service.py | M7 memory with Redis cache | mutate |
| AOS-BE-SVC-GOV-001 | governance_service.py | M15 LLM governance | enforce |
| AOS-BE-SVC-CRD-001 | credit_service.py | M12 credit billing | enforce |
| AOS-BE-SVC-EVT-001 | publisher.py | Event publishing | observe |

---

## Frontend Pages (17)

| Artifact ID | File | Purpose | Authority |
|-------------|------|---------|-----------|
| AOS-FE-AIC-SYS-001 | main.tsx | Application entry point | observe |
| AOS-FE-AIC-SYS-002 | AIConsoleApp.tsx | Root component, routing | observe |
| AOS-FE-AIC-SYS-003 | ConsoleLayout.tsx | Shell layout component | observe |
| AOS-FE-AIC-OVR-001 | OverviewPage.tsx | Overview domain page | observe |
| AOS-FE-AIC-ACT-001 | ActivityPage.tsx | Activity domain page | observe |
| AOS-FE-AIC-INC-001 | IncidentsPage.tsx | Incidents list page | observe |
| AOS-FE-AIC-INC-002 | IncidentDetailPage.tsx | Incident detail page | observe |
| AOS-FE-AIC-INC-003 | IncidentReplayPage.tsx | Incident replay page | advise |
| AOS-FE-AIC-INC-004 | IncidentTimelinePage.tsx | Incident timeline page | observe |
| AOS-FE-AIC-INC-005 | RecoverySuggestionsPage.tsx | Recovery suggestions page | advise |
| AOS-FE-AIC-POL-001 | PoliciesPage.tsx | Policies domain page | observe |
| AOS-FE-AIC-LOG-001 | LogsPage.tsx | Logs domain page | observe |
| AOS-FE-AIC-INT-001 | IntegrationsPage.tsx | Integrations page | observe |
| AOS-FE-AIC-INT-002 | APIKeysPage.tsx | API keys page | mutate |
| AOS-FE-AIC-ACC-001 | ProfilePage.tsx | Profile page | mutate |
| AOS-FE-AIC-ACC-002 | BillingPage.tsx | Billing page | observe |
| AOS-FE-AIC-ACC-003 | SupportPage.tsx | Support page | observe |

---

## SDK Packages (4)

| Artifact ID | Name | Language | Authority |
|-------------|------|----------|-----------|
| AOS-SDK-PY-AOS-001 | aos_sdk | Python | observe |
| AOS-SDK-PY-NVA-001 | nova_sdk | Python | observe |
| AOS-SDK-JS-AOS-001 | @agenticverz/aos-sdk | JavaScript/TypeScript | observe |
| AOS-SDK-JS-NVA-001 | nova-sdk | JavaScript | observe |

---

## Candidate Unregistered Artifacts (Classified)

**Reference:** SURVEY_BACKLOG.md for registration tracking
**PIN:** PIN-237

The following artifacts were surveyed, classified, and documented for future registration waves.

---

### Backend Services (25 files) - Wave 2

#### Platform Core Services (3)

| File | Purpose | Milestone | Authority |
|------|---------|-----------|-----------|
| `worker_registry_service.py` | Worker discovery, status queries, per-tenant config | M21 | enforce |
| `tenant_service.py` | Tenant CRUD, API key management, quota enforcement | M21 | enforce |
| `worker_service.py` | M12 concurrent-safe job item claiming (FOR UPDATE SKIP LOCKED) | M12 | mutate |

#### Cost & Anomaly Detection (1)

| File | Purpose | Milestone | Authority |
|------|---------|-----------|-----------|
| `cost_anomaly_detector.py` | Absolute spike, sustained drift, budget warning detection | M29 | observe |

#### Evidence & Incident Management (3)

| File | Purpose | Milestone | Authority |
|------|---------|-----------|-----------|
| `evidence_report.py` | Legal-grade PDF export with cover page, hash verification | M23 | observe |
| `incident_aggregator.py` | Anti-explosion grouping (5-min window, 20/hour cap) | - | enforce |
| `event_emitter.py` | PIN-105 ops console events with friction tracking | M24 | observe |

#### Failure & Recovery Services (6)

| File | Purpose | Contract | Authority |
|------|---------|----------|-----------|
| `llm_failure_service.py` | S4 failure truth - persistence BEFORE any action | S4 | enforce |
| `orphan_recovery.py` | PB-S2 crash recovery - detect runs orphaned by system crash | PB-S2 | mutate |
| `pattern_detection.py` | PB-S3 pattern detection WITHOUT modifying history | PB-S3 | observe |
| `prediction.py` | PB-S5 advisory predictions - zero side-effects | PB-S5 | advise |
| `recovery_rule_engine.py` | M10 rule-based evaluation for recovery suggestions | M10 | advise |
| `recovery_matcher.py` | M10 pattern matching with time-decay scoring | M10 | advise |

#### Security & Verification Services (4)

| File | Purpose | Milestone | Authority |
|------|---------|-----------|-----------|
| `certificate.py` | M23 cryptographic evidence using HMAC infrastructure | M23 | enforce |
| `policy_violation_service.py` | S3 violation detection, fact persistence, incident creation | S3 | enforce |
| `replay_determinism.py` | Determinism semantics (STRICT/LOGICAL/SEMANTIC) | - | observe |
| `email_verification.py` | OTP-based email verification (6-digit, 10-min TTL) | M24 | mutate |

#### Multi-Agent Coordination Services (7)

| File | Purpose | Milestone | Authority |
|------|---------|-----------|-----------|
| `job_service.py` | Job creation, status tracking, item distribution | M12 | mutate |
| `message_service.py` | P2P messaging with LISTEN/NOTIFY | M12 | mutate |
| `blackboard_service.py` | Shared Redis blackboard for agent coordination | M12 | mutate |
| `registry_service.py` | Agent registration, heartbeats, stale detection | M12 | enforce |
| `invoke_audit_service.py` | Audit trail for agent_invoke calls | M12.1 | observe |

---

### BudgetLLM Module (12 files) - Wave 3

**Location:** `/root/agenticverz2.0/budgetllm/`
**Purpose:** Hard budget limits + prompt caching + safety governance for LLM API calls

#### Core Modules (7)

| File | Purpose | Authority |
|------|---------|-----------|
| `budget.py` | Budget enforcement with daily/monthly/cumulative hard limits | enforce |
| `cache.py` | Prompt caching for cost savings on repeated queries | observe |
| `client.py` | OpenAI-compatible client wrapper with budget + safety | mutate |
| `safety.py` | Safety governance controller with parameter clamping | enforce |
| `output_analysis.py` | Risk signal detection (unsupported claims, hedging, contradictions) | observe |
| `prompt_classifier.py` | Prompt categorization (factual, analytical, coding, etc.) | observe |
| `risk_formula.py` | Risk scoring formula (0.0-1.0 scale) | observe |

#### Backend Modules (2)

| File | Purpose | Authority |
|------|---------|-----------|
| `backends/memory.py` | Thread-safe in-memory cache with LRU eviction | observe |
| `backends/redis.py` | Redis-backed cache for multi-process state | observe |

---

### Scripts (180+ files) - Wave 4 (Selective)

| Category | Location | Count | Key Files | Purpose |
|----------|----------|-------|-----------|---------|
| **CI/CD** | `scripts/ci/` | 35 | `synthetic_alert.sh`, `check_env_misuse.sh` | Phase guardrails (C2-C5), schema validation |
| **Operations** | `scripts/ops/` | 96 | `m10_orchestrator.py`, `rbac_enable.sh` | Consolidated maintenance, deployment, monitoring |
| **Stress Testing** | `scripts/stress/` | 13 | `run_golden_stress.sh`, `run_fault_injection.sh` | Golden replay verification, determinism testing |
| **Smoke Testing** | `scripts/smoke/` | 2 | `rbac_smoke.sh` | Quick RBAC validation |
| **Chaos Engineering** | `scripts/chaos/` | 3 | `cpu_spike.sh`, `memory_pressure.sh`, `redis_stall.sh` | Resource exhaustion simulation |
| **Deployment** | `scripts/deploy/` | 6 | `aos-console-deploy.sh` | Service deployment automation |
| **Verification** | `scripts/verification/` | 10 | `truth_preflight.sh`, `tenant_isolation_test.py` | Phase certification, invariant testing |
| **Tools** | `scripts/tools/` | 1 | `pin_drift_detector.sh` | PIN drift detection |
| **Root Level** | `scripts/` | 12 | `e2e_integration.sh`, `bootstrap-dev.sh` | Core operations, setup |

**Key Observations:**
- Operations scripts dominate (53% of total)
- Phase-aware CI checks (C1-C5 guardrails)
- Determinism-focused stress tests
- Safety-first chaos engineering (requires `CHAOS_ALLOWED=true`)

---

### Frontend Components (85+ files) - Not Registered

Page-level registration (17 pages) captures the primary executable surface. Individual React components are structural and do not warrant individual registration.

---

### Registration Priority Matrix

| Wave | Category | Count | Priority | Status |
|------|----------|-------|----------|--------|
| 1 | Initial Survey | 58 | P0 | COMPLETE |
| 2 | Backend Services | 25 | P1 | PENDING |
| 3 | BudgetLLM | 12 | P2 | PENDING |
| 4 | Scripts (Selective) | ~25 | P3 | PENDING |
| - | Frontend Components | 85+ | - | NOT PLANNED |
| **Total Registered** | - | **58** | - | - |
| **Total Backlog** | - | **~62** | - | - |

---

## Observations (No Recommendations)

1. **High API Route Coverage**: 28 of ~33 API routes surveyed and registered
2. **Worker Coverage**: All 5 identified workers registered
3. **Service Selection**: 4 key services registered; ~48 services not registered
4. **SDK Coverage**: All 4 SDK packages registered
5. **Frontend Coverage**: 17 pages registered per PIN-236 Customer Console Constitution
6. **Scripts Unregistered**: 160 scripts identified but not individually registered

---

## Survey Integrity

| Check | Status |
|-------|--------|
| Schema v1 used | YES |
| No decisions made | YES |
| No fixes applied | YES |
| No recommendations | YES |
| Transcription only | YES |

---

## Registry Locations

- **Schema**: `/docs/codebase-registry/schema-v1.yaml`
- **Artifacts**: `/docs/codebase-registry/artifacts/*.yaml`
- **README**: `/docs/codebase-registry/README.md`

---

*Generated by Codebase Survey - STRICT MODE*
