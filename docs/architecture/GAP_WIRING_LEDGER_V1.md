# Gap Wiring Ledger v1

**Status:** DRAFT
**Date:** 2026-01-21
**Reference:** GAP_IMPLEMENTATION_PLAN_V1.md
**Author:** Systems Architect

---

## Executive Summary

This ledger documents the missing wiring gaps identified from the T0-T4 cascade analysis. These gaps represent the work needed to expose L4 governance services via L2 API routes and integrate them into the aos_sdk.

**Current State:**
- 85 L4 governance gaps implemented (GAP-001 to GAP-089)
- 2,007 governance tests passing
- L2 API routes: ~18% exposed
- aos_sdk integration: 0%

**New Gaps Identified:** 47 additional gaps (GAP-090 to GAP-136)

---

## Gap Classification Legend

| Type | Symbol | Meaning |
|------|--------|---------|
| **DISCRETE** | `[D]` | Independent, no prerequisites beyond parent L4 gap |
| **LINKED** | `[L]` | Requires another wiring gap to be complete first |
| **BUNDLE** | `[B]` | Multiple related items grouped as one gap |

---

## Execution Invariants Reference

**Source:** `GAP_IMPLEMENTATION_PLAN_V2.md` Section 1.4

These invariants are **foundational contracts** that govern HOW gaps must be implemented. They are not gaps themselves but enforcement rules.

| Invariant | Name | Priority | Acceptance Criteria | Applies To |
|-----------|------|----------|---------------------|------------|
| **INV-W0-001** | ExecutionContext | CRITICAL | EC-001 to EC-004 | All W0 hooks (GAP-137→143) |
| **INV-W0-002** | KillSwitch Propagation | HIGH | KS-001 to KS-004 | Job execution (GAP-154→158), Lifecycle (GAP-159→164) |
| **INV-W0-003** | Idempotency & Replay | HIGH | IDEM-001 to IDEM-004 | Job execution (GAP-155), Lifecycle (GAP-159→164) |
| **INV-W0-004** | Failure Semantics | MEDIUM | FS-001 to FS-004 | SDK facade (GAP-083→085), L2 APIs (GAP-090→136) |

### Invariant Acceptance Criteria Summary

**INV-W0-001 (ExecutionContext):**
| ID | Criterion | Verification |
|----|-----------|--------------|
| EC-001 | All L4 services accept ExecutionContext | grep for `ctx: ExecutionContext` |
| EC-002 | Context propagated to downstream calls | Code review + integration test |
| EC-003 | Audit emissions include context | Log verification |
| EC-004 | No context = BLOCK (fail-closed) | Unit test for missing context |

**INV-W0-002 (KillSwitch):**
| ID | Criterion | Verification |
|----|-----------|--------------|
| KS-001 | All job handlers use KillSwitchGuard | grep for `KillSwitchGuard` |
| KS-002 | Heartbeat check every 30s | Timer verification in tests |
| KS-003 | Killed jobs do not commit | Integration test with switch toggle |
| KS-004 | Kill events audited | Audit log verification |

**INV-W0-003 (Idempotency):**
| ID | Criterion | Verification |
|----|-----------|--------------|
| IDEM-001 | All state-mutating jobs use IdempotencyKey | grep for `IdempotencyKey` |
| IDEM-002 | Duplicate calls return cached result | Unit test with same key |
| IDEM-003 | Failed jobs can retry (unless permanent) | Retry test |
| IDEM-004 | TTL prevents unbounded growth | Redis key expiry check |

**INV-W0-004 (FailureSemantics):**
| ID | Criterion | Verification |
|----|-----------|--------------|
| FS-001 | All SDK methods return SDKResult | Type check |
| FS-002 | All failures have category | No raw exceptions in responses |
| FS-003 | TRANSIENT includes retry_after | Schema validation |
| FS-004 | POLICY includes policy context | Log verification |

---

## T0 Wiring Gaps (GAP-090 to GAP-101)

### T0 L2 API Route Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-090** | Kill Switch API | `[D]` | GAP-069 | `POST /api/v1/governance/kill-switch` — Enable/disable global governance | CRITICAL |
| **GAP-091** | Degraded Mode API | `[D]` | GAP-070 | `POST /api/v1/governance/mode` — Set governance mode (NORMAL/DEGRADED/KILL) | CRITICAL |
| **GAP-092** | Conflict Resolution API | `[D]` | GAP-068 | `POST /api/v1/governance/resolve-conflict` — Manual conflict resolution | MEDIUM |
| **GAP-093** | Connector Registry API | `[B]` | GAP-059,060,063 | `GET/POST /api/v1/connectors` — List, register, test connectors | HIGH |
| **GAP-094** | Retrieval Mediator API | `[D]` | GAP-065 | `POST /api/v1/retrieval/execute` — Execute governed retrieval | HIGH |
| **GAP-095** | Boot Status API | `[D]` | GAP-067 | `GET /api/v1/governance/boot-status` — SPINE component health | LOW |

