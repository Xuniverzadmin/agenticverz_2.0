# AOS Domain Architecture - Mental Map

**Status:** ACTIVE
**Date:** 2026-01-21
**Reference:** PIN-454, DOMAINS_E2E_SCAFFOLD_V3.md

---

## 1. Customer Lifecycle Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER LIFECYCLE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   ONBOARD    │───▶│   OPERATE    │───▶│   OFFBOARD   │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ • Register   │    │ • Run        │    │ • Deregister │                   │
│  │ • Verify     │    │ • Monitor    │    │ • Verify     │                   │
│  │ • Ingest     │    │ • Enforce    │    │ • Deactivate │                   │
│  │ • Index      │    │ • Incident   │    │ • Archive    │                   │
│  │ • Classify   │    │ • Learn      │    │ • Purge      │                   │
│  │ • Activate   │    │ • Export     │    │              │                   │
│  │ • Govern     │    │              │    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Domain Interaction During a Run

```
                              CUSTOMER REQUEST
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATION DOMAIN                                   │
│  "How do agents access customer environment?"                               │
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │ Data Source │   │  Knowledge  │   │  Connector  │   │  Mediation  │     │
│  │  Registry   │──▶│   Planes    │──▶│   Layer     │──▶│   Layer     │     │
│  │  (GAP-055)  │   │  (GAP-056)  │   │(GAP-059-64) │   │  (GAP-065)  │     │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │
│                                                              │               │
└──────────────────────────────────────────────────────────────│───────────────┘
                                                               │
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          POLICY DOMAIN                                       │
│  "How is behavior controlled?"                                              │
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │   Scope     │   │  Monitors   │   │   Limits    │   │  Actions    │     │
│  │  Selector   │──▶│ (what to    │──▶│ (hard caps) │──▶│ (on breach) │     │
│  │(GAP-001-04) │   │  observe)   │   │(GAP-009-12) │   │(GAP-013-16) │     │
│  └─────────────┘   │(GAP-005-08) │   └─────────────┘   └─────────────┘     │
│                    └─────────────┘          │                │              │
│                                             ▼                ▼              │
│                    ┌────────────────────────────────────────────┐          │
│                    │         ENFORCEMENT ENGINE                  │          │
│                    │  • Binding moment (GAP-031)                │          │
│                    │  • Failure mode (GAP-035)                  │          │
│                    │  • Conflict resolution (GAP-068)           │          │
│                    └────────────────────────────────────────────┘          │
│                                             │                               │
└─────────────────────────────────────────────│───────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐
│     ACTIVITY DOMAIN       │  │    INCIDENTS DOMAIN       │  │      LOGS DOMAIN          │
│ "What ran / is running?"  │  │  "What went wrong?"       │  │  "What is the truth?"     │
│                           │  │                           │  │                           │
│ • Live runs               │  │ • Policy violations       │  │ • LLM Run Records         │
│ • Completed runs          │  │ • Execution failures      │  │ • System Records          │
│ • Traces & Steps          │  │ • Hallucinations          │  │ • Audit Ledger            │
│ • Signals & Alerts        │  │ • Recovery actions        │  │ • Retrieval Evidence      │
│                           │  │                           │  │                           │
│ GAP-017-19 (alerting)     │  │ GAP-023 (hallucination)   │  │ GAP-025-27 (export)       │
│ GAP-028-30 (runtime)      │  │ GAP-024 (inflection)      │  │ GAP-058 (evidence)        │
│ GAP-049 (fatigue)         │  │ GAP-069-70 (kill/degrade) │  │                           │
└───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘
```

---

## 3. Customer Environment Onboarding Flow

