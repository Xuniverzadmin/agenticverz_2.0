# V3 Manual Audit Workbook

**Generated:** 2026-01-26
**Total AMBIGUOUS Files:** 184
**Method:** Manual review using Decision Ownership lens

## Audit Methodology

For each file, answer:
1. **What irreversible decision does this file make?**
2. **Decision of WHAT?** (rules vs limits vs incidents vs runs)
3. **Decision for WHOM?** (system orchestration vs customer config)

## Status Legend

- [ ] NOT REVIEWED
- [~] REVIEWED - NEEDS DISCUSSION
- [x] REVIEWED - DOMAIN ASSIGNED

---

## duplicates (3 files) — DEFERRED

> **Note:** Duplicates folder files deferred - no value created on working these files.

### [~] `duplicates/M17_internal_worker.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | duplicates |
| **Layer** | L2 — Product APIs |
| **Audience** | INTERNAL |
| **What It Does** | API endpoints for viewing WorkerRegistry and WorkerConfig tables. Lists available workers (business-builder, etc.) and per-tenant worker configurations. |
| **Tables Accessed** | WorkerRegistry (R), WorkerConfig (R) |
| **Callers** | None - NOT registered in main.py |
| **Decision Made** | None - read-only view of internal worker infrastructure |
| **Status** | DEPRECATED - Router NOT registered in main.py |
| **Qualifier Test** | N/A - deprecated code, not customer-facing |

**DECISION:** `DELETE` (or `_archive/`)
**Reason:** Explicitly marked DEPRECATED. Not registered. INTERNAL audience (not customer). Customer-facing integration is in `aos_cus_integrations.py`.

---

### [~] `duplicates/api.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | duplicates |
| **Layer** | L2 — API Route (misplaced, should not be in engines/) |
| **Audience** | CUSTOMER |
| **What It Does** | C2 Prediction API - creates advisory predictions for incident risk, spend spike, policy drift. All predictions are advisory-only, expire in 30 minutes, and have zero enforcement influence. |
| **Tables Accessed** | PredictionEvent (W) |
| **Callers** | FastAPI application |
| **Decision Made** | "Is this pattern elevated risk?" - computes confidence scores, creates disposable predictions |
| **Qualifier Test** | "WHAT can be derived?" → Predictions are derived/computed metrics |

**DECISION:** `analytics`
**Reason:** Creates derived metrics (predictions). Advisory-only computation. Matches analytics qualifier: "derived metric", "statistical", "cost analysis". Does NOT create incidents (would be `incidents`) or enforce policies (would be `policies`).

---

### [~] `duplicates/pattern_detection.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | duplicates (QUARANTINED, original: logs/) |
| **Layer** | L8 — Catalyst / Meta |
| **Audience** | INTERNAL |
| **What It Does** | Detects failure patterns (same error N times) and cost spikes (abnormal cost increase). Reads execution data, writes to pattern_feedback table. Does NOT modify history. |
| **Tables Accessed** | WorkerRun (R), PatternFeedback (W) |
| **Callers** | None (ORPHAN - pending integration) |
| **Decision Made** | "Is this a pattern?" - computes error signatures, detects repetition/anomalies |
| **Why Quarantined** | Header says: "Contains decision logic which violates Logs domain. Logs is FACT EMISSION, not DECISION." |
| **Qualifier Test** | "WHAT can be derived?" → Pattern detection = behavioral analysis |

**DECISION:** `analytics`
**Reason:** Behavioral analysis (pattern detection) = derived insight. Matches analytics qualifiers: "behavioral analysis", "divergence", "derived metric". The header explicitly suggests "Reassign to analytics domain".

---

## activity (5 files)

### [x] `activity/L5_engines/activity_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | activity |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Unified facade for activity domain. Provides: run listing, run details (O3), run evidence (O4), run integrity proof (O5), status summaries, pattern detection, cost analysis, attention ranking, signals, and signal acknowledgment. |
| **Tables Accessed** | WorkerRun (R), AuditLedger (R) via drivers |
| **Callers** | app.api.activity (L2) |
| **Decision Made** | None (read-only facade). Answers: "What ran? What's the status? What evidence exists?" |
| **Why AMBIGUOUS** | V2 scored activity=9, analytics=9 (close margin) |
| **Qualifier Test** | "WHAT LLM run occurred?" → Run listing, run details, run evidence |

**DECISION:** `activity` ✓ (CONFIRMED CORRECT)
**Reason:** Core question is "What ran?" Run lifecycle, execution metadata, run state. The pattern/cost sub-operations support the activity view but don't change the domain ownership.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `activity/L5_engines/attention_ranking_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | activity |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Ranks and prioritizes activity signals. Computes attention scores based on: severity (40%), recency (30%), pattern frequency (30%). Provides attention queue for tenant. |
| **Tables Accessed** | None (pure in-memory computation) |
| **Callers** | activity_facade.py |
| **Decision Made** | "What needs attention first?" - prioritizes signals for user attention |
| **Why AMBIGUOUS** | V2 scored account=4 vs incidents=3 (likely false match on "attention") |
| **Qualifier Test** | "WHAT LLM run occurred?" → Ranks signals ABOUT runs |

**DECISION:** `activity` ✓ (CONFIRMED CORRECT)
**Reason:** This is a support engine for activity domain. It ranks signals that originate from run data. The core function is prioritizing activity-related signals. No account/billing/tenant-management logic.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `activity/L5_engines/run_governance_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | activity |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Facade for governance operations DURING run execution. Subscribes to RUN_STARTED, RUN_COMPLETED. Wraps LessonsLearnedEngine and PolicyViolationService. Emits RAC (Runtime Audit Contract) acknowledgments. Creates policy evaluations and lessons learned. |
| **Tables Accessed** | Policy (R), Limit (R) via wrapped engines |
| **Callers** | L5 runner (worker runtime) |
| **Decision Made** | Coordinates governance evaluation during run lifecycle. Delegates actual policy decisions to PolicyViolationService. |
| **Why AMBIGUOUS** | V2 scored logs=7 vs policies=6 (audit/policy language overlap) |
| **Qualifier Test** | "WHAT LLM run occurred?" → It's triggered BY run events, coordinates governance FOR runs |

**DECISION:** `activity` ✓ (CONFIRMED CORRECT)
**Reason:** Subject is RUNS. Triggered by run lifecycle events (RUN_STARTED, RUN_COMPLETED). It's a facade that coordinates governance during execution - the run is the owner, policies are consulted. Belongs with run lifecycle.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `activity/L5_engines/signal_identity.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | activity |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Pure utility for signal fingerprinting. Computes SHA-256 hashes for: signal deduplication, change detection, idempotent signal creation. No side effects. |
| **Tables Accessed** | None (pure computation) |
| **Callers** | activity_facade.py, signal engines |
| **Decision Made** | None (deterministic hash computation) |
| **Why AMBIGUOUS** | V2 scored apis=4 vs analytics=3 (false match on "key" word in code) |
| **Qualifier Test** | Supports activity signal processing |

**DECISION:** `activity` ✓ (CONFIRMED CORRECT)
**Reason:** Pure utility for activity domain's signal management. No business decisions. Supports fingerprinting of activity signals.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `activity/L6_drivers/threshold_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | activity |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Database operations for threshold limits. Reads Limit and LimitBreach tables. Returns LimitSnapshot objects (frozen dataclass). Emits THRESHOLD_SIGNAL. Pure data access, no business logic. |
| **Tables Accessed** | Limit (R), LimitBreach (R) — from `app.models.policy_control_plane` |
| **Callers** | threshold_engine.py (L5 in activity) |
| **Decision Made** | None (pure data access) |
| **Why AMBIGUOUS** | V2 scored activity=6 vs account=6 |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Reads LIMIT tables |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** Accesses Limit and LimitBreach tables which belong to controls domain. The model is from `policy_control_plane`. The qualifier is "WHAT limits apply" (controls), not "WHAT ran" (activity). Header incorrectly says "Scope: domain (activity)" but data is controls-owned.

---

## account (6 files)

### [x] `account/L5_engines/notifications_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | account |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Centralized facade for notification operations. Sends notifications via email, slack, webhook, in_app, SMS. Manages notification preferences. Logs delivery status. Provides unified access to notification channels. |
| **Tables Accessed** | User (R), Tenant (R), NotificationLog (W) |
| **Callers** | L2 notifications.py API, SDK, Worker |
| **Decision Made** | "Send notification to whom? Via what channel?" Based on user preferences. |
| **Channels** | EMAIL, SLACK, WEBHOOK, IN_APP, SMS |
| **Why AMBIGUOUS** | V2 scored account=6 vs integrations=4 |
| **Qualifier Test** | "WHO owns what?" → User notification preferences, tenant-level settings |

**DECISION:** `account` ✓ (CONFIRMED CORRECT)
**Reason:** Primary subject is USER/TENANT notification preferences. Reads User, Tenant tables. Manages per-user notification settings. The delivery channels (webhook, etc.) are mechanisms, not the core decision. Account owns "who receives what".
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `account/L5_notifications/engines/channel_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | account |
| **Layer** | L4 — Domain Engine (in L5_notifications/engines/ path) |
| **Audience** | CUSTOMER |
| **What It Does** | Configurable notification channel management. Manages channels: UI, WEBHOOK, EMAIL, SLACK, PAGERDUTY, TEAMS. Provides: channel configuration (enable/disable), connectivity validation, delivery tracking, retry logic. |
| **Channels** | WEBHOOK, SLACK, PAGERDUTY, TEAMS, EMAIL, UI |
| **Event Types** | ALERT_NEAR_THRESHOLD, ALERT_BREACH, INCIDENT_CREATED, POLICY_VIOLATED, RUN_FAILED, etc. |
| **Callers** | alert_emitter, incident_service, policy_engine (cross-domain) |
| **Decision Made** | "HOW should this event reach external systems?" - channel selection, connectivity, delivery |
| **Why AMBIGUOUS** | V2 scored incidents=7 vs activity=6 (event types mention incidents/runs) |
| **Qualifier Test** | "HOW external systems connect?" → Manages WEBHOOK, SLACK, PAGERDUTY, TEAMS connections |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Manages external system connections (Slack, PagerDuty, Teams, webhooks). Tests connectivity. Handles delivery to external channels. Matches integrations qualifier: "webhook", "connector", "integration config". Cross-domain callers (incidents, policies) use this to connect to external systems.

---

### [x] `account/L5_support/CRM/engines/audit_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | account |
| **Layer** | L8 — Catalyst / Verification |
| **Audience** | CUSTOMER |
| **What It Does** | Governance audit engine. Verifies job execution matched contract intent. Produces verdicts: PASS / FAIL / INCONCLUSIVE. Reads frozen evidence only. Post-execution, deterministic, authoritative. |
| **Tables Accessed** | AuditVerdict (from app.models.contract) |
| **Callers** | GovernanceOrchestrator (via AuditTrigger) |
| **Key Properties** | EVIDENCE CONSUMER, VERDICT PRODUCER, TERMINAL, INDEPENDENT |
| **Why AMBIGUOUS** | V2 scored apis=10 vs activity=8 |
| **Qualifier Test** | "WHAT immutable record exists?" → Produces verdicts (proof), reads evidence |

**DECISION:** `logs` ⚠️ (MISPLACED)
**Reason:** Audit engine that reads frozen evidence and produces authoritative verdicts. "Evidence is preserved", "Verdicts are immutable". Matches logs: "audit trail", "evidence record", "proof".

---

### [x] `account/L5_support/CRM/engines/job_executor.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | account |
| **Layer** | L5 — Execution & Workers |
| **Audience** | CUSTOMER |
| **What It Does** | Executes governance job steps. MACHINE that performs declared steps. Emits evidence per step. No decision-making - just executes and records. FAILURE-STOP on first failure. |
| **Tables Accessed** | JobStatus, JobStep, StepResult, StepStatus (from app.models.governance_job) |
| **Callers** | workers, governance orchestrator (via message queue) |
| **Key Properties** | PLAN CONSUMER, EVIDENCE EMITTER, FAILURE-STOP, NO DECISION |
| **Why AMBIGUOUS** | V2 scored logs=5 vs apis=4 |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Execution coordination |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** System-wide execution engine. Coordinates job step execution. "WHEN and HOW actions execute" matches general's "execution coordinator", "workflow orchestration". Not account-specific - it's infrastructure.

---

### [x] `account/L6_drivers/user_write_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | account |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pure database write operations for User management. Creates users, updates login timestamps, converts to DTO. No business logic. |
| **Tables Accessed** | User (R/W) |
| **Callers** | user_write_engine.py (L5) |
| **Decision Made** | None (pure data access) |
| **Why AMBIGUOUS** | V2 scored integrations=6 vs account=4 (false match) |
| **Qualifier Test** | "WHO owns what?" → User management, tenant data |

**DECISION:** `account` ✓ (CONFIRMED CORRECT)
**Reason:** User table = account data. Pure CRUD for user management. "WHO owns what" qualifier.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `account/L6_drivers/worker_registry_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | account |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Worker discovery, status queries, capability registry. Per-tenant worker configuration. Worker availability checks. |
| **Tables Accessed** | WorkerRun (R/W), Tenant (R), WorkerRegistry (R), WorkerConfig (R) |
| **Callers** | L5 engines, L2 APIs |
| **Decision Made** | None (pure data access) |
| **Why AMBIGUOUS** | V2 evidence: NO (missing header data) |
| **Qualifier Test** | "HOW external systems connect?" → Worker discovery, connector registry |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Workers are external processing units/connectors. Worker discovery = finding available integration points. WorkerRegistry/WorkerConfig = integration configuration. Matches integrations: "connector", "adapter", "integration config".

---

## analytics (15 files)

### [x] `analytics/L3_adapters/v2_adapter.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L3 — Boundary Adapter |
| **Audience** | CUSTOMER |
| **What It Does** | Cost simulation adapter. Translation only. Wraps V1 CostSimulator, adds confidence scoring, provenance logging, V1 comparison. Delegates domain decisions to L4 CostModelEngine. |
| **Tables Accessed** | None directly (uses L4/L5/L6) |
| **Callers** | simulation endpoints, workflow engine |
| **Decision Made** | None (L3 = shape, transport, provenance, context binding) |
| **Why AMBIGUOUS** | V2 scored analytics=6 vs controls=4 |
| **Qualifier Test** | "WHAT can be derived?" → Cost simulation = cost analysis |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Cost simulation = derived metrics. Matches analytics: "cost analysis", "cost sim". Pure translation layer.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `analytics/L5_engines/alert_worker.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Alert queue processing. Background worker for reliable alert delivery to Alertmanager. Exponential backoff retry logic, dead letter handling, batch processing. |
| **Tables Accessed** | via alert_driver (L6) |
| **Callers** | background task, cron |
| **Decision Made** | Retry eligibility, backoff calculation, status transitions |
| **Key Pattern** | "Retry logic" - explicitly listed in general qualifier_phrases |
| **Why AMBIGUOUS** | V2 scored activity=6 vs integrations=4 |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Retry orchestration |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Retry logic and execution orchestration. "retry logic" is explicitly in general's qualifier_phrases. The content of alerts (cost metrics) is analytics, but this worker is about delivery mechanism/orchestration.

---

### [x] `analytics/L5_engines/cb_sync_wrapper.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Thread-safe sync wrapper for async circuit breaker functions. Uses ThreadPoolExecutor to bridge sync/async contexts. Enables circuit breaker checks from sync middleware. |
| **Tables Accessed** | via circuit_breaker (L6) |
| **Callers** | sync middleware, legacy code |
| **Decision Made** | None (pure utility/wrapper for circuit breaker) |
| **Key Pattern** | "Circuit breaker" - explicitly in controls qualifier_phrases |
| **Why AMBIGUOUS** | V2 scored activity=6 vs controls=5 |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Circuit breaker state |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** Circuit breaker functionality. "circuit breaker" is explicitly in controls' qualifier_phrases. This is about system limits/safety controls, not analytics.

---

### [x] `analytics/L5_engines/cost_model_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Cost modeling and risk estimation. Domain authority for cost model coefficients (per-skill pricing), risk estimation logic, feasibility determination, drift classification. Pure computation. |
| **Tables Accessed** | None (pure computation) |
| **Callers** | CostSimV2Adapter (L3), simulation endpoints |
| **Decision Made** | "What is the estimated cost/risk?" |
| **Why AMBIGUOUS** | V2 scored integrations=4 vs apis=4 |
| **Qualifier Test** | "WHAT can be derived?" → Cost modeling, risk estimation |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Cost modeling = derived metrics. Risk estimation = statistical analysis. Matches: "cost analysis", "derived metric".
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `analytics/L5_engines/datasets.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | CostSim V2 reference datasets for validation. Static reference data: sample plans, expected behavior, validation thresholds. Used for canary validation and divergence analysis. |
| **Tables Accessed** | None (static data) |
| **Callers** | canary runner, divergence engine |
| **Decision Made** | None (static reference data) |
| **Why AMBIGUOUS** | V2 scored integrations=4 vs analytics=2 |
| **Qualifier Test** | "WHAT can be derived?" → Divergence analysis support |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Reference datasets for cost simulation validation. Supports divergence analysis. "divergence" is in analytics qualifiers.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `analytics/L5_engines/detection_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Facade for anomaly detection. Provides access to: cost anomalies (CostAnomalyDetector), behavioral anomalies, drift detection. Lists and resolves anomalies. |
| **Detection Types** | COST, BEHAVIORAL, DRIFT, POLICY |
| **Tables Accessed** | via L6 drivers |
| **Callers** | L2 detection.py API, SDK, Worker |
| **Decision Made** | "Is this data point anomalous?" |
| **Why AMBIGUOUS** | V2 scored incidents=7 vs activity=6 |
| **Qualifier Test** | "WHAT can be derived?" → Behavioral analysis, divergence |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Anomaly detection = behavioral analysis + divergence detection. Core function is deriving anomalies from data. Matches: "behavioral analysis", "divergence".
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `analytics/L5_engines/killswitch.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Optimization killswitch for emergency stops. Manages global state (ENABLED/DISABLED). Triggers immediate reversion of all optimization envelopes. Pure state logic, in-memory. |
| **Tables Accessed** | None (in-memory state) |
| **Callers** | API routes, workers |
| **Invariants** | K-1 to K-5: Killswitch overrides all, immediate reversion, auditable |
| **Key Pattern** | "killswitch" - explicitly in controls qualifier_phrases |
| **Why AMBIGUOUS** | V2 scored controls=5 vs logs=5 |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Emergency stop control |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** "killswitch" is EXPLICITLY in controls' qualifier_phrases. Emergency stop = system limit/control.

---

### [x] `analytics/L5_engines/manager.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Optimization envelope lifecycle management. Manages active envelopes, handles kill-switch triggered rollback, emits audit records. Thread-safe. |
| **Tables Accessed** | None (in-memory state) |
| **Callers** | workers |
| **Imports** | Envelope, KillSwitch from optimization modules |
| **Key Pattern** | Lifecycle management, orchestration, rollback coordination |
| **Why AMBIGUOUS** | V2 scored logs=7 vs controls=5 |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Envelope lifecycle coordination |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Envelope lifecycle management = orchestration. Coordinates envelope application and rollback. Matches general: "workflow orchestrat", "coordinator".

---

### [x] `analytics/L5_engines/prediction.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Prediction generation and orchestration. Calculates failure likelihood, cost overruns. Advisory only - predictions have zero side-effects on execution. |
| **Tables Accessed** | via prediction_driver (L6) |
| **Callers** | predictions API |
| **Decision Made** | "predict_failure_likelihood", "predict_cost_overrun" |
| **Contract** | "Advise, don't influence" |
| **Why AMBIGUOUS** | V2 scored activity=6 vs overview=4 |
| **Qualifier Test** | "WHAT can be derived?" → Predictions = derived metrics |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Predictions = derived metrics. Confidence scoring = statistical analysis. Matches: "derived metric", "statistical", "cost analysis".
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `analytics/L5_engines/s2_cost_smoothing.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | S2 Cost smoothing envelope implementation. Defines optimization envelope with tight bounds: decrease only (-10% max), absolute floor=1, timebox ≤15min. Adjusts max_concurrent_jobs. |
| **Tables Accessed** | None (pure envelope definition) |
| **Callers** | optimization/coordinator |
| **Key Pattern** | Envelope bounds, throttle control, concurrency limits |
| **Why AMBIGUOUS** | V2 scored apis=4 vs analytics=3 |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Concurrency limits |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** Envelope defines LIMITS on system behavior (max_concurrent_jobs). "throttle" in controls qualifiers. The envelope is a control mechanism, even if triggered by analytics predictions.

---

### [x] `analytics/L6_drivers/alert_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Data access for alert queue operations. Pure DB operations: fetch pending, update status, queue stats. No business logic, no HTTP. |
| **Tables Accessed** | CostSimAlertQueueModel (R/W), CostSimCBIncidentModel (R/W) |
| **Callers** | alert_worker.py (L5 engine) → moving to general |
| **Decision Made** | None (pure data access) |
| **Why AMBIGUOUS** | V2 scored incidents=6 vs controls=5 |
| **Qualifier Test** | Follows engine (alert_worker) for consistency |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Driver follows its engine. alert_worker → general, so alert_driver → general for consistency.