### T0 aos_sdk Integration Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-096** | SDK Governance Namespace | `[D]` | GAP-069,070 | `aos_sdk.governance.*` — Kill switch, mode control | CRITICAL |
| **GAP-097** | SDK Connector Namespace | `[L→GAP-093]` | GAP-059,060,063 | `aos_sdk.connectors.*` — HTTP, SQL, MCP operations | HIGH |
| **GAP-098** | SDK Retrieval Namespace | `[L→GAP-094]` | GAP-065 | `aos_sdk.retrieval.*` — Governed data retrieval | HIGH |

### T0 Database Persistence Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-099** | Runtime Switch Persistence | `[D]` | GAP-069,070 | Persist kill switch / degraded mode state | MEDIUM |
| **GAP-100** | Connector Registry DB | `[D]` | GAP-059,060,063 | `connectors` table for registered connectors | MEDIUM |
| **GAP-101** | Conflict Audit Log DB | `[D]` | GAP-068 | `conflict_resolutions` table for audit | LOW |

### T0 Dependency Graph

```
GAP-069 (KillSwitch) ──────────────┬──▶ GAP-090 (L2 API)
GAP-070 (DegradedMode) ────────────┤        │
                                   │        ▼
                                   └──▶ GAP-096 (SDK) ◀── GAP-099 (DB)

GAP-059,060,063 (Connectors) ─────▶ GAP-093 (L2 API)
                                        │
                                        ▼
                                   GAP-097 (SDK) ◀── GAP-100 (DB)

GAP-065 (RetrievalMediator) ──────▶ GAP-094 (L2 API)
                                        │
                                        ▼
                                   GAP-098 (SDK)

GAP-068 (ConflictResolver) ───────▶ GAP-092 (L2 API) ◀── GAP-101 (DB)

GAP-067 (BootGuard) ──────────────▶ GAP-095 (L2 API)
```

---

## T1 Wiring Gaps (GAP-102 to GAP-108)

### T1 L2 API Route Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-102** | Hallucination Check API | `[D]` | GAP-023 | `POST /api/v1/detection/hallucination` — Run hallucination check | HIGH |
| **GAP-103** | SOC2 Mapping API | `[D]` | GAP-025 | `GET /api/v1/compliance/soc2-controls` — List control mappings | MEDIUM |
| **GAP-104** | Override Authority API | `[D]` | GAP-034 | `POST /api/v1/governance/override` — Request override with authority | MEDIUM |
| **GAP-105** | Evidence Export API | `[D]` | GAP-027 | `GET /api/v1/exports/evidence/{run_id}` — Export evidence PDF | HIGH |

### T1 aos_sdk Integration Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-106** | SDK Evidence Namespace | `[L→GAP-105]` | GAP-027,058 | `aos_sdk.evidence.*` — Retrieve, export evidence | HIGH |
| **GAP-107** | SDK Compliance Namespace | `[L→GAP-103]` | GAP-025 | `aos_sdk.compliance.*` — SOC2 mappings | MEDIUM |
| **GAP-108** | SDK Detection Namespace | `[L→GAP-102]` | GAP-023 | `aos_sdk.detection.*` — Hallucination check | MEDIUM |

### T1 Dependency Graph

```
GAP-023 (Hallucination) ──────────▶ GAP-102 (L2 API)
                                        │
                                        ▼
                                   GAP-108 (SDK)

GAP-025 (SOC2Mapper) ─────────────▶ GAP-103 (L2 API)
                                        │
                                        ▼
                                   GAP-107 (SDK)

GAP-027,058 (Evidence) ───────────▶ GAP-105 (L2 API)
                                        │
                                        ▼
                                   GAP-106 (SDK)

GAP-034 (OverrideAuthority) ──────▶ GAP-104 (L2 API)
```

---

## T2 Wiring Gaps (GAP-109 to GAP-118)

### T2 L2 API Route Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-109** | Notification Channels API | `[D]` | GAP-036 | `GET/POST /api/v1/notifications/channels` — Manage channels | HIGH |
| **GAP-110** | Alert Log Link API | `[D]` | GAP-037 | `GET /api/v1/alerts/{id}/logs` — Get linked logs for alert | MEDIUM |
| **GAP-111** | Alert Fatigue API | `[D]` | GAP-038 | `GET /api/v1/alerts/fatigue-status` — Check fatigue state | MEDIUM |
| **GAP-112** | Job Scheduler API | `[D]` | GAP-039 | `GET/POST /api/v1/scheduler/jobs` — Manage scheduled jobs | HIGH |
| **GAP-113** | Customer Data Source API | `[D]` | GAP-040 | `GET/POST /api/v1/datasources` — Manage data sources | HIGH |
| **GAP-114** | Policy Snapshot API | `[D]` | GAP-044 | `GET/POST /api/v1/policies/snapshots` — Manage snapshots | HIGH |