This is the flow for onboarding customer data sources via `aos_sdk`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CUSTOMER ENVIRONMENT ONBOARDING (aos_sdk)                       │
│                                                                              │
│  Stage 1: REGISTER                                                          │
│  ────────────────                                                           │
│  aos_sdk.register_data_source(                                              │
│      type="POSTGRES",                                                       │
│      connection_config={...},                                               │
│      credential_ref="vault://cus/db/prod"                              │
│  )                                                                          │
│  → Creates CustomerDataSource record (GAP-055)                              │
│  → Status: REGISTERED                                                       │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 2: VERIFY                                                            │
│  ───────────────                                                            │
│  aos_sdk.verify_data_source(source_id)                                      │
│  → Test connection (read-only)                                              │
│  → Validate credentials                                                     │
│  → Check permissions (least privilege)                                      │
│  → Status: VERIFIED | VERIFICATION_FAILED                                   │
│  Implementation: GAP-039, GAP-072                                           │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 3: INGEST                                                            │
│  ──────────────                                                             │
│  aos_sdk.ingest_data_source(source_id, options={...})                       │
│  → Pull schema metadata                                                     │
│  → Detect PII columns                                                       │
│  → Hash content for integrity                                               │
│  → Status: INGESTING → INGESTED                                             │
│  Implementation: GAP-040, GAP-073                                           │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 4: INDEX                                                             │
│  ─────────────                                                              │
│  aos_sdk.index_data_source(source_id)                                       │
│  → Chunk documents                                                          │
│  → Generate embeddings                                                      │
│  → Store in vector index                                                    │
│  → Status: INDEXING → INDEXED                                               │
│  Implementation: GAP-040, GAP-074                                           │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 5: CLASSIFY                                                          │
│  ────────────────                                                           │
│  aos_sdk.classify_data_source(source_id, sensitivity="CONFIDENTIAL")        │
│  → Assign sensitivity level (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED)       │
│  → Determine default policy (ALLOW/DENY)                                    │
│  → Status: CLASSIFIED                                                       │
│  Implementation: GAP-044, GAP-075                                           │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 6: ACTIVATE (Create Knowledge Plane)                                 │
│  ─────────────────────────────────────────                                  │
│  aos_sdk.create_knowledge_plane(                                            │
│      name="Customer CRM Data",                                              │
│      source_ids=[source_id],                                                │
│      default_policy="DENY",                                                 │
│      sensitivity="CONFIDENTIAL"                                             │
│  )                                                                          │
│  → Bundle sources into policy-addressable unit                              │
│  → Require owner confirmation                                               │
│  → Status: ACTIVATING → ACTIVE                                              │
│  Implementation: GAP-056, GAP-041, GAP-076                                  │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 7: GOVERN (Bind to Policies)                                         │
│  ─────────────────────────────────                                          │
│  aos_sdk.create_policy(                                                     │
│      scope={"plane_ids": [plane_id]},                                       │
│      monitors=["token_usage", "rag_access"],                                │
│      limits={"tokens_per_run": 10000},                                      │
│      actions={"on_breach": "STOP"}                                          │
│  )                                                                          │
│  → Plane becomes governed                                                   │
│  → All access routed through mediation layer                                │
│  → Evidence emitted on every access                                         │
│  Implementation: GAP-042, GAP-077                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Customer Environment Offboarding Flow

