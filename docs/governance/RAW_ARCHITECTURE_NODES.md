# RAW_ARCHITECTURE_NODES.md

**Status:** REFINED (v2)
**Created:** 2025-12-31
**Refined:** 2025-12-31
**Method:** Code archaeology from actual files
**Reference:** Phase A-D evidence, backend/app/**

---

## Refinement Log

| Version | Change | Reason |
|---------|--------|--------|
| v1 | Initial extraction | 50 nodes from code |
| v2 | Entry Points split into containers + transactions | User scrutiny: module-level ≠ transactional-level |
| v2 | External nodes expanded | User scrutiny: "External" was a black hole |
| v2 | Scheduler triggers annotated | User scrutiny: trigger semantics missing |
| v2 | Observer types differentiated | User scrutiny: telemetry ≠ governance control |

---

## Extraction Rules Applied

- NO layer names (L1-L8)
- NO frontend/backend grouping
- NO simplification or abstraction
- Derived ONLY from: file existence, import statements, function signatures, Phase A-D findings

---

## ACTORS

### ACTOR-001: Human User
- **Type:** actor
- **Triggered by:** External intent
- **Calls:** Frontend UI
- **Writes:** Nothing directly
- **Reads:** UI state
- **Emits:** Click events, form submissions
- **Evidence:** Phase D F1 entry points (32 transaction initiators)

### ACTOR-002: External System (SDK Client)
- **Type:** actor
- **Triggered by:** Machine-native agent
- **Calls:** API endpoints directly (no UI)
- **Writes:** Nothing directly
- **Reads:** API responses
- **Emits:** HTTP requests
- **Evidence:** `agents.py`, `runtime.py`, `traces.py` endpoints

### ACTOR-003: Scheduler (systemd/cron)
- **Type:** actor
- **Triggered by:** Time
- **Calls:** Worker entry points, job scripts
- **Writes:** Nothing directly
- **Reads:** System time
- **Emits:** Process invocation
- **Evidence:** `jobs/failure_aggregation.py`, `jobs/graduation_evaluator.py`

---

## ENTRY POINT CONTAINERS (API Modules)

These are the **modules** that host entry points. Each contains multiple transactional entries.

### ENTRY-CONTAINER-001: agents.py
- **Type:** entry_container
- **Hosts:** 10 transactional entries (TXENTRY-001 to TXENTRY-010)
- **Triggered by:** SDK clients, external agents
- **Evidence:** `backend/app/api/agents.py`

### ENTRY-CONTAINER-002: guard.py
- **Type:** entry_container
- **Hosts:** 7 transactional entries (TXENTRY-011 to TXENTRY-017)
- **Triggered by:** Guard Console (guard.agenticverz.com)
- **Evidence:** `backend/app/api/guard.py`

### ENTRY-CONTAINER-003: ops.py
- **Type:** entry_container
- **Hosts:** Read-only endpoints (no mutations after C01/C02 removal)
- **Triggered by:** Founder Console (ops.agenticverz.com)
- **Evidence:** `backend/app/api/ops.py`

### ENTRY-CONTAINER-004: recovery.py
- **Type:** entry_container
- **Hosts:** 6 transactional entries (TXENTRY-018 to TXENTRY-023)
- **Triggered by:** Machine tokens, recovery system
- **Evidence:** `backend/app/api/recovery.py`

### ENTRY-CONTAINER-005: founder_actions.py
- **Type:** entry_container
- **Hosts:** 7 transactional entries (TXENTRY-024 to TXENTRY-030)
- **Triggered by:** Founder Console
- **Evidence:** `backend/app/api/founder_actions.py`

### ENTRY-CONTAINER-006: v1_killswitch.py
- **Type:** entry_container
- **Hosts:** 5 transactional entries (TXENTRY-031 to TXENTRY-035)
- **Triggered by:** Operator override
- **Evidence:** `backend/app/api/v1_killswitch.py`

### ENTRY-CONTAINER-007: costsim.py
- **Type:** entry_container
- **Hosts:** 3 transactional entries (TXENTRY-036 to TXENTRY-038)
- **Triggered by:** API clients, workers
- **Evidence:** `backend/app/api/costsim.py`

### ENTRY-CONTAINER-008: onboarding.py
- **Type:** entry_container
- **Hosts:** 6 transactional entries (TXENTRY-039 to TXENTRY-044)
- **Triggered by:** Auth flows
- **Evidence:** `backend/app/api/onboarding.py`

### ENTRY-CONTAINER-009: memory_pins.py
- **Type:** entry_container
- **Hosts:** 2 transactional entries (TXENTRY-045, TXENTRY-046)
- **Triggered by:** Memory system
- **Evidence:** `backend/app/api/memory_pins.py`

### ENTRY-CONTAINER-010: workers.py
- **Type:** entry_container
- **Hosts:** 3 transactional entries (TXENTRY-047 to TXENTRY-049)
- **Triggered by:** Worker orchestration
- **Evidence:** `backend/app/api/workers.py`

### ENTRY-CONTAINER-011: rbac_api.py
- **Type:** entry_container
- **Hosts:** 1 transactional entry (TXENTRY-050)
- **Triggered by:** Admin operations
- **Evidence:** `backend/app/api/rbac_api.py`

### ENTRY-CONTAINER-012: v1_proxy.py
- **Type:** entry_container
- **Hosts:** 2 transactional entries (TXENTRY-051, TXENTRY-052)
- **Triggered by:** LLM proxy calls
- **Evidence:** `backend/app/api/v1_proxy.py`

---

## TRANSACTIONAL ENTRY POINTS (Atomic Actions)

These are the **actual endpoints** that initiate transactions.

### agents.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-001 | /api/v1/jobs | POST | Creates job | Job state |
| TXENTRY-002 | /api/v1/jobs/{id}/cancel | POST | Cancels job | Job state |
| TXENTRY-003 | /api/v1/jobs/{id}/claim | POST | Worker claims | Job state |
| TXENTRY-004 | /api/v1/jobs/{id}/items/{item_id}/complete | POST | Completes item | Job state |
| TXENTRY-005 | /api/v1/blackboard/{key} | PUT | Updates blackboard | Blackboard state |
| TXENTRY-006 | /api/v1/blackboard/{key}/lock | POST | Locks key | Lock state |
| TXENTRY-007 | /api/v1/agents/register | POST | Registers agent | Agent registry |
| TXENTRY-008 | /api/v1/agents/{id}/heartbeat | POST | Updates heartbeat | Agent state |
| TXENTRY-009 | /api/v1/sba/validate | POST | Validates SBA | None (validation) |
| TXENTRY-010 | /api/v1/sba/register | POST | Registers SBA | SBA registry |

### guard.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-011 | /guard/killswitch/activate | POST | HALTS TRAFFIC | Killswitch state |
| TXENTRY-012 | /guard/killswitch/deactivate | POST | Resumes traffic | Killswitch state |
| TXENTRY-013 | /guard/incidents/{id}/acknowledge | POST | Acknowledges | Incident state |
| TXENTRY-014 | /guard/incidents/{id}/resolve | POST | Resolves | Incident state |
| TXENTRY-015 | /guard/replay/{call_id} | POST | Triggers replay | Execution |
| TXENTRY-016 | /guard/keys/{id}/freeze | POST | Freezes key | Key state |
| TXENTRY-017 | /guard/keys/{id}/unfreeze | POST | Unfreezes key | Key state |

### recovery.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-018 | /api/v1/recovery/suggest | POST | Generates suggestion | Recovery candidates |
| TXENTRY-019 | /api/v1/recovery/candidates/{id} | PATCH | Updates candidate | Candidate state |
| TXENTRY-020 | /api/v1/recovery/approve | POST | Approves/rejects | Candidate state |
| TXENTRY-021 | /api/v1/recovery/candidates/{id} | DELETE | Revokes suggestion | Candidate removed |
| TXENTRY-022 | /api/v1/recovery/evaluate | POST | Evaluates rules | None (evaluation) |
| TXENTRY-023 | /api/v1/recovery/ingest | POST | Ingests failure | Recovery queue |

### founder_actions.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-024 | /ops/actions/freeze-tenant | POST | BLOCKS TENANT | Tenant frozen |
| TXENTRY-025 | /ops/actions/throttle-tenant | POST | Reduces rate | Tenant throttled |
| TXENTRY-026 | /ops/actions/freeze-api-key | POST | REVOKES KEY | Key frozen |
| TXENTRY-027 | /ops/actions/override-incident | POST | False positive | Incident state |
| TXENTRY-028 | /ops/actions/unfreeze-tenant | POST | Restores access | Tenant unfrozen |
| TXENTRY-029 | /ops/actions/unthrottle-tenant | POST | Restores rate | Tenant unthrottled |
| TXENTRY-030 | /ops/actions/unfreeze-api-key | POST | Restores key | Key unfrozen |

### v1_killswitch.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-031 | /v1/killswitch/tenant | POST | Freezes tenant | Tenant frozen |
| TXENTRY-032 | /v1/killswitch/key | POST | Freezes key | Key frozen |
| TXENTRY-033 | /v1/killswitch/tenant | DELETE | Unfreezes tenant | Tenant unfrozen |
| TXENTRY-034 | /v1/killswitch/key | DELETE | Unfreezes key | Key unfrozen |
| TXENTRY-035 | /v1/replay/{call_id} | POST | Triggers replay | Execution |

### costsim.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-036 | /costsim/v2/simulate | POST | Runs simulation | Memory (if flag) |
| TXENTRY-037 | /costsim/v2/reset | POST | Resets breaker | Circuit state |
| TXENTRY-038 | /costsim/canary/run | POST | Triggers canary | Canary execution |

### onboarding.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-039 | /api/v1/auth/login/google | POST | Initiates OAuth | Session |
| TXENTRY-040 | /api/v1/auth/login/azure | POST | Initiates OAuth | Session |
| TXENTRY-041 | /api/v1/auth/signup/email | POST | Sends OTP | Email sent |
| TXENTRY-042 | /api/v1/auth/verify/email | POST | Verifies OTP | User verified |
| TXENTRY-043 | /api/v1/auth/refresh | POST | Refreshes token | Session |
| TXENTRY-044 | /api/v1/auth/logout | POST | Invalidates | Session ended |

### memory_pins.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-045 | /api/v1/memory/pins | POST | Creates/upserts | Pin state |
| TXENTRY-046 | /api/v1/memory/pins/{key} | DELETE | Deletes pin | Pin removed |

### workers.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-047 | /api/v1/workers/business-builder/run | POST | Executes worker | Execution |
| TXENTRY-048 | /api/v1/workers/business-builder/replay | POST | Replays execution | Execution |
| TXENTRY-049 | /api/v1/workers/business-builder/validate-brand | POST | Validates | None |

### rbac_api.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-050 | /api/v1/rbac/reload | POST | Hot-reloads | Policy state |

### v1_proxy.py Transactions

| ID | Endpoint | Method | Authority | Side Effect |
|----|----------|--------|-----------|-------------|
| TXENTRY-051 | /v1/chat/completions | POST | LLM call | External LLM |
| TXENTRY-052 | /v1/embeddings | POST | Embedding call | External LLM |

---

## PROCESSORS (Domain Engines)

### PROC-001: recovery_rule_engine.py
- **Type:** processor (DOMAIN ENGINE)
- **Triggered by:** `recovery_evaluator.py`, `recovery.py` API
- **Calls:** `db.py`, `models.*`
- **Writes:** Nothing (decision-only)
- **Reads:** Error patterns, historical data
- **Emits:** Recovery decisions (should_auto_execute, classify_error_category, suggest_recovery_mode)
- **Evidence:** `backend/app/services/recovery_rule_engine.py`
- **Phase A Evidence:** SHADOW-001, SHADOW-002, SHADOW-003 fixed by delegating here

### PROC-002: cost_model_engine.py
- **Type:** processor (DOMAIN ENGINE)
- **Triggered by:** `runtime.py`, `costsim/v2_adapter.py`
- **Calls:** `models.*`
- **Writes:** Nothing (calculation-only)
- **Reads:** Cost coefficients
- **Emits:** Cost estimates (estimate_step_cost, check_feasibility, classify_drift)
- **Evidence:** `backend/app/services/cost_model_engine.py`
- **Phase B Evidence:** B02 — CostSimV2Adapter now delegates here

### PROC-003: llm_policy_engine.py
- **Type:** processor (DOMAIN ENGINE)
- **Triggered by:** `skills/adapters/openai_adapter.py`
- **Calls:** `os`, `threading`
- **Writes:** Nothing (policy-only)
- **Reads:** Rate limits, model restrictions
- **Emits:** Safety decisions (check_safety_limits, is_model_allowed, get_model_for_task)
- **Evidence:** `backend/app/services/llm_policy_engine.py`
- **Phase B Evidence:** B01 — OpenAIAdapter now delegates here

### PROC-004: rbac_engine.py
- **Type:** processor (DOMAIN ENGINE)
- **Triggered by:** Auth middleware, API routes
- **Calls:** `jwt`, `fastapi.Request`, `metrics`
- **Writes:** Audit log
- **Reads:** RBAC policies
- **Emits:** Authorization decisions (check, get_max_approval_level, map_external_roles_to_aos)
- **Evidence:** `backend/app/auth/rbac_engine.py`
- **Phase B Evidence:** B03, B04 — ClerkAuthProvider, OIDCProvider now delegate here

### PROC-005: policy_engine.py
- **Type:** processor (DOMAIN ENGINE)
- **Triggered by:** `policy.py`, `policy_layer.py`
- **Calls:** `policy.models`, `sqlalchemy`
- **Writes:** Policy decisions
- **Reads:** Policy rules
- **Emits:** Policy evaluation results
- **Evidence:** `backend/app/policy/engine.py`

---

## PROCESSORS (Services)

### PROC-006: recovery_matcher.py
- **Type:** processor (SERVICE)
- **Triggered by:** `recovery.py` API
- **Calls:** `embedding`, `db`, EXT-003 (VoyageAI)
- **Writes:** Nothing (matching-only)
- **Reads:** Recovery patterns
- **Emits:** Match results (suggest_hybrid)
- **Evidence:** `backend/app/services/recovery_matcher.py`

### PROC-007: guard_write_service.py
- **Type:** processor (WRITE SERVICE)
- **Triggered by:** `guard.py` API
- **Calls:** `db`, `models`
- **Writes:** Incidents, killswitch state
- **Reads:** Nothing
- **Emits:** Write confirmations
- **Evidence:** `backend/app/services/guard_write_service.py`

### PROC-008: recovery_write_service.py
- **Type:** processor (WRITE SERVICE)
- **Triggered by:** `recovery.py` API, workers
- **Calls:** `db`, `models`
- **Writes:** Recovery candidates, actions
- **Reads:** Nothing
- **Emits:** Write confirmations
- **Evidence:** `backend/app/services/recovery_write_service.py`

### PROC-009: ops_write_service.py
- **Type:** processor (WRITE SERVICE)
- **Triggered by:** `ops.py` API
- **Calls:** `db`, `models`
- **Writes:** Ops events
- **Reads:** Nothing
- **Emits:** Write confirmations
- **Evidence:** `backend/app/services/ops_write_service.py`

### PROC-010: certificate.py
- **Type:** processor (SERVICE)
- **Triggered by:** `guard.py` API
- **Calls:** `cryptography`
- **Writes:** Certificates
- **Reads:** Certificate state
- **Emits:** Certificate data
- **Evidence:** `backend/app/services/certificate.py`

### PROC-011: replay_determinism.py
- **Type:** processor (SERVICE)
- **Triggered by:** `guard.py` API
- **Calls:** `db`, `models`
- **Writes:** Replay results
- **Reads:** Execution traces
- **Emits:** Determinism verification
- **Evidence:** `backend/app/services/replay_determinism.py`

### PROC-012: incident_aggregator.py
- **Type:** processor (SERVICE)
- **Triggered by:** Workers
- **Calls:** `models.*`
- **Writes:** Aggregated incidents
- **Reads:** Raw incidents
- **Emits:** Incident keys
- **Evidence:** `backend/app/services/incident_aggregator.py`

### PROC-013: event_emitter.py
- **Type:** processor (SERVICE)
- **Triggered by:** Workers
- **Calls:** `db`, `models`
- **Writes:** Events to outbox
- **Reads:** Nothing
- **Emits:** OpsEvent
- **Evidence:** `backend/app/services/event_emitter.py`

---

## PROCESSORS (Workers)

### WORK-001: runner.py (RunRunner)
- **Type:** processor (WORKER)
- **Triggered by:** Job submission via `agents.py`
- **Calls:** Services, engines, adapters
- **Writes:** Run state, traces
- **Reads:** Job configuration, budget
- **Emits:** Execution results
- **Evidence:** `backend/app/worker/runner.py`

### WORK-002: pool.py (WorkerPool)
- **Type:** processor (WORKER MANAGER)
- **Triggered by:** System startup
- **Calls:** `runner.py`
- **Writes:** Nothing
- **Reads:** Pool configuration
- **Emits:** Process signals
- **Evidence:** `backend/app/worker/pool.py`

### WORK-003: recovery_evaluator.py
- **Type:** processor (EVENT HANDLER)
- **Triggered by:** Failure events
- **Calls:** `recovery_rule_engine.py`
- **Writes:** Recovery suggestions
- **Reads:** Failure events
- **Emits:** Evaluation outcomes
- **Evidence:** `backend/app/worker/recovery_evaluator.py`
- **Phase A Evidence:** Previously had hardcoded confidence threshold (SHADOW-001)

### WORK-004: recovery_claim_worker.py
- **Type:** processor (BACKGROUND WORKER)
- **Triggered by:** Periodic schedule
- **Calls:** `recovery_matcher.py`, `recovery_write_service.py`
- **Writes:** Recovery actions
- **Reads:** Recovery candidates
- **Emits:** Auto-execution results
- **Evidence:** `backend/app/worker/recovery_claim_worker.py`

### WORK-005: outbox_processor.py
- **Type:** processor (EVENT PROCESSOR)
- **Triggered by:** Outbox events
- **Calls:** HTTP endpoints, webhooks (EXT-006)
- **Writes:** Delivery confirmations
- **Reads:** Outbox queue
- **Emits:** External HTTP events
- **Evidence:** `backend/app/worker/outbox_processor.py`

### WORK-006: simulate.py (CostSimulator)
- **Type:** processor (SIMULATION)
- **Triggered by:** `runtime.py` API
- **Calls:** `cost_model_engine.py`
- **Writes:** Nothing (simulation-only)
- **Reads:** Plan configuration
- **Emits:** Simulation results
- **Evidence:** `backend/app/worker/simulate.py`

---

## PROCESSORS (Adapters)

### ADAPT-001: openai_adapter.py
- **Type:** processor (ADAPTER)
- **Triggered by:** Skill execution
- **Calls:** EXT-001 (OpenAI API), `llm_policy_engine.py`
- **Writes:** Nothing (translation-only)
- **Reads:** Skill parameters
- **Emits:** LLM responses
- **Evidence:** `backend/app/skills/adapters/openai_adapter.py`
- **Phase B Evidence:** B01 — now delegates safety limits to LLMPolicyEngine

### ADAPT-002: v2_adapter.py (CostSimV2Adapter)
- **Type:** processor (ADAPTER)
- **Triggered by:** `costsim.py` API
- **Calls:** `cost_model_engine.py`
- **Writes:** Nothing (translation-only)
- **Reads:** Cost parameters
- **Emits:** Cost simulation requests
- **Evidence:** `backend/app/costsim/v2_adapter.py`
- **Phase B Evidence:** B02 — now delegates cost modeling to CostModelEngine

### ADAPT-003: anthropic_adapter.py
- **Type:** processor (ADAPTER)
- **Triggered by:** Skill execution
- **Calls:** EXT-002 (Anthropic API)
- **Writes:** Nothing (translation-only)
- **Reads:** Skill parameters
- **Emits:** LLM responses
- **Evidence:** `backend/app/planners/anthropic_adapter.py`

### ADAPT-004: nats_adapter.py
- **Type:** processor (ADAPTER)
- **Triggered by:** Event emission
- **Calls:** EXT-007 (NATS server)
- **Writes:** Nothing (translation-only)
- **Reads:** Event payload
- **Emits:** NATS messages
- **Evidence:** `backend/app/events/nats_adapter.py`

---

## EXTERNAL SYSTEMS (Expanded)

### EXT-001: OpenAI API
- **Type:** external (LLM PROVIDER)
- **Called by:** ADAPT-001 (openai_adapter), v1_proxy.py, llm_invoke.py
- **Read/Write:** READ (model responses)
- **Authority:** LLM completions, embeddings
- **Retry behavior:** Provider may retry internally
- **Callback behavior:** None
- **Evidence:** `from openai import OpenAI` in adapters

### EXT-002: Anthropic API
- **Type:** external (LLM PROVIDER)
- **Called by:** ADAPT-003 (anthropic_adapter), claude_adapter, llm_invoke.py
- **Read/Write:** READ (model responses)
- **Authority:** LLM completions
- **Retry behavior:** Provider may retry internally
- **Callback behavior:** None
- **Evidence:** `import anthropic` in adapters

### EXT-003: VoyageAI (Embeddings)
- **Type:** external (EMBEDDING PROVIDER)
- **Called by:** recovery_matcher.py, voyage_embed.py
- **Read/Write:** READ (embeddings)
- **Authority:** Embedding generation
- **Retry behavior:** None
- **Callback behavior:** None
- **Evidence:** httpx calls to VoyageAI API

### EXT-004: HashiCorp Vault
- **Type:** external (SECRETS MANAGER)
- **Called by:** vault_client.py
- **Read/Write:** READ (secrets)
- **Authority:** Secret storage and retrieval
- **Retry behavior:** None
- **Callback behavior:** None
- **Evidence:** `backend/app/secrets/vault_client.py`

### EXT-005: Identity Providers (Google, Azure, Clerk)
- **Type:** external (IDENTITY)
- **Called by:** oauth_providers.py, clerk_provider.py, oidc_provider.py
- **Read/Write:** READ (tokens, user info)
- **Authority:** Authentication
- **Retry behavior:** OAuth flow may timeout
- **Callback behavior:** OAuth redirects
- **Evidence:** httpx calls in auth/*.py

### EXT-006: Webhooks (Customer Endpoints)
- **Type:** external (CUSTOMER SYSTEMS)
- **Called by:** WORK-005 (outbox_processor), webhook_send.py
- **Read/Write:** WRITE (event delivery)
- **Authority:** Event notification
- **Retry behavior:** Outbox retry pattern
- **Callback behavior:** Customer may respond
- **Evidence:** `backend/app/worker/outbox_processor.py`

### EXT-007: NATS Server
- **Type:** external (MESSAGE BROKER)
- **Called by:** ADAPT-004 (nats_adapter)
- **Read/Write:** WRITE (messages)
- **Authority:** Event pub/sub
- **Retry behavior:** NATS built-in
- **Callback behavior:** None
- **Evidence:** `backend/app/events/nats_adapter.py`

### EXT-008: Slack API
- **Type:** external (NOTIFICATION)
- **Called by:** slack_send.py
- **Read/Write:** WRITE (messages)
- **Authority:** Team notifications
- **Retry behavior:** None
- **Callback behavior:** None
- **Evidence:** `backend/app/skills/slack_send.py`

### EXT-009: Email Provider (SMTP/API)
- **Type:** external (NOTIFICATION)
- **Called by:** email_send.py, email_verification.py
- **Read/Write:** WRITE (emails)
- **Authority:** User notifications, verification
- **Retry behavior:** None
- **Callback behavior:** None
- **Evidence:** `backend/app/skills/email_send.py`

---

## STORES

### STORE-001: PostgreSQL (via db.py)
- **Type:** store
- **Triggered by:** All write services
- **Calls:** Nothing
- **Writes:** All persistent state
- **Reads:** Provides state to all services
- **Emits:** Query results
- **Evidence:** `backend/app/db.py`, `backend/app/db_async.py`

### STORE-002: Redis
- **Type:** store
- **Triggered by:** Rate limiters, caches
- **Calls:** Nothing
- **Writes:** Advisory cache
- **Reads:** Cached values
- **Emits:** Cache responses
- **Invariant:** Loss must not change behavior (advisory only)
- **Evidence:** Imported in various rate limiting code

### STORE-003: models/killswitch.py
- **Type:** store (ORM)
- **Triggered by:** guard_write_service
- **Calls:** PostgreSQL
- **Writes:** Incident, IncidentEvent, KillSwitchState
- **Reads:** Same
- **Emits:** Model instances
- **Evidence:** `backend/app/models/killswitch.py`

### STORE-004: models/trace.py
- **Type:** store (ORM)
- **Triggered by:** traces.py API, workers
- **Calls:** PostgreSQL
- **Writes:** Trace, TraceStep (IMMUTABLE)
- **Reads:** Same
- **Emits:** Model instances
- **Invariant:** NEVER mutated after creation
- **Evidence:** `backend/app/models/trace.py`

### STORE-005: models/policy.py
- **Type:** store (ORM)
- **Triggered by:** policy engine
- **Calls:** PostgreSQL
- **Writes:** Policy, PolicyRule, PolicyDecision, PolicyViolation
- **Reads:** Same
- **Emits:** Model instances
- **Evidence:** `backend/app/models/policy.py`

### STORE-006: models/recovery.py
- **Type:** store (ORM)
- **Triggered by:** recovery_write_service
- **Calls:** PostgreSQL
- **Writes:** RecoveryCandidate, RecoveryAction
- **Reads:** Same
- **Emits:** Model instances
- **Evidence:** `backend/app/models/recovery.py`

---

## SCHEDULERS (With Trigger Semantics)

### SCHED-001: failure_aggregation.py
- **Type:** scheduler
- **Trigger Type:** TIME-BASED (periodic)
- **Trigger Source:** systemd timer / cron
- **Frequency:** Configurable (likely hourly)
- **Can fire without human intent:** YES
- **Calls:** `incident_aggregator.py`, `recovery_rule_engine.py`
- **Writes:** Aggregated incidents
- **Reads:** Raw failures
- **Emits:** Aggregation events
- **Evidence:** `backend/app/jobs/failure_aggregation.py`
- **Phase A Evidence:** Previously had hardcoded heuristics (SHADOW-002, SHADOW-003)

### SCHED-002: graduation_evaluator.py
- **Type:** scheduler
- **Trigger Type:** TIME-BASED (periodic)
- **Trigger Source:** systemd timer / cron
- **Frequency:** Configurable (likely daily)
- **Can fire without human intent:** YES
- **Calls:** `graduation_engine.py`, `policy_engine.py`
- **Writes:** Graduation state
- **Reads:** Feature metrics
- **Emits:** Graduation decisions
- **Evidence:** `backend/app/jobs/graduation_evaluator.py`

### SCHED-003: cost_snapshots.py
- **Type:** scheduler
- **Trigger Type:** TIME-BASED (periodic)
- **Trigger Source:** systemd timer / cron
- **Frequency:** Configurable (likely hourly/daily)
- **Can fire without human intent:** YES
- **Calls:** `cost_write_service.py`, `cost_model_engine.py`
- **Writes:** Cost snapshots
- **Reads:** Current costs
- **Emits:** Snapshot events
- **Evidence:** `backend/app/integrations/cost_snapshots.py`

---

## OBSERVERS (Differentiated)

### OBS-001: BLCA (Bidirectional Layer Consistency Auditor)
- **Type:** observer (GOVERNANCE CONTROL)
- **Observer Class:** CONTROL (can halt work)
- **Triggered by:** Session start, code changes, governance changes
- **Calls:** Nothing (read-only for data, but BLOCKS for control)
- **Writes:** BIDIRECTIONAL_AUDIT_STATUS.md
- **Reads:** All architecture artifacts
- **Emits:** Audit verdicts (CLEAN/BLOCKED)
- **Control Authority:** Can BLOCK PR merge, BLOCK code changes
- **Evidence:** `docs/governance/BIDIRECTIONAL_AUDIT_STATUS.md`, SESSION_PLAYBOOK.yaml Section 28-29

### OBS-002: CI Pipeline
- **Type:** observer (GOVERNANCE CONTROL)
- **Observer Class:** CONTROL (can halt merge)
- **Triggered by:** PR open/update
- **Calls:** Linters, tests, validators
- **Writes:** CI status
- **Reads:** Code changes
- **Emits:** Pass/fail status
- **Control Authority:** Can BLOCK PR merge (Tier 1 checks)
- **Evidence:** `.github/workflows/*.yml`

### OBS-003: Prometheus Metrics
- **Type:** observer (TELEMETRY)
- **Observer Class:** TELEMETRY (read-only, no control)
- **Triggered by:** HTTP requests, worker events
- **Calls:** Nothing
- **Writes:** Metrics to Prometheus
- **Reads:** Runtime state
- **Emits:** Metric samples
- **Control Authority:** NONE (passive observation only)
- **Evidence:** `workflow/metrics.py`, monitoring/ directory

### OBS-004: Alertmanager
- **Type:** observer (TELEMETRY + NOTIFICATION)
- **Observer Class:** TELEMETRY (observes, then notifies)
- **Triggered by:** Prometheus alerts
- **Calls:** Slack, email
- **Writes:** Alert state
- **Reads:** Prometheus metrics
- **Emits:** Alert notifications
- **Control Authority:** NONE (notifies humans, does not control)
- **Evidence:** `monitoring/alertmanager.yml`

---

## NODE SUMMARY (v2)

| Type | Count | Examples |
|------|-------|----------|
| **Actors** | 3 | Human, SDK Client, Scheduler |
| **Entry Containers** | 12 | agents.py, guard.py, ops.py, recovery.py... |
| **Transactional Entries** | 52 | TXENTRY-001 to TXENTRY-052 |
| **Processors (Engines)** | 5 | recovery_rule_engine, cost_model_engine, llm_policy_engine... |
| **Processors (Services)** | 8 | recovery_matcher, guard_write_service, incident_aggregator... |
| **Processors (Workers)** | 6 | runner.py, recovery_evaluator.py, outbox_processor.py... |
| **Processors (Adapters)** | 4 | openai_adapter, v2_adapter, anthropic_adapter... |
| **External Systems** | 9 | OpenAI, Anthropic, VoyageAI, Vault, Identity, Webhooks, NATS, Slack, Email |
| **Stores** | 6 | PostgreSQL, Redis, ORM models... |
| **Schedulers** | 3 | failure_aggregation, graduation_evaluator, cost_snapshots |
| **Observers** | 4 | BLCA (control), CI (control), Prometheus (telemetry), Alertmanager (telemetry) |
| **TOTAL (unique)** | 112 | (52 transactional entries + 60 other nodes) |

---

*Refined from code. Not designed.*
*Evidence: backend/app/**, Phase A-D findings, PIN-252 Signal Registry*
*v2: Entry split, External expanded, Scheduler triggers, Observer differentiation*