### T2 aos_sdk Integration Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-115** | SDK Notifications Namespace | `[L→GAP-109]` | GAP-036,037 | `aos_sdk.notifications.*` — Send, list notifications | HIGH |
| **GAP-116** | SDK Alerts Namespace | `[L→GAP-110,111]` | GAP-037,038 | `aos_sdk.alerts.*` — Query, acknowledge alerts | HIGH |
| **GAP-117** | SDK Scheduler Namespace | `[L→GAP-112]` | GAP-039 | `aos_sdk.scheduler.*` — Schedule, cancel jobs | MEDIUM |
| **GAP-118** | SDK DataSources Namespace | `[L→GAP-113]` | GAP-040 | `aos_sdk.datasources.*` — Connect, sync sources | HIGH |

### T2 Dependency Graph

```
GAP-036 (NotifyChannels) ─────────▶ GAP-109 (L2 API)
GAP-037 (AlertLogLinker) ─────────▶ GAP-110 (L2 API)
                                   ├───────────────────▶ GAP-115 (SDK)
                                   └───────────────────▶ GAP-116 (SDK)

GAP-038 (AlertFatigue) ───────────▶ GAP-111 (L2 API) ──▶ GAP-116 (SDK)

GAP-039 (JobScheduler) ───────────▶ GAP-112 (L2 API)
                                        │
                                        ▼
                                   GAP-117 (SDK)

GAP-040 (CustomerDataSource) ─────▶ GAP-113 (L2 API)
                                        │
                                        ▼
                                   GAP-118 (SDK)

GAP-044 (PolicySnapshot) ─────────▶ GAP-114 (L2 API)
```

---

## T3 Wiring Gaps (GAP-119 to GAP-130)

### T3 L2 API Route Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-119** | Scope Selector API | `[D]` | GAP-052 | `GET/POST /api/v1/policies/scopes` — Manage policy scopes | HIGH |
| **GAP-120** | Usage Monitor API | `[D]` | GAP-053 | `GET /api/v1/monitors/usage` — Get usage metrics | MEDIUM |
| **GAP-121** | Health Monitor API | `[D]` | GAP-054 | `GET /api/v1/monitors/health` — Get health status | MEDIUM |
| **GAP-122** | Limit Enforcer API | `[D]` | GAP-055 | `GET/POST /api/v1/limits` — Manage limits/quotas | HIGH |
| **GAP-123** | Control Actions API | `[D]` | GAP-056 | `POST /api/v1/controls/execute` — Execute control action | HIGH |
| **GAP-124** | Alert Rules API | `[D]` | GAP-057 | `GET/POST /api/v1/alerts/rules` — Manage alert rules | HIGH |
| **GAP-125** | Policy Lifecycle API | `[D]` | GAP-064 | `POST /api/v1/policies/{id}/lifecycle` — Transition policy state | HIGH |

### T3 aos_sdk Integration Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-126** | SDK Scopes Namespace | `[L→GAP-119]` | GAP-052 | `aos_sdk.scopes.*` — Query, bind scopes | HIGH |
| **GAP-127** | SDK Monitors Namespace | `[L→GAP-120,121]` | GAP-053,054 | `aos_sdk.monitors.*` — Get usage/health | MEDIUM |
| **GAP-128** | SDK Limits Namespace | `[L→GAP-122]` | GAP-055 | `aos_sdk.limits.*` — Check, request limits | HIGH |
| **GAP-129** | SDK Controls Namespace | `[L→GAP-123]` | GAP-056 | `aos_sdk.controls.*` — Execute actions | HIGH |
| **GAP-130** | SDK PolicyLifecycle Namespace | `[L→GAP-125]` | GAP-064 | `aos_sdk.policy.lifecycle.*` — State transitions | HIGH |

### T3 Dependency Graph

```
GAP-052 (PolicyScope) ────────────▶ GAP-119 (L2 API)
                                        │
                                        ▼
                                   GAP-126 (SDK)

GAP-053,054 (Monitors) ───────────▶ GAP-120,121 (L2 APIs)
                                        │
                                        ▼
                                   GAP-127 (SDK)

GAP-055 (LimitEnforcer) ──────────▶ GAP-122 (L2 API)
                                        │
                                        ▼
                                   GAP-128 (SDK)

GAP-056 (ControlActions) ─────────▶ GAP-123 (L2 API)
                                        │
                                        ▼
                                   GAP-129 (SDK)

GAP-057 (AlertRules) ─────────────▶ GAP-124 (L2 API)

GAP-064 (PolicyLifecycle) ────────▶ GAP-125 (L2 API)
                                        │
                                        ▼
                                   GAP-130 (SDK)
```

---

## T4 Wiring Gaps (GAP-131 to GAP-136)