Flow for offboarding customer data sources:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              CUSTOMER ENVIRONMENT OFFBOARDING (aos_sdk)                      │
│                                                                              │
│  Stage 1: DEREGISTER                                                        │
│  ───────────────────                                                        │
│  aos_sdk.deregister_knowledge_plane(plane_id, reason="migration")           │
│  → Mark plane as DEREGISTERING                                              │
│  → Block new runs that reference this plane                                 │
│  → Wait for in-flight runs to complete                                      │
│  Implementation: GAP-078                                                    │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 2: VERIFY CLEAN                                                      │
│  ─────────────────────                                                      │
│  aos_sdk.verify_plane_clean(plane_id)                                       │
│  → Verify no active policies reference plane                                │
│  → Verify no pending runs                                                   │
│  → Generate audit report                                                    │
│  → Status: CLEAN | BLOCKED (reason)                                         │
│  Implementation: GAP-079                                                    │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 3: DEACTIVATE                                                        │
│  ───────────────────                                                        │
│  aos_sdk.deactivate_knowledge_plane(plane_id)                               │
│  → Unbind from all policies                                                 │
│  → Remove from connector registry                                           │
│  → Revoke credentials                                                       │
│  → Status: DEACTIVATED                                                      │
│  Implementation: GAP-080                                                    │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 4: ARCHIVE (Optional)                                                │
│  ─────────────────────────                                                  │
│  aos_sdk.archive_plane_evidence(plane_id, retention_days=365)               │
│  → Export all retrieval evidence                                            │
│  → Export audit logs                                                        │
│  → Store in cold storage                                                    │
│  → Status: ARCHIVED                                                         │
│  Implementation: GAP-081                                                    │
│                                                                              │
│                           │                                                  │
│                           ▼                                                  │
│  Stage 5: PURGE (Optional, requires approval)                               │
│  ────────────────────────────────────────────                               │
│  aos_sdk.purge_plane_data(plane_id, approval_token="...")                   │
│  → Delete vector embeddings                                                 │
│  → Delete metadata                                                          │
│  → Tombstone audit records (keep IDs, remove content)                       │
│  → Status: PURGED                                                           │
│  Implementation: GAP-082                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Run Execution Flow (Domain Interactions)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RUN EXECUTION FLOW                                   │
│                                                                              │
│  aos_sdk.post_goal(agent_id, goal, context)                                 │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. SCOPE RESOLUTION (Policy Domain)                                 │    │
│  │    • Which policies apply to this run?                              │    │
│  │    • Resolve by: tenant → project → agent → api_key → human_actor   │    │
│  │    • Snapshot resolved policies (GAP-004, GAP-028)                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 2. PRE-RUN ENFORCEMENT (Policy Domain)                              │    │
│  │    • Check binding moment: RUN_START policies evaluated now         │    │
│  │    • Check budget available                                         │    │
│  │    • Check rate limits                                              │    │
│  │    • DECISION: ALLOW | BLOCK | QUEUE                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│            ┌──────────────┼──────────────┐                                  │
│            │              │              │                                   │
│         BLOCK          QUEUE         ALLOW                                   │
│            │              │              │                                   │
│            ▼              ▼              ▼                                   │
│       ┌────────┐    ┌────────┐    ┌─────────────────────────────────────┐   │
│       │Incident│    │Activity│    │ 3. EXECUTION LOOP                   │   │
│       │Created │    │Queued  │    │    For each step:                   │   │
│       └────────┘    └────────┘    │    ┌───────────────────────────────┐│   │
│                                   │    │ a. Plan step (LLM decides)    ││   │
│                                   │    │ b. Pre-step policy check      ││   │
│                                   │    │ c. Execute skill              ││   │
│                                   │    │    → If data access:          ││   │
│                                   │    │      → MEDIATION LAYER        ││   │
│                                   │    │      → Policy gate            ││   │
│                                   │    │      → Evidence emission      ││   │
│                                   │    │ d. Post-step policy check     ││   │
│                                   │    │ e. Emit trace step            ││   │
│                                   │    │ f. Check mid-execution policy ││   │
│                                   │    └───────────────────────────────┘│   │
│                                   └─────────────────────────────────────┘   │
│                                              │                               │
│                           ┌──────────────────┼──────────────────┐           │
│                           │                  │                  │           │
│                      VIOLATION           SUCCESS            FAILURE         │
│                           │                  │                  │           │
│                           ▼                  ▼                  ▼           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. POST-RUN PROCESSING                                              │   │
│  │                                                                      │   │
│  │  ACTIVITY           INCIDENTS           LOGS              POLICY    │   │
│  │  • Status update    • Create incident   • Finalize trace  • Update  │   │
│  │  • Signal emit      • Link to run       • LLM run record    budget  │   │
│  │  • Alert check      • Maybe proposal    • Audit entry      usage    │   │
│  │                                                            • Learn? │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Domain Overview

| Domain | Core Question | Key Objects | Primary Gaps |
|--------|---------------|-------------|--------------|
| **Integration** | How do agents access customer environment? | DataSource, KnowledgePlane, Connector | GAP-055-065, GAP-071-077 |
| **Policy** | How is behavior controlled? | PolicyRule, Limit, AlertConfig, Scope | GAP-001-016, GAP-020-022, GAP-031-035, GAP-068 |
| **Activity** | What ran / is running? | Run, Trace, TraceStep, Signal | GAP-017-019, GAP-028-030, GAP-049, GAP-052 |
| **Incidents** | What went wrong? | Incident, Violation, PolicyProposal | GAP-023-024, GAP-069-070 |
| **Logs** | What is the raw truth? | LLMRunRecord, SystemRecord, AuditLedger, Evidence | GAP-025-027, GAP-058, GAP-081-082 |
| **Governance Spine** | Is enforcement working? | EventReactor, BootGuard, RAC | GAP-046-054, GAP-067 |