---

### [x] `analytics/L6_drivers/circuit_breaker.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | DB-backed circuit breaker state tracking (sync). Manages CostSimCBState (disabled state, consecutive failures). Creates CostSimCBIncident records when tripped. SELECT FOR UPDATE locking. TTL-based auto-recovery. Alertmanager integration. |
| **Tables Accessed** | CostSimCBState (R/W), CostSimCBIncident (R/W) |
| **Callers** | L5 engines (must provide session) |
| **Invariants** | L6 DOES NOT COMMIT — L4 coordinator owns transaction |
| **Key Pattern** | "circuit breaker" - explicitly in controls qualifier_phrases |
| **Why AMBIGUOUS** | V2 scored incidents=9 vs controls=7 |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Circuit breaker = system limit |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** "circuit breaker" is EXPLICITLY in controls' qualifier_phrases. Circuit breakers are safety controls that limit system behavior when thresholds are exceeded. The fact that it creates "incidents" (CB incidents) is coincidental naming - these are control state records, not domain Incidents.

---

### [x] `analytics/L6_drivers/circuit_breaker_async.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Async DB-backed circuit breaker state tracking. Same functionality as sync version but using AsyncSession. Non-blocking DB operations. TTL auto-recovery with proper locking. Alert queue for reliable delivery. |
| **Tables Accessed** | CostSimCBStateModel (R/W), CostSimCBIncidentModel (R/W), CostSimAlertQueueModel (R/W) |
| **Callers** | sandbox.py, canary.py (L5 engines) |
| **Invariants** | NO COMMIT — L4 coordinator owns transaction boundary |
| **Key Pattern** | "circuit breaker" - explicitly in controls qualifier_phrases |
| **Why AMBIGUOUS** | V2 scored controls=7 vs incidents=6 |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Circuit breaker = system limit |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** Same as sync version. "circuit breaker" is EXPLICITLY in controls' qualifier_phrases. This is the async variant of the same control mechanism.

---

### [x] `analytics/L6_drivers/pattern_detection_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L6 — Data Access Driver |
| **Audience** | INTERNAL |
| **What It Does** | Pattern detection data access operations. Fetches failed runs for pattern analysis. Fetches completed runs for cost spike detection. Inserts PatternFeedback records. Queries feedback summaries. Pure DB operations - NO business logic. |
| **Tables Accessed** | WorkerRun (R), PatternFeedback (R/W) |
| **Callers** | pattern_detection.py (L5 engine) |
| **Decision Made** | None (pure data access). "Business decisions (threshold checks, pattern grouping) stay in L5." |
| **Key Pattern** | "Pattern detection" - behavioral analysis |
| **Why AMBIGUOUS** | Likely analytics vs incidents match on "pattern" |
| **Qualifier Test** | "WHAT can be derived?" → Pattern detection = behavioral analysis (derived insights) |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Pattern detection = behavioral analysis = derived insights from raw data. Driver supports analytics engines. Matches analytics: "behavioral analysis", "divergence". Not incidents because incidents are ABOUT failures - this is ANALYZING patterns IN failures.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

### [x] `analytics/L6_drivers/prediction_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | analytics |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Data access for prediction operations. Fetches failure patterns from feedback. Fetches failed runs and run totals. Fetches cost runs for projections. Reads/writes PredictionEvent. Pure DB operations - NO business logic. |
| **Tables Accessed** | PatternFeedback (R), PredictionEvent (R/W), WorkerRun (R) |
| **Callers** | prediction.py (L5 engine) |
| **Decision Made** | None (pure data access). "NO prediction math, thresholding, or confidence calculations - that stays in L4 engine." |
| **Governance Note** | "Predictions are ALWAYS advisory" - `is_advisory=True` enforced at driver level |
| **Why AMBIGUOUS** | Likely analytics vs activity (reads WorkerRun) |
| **Qualifier Test** | "WHAT can be derived?" → Predictions = derived metrics, advisory data |

**DECISION:** `analytics` ✓ (CONFIRMED CORRECT)
**Reason:** Predictions = derived metrics. Advisory-only data. Matches analytics: "derived metric", "statistical". The driver is explicit: "NO prediction math - that stays in L4" - pure data access for analytics domain.
**Action:** TODO: Update header or pyscript keywords to prevent false positive.

---

## incidents (16 files)

### [x] `incidents/L5_engines/channel_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Notification channel management (UI, WEBHOOK, EMAIL, SLACK, PAGERDUTY, TEAMS). Configures channels per tenant, validates connectivity, tracks delivery. |
| **Tables Accessed** | ChannelConfig (via driver) |
| **Callers** | alert_emitter, incident_service, policy_engine |
| **Decision Made** | Channel configuration, connectivity validation, delivery routing |
| **Key Pattern** | External system integration (Slack/PagerDuty/Teams webhooks) |
| **Why AMBIGUOUS** | Located in incidents but manages external adapters |
| **Qualifier Test** | "HOW external systems connect?" → Manages external notification bridges |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Manages external system connections (Slack, PagerDuty, Teams webhooks). The qualifier phrase "webhook", "connector", "integration" are explicit in integrations' qualifier_phrases. Called by multiple domains (cross-domain), not incident-specific.

---

### [x] `incidents/L5_engines/degraded_mode_checker.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Governance degraded mode tracking (NORMAL, DEGRADED, CRITICAL). Enforces degraded mode rules (block/warn runs). Creates incidents for mode transitions. |
| **Tables Accessed** | GovernanceState (via runtime_switch), Incident (writes on mode change) |
| **Callers** | ROK (L5), prevention_engine, incident_engine |
| **Decision Made** | Whether runs can proceed based on governance health |
| **Key Pattern** | "governance enforcement", "runtime enforcement", blocking/warning runs |
| **Why AMBIGUOUS** | Creates incidents but primary role is governance enforcement |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Controls run execution based on system health |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Primary decision is "WHEN runs can execute" (governance enforcement). Creating incidents is a side effect, not the core decision. Matches general's qualifier_phrases: "governance enforcement", "runtime enforcement". The file decides whether to BLOCK/WARN runs based on system state — that's runtime orchestration.

---

### [x] `incidents/L5_engines/evidence_report.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Generates legal-grade PDF evidence reports. Includes incident snapshot, executive summary, factual reconstruction, policy evaluation, decision timeline, replay verification, certificate (M23), prevention proof, legal attestation. |
| **Tables Accessed** | None (receives data as input) |
| **Callers** | guard.py (incident export endpoint) |
| **Decision Made** | PDF content structure, verification signature generation |
| **Key Pattern** | "evidence report", "proof", "legal attestation", "immutable record" |
| **Why AMBIGUOUS** | Reports about incidents but core function is evidence/proof generation |
| **Qualifier Test** | "WHAT immutable record exists?" → Creates verifiable evidence documents |

**DECISION:** `logs` ⚠️ (MISPLACED)
**Reason:** Matches logs' qualifier_phrases: "evidence report", "proof", "immutable record". The file generates legal-grade evidence documents — that's audit trail domain, not incident classification. An incident is the SUBJECT of the report; the DECISION is about evidence completeness and verification.

---

### [x] `incidents/L5_engines/failure_mode_handler.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Handles failure modes for policy evaluation (FAIL_CLOSED default, FAIL_OPEN, FAIL_WARN). Determines action when policy evaluation fails. |
| **Tables Accessed** | GovernanceConfig (reads via driver) |
| **Callers** | prevention_engine.py |
| **Decision Made** | STOP/WARN/CONTINUE when policy evaluation fails |
| **Key Pattern** | "policy failure", "policy evaluation", fail-closed default |
| **Why AMBIGUOUS** | Handles failures but specifically for policy evaluation |
| **Qualifier Test** | "WHAT rules govern behavior?" → Determines policy failure behavior |

**DECISION:** `policies` ⚠️ (MISPLACED)
**Reason:** Called by prevention_engine.py (policy domain). The decision is "what happens when policy evaluation fails" — that's policy behavior, not incident classification. The file doesn't classify failures as incidents; it determines the policy engine's response to its own failures.

---

### [x] `incidents/L5_engines/incident_read_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | L5 facade for incident read operations. Delegates to IncidentReadDriver (L6). Lists incidents, gets details, events, counts. |
| **Tables Accessed** | Incident, IncidentEvent (via driver) |
| **Callers** | customer_incidents_adapter.py (L3) |
| **Decision Made** | None (pure data access facade) |
| **Key Pattern** | Pure incident domain operations |
| **Why AMBIGUOUS** | Should not be ambiguous - pure incident reads |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Retrieves incident classifications |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Pure incident domain read operations. Correctly placed.

---

### [x] `incidents/L3_adapters/anomaly_bridge.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L3 — Boundary Adapter |
| **Audience** | CUSTOMER |
| **What It Does** | Anomaly-to-Incident bridge. Accepts CostAnomalyFact from analytics and decides if incident should be created. Applies severity/confidence thresholds, deduplication, suppression rules. |
| **Tables Accessed** | Incident (via IncidentWriteDriver) |
| **Callers** | Orchestrators that process CostAnomalyFact from analytics |
| **Decision Made** | "Does this anomaly warrant an incident?" |
| **Key Pattern** | Header explicitly states: "This bridge is OWNED BY INCIDENTS" |
| **Why AMBIGUOUS** | Bridge between analytics and incidents domains |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Decides if anomaly = incident |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Explicitly states "OWNED BY INCIDENTS". The decision is "does this anomaly warrant an incident" - that's incident classification.

---

### [x] `incidents/L5_engines/hallucination_detector.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Detects potential hallucinations in LLM outputs. Types: fabricated citations, invalid URLs, contradictions, capability overclaims. Non-blocking by default (60-90% confidence). |
| **Tables Accessed** | None (pure detection logic) |
| **Callers** | worker/runner.py, incident_engine.py |
| **Decision Made** | "Is this output a hallucination?" |
| **Key Pattern** | "failure classif", "violation detect" |
| **Why AMBIGUOUS** | Detection logic, not storage - could be analytics |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Classifies outputs as hallucinated |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Hallucination detection = failure classification. Emits "hallucination_detected" which feeds incident creation.

---

### [x] `incidents/L5_engines/incident_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine (System Truth) |
| **Audience** | INTERNAL |
| **What It Does** | Core incident creation engine. Implements SDSR cross-domain propagation: Run failure → Incident. Decides severity, category, suppression, title generation. |
| **Tables Accessed** | Incident, IncidentEvent, PreventionRecord (via driver) |
| **Callers** | Worker runtime, API endpoints |
| **Decision Made** | "Should incident be created? What severity? What category?" |
| **Key Pattern** | Core "incident classif" engine |
| **Why AMBIGUOUS** | Should not be ambiguous - core incidents engine |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Core incident classification |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Core incident domain engine. The definition of incidents domain.

---

### [x] `incidents/L5_engines/incident_write_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Incident write operations with audit. Acknowledge incidents, resolve incidents. Emits audit events. Transaction orchestration. |
| **Tables Accessed** | Incident, IncidentEvent (via driver) |
| **Callers** | customer_incidents_adapter.py (L3) |
| **Decision Made** | Incident state transitions (acknowledge, resolve) |
| **Key Pattern** | Pure incident domain operations |
| **Why AMBIGUOUS** | Should not be ambiguous - pure incident writes |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Manages incident state |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Pure incident domain write operations. Correctly placed.

---

### [x] `incidents/L5_engines/lessons_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine (System Truth) |
| **Audience** | INTERNAL |
| **What It Does** | Lessons learned creation. Creates lessons from failures, near-threshold events, success events. Lessons are "memory substrate for policy evolution." PolicyProposalEngine converts lessons to drafts. |
| **Tables Accessed** | LessonsLearned, PolicyProposal (via driver) |
| **Callers** | IncidentEngine, Worker runtime, API endpoints |
| **Decision Made** | "Should a lesson be created? What type?" |
| **Key Pattern** | "lesson learned" - EXPLICITLY in policies qualifier_phrases |
| **Why AMBIGUOUS** | Located in incidents but feeds policy evolution |
| **Qualifier Test** | "WHAT rules govern behavior?" → Lessons feed policy proposals |

**DECISION:** `policies` ⚠️ (MISPLACED)
**Reason:** "lesson learned" is EXPLICITLY in policies' qualifier_phrases. Lessons are the "memory substrate for policy evolution." References POLICIES_DOMAIN_AUDIT.md.

---

### [x] `incidents/L5_engines/mapper.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Maps incidents and evidence to SOC2 Trust Service Criteria controls for compliance exports, executive debriefs. |
| **Tables Accessed** | SOC2ControlRegistry (R) |
| **Callers** | export_bundle_service.py, api/incidents.py |
| **Decision Made** | "Which SOC2 controls does this incident relate to?" |
| **Key Pattern** | Compliance evidence mapping, SOC2 attestation |
| **Why AMBIGUOUS** | Operates on incidents but for compliance/audit purposes |
| **Qualifier Test** | "WHAT immutable record exists?" → Generates compliance evidence |

**DECISION:** `logs` ⚠️ (MISPLACED)
**Reason:** Maps incidents to SOC2 controls for compliance/audit purposes. Matches logs: "evidence record", "proof", "audit".

---

### [x] `incidents/L5_engines/panel_invariant_monitor.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Monitors panel-backing queries for silent governance failures. Detects empty panels, stale data, filter breaks. Out-of-band alerting. |
| **Tables Accessed** | Panel metrics (via driver) |
| **Callers** | main.py (scheduler), ops endpoints |
| **Decision Made** | "Is this panel state indicative of a system failure?" |
| **Key Pattern** | "governance enforcement", system health monitoring |
| **Why AMBIGUOUS** | Monitors for problems but doesn't classify incidents |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Detects governance failures |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Monitors system health for governance failures. "governance enforcement" in general's qualifier_phrases. Infrastructure monitoring, not incident classification.

---

### [x] `incidents/L5_engines/panel_verification_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Verifies panel inputs and enforces determinism rules. Hard failures on violations. Input validation, contradiction checking. |
| **Tables Accessed** | None (pure verification logic) |
| **Callers** | Panel adapters (L3) |
| **Decision Made** | "Are panel inputs valid? Is determinism preserved?" |
| **Key Pattern** | System enforcement, input validation |
| **Why AMBIGUOUS** | "verification" could be incident-related but this is panel infrastructure |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Enforces determinism rules |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Enforces system-wide determinism rules for panels. Infrastructure verification, not incident classification.

---

### [x] `incidents/L5_engines/pdf_renderer.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Renders export bundles to PDF format. Handles EvidenceBundle, SOC2Bundle, ExecutiveDebriefBundle. Uses reportlab. |
| **Tables Accessed** | None (receives bundles as input) |
| **Callers** | api/incidents.py |
| **Decision Made** | PDF structure and formatting |
| **Key Pattern** | "evidence documentation", "compliance exports" |
| **Why AMBIGUOUS** | Renders incident data but for compliance/evidence purposes |
| **Qualifier Test** | "WHAT immutable record exists?" → Creates evidence documents |

**DECISION:** `logs` ⚠️ (MISPLACED)
**Reason:** Renders evidence documentation for compliance. Similar to evidence_report.py. Matches logs: "evidence record", "proof".

---

### [x] `incidents/L5_engines/policy_violation_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Implements S3 violation truth model. Violation detection, fact persistence, incident creation (severity-bound), evidence linking. |
| **Tables Accessed** | Policy (R), PreventionRecord (R/W), PolicyEvaluation (W) via driver |
| **Callers** | L5 policy engine, L5 workers |
| **Decision Made** | "Was the policy violated? Create incident if yes." |
| **Key Pattern** | "violation detect", "threshold violation" |
| **Why AMBIGUOUS** | Involves both policy and incident domains |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Detects violations, creates incidents |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Primary decision is "was a rule violated?" - that's incident classification. Policy defines rules; incidents determines if rules were violated.

---

### [x] `incidents/L5_engines/recovery_evaluation_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine (System Truth) |
| **Audience** | CUSTOMER |
| **What It Does** | Recovery evaluation decision-making. Rule evaluation, pattern matching, confidence combination, action selection thresholds. |
| **Tables Accessed** | RecoveryRule, FailureHistory, RecoveryDecision (via driver) |
| **Callers** | API endpoints, failure processing pipeline |
| **Decision Made** | "What recovery action should be taken? Auto-execute?" |
| **Key Pattern** | "Rule evaluation", imports from policies.L6_drivers.recovery_matcher |
| **Why AMBIGUOUS** | Triggered by failures (incidents) but evaluates rules (policies) |
| **Qualifier Test** | "WHAT rules govern behavior?" → Evaluates recovery RULES |

**DECISION:** `policies` ⚠️ (MISPLACED)
**Reason:** Evaluates recovery RULES to make decisions. Imports RecoveryMatcher from policies domain. "Rule evaluation" is policy domain.

---

### [x] `incidents/L5_engines/runtime_switch.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Runtime toggle for governance enforcement. Emergency kill switch. Enable/disable governance. Degraded mode management. |
| **Tables Accessed** | None (in-memory state) |
| **Callers** | ops_api.py, failure_mode_handler.py, health.py, prevention_engine, runner.py |
| **Decision Made** | "Is governance active? Is system in degraded mode?" |
| **Key Pattern** | "runtime enforcement", "governance enforcement", "system-wide" |
| **Why AMBIGUOUS** | System state management, not incident classification |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Runtime orchestration |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** "Runtime toggle for governance enforcement" matches general's "runtime enforcement" and "governance enforcement". System-wide runtime orchestration, not customer-configured limits.

---

### [x] `incidents/L6_drivers/incident_aggregator.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Intelligent incident grouping to prevent explosion. Time-window aggregation, rate limiting, auto-escalation. |
| **Tables Accessed** | Incident (R/W), IncidentEvent (R/W) |
| **Callers** | L2 APIs, L5 workers |
| **Key Pattern** | Pure incident domain driver |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Incident data access |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Pure incident domain driver. Correctly placed.

---

### [x] `incidents/L6_drivers/incident_read_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pure data access for incident read operations. Query construction, data retrieval with tenant isolation. |
| **Tables Accessed** | Incident (R), IncidentEvent (R) |
| **Callers** | incident engines (L5) |
| **Key Pattern** | Pure incident domain driver |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Incident data access |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Pure incident domain read driver. Correctly placed.

---

### [x] `incidents/L6_drivers/incidents_facade_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pure database access for incidents facade. Returns snapshots (dicts/dataclasses), not ORM models. |
| **Tables Accessed** | Incident (R) |
| **Callers** | incidents_facade.py (L5) |
| **Key Pattern** | Pure incident domain driver |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Incident data access |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Pure incident domain driver. Correctly placed.

---

### [x] `incidents/L6_drivers/llm_failure_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pure data access for LLM failure operations. Create failure facts, evidence records, mark runs as failed. |
| **Tables Accessed** | RunFailure (R/W), FailureEvidence (R/W), WorkerRun (R/W) |
| **Callers** | LLMFailureEngine (L5) |
| **Key Pattern** | Pure incident domain driver for failure facts |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Failure fact persistence |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Pure incident domain driver for failure facts. Correctly placed.

---

### [x] `incidents/L6_drivers/policy_violation_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pure data access for policy violation handling. Create violation facts, check policy existence. |
| **Tables Accessed** | PreventionRecord (R/W), PolicyEvaluation (R/W), Policy (R), Incident (R) |
| **Callers** | PolicyViolationEngine (L5) |
| **Key Pattern** | Driver follows its engine (policy_violation_engine → incidents) |
| **Qualifier Test** | Driver follows engine domain |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** Driver follows its engine. PolicyViolationEngine is incidents domain.

---

### [x] `incidents/L6_drivers/postmortem_driver.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pure data access for post-mortem analytics. Category statistics, resolution methods, recurrence rates. |
| **Tables Accessed** | Incident (R) |
| **Callers** | PostMortemEngine (L5) |
| **Key Pattern** | "recurrence" - in incidents qualifier_phrases |
| **Qualifier Test** | "WHETHER an outcome is a problem?" → Incident recurrence analysis |

**DECISION:** `incidents` ✓ (CONFIRMED)
**Reason:** "recurrence" is in incidents' qualifier_phrases. Incident analytics domain.

---