### T4 L2 API Route Gaps

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-131** | Lifecycle State API | `[D]` | GAP-086,089 | `GET /api/v1/lifecycle/{plane_id}/state` — Get current state | HIGH |
| **GAP-132** | Lifecycle Transition API | `[D]` | GAP-086 | `POST /api/v1/lifecycle/{plane_id}/transition` — Request transition | HIGH |
| **GAP-133** | Lifecycle Audit API | `[D]` | GAP-088 | `GET /api/v1/lifecycle/{plane_id}/audit` — Get audit history | MEDIUM |
| **GAP-134** | Lifecycle Stages API | `[B]` | GAP-071-082 | `GET /api/v1/lifecycle/{plane_id}/stages` — Get stage status | MEDIUM |

### T4 aos_sdk Integration Gaps

**Required Invariant Compliance:** `INV-W0-004` (Failure Semantics)

All SDK methods MUST:
- Return `SDKResult` with structured failure (FS-001)
- Categorize failures as TRANSIENT/PERMANENT/POLICY (FS-002)
- Include `retry_after_seconds` for TRANSIENT (FS-003)
- Include `policy_id` for POLICY failures (FS-004)

| Gap ID | Name | Type | Parent Gap | Invariants | Description | Priority |
|--------|------|------|------------|------------|-------------|----------|
| **GAP-135** | SDK Lifecycle L2 Binding | `[L→GAP-131,132]` | GAP-083-085 | INV-W0-004 | Wire KnowledgeSDK to L2 routes (currently in-memory only) | CRITICAL |
| **GAP-136** | SDK Lifecycle HTTP Client | `[L→GAP-135]` | GAP-083-085 | INV-W0-004 | HTTP client for aos_sdk.lifecycle.* methods | CRITICAL |

### T4 Dependency Graph

```
GAP-086 (LifecycleManager) ───────▶ GAP-131 (State API)
GAP-089 (StateMachine)            │  GAP-132 (Transition API)
                                  │        │
                                  │        ▼
                                  └──▶ GAP-135 (SDK L2 Binding)
                                            │
                                            ▼
GAP-083-085 (KnowledgeSDK) ──────────▶ GAP-136 (HTTP Client)

GAP-088 (AuditEvents) ────────────▶ GAP-133 (Audit API)

GAP-071-082 (Stages) ─────────────▶ GAP-134 (Stages API)
```

---

## Summary: Gap Relationship Analysis

### Independent Gaps (Can implement in any order within tier)

| Tier | Gap IDs | Count |
|------|---------|-------|
| T0 | GAP-090, 091, 092, 093, 094, 095, 096, 099, 100, 101 | 10 |
| T1 | GAP-102, 103, 104, 105 | 4 |
| T2 | GAP-109, 110, 111, 112, 113, 114 | 6 |
| T3 | GAP-119, 120, 121, 122, 123, 124, 125 | 7 |
| T4 | GAP-131, 132, 133, 134 | 4 |
| **Total Discrete** | | **31** |

### Linked Gaps (Require L2 API first)

| Tier | Gap ID | Depends On |
|------|--------|------------|
| T0 | GAP-097 | GAP-093 |
| T0 | GAP-098 | GAP-094 |
| T1 | GAP-106 | GAP-105 |
| T1 | GAP-107 | GAP-103 |
| T1 | GAP-108 | GAP-102 |
| T2 | GAP-115 | GAP-109 |
| T2 | GAP-116 | GAP-110, 111 |
| T2 | GAP-117 | GAP-112 |
| T2 | GAP-118 | GAP-113 |
| T3 | GAP-126 | GAP-119 |
| T3 | GAP-127 | GAP-120, 121 |
| T3 | GAP-128 | GAP-122 |
| T3 | GAP-129 | GAP-123 |
| T3 | GAP-130 | GAP-125 |
| T4 | GAP-135 | GAP-131, 132 |
| T4 | GAP-136 | GAP-135 |
| **Total Linked** | | **16** |

---

## Implementation Priority Matrix

### Critical Path (Must implement first)

| Order | Gap ID | Name | Rationale |
|-------|--------|------|-----------|
| 1 | GAP-090 | Kill Switch API | Ops safety control |
| 2 | GAP-091 | Degraded Mode API | Ops safety control |
| 3 | GAP-096 | SDK Governance Namespace | SDK must control governance |
| 4 | GAP-131 | Lifecycle State API | Expose T4 state queries |
| 5 | GAP-132 | Lifecycle Transition API | Enable SDK lifecycle operations |
| 6 | GAP-135 | SDK Lifecycle L2 Binding | Connect SDK to L2 routes |
| 7 | GAP-136 | SDK Lifecycle HTTP Client | Complete SDK→HTTP chain |

### High Priority

| Gap IDs | Count | Domain |
|---------|-------|--------|
| GAP-093, 094, 097, 098 | 4 | Connectors & Retrieval |
| GAP-105, 106 | 2 | Evidence Export |
| GAP-109, 112, 113, 115, 117, 118 | 6 | Notifications, Scheduler, DataSources |
| GAP-119, 122, 123, 124, 125, 126, 128, 129, 130 | 9 | Scopes, Limits, Controls, Policy |
| GAP-133, 134 | 2 | Lifecycle Audit & Stages |