---

## 7. Gap Coverage Matrix

| Lifecycle Stage | Integration | Policy | Activity | Incidents | Logs |
|-----------------|-------------|--------|----------|-----------|------|
| **ONBOARD** | | | | | |
| → Register | GAP-055, GAP-071 | - | - | - | - |
| → Verify | GAP-039, GAP-072 | - | - | - | - |
| → Ingest | GAP-040, GAP-073 | - | - | - | - |
| → Index | GAP-040, GAP-074 | - | - | - | - |
| → Classify | GAP-044, GAP-075 | - | - | - | - |
| → Activate | GAP-041, GAP-076 | - | - | - | GAP-058 |
| → Govern | GAP-042, GAP-077 | GAP-056 | - | - | - |
| **OPERATE** | | | | | |
| → Pre-run | GAP-065 | GAP-031,035 | GAP-028 | - | - |
| → Execute | GAP-059-64 | GAP-016,030 | Traces | - | GAP-058 |
| → Monitor | - | GAP-005-08 | GAP-017-19 | - | - |
| → Enforce | GAP-065 | GAP-013-16 | GAP-049 | GAP-023,24 | - |
| → Post-run | - | GAP-068 | - | GAP-069,70 | GAP-025-27 |
| **OFFBOARD** | | | | | |
| → Deregister | GAP-078 | - | - | - | - |
| → Verify clean | GAP-079 | - | - | - | - |
| → Deactivate | GAP-080 | - | - | - | - |
| → Archive | GAP-081 | - | - | - | GAP-081 |
| → Purge | GAP-082 | - | - | - | GAP-082 |
| **SDK** | | | | | |
| → Knowledge plane methods | GAP-083 | - | - | - | - |
| → Data source methods | GAP-084 | - | - | - | - |
| → Async/streaming | GAP-085 | - | - | - | - |
| **FRAMEWORK** | | | | | |
| → State Machine | GAP-089 | - | - | - | - |
| → LifecycleManager | GAP-086 | - | - | - | - |
| → Policy Gates | - | GAP-087 | - | - | - |
| → Audit Events | - | - | - | - | GAP-088 |

---

## 8. Lifecycle Orchestration Framework

The lifecycle gaps (7.16-7.18) require a binding framework (7.15) to be coherent.

**Architectural Principle:**
> Lifecycle operations are governance-controlled, not user-controlled.
> SDK calls **request** transitions. LifecycleManager **decides**. Policy + state machine **arbitrate**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     KnowledgeLifecycleManager (GAP-086)                     │
│                           THE ORCHESTRATOR                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐       │
│  │  State Machine    │  │  Policy Gates     │  │  Audit Emitter    │       │
│  │    (GAP-089)      │  │    (GAP-087)      │  │    (GAP-088)      │       │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘       │
│                                  │                                          │
│                                  ▼                                          │
│           ┌───────────────────────┼───────────────────────┐                │
│           │                       │                       │                │
│           ▼                       ▼                       ▼                │
│   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐             │
│   │   ONBOARDING    │ │   OFFBOARDING   │ │   SDK SURFACE   │             │
│   │   (GAP-071→077) │ │   (GAP-078→082) │ │   (GAP-083→085) │             │
│   └─────────────────┘ └─────────────────┘ └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Implementation Order:**
1. GAP-089 (State Machine) → 2. GAP-086 (Manager) → 3. GAP-088 (Audit) → 4. GAP-087 (Gates) → 5-7. Stages/SDK

---