### [x] `incidents/L6_drivers/scoped_execution.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | incidents |
| **Layer** | L6 — Domain Driver |
| **Audience** | CUSTOMER |
| **What It Does** | Pre-execution gate for MEDIUM+ risk recovery actions. Scope creation with incident binding, cost ceiling, action limits, expiry. |
| **Tables Accessed** | Scope (R), Incident (R) |
| **Callers** | L2 APIs (recovery actions), L5 workers |
| **Decision Made** | "Can this action execute within the defined scope?" |
| **Key Pattern** | "cost ceiling", "action limits" - matches controls qualifiers |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Execution scope limits |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** "cost ceiling" matches controls' "cost limit". "action limits" matches controls' "rate limit". Enforces execution limits.

---

**Incidents domain COMPLETE: 24 files reviewed, 12 confirmed, 12 misplaced**

---

## logs (35 files)

### [x] `logs/L3_adapters/export_bundle_adapter.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L3 — Boundary Adapter |
| **Audience** | CUSTOMER |
| **What It Does** | Generates structured export bundles from incidents and traces for evidence export, SOC2 compliance, and executive debriefs. |
| **Tables Accessed** | via L6 ExportBundleStore |
| **Callers** | L2 API routes |
| **Decision Made** | Bundle structure, evidence compilation |
| **Key Pattern** | "evidence export", "SOC2 compliance", "evidence bundle" |
| **Qualifier Test** | "WHAT immutable record exists?" → Creates compliance evidence |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Matches logs qualifiers: "evidence report", "proof", "audit". Creates immutable evidence records for compliance.

---

### [x] `logs/L5_engines/alert_fatigue.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Alert deduplication and fatigue control. Sliding window rate limiting, per-tenant/per-domain cooldowns, deduplication within window. |
| **Tables Accessed** | Redis (alert state via driver) |
| **Callers** | AlertEmitter (L3), EventReactor (L5) |
| **Decision Made** | "Should this alert be sent?" based on rate limits and cooldowns |
| **Key Pattern** | "rate limit", "sliding window rate limiting", "cooldown" |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Alert rate limits |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** "Rate limit" is EXPLICITLY in controls' qualifier_phrases. Controls WHEN alerts are sent via rate limiting and deduplication.

---

### [x] `logs/L5_engines/audit_durability.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | RAC durability enforcement before acknowledgment. Ensures audit data is durably stored before accepting acks. |
| **Tables Accessed** | durability state (via driver) |
| **Callers** | ROK (L5), Facades (L4), AuditReconciler (L4) |
| **Decision Made** | "Is storage durable? Can operation proceed?" |
| **Key Pattern** | "durability enforcement", "governance enforcement", "enforcement enabled" |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Governance enforcement for audit |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** "governance enforcement" in general's qualifier_phrases. This is governance enforcement for audit system invariants - decides WHEN operations can proceed based on durability.

---

### [x] `logs/L5_engines/audit_evidence.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Emits compliance-grade audit for MCP tool calls. Tamper-evident audit trail with integrity hashing. Sensitive data redaction. |
| **Tables Accessed** | audit events (via driver) |
| **Callers** | Runner, skill executor |
| **Decision Made** | Audit event structure, integrity hash generation |
| **Key Pattern** | "audit trail", "tamper-evident", "immutable record", "compliance-grade audit" |
| **Qualifier Test** | "WHAT immutable record exists?" → Creates tamper-evident audit events |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Multiple logs qualifiers: "audit trail", "immutable record", "evidence record". Creates compliance-grade, tamper-evident audit events.

---

### [x] `logs/L5_engines/audit_reconciler.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Reconciles audit expectations against acknowledgments. Four-way validation: missing actions, drift actions, stale runs, invalid contracts. |
| **Tables Accessed** | audit expectations, acknowledgments (via driver) |
| **Callers** | ROK (L5), Scheduler (L5) |
| **Decision Made** | "Is the audit record complete? What's missing?" |
| **Key Pattern** | "reconcile", "completeness", "audit" |
| **Qualifier Test** | "WHAT immutable record exists?" → Verifies audit completeness |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "completeness" is in logs' qualifier_phrases. Verifies audit record integrity and completeness.

---

### [x] `logs/L5_engines/reconciler.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Performs four-way validation of audit expectations vs acknowledgments: (1) expected − acked → missing audit alert, (2) acked − expected → drift detection, (3) missing finalization → stale run (liveness violation), (4) expectations without deadline → invalid contract. Core of Runtime Audit Contract (RAC). |
| **Tables Accessed** | AuditExpectation (R), DomainAck (R) via AuditStore |
| **Callers** | ROK (L5), Scheduler (L5) |
| **Decision Made** | "Is the audit trail complete?" - validates expectations against acknowledgments, detects missing/drift/stale entries |
| **Key Pattern** | "reconcile", "completeness", "audit expectations", "Runtime Audit Contract" |
| **Qualifier Test** | "WHAT immutable record exists?" → audit reconciliation = completeness verification of audit trail |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "completeness" qualifier matches logs. Validates audit trail integrity. Not deriving insights (analytics), validating existing audit records exist.

---

### [x] `logs/L5_engines/traces_metrics.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Prometheus metrics instrumentation for AOS Traces API. Exports: aos_trace_request_duration_seconds (Histogram), aos_trace_requests_total (Counter), aos_trace_parity_status (Gauge), aos_replay_enforcement_total (Counter), aos_idempotency_total (Counter). Pure observability infrastructure, no business logic. |
| **Tables Accessed** | None (metrics export only) |
| **Callers** | trace store |
| **Decision Made** | None - pure instrumentation, emits metrics counters/histograms |
| **Key Pattern** | Prometheus metrics, observability instrumentation |
| **Qualifier Test** | No domain qualifier matches. Not "WHAT immutable record" (logs), not "WHAT can be derived" (analytics), not classification/enforcement. Pure Prometheus instrumentation infrastructure. |

**DECISION:** `general/L5_Infra/metrics/` ⚠️ (MISPLACED → INFRASTRUCTURE)
**Reason:** Observability instrumentation doesn't own a business decision. Pure Prometheus metrics infrastructure. Move to general infrastructure path: `general/L5_Infra/metrics/traces_metrics.py`.

---

### [x] `logs/L5_engines/monitors_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Monitors Facade for external service health monitoring. CRUD for monitors: HTTP, TCP, DNS, heartbeat, custom. Runs health checks against external endpoints. Tracks monitor status: healthy/unhealthy/degraded. API routes: create/list/get/update/delete monitors, run health check, get check history, get overall status. |
| **Tables Accessed** | Monitors, HealthChecks (via driver) |
| **Callers** | L2 monitors.py API, SDK, Scheduler |
| **Decision Made** | "Is the external service healthy?" - monitors external HTTP/TCP/DNS endpoints, not internal audit records |
| **Key Pattern** | External service health monitoring, HTTP/TCP/DNS health checks |
| **Qualifier Test** | "HOW external systems connect?" → monitors external service health. "webhook" in integrations qualifiers. This monitors EXTERNAL systems, not internal audit/evidence records. |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Monitors external services (HTTP, TCP, DNS health). Matches integrations "connector", "external". Not about immutable audit records.

---

### [x] `logs/L5_engines/evidence_report.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Evidence report generator - Legal-grade PDF export for AI incidents. Creates deterministic, verifiable PDF evidence reports that survive legal review, audit, and hostile questioning. Includes: Cover page with metadata, Executive summary for legal/leadership, Factual reconstruction (pure evidence), Policy evaluation record, Decision timeline (deterministic trace), Replay verification with hash matching, Counterfactual prevention proof, Remediation & controls, Legal attestation with verification signature. |
| **Tables Accessed** | None (PDF generation only, reads incident evidence data) |
| **Callers** | guard.py (incident export endpoint) |
| **Decision Made** | "WHAT is the immutable evidence record?" - generates legal-grade proof documents with verification signatures |
| **Key Pattern** | "evidence report", "proof", "legal attestation", "verification signature", "audit" |
| **Qualifier Test** | "WHAT immutable record exists?" → evidence report generation. Strong qualifiers: "evidence report" → logs, "proof" → logs, "audit" → logs, "legal attestation" → logs |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "evidence report", "proof", "audit" all match logs domain. Creates immutable, verifiable evidence records.

---

### [x] `logs/L5_engines/notifications_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Notifications Facade for multi-channel notification delivery. Supports channels: email, slack, webhook, in_app, sms. Priorities: low, normal, high, urgent. API routes: send notification, list notifications, get notification, mark as read, list channels, update preferences. |
| **Tables Accessed** | Notifications, Preferences (via driver) |
| **Callers** | L2 notifications.py API, SDK, Worker |
| **Decision Made** | "HOW do we deliver to external channels?" - routes notifications to email/slack/webhook/sms |
| **Key Pattern** | Multi-channel notification delivery: email, Slack, webhook, in_app, SMS |
| **Qualifier Test** | "HOW external systems connect?" → notification delivery to external channels. "webhook" → integrations qualifier. This is an external adapter for notification delivery, not audit/evidence records. |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Delivers notifications to external channels (email, Slack, webhook, SMS). Matches integrations "webhook", "external adapter", "connector". Not about immutable audit records.

---

### [x] `logs/L5_engines/alerts_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Alerts Facade for alert operations. CRUD for alert rules: create/list/get/update/delete alert rules. Alert routing configuration. Alert history retrieval. Manages customer-configured alert thresholds and conditions (metric thresholds, severity levels). |
| **Tables Accessed** | AlertRule, AlertHistory, AlertRoute (via driver) |
| **Callers** | L2 alerts.py API, SDK, Worker |
| **Decision Made** | "What alert rules are configured? What thresholds trigger alerts?" Customer-configured alert conditions and thresholds. |
| **Key Pattern** | Alert rules, thresholds, conditions, routing configuration |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Customer-configured alert thresholds and rules. "threshold config" matches controls. Not "WHAT immutable record" (logs). |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** Manages customer-configured alert rules with thresholds and conditions. "threshold config" is in controls' qualifier_phrases. Alert rules define WHEN alerts fire based on limits/thresholds - that's controls domain.

---

### [x] `logs/L5_engines/audit_ledger_service.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Sync audit ledger writer for governance events. APPEND-ONLY immutable governance action log. All writes are INSERT only - no UPDATE, no DELETE. Writes incident_acknowledged, incident_resolved, incident_manually_closed events to AuditLedger table. |
| **Tables Accessed** | AuditLedger (W - append-only) |
| **Callers** | incident_write_engine (L5) |
| **Decision Made** | None - pure audit trail emission. Writes immutable governance events. |
| **Key Pattern** | "audit ledger", "append-only", "immutable", "INSERT only" |
| **Qualifier Test** | "WHAT immutable record exists?" → Core audit ledger writer. "audit ledger", "append-only", "immutable record" all match logs. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Core audit ledger writer. Multiple logs qualifiers: "audit ledger", "append-only", "immutable record". THE canonical audit trail writer.

---

### [x] `logs/L5_engines/certificate.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | M23 Certificate Service - Cryptographic evidence of deterministic replay. Creates HMAC-signed certificates that prove: (1) Policy decisions were evaluated at specific time, (2) Replay validation passed at specific determinism level, (3) No tampering occurred between original call and validation. Certificate types: REPLAY_PROOF, POLICY_AUDIT, INCIDENT_EXPORT. |
| **Tables Accessed** | None (pure computation - cryptographic signature generation) |
| **Callers** | guard.py (replay endpoint) |
| **Decision Made** | Certificate validity, signature generation, expiry enforcement |
| **Key Pattern** | "cryptographic evidence", "signed certificates", "HMAC signature", "proof", "validation_passed" |
| **Qualifier Test** | "WHAT immutable record exists?" → Creates cryptographic proof certificates. "proof" is in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Generates cryptographic proof certificates. "proof" is explicitly in logs' qualifier_phrases. Creates verifiable evidence of replay/policy/incident validation.

---

### [x] `logs/L5_engines/completeness_checker.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Evidence PDF completeness validation for SOC2 compliance. Validates that all required fields are present before allowing PDF generation. Required fields: incident_id, tenant_id, run_id, trace_id, policy_snapshot_id, termination_reason, total_steps, total_tokens, total_cost_cents. SOC2 required: control_mappings, attestation_statement, compliance_period_start/end. |
| **Tables Accessed** | None (pure validation logic) |
| **Callers** | pdf_renderer, evidence_report, export APIs |
| **Decision Made** | "Is evidence bundle complete for export?" |
| **Key Pattern** | "completeness validation", "SOC2 compliance", "evidence bundle", "required fields" |
| **Qualifier Test** | "WHAT immutable record exists?" → Validates evidence completeness before export. "completeness" is in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "completeness" is explicitly in logs' qualifier_phrases. Validates evidence bundle integrity before export. Core to audit/evidence quality.

---

### [x] `logs/L5_engines/compliance_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Compliance Facade for compliance verification operations. Runs compliance verification across scopes: ALL, DATA, POLICY, COST, SECURITY. Generates compliance reports. Lists compliance rules. Returns compliance status: COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT. |
| **Tables Accessed** | ComplianceRule, ComplianceReport (via driver) |
| **Callers** | L2 compliance.py API, SDK |
| **Decision Made** | "Is tenant compliant? Generate compliance report." |
| **Key Pattern** | "compliance verification", "compliance reports", "compliance status" |
| **Qualifier Test** | "WHAT immutable record exists?" → Generates compliance reports (audit artifacts). Reports prove compliance status at point in time. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Generates compliance reports which are audit artifacts proving compliance status. Compliance reports = evidence/proof of compliance state.

---

### [x] `logs/L5_engines/connectors_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Connectors Facade for connector operations. Manages HTTP, SQL, MCP connectors. CRUD for connectors: register, list, get, update, delete. Tests connector connectivity. Wrapped services: ConnectorRegistry, HTTPConnector, SQLConnector, MCPConnector. |
| **Tables Accessed** | ConnectorRegistry (via driver) |
| **Callers** | L2 connectors.py API, SDK |
| **Decision Made** | "Which connectors are available? Does connection work?" |
| **Key Pattern** | "connector", "HTTP connector", "SQL connector", "MCP connector", "test connector" |
| **Qualifier Test** | "HOW external systems connect?" → Manages external connectors (HTTP, SQL, MCP). "connector" is explicitly in integrations qualifiers. |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** "connector" is explicitly in integrations' qualifier_phrases. Manages external HTTP, SQL, MCP connectors. Core external system connectivity.

---

### [x] `logs/L5_engines/controls_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Controls Facade for control operations. Manages system controls: KILLSWITCH, CIRCUIT_BREAKER, FEATURE_FLAG, THROTTLE, MAINTENANCE. Enable/disable controls. Get control status. Control states: ENABLED, DISABLED, AUTO. |
| **Tables Accessed** | ControlConfig, ControlState (via driver) |
| **Callers** | L2 controls.py API, SDK |
| **Decision Made** | "What controls are active? Enable/disable control." |
| **Key Pattern** | "killswitch", "circuit breaker", "feature flag", "throttle" - ALL explicitly in controls qualifier_phrases |
| **Qualifier Test** | "WHAT limits and configurations apply?" → Manages killswitches, circuit breakers, feature flags, throttles - core controls domain. |

**DECISION:** `controls` ⚠️ (MISPLACED)
**Reason:** "killswitch", "circuit breaker", "feature flag", "throttle" are ALL explicitly in controls' qualifier_phrases. This IS the controls domain facade.

---

### [x] `logs/L5_engines/datasources_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | DataSources Facade for data source operations. Manages external data sources. CRUD: create, list, get, update, delete. Test connection. Activate/deactivate sources. Imports from integrations.L5_schemas.datasource_model. |
| **Tables Accessed** | CustomerDataSource, DataSourceRegistry (via driver) |
| **Callers** | L2 datasources.py API, SDK |
| **Decision Made** | "Which data sources are configured? Test connection." |
| **Key Pattern** | "data source registration", "test connection", "connector" - imports from integrations domain schemas |
| **Qualifier Test** | "HOW external systems connect?" → External data source management. Actually imports from integrations.L5_schemas - belongs with integrations. |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Manages external data sources. Imports from `integrations.L5_schemas.datasource_model`. External system connection management = integrations.

---

### [x] `logs/L5_engines/detection_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Detection Facade for anomaly detection operations. Detection types: COST (spikes, drift, budget), BEHAVIORAL (patterns), DRIFT (model/data drift), POLICY (violations). Lists anomalies, resolves anomalies. Wraps CostAnomalyDetector, BehavioralDetector, DriftDetector. |
| **Tables Accessed** | Anomalies (via driver) |
| **Callers** | L2 detection.py API, SDK, Worker |
| **Decision Made** | "Is this data anomalous? What anomalies exist?" |
| **Key Pattern** | "anomaly detection", "behavioral anomalies", "drift detection", "cost anomalies" |
| **Qualifier Test** | "WHAT can be derived?" → Anomaly detection = behavioral analysis + divergence detection. Detects patterns in data to identify anomalies. "behavioral analysis", "divergence" in analytics qualifiers. |

**DECISION:** `analytics` ⚠️ (MISPLACED)
**Reason:** Anomaly detection = behavioral analysis (deriving anomalies from data patterns). "behavioral analysis" and "divergence" are in analytics' qualifier_phrases. Detection is about deriving insights, not classifying incidents.

---

### [x] `logs/L5_engines/durability.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | RAC durability enforcement before acknowledgment. Ensures audit contracts survive crashes by enforcing durable storage. When enabled: acks must be persisted, expectations must be durably stored, in-memory mode raises RACDurabilityEnforcementError. |
| **Tables Accessed** | Durability state (via driver) |
| **Callers** | ROK (L5), Facades (L4), AuditReconciler (L4) |
| **Decision Made** | "Is storage durable? Can operation proceed?" |
| **Key Pattern** | "durability enforcement", "governance enforcement", "RAC durability" |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Governance enforcement for system durability invariants. "governance enforcement" matches general. |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** "governance enforcement" is in general's qualifier_phrases. Enforces system-wide durability invariants before operations proceed. Same pattern as audit_durability.py.

---

### [x] `logs/L5_engines/evidence_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Evidence Facade for evidence chain and export operations. Manages evidence chains: list, get, create, verify integrity. Evidence types: EXECUTION, RETRIEVAL, POLICY, COST, INCIDENT. Export formats: JSON, CSV, PDF. Verifies chain integrity via hash verification. |
| **Tables Accessed** | EvidenceChain, EvidenceExport (via driver) |
| **Callers** | L2 evidence.py API, SDK |
| **Decision Made** | "Is evidence chain valid? Export evidence in format X." |
| **Key Pattern** | "evidence chains", "verify chain integrity", "export evidence", "evidence record" |
| **Qualifier Test** | "WHAT immutable record exists?" → Manages evidence chains and integrity verification. "evidence record" is in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Core evidence management. "evidence record" is explicitly in logs' qualifier_phrases. Manages evidence chains, integrity verification, and export.

---

### [x] `logs/L5_engines/export_completeness_checker.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Export completeness validation for SOC2 compliance. Validates required fields before PDF generation. Required fields: incident_id, tenant_id, run_id, trace_id, policy_snapshot_id, etc. SOC2 required: control_mappings, attestation_statement, compliance_period dates. (NOTE: Appears to be duplicate of completeness_checker.py) |
| **Tables Accessed** | None (pure validation logic) |
| **Callers** | pdf_renderer, evidence_report, export APIs |
| **Decision Made** | "Is evidence bundle complete for export?" |
| **Key Pattern** | "completeness validation", "SOC2 compliance", "required fields" |
| **Qualifier Test** | "WHAT immutable record exists?" → Validates evidence completeness. "completeness" is in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "completeness" is explicitly in logs' qualifier_phrases. Same pattern as completeness_checker.py. Validates evidence export quality.

---

### [x] `logs/L5_engines/lifecycle_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Lifecycle Facade for agent and run lifecycle operations. Agent states: CREATED, STARTING, RUNNING, STOPPING, STOPPED, TERMINATED, ERROR. Run states: PENDING, RUNNING, PAUSED, COMPLETED. Operations: create, start, stop, terminate agents; create, pause, resume, cancel runs. |
| **Tables Accessed** | Agents, Runs (via driver) |
| **Callers** | L2 lifecycle.py API, SDK |
| **Decision Made** | "What state is agent/run in? Transition to next state." |
| **Key Pattern** | "agent lifecycle", "run lifecycle", "run state", "state transitions" |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → System-wide lifecycle state management. Activity domain imports FROM this for run state definitions. |

**DECISION:** `general/L5_engines/lifecycle/` ⚠️ (MISPLACED)
**Reason:** System-wide lifecycle management that defines canonical agent/run states. Activity domain needs to IMPORT from this to define LLM_RUN states. This is shared infrastructure, not activity-specific logic. Move to `general/L5_engines/lifecycle/lifecycle_facade.py`.

---