### Medium/Low Priority

| Gap IDs | Count | Domain |
|---------|-------|--------|
| GAP-092, 095, 099, 100, 101 | 5 | Conflict Resolution, Boot, DB |
| GAP-102, 103, 104, 107, 108 | 5 | Detection, Compliance, Override |
| GAP-110, 111, 114, 116 | 4 | Alerts, Snapshots |
| GAP-120, 121, 127 | 3 | Monitors |

---

## Consolidated Gap Count

| Category | T0 | T1 | T2 | T3 | T4 | Total |
|----------|----|----|----|----|----|----|
| L4 Services (existing) | 13 | 11 | 14 | 31 | 19 | **85** |
| L2 API Routes (new) | 6 | 4 | 6 | 7 | 4 | **27** |
| aos_sdk Integration (new) | 3 | 3 | 4 | 5 | 2 | **17** |
| Database Persistence (new) | 3 | 0 | 0 | 0 | 0 | **3** |
| **Total per Tier** | **25** | **18** | **24** | **43** | **25** | **132** |

**New Gaps (v1.0):** 47 (GAP-090 to GAP-136)

---

## Section 2: Execution Coupling Gaps (GAP-137 to GAP-143)

**GPT Analysis Reference:** "Implemented ≠ Integrated" — checkers exist but execution coupling is missing.

**Required Invariant Compliance:** `INV-W0-001` (ExecutionContext)

All gaps in this section MUST:
- Accept `ExecutionContext` as parameter (EC-001)
- Propagate context to downstream calls (EC-002)
- Include context in audit emissions (EC-003)
- Fail-closed if context is missing (EC-004)

### Runner Integration Gaps

| Gap ID | Name | Type | Parent Gap | Invariants | Description | Priority |
|--------|------|------|------------|------------|-------------|----------|
| **GAP-137** | RetrievalMediator Runner Hook | `[D]` | GAP-065 | INV-W0-001 | Wire RetrievalMediator as **mandatory** in LLM path — no bypass allowed | **CRITICAL** |
| **GAP-138** | HallucinationDetector Runner Hook | `[D]` | GAP-023 | INV-W0-001 | Wire HallucinationDetector to runner output — annotate responses | **HIGH** |
| **GAP-139** | Monitor/Limit Runner Enforcement | `[B]` | GAP-053-055 | INV-W0-001 | Wire UsageMonitor + LimitEnforcer into runner step loop | **HIGH** |
| **GAP-140** | StepEnforcement Event Bus | `[D]` | GAP-016 | INV-W0-001 | Emit enforcement events to EventReactor for audit | MEDIUM |

### MCP Control Plane Gaps

| Gap ID | Name | Type | Parent Gap | Invariants | Description | Priority |
|--------|------|------|------------|------------|-------------|----------|
| **GAP-141** | MCP Server Registration | `[D]` | GAP-063 | INV-W0-001 | `mcp_servers` table + registration API for external MCP servers | **HIGH** |
| **GAP-142** | MCP Tool→Policy Mapping | `[L→GAP-141]` | GAP-063,087 | INV-W0-001 | Map MCP tool calls to policy gates — enforce before invocation | **HIGH** |
| **GAP-143** | MCP Audit Evidence | `[L→GAP-141]` | GAP-063,088 | INV-W0-001 | Emit compliance-grade audit for all MCP tool invocations | **HIGH** |

---

## Section 3: Real Adapter Gaps (GAP-144 to GAP-153)

**GPT Analysis Reference:** "Stub operations" — adapters exist as contracts but no real implementations.

### Vector Store Adapters

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-144** | Pinecone Adapter | `[D]` | GAP-065 | Real Pinecone vector store integration with API key management | **HIGH** |
| **GAP-145** | Weaviate Adapter | `[D]` | GAP-065 | Real Weaviate vector store integration | MEDIUM |
| **GAP-146** | pgvector Production Config | `[D]` | GAP-065 | Production-grade pgvector with HNSW tuning, connection pooling | **HIGH** |

### File Storage Adapters

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-147** | S3 Storage Adapter | `[D]` | GAP-059 | Real S3/MinIO file storage with presigned URLs, multipart upload | **HIGH** |
| **GAP-148** | GCS Storage Adapter | `[D]` | GAP-059 | Google Cloud Storage adapter | MEDIUM |

### Serverless Adapters

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-149** | Lambda Adapter | `[D]` | GAP-059 | AWS Lambda invocation with IAM, timeout, cost tracking | **HIGH** |
| **GAP-150** | Cloud Functions Adapter | `[D]` | GAP-059 | GCP Cloud Functions adapter | MEDIUM |

### Notification Delivery

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-151** | SMTP Delivery Client | `[D]` | GAP-036 | Real SMTP with retry, bounce handling, delivery evidence | **HIGH** |
| **GAP-152** | Slack Client | `[D]` | GAP-036 | Real Slack API client with rate limits, error handling | **HIGH** |
| **GAP-153** | Webhook Retry Engine | `[D]` | GAP-036 | Webhook delivery with exponential backoff, dead letter queue | **HIGH** |