## 9. Complete Domain Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AOS DOMAIN MODEL                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     INTEGRATION DOMAIN                               │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │    │
│  │  │ DataSource    │  │ KnowledgePlane│  │ Connector     │            │    │
│  │  │ ────────────  │  │ ────────────  │  │ ────────────  │            │    │
│  │  │ • id          │──│ • plane_id    │──│ • type        │            │    │
│  │  │ • type        │  │ • sources[]   │  │ • config      │            │    │
│  │  │ • config      │  │ • sensitivity │  │ • credentials │            │    │
│  │  │ • status      │  │ • default_pol │  │ • health      │            │    │
│  │  │ • lifecycle   │  │ • lifecycle   │  └───────────────┘            │    │
│  │  └───────────────┘  └───────────────┘                               │    │
│  │         │                   │                                        │    │
│  │         │    REGISTER → VERIFY → INGEST → INDEX → CLASSIFY          │    │
│  │         │         → ACTIVATE → GOVERN → ... → DEACTIVATE → PURGE    │    │
│  │         │                   │                                        │    │
│  └─────────│───────────────────│────────────────────────────────────────┘    │
│            │                   │                                             │
│            ▼                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       POLICY DOMAIN                                  │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │    │
│  │  │ PolicyRule    │  │ Limit         │  │ AlertConfig   │            │    │
│  │  │ ────────────  │  │ ────────────  │  │ ────────────  │            │    │
│  │  │ • scope       │──│ • category    │──│ • thresholds  │            │    │
│  │  │ • monitors    │  │ • max_value   │  │ • channels    │            │    │
│  │  │ • actions     │  │ • window      │  │ • throttle    │            │    │
│  │  │ • lifecycle   │  │ • enforcement │  └───────────────┘            │    │
│  │  └───────────────┘  └───────────────┘                               │    │
│  │         │                                                            │    │
│  │         │    DRAFT → ACTIVE → SUSPENDED → RETIRED                   │    │
│  │         │                                                            │    │
│  └─────────│────────────────────────────────────────────────────────────┘    │
│            │                                                                 │
│            ▼                                                                 │
│  ┌───────────────────┬───────────────────┬───────────────────┐              │
│  │  ACTIVITY DOMAIN  │  INCIDENTS DOMAIN │    LOGS DOMAIN    │              │
│  │  ────────────────  │  ────────────────  │  ────────────────  │              │
│  │  • Run            │  • Incident       │  • LLMRunRecord   │              │
│  │  • Trace          │  • Violation      │  • SystemRecord   │              │
│  │  • TraceStep      │  • PolicyProposal │  • AuditLedger    │              │
│  │  • Signal         │  • Recovery       │  • Evidence       │              │
│  │                   │                   │                   │              │
│  │  queued→running   │  detected→acked   │  immutable        │              │
│  │  →succeeded/failed│  →resolved        │  write-once       │              │
│  └───────────────────┴───────────────────┴───────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Summary

**What's implemented (T0-T3 Complete — 66 gaps, 1,256 tests):**
- Core Policy domain (rules, limits, enforcement)
- Core Activity domain (runs, traces, signals)
- Core Incidents domain (violations, proposals)
- Core Logs domain (records, audit)
- Partial Integration domain (connectors, mediation)

**What's missing (T4 Pending — 19 gaps):**

| Priority | Component | Gaps | Notes |
|----------|-----------|------|-------|
| **1 (CRITICAL)** | Lifecycle Orchestration Framework | GAP-086-089 | **Must implement first** |
| 2 | Complete onboarding lifecycle | GAP-071-077 | Requires framework |
| 3 | Entire offboarding lifecycle | GAP-078-082 | **GDPR/CCPA critical** |
| 4 | SDK thin façade | GAP-083-085 | State-driven, async-aware |

**Non-Goals (Explicit Exclusions):**
- No row-level data verification (verify access path, not semantic correctness)
- No aggressive auto-policy binding (default DENY, explicit activation)
- No forced transitions (SDK requests, LifecycleManager arbitrates)

---

## References

- `docs/architecture/DOMAINS_E2E_SCAFFOLD_V3.md` - Gap definitions (Sections 7.15-7.18)
- `docs/architecture/GAP_IMPLEMENTATION_PLAN_V1.md` - Implementation status
- PIN-454 - Cross-domain orchestration audit