### [x] `logs/L5_engines/logs_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Logs Domain Facade - unified entry point for all logs operations. Covers: LLM_RUNS (envelope, trace, governance, replay, export), SYSTEM_LOGS (snapshot, telemetry, events, replay, audit), AUDIT (identity, authorization, access, integrity, exports). All responses include EvidenceMetadata per INV-LOG-META-001. Composition-only, delegates to L6 LogsDomainStore. |
| **Tables Accessed** | Via L6 LogsDomainStore |
| **Callers** | L2 logs API, L3 adapters |
| **Decision Made** | None - composition/delegation only, orchestrates log queries |
| **Key Pattern** | "audit", "system log", "evidence metadata", "trace", "replay" |
| **Qualifier Test** | "WHAT immutable record exists?" → Core logs domain facade. "audit", "system log" are in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** THE core logs domain facade. "audit", "system log" are explicitly in logs' qualifier_phrases. Orchestrates all logs domain operations.

---

### [x] `logs/L5_engines/logs_read_engine.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Logs/Traces domain read operations. Query traces with tenant isolation, get trace details, get trace counts, search traces with filters. Sits between L3 adapter and L6 PostgresTraceStore. No write operations. |
| **Tables Accessed** | TraceRecord, TraceSummary (via L6 PostgresTraceStore) |
| **Callers** | customer_logs_adapter.py (L3) |
| **Decision Made** | None - pure read operations for traces |
| **Key Pattern** | "trace reads", "search traces", "trace details" |
| **Qualifier Test** | "WHAT immutable record exists?" → Trace read operations. "trace" is in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "trace" is in logs' qualifier_phrases. Pure trace read operations for logs domain.

---

### [x] `logs/L5_engines/pdf_renderer.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Renders export bundles to PDF format for compliance exports, executive debriefs, and evidence documentation. Handles EvidenceBundle, SOC2Bundle, ExecutiveDebriefBundle using reportlab. Same library as evidence_report.py. |
| **Tables Accessed** | None (receives bundles as input) |
| **Callers** | api/incidents.py |
| **Decision Made** | PDF structure and formatting for evidence documentation |
| **Key Pattern** | "evidence documentation", "compliance exports", "SOC2 attestations" |
| **Qualifier Test** | "WHAT immutable record exists?" → Creates evidence documentation PDFs |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Creates evidence documentation. Matches logs qualifiers: "evidence report", "proof". Same purpose as evidence_report.py. Creates compliance-grade PDF evidence.

---

### [x] `logs/L5_engines/redact.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | PII redaction for trace data before storage. Fixed regex patterns for passwords, API keys, tokens, credit cards, emails. Security compliance (GDPR/SOC2). Pure data transformation with fixed rules. |
| **Tables Accessed** | None (pure transformation) |
| **Callers** | trace store |
| **Decision Made** | None - executes fixed security patterns, no business decisions |
| **Key Pattern** | "trace data redaction", "compliance standard (GDPR/SOC2)", "security rules" |
| **Qualifier Test** | "WHAT immutable record exists?" → Ensures traces are compliance-redacted before becoming immutable. Supports trace integrity. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** Trace-specific PII redaction for compliance. Supports logs domain's trace storage with security-compliant data handling. Integral to trace evidence integrity. Not general infrastructure - specifically for trace data.

---

### [x] `logs/L5_engines/replay_determinism.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Replay determinism validation for LLM calls. Defines canonical determinism levels (STRICT, LOGICAL, SEMANTIC). Validates replay results. Addresses logical vs byte-for-byte determinism. |
| **Tables Accessed** | None (pure validation) |
| **Callers** | logs_facade.py, evidence services, other domains (read-only) |
| **Decision Made** | "Is replay deterministic?" - validates replay outcomes against determinism level |
| **Key Pattern** | "replay", "determinism", "version tracking", "audit trail" |
| **Governance** | INV-LOGS-003 — Determinism definitions live here exclusively |
| **Qualifier Test** | "WHAT immutable record exists?" → Validates trace replay fidelity. "trace" and "replay" are logs qualifiers. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "trace" is in logs' qualifier_phrases. Canonical determinism definitions for replay validation per INV-LOGS-003. Core logs domain functionality for trace integrity verification.

---

### [x] `logs/L5_engines/retrieval_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Retrieval Facade for mediated data retrieval. Provides APIs: mediated data access, list available planes, retrieve evidence records. Wraps RetrievalMediator. Single point for audit emission. |
| **Tables Accessed** | evidence, planes (via driver) |
| **Callers** | L2 retrieval.py API, SDK |
| **Decision Made** | None - facade/delegation only, orchestrates retrieval with policy enforcement |
| **Key Pattern** | "mediated data retrieval", "policy enforcement", "unified access", "audit emission" |
| **Qualifier Test** | Wraps general mediator. "connector" access + policy check + evidence = cross-domain orchestrator |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Facade over RetrievalMediator which is system-wide data access governance. Provides unified access to multiple data planes with policy enforcement. Cross-domain orchestration, not logs-specific.

---

### [x] `logs/L5_engines/retrieval_mediator.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | CENTRAL CHOKE POINT for all external data access. Deny-by-default. Policy check before connector. Evidence emitted for every access. Tenant isolation enforced. |
| **Tables Accessed** | external data (via connectors) |
| **Callers** | L2 API routes, skill execution |
| **Decision Made** | "Is this data access allowed?" - coordinates policy, connectors, evidence |
| **Key Pattern** | "central choke point", "deny-by-default", "policy check", "connector", "evidence emitted" |
| **Invariant** | "Deny-by-default. All access blocked unless explicitly allowed." |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → "gateway control" in general. Coordinates policies (policy check), integrations (connectors), logs (evidence). System-wide orchestration. |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Central orchestrator for data access that coordinates policies (policy check), integrations (connectors), and logs (evidence). Matches general's "gateway control" qualifier. System-wide data access governance, not domain-specific.

---

### [x] `logs/L5_engines/panel_slot_evaluator.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Evaluates individual panel slots given collected signals and verification results. Computes derived output signals (system_state, attention_required, highest_severity). |
| **Tables Accessed** | None (pure evaluation) |
| **Callers** | Panel adapters |
| **Decision Made** | "What is the slot state?" - computes derived panel signals |
| **Key Pattern** | "panel slots", "system_state", "attention_required", "verification" |
| **Qualifier Test** | Panel infrastructure, not logs-specific. System-wide UI panel evaluation. |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Panel slot evaluation is system-wide UI infrastructure. Computes system_state, attention signals for panels. Infrastructure for all domains' panels, not logs-specific.

---

### [x] `logs/L5_engines/scheduler_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Scheduler Facade for job scheduling operations. CRUD for scheduled jobs, trigger/pause/resume jobs, job run history. Cron-style scheduling. |
| **Tables Accessed** | jobs (via driver) |
| **Callers** | L2 scheduler.py API, SDK, Worker |
| **Decision Made** | "When should jobs execute?" - schedule management |
| **Key Pattern** | "job scheduling", "scheduled execution", "cron", "trigger job" |
| **Qualifier Test** | "WHEN and HOW system actions execute?" → Job scheduling is system-wide orchestration. |

**DECISION:** `general` ⚠️ (MISPLACED)
**Reason:** Job scheduling is system-wide orchestration. Controls WHEN things execute. Matches general's "execution order" and "workflow orchestrat" patterns. Not logs-specific.

---

### [x] `logs/L5_engines/service.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Credential Service for credential management. Input validation, audit logging, expiration checking, rotation scheduling. Wraps CredentialVault. |
| **Tables Accessed** | credentials (via driver) |
| **Callers** | ConnectorRegistry, LifecycleHandlers, API routes |
| **Decision Made** | "Is credential valid? When to rotate?" |
| **Key Pattern** | "credential management", "credential vault", "rotation scheduling" |
| **Qualifier Test** | "HOW external systems connect?" → Credentials for connectors. "integration config" in integrations. |

**DECISION:** `integrations` ⚠️ (MISPLACED)
**Reason:** Credential/vault management for connectors. Callers include ConnectorRegistry. Secrets management for external connections matches integrations' "integration config" qualifier.

---

### [x] `logs/L5_engines/trace_facade.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Trace Domain Facade - centralized access to trace operations with RAC acknowledgments. Wraps TraceStore operations, emits START_TRACE/COMPLETE_TRACE acks. |
| **Tables Accessed** | traces (via driver) |
| **Callers** | L5 runner/observability guard, API routes |
| **Decision Made** | None - facade for trace operations |
| **Key Pattern** | "trace operations", "RAC acknowledgments", "trace domain" |
| **Qualifier Test** | "WHAT immutable record exists?" → "trace" is in logs' qualifier_phrases. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "trace" is in logs' qualifier_phrases. Core trace domain facade. Centralized trace operations with audit (RAC) acknowledgments.

---

### [x] `logs/L5_engines/traces_models.py`