---

## Section 4: Job Execution Gaps (GAP-154 to GAP-158)

**GPT Analysis Reference:** "Jobs never run" — scheduler models exist but no executor binding.

**Required Invariant Compliance:** `INV-W0-002` (KillSwitch), `INV-W0-003` (Idempotency)

All gaps in this section MUST:
- Use `KillSwitchGuard` at start, heartbeat, and commit (KS-001 to KS-004)
- Use `IdempotencyKey` for state-mutating operations (IDEM-001 to IDEM-004)

| Gap ID | Name | Type | Parent Gap | Invariants | Description | Priority |
|--------|------|------|------------|------------|-------------|----------|
| **GAP-154** | APScheduler Binding | `[D]` | GAP-039 | INV-W0-002 | Bind JobScheduler to APScheduler for cron + one-time execution | **CRITICAL** |
| **GAP-155** | Job Queue Worker | `[D]` | GAP-039 | INV-W0-002, INV-W0-003 | Background worker that processes job queue (Redis-backed) | **CRITICAL** |
| **GAP-156** | Job Failure Retry | `[L→GAP-155]` | GAP-039 | INV-W0-003 | Retry failed jobs with backoff, max attempts, dead letter | **HIGH** |
| **GAP-157** | Job Progress Reporting | `[L→GAP-155]` | GAP-039 | INV-W0-002 | Real-time job progress updates via SSE/WebSocket | MEDIUM |
| **GAP-158** | Job Audit Evidence | `[L→GAP-155]` | GAP-039,088 | INV-W0-001 | Emit audit events for job start/complete/fail | **HIGH** |

---

## Section 5: Lifecycle Real Execution Gaps (GAP-159 to GAP-164)

**GPT Analysis Reference:** "Lifecycle jobs are fake" — stage handlers simulate, don't execute.

**Required Invariant Compliance:** `INV-W0-002` (KillSwitch), `INV-W0-003` (Idempotency)

All gaps in this section MUST:
- Use `KillSwitchGuard` with capability `lifecycle.{stage}` (KS-001 to KS-004)
- Use `IdempotencyKey(job_id, plane_id)` for stage execution (IDEM-001 to IDEM-004)
- Support checkpoint-based resume for idempotent replay (IDEM-003)

| Gap ID | Name | Type | Parent Gap | Invariants | Description | Priority |
|--------|------|------|------------|------------|-------------|----------|
| **GAP-159** | IngestHandler Real Execution | `[D]` | GAP-073 | INV-W0-002, INV-W0-003 | Replace `_simulate_ingestion` with real data source reads | **CRITICAL** |
| **GAP-160** | IndexHandler Real Execution | `[D]` | GAP-074 | INV-W0-002, INV-W0-003 | Replace `_simulate_indexing` with real embedding generation + pgvector insert | **CRITICAL** |
| **GAP-161** | ClassifyHandler Real Execution | `[D]` | GAP-075 | INV-W0-002, INV-W0-003 | Replace `_simulate_classification` with real PII detection + sensitivity scoring | **HIGH** |
| **GAP-162** | Lifecycle Worker Orchestration | `[B]` | GAP-086 | INV-W0-002, INV-W0-003 | Background worker for long-running lifecycle transitions (ingest, index, classify) | **CRITICAL** |
| **GAP-163** | Lifecycle Progress Tracking | `[L→GAP-162]` | GAP-086 | INV-W0-002 | Track progress % for async operations, expose via API | **HIGH** |
| **GAP-164** | Lifecycle Failure Recovery | `[L→GAP-162]` | GAP-086 | INV-W0-003 | Resume failed lifecycle operations from checkpoint | **HIGH** |

---

## Section 6: Database Migration Gaps (GAP-165 to GAP-170)

**GPT Analysis Reference:** "Ready for DB migration" appears ~40 times — no Alembic migrations exist.

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-165** | T1 Evidence Migration | `[D]` | GAP-058 | Alembic migration for `retrieval_evidence` table | **HIGH** |
| **GAP-166** | T2 Notifications Migration | `[D]` | GAP-036-038 | Alembic migrations for `notification_channels`, `alerts`, `alert_rules` | **HIGH** |
| **GAP-167** | T2 DataSources Migration | `[D]` | GAP-040 | Alembic migration for `customer_data_sources` table | **HIGH** |
| **GAP-168** | T3 Policy Scopes Migration | `[D]` | GAP-052 | Alembic migration for `policy_scopes` table | **HIGH** |
| **GAP-169** | T3 Monitors/Limits Migration | `[B]` | GAP-053-055 | Alembic migrations for `usage_monitors`, `health_monitors`, `limit_configs` | **HIGH** |
| **GAP-170** | T4 Knowledge Planes Migration | `[D]` | GAP-086 | Alembic migration for `knowledge_planes`, `lifecycle_audit_events` tables | **CRITICAL** |

---

## Section 7: Credential & Security Gaps (GAP-171 to GAP-174)

**GPT Analysis Reference:** "Data source connections" — no credential vault integration.

| Gap ID | Name | Type | Parent Gap | Description | Priority |
|--------|------|------|------------|-------------|----------|
| **GAP-171** | Credential Vault Integration | `[D]` | GAP-040,059-063 | HashiCorp Vault / AWS Secrets Manager integration for connector credentials | **CRITICAL** |
| **GAP-172** | Connection Pool Management | `[D]` | GAP-060 | SQL connection pools with health probes, per-tenant isolation | **HIGH** |
| **GAP-173** | IAM Integration | `[D]` | GAP-149,150 | AWS IAM / GCP Service Account integration for serverless | **HIGH** |
| **GAP-174** | Execution Sandboxing | `[D]` | GAP-149,150 | Isolated execution for untrusted code (container/firecracker) | MEDIUM |

---

## Revised Gap Summary

### Gap Count by Category

| Category | Gap Range | Count | Priority Split |
|----------|-----------|-------|----------------|
| L2 API Routes | GAP-090→134 | 27 | 7 CRITICAL, 15 HIGH |
| aos_sdk Integration | GAP-096→136 | 17 | 4 CRITICAL, 10 HIGH |
| T0 Database | GAP-099→101 | 3 | 0 CRITICAL, 2 MEDIUM |
| **Execution Coupling** | GAP-137→143 | **7** | 1 CRITICAL, 5 HIGH |
| **Real Adapters** | GAP-144→153 | **10** | 0 CRITICAL, 8 HIGH |
| **Job Execution** | GAP-154→158 | **5** | 2 CRITICAL, 3 HIGH |
| **Lifecycle Real Exec** | GAP-159→164 | **6** | 3 CRITICAL, 3 HIGH |
| **Database Migrations** | GAP-165→170 | **6** | 1 CRITICAL, 5 HIGH |
| **Credentials/Security** | GAP-171→174 | **4** | 1 CRITICAL, 2 HIGH |

### New Totals (v1.1)

| Metric | v1.0 | v1.1 | Delta |
|--------|------|------|-------|
| New Wiring Gaps | 47 | 85 | +38 |
| Total Gaps | 132 | 170 | +38 |
| CRITICAL Gaps | 7 | 19 | +12 |
| HIGH Gaps | 24 | 53 | +29 |

---

## Dependency Analysis (v1.1)

### CRITICAL Path (19 gaps)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CRITICAL PATH (Blocks Shippability)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PHASE 1: Execution Coupling (Unblocks RAG Mediation)                          │
│  ═════════════════════════════════════════════════════                          │
│  GAP-137 → RetrievalMediator Runner Hook (NO BYPASS)                           │
│  GAP-154 → APScheduler Binding                                                 │
│  GAP-155 → Job Queue Worker                                                    │
│                                                                                 │
│  PHASE 2: Lifecycle Real Execution (Unblocks Knowledge Onboarding)             │
│  ══════════════════════════════════════════════════════════════════            │
│  GAP-159 → IngestHandler Real Execution                                        │
│  GAP-160 → IndexHandler Real Execution                                         │
│  GAP-162 → Lifecycle Worker Orchestration                                      │
│  GAP-170 → T4 Knowledge Planes Migration                                       │
│                                                                                 │
│  PHASE 3: API Surface (Unblocks UI & SDK)                                      │
│  ═════════════════════════════════════════                                      │
│  GAP-090 → Kill Switch API                                                     │
│  GAP-091 → Degraded Mode API                                                   │
│  GAP-096 → SDK Governance Namespace                                            │
│  GAP-131 → Lifecycle State API                                                 │
│  GAP-132 → Lifecycle Transition API                                            │
│  GAP-135 → SDK Lifecycle L2 Binding                                            │
│  GAP-136 → SDK Lifecycle HTTP Client                                           │
│                                                                                 │
│  PHASE 4: Credentials & Adapters (Unblocks Real Connections)                   │
│  ════════════════════════════════════════════════════════════                   │
│  GAP-171 → Credential Vault Integration                                        │
│  GAP-144 → Pinecone Adapter (or GAP-146 pgvector production)                   │
│  GAP-147 → S3 Storage Adapter                                                  │
│  GAP-149 → Lambda Adapter                                                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Gap Relationship Graph (v1.1)