| Attribute | Value |
|-----------|-------|
| **Current Domain** | logs |
| **Layer** | L5 — Domain Engine |
| **Audience** | CUSTOMER |
| **What It Does** | Trace data models (dataclasses). Defines structure for execution traces, replay verification, determinism testing. Determinism invariant per PIN-126. |
| **Tables Accessed** | None (pure data models) |
| **Callers** | traces/* |
| **Decision Made** | None - pure data model definitions |
| **Key Pattern** | "trace models", "replay verification", "determinism" |
| **Qualifier Test** | "WHAT immutable record exists?" → Trace data structures for logs domain. |

**DECISION:** `logs` ✓ (CONFIRMED)
**Reason:** "trace" is in logs' qualifier_phrases. Pure trace data models supporting trace domain.

---

**Logs L5_engines COMPLETE. Remaining: L6_drivers + L5_schemas + L3_adapters**

---

## general (28 files)

(Pending audit)

---

## integrations (31 files)

(Pending audit)

---

## policies (55 files)

### [x] `policies/L5_controls/drivers/killswitch_read_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Pure data access for killswitch read operations. Query killswitch
  state for tenant, query active guardrails, query incident statistics.
  No mutations - read-only. ORM ↔ DTO transformation.
────────────────────────────────────────
Attribute: Tables Accessed
Value: KillSwitchState (R), DefaultGuardrail (R), Incident (R)
────────────────────────────────────────
Attribute: Callers
Value: killswitch engines (L4)
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "killswitch", "guardrails", "read operations"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "killswitch" is
  EXPLICITLY in controls' qualifier_phrases.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "killswitch" is EXPLICITLY in controls' qualifier_phrases. Driver
  for killswitch data which is a control mechanism, not policy rules.
```

---

### [x] `policies/L5_controls/drivers/runtime_switch.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Runtime toggle for governance enforcement. Emergency kill switch.
  Provides: is_governance_active(), disable_governance_runtime(),
  enable_governance_runtime(), is_degraded_mode(), enter_degraded_mode(),
  exit_degraded_mode(). Thread-safe operations.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (in-memory state)
────────────────────────────────────────
Attribute: Callers
Value: ops_api.py, failure_mode_handler.py, health.py, prevention_engine,
  runner.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Is governance active? Is system in degraded mode?" - runtime state
  decisions for system-wide enforcement
────────────────────────────────────────
Attribute: Key Pattern
Value: "runtime toggle", "governance enforcement", "emergency kill switch",
  "degraded mode management"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "governance enforcement"
  and "runtime enforcement" are in general's qualifier_phrases. System-wide
  runtime orchestration for ops/emergency use.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: "governance enforcement" matches general's qualifier. System-wide
  runtime toggle called by ops_api, runner, health. Not customer-configured
  limits - this is system orchestration.
```

---

### [x] `policies/L5_controls/engines/degraded_mode_checker.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L4 — Domain Engines
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Governance degraded mode checker with incident response. Tracks
  degraded state (NORMAL/DEGRADED/CRITICAL), creates incidents for
  degraded mode transitions, enforces degraded mode rules (block new runs,
  warn existing), integrates with incident response for visibility.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None apparent (in-memory state management)
────────────────────────────────────────
Attribute: Callers
Value: ROK (L5), prevention_engine, incident_engine
────────────────────────────────────────
Attribute: Decision Made
Value: "Is governance degraded? What mode?" - determines if runs can
  execute based on governance health state
────────────────────────────────────────
Attribute: Key Pattern
Value: "governance degraded mode", "incident integration", "block new runs",
  "governance state transitions"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → Governance state management
  for system-wide operations. Decides WHEN runs can execute.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: Governance state management deciding WHEN actions can execute.
  "governance enforcement" in general's qualifier_phrases. System health
  monitoring, not customer policy rules.
```

---

### [x] `policies/L5_controls/engines/customer_killswitch_read_engine.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: Product
Value: ai-console (Customer Console)
────────────────────────────────────────
Attribute: What It Does
Value: Customer killswitch read operations. L5 engine over L6 driver.
  Delegates ALL database operations to KillswitchReadDriver (L6). No
  direct database access - only driver calls.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via KillswitchReadDriver (L6)
────────────────────────────────────────
Attribute: Callers
Value: customer_killswitch_adapter.py (L3)
────────────────────────────────────────
Attribute: Decision Made
Value: None - read operations delegating to driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "killswitch", "customer", "read operations"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "killswitch" is
  EXPLICITLY in controls' qualifier_phrases. Customer-facing killswitch.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "killswitch" is EXPLICITLY in controls' qualifier_phrases.
  Customer-facing killswitch operations belong in controls domain, not
  policies.
```

---

### [x] `policies/L5_schemas/retry.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Platform Substrate (per header)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied)
────────────────────────────────────────
Attribute: What It Does
Value: Retry Policy schemas. Defines retry behavior and backoff strategies:
  CONSTANT, LINEAR, EXPONENTIAL, FIBONACCI. Configures max_attempts,
  initial_delay, max_delay, jitter, retryable_errors.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: API routes
────────────────────────────────────────
Attribute: Decision Made
Value: None - data model definitions for retry configuration
────────────────────────────────────────
Attribute: Key Pattern
Value: "retry policy", "backoff strategy", "max_attempts", "retry behavior"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "retry logic" is
  EXPLICITLY in general's qualifier_phrases. Defines WHEN/HOW actions
  re-execute after failure.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: "retry logic" is EXPLICITLY in general's qualifier_phrases. Retry
  policies define WHEN and HOW actions re-execute. System orchestration
  infrastructure, not customer-configured policy rules.
```

---

### [x] `policies/L5_schemas/overrides.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schema
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied)
────────────────────────────────────────
Attribute: What It Does
Value: Limit override request/response schemas. Temporary limit increase
  requests with approval workflow. OverrideStatus: PENDING, APPROVED,
  ACTIVE, EXPIRED, REJECTED, CANCELLED. Includes duration, reason,
  business justification.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: api/limits/override.py, services/limits/override_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: None - data model definitions for limit override requests
────────────────────────────────────────
Attribute: Key Pattern
Value: "limit override", "temporary limit increases", "override_value"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → Limit overrides are
  temporary changes to LIMITS. "limit" context = controls domain.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: Limit override schemas. Overrides temporarily modify LIMITS, which
  belong to controls domain. Not policy rules - these are limit structures.
```

---

### [x] `policies/L5_schemas/simulation.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schema
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied)
────────────────────────────────────────
Attribute: What It Does
Value: Limit simulation request/response schemas. Pre-execution limit
  checks (dry-run). SimulationDecision: ALLOW/BLOCK/WARN. MessageCodes
  for limit breaches: DAILY_RUN_LIMIT_EXCEEDED, RATE_LIMIT_EXCEEDED,
  MONTHLY_COST_BUDGET_EXCEEDED, THRESHOLD_LIMIT_EXCEEDED, etc.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: api/limits/simulate.py, services/limits/simulation_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: None - data model definitions for limit simulation
────────────────────────────────────────
Attribute: Key Pattern
Value: "limit simulation", "pre-execution limit checks", "rate limit",
  "budget exceeded", "threshold limit"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → Simulation of LIMITS
  enforcement. "rate limit", "budget" explicitly in controls qualifiers.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: Limit simulation schemas. "rate limit", "budget", "threshold limit"
  are controls qualifiers. These define schemas for checking controls/limits
  before execution.
```

---

### [x] `policies/L5_schemas/policy_rules.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schema
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied)
────────────────────────────────────────
Attribute: What It Does
Value: Policy rules request/response schemas. CRUD operations for policy
  rules. Rules define governance constraints that govern LLM Run behavior.
  EnforcementMode (BLOCK/WARN/AUDIT/DISABLED), PolicyScope
  (GLOBAL/TENANT/PROJECT/AGENT), PolicySource (MANUAL/SYSTEM/LEARNED).
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: api/policies.py, services/limits/policy_rules_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: None - data model definitions for policy rules
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy rule", "governance constraints", "enforcement modes"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "policy rule" in policies'
  weak_keywords. "governance rule" in policies' qualifier_phrases.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: "policy rule" matches policies domain. Defines governance
  constraints that govern LLM Run behavior. Core policies domain schemas.
```

---

### [x] `policies/L5_schemas/policy_limits.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schema
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied)
────────────────────────────────────────
Attribute: What It Does
Value: Policy limits request/response schemas. CRUD for limits.
  LimitCategory: BUDGET/RATE/THRESHOLD. LimitEnforcement:
  BLOCK/WARN/REJECT/QUEUE/DEGRADE/ALERT. LimitScope:
  GLOBAL/TENANT/PROJECT/AGENT/PROVIDER. ResetPeriod: DAILY/WEEKLY/MONTHLY.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: api/policies.py, services/limits/policy_limits_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: None - data model definitions for limits
────────────────────────────────────────
Attribute: Key Pattern
Value: "budget", "rate", "threshold", "limit enforcement", "limit scope"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → Despite name "policy_limits",
  content is BUDGET/RATE/THRESHOLD limits. "rate limit", "budget",
  "threshold config" are controls qualifiers.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: Despite name "policy_limits", these are LIMIT schemas (budget, rate,
  threshold). Controls owns limits. Policies owns rules. These are limits.
```

---

### [x] `policies/L6_drivers/policy_rules_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Pure data access for policy rules CRUD. No business logic - only
  DB operations. Tables: policy_rules, policy_rule_integrity. Extracted
  from policy_rules_service.py per Phase-2.5A.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_rules (R/W), policy_rule_integrity (R/W)
────────────────────────────────────────
Attribute: Callers
Value: policy_rules_service.py (L5 engine)
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy rules", "data access driver", "rule persistence"
────────────────────────────────────────
Attribute: Qualifier Test
Value: Driver follows its engine. Policy rules = policies domain.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Driver for policy rules table. "policy rule" in policies domain.
  Driver follows engine (policy rules engine → policies).
```

---

### [x] `policies/L6_drivers/alert_emitter.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Emits alerts for near-threshold and breach events via configured
  channels (UI notifications, Webhooks, Email, Slack). Handles alert
  throttling, channel routing, and delivery tracking.
────────────────────────────────────────
Attribute: Tables Accessed
Value: AlertConfig (R), ThresholdSignal (R/W), AlertRecord (W)
────────────────────────────────────────
Attribute: Callers
Value: L5 engines (must provide session, must own transaction boundary)
────────────────────────────────────────
Attribute: Decision Made
Value: "Should this alert be sent? Via which channels?" - throttling and
  channel routing decisions
────────────────────────────────────────
Attribute: Key Pattern
Value: "emit alerts", "threshold events", "near-threshold", "breach events",
  "alert throttling", "channel routing"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW alerts are sent?" → Alert emission is system-wide
  notification orchestration. general/L6_drivers/alert_emitter.py already
  exists with same role. alerts_facade.py is in general.
────────────────────────────────────────
Attribute: NOTE
Value: POTENTIAL DUPLICATE of general/L6_drivers/alert_emitter.py

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: Alert emission is system-wide notification orchestration (WHEN and
  HOW alerts are sent). The general domain already has alerting infrastructure:
  general/L6_drivers/alert_emitter.py, alerts_facade.py, alert_log_linker.py.
  This file appears to be a duplicate or should be consolidated into general.
```

---

### [x] `policies/L6_drivers/override_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Limit override driver (PIN-LIM-05) - DB boundary crossing. Manages
  lifecycle of temporary limit overrides: create override requests, handle
  approval workflow, expiry handling, attach justification & requester,
  emit signals to runtime evaluator, audit events.
────────────────────────────────────────
Attribute: Tables Accessed
Value: Limit (R), LimitOverride (R/W)
────────────────────────────────────────
Attribute: Callers
Value: L5 engines, api/limits/override.py
────────────────────────────────────────
Attribute: Decision Made
Value: "What is the override status? Is it expired?" - override lifecycle
────────────────────────────────────────
Attribute: Key Pattern
Value: "Limit override", "temporary limit overrides", "LimitOverride",
  "limit_overrides", "override lifecycle"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply (temporary increases)?" →
  "limit" is explicitly in controls' qualifier_phrases ("rate limit",
  "cost limit", "usage limit"). Limit overrides are controls domain.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: Limit overrides belong to controls domain. The file manages temporary
  increases to limits, which is fundamentally about WHAT limits apply — the
  core controls question. "limit" is explicitly in controls qualifiers.
```

---

### [x] `policies/L6_drivers/policy_proposal_read_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Data Access Driver
────────────────────────────────────────
Attribute: Audience
Value: INTERNAL
────────────────────────────────────────
Attribute: What It Does
Value: Read operations for policy proposal engine. Pure data access layer
  for policy proposal read operations. No business logic - only query
  execution and data retrieval. Fetches unacknowledged feedback, proposals
  by ID, and policy versions.
────────────────────────────────────────
Attribute: Tables Accessed
Value: PatternFeedback (R), PolicyProposal (R), PolicyVersion (R)
────────────────────────────────────────
Attribute: Callers
Value: L5 policy_proposal_engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy proposals", "PolicyProposal", "PolicyVersion", "pattern feedback"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior (policy proposals)?" → "policy proposal"
  maps to policies' qualifier_phrases ("policy definition", "policy proposal",
  "policy version").

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy proposals are governance rules under consideration. The file
  handles reads for policy proposals and versions, which belongs to the
  policies domain (WHAT rules govern behavior). Driver follows its engine.
```

---

### [x] `policies/L6_drivers/arbitrator.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Resolves conflicts between multiple applicable policies. Arbitration
  rules: MOST_RESTRICTIVE (smallest limit, harshest action wins),
  EXPLICIT_PRIORITY (higher precedence wins), FAIL_CLOSED (if ambiguous,
  deny/stop). Returns effective limits and actions.
────────────────────────────────────────
Attribute: Tables Accessed
Value: PolicyPrecedence (R), via PolicyRule
────────────────────────────────────────
Attribute: Callers
Value: policy/prevention_engine.py, worker/runner.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Which policy wins when conflicts occur?" - conflict resolution
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy conflicts", "PolicyPrecedence", "ArbitrationResult",
  "ConflictStrategy", "MOST_RESTRICTIVE", "EXPLICIT_PRIORITY"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior (when multiple policies conflict)?" →
  "policy" in policies' qualifier_phrases. Conflict resolution is policy
  rule governance logic.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy arbitration determines which rules win when conflicts occur.
  This is governance rule resolution — clearly policies domain (WHAT rules
  govern behavior). PolicyPrecedence, ConflictStrategy are policy concepts.
```

---

### [x] `policies/L6_drivers/recovery_matcher.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Match failure patterns and generate recovery suggestions. M10 Recovery
  Suggestion Engine - Matcher Service. Scoring algorithm with time-decay,
  embedding similarity threshold, LLM escalation threshold. Matches failure
  entries against historical patterns.
────────────────────────────────────────
Attribute: Tables Accessed
Value: FailurePattern (R), RecoverySuggestion (R), RecoveryCandidate (W)
────────────────────────────────────────
Attribute: Callers
Value: L5 engines (must provide session, must own transaction boundary)
────────────────────────────────────────
Attribute: Decision Made
Value: "What recovery suggestion applies to this failure pattern?"
────────────────────────────────────────
Attribute: Key Pattern
Value: "failure patterns", "recovery suggestions", "FailurePattern",
  "RecoverySuggestion", "pattern matching", "confidence scoring"
────────────────────────────────────────
Attribute: Qualifier Test
Value: Part of policy proposal workflow. Pattern matching leads to policy
  proposals for governance rules. Recovery suggestions become policy
  recommendations.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Recovery matcher is part of the policy proposal workflow. Failure
  pattern matching generates recovery suggestions that feed into policy
  proposals. The policy_proposal_engine imports RecoveryMatcher. Part of
  WHAT rules govern behavior (generating policy recommendations).
```

---

### [x] `policies/L6_drivers/budget_enforcement_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Data Access Driver
────────────────────────────────────────
Attribute: Audience
Value: INTERNAL
────────────────────────────────────────
Attribute: What It Does
Value: Budget enforcement data access operations. Queries halted runs without
  decision records. Pure DB operations - no business logic.
────────────────────────────────────────
Attribute: Tables Accessed
Value: runs (R), provenances (R), decision_records (R)
────────────────────────────────────────
Attribute: Callers
Value: budget_enforcement_engine.py (L5 engine)
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "budget enforcement", "halted runs", "decision records"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "budget" is EXPLICITLY
  in controls' qualifier_phrases. Budget enforcement = controls domain.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "budget" is EXPLICITLY in controls' qualifier_phrases. Budget
  enforcement is about WHAT limits apply, not WHAT rules govern behavior.
```

---

### [x] `policies/L6_drivers/capture.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Taxonomy evidence capture service. Single entry point for all governance
  taxonomy evidence writes (Classes B-J). Writes activity_evidence, policy_decisions,
  integrity_evidence. Three layers: Operational, Governance, Integrity (terminal seal).
────────────────────────────────────────
Attribute: Tables Accessed
Value: activity_evidence (W), policy_decisions (W), integrity_evidence (W)
────────────────────────────────────────
Attribute: Callers
Value: L5 engines (must provide session)
────────────────────────────────────────
Attribute: Decision Made
Value: None - thin DB writes only, no business logic
────────────────────────────────────────
Attribute: Key Pattern
Value: "evidence capture", "integrity evidence", "governance taxonomy evidence",
  "audit layer"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT immutable record exists?" → "evidence record" is in logs'
  qualifier_phrases. Evidence capture/persistence is logs domain.

ASSIGN TO: logs ⚠️ (MISPLACED)
Reason: Evidence capture/persistence. "evidence record" is in logs' qualifier_phrases.
  This file captures evidence for audit purposes - logs owns immutable evidence records.
```

---

### [x] `policies/L6_drivers/cross_domain.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Cross-Domain Governance - Mandatory data integrity functions. Implements
  mandatory governance for customer-facing paths. Analytics→Incidents (cost
  anomalies MUST create incidents), Policies↔Analytics (limit breaches MUST
  be recorded). GovernanceError must surface - never catch and ignore.
────────────────────────────────────────
Attribute: Tables Accessed
Value: Incident (R/W), PolicyBreach (W) via LimitBreach
────────────────────────────────────────
Attribute: Callers
Value: cost_anomaly_detector, budget services, worker runtime
────────────────────────────────────────
Attribute: Decision Made
Value: "Must this cross-domain action be recorded?" - enforces mandatory
  governance across domain boundaries
────────────────────────────────────────
Attribute: Key Pattern
Value: "cross-domain governance", "mandatory governance", "GovernanceError",
  "incidents created", "limit breaches recorded"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → Cross-domain orchestration
  is system-wide coordination. general handles cross-domain operations per
  HOC topology "Cross-Domain Location Rule".

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: Cross-domain orchestration coordinating policies↔analytics↔incidents.
  System-wide governance enforcement across domain boundaries. Per HOC topology,
  cross-domain items go to general.
```

---

### [x] `policies/L6_drivers/dag_executor.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: DAG-based parallel policy executor. Executes policies in topologically
  sorted order: parallel execution within stages, sequential across stages,
  governance-aware ordering, full execution trace.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policies (R), ir_modules (R)
────────────────────────────────────────
Attribute: Callers
Value: policy engine, workers
────────────────────────────────────────
Attribute: Decision Made
Value: "In what order should policies execute?" - execution orchestration
────────────────────────────────────────
Attribute: Key Pattern
Value: "parallel execution", "topologically sorted", "execution order",
  "governance-aware ordering", "DAG stages"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "execution order" is in
  general's qualifier_phrases. This is execution orchestration, not policy
  rule definition.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: "execution order" is in general's qualifier_phrases. DAG execution
  orchestration decides WHEN and HOW policies run - system orchestration,
  not WHAT rules govern behavior.
```

---

### [x] `policies/L6_drivers/governance_signal_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Governance signal persistence service. Writes from L7 (BLCA, CI, OPS),
  reads from L4/L5. Persists blocking/warning signals, supersedes previous
  signals for same scope/type. All governance influence becomes visible data.
────────────────────────────────────────
Attribute: Tables Accessed
Value: governance_signals (R/W)
────────────────────────────────────────
Attribute: Callers
Value: L7 (BLCA, CI) for writes, L4/L5 for reads
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure persistence, orchestrators check signals for decisions
────────────────────────────────────────
Attribute: Key Pattern
Value: "governance signals", "blocking/warning signals", "governance influence",
  "BLCA", "CI writes signals"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "governance enforcement" in
  general's qualifier_phrases. Governance signal infrastructure for system-wide
  blocking/warning decisions.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: "governance enforcement" in general's qualifier_phrases. Governance
  signal persistence is system-wide infrastructure used by BLCA/CI to control
  WHEN actions can execute. System orchestration infrastructure.
```

---

### [x] `policies/L6_drivers/keys_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: API Keys data access operations. Pure data access for API keys. CRUD
  operations on api_keys table, usage tracking via proxy_calls.
────────────────────────────────────────
Attribute: Tables Accessed
Value: api_keys (R/W), proxy_calls (R)
────────────────────────────────────────
Attribute: Callers
Value: keys_service.py (L5 shim), customer_keys_adapter.py (L3)
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "API keys", "api_keys table", "key persistence"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHO can call what?" → "api key" is EXPLICITLY in apis' qualifier_phrases.
  API key management is apis domain.

ASSIGN TO: apis ⚠️ (MISPLACED)
Reason: "api key" is EXPLICITLY in apis' qualifier_phrases. API key data
  access belongs to apis domain (WHO can call what), not policies.
```

---

### [x] `policies/L6_drivers/limits_read_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Data Access Driver
────────────────────────────────────────
Attribute: Audience
Value: INTERNAL
────────────────────────────────────────
Attribute: What It Does
Value: Read operations for limits. Pure data access layer for limits read
  operations. Fetches limits with filters, pagination, breach history.
────────────────────────────────────────
Attribute: Tables Accessed
Value: limits (R), limit_integrity (R), limit_breaches (R)
────────────────────────────────────────
Attribute: Callers
Value: L5 policies_limits_query_engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access driver
────────────────────────────────────────
Attribute: Key Pattern
Value: "limits", "limit_integrity", "limit_breaches", "BUDGET category"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "limit" is EXPLICITLY in
  controls' qualifier_phrases. Limits data access is controls domain.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "limit" is EXPLICITLY in controls' qualifier_phrases. Limits read
  driver belongs to controls domain, not policies.
```

---

### [x] `policies/L6_drivers/llm_threshold_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: LLM run threshold resolution and evaluation. Resolves effective params
  from Policy→Limit chain. Evaluates runs against thresholds, emits signals
  to both Founder Console (ops_events) and Customer Console (runs.risk_level).
────────────────────────────────────────
Attribute: Tables Accessed
Value: thresholds (R), runs (R), ops_events (W), run_signals (W)
────────────────────────────────────────
Attribute: Callers
Value: api/activity/*, worker/runtime/*
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this threshold exceeded?" - evaluates runs against thresholds
────────────────────────────────────────
Attribute: Key Pattern
Value: "threshold", "threshold signals", "ThresholdParams", "threshold
  evaluation", "risk_level"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "threshold config" is in
  controls' qualifier_phrases. Threshold evaluation is controls domain.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "threshold config" is in controls' qualifier_phrases. Threshold
  resolution and evaluation is about WHAT limits apply, not WHAT rules
  govern behavior. Controls owns thresholds.
```

---

### [x] `policies/L6_drivers/optimizer_conflict_resolver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy conflict resolution for PLang v2.0. Resolves conflicts: action
  conflicts, priority conflicts, category conflicts, circular dependencies.
  Uses category precedence (SAFETY > PRIVACY > OPERATIONAL > ROUTING > CUSTOM).
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_conflicts (R), policy_conflict_resolutions (W)
────────────────────────────────────────
Attribute: Callers
Value: policy/engine
────────────────────────────────────────
Attribute: Decision Made
Value: "Which policy wins in a conflict?" - policy precedence resolution
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy conflicts", "conflict resolution", "PolicyConflict", "category
  precedence", "action precedence"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Policy conflict resolution determines
  which governance rules apply. Similar to arbitrator.py (confirmed policies).

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy conflict resolution determines which governance rules win.
  This is about WHAT rules govern behavior. Similar to arbitrator.py which
  was confirmed as policies domain.
```

---

### [x] `policies/L6_drivers/orphan_recovery.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Orphan Run Recovery Service (PB-S2). Detects and marks runs orphaned
  due to system crash. On startup, detect runs stuck in "queued" or "running",
  mark them as "crashed" (factual status). PB-S2 Guarantee: Crashed runs are
  never silently lost.
────────────────────────────────────────
Attribute: Tables Accessed
Value: runs (R/W) via WorkerRun
────────────────────────────────────────
Attribute: Callers
Value: L5 workers (startup), L7 ops scripts
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this run orphaned?" - factual determination about run state
────────────────────────────────────────
Attribute: Key Pattern
Value: "orphan run recovery", "run state", "runs stuck", "crashed status"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT LLM run occurred?" → "run lifecycle", "run state" are in
  activity's qualifier_phrases. This is about run state management.

ASSIGN TO: activity ⚠️ (MISPLACED)
Reason: "run lifecycle", "run state" are in activity's qualifier_phrases.
  Orphan recovery manages run lifecycle states (crashed, running, queued).
  This is about WHAT happened to runs, not policy rules.
```

---

### [x] `policies/L6_drivers/policy_engine_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy engine data access operations. Core policy engine data access:
  policy activation, policy rule lookup, policy evaluation context. Reads
  policies, policy_rules, policy_versions tables.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policies (R/W), policy_rules (R), policy_versions (R)
────────────────────────────────────────
Attribute: Callers
Value: policy_engine.py (L5), policy evaluation services
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access for policy engine business logic
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy engine", "policy activation", "policy rules", "policy versions"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Core policy engine data layer.
  "policy rule", "policy evaluation" in policies' qualifier_phrases.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Core policy engine data access. Supports policy rule lookup and
  evaluation - directly serves "WHAT rules govern behavior" question.
```

---

### [x] `policies/L6_drivers/policy_graph_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy graph and conflict detection data access. Builds policy
  dependency graphs, detects policy conflicts, validates policy relationships.
  Supports policy_graph_engine for conflict resolution.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policies (R), policy_dependencies (R), policy_conflicts (R/W)
────────────────────────────────────────
Attribute: Callers
Value: policy_graph_engine.py (L5), conflict resolver
────────────────────────────────────────
Attribute: Decision Made
Value: None - data access for graph traversal and conflict lookup
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy graph", "policy dependencies", "policy conflicts", "conflict
  detection"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Policy graph relationships determine
  how rules interact. Part of policy evaluation infrastructure.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy graph and conflict detection data access. Supports policy
  rule relationships and conflict detection - core to "WHAT rules govern
  behavior" domain question.
```

---

### [x] `policies/L6_drivers/policy_limits_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy limits data access operations. CRUD for limits attached to
  policies: budget limits, rate limits, token limits. Links limits to
  policy rules via policy_limit_attachments table.
────────────────────────────────────────
Attribute: Tables Accessed
Value: limits (R/W), policy_limit_attachments (R/W), limit_breaches (R)
────────────────────────────────────────
Attribute: Callers
Value: policy_limits_engine.py (L5), limits management UI
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access for limits CRUD
────────────────────────────────────────
Attribute: Key Pattern
Value: "limits", "policy limits", "budget limits", "rate limits", "token
  limits", "limit attachments"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "limit" is EXPLICITLY in
  controls' qualifier_phrases. Despite the name "policy_limits", this file
  manages limits data, not policy rules.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "limit" is EXPLICITLY in controls' qualifier_phrases. This driver
  manages limit data (budget/rate/token limits). The decision is "WHAT
  limits apply", not "WHAT rules govern behavior". Controls domain owns
  limits, even when attached to policies.
```

---

### [x] `policies/L6_drivers/policy_proposal_write_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy proposal write operations. Creates, updates, approves/rejects
  policy proposals. Manages proposal lifecycle state transitions. Persists
  proposal versions and approval history.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_proposals (W), proposal_versions (W), proposal_approvals (W)
────────────────────────────────────────
Attribute: Callers
Value: policy_proposal_engine.py (L5), proposal workflow API
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data persistence for proposal workflow
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy proposal", "proposal lifecycle", "proposal approval",
  "proposal state"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "policy proposal" is EXPLICITLY in
  policies' qualifier_phrases. Proposal workflow is how new rules are
  introduced to the system.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: "policy proposal" is EXPLICITLY in policies' qualifier_phrases.
  Policy proposal persistence is core to how governance rules are introduced
  and approved - directly serves policies domain.
```

---

### [x] `policies/L6_drivers/policy_read_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy read operations. Fetches policies by tenant, project, status.
  Retrieves policy rules, versions, and configuration. Supports policy
  listing and detail views for customer console.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policies (R), policy_rules (R), policy_versions (R), policy_configs (R)
────────────────────────────────────────
Attribute: Callers
Value: policy_read_engine.py (L5), customer console API
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure read-only data access
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy read", "policy listing", "customer policy settings",
  "policy configuration"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Policy read operations for customer
  policy viewing. Core policy domain data access.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy read operations for customer policy viewing. Directly serves
  the policies domain question "WHAT rules govern behavior" by providing
  access to policy rules and configurations.
```

---

### [x] `policies/L6_drivers/policy_rules_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Data access for policy rules CRUD operations. Reads/writes policy_rules
  and policy_rule_integrity tables. Pure data access - no business logic.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_rules (R/W), policy_rule_integrity (R/W)
────────────────────────────────────────
Attribute: Callers
Value: policy_rules_service.py (L5 engine)
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data access for policy rules persistence
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy rules", "policy_rules table", "rule CRUD"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "policy rule" is in policies'
  qualifier_phrases. Policy rules data access is core policies domain.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy rules CRUD operations. "policy rule" is in policies'
  qualifier_phrases. Data access for governance rules persistence.
```

---

### [x] `policies/L6_drivers/policy_rules_read_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Data Access Driver
────────────────────────────────────────
Attribute: Audience
Value: INTERNAL
────────────────────────────────────────
Attribute: What It Does
Value: Read operations for policy rules. Fetches policy rules with filters
  and pagination. Queries policy_rules, policy_rule_integrity, and
  policy_enforcements tables.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_rules (R), policy_rule_integrity (R), policy_enforcements (R)
────────────────────────────────────────
Attribute: Callers
Value: L5 policies_rules_query_engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure read-only data access
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy rules", "rule enforcement", "rule listing"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Policy rule read operations.
  Core policies domain data access.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy rules read operations. Supports listing and filtering
  governance rules - directly serves policies domain question.
```

---

### [x] `policies/L6_drivers/proposals_read_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Data Access Driver
────────────────────────────────────────
Attribute: Audience
Value: INTERNAL
────────────────────────────────────────
Attribute: What It Does
Value: Read operations for policy proposals (list view). Fetches proposals
  for the "Proposals" tab in policies domain. Separate from lifecycle
  operations in policy_proposal_read_driver.py.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_proposals (R)
────────────────────────────────────────
Attribute: Callers
Value: L5 policies_proposals_query_engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure read-only data access for proposal listing
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy proposals", "proposal listing", "draft proposals"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "policy proposal" is EXPLICITLY in
  policies' qualifier_phrases. Proposal listing is core policies domain.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: "policy proposal" is EXPLICITLY in policies' qualifier_phrases.
  Policy proposal listing supports the governance rule introduction workflow.
```

---

### [x] `policies/L6_drivers/recovery_write_driver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: DB write driver for Recovery APIs. Writes recovery_patterns and
  recovery_suggestions tables. UPSERT operations for failure pattern
  recording. Part of recovery→policy proposal workflow.
────────────────────────────────────────
Attribute: Tables Accessed
Value: recovery_patterns (R/W), recovery_suggestions (W)
────────────────────────────────────────
Attribute: Callers
Value: L5 engines, api/recovery_ingest.py, api/recovery.py
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure data persistence for recovery patterns
────────────────────────────────────────
Attribute: Key Pattern
Value: "recovery patterns", "recovery suggestions", "failure patterns"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Part of recovery→policy proposal
  workflow. Similar to recovery_matcher.py (confirmed policies). Recovery
  suggestions feed into policy recommendations.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Part of the recovery→policy proposal workflow. Recovery suggestions
  become policy recommendations. Consistent with recovery_matcher.py
  classification (confirmed policies in Batch 20).
```

---

### [x] `policies/L6_drivers/scope_resolver.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Resolves which policies apply to a given run context. Resolution
  based on: Tenant ID, Agent ID, API Key ID, Human Actor ID. Result
  frozen into policy snapshot for audit.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policy_scopes (R)
────────────────────────────────────────
Attribute: Callers
Value: policy/prevention_engine.py, worker/runner.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Which policies apply to this run?" - policy applicability resolution
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy scopes", "scope resolution", "policy applicability"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Determines which policy rules apply
  to a run. Policy scoping is core to policy evaluation.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Resolves which governance rules apply to a given context. Core
  policy infrastructure - determines "WHAT rules govern behavior" for
  each run.
```

---

### [x] `policies/L6_drivers/symbol_table.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy symbol table management for PLang v2.0 compilation. In-memory
  symbol table with hierarchical scoping (global, policy, rule, block).
  Category-aware symbol lookup. No DB access.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (in-memory symbol table)
────────────────────────────────────────
Attribute: Callers
Value: policy/ir/ir_builder
────────────────────────────────────────
Attribute: Decision Made
Value: None - symbol management for compilation
────────────────────────────────────────
Attribute: Key Pattern
Value: "symbol table", "PLang compilation", "policy symbols"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Part of policy language infrastructure.
  Symbol management for compiling policy rules into IR.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy language/compilation infrastructure. Symbol table supports
  policy rule definition and compilation - core to "WHAT rules govern behavior".
```

---

### [x] `policies/L5_engines/ast.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy DSL AST node definitions. Immutable, typed data structures
  defining policy structure: Scope (ORG, PROJECT), Mode (MONITOR, ENFORCE),
  actions, conditions. No runtime evaluation, serializable to JSON.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure data structures)
────────────────────────────────────────
Attribute: Callers
Value: policy/compiler, policy/engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - defines the MEANING of policy structure
────────────────────────────────────────
Attribute: Key Pattern
Value: "AST", "policy DSL", "policy structure", "enforcement semantics"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Defines the structure of policy rules.
  Core policy language infrastructure.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy DSL AST definitions. Defines what policy rules mean and
  how they're structured - foundational to "WHAT rules govern behavior".
```

---

### [x] `policies/L5_engines/audit_engine.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L8 — Catalyst / Verification
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Governance Audit Engine - verifies job execution against contract intent.
  Evidence consumer, verdict producer (PASS/FAIL/INCONCLUSIVE). Deterministic
  verification. Terminal verdicts cannot be overridden.
────────────────────────────────────────
Attribute: Tables Accessed
Value: Reads frozen evidence only
────────────────────────────────────────
Attribute: Callers
Value: GovernanceOrchestrator (via AuditTrigger)
────────────────────────────────────────
Attribute: Decision Made
Value: "Did execution match contract intent?" - produces verdicts
────────────────────────────────────────
Attribute: Key Pattern
Value: "audit", "evidence consumer", "verdict producer", "governance audit",
  "PASS/FAIL", "immutable verdicts"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT immutable record exists?" → "audit" is EXPLICITLY in logs'
  qualifier_phrases. This is evidence consumption and verdict production -
  creating immutable audit records.

ASSIGN TO: logs ⚠️ (MISPLACED)
Reason: "audit" is EXPLICITLY in logs' qualifier_phrases. This engine
  consumes evidence and produces verdicts - audit records. Despite being
  in policies folder, it answers "WHAT immutable record exists" not
  "WHAT rules govern behavior".
```

---

### [x] `policies/L5_engines/audit_evidence.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Emit compliance-grade audit for MCP tool calls. Records policy
  decisions for compliance. Tamper-evident audit trail. Captures input/output
  for forensic analysis. Redacts sensitive data.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (emits audit_evidence events via driver)
────────────────────────────────────────
Attribute: Callers
Value: Runner, skill executor
────────────────────────────────────────
Attribute: Decision Made
Value: None - emits audit events for compliance
────────────────────────────────────────
Attribute: Key Pattern
Value: "audit evidence", "compliance audit", "tamper-evident", "forensic
  analysis", "audit trail"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT immutable record exists?" → "audit trail", "evidence record"
  are in logs' qualifier_phrases. This emits audit evidence for compliance.

ASSIGN TO: logs ⚠️ (MISPLACED)
Reason: "audit trail", "evidence record" are in logs' qualifier_phrases.
  This engine emits compliance audit evidence - creating immutable records
  for forensic analysis. Logs domain owns audit/evidence.
```

---

### [x] `policies/L5_engines/authority_checker.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Check override authority status for prevention engine. If an override
  is active for a policy, enforcement is skipped. Returns OverrideStatus
  (NO_OVERRIDE, OVERRIDE_ACTIVE, OVERRIDE_EXPIRED, OVERRIDE_NOT_ALLOWED).
────────────────────────────────────────
Attribute: Tables Accessed
Value: overrides (R) via driver
────────────────────────────────────────
Attribute: Callers
Value: policy/prevention_engine.py, services/enforcement/
────────────────────────────────────────
Attribute: Decision Made
Value: "Should policy enforcement be skipped?" - determines if override blocks enforcement
────────────────────────────────────────
Attribute: Key Pattern
Value: "override authority", "override check", "skip enforcement", "policy enforcement"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Part of policy enforcement workflow.
  Determines whether a policy rule should be enforced based on override status.
  This is policy execution control, not limit configuration.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Part of policy enforcement workflow. Decides whether governance
  rules should be enforced. While it reads overrides, the decision is
  "should this policy be applied" - core to "WHAT rules govern behavior".
```

---

### [x] `policies/L5_engines/billing_provider.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Phase-6 BillingProvider protocol and MockBillingProvider. Gets billing
  state for tenant, returns plan and limits. Hardcoded mock for testing,
  interface-compatible with future real provider (Stripe).
────────────────────────────────────────
Attribute: Tables Accessed
Value: None
────────────────────────────────────────
Attribute: Callers
Value: billing middleware, billing APIs, runtime enforcement
────────────────────────────────────────
Attribute: Decision Made
Value: "What is the tenant's billing state/plan?" - determines billing context
────────────────────────────────────────
Attribute: Key Pattern
Value: "billing", "BillingState", "Plan", "subscription", "billing provider"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHO owns what?" → "billing", "subscription" are in account's
  qualifier_phrases. Billing/subscription management is account domain.

ASSIGN TO: account ⚠️ (MISPLACED)
Reason: "billing", "subscription" are in account's qualifier_phrases.
  Billing provider determines tenant billing state - this is account
  domain responsibility (WHO owns what subscription/plan).
```

---

### [x] `policies/L5_engines/binding_moment_enforcer.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Enforce binding moments - when policies are evaluated. RUN_START,
  STEP_START, STEP_END, ON_CHANGE. If bind_at=RUN_START, prevents
  re-evaluation mid-run.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policies (R) via driver
────────────────────────────────────────
Attribute: Callers
Value: prevention_engine.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Should this policy be evaluated now?" - timing of policy evaluation
────────────────────────────────────────
Attribute: Key Pattern
Value: "binding moment", "policy evaluation", "RUN_START", "STEP_START"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Binding moments define WHEN policy
  rules are evaluated. Part of policy enforcement workflow.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Part of policy evaluation workflow. Determines when governance
  rules are applied - core to "WHAT rules govern behavior" timing.
```

---

### [x] `policies/L5_engines/budget_enforcement_engine.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L4 — Domain Engine (System Truth)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Budget enforcement decision-making. Identifies runs halted due to
  budget enforcement. Emits budget_enforcement decision records. Processes
  halted runs from L6 driver.
────────────────────────────────────────
Attribute: Tables Accessed
Value: runs (R), decision_records (W) via driver
────────────────────────────────────────
Attribute: Callers
Value: Background tasks, API endpoints
────────────────────────────────────────
Attribute: Decision Made
Value: "Was this run halted for budget reasons?" - budget enforcement decisions
────────────────────────────────────────
Attribute: Key Pattern
Value: "budget enforcement", "budget exhausted", "budget_enforcement decision"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "budget" is EXPLICITLY in
  controls' qualifier_phrases. Budget enforcement is about limit enforcement.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "budget" is EXPLICITLY in controls' qualifier_phrases. Budget
  enforcement determines "WHAT limits apply" and whether those limits
  caused a run halt. Controls domain owns budget enforcement.
```

---

### [x] `policies/L5_engines/certificate.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L3 — Boundary Adapter
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Cryptographic evidence of deterministic replay. Creates HMAC-signed
  certificates proving: policy decisions were evaluated at a time, replay
  validation passed, no tampering occurred. Types: REPLAY_PROOF, POLICY_AUDIT,
  INCIDENT_EXPORT.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (uses M4 HMAC infrastructure)
────────────────────────────────────────
Attribute: Callers
Value: guard.py (replay endpoint)
────────────────────────────────────────
Attribute: Decision Made
Value: None - creates cryptographic proof of events
────────────────────────────────────────
Attribute: Key Pattern
Value: "certificate", "cryptographic evidence", "HMAC signature", "proof",
  "replay proof", "policy audit"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT immutable record exists?" → "proof", "evidence record" are
  in logs' qualifier_phrases. Certificates are cryptographic proof records.

ASSIGN TO: logs ⚠️ (MISPLACED)
Reason: "proof", "evidence record" are in logs' qualifier_phrases.
  Certificates create tamper-proof evidence of system behavior - this
  is immutable audit record creation. Logs domain owns proof/evidence.
```

---

### [x] `policies/L5_engines/claim_decision_engine.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L4 — Domain Engine (System Truth)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Recovery claim decisions. Determines claim eligibility based on
  confidence thresholds. Defines what "unevaluated" means in claim processing.
  Status determination: how evaluation results map to status.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (reads from environment)
────────────────────────────────────────
Attribute: Callers
Value: L4 services
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this candidate eligible for claiming?" - claim eligibility rules
────────────────────────────────────────
Attribute: Key Pattern
Value: "recovery claim", "claim eligibility", "claim decision", "confidence
  threshold"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Part of recovery→policy proposal
  workflow. Claim decisions lead to policy proposals. Similar to
  recovery_matcher.py (confirmed policies).

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Part of recovery→policy proposal workflow. Claim decisions
  determine what failures get processed for policy learning. Consistent
  with recovery_matcher.py and recovery_write_driver.py classifications.
```

---

### [x] `policies/L5_engines/compiler_parser.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy language parser for PLang v2.0. Produces AST from tokens.
  Supports policy declarations with categories, rule declarations with
  priorities, condition/action blocks, expression evaluation.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure parsing)
────────────────────────────────────────
Attribute: Callers
Value: policy/engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - syntax analysis producing AST
────────────────────────────────────────
Attribute: Key Pattern
Value: "parser", "PLang", "AST", "policy declarations", "rule declarations"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Policy language infrastructure.
  Parser produces AST for policy rule compilation.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Policy language parser. Produces AST for policy rules - core
  infrastructure for "WHAT rules govern behavior".
```

---

### [x] `policies/L5_engines/constraint_checker.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Enforce MonitorConfig inspection constraints before logging. Checks:
  allow_prompt_logging, allow_response_logging, allow_pii_capture,
  allow_secret_access. "Negative capabilities" - what is NOT allowed.
────────────────────────────────────────
Attribute: Tables Accessed
Value: monitor_config (R) via driver
────────────────────────────────────────
Attribute: Callers
Value: worker/runtime/trace_collector.py, services/logging_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this inspection operation allowed?" - constraint enforcement
────────────────────────────────────────
Attribute: Key Pattern
Value: "inspection constraints", "MonitorConfig", "allow_prompt_logging",
  "negative capabilities", "constraint violation"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → Enforces constraints BEFORE
  logging operations execute. "governance enforcement" in general qualifiers.
  Runtime enforcement of WHEN operations can happen.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: "governance enforcement" in general's qualifier_phrases. Enforces
  constraints before operations execute - runtime enforcement of WHEN
  actions can happen. Belongs in general/L5_engines/lifecycle/.
```

---

### [x] `policies/L5_engines/content_accuracy.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy content accuracy validation. Prevents AI from making definitive
  assertions about data that is missing or NULL. Detects assertion types:
  DEFINITIVE, CONDITIONAL, UNCERTAIN, HEDGED.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure validation logic)
────────────────────────────────────────
Attribute: Callers
Value: policy/engine
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this AI assertion valid given available data?" - content validation
────────────────────────────────────────
Attribute: Key Pattern
Value: "content accuracy", "assertion validation", "CONTENT_ACCURACY policy"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Validates AI output against policy
  rules about content accuracy. Part of policy enforcement.

ASSIGN TO: policies ✓ (CONFIRMED)
Reason: Content accuracy validation enforces policy rules about what
  AI can assert. Part of "WHAT rules govern behavior" enforcement.
```

---

### [x] `policies/L5_engines/contract_engine.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Contract Engine - stateful contract state machine. Creates contracts
  from validated proposals, enforces state transitions, records history.
  States: DRAFT → APPROVED → ACTIVE → COMPLETED/CANCELLED.
────────────────────────────────────────
Attribute: Tables Accessed
Value: contracts (R/W) via driver
────────────────────────────────────────
Attribute: Callers
Value: L3 (adapters), L4 (orchestrators)
────────────────────────────────────────
Attribute: Decision Made
Value: "What is the contract state?" - manages governance contract lifecycle
────────────────────────────────────────
Attribute: Key Pattern
Value: "contract", "state machine", "lifecycle", "state transitions"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "job state" in general's
  qualifier_phrases. State machine managing contract LIFECYCLE - orchestration
  concern, not rule definition.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: "job state" in general's qualifier_phrases. Contract state machine
  manages LIFECYCLE of governance contracts (DRAFT → ACTIVE). Lifecycle
  management is general domain. Belongs in general/L5_engines/lifecycle/.
```

---

### [x] `policies/L5_engines/control_registry.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: SOC2 Trust Service Criteria control registry. Defines compliance
  controls: CC (Security), A (Availability), PI (Processing Integrity),
  C (Confidentiality), P (Privacy). Used for compliance mapping.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (registry definition)
────────────────────────────────────────
Attribute: Callers
Value: services/soc2/mapper.py, services/export_bundle_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: None - defines compliance control definitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "SOC2", "Trust Service Criteria", "compliance controls", "CC7.x",
  "audit", "compliance status"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT immutable record exists?" → "audit", "completeness" are in
  logs' qualifier_phrases. SOC2 controls are audit/compliance infrastructure.

ASSIGN TO: logs ⚠️ (MISPLACED)
Reason: SOC2 compliance control registry is audit/compliance infrastructure.
  "audit" is in logs' qualifier_phrases. Logs domain owns compliance
  mapping infrastructure.
```

---

### [x] `policies/L5_engines/controls_facade.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Controls Facade - Centralized access to control operations. Manages
  ControlType enum (killswitch, circuit_breaker, feature_flag, throttle,
  maintenance), ControlState enum, ControlConfig. Provides unified access
  to system controls.
────────────────────────────────────────
Attribute: Tables Accessed
Value: controls (via driver)
────────────────────────────────────────
Attribute: Callers
Value: L2 controls.py API, SDK
────────────────────────────────────────
Attribute: Decision Made
Value: "What controls are available?" - manages killswitches, circuit breakers
────────────────────────────────────────
Attribute: Key Pattern
Value: "killswitch", "circuit breaker", "feature flag", "throttle"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "killswitch", "circuit breaker",
  "feature flag", "throttle" are ALL in controls' qualifier_phrases.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: Manages killswitches, circuit breakers, feature flags, throttles - all
  control mechanisms. Belongs in controls/L5_engines/.
```

---

### [x] `policies/L5_engines/cus_enforcement_service.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Customer enforcement service - Enforcement policy evaluation for
  customer LLM integrations. Re-exports CusEnforcementEngine with HOC aliases.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (re-export wrapper)
────────────────────────────────────────
Attribute: Callers
Value: cus_enforcement.py API endpoints
────────────────────────────────────────
Attribute: Decision Made
Value: Evaluates customer-defined enforcement policies for LLM integrations
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy enforcement", "policy evaluation", "customer rule"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "policy enforcement", "policy evaluation"
  are in policies' qualifier_phrases.

ASSIGN TO: policies ✓ (CONFIRMED CORRECT)
Reason: Evaluates customer-defined policy rules for LLM integrations.
```

---

### [x] `policies/L5_engines/customer_policy_read_engine.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Customer policy domain read operations with business logic. Calculates
  period bounds, budget remaining/percentage, assembles customer-safe DTOs,
  provides rate limit defaults.
────────────────────────────────────────
Attribute: Tables Accessed
Value: policies, budgets (via driver)
────────────────────────────────────────
Attribute: Callers
Value: customer_policies_adapter.py (L3)
────────────────────────────────────────
Attribute: Decision Made
Value: "What policies exist and what's their budget status?" - reads policy data
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy domain read", "customer policy", "budget constraint display"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Reads customer policy data and budget info.
  Policy domain owns policy read operations.

ASSIGN TO: policies ✓ (CONFIRMED CORRECT)
Reason: Reads policy data and calculates policy-related budgets for customer view.
```

---

### [x] `policies/L5_engines/dag_sorter.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Policy DAG topological sorting (pure algorithm). Provides deterministic
  execution ordering for PLang v2.0. Features: topological sort for dependency-
  respecting execution, category-aware ordering (SAFETY first), priority-based
  tie breaking.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure algorithm)
────────────────────────────────────────
Attribute: Callers
Value: policy/optimizer
────────────────────────────────────────
Attribute: Decision Made
Value: "What is the execution order?" - determines WHEN policies execute
────────────────────────────────────────
Attribute: Key Pattern
Value: "execution ordering", "deterministic execution plan", "ExecutionPhase"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "execution order" is in general's
  qualifier_phrases. This determines the ORDER of policy execution - that's
  orchestration/lifecycle (WHEN), not policy definition (WHAT).

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: Determines execution ORDER of policies - orchestration concern. Belongs
  in general/L5_engines/lifecycle/.
```

---

### [x] `policies/L5_engines/decisions.py`

```
Attribute: Current Domain
Value: policies
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Phase-7 Abuse Protection Decision Types. Defines Decision enum: ALLOW,
  THROTTLE, REJECT, WARN. For AbuseProtectionProvider, protection middleware.
  "Abuse protection constrains behavior, not identity."
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (type definitions)
────────────────────────────────────────
Attribute: Callers
Value: AbuseProtectionProvider, protection middleware
────────────────────────────────────────
Attribute: Decision Made
Value: "What protection decision to apply?" - ALLOW, THROTTLE, REJECT, WARN
────────────────────────────────────────
Attribute: Key Pattern
Value: "throttle", "rate", "abuse protection", "limit enforcement"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "throttle" is in controls'
  qualifier_phrases. Abuse protection decisions (throttle, reject) are
  enforcement of limits.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: Abuse protection decisions (throttle, reject) are enforcement of limits.
  Belongs in controls/L5_engines/.
```

---

## general (28 files)

### [x] `general/L4_runtime/engines/constraint_checker.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Enforce MonitorConfig inspection constraints before logging (pure business
  logic). Inspection constraints are "negative capabilities" - defines what policy
  is NOT allowed to inspect or capture. Checks: allow_prompt_logging,
  allow_response_logging, allow_pii_capture, allow_secret_access.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (in-memory logic)
────────────────────────────────────────
Attribute: Callers
Value: worker/runtime/trace_collector.py, services/logging_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this inspection allowed?" - runtime enforcement of constraints
────────────────────────────────────────
Attribute: Key Pattern
Value: "governance enforcement", "constraint enforcement", "before logging"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "governance enforcement" is in
  general's qualifier_phrases. Runtime enforcement of constraints before
  logging operations.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Runtime enforcement of inspection constraints. Governance enforcement
  that controls WHEN/HOW logging operations proceed.
```

---

### [x] `general/L4_runtime/engines/phase_status_invariants.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Phase-status invariant enforcement from GovernanceConfig (pure business
  logic). Enforces phase-status invariants like EXECUTING→running,
  COMPLETED→succeeded. When enforcement enabled, invalid combinations raise
  PhaseStatusInvariantEnforcementError.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (in-memory logic)
────────────────────────────────────────
Attribute: Callers
Value: ROK, worker runtime
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this phase-status combination valid?" - invariant enforcement
────────────────────────────────────────
Attribute: Key Pattern
Value: "governance enforcement", "invariant enforcement", "phase-status"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "governance enforcement" is in
  general's qualifier_phrases. Governance invariant enforcement ensures valid
  state transitions.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Governance invariant enforcement - ensures valid state transitions
  during execution lifecycle.
```

---

### [x] `general/L5_controls/engines/guard_write_engine.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Guard write operations (L5 engine delegating to L6 driver). For Guard API -
  handles KillSwitch operations AND Incident operations. Works with KillSwitchState,
  Incident, IncidentEvent.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 driver (KillSwitchState, Incident, IncidentEvent)
────────────────────────────────────────
Attribute: Callers
Value: api/guard.py
────────────────────────────────────────
Attribute: Decision Made
Value: Cross-domain operations: killswitch (controls) + incidents
────────────────────────────────────────
Attribute: Key Pattern
Value: "KillSwitch", "Incident", cross-domain
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain rule: "Cross-domain items go to general". This engine handles
  both killswitch (controls domain) and incidents (incidents domain).

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain engine (killswitch=controls, Incident=incidents). Per HOC
  Cross-Domain Location Rule, cross-domain items stay in general.
```

---

### [x] `general/L5_engines/alerts_facade.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Adapter (Facade)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Alerts Facade - Thin translation layer for alert operations. Manages alert
  rules, alert history, alert routing. Provides API: create/list/update/delete
  alert rules, alert history, alert routes. AlertSeverity, AlertStatus enums.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 drivers
────────────────────────────────────────
Attribute: Callers
Value: L2 alerts.py API, SDK, Worker
────────────────────────────────────────
Attribute: Decision Made
Value: Coordination facade - controls domain IMPORTS from this
────────────────────────────────────────
Attribute: Key Pattern
Value: "facade", "thin translation layer", cross-domain coordination
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain coordination facade. Controls domain would IMPORT FROM this
  facade. Alerts are consumed by multiple domains (controls for thresholds,
  incidents for alert events). Per HOC Cross-Domain Location Rule, cross-domain
  coordination stays in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain coordination facade. Controls domain imports from this, but
  the facade itself is system-wide orchestration. Per cross-domain rule, stays
  in general.
```

---

### [x] `general/L5_engines/compliance_facade.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Adapter (Facade)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Compliance Facade - Thin translation layer for compliance operations.
  Provides compliance verification, compliance reports, compliance rules.
  ComplianceScope: ALL, DATA, POLICY, COST, SECURITY. ComplianceStatus:
  COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT, UNKNOWN.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 drivers
────────────────────────────────────────
Attribute: Callers
Value: L2 compliance.py API, SDK
────────────────────────────────────────
Attribute: Decision Made
Value: Coordination facade - logs domain IMPORTS from this
────────────────────────────────────────
Attribute: Key Pattern
Value: "facade", "thin translation layer", cross-domain coordination
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain coordination facade. Logs domain would IMPORT FROM this
  facade. Compliance verification serves multiple domains (audit for logs,
  policy checks, etc.). Per HOC Cross-Domain Location Rule, cross-domain
  coordination stays in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain coordination facade. Logs domain imports from this, but
  the facade itself is system-wide orchestration. Per cross-domain rule, stays
  in general.
```

---

### [x] `general/L5_engines/concurrent_runs.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Concurrent run limit enforcement (Redis-backed). Limits concurrent runs
  per agent/tenant using Redis semaphore. Uses Lua script for atomic acquire.
  ConcurrentRunsLimiter class with slot timeout and fail_open option.
────────────────────────────────────────
Attribute: Tables Accessed
Value: Redis (semaphore state)
────────────────────────────────────────
Attribute: Callers
Value: API routes
────────────────────────────────────────
Attribute: Decision Made
Value: "Can this run proceed?" - enforces concurrent run limits
────────────────────────────────────────
Attribute: Key Pattern
Value: "run limit", "concurrent", cross-domain (controls limit on activity runs)
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain: "rate limit" (controls) applied to "run" (activity). Enforces
  limits (controls domain concern) on runs (activity domain concern). Per HOC
  Cross-Domain Location Rule, cross-domain items stay in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain coordination: enforces limits (controls) on runs (activity).
  Per HOC cross-domain rule, stays in general.
```

---

### [x] `general/L5_engines/control_registry.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: SOC2 Trust Service Criteria control registry (pure business logic). Defines
  SOC2 categories: Common Criteria (CC), Availability (A), Processing Integrity (PI),
  Confidentiality (C), Privacy (P). SOC2ComplianceStatus enum for compliance states.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (static registry)
────────────────────────────────────────
Attribute: Callers
Value: services/soc2/mapper.py, services/export_bundle_service.py
────────────────────────────────────────
Attribute: Decision Made
Value: "What SOC2 controls exist?" - defines compliance control registry
────────────────────────────────────────
Attribute: Key Pattern
Value: "SOC2", "compliance", cross-domain registry
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain: Shared SOC2 compliance registry used by multiple services
  (soc2/mapper.py, export_bundle_service.py). Cross-domain infrastructure stays
  in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Shared SOC2 compliance registry used by multiple services. Cross-domain
  infrastructure stays in general.
```

---

### [x] `general/L5_engines/cus_health_shim.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine (DEPRECATED SHIM)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: DEPRECATED SHIM - Redirect to drivers/cus_health_driver.py. Re-exports
  CusHealthDriver with deprecation warning for backward compatibility.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (redirect only)
────────────────────────────────────────
Attribute: Callers
Value: Legacy imports
────────────────────────────────────────
Attribute: Decision Made
Value: None - just a redirect
────────────────────────────────────────
Attribute: Key Pattern
Value: "DEPRECATED", "shim", "redirect"
────────────────────────────────────────
Attribute: Qualifier Test
Value: N/A - backward-compatibility redirect only. No actual business logic.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Deprecated shim providing backward compatibility. No actual business
  logic - just redirect.
```

---

### [x] `general/L5_engines/guard.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine (Schema)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Guard contract DTOs for access control (Pydantic schemas). GuardStatusDTO
  with status (protected/attention_needed/action_required), is_frozen (killswitch),
  incidents_blocked_24h, active_guardrails, last_incident_time.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (Pydantic schemas)
────────────────────────────────────────
Attribute: Callers
Value: API routes, engines
────────────────────────────────────────
Attribute: Decision Made
Value: None - schema definitions for Guard API
────────────────────────────────────────
Attribute: Key Pattern
Value: "guard", "killswitch", "incidents", cross-domain schema
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain schema: killswitch (controls) + incidents (incidents). Guard
  API schemas span controls (is_frozen = killswitch) and incidents (incidents_blocked).
  Cross-domain schemas stay in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Guard API schemas span controls (killswitch) and incidents. Cross-domain
  schemas stay in general.
```

---

### [x] `general/L5_engines/input_sanitizer.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine (Utility)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Input sanitization for security (pure regex validation and URL parsing).
  Detects prompt injection attempts, dangerous SQL, bypass attempts, role hijack,
  recursive plan attacks, code execution attempts. Applies to ALL user input.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure computation)
────────────────────────────────────────
Attribute: Callers
Value: API routes
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this input safe?" - security validation
────────────────────────────────────────
Attribute: Key Pattern
Value: "security", "sanitization", system-wide utility
────────────────────────────────────────
Attribute: Qualifier Test
Value: System-wide: Applies to all domains. Input sanitization is security
  infrastructure that protects the entire system, not domain-specific.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide security utility for input sanitization. Not domain-specific
  - belongs in general.
```

---

### [x] `general/L5_engines/knowledge_sdk.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: GAP-083-085 Knowledge SDK Façade (thin wrapper over KnowledgeLifecycleManager).
  SDK interface for knowledge plane lifecycle. Design invariants: SDK requests
  transitions, LifecycleManager DECIDES, Policy + state machine ARBITRATE.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 drivers (delegated)
────────────────────────────────────────
Attribute: Callers
Value: External SDK consumers, API endpoints
────────────────────────────────────────
Attribute: Decision Made
Value: Coordinates lifecycle transitions - requests, doesn't decide
────────────────────────────────────────
Attribute: Key Pattern
Value: "lifecycle", "orchestrator", "state machine", transitions
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → Lifecycle orchestration facade
  coordinating knowledge plane transitions. Orchestration stays in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Thin facade coordinating knowledge plane lifecycle transitions.
  Orchestration stays in general.
```

---

### [x] `general/L5_engines/lifecycle_facade.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Adapter (Facade)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Lifecycle Facade - Thin translation layer for lifecycle operations.
  Agent lifecycle (create/start/stop/terminate), Run lifecycle (pause/resume/cancel).
  AgentState enum, RunState enum.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 drivers
────────────────────────────────────────
Attribute: Callers
Value: L2 lifecycle.py API, SDK
────────────────────────────────────────
Attribute: Decision Made
Value: Coordinates agent and run lifecycle state transitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "lifecycle", "state transitions", "agent", "run"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "workflow orchestrat", "job state",
  "execution coordinator" are in general's qualifier_phrases.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Core lifecycle orchestration for agents and runs. Clearly general domain.
```

---

### [x] `general/L5_engines/monitors_facade.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Adapter (Facade)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Monitors Facade - Thin translation layer for monitoring operations.
  Health monitoring: create/list/get/update/delete monitors, run health checks.
  MonitorType (HTTP, TCP, DNS, HEARTBEAT, CUSTOM), MonitorStatus.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 drivers
────────────────────────────────────────
Attribute: Callers
Value: L2 monitors.py API, SDK, Scheduler
────────────────────────────────────────
Attribute: Decision Made
Value: Coordinates health monitoring operations
────────────────────────────────────────
Attribute: Key Pattern
Value: "facade", "health monitoring", cross-domain coordination
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain: System-wide health monitoring facade serving multiple domains.
  Health monitoring is infrastructure used across the system.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide health monitoring facade serving multiple domains. Cross-domain
  coordination stays in general.
```

---

### [x] `general/L5_engines/panel_invariant_monitor.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Monitor panel invariants and detect silent governance failures (in-memory logic).
  AlertType: EMPTY_PANEL, STALE_PANEL, FILTER_BREAK. AlertSeverity: INFO, WARNING,
  CRITICAL. Prevents silent governance failures by monitoring panel-backing queries.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (in-memory logic)
────────────────────────────────────────
Attribute: Callers
Value: main.py (scheduler), ops endpoints
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this panel showing correct data or silent failure?"
────────────────────────────────────────
Attribute: Key Pattern
Value: "governance", "silent governance failures", "invariant monitor"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "governance enforcement" is in
  general's qualifier_phrases. Detects silent governance failures.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Governance monitoring to detect silent failures. System-wide governance concern.
```

---

### [x] `general/L5_engines/scheduler_facade.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Adapter (Facade)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Scheduler Facade - Thin translation layer for job scheduling operations.
  Job scheduling: create/list/get/update/delete jobs, trigger, pause, resume.
  JobStatus (ACTIVE, PAUSED, DISABLED), JobRunStatus (PENDING, RUNNING, COMPLETED).
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L6 drivers
────────────────────────────────────────
Attribute: Callers
Value: L2 scheduler.py API, SDK, Worker
────────────────────────────────────────
Attribute: Decision Made
Value: Coordinates job scheduling - WHEN jobs execute
────────────────────────────────────────
Attribute: Key Pattern
Value: "scheduler", "job", "execution", "trigger"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → "job state", "execution coordinator"
  are in general's qualifier_phrases. Job scheduling orchestration.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Job scheduling orchestration - determines WHEN scheduled jobs execute.
```

---

### [x] `general/L5_engines/webhook_verify.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Webhook signature verification utility. Verifies HMAC signatures for
  incoming webhooks: verify_slack_signature(), verify_github_signature(),
  verify_stripe_signature(). System-wide security infrastructure.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure verification logic)
────────────────────────────────────────
Attribute: Callers
Value: webhook endpoints, integration adapters
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this webhook authentic?" - security verification
────────────────────────────────────────
Attribute: Key Pattern
Value: "webhook verify", "HMAC signature", "security"
────────────────────────────────────────
Attribute: Qualifier Test
Value: System-wide security utility used by any domain receiving webhooks.
  Cross-domain infrastructure belongs in general per HOC topology.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide security utility. Cross-domain webhook verification
  infrastructure belongs in general.
```

---

### [x] `general/L5_lifecycle/execution.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Lifecycle
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Lifecycle stage execution. Defines ExecutionStage enum, stage transitions,
  stage validation. Supports agent/run lifecycle state machine implementation.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (lifecycle definitions)
────────────────────────────────────────
Attribute: Callers
Value: lifecycle_facade.py, worker runtime
────────────────────────────────────────
Attribute: Decision Made
Value: Coordinates execution stage transitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "execution", "lifecycle", "stage"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → Lifecycle stage execution
  is orchestration infrastructure. "workflow orchestrat", "job state" in
  general's qualifier_phrases.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Lifecycle stage execution is core orchestration infrastructure.
  Clearly belongs in general domain.
```

---

### [x] `general/L5_lifecycle/knowledge_plane.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Lifecycle
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Knowledge plane lifecycle domain models. Defines knowledge plane states,
  transitions, validation. Supports knowledge_sdk.py facade implementation.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (domain models)
────────────────────────────────────────
Attribute: Callers
Value: knowledge_sdk.py, lifecycle services
────────────────────────────────────────
Attribute: Decision Made
Value: Defines knowledge plane lifecycle states
────────────────────────────────────────
Attribute: Key Pattern
Value: "knowledge plane", "lifecycle", "domain models"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHEN and HOW system actions execute?" → Lifecycle domain models
  for knowledge plane orchestration. Lifecycle infrastructure stays in general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Knowledge plane lifecycle domain models supporting orchestration.
  Lifecycle infrastructure belongs in general.
```

---

### [x] `general/L5_schemas/common.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schema
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Cross-domain shared schemas. Common Pydantic models used across
  multiple domains. Base classes, shared enums, utility types.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: Multiple domains import from this
────────────────────────────────────────
Attribute: Decision Made
Value: None - shared type definitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "common", "shared schemas", "cross-domain"
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain schemas - per HOC topology "Cross-Domain Location Rule",
  cross-domain items go to general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain shared schemas. Per HOC topology, cross-domain items
  belong in general.
```

---

### [x] `general/L5_schemas/rac_models.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schema
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: RAC (Replay Audit Contract) domain models. Cross-domain contract
  models for replay/audit functionality. Used by multiple domains for
  audit trail and replay verification.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: audit services, replay services, multiple domains
────────────────────────────────────────
Attribute: Decision Made
Value: None - contract model definitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "RAC", "contract models", "cross-domain audit"
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain audit contract models - per HOC topology, cross-domain
  items go to general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain RAC contract models. Per HOC topology, cross-domain
  items belong in general.
```

---

### [x] `general/L6_drivers/alert_emitter.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Emit alerts for near-threshold and breach events. Checks AlertConfig,
  routes to configured channels (UI notifications, webhooks). Handles alert
  throttling and delivery tracking.
────────────────────────────────────────
Attribute: Tables Accessed
Value: AlertConfig (R), ThresholdSignal (R/W)
────────────────────────────────────────
Attribute: Callers
Value: policy/prevention_engine.py
────────────────────────────────────────
Attribute: Decision Made
Value: "Should this alert be sent?" - based on config and throttling
────────────────────────────────────────
Attribute: Key Pattern
Value: "threshold events", "alert channels", "alert emission"
────────────────────────────────────────
Attribute: Qualifier Test
Value: Cross-domain: Reads threshold signals (controls concern) and sends via
  webhooks/UI (integrations/overview). Per HOC topology "Cross-Domain Location
  Rule", cross-domain items go to general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: Cross-domain alert emission. Bridges threshold events (controls) and
  notification delivery (integrations). Cross-domain stays in general.
```

---

### [x] `general/L6_drivers/decisions.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Decision contract enforcement. Records decisions across the system:
  ROUTING, RECOVERY, MEMORY, POLICY, BUDGET. "Emit records where decisions
  already happen. No logic changes." Contract-mandated fields: decision_source,
  decision_trigger.
────────────────────────────────────────
Attribute: Tables Accessed
Value: decision_records (W)
────────────────────────────────────────
Attribute: Callers
Value: API routes, workers
────────────────────────────────────────
Attribute: Decision Made
Value: None - records decisions made elsewhere, doesn't make decisions
────────────────────────────────────────
Attribute: Key Pattern
Value: "decision record", "contract enforcement", "decision tracking"
────────────────────────────────────────
Attribute: Qualifier Test
Value: System-wide decision recording infrastructure. Records decisions from
  ANY domain (routing, recovery, policy, budget). Per HOC topology, system-wide
  infrastructure goes to general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide decision recording infrastructure serving all domains.
  Cross-domain infrastructure belongs in general.
```

---

### [x] `general/L6_drivers/idempotency.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Idempotency key utilities. Prevents duplicate runs using idempotency
  keys. Checks if a run with given key already exists, handles TTL expiration.
────────────────────────────────────────
Attribute: Tables Accessed
Value: Run (R)
────────────────────────────────────────
Attribute: Callers
Value: API routes, workers
────────────────────────────────────────
Attribute: Decision Made
Value: "Does this run already exist?" - idempotency check
────────────────────────────────────────
Attribute: Key Pattern
Value: "idempotency", "duplicate prevention", "system-wide utility"
────────────────────────────────────────
Attribute: Qualifier Test
Value: System-wide infrastructure for run creation idempotency. Used by
  orchestration layer when creating runs. Per HOC topology, system-wide
  utilities go to general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide idempotency infrastructure. Cross-domain utility used
  during run orchestration. Belongs in general.
```

---

### [x] `general/L6_drivers/ledger.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Discovery ledger for artifact tracking. "Discovery Ledger records
  curiosity, not decisions." Pure observation - nothing depends on this table.
  Aggregates signals: same (artifact, field, signal_type) updates seen_count.
────────────────────────────────────────
Attribute: Tables Accessed
Value: discovery_ledger (R/W)
────────────────────────────────────────
Attribute: Callers
Value: API routes, workers
────────────────────────────────────────
Attribute: Decision Made
Value: None - pure observation, no system depends on it
────────────────────────────────────────
Attribute: Key Pattern
Value: "discovery ledger", "signal recording", "artifact tracking"
────────────────────────────────────────
Attribute: Qualifier Test
Value: System-wide observational infrastructure. Records signals from any
  part of the system. Per HOC topology, system-wide infrastructure goes to
  general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide discovery/observation infrastructure. Cross-domain
  signal recording belongs in general.
```

---

### [x] `general/L6_drivers/schema_parity.py`

```
Attribute: Current Domain
Value: general
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Schema parity checking utilities. "M26 Prevention Mechanism #2: Startup
  Schema Parity Guard." Verifies SQLModel metadata matches live DB schema.
  Hard crashes on boot if mismatch - "cost integrity errors are worse than
  downtime."
────────────────────────────────────────
Attribute: Tables Accessed
Value: database schema (introspection)
────────────────────────────────────────
Attribute: Callers
Value: startup, SDK, API
────────────────────────────────────────
Attribute: Decision Made
Value: "Does model match database?" - schema validation
────────────────────────────────────────
Attribute: Key Pattern
Value: "schema parity", "startup guard", "validation"
────────────────────────────────────────
Attribute: Qualifier Test
Value: System-wide governance/validation infrastructure. Enforces schema
  consistency for entire system at startup. Per HOC topology, system-wide
  infrastructure goes to general.

ASSIGN TO: general ✓ (CONFIRMED CORRECT)
Reason: System-wide schema validation infrastructure. Governance guard for
  entire system belongs in general.
```

---

### [x] `integrations/L3_adapters/customer_killswitch_adapter.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L3 — Boundary Adapter
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied from path)
────────────────────────────────────────
Attribute: What It Does
Value: Customer killswitch boundary adapter (L2 → L3 → L4). Enforces tenant
  isolation, delegates to GuardWriteService and CustomerKillswitchReadService.
  Transforms results to customer-safe DTOs.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via L4/L5 services
────────────────────────────────────────
Attribute: Callers
Value: guard.py (L2)
────────────────────────────────────────
Attribute: Decision Made
Value: None - translation only, delegates to L4
────────────────────────────────────────
Attribute: Key Pattern
Value: "killswitch", "customer killswitch", "tenant isolation"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "killswitch" is EXPLICITLY
  in controls' qualifier_phrases. This adapter serves killswitch operations.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "killswitch" is EXPLICITLY in controls' qualifier_phrases. Adapters
  are classified by the domain they SERVE. This serves controls operations.
```

---

### [x] `integrations/L3_adapters/founder_contract_review_adapter.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L3 — Boundary Adapter
────────────────────────────────────────
Attribute: Audience
Value: FOUNDER (from header - Part-2 CRM Workflow)
────────────────────────────────────────
Attribute: What It Does
Value: Translate Contract domain models to Founder Review views. Receives
  ContractState from L4, selects/renames fields for Founder audience.
  HARD RULES: NO business logic, NO state transitions, NO eligibility decisions.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure translation)
────────────────────────────────────────
Attribute: Callers
Value: founder_review.py (L2)
────────────────────────────────────────
Attribute: Decision Made
Value: None - field selection and translation only
────────────────────────────────────────
Attribute: Key Pattern
Value: "contract", "contract review", "ContractState"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → Contract review is part of governance
  contract workflow. Imports from policies/L5_engines/contract_engine.
  Adapters classified by domain served.

ASSIGN TO: policies ⚠️ (MISPLACED)
Reason: Translates policy Contract domain models for review. Imports from
  policies/L5_engines/contract_engine. Serves the policies domain contract
  review workflow.
```

---

### [x] `integrations/L3_adapters/policy_adapter.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L3 — Boundary Adapter
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER (implied)
────────────────────────────────────────
Attribute: What It Does
Value: Policy evaluation boundary adapter (L2 → L3 → L4). Receives API requests,
  translates to domain facts, delegates to policy_command.py. "L3 Is Translation
  Only - no branching, no thresholds."
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure translation)
────────────────────────────────────────
Attribute: Callers
Value: policy.py (L2)
────────────────────────────────────────
Attribute: Decision Made
Value: None - translation only, delegates to L4
────────────────────────────────────────
Attribute: Key Pattern
Value: "policy evaluation", "policy adapter"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "policy evaluation" is in policies'
  qualifier_phrases. This adapter serves policy operations.

ASSIGN TO: policies ⚠️ (MISPLACED)
Reason: "policy evaluation" is in policies' qualifier_phrases. Imports from
  policy_command. Adapters classified by domain served. Serves policies.
```

---

### [x] `integrations/L5_engines/connectors_facade.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Connectors Facade - Centralized access to connector operations. Provides
  unified access to HTTP, SQL, MCP connectors. Connector registration,
  management, testing. Single point for audit emission.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via connector services
────────────────────────────────────────
Attribute: Callers
Value: L2 connectors.py API, SDK
────────────────────────────────────────
Attribute: Decision Made
Value: Coordinates connector operations
────────────────────────────────────────
Attribute: Key Pattern
Value: "connector", "HTTP connector", "SQL connector", "MCP connector"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "HOW external systems connect?" → "connector" is in integrations'
  qualifier_phrases. External connector management is integrations domain.

ASSIGN TO: integrations ✓ (CONFIRMED CORRECT)
Reason: "connector" is in integrations' qualifier_phrases. Manages HTTP, SQL,
  MCP connectors for external system connectivity. Clearly integrations.
```

---

### [x] `integrations/L5_engines/cost_safety_rails.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Cost safety rail enforcement (business rules). Per-tenant auto-apply
  caps and blast-radius limits. "No automatic cost action may exceed:
  Per-tenant daily cap, Per-org daily cap, Blast-radius scope limits."
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure business rules)
────────────────────────────────────────
Attribute: Callers
Value: cost services, workers
────────────────────────────────────────
Attribute: Decision Made
Value: "Is this cost action within safety limits?"
────────────────────────────────────────
Attribute: Key Pattern
Value: "cost cap", "daily cap", "blast-radius limits", "safety rails"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT limits and configurations apply?" → "cost limit", "budget" are
  in controls' qualifier_phrases. Cost caps and limits enforcement.

ASSIGN TO: controls ⚠️ (MISPLACED)
Reason: "cost limit", "budget" are in controls' qualifier_phrases. Cost safety
  rails enforce per-tenant caps and limits. Limits belong to controls domain.
```

---

### [x] `integrations/L5_engines/cost_snapshots.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5/L6 — HYBRID (pending refactor)
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Cost snapshot computation with embedded DB operations. "Anomaly detection
  reads ONLY from complete snapshots, never from live data." Computes hourly
  snapshots for CostAnomalyDetector evaluation.
────────────────────────────────────────
Attribute: Tables Accessed
Value: cost_records (R), cost_snapshots (R/W)
────────────────────────────────────────
Attribute: Callers
Value: workers, cost services
────────────────────────────────────────
Attribute: Decision Made
Value: "What is the cost snapshot for this period?" - derived cost computation
────────────────────────────────────────
Attribute: Key Pattern
Value: "cost snapshot", "cost computation", "anomaly detection"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT can be derived?" → "cost analysis", "cost intelligence" are in
  analytics' qualifier_phrases. Cost snapshot computation is derived metrics.

ASSIGN TO: analytics ⚠️ (MISPLACED)
Reason: "cost analysis" is in analytics' qualifier_phrases. Cost snapshot
  computation produces derived metrics for anomaly detection. Analytics domain
  owns derived cost metrics.
```

---

### [x] `integrations/L5_engines/cus_telemetry_service.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Customer telemetry service - LLM usage ingestion and reporting. Re-exports
  from cus_telemetry_engine.py. Provides telemetry ingestion for runs.
────────────────────────────────────────
Attribute: Tables Accessed
Value: via cus_telemetry_engine
────────────────────────────────────────
Attribute: Callers
Value: cus_telemetry.py API
────────────────────────────────────────
Attribute: Decision Made
Value: None - data ingestion
────────────────────────────────────────
Attribute: Key Pattern
Value: "telemetry", "LLM usage", "ingestion"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT LLM run occurred?" → "trace", "execution record" are in activity's
  qualifier_phrases. Telemetry records run execution data.

ASSIGN TO: activity ⚠️ (MISPLACED)
Reason: Telemetry ingestion records LLM run execution data. "trace", "execution
  record" are in activity's qualifier_phrases. Run telemetry belongs in activity.
```

---

### [x] `integrations/L5_engines/graduation_engine.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Agent graduation evaluation domain logic (pure computation). "Graduation
  is DERIVED, not DECLARED." Computed from evidence, re-evaluated periodically,
  downgradable when evidence regresses. Tied to real capability gates.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure computation)
────────────────────────────────────────
Attribute: Callers
Value: graduation_evaluator.py (L5)
────────────────────────────────────────
Attribute: Decision Made
Value: "What graduation level has this agent earned?"
────────────────────────────────────────
Attribute: Key Pattern
Value: "graduation", "capability gates", "evidence-based"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "HOW external systems connect?" → "graduation" is in integrations'
  qualifier_phrases. Agent graduation is about integration readiness.

ASSIGN TO: integrations ✓ (CONFIRMED CORRECT)
Reason: "graduation" is in integrations' qualifier_phrases. Agent graduation
  evaluation determines integration readiness levels. Correctly placed.
```

---

### [x] `integrations/L5_engines/identity_resolver.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Identity resolution from various providers (JWT parsing). Resolves
  identities from Clerk JWT, Auth0 JWT, API keys, System tokens. Abstract
  resolver pattern with provider-specific implementations.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure identity resolution)
────────────────────────────────────────
Attribute: Callers
Value: IAMService, Auth middleware
────────────────────────────────────────
Attribute: Decision Made
Value: "Who is this actor?" - identity resolution
────────────────────────────────────────
Attribute: Key Pattern
Value: "identity", "JWT", "Clerk", "Auth0", "user"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHO owns what?" → Identity resolution determines WHO the actor is.
  "user role", "membership" are in account's qualifier_phrases. Identity
  is fundamentally about ownership/tenancy.

ASSIGN TO: account ⚠️ (MISPLACED)
Reason: Identity resolution answers "WHO is this actor?" which is the account
  domain question. While it integrates with external providers, the core
  decision is about user identity/ownership - account domain.
```

---

### [x] `integrations/L5_engines/learning_proof_engine.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engine
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Learning proof generation (graduation gates, regret tracking). Proves
  the integration loop LEARNS: PREVENTION PROOF (did policy prevent recurrence?),
  REGRET TRACKING (did policy cause harm?), ADAPTIVE CONFIDENCE (calibrate
  thresholds from outcomes).
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure computation)
────────────────────────────────────────
Attribute: Callers
Value: learning workers, policy engines
────────────────────────────────────────
Attribute: Decision Made
Value: "Did this policy actually learn and improve?"
────────────────────────────────────────
Attribute: Key Pattern
Value: "prevention proof", "regret tracking", "lesson learned"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT rules govern behavior?" → "lesson learned" is in policies'
  qualifier_phrases. Proves that policies learn from incidents.

ASSIGN TO: policies ⚠️ (MISPLACED)
Reason: "lesson learned" is in policies' qualifier_phrases. Learning proof
  demonstrates that policies improve from incidents. Policy learning evidence
  belongs in policies domain.
```

---

### [x] `integrations/L5_schemas/cost_snapshot_schemas.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Schemas
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Cost snapshot dataclasses and enums. Defines SnapshotType (HOURLY/DAILY),
  SnapshotStatus, EntityType. Includes SEVERITY_THRESHOLDS for anomaly detection.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure schema definitions)
────────────────────────────────────────
Attribute: Callers
Value: cost_snapshot_engine, cost_snapshot_driver
────────────────────────────────────────
Attribute: Decision Made
Value: None - data type definitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "cost snapshot", "severity thresholds", "anomaly"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT can be derived?" → Schemas for cost snapshot computation.
  cost_snapshots.py engine was classified as analytics. Schemas follow engine.

ASSIGN TO: analytics ⚠️ (MISPLACED)
Reason: Schemas for cost snapshot computation which is analytics domain.
  Schemas should be co-located with their engine (cost_snapshots.py → analytics).
```

---

### [x] `integrations/L5_schemas/datasource_model.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L5 — Domain Engines
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: CustomerDataSource - Customer data source models and registry. Data source
  abstraction for: Database connections, File storage, API endpoints, Vector
  stores, Custom connectors. DataSourceType, DataSourceStatus, DataSourceConfig.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (pure model definitions)
────────────────────────────────────────
Attribute: Callers
Value: Data source services
────────────────────────────────────────
Attribute: Decision Made
Value: None - data model definitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "data source", "connector", "external connection"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "HOW external systems connect?" → "connector", "data bridge" are in
  integrations' qualifier_phrases. External data source management.

ASSIGN TO: integrations ✓ (CONFIRMED CORRECT)
Reason: "connector" is in integrations' qualifier_phrases. Data source models
  for external system connections. Clearly integrations domain.
```

---

### [x] `integrations/L6_drivers/bridges_driver.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Database operations for integration bridge audit trails. Records policy
  activation audits. "Every ACTIVE policy must have an audit record."
  PolicyActivationAudit persistence.
────────────────────────────────────────
Attribute: Tables Accessed
Value: PolicyActivationAudit (R/W)
────────────────────────────────────────
Attribute: Callers
Value: bridges_engine
────────────────────────────────────────
Attribute: Decision Made
Value: None - audit record persistence
────────────────────────────────────────
Attribute: Key Pattern
Value: "audit trail", "policy activation audit", "audit record"
────────────────────────────────────────
Attribute: Qualifier Test
Value: "WHAT immutable record exists?" → "audit trail", "audit" are in logs'
  qualifier_phrases. Policy activation audit records.

ASSIGN TO: logs ⚠️ (MISPLACED)
Reason: "audit trail" is in logs' qualifier_phrases. Records policy activation
  audit trail - immutable audit records belong in logs domain.
```

---

### [x] `integrations/L6_drivers/knowledge_plane.py`

```
Attribute: Current Domain
Value: integrations
────────────────────────────────────────
Attribute: Layer
Value: L6 — Domain Driver
────────────────────────────────────────
Attribute: Audience
Value: CUSTOMER
────────────────────────────────────────
Attribute: What It Does
Value: Knowledge plane models and registry. Knowledge graph abstraction for:
  Knowledge organization, Semantic relationships, Multi-source integration.
  KnowledgePlaneStatus, KnowledgeNodeType.
────────────────────────────────────────
Attribute: Tables Accessed
Value: None (data models only)
────────────────────────────────────────
Attribute: Callers
Value: L5 engines
────────────────────────────────────────
Attribute: Decision Made
Value: None - model definitions
────────────────────────────────────────
Attribute: Key Pattern
Value: "knowledge plane", "knowledge graph", "system-wide"
────────────────────────────────────────
Attribute: Qualifier Test
Value: Product: system-wide. Knowledge plane is cross-domain infrastructure.
  Similar to general/L5_lifecycle/knowledge_plane.py which is in general.
  Per HOC topology, system-wide infrastructure goes to general.

ASSIGN TO: general ⚠️ (MISPLACED)
Reason: Product marked as "system-wide". Knowledge plane is cross-domain
  infrastructure. Per HOC topology, system-wide items go to general.
```

---

## V3 MANUAL AUDIT COMPLETE

---

## Final Audit Progress Summary

| Domain | Total | Reviewed | Confirmed | Misplaced |
|--------|-------|----------|-----------|-----------|
| duplicates | 3 | 3 | 0 | 3 (DEFERRED) |
| activity | 5 | 5 | 4 | 1 |
| account | 6 | 6 | 2 | 4 |
| analytics | 15 | 15 | 7 | 8 |
| incidents | 24 | 24 | 12 | 12 |
| logs | 35 | 35 | 18 | 17 |
| general | 30 | 30 | 30 | 0 |
| integrations | 14 | 14 | 3 | 11 |
| policies | 55 | 55 | 24 | 31 |
| **TOTAL** | **187** | **187** | **100** | **87** |

## Domain Performance Summary

| Domain | Confirmation Rate | Notes |
|--------|------------------|-------|
| general | 100% (30/30) | Excellent - cross-domain items correctly placed |
| activity | 80% (4/5) | Good |
| logs | 51% (18/35) | Mixed - many misplacements |
| incidents | 50% (12/24) | Mixed |
| analytics | 47% (7/15) | Mixed |
| policies | 44% (24/55) | Many controls/general items misplaced here |
| account | 33% (2/6) | Low |
| integrations | 21% (3/14) | Low - many items serving other domains |

## Key Findings

1. **general domain is the gold standard** - 100% confirmation rate. Cross-domain and system-wide items correctly centralized.

2. **policies domain is overloaded** - 31 misplaced files, mostly:
   - Controls items (killswitch, limits, budgets, thresholds)
   - General items (orchestration, lifecycle, governance enforcement)
   - Logs items (audit, evidence, proof)

3. **integrations domain misused as catch-all** - Only 21% confirmation. Files serving controls, policies, account, analytics placed here incorrectly.

4. **controls domain underutilized** - Many limit/threshold/killswitch items scattered across policies and integrations.

5. **Adapters should follow their domain** - L3 adapters were often placed in wrong domain; should be co-located with the domain they serve.

---

## Misplacement Summary (so far)

| File | From | To | Reason |
|------|------|-----|--------|
| activity/L6_drivers/threshold_driver.py | activity | controls | Reads Limit tables |
| account/L5_notifications/engines/channel_engine.py | account | integrations | Manages Slack/PagerDuty/webhook |
| account/L5_support/CRM/engines/audit_engine.py | account | logs | Evidence/verdict producer |
| account/L5_support/CRM/engines/job_executor.py | account | general | Execution coordinator |
| account/L6_drivers/worker_registry_driver.py | account | integrations | Worker/connector registry |
| analytics/L5_engines/alert_worker.py | analytics | general | Retry orchestration |
| analytics/L5_engines/cb_sync_wrapper.py | analytics | controls | Circuit breaker wrapper |
| analytics/L5_engines/killswitch.py | analytics | controls | Killswitch control |
| analytics/L5_engines/manager.py | analytics | general | Envelope lifecycle |
| analytics/L5_engines/s2_cost_smoothing.py | analytics | controls | Concurrency limits |
| analytics/L6_drivers/alert_driver.py | analytics | general | Follows alert_worker |
| analytics/L6_drivers/circuit_breaker.py | analytics | controls | Circuit breaker = system limit |
| analytics/L6_drivers/circuit_breaker_async.py | analytics | controls | Circuit breaker async variant |
| incidents/L5_engines/channel_engine.py | incidents | integrations | Slack/PagerDuty/Teams webhooks |
| incidents/L5_engines/degraded_mode_checker.py | incidents | general | Governance enforcement |
| incidents/L5_engines/evidence_report.py | incidents | logs | Evidence/proof generation |
| incidents/L5_engines/failure_mode_handler.py | incidents | policies | Policy failure handling |
| incidents/L5_engines/lessons_engine.py | incidents | policies | "lesson learned" in policies qualifiers |
| incidents/L5_engines/mapper.py | incidents | logs | SOC2 compliance evidence mapping |
| incidents/L5_engines/panel_invariant_monitor.py | incidents | general | Governance monitoring |
| incidents/L5_engines/panel_verification_engine.py | incidents | general | System determinism enforcement |
| incidents/L5_engines/pdf_renderer.py | incidents | logs | Evidence document rendering |
| incidents/L5_engines/recovery_evaluation_engine.py | incidents | policies | Recovery rule evaluation |
| incidents/L5_engines/runtime_switch.py | incidents | general | Governance runtime toggle |
| incidents/L6_drivers/scoped_execution.py | incidents | controls | Execution scope limits |
| logs/L5_engines/alert_fatigue.py | logs | controls | "rate limit" qualifier |
| logs/L5_engines/audit_durability.py | logs | general | "governance enforcement" for audit |
| logs/L5_engines/traces_metrics.py | logs | general/L5_Infra/metrics/ | Pure Prometheus instrumentation infrastructure |
| logs/L5_engines/monitors_facade.py | logs | integrations | External service health monitoring (HTTP/TCP/DNS) |
| logs/L5_engines/notifications_facade.py | logs | integrations | Multi-channel notification delivery (email/Slack/webhook/SMS) |
| logs/L5_engines/alerts_facade.py | logs | controls | Customer-configured alert rules/thresholds |
| logs/L5_engines/connectors_facade.py | logs | integrations | HTTP/SQL/MCP connector management |
| logs/L5_engines/controls_facade.py | logs | controls | Killswitch/circuit breaker/feature flag/throttle |
| logs/L5_engines/datasources_facade.py | logs | integrations | External data source management |
| logs/L5_engines/detection_facade.py | logs | analytics | Anomaly detection (behavioral analysis) |
| logs/L5_engines/durability.py | logs | general | RAC durability enforcement |
| logs/L5_engines/lifecycle_facade.py | logs | general/L5_engines/lifecycle/ | System-wide lifecycle states (activity imports from this) |
| logs/L5_engines/retrieval_facade.py | logs | general | Facade over system-wide data access mediator |
| logs/L5_engines/retrieval_mediator.py | logs | general | Central choke point for data access (gateway control) |
| logs/L5_engines/panel_slot_evaluator.py | logs | general | System-wide UI panel infrastructure |
| logs/L5_engines/scheduler_facade.py | logs | general | Job scheduling = system-wide orchestration |
| logs/L5_engines/service.py | logs | integrations | Credential/vault management for connectors |
| policies/L5_controls/drivers/killswitch_read_driver.py | policies | controls | "killswitch" in controls qualifiers |
| policies/L5_controls/drivers/runtime_switch.py | policies | general | "governance enforcement" - system orchestration |
| policies/L5_controls/engines/degraded_mode_checker.py | policies | general | Governance state management - WHEN actions execute |
| policies/L5_controls/engines/customer_killswitch_read_engine.py | policies | controls | "killswitch" in controls qualifiers |
| policies/L5_schemas/retry.py | policies | general | "retry logic" in general qualifiers |
| policies/L5_schemas/overrides.py | policies | controls | Limit override schemas |
| policies/L5_schemas/simulation.py | policies | controls | Limit simulation schemas (rate limit, budget) |
| policies/L5_schemas/policy_limits.py | policies | controls | LIMIT schemas (budget/rate/threshold) despite name |
| policies/L6_drivers/alert_emitter.py | policies | general | Alert emission (potential duplicate of general/alert_emitter.py) |
| policies/L6_drivers/override_driver.py | policies | controls | Limit override lifecycle - "limit" in controls qualifiers |
| policies/L6_drivers/budget_enforcement_driver.py | policies | controls | "budget" in controls qualifiers |
| policies/L6_drivers/capture.py | policies | logs | Evidence capture - "evidence record" in logs qualifiers |
| policies/L6_drivers/cross_domain.py | policies | general | Cross-domain orchestration - per HOC topology |
| policies/L6_drivers/dag_executor.py | policies | general | "execution order" in general qualifiers |
| policies/L6_drivers/governance_signal_driver.py | policies | general | "governance enforcement" - system-wide signal infrastructure |
| policies/L6_drivers/keys_driver.py | policies | apis | "api key" in apis qualifiers |
| policies/L6_drivers/limits_read_driver.py | policies | controls | "limit" in controls qualifiers |
| policies/L6_drivers/llm_threshold_driver.py | policies | controls | "threshold config" in controls qualifiers |
| policies/L6_drivers/orphan_recovery.py | policies | activity | "run lifecycle", "run state" in activity qualifiers |
| policies/L6_drivers/policy_limits_driver.py | policies | controls | "limit" in controls qualifiers (budget/rate/token limits) |
| policies/L5_engines/audit_engine.py | policies | logs | "audit" in logs qualifiers - verdict producer |
| policies/L5_engines/audit_evidence.py | policies | logs | "audit trail", "evidence record" in logs qualifiers |
| policies/L5_engines/billing_provider.py | policies | account | "billing", "subscription" in account qualifiers |
| policies/L5_engines/budget_enforcement_engine.py | policies | controls | "budget" in controls qualifiers |
| policies/L5_engines/certificate.py | policies | logs | "proof", "evidence record" in logs qualifiers |
| policies/L5_engines/constraint_checker.py | policies | general | "governance enforcement" - runtime constraint enforcement |
| policies/L5_engines/contract_engine.py | policies | general | "job state" - contract lifecycle state machine |
| policies/L5_engines/control_registry.py | policies | logs | "audit" - SOC2 compliance control registry |
| policies/L5_engines/controls_facade.py | policies | controls | "killswitch", "circuit breaker", "feature flag", "throttle" |
| policies/L5_engines/dag_sorter.py | policies | general | "execution order" - policy execution ordering is orchestration |
| policies/L5_engines/decisions.py | policies | controls | "throttle" - abuse protection decisions are limit enforcement |