```
                              ┌─────────────────────────────────────┐
                              │       GOVERNANCE KERNEL (L4)        │
                              │        85 gaps - COMPLETE           │
                              └─────────────────────────────────────┘
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              │                               │                               │
              ▼                               ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│   EXECUTION COUPLING    │   │     DATABASE LAYER      │   │    REAL ADAPTERS        │
│      (7 gaps)           │   │      (6 gaps)           │   │     (10 gaps)           │
│                         │   │                         │   │                         │
│ GAP-137: Mediator Hook  │   │ GAP-165: T1 Migration   │   │ GAP-144: Pinecone       │
│ GAP-138: Hallucination  │   │ GAP-166: T2 Migration   │   │ GAP-146: pgvector       │
│ GAP-139: Monitor/Limit  │   │ GAP-167: DataSources    │   │ GAP-147: S3             │
│ GAP-140: Event Bus      │   │ GAP-168: Scopes         │   │ GAP-149: Lambda         │
│ GAP-141: MCP Registry   │   │ GAP-169: Monitors       │   │ GAP-151: SMTP           │
│ GAP-142: MCP Policy     │   │ GAP-170: Lifecycle      │   │ GAP-152: Slack          │
│ GAP-143: MCP Audit      │   │                         │   │ GAP-153: Webhook        │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
              │                               │                               │
              └───────────────────────────────┼───────────────────────────────┘
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              │                               │                               │
              ▼                               ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│    JOB EXECUTION        │   │  LIFECYCLE REAL EXEC    │   │   CREDENTIALS/SEC       │
│      (5 gaps)           │   │      (6 gaps)           │   │     (4 gaps)            │
│                         │   │                         │   │                         │
│ GAP-154: APScheduler    │──▶│ GAP-159: Real Ingest    │◀──│ GAP-171: Vault          │
│ GAP-155: Queue Worker   │──▶│ GAP-160: Real Index     │   │ GAP-172: Conn Pool      │
│ GAP-156: Retry Logic    │   │ GAP-161: Real Classify  │   │ GAP-173: IAM            │
│ GAP-157: Progress       │   │ GAP-162: Worker Orch    │   │ GAP-174: Sandbox        │
│ GAP-158: Job Audit      │   │ GAP-163: Progress       │   │                         │
│                         │   │ GAP-164: Recovery       │   │                         │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────────────┐
                              │         L2 API ROUTES               │
                              │          (27 gaps)                  │
                              └─────────────────────────────────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────────────┐
                              │         aos_sdk METHODS             │
                              │          (17 gaps)                  │
                              └─────────────────────────────────────┘
```

---

## Shippability Assessment (v1.1)

### Before (v1.0 Analysis)

| Aspect | Score | Blocker |
|--------|-------|---------|
| Design | 9.5/10 | None |
| Test Discipline | 10/10 | None |
| Shippability | **5/10** | L2 APIs, SDK |
| Customer Usability | **4/10** | Real execution |

### After (v1.1 Analysis)

| Aspect | Score | Blocker |
|--------|-------|---------|
| Design | 9.5/10 | None |
| Test Discipline | 10/10 | None |
| Shippability | **5/10** | +38 gaps identified |
| Customer Usability | **4/10** | Execution coupling, real adapters |
| **Path to 8/10** | +19 CRITICAL gaps | Clear roadmap |

---

## Minimum Shippable Product (MSP) — 19 Critical Gaps

To reach **80% client integration coverage**, complete these 19 gaps:

| Phase | Gaps | Focus | Unblocks |
|-------|------|-------|----------|
| **1** | GAP-137, 154, 155 | Execution Coupling | RAG mediation works |
| **2** | GAP-159, 160, 162, 170 | Lifecycle Real Exec | Knowledge onboarding works |
| **3** | GAP-090, 091, 096, 131, 132, 135, 136 | API Surface | UI & SDK work |
| **4** | GAP-171, 144/146, 147, 149 | Real Connections | External systems work |

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-21 | v1.0 | Systems Architect | Initial wiring gap ledger from cascade analysis |
| 2026-01-21 | v1.1 | Systems Architect | Added 38 gaps from GPT analysis: execution coupling (7), real adapters (10), job execution (5), lifecycle real exec (6), database migrations (6), credentials (4) |
| 2026-01-21 | v1.2 | Systems Architect | Added Execution Invariants Reference section (INV-W0-001 to INV-W0-004) with acceptance criteria; Updated Sections 2, 4, 5 and T4 SDK gaps with invariant compliance requirements |

---

**End of Gap Wiring Ledger v1.2**

---

## Appendix A: GPT Analysis Reference

### Key Insights Applied

| GPT Finding | Gap(s) Added | Impact |
|-------------|--------------|--------|
| "Implemented ≠ Integrated" | GAP-137→143 | Execution coupling |
| "Jobs never run" | GAP-154→158 | Job execution |
| "Lifecycle jobs are fake" | GAP-159→164 | Real lifecycle |
| "Ready for DB migration ×40" | GAP-165→170 | Database persistence |
| "Stub operations" | GAP-144→153 | Real adapters |
| "No credential vault" | GAP-171→174 | Security/credentials |
| "MCP is connector not control plane" | GAP-141→143 | MCP enforcement |

### GPT Verdict Applied

> "You built the **hard part first** — governance correctness.
> Now you must build the **boring part** — wiring, persistence, APIs, SDKs."

This ledger captures the "boring part" as 85 explicit gaps with clear dependencies and priorities.
