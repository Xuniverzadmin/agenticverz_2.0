# V4 Domain Workbook — Canonical Consolidation Final

**Status:** EXECUTION COMPLETE — MIGRATION CLOSED
**Created:** 2026-01-27
**Closed:** 2026-01-27
**Phase:** P10 (Close-out)
**Reference:** PIN-470, PIN-479, PIN-480, PIN-481, PIN-482
**Input:** PHASE5_CONSOLIDATION_CANDIDATES.csv (90 candidates)
**Generator:** Manual review with Claude — batch-of-5, explicit approval required

---

## Domain Classification Criteria

> These criteria are the authoritative decision framework for determining which file is canonical
> and which is redundant. Applied domain-by-domain during batch review.

### 1. General

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHEN and HOW system actions execute |
| **Allowed Responsibilities** | Runtime orchestration, execution order, retries, compensation, governance enforcement, gateway control, system invariants, lifecycle gating |
| **Explicitly Forbidden** | Business rules, customer policies, limits, analytics, domain-specific state |
| **Canonical If** | Code decides **system-facing** execution timing, ordering, retry, blocking, or system correctness |
| **Redundant If** | Duplicate only consumes runtime context or applies domain rules |
| **Typical Keywords (Qualified)** | runtime orchestration, governance enforcement, execution order, retry, compensation |
| **Never Owns** | "What rule", "What limit", "What incident", "What metric" |

### 2. Overview

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHAT consolidated state is visible |
| **Allowed Responsibilities** | Read-only aggregation, summaries, dashboards, projections |
| **Explicitly Forbidden** | Writing state, triggering actions, enforcement |
| **Canonical If** | Code aggregates or presents data without mutating or deciding |
| **Redundant If** | Duplicate performs derivation (analytics) or enforcement |
| **Typical Keywords** | summary, overview, snapshot, dashboard |
| **Never Owns** | Execution, policies, incidents, limits |

### 3. Activity

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHAT LLM run occurred |
| **Allowed Responsibilities** | Run lifecycle, execution metadata, raw run state, traces |
| **Explicitly Forbidden** | Policy evaluation, classification, aggregation |
| **Canonical If** | Code records or manages run execution and raw outcomes |
| **Redundant If** | Duplicate classifies, evaluates, or limits runs |
| **Typical Keywords** | run, execution, trace, span |
| **Never Owns** | "Is this a problem?", "Is this allowed?" |

### 4. Incidents

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHETHER an outcome is a problem |
| **Allowed Responsibilities** | Failure classification, near-threshold detection, violation detection, recovery signals |
| **Explicitly Forbidden** | Policy definition, limits, runtime execution |
| **Canonical If** | Code classifies outcomes as failures, violations, or degradations |
| **Redundant If** | Duplicate only records logs or enforces limits |
| **Typical Keywords** | incident, failure, violation, near-threshold |
| **Never Owns** | Policy rules, retries, execution |

### 5. Policies

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHAT rules govern behavior |
| **Allowed Responsibilities** | Policy definition, activation, evaluation logic, lessons learned |
| **Explicitly Forbidden** | Runtime execution, retries, orchestration |
| **Canonical If** | Code defines or evaluates rules against behavior |
| **Redundant If** | Duplicate enforces timing or system execution |
| **Typical Keywords** | policy, rule, evaluation, lesson |
| **Never Owns** | "When to execute", "How to retry" |

### 6. Controls

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHAT limits and configurations apply |
| **Allowed Responsibilities** | Thresholds, quotas, environment variables, feature flags, kill-switches |
| **Explicitly Forbidden** | Run execution, analytics derivation |
| **Canonical If** | Code enforces limits or configurations |
| **Redundant If** | Duplicate classifies incidents or defines policies |
| **Typical Keywords** | limit, quota, threshold, config |
| **Never Owns** | Business rules, execution |

### 7. Logs

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHAT immutable record exists |
| **Allowed Responsibilities** | Audit ledger, system logs, evidence, append-only records, integrity verification |
| **Explicitly Forbidden** | Classification, mutation, aggregation, enforcement timing |
| **Canonical If** | Code creates or validates immutable records |
| **Redundant If** | Duplicate enforces runtime behavior or derives metrics |
| **Typical Keywords** | audit, evidence, immutable, ledger |
| **Never Owns** | "Is this allowed?", "Is this a problem?" |

### 8. Analytics

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHAT can be derived |
| **Allowed Responsibilities** | Cost intelligence, statistics, behavioral analysis, aggregates |
| **Explicitly Forbidden** | Writing source-of-truth data |
| **Canonical If** | Code derives insights from existing data |
| **Redundant If** | Duplicate writes authoritative records |
| **Typical Keywords** | metrics, stats, aggregates |
| **Never Owns** | Source-of-truth, execution |

### 9. Integrations

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | HOW external systems connect |
| **Allowed Responsibilities** | SDK setup, adapters, external auth, data bridges, webhooks |
| **Explicitly Forbidden** | Policy decisions, runtime orchestration |
| **Canonical If** | Code manages external connectivity or delivery |
| **Redundant If** | Duplicate defines business rules |
| **Typical Keywords** | adapter, webhook, connector |
| **Never Owns** | Enforcement, governance |

### 10. API Keys

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHO can call what |
| **Allowed Responsibilities** | API keys, scopes, access control |
| **Explicitly Forbidden** | Business logic, policy evaluation |
| **Canonical If** | Code authorizes or authenticates API access |
| **Redundant If** | Duplicate executes business logic |
| **Typical Keywords** | api key, scope, access |
| **Never Owns** | Domain behavior |

### 11. Account

| Field | Definition |
|-------|------------|
| **Exclusive Decision Owned** | WHO owns what |
| **Allowed Responsibilities** | Tenancy, subscription, user roles, sub-tenants |
| **Explicitly Forbidden** | Runtime actions, analytics |
| **Canonical If** | Code manages ownership or entitlement |
| **Redundant If** | Duplicate enforces limits or executes runs |
| **Typical Keywords** | tenant, subscription, role |
| **Never Owns** | Execution, enforcement |

---

## Protocol

1. Every candidate is reviewed in batches of 5
2. **No file is deleted without explicit user approval**
3. Each candidate is cross-referenced against V3_MANUAL_AUDIT_WORKBOOK.md
4. Callers are verified before any deletion
5. Import repoints are executed only after approval
6. SHA-256 hashes are verified post-operation
7. **Naming Correction Precedence:** If a file is correctly placed by responsibility but semantically misleading, **rename first, relocate only if still conflicting**. Misclassification driven by ambiguous filenames is resolved by rename, not extraction.
8. **Domain criteria are authoritative.** V3 workbook, CSV recommendations, and prior analysis are overridden where they conflict with the locked domain classification criteria.
9. **WHEN/HOW boundary split (C071 ruling):** General owns **system-facing** WHEN/HOW (runtime orchestration, execution order, retries, system invariants). Domain-specific modules own **customer-facing** WHEN/HOW (hallucination detection for customer runs, incident detection for customer incidents). If code decides WHEN/HOW something fires **in relation to customer-observable behavior**, it belongs to the domain that owns that behavior, NOT General. Future refinement may be needed to sharpen this boundary.

---

## Decision Legend

| Decision | Meaning |
|----------|---------|
| `APPROVED` | User approved — execute extraction/deletion + repoint |
| `REJECTED` | User rejected — skip, leave files as-is |
| `DEFERRED` | User deferred — revisit in a later batch |
| `MODIFIED` | User changed the recommendation — see notes |
| `PENDING` | Not yet reviewed |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total candidates | 90 |
| EXTRACT_TO_GENERAL | 52 |
| DELETE_FROM_{DOMAIN} | 35 |
| REVIEW_MERGE | 3 |
| Batches | 18 |
| Reviewed | **90 / 90 — COMPLETE** |
| Approved | 63 |
| Rejected | 9 (C002, C027, C052, C053, C054, C055, C059, C079, C081) |
| Subsumed | 18 (C014→C013, C015→C013, C021→C020, C026→C011, C063→C041, C064→C042, C065→C043, C066→C044, C069→C052, C070→C053, C072→C041+C042, C073→C041+C043, C074→C041+C044, C084→C042+C043, C087→C057+C058, C088→C033+C034, C089→C043+C044, C090→C067+C068) |
| Executed | 0 |

---

## Batch 1 (C001–C005) — STATUS: APPROVED (RE-ANALYZED WITH DOMAIN CRITERIA)

> **Note:** Original analysis was pre-domain-criteria. Re-analyzed 2026-01-27 with locked domain
> classification criteria + owner corrections for C004 and C005.

### C001: `email_verification.py`

| Field | Value |
|-------|-------|
| **ID** | C001 |
| **Duplicate IDs** | D529, D644, D645, D646, D911 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical** | `account/L5_engines/email_verification.py` |
| **Delete Targets** | `api_keys/L5_engines/email_verification.py` |
| **Callers** | account copy: `account/L5_engines/__init__.py:22` (1 ref). api_keys copy: **0 callers** |
| **V3 Workbook** | Not audited |
| **Domain Criteria** | `EmailVerificationService` — OTP-based identity verification for onboarding. Generates OTP, stores in Redis, sends via Resend API, enforces max 3 attempts + 60s cooldown. Contains Agenticverz-branded templates. This answers "WHO is this person?" = **Account** ("WHO owns what"). General is **forbidden** from business rules (OTP length, attempt limits, cooldown, branded emails). |
| **Analysis** | CSV recommendation INCORRECT. This is not a utility — it contains domain-specific business rules. Account is the correct owner. api_keys copy has zero callers and was a misplacement. |
| **Decision** | `APPROVED` — DELETE_FROM_API_KEYS, keep Account canonical |
| **Executed** | NO |

---

### C002: `notifications_facade.py` vs `notifications_base.py`

| Field | Value |
|-------|-------|
| **ID** | C002 |
| **Duplicate IDs** | D648, D651 |
| **Match Types** | CLASS |
| **Similarity** | 83.3% (partial) |
| **CSV Recommendation** | REVIEW_MERGE |
| **Canonical** | N/A — not true duplicates |
| **Delete Targets** | None |
| **Callers** | account facade: `policies/notifications.py:40`, `account/__init__.py:41` (2 refs). integrations base: **0 callers** (orphan) |
| **V3 Workbook** | `account/L5_engines/notifications_facade.py` marked `[x]` (audited) |
| **Domain Criteria** | **LAYER MISMATCH.** `notifications_facade.py` is L5 (concrete service with CRUD, preferences, channel mgmt). `notifications_base.py` is L3 (abstract adapter interface: `NotificationAdapter(ABC)` with abstract `connect()`, `send()`, `health_check()`). 83.3% match is false positive from shared enums. Different architectural roles, different layers. |
| **Analysis** | Not duplicates. Merging would violate layer topology. `notifications_base.py` is an orphan with 0 callers — flag for separate cleanup. |
| **Decision** | `REJECTED` — not a true duplicate |
| **Executed** | N/A |

---

### C003: `notifications_facade.py` (account + integrations)

| Field | Value |
|-------|-------|
| **ID** | C003 |
| **Duplicate IDs** | D530, D647, D649, D652, D654, D655, D656, D657, D923 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical** | `account/L5_engines/notifications_facade.py` |
| **Delete Targets** | `integrations/L5_engines/notifications_facade.py` |
| **Callers** | account copy: `policies/notifications.py:40`, `account/__init__.py:41` (2 refs). integrations copy: **0 callers** |
| **V3 Workbook** | account copy: **CONFIRMED account** — "Primary subject is USER/TENANT notification preferences." |
| **Domain Criteria** | `NotificationsFacade` manages per-user notification preferences, notification CRUD, channel configuration. Answers "WHO receives notifications and what are their preferences?" = **Account** ("WHO owns what"). Contains business logic (preferences, channel validation) — General is **forbidden** from business rules. V3 explicitly confirmed account. |
| **Analysis** | CSV recommendation INCORRECT. integrations copy has zero callers. V3 confirmed account ownership. General extraction would violate "Forbidden: Business rules" constraint. |
| **Decision** | `APPROVED` — DELETE_FROM_INTEGRATIONS, keep Account canonical |
| **Executed** | NO |

---

### C004: `profile.py` → RENAME to `profile_policy_mode.py`

| Field | Value |
|-------|-------|
| **ID** | C004 |
| **Duplicate IDs** | D531, D532, D533, D534, D535, D536, D537, D658, D659, D660, D926 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical** | `general/L5_engines/profile_policy_mode.py` (MOVE + RENAME) |
| **Delete Targets** | `account/L5_engines/profile.py` (0 callers), `policies/L5_engines/profile.py` (repoint 3 callers) |
| **Callers** | account copy: **0 callers**. policies copy: 3 callers — `boot_guard.py:87,101`, `failure_mode_handler.py:97` |
| **V3 Workbook** | Not audited |
| **Owner Correction** | This is NOT customer-console policy. It defines **system governance modes** (STRICT/STANDARD/OBSERVE_ONLY) with platform-internal feature flags (ROK, RAC, transaction coordinator, event reactor). Not customer-editable. Not policy library. Defines HOW the system governs itself. |
| **Domain Criteria** | System governance mode configuration = system invariants = **General** ("WHEN and HOW system actions execute"). The ambiguous name `profile.py` caused misclassification — rename to `profile_policy_mode.py` clarifies semantic intent. |
| **Analysis** | MOVE to General + RENAME. The file was in policies because "governance" sounded like policy, but system governance modes are platform-internal orchestration config. 3 import repoints required (boot_guard is infra-critical — repoint carefully). |
| **Action** | 1) Copy policies version → `general/L5_engines/profile_policy_mode.py`. 2) Repoint 3 imports. 3) Delete both domain copies. |
| **Decision** | `APPROVED` — MOVE to General + RENAME |
| **Executed** | NO |

---

### C005: `validator_engine.py` → RENAME to `crm_validator_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C005 |
| **Duplicate IDs** | D635, D636, D637, D638, D639, D640, D641, D642, D643, D936 |
| **Match Types** | BLOCK, CLASS |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical** | `account/L5_support/CRM/engines/crm_validator_engine.py` (KEEP + RENAME) |
| **Delete Targets** | `policies/L5_engines/validator_engine.py` (repoint 2 callers) |
| **Callers** | account copy: **0 callers**. policies copy: 2 callers — `general/L5_workflow/contracts/engines/contract_engine.py:102`, `general/L4_runtime/engines/__init__.py:113` |
| **V3 Workbook** | Not audited |
| **Owner Correction** | This is NOT policy. `ValidatorService` classifies CRM issues (bug_report, capability_request, escalation), determines severity, extracts affected capabilities via keyword matching, recommends actions. **Advisory only** — never mutates, never enforces. Heuristic classification for customer-facing CRM, not rule governance. |
| **Domain Criteria** | CRM issue classification and advisory = customer interaction = **Account** ("WHO owns what" — specifically, CRM/support sub-domain). NOT Policies (no enforceable rules). NOT General (no runtime orchestration). General consuming it as a cross-domain import proves the boundary is correct — consumer ≠ owner. |
| **Analysis** | MOVE to Account CRM + RENAME. The ambiguous name `validator_engine.py` caused misclassification into policies. Rename to `crm_validator_engine.py` clarifies intent. 2 import repoints required in general (both currently import from policies path). |
| **Action** | 1) Rename account copy → `crm_validator_engine.py`. 2) Repoint 2 imports from policies path → account CRM path. 3) Delete policies copy. |
| **Decision** | `APPROVED` — MOVE to Account CRM + RENAME |
| **Executed** | NO |

---

## Batch 2 (C006–C010) — STATUS: APPROVED

### C006: `utc_now()` in `user_write_driver.py` / `cost_write_driver.py`

| Field | Value |
|-------|-------|
| **ID** | C006 |
| **Duplicate IDs** | D501 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Corrected Canonical** | `general/L5_utils/time.py` (ALREADY EXISTS — 18 importers across 8 domains) |
| **Delete Targets** | Inline `utc_now()` from `account/L6_drivers/user_write_driver.py` + `analytics/L6_drivers/cost_write_driver.py` |
| **Callers** | utc_now is private inline in both files — zero external importers |
| **V3 Workbook** | user_write_driver: CONFIRMED account. cost_write_driver: not in V3 |
| **Domain Criteria** | General: system invariants. Pure datetime utility = General canonical. |
| **Analysis** | CSV framing incorrect — canonical already exists at `general/L5_utils/time.py`. Action is delete inline copies + add import. |
| **Decision** | `APPROVED` |
| **Executed** | NO |

---

### C007: `utc_now()` in `guard_write_driver.py` vs `user_write_driver.py`

| Field | Value |
|-------|-------|
| **ID** | C007 |
| **Duplicate IDs** | D502 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_ACCOUNT |
| **Corrected Canonical** | `general/L5_utils/time.py` (NOT `guard_write_driver.py` — that file is itself a consumer) |
| **Delete Targets** | Inline `utc_now()` from `account/L6_drivers/user_write_driver.py` AND from `general/L5_controls/drivers/guard_write_driver.py` |
| **Callers** | utc_now private inline in both — zero external importers |
| **Domain Criteria** | A driver file is not an appropriate canonical for a utility function. `time.py` is the canonical. |
| **Analysis** | CSV canonical designation incorrect. Delete from account is correct, but guard_write_driver.py also has an inline copy that should be cleaned. |
| **Decision** | `APPROVED` (with corrected canonical) |
| **Executed** | NO |

---

### C008: `utc_now()` in `time.py` vs `user_write_driver.py`

| Field | Value |
|-------|-------|
| **ID** | C008 |
| **Duplicate IDs** | D503 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_ACCOUNT |
| **Canonical** | `general/L5_utils/time.py` (established, 18 importers) |
| **Delete Targets** | Inline `utc_now()` from `account/L6_drivers/user_write_driver.py` |
| **Callers** | Zero external importers of the inline copy |
| **Domain Criteria** | General: system invariants. Cleanest candidate in batch. |
| **Analysis** | Correct as stated. Mechanical change — delete inline, add import. |
| **Decision** | `APPROVED` |
| **Executed** | NO |

---

### C009: `utc_now()` in `user_write_driver.py` / `guard_write_driver.py` (incidents)

| Field | Value |
|-------|-------|
| **ID** | C009 |
| **Duplicate IDs** | D504 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Corrected Canonical** | `general/L5_utils/time.py` (ALREADY EXISTS) |
| **Delete Targets** | Inline `utc_now()` from `account/L6_drivers/user_write_driver.py` + `incidents/L6_drivers/guard_write_driver.py` |
| **Callers** | utc_now private inline — zero external importers |
| **BIGGER ISSUE** | `incidents/L6_drivers/guard_write_driver.py` is a FULL CLASS duplicate of `general/L5_controls/drivers/guard_write_driver.py` (GuardWriteService vs GuardWriteDriver, cosmetic diffs only). 1 caller: `hoc/api/cus/policies/guard.py`. Full file consolidation addressed by C028. |
| **Domain Criteria** | Guard/KillSwitch = governance enforcement = General. Not Incidents (WHETHER an outcome is a problem). |
| **Analysis** | utc_now action is trivial. The real consolidation target is the full guard_write_driver.py class duplicate (C028). |
| **Decision** | `APPROVED` (utc_now cleanup; full file deferred to C028) |
| **Executed** | NO |

---

### C010: `run_governance_facade.py` — 4 copies discovered

| Field | Value |
|-------|-------|
| **ID** | C010 |
| **Duplicate IDs** | D538, D662, D931 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_ACTIVITY |
| **Canonical** | `general/L4_runtime/facades/run_governance_facade.py` |
| **Delete Targets** | `activity/L5_engines/run_governance_facade.py` (Copy 2), `policies/L5_engines/run_governance_facade.py` (Copy 3 — repoint 2 imports) |
| **Deferred** | `app/services/governance/run_governance_facade.py` (Copy 4 — legacy, only copy with live runtime callers. Migration out of P6 scope.) |
| **Callers** | Copy 1 (general): 0 live. Copy 2 (activity): 0 live. Copy 3 (policies): 2 callers in general/L4_runtime. Copy 4 (legacy): 3 callers (worker runner, analytics runner, transaction_coordinator). |
| **V3 Workbook** | activity copy: CONFIRMED activity — "Subject is RUNS." |
| **V3 Override** | YES — V3 classified by subject ("runs"), domain criteria classify by decision authority ("orchestrates WHEN governance fires"). Domain criteria are authoritative. |
| **Domain Criteria** | Facade orchestrates WHEN cross-domain governance operations execute during run lifecycle. This is General L4_runtime (execution timing, ordering, system correctness). NOT Activity (does not record runs). NOT Policies (delegates TO policies, does not own rule logic). |
| **Domain Locks** | All 3 HOC copies domain-locked. Locks allow deletion during documented consolidation. |
| **Analysis** | "Triggered by" ≠ "owns." Facade delegates to Policies (evaluation, lessons) and Logs (audit ACK) but owns none of these — it coordinates WHEN they fire. General/L4_runtime is correct canonical. Fix header to L4 consistently. |
| **Action Plan** | 1) Fix Copy 1 header to L4. 2) Delete Copy 2 (activity). 3) Delete Copy 3 (policies), repoint 2 imports. 4) Defer Copy 4 (legacy). 5) Override V3 with rationale. 6) Update domain locks. |
| **Decision** | `APPROVED` |
| **Executed** | NO |

---

## Batch 3 (C011–C015) — STATUS: APPROVED

> **Meta-rule locked:** Anything that computes or resolves limits, quotas, thresholds, or caps —
> regardless of when it is applied — belongs to **Controls**.

### C011: `run_governance_facade.py` (activity + policies → general)

| Field | Value |
|-------|-------|
| **ID** | C011 |
| **Duplicate IDs** | D539, D663, D932 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical** | `general/L4_runtime/facades/run_governance_facade.py` (already exists) |
| **Delete Targets** | `activity/L5_engines/run_governance_facade.py` (covered by C010), `policies/L5_engines/run_governance_facade.py` (repoint 2 imports) |
| **Callers** | activity copy: only `__init__.py` re-export. policies copy: 2 callers — `general/L4_runtime/engines/__init__.py:133`, `general/L4_runtime/drivers/transaction_coordinator.py:473` |
| **Domain Criteria** | Already ruled in C010: facade orchestrates WHEN governance fires = **General** L4_runtime. "Triggered by" ≠ "owns." |
| **Overlap** | C010 covers activity deletion. C026 covers same policies copy — mark **C026 = SUBSUMED_BY_C011**. |
| **Analysis** | Consolidation of all 3 HOC copies into canonical general/L4_runtime/facades/. Activity deletion via C010. Policies deletion + 2 repoints via this candidate. |
| **Decision** | `APPROVED` |
| **Executed** | NO |

---

### C012: `threshold_engine.py` / `llm_threshold_driver.py` — CSV WRONG

| Field | Value |
|-------|-------|
| **ID** | C012 |
| **Duplicate IDs** | D541, D542, D665–D672 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Corrected Canonical** | `controls/L5_engines/threshold_engine.py` (RELOCATE from activity) |
| **Delete Targets** | `activity/L5_engines/threshold_engine.py` (relocate to controls). Strip redundant L5 logic from `controls/L6_drivers/llm_threshold_driver.py`. |
| **activity/L5_engines/threshold_engine.py** | 709 lines. Pure L5 engine: `ThresholdParams`, `LLMRunThresholdResolver`, `LLMRunEvaluator`, sync variants, `ThresholdSignalRecord`. No SQLAlchemy. Clean layer separation. |
| **controls/L6_drivers/llm_threshold_driver.py** | 823 lines. SUPERSET — contains same L5 business logic PLUS direct SQLAlchemy queries + signal emission. Violates layer separation (L5 logic mixed into L6 driver). |
| **Callers — threshold_engine.py** | `worker/runner.py:562` (LLMRunThresholdResolverSync, LLMRunEvaluatorSync), `api/policy_limits_crud.py:364,443` (ThresholdParams), `controls/L6_drivers/threshold_driver.py:287` (ThresholdParams, ThresholdSignal) |
| **Callers — llm_threshold_driver.py** | Header reference only, no direct import found |
| **V3 Workbook** | llm_threshold_driver.py: "ASSIGN TO: controls (MISPLACED from policies)" |
| **Domain Criteria** | Threshold resolution answers "WHAT limits and configurations apply?" — resolves max_execution_time_ms, max_tokens, max_cost_usd via precedence rules. This is **Controls** ("Owns WHAT limits and configurations apply. Allowed: Thresholds, quotas."). NOT General (not execution timing/ordering). "Used during execution" ≠ "owns execution." Controls constrain execution, they do not orchestrate it. |
| **Analysis** | CSV WRONG — General does not own thresholds. Controls does. Files are NOT exact duplicates — L6 driver is a superset with redundant L5 logic. Correct action is relocate + deduplicate, not extract. |
| **Action** | 1) Relocate `threshold_engine.py` from `activity/L5_engines/` → `controls/L5_engines/threshold_engine.py`. 2) Strip redundant L5 classes from `llm_threshold_driver.py` (keep only DB-specific emission ops). 3) Repoint callers from activity path → controls path. |
| **Decision** | `APPROVED` (CSV overridden — Controls, not General) |
| **Executed** | NO |

---

### C013: `utc_now()` inline cleanup (COLLAPSED: C013 + C014 + C015)

| Field | Value |
|-------|-------|
| **ID** | C013 (absorbs C014, C015) |
| **Duplicate IDs** | D505, D506, D507 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_ANALYTICS (C013, C014), EXTRACT_TO_GENERAL (C015) |
| **Corrected Canonical** | `general/L5_utils/time.py` (ALREADY EXISTS — 19 importers across 8 domains) |
| **Delete Targets** | Inline `utc_now()` from: `general/L5_controls/drivers/guard_write_driver.py:64`, `analytics/L6_drivers/cost_write_driver.py:52`, `incidents/L6_drivers/guard_write_driver.py:66` |
| **Callers** | All inline copies are private module-level helpers — zero external importers. Used only within same file. |
| **Domain Criteria** | Pure datetime utility = General system invariant. Canonical already correct and widely adopted. |
| **Analysis** | Three CSV candidates collapse into one mechanical operation. Canonical exists. Nothing to extract. Delete 3 inline definitions, replace with `from app.hoc.hoc_spine.services.time import utc_now`. L6 drivers importing L5 utils is a legal downward import. |
| **Decision** | `APPROVED` |
| **Executed** | NO |

---

### C014: `utc_now()` in `time.py` vs `cost_write_driver.py`

| Field | Value |
|-------|-------|
| **ID** | C014 |
| **Decision** | `SUBSUMED_BY_C013` |

---

### C015: `utc_now()` in `cost_write_driver.py` / `guard_write_driver.py`

| Field | Value |
|-------|-------|
| **ID** | C015 |
| **Decision** | `SUBSUMED_BY_C013` |

---

## Batch 4 (C016–C020) — STATUS: APPROVED

### C016: `alerts_facade.py` (general canonical, controls duplicate)

| Field | Value |
|-------|-------|
| **ID** | C016 |
| **Duplicate IDs** | D551, D675–D680, D902 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_CONTROLS |
| **Canonical** | `general/L5_engines/alerts_facade.py` (680 lines, `AlertsFacade` — CRUD for alert rules, events, routes) |
| **Delete Targets** | `controls/L5_engines/alerts_facade.py` (677 lines, identical — 0 callers) |
| **Callers** | general copy: 1 — `hoc/api/cus/policies/alerts.py:46`. controls copy: **0 callers**. |
| **Domain Criteria** | Alert rules define thresholds/conditions = arguably Controls ("WHAT limits apply"). However, general copy has the live caller. Pragmatic: delete zero-caller copy. Flag for future domain audit. |
| **Decision** | `APPROVED` — delete controls copy (0 callers). Future audit flag: alert config may belong in Controls. |
| **Executed** | NO |

---

### C017: `circuit_breaker.py` / `circuit_breaker_async.py` — CSV WRONG

| Field | Value |
|-------|-------|
| **ID** | C017 |
| **Duplicate IDs** | D673, D674 |
| **Match Types** | CLASS |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL |
| **Corrected Action** | **KEEP in controls/L6_drivers/** — these are sync/async variants, not cross-domain duplicates |
| **controls/L6_drivers/circuit_breaker.py** | 984 lines. DB-backed `CircuitBreaker` for CostSim V2 auto-disable. PostgreSQL `SELECT FOR UPDATE`. Alertmanager integration. Sync. |
| **controls/L6_drivers/circuit_breaker_async.py** | 1000 lines. Async variant. Same logic, SQLAlchemy async sessions. |
| **Callers** | All use legacy `app.costsim.circuit_breaker` path. No callers import from controls/L6_drivers directly. |
| **Domain Criteria** | Circuit breaker **enforces thresholds** (drift_threshold) to disable/enable CostSim = kill-switch. Per meta-rule: "computes/resolves thresholds → Controls." Controls owns "kill-switches." NOT General. |
| **Decision** | `APPROVED` — KEEP in Controls. Do NOT extract to general. No deletion needed (not cross-domain duplicates). |
| **Executed** | N/A (no action required) |

---

### C018: `llm_threshold_driver.py` / `threshold_driver.py` — CSV WRONG

| Field | Value |
|-------|-------|
| **ID** | C018 |
| **Duplicate IDs** | D543, D544 |
| **Match Types** | FUNCTION |
| **Similarity** | 94.3% (partial) |
| **CSV Recommendation** | REVIEW_MERGE → general |
| **Corrected Action** | **DELETE `llm_threshold_driver.py`**, KEEP `threshold_driver.py` in Controls |
| **controls/L6_drivers/llm_threshold_driver.py** | 823 lines. Layer-violating monolith: L5 business logic (ThresholdParams, LLMRunThresholdResolver, LLMRunEvaluator) + L6 data access + signal emission. **0 live callers.** |
| **controls/L6_drivers/threshold_driver.py** | 381 lines. Proper L6 driver: `ThresholdDriver`/`ThresholdDriverSync` (pure data access) + signal emission. `LimitSnapshot` DTO. No business logic. |
| **Callers — threshold_driver.py** | `worker/runner.py:567`, `hoc/int/analytics/engines/runner.py:567`, `activity/L5_engines/threshold_engine.py:59` |
| **Callers — llm_threshold_driver.py** | **0 live callers** |
| **Overlap** | C012 approved relocating `threshold_engine.py` (L5 logic) to controls. The L5 logic in llm_threshold_driver is the same redundant code. |
| **Domain Criteria** | Threshold = Controls. Both files correctly in controls. llm_threshold_driver is superseded by threshold_driver.py (L6) + threshold_engine.py (L5). |
| **Decision** | `APPROVED` — DELETE `llm_threshold_driver.py` (0 callers, superseded). KEEP `threshold_driver.py` in controls. |
| **Executed** | NO |

---

### C019: `generate_uuid()` in `cross_domain.py` vs `override_driver.py`

| Field | Value |
|-------|-------|
| **ID** | C019 |
| **Duplicate IDs** | D545 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_CONTROLS |
| **Canonical** | `general/L6_drivers/cross_domain.py:67` (`generate_uuid()` — 1-line stdlib wrapper) |
| **Delete Targets** | Inline `generate_uuid()` from `controls/L6_drivers/override_driver.py:59` |
| **Callers** | Both are private file-local utilities. Zero external importers. |
| **Domain Criteria** | Trivial utility. Host files correctly placed (cross_domain → General, override_driver → Controls). |
| **Decision** | `APPROVED` — delete inline from override_driver, import from `general/L6_drivers/cross_domain.py` |
| **Executed** | NO |

---

### C020: `generate_uuid()` / `utc_now()` in `override_driver.py` / `policy_limits_engine.py` — CSV WRONG

| Field | Value |
|-------|-------|
| **ID** | C020 |
| **Duplicate IDs** | D508, D546 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL (target: `general/override_driver.py`) |
| **Corrected Action** | Delete inline utilities, import from existing canonicals. Do NOT create `general/override_driver.py`. |
| **controls/L6_drivers/override_driver.py** | `generate_uuid()` line 59, `utc_now()` line 54. Host: `LimitOverrideService`. |
| **policies/L5_engines/policy_limits_engine.py** | `generate_uuid()` line 83, `utc_now()` line 78. Host: `PolicyLimitsService`. Caller: `hoc/api/cus/policies/policy_limits_crud.py`. |
| **Domain Criteria** | `utc_now()` canonical: `general/L5_utils/time.py`. `generate_uuid()` canonical: `general/L6_drivers/cross_domain.py`. CSV target "general/override_driver.py" is semantically misleading — implies General owns override behavior. Override logic → Controls. |
| **Decision** | `APPROVED` — delete inline `utc_now()` + `generate_uuid()` from both files. Import from existing canonicals. Host files stay in their domains. |
| **Executed** | NO |

---

## Batch 5 (C021–C025) — STATUS: APPROVED

### C021: `generate_uuid()` in `override_driver.py` / `policy_rules_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C021 |
| **Duplicate IDs** | D509, D547 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | EXTRACT_TO_GENERAL (target: `general/override_driver.py`) |
| **Corrected Action** | Delete inline `utc_now()` + `generate_uuid()` from `policies/L5_engines/policy_rules_engine.py`. Import from existing canonicals. |
| **Callers** | override_driver: `hoc/api/cus/policies/override.py`. policy_rules_engine: `hoc/api/cus/policies/policy_rules_crud.py`. Inline utilities are private. |
| **Overlap** | C020 covers override_driver inline cleanup. C021 adds policy_rules_engine cleanup. |
| **Decision** | `SUBSUMED_BY_C020` — same utilities, existing canonicals. No new file. |
| **Executed** | NO |

---

### C022: `constraint_checker.py` (L4_runtime vs L5_engines within general)

| Field | Value |
|-------|-------|
| **ID** | C022 |
| **Duplicate IDs** | D567, D568, D704–D706, D907 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L4_runtime/engines/constraint_checker.py` (310 lines, `InspectionConstraintChecker` — enforces inspection constraints: allow_prompt_logging, allow_pii_capture, etc.) |
| **Delete Targets** | `general/L5_engines/constraint_checker.py` (309 lines, identical, header-only diff) |
| **Callers** | **0 importers** for either copy |
| **Domain Criteria** | Enforces system invariants about what inspection/logging is allowed. General: "system invariants, lifecycle gating." Flag for future Policies relocation audit. |
| **Decision** | `APPROVED` — delete L5_engines copy. Keep L4_runtime canonical. |
| **Executed** | NO |

---

### C023: `governance_orchestrator.py` (general L4 canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C023 |
| **Duplicate IDs** | D707–D716, D914 |
| **Match Types** | BLOCK, CLASS |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L4_runtime/engines/governance_orchestrator.py` (807 lines, `GovernanceOrchestrator` — contract activation, job state machine, execution planning, audit triggering. "Orchestrates only; does not execute jobs.") |
| **Delete Targets** | `policies/L5_engines/governance_orchestrator.py` (807 lines, identical except 1 import line — policies copy has corrected import from Sweep-02A) |
| **Callers** | L4_runtime copy: `general/L4_runtime/engines/__init__.py`. policies copy: **0 importers**. |
| **Domain Criteria** | Decides WHEN to start/track/complete jobs, manages execution ordering = **General** ("execution timing, ordering, system correctness"). |
| **Pre-delete fix** | Canonical line 82: update stale import `from app.hoc.cus.general.L5_engines.contract_engine` → `from app.hoc.cus.general.L4_runtime.engines` (policies copy already has this fix). |
| **Decision** | `APPROVED` — fix stale import in canonical, then delete policies copy. |
| **Executed** | NO |

---

### C024: `phase_status_invariants.py` (general L4 canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C024 |
| **Duplicate IDs** | D569, D570, D717–D720, D924 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L4_runtime/engines/phase_status_invariants.py` (361 lines, `PhaseStatusInvariantChecker` — enforces valid phase-status combinations, blocks invalid transitions) |
| **Delete Targets** | `policies/L5_engines/phase_status_invariants.py` (360 lines, identical, header-only diff) |
| **Callers** | **0 importers** for either copy |
| **Domain Criteria** | Hard-coded system invariants about execution phase validity = **General** ("system invariants, lifecycle gating"). NOT customer-defined policy rules. |
| **Decision** | `APPROVED` — clean delete. 0 importers, no repoints. |
| **Executed** | NO |

---

### C025: `plan_generation_engine.py` (general L4 canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C025 |
| **Duplicate IDs** | D571, D721–D723, D925 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **CSV Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L4_runtime/engines/plan_generation_engine.py` (264 lines, `PlanGenerationEngine` — generates execution plans. Header: "This L4 engine owns PLAN GENERATION logic. L5 runner.py owns only PLAN EXECUTION logic.") |
| **Delete Targets** | `policies/L5_engines/plan_generation_engine.py` (257 lines, identical, header-only diff) |
| **Callers** | L4_runtime copy: `hoc/api/int/agent/main.py`. policies copy: **0 importers**. |
| **Domain Criteria** | Determines execution order and structure = **General** ("Runtime orchestration, execution order"). |
| **Decision** | `APPROVED` — delete policies copy. Canonical has active caller. |
| **Executed** | NO |

---

## Batch 6 (C026–C030) — STATUS: APPROVED

### C026: `run_governance_facade.py` (general L4 canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C026 |
| **Duplicate IDs** | D540, D664, D933 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L4_runtime/facades/run_governance_facade.py` |
| **Delete Targets** | `policies/L5_engines/run_governance_facade.py` |
| **Decision** | `SUBSUMED_BY_C011` |
| **Executed** | NO |

### C027: `utc_now()` in `guard_write_driver.py` vs `time.py` (both general)

| Field | Value |
|-------|-------|
| **ID** | C027 |
| **Duplicate IDs** | D510 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_controls/drivers/guard_write_driver.py` |
| **Delete Targets** | `general/L5_utils/time.py` |
| **Decision** | `REJECT — CSV INVERTED. time.py is canonical (19 importers). Covered by C013.` |
| **Executed** | N/A |

### C028: `guard_write_driver.py` (general canonical, incidents duplicate)

| Field | Value |
|-------|-------|
| **ID** | C028 |
| **Duplicate IDs** | D511, D915 |
| **Match Types** | BLOCK, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INCIDENTS |
| **Canonical** | `general/L5_controls/drivers/guard_write_driver.py` |
| **Delete Targets** | `incidents/L6_drivers/guard_write_driver.py` |
| **Decision** | `APPROVE — delete incidents copy (263 lines). Repoint 1 caller (guard.py), class rename GuardWriteService→GuardWriteDriver.` |
| **Executed** | NO |

### C029: `runtime_switch.py` (L5_controls vs L5_engines within general)

| Field | Value |
|-------|-------|
| **ID** | C029 |
| **Duplicate IDs** | D552–D560, D681, D934 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_controls/drivers/runtime_switch.py` |
| **Delete Targets** | `general/L5_engines/runtime_switch.py` |
| **Decision** | `APPROVE — delete L5_engines copy (276 lines). Repoint 4 callers: step_enforcement, kill_switch_guard, boot_guard, governance_facade.` |
| **Executed** | NO |

### C030: `degraded_mode_checker.py` (L5_controls vs L5_engines within general)

| Field | Value |
|-------|-------|
| **ID** | C030 |
| **Duplicate IDs** | D561–D564, D682–D689, D910 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_controls/engines/degraded_mode_checker.py` |
| **Delete Targets** | `general/L5_engines/degraded_mode_checker.py` |
| **Decision** | `APPROVE — delete L5_engines copy (683 lines). Repoint 1 test. Fix canonical header L4→L5.` |
| **Executed** | NO |

---

## Batch 7 (C031–C035) — STATUS: APPROVED

### C031: `alert_log_linker.py` (general canonical, incidents duplicate)

| Field | Value |
|-------|-------|
| **ID** | C031 |
| **Duplicate IDs** | D597–D601, D778–D783, D901 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INCIDENTS |
| **Canonical** | `general/L5_engines/alert_log_linker.py` |
| **Delete Targets** | `incidents/L5_engines/alert_log_linker.py` |
| **Decision** | `APPROVE — delete incidents copy (758 lines, 0 importers). General owns runtime linking.` |
| **Executed** | NO |

### C032: `audit_durability.py` vs `durability.py` (exact file, both general)

| Field | Value |
|-------|-------|
| **ID** | C032 |
| **Duplicate IDs** | D001, D602, D603, D784–D787 |
| **Match Types** | CLASS, EXACT_FILE, FUNCTION |
| **Similarity** | 100.0% (exact hash) |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_engines/audit_durability.py` |
| **Delete Targets** | `general/L5_engines/durability.py` |
| **Decision** | `APPROVE — delete durability.py (alias, 0 importers). Keep audit_durability.py. FLAG: both orphaned, future dead-code audit.` |
| **Executed** | NO |

### C033: `audit_store.py` (general canonical, logs duplicate)

| Field | Value |
|-------|-------|
| **ID** | C033 |
| **Duplicate IDs** | D604, D607, D788, D791, D794, D904 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_engines/audit_store.py` |
| **Delete Targets** | `logs/L6_drivers/audit_store.py` |
| **Decision** | `APPROVE — delete logs copy (455 lines, 0 importers). FLAG: canonical needs future L5→L6 layer fix + General→Logs domain migration.` |
| **Executed** | NO |

### C034: `audit_store.py` vs `store.py` (general canonical, logs duplicate)

| Field | Value |
|-------|-------|
| **ID** | C034 |
| **Duplicate IDs** | D605, D608, D789, D792, D795 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_engines/audit_store.py` |
| **Delete Targets** | `logs/L6_drivers/store.py` |
| **Decision** | `APPROVE — delete store.py (454 lines, 0 importers). Both orphaned, keep audit_store.py for C033 alignment.` |
| **Executed** | NO |

### C035: `compliance_facade.py` (general canonical, logs duplicate)

| Field | Value |
|-------|-------|
| **ID** | C035 |
| **Duplicate IDs** | D610, D797–D803, D906 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_engines/compliance_facade.py` |
| **Delete Targets** | `logs/L5_engines/compliance_facade.py` |
| **Decision** | `APPROVE — delete logs copy (515 lines, 0 importers). General owns governance execution.` |
| **Executed** | NO |

---

## Batch 8 (C036–C040) — STATUS: APPROVED

### C036: `contract_engine.py` (L5_workflow vs L5_engines within general)

| Field | Value |
|-------|-------|
| **ID** | C036 |
| **Duplicate IDs** | D690–D692, D908 |
| **Match Types** | BLOCK, CLASS |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_workflow/contracts/engines/contract_engine.py` |
| **Delete Targets** | `general/L5_engines/contract_engine.py` |
| **Decision** | `APPROVE — delete L5_engines copy (717 lines). Repoint 6 importers to general.L5_workflow.contracts.engines.contract_engine.` |
| **Executed** | NO |

### C037: `control_registry.py` (general canonical, logs duplicate)

| Field | Value |
|-------|-------|
| **ID** | C037 |
| **Duplicate IDs** | D611, D804–D808, D909 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_engines/control_registry.py` |
| **Delete Targets** | `logs/L5_engines/control_registry.py` |
| **Decision** | `APPROVE — delete logs copy (454 lines, 0 importers). General owns governance control definitions.` |
| **Executed** | NO |

### C038: `cus_credential_service.py` vs `cus_credential_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C038 |
| **Duplicate IDs** | D809 |
| **Match Types** | CLASS |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_engines/cus_credential_service.py` |
| **Delete Targets** | `integrations/L5_vault/engines/cus_credential_engine.py` |
| **Decision** | `APPROVE — delete integrations orphan (480 lines, 0 importers). General owns encryption mechanics.` |
| **Executed** | NO |

### C039: `fatigue_controller.py` (general canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C039 |
| **Duplicate IDs** | D612–D616, D810–D817, D913 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L5_engines/fatigue_controller.py` |
| **Delete Targets** | `policies/L5_engines/fatigue_controller.py` |
| **Decision** | `APPROVE — delete policies copy (749 lines). Fix broken import in controls/alert_fatigue.py.` |
| **Executed** | NO |

### C040: `utc_now()` in `cross_domain.py` vs `knowledge_lifecycle_manager.py` (both general)

| Field | Value |
|-------|-------|
| **ID** | C040 |
| **Duplicate IDs** | D513 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `general/L5_engines/knowledge_lifecycle_manager.py` |
| **Decision** | `APPROVE — delete inline utc_now() from knowledge_lifecycle_manager.py. Canonical = general/L6_drivers/cross_domain.py.` |
| **Executed** | NO |

---

## Batch 9 (C041–C045) — STATUS: APPROVED

### C041: `utc_now()` in `knowledge_lifecycle_manager.py` vs `incident_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C041 |
| **Duplicate IDs** | D518 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INCIDENTS |
| **Canonical** | `general/L5_engines/knowledge_lifecycle_manager.py` |
| **Delete Targets** | `incidents/L5_engines/incident_engine.py` |
| **Decision** | `APPROVE — delete inline utc_now() (line 93-95). Import from general/L5_utils/time.py. CSV canonical wrong (C040 supersedes).` |
| **Executed** | NO |

### C042: `utc_now()` in `knowledge_lifecycle_manager.py` vs `mapper.py` (logs)

| Field | Value |
|-------|-------|
| **ID** | C042 |
| **Duplicate IDs** | D519 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_engines/knowledge_lifecycle_manager.py` |
| **Delete Targets** | `logs/L5_engines/mapper.py` |
| **Decision** | `APPROVE — delete inline utc_now() (line 43-45). Import from general/L5_utils/time.py.` |
| **Executed** | NO |

### C043: `utc_now()` in `knowledge_lifecycle_manager.py` vs `lessons_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C043 |
| **Duplicate IDs** | D520 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L5_engines/knowledge_lifecycle_manager.py` |
| **Delete Targets** | `policies/L5_engines/lessons_engine.py` |
| **Decision** | `APPROVE — delete inline utc_now() (line 85-87). Import from general/L5_utils/time.py. 28 importers unaffected.` |
| **Executed** | NO |

### C044: `utc_now()` in `knowledge_lifecycle_manager.py` vs `mapper.py` (policies)

| Field | Value |
|-------|-------|
| **ID** | C044 |
| **Duplicate IDs** | D521 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L5_engines/knowledge_lifecycle_manager.py` |
| **Delete Targets** | `policies/L5_engines/mapper.py` |
| **Decision** | `APPROVE — delete inline utc_now() (line 43-45). Import from general/L5_utils/time.py.` |
| **Executed** | NO |

### C045: `lifecycle_facade.py` (L5_engines vs L5_engines/lifecycle within general)

| Field | Value |
|-------|-------|
| **ID** | C045 |
| **Duplicate IDs** | D617, D661, D818–D822, D919 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_engines/lifecycle_facade.py` |
| **Delete Targets** | `general/L5_engines/lifecycle/lifecycle_facade.py` |
| **Decision** | `APPROVE — delete subdirectory copy (704 lines, 0 importers). Root L5_engines/lifecycle_facade.py is canonical (2 importers).` |
| **Executed** | NO |

---

## Batch 10 (C046–C050) — STATUS: APPROVED

### C046: `base.py` vs `lifecycle_stages_base.py` (exact file, both general)

| Field | Value |
|-------|-------|
| **ID** | C046 |
| **Duplicate IDs** | D002, D772–D777 |
| **Match Types** | CLASS, EXACT_FILE |
| **Similarity** | 100.0% (exact hash) |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_engines/lifecycle_stages_base.py` |
| **Delete Targets** | `general/L5_lifecycle/engines/base.py` |
| **Decision** | `APPROVE (REVERSED) — delete base.py, keep lifecycle_stages_base.py. Repoint 1 importer (incidents/lifecycle_worker.py). User override: descriptive name preferred.` |
| **Executed** | NO |

### C047: `monitors_facade.py` (general canonical, integrations duplicate)

| Field | Value |
|-------|-------|
| **ID** | C047 |
| **Duplicate IDs** | D618, D823–D829, D922 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_engines/monitors_facade.py` |
| **Delete Targets** | `integrations/L5_engines/monitors_facade.py` |
| **Decision** | `APPROVE — delete integrations copy (538 lines, 0 importers). General owns runtime monitoring.` |
| **Executed** | NO |

### C048: `retrieval_facade.py` (general canonical, integrations duplicate)

| Field | Value |
|-------|-------|
| **ID** | C048 |
| **Duplicate IDs** | D619, D830–D833, D928 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_engines/retrieval_facade.py` |
| **Delete Targets** | `integrations/L5_engines/retrieval_facade.py` |
| **Decision** | `APPROVE — delete integrations copy (520 lines). Repoint 1 caller (policies/retrieval.py) to general.L5_engines.retrieval_facade.` |
| **Executed** | NO |

### C049: `retrieval_mediator.py` (general canonical, integrations duplicate)

| Field | Value |
|-------|-------|
| **ID** | C049 |
| **Duplicate IDs** | D620, D621, D834–D843, D929 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_engines/retrieval_mediator.py` |
| **Delete Targets** | `integrations/L5_engines/retrieval_mediator.py` |
| **Decision** | `APPROVE — delete integrations copy (472 lines). Repoint 3 callers to general.L5_engines.retrieval_mediator.` |
| **Executed** | NO |

### C050: `execution.py` (general L5_lifecycle canonical, integrations duplicate)

| Field | Value |
|-------|-------|
| **ID** | C050 |
| **Duplicate IDs** | D593–D596, D761–D771, D912 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_lifecycle/drivers/execution.py` |
| **Delete Targets** | `integrations/L6_drivers/execution.py` |
| **Decision** | `APPROVE — delete integrations copy (1323 lines, 0 importers). General owns lifecycle execution.` |
| **Executed** | NO |

---

## Batch 11 (C051–C055) — STATUS: APPROVED

### C051: `knowledge_plane.py` (L6_drivers vs L5_lifecycle within general)

| Field | Value |
|-------|-------|
| **ID** | C051 |
| **Duplicate IDs** | D583, D584, D590–D592, D754–D760, D918 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_lifecycle/drivers/knowledge_plane.py` |
| **Delete Targets** | `general/L6_drivers/knowledge_plane.py` |
| **Decision** | `APPROVE (REVERSED) — delete L6_drivers copy, keep L5_lifecycle canonical. Repoint L4 facade. User override: lifecycle location preferred.` |
| **Executed** | NO |

### C052: function duplicate in `knowledge_plane.py` vs `datasource_model.py`

| Field | Value |
|-------|-------|
| **ID** | C052 |
| **Duplicate IDs** | D587 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_lifecycle/drivers/knowledge_plane.py` |
| **Delete Targets** | `integrations/L5_schemas/datasource_model.py` |
| **Decision** | `REJECT — pattern method (record_error) on different domain classes with domain-specific status enums. Not a true duplicate.` |
| **Executed** | N/A |

### C053: function duplicate in `knowledge_plane.py` vs `connector_registry.py`

| Field | Value |
|-------|-------|
| **ID** | C053 |
| **Duplicate IDs** | D588 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_lifecycle/drivers/knowledge_plane.py` |
| **Delete Targets** | `integrations/L6_drivers/connector_registry.py` |
| **Decision** | `REJECT — pattern method on BaseConnector, domain-specific. Same as C052.` |
| **Executed** | N/A |

### C054: function duplicate in `agent.py` vs `artifact.py` (both general schemas)

| Field | Value |
|-------|-------|
| **ID** | C054 |
| **Duplicate IDs** | D574 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_schemas/agent.py` |
| **Delete Targets** | `general/L5_schemas/artifact.py` |
| **Decision** | `REJECT — false positive. No overlapping function between schema files.` |
| **Executed** | N/A |

### C055: function duplicate in `agent.py` vs `plan.py` (both general schemas)

| Field | Value |
|-------|-------|
| **ID** | C055 |
| **Duplicate IDs** | D575 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_schemas/agent.py` |
| **Delete Targets** | `general/L5_schemas/plan.py` |
| **Decision** | `REJECT — false positive. No overlapping function between schema files.` |
| **Executed** | N/A |

---

## Batch 12 (C056–C060) — STATUS: APPROVED

### C056: function duplicate in `artifact.py` vs `plan.py` (both general schemas)

| Field | Value |
|-------|-------|
| **ID** | C056 |
| **Duplicate IDs** | D576 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_GENERAL |
| **Canonical** | `general/L5_utils/time.py` |
| **Delete Targets** | `general/L5_schemas/artifact.py` AND `general/L5_schemas/plan.py` (both inline) |
| **Decision** | `APPROVE (MODIFIED) — delete inline _utc_now() from BOTH artifact.py and plan.py. Import from canonical general/L5_utils/time.py. utc_now sweep.` |
| **Executed** | NO |

### C057: `rac_models.py` vs `audit_models.py` (general vs logs schemas)

| Field | Value |
|-------|-------|
| **ID** | C057 |
| **Duplicate IDs** | D577, D580, D732, D735, D738, D741, D744, D747, D750 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_schemas/rac_models.py` |
| **Delete Targets** | `logs/L5_schemas/audit_models.py` |
| **Decision** | `APPROVE — delete logs audit_models.py (380 lines). Repoint 2 importers (audit_store.py, audit_reconciler.py) to general/L5_schemas/rac_models.py.` |
| **Executed** | NO |

### C058: `rac_models.py` vs `models.py` (general vs logs schemas)

| Field | Value |
|-------|-------|
| **ID** | C058 |
| **Duplicate IDs** | D578, D581, D733, D736, D739, D742, D745, D748, D751 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L5_schemas/rac_models.py` |
| **Delete Targets** | `logs/L5_schemas/models.py` |
| **Decision** | `APPROVE (CAVEAT) — delete RAC-duplicate content from logs models.py. If unique Trace classes exist, split and keep. Repoint RAC importers to general/L5_schemas/rac_models.py.` |
| **Executed** | NO |

### C059: `skill.py` vs `http_connector.py` (general vs integrations)

| Field | Value |
|-------|-------|
| **ID** | C059 |
| **Duplicate IDs** | D753 |
| **Match Types** | CLASS |
| **Similarity** | 70.6% (partial) |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L5_schemas/skill.py` |
| **Delete Targets** | `integrations/L5_engines/http_connector.py` |
| **Decision** | `REJECT — false positive. Pattern enum (HttpMethod) on different layers (schema vs engine). C052/C053 precedent.` |
| **Executed** | N/A |

### C060: `job_executor.py` (general CRM canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C060 |
| **Duplicate IDs** | D572, D573, D724–D731, D917 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L5_support/CRM/engines/job_executor.py` |
| **Delete Targets** | `policies/L5_engines/job_executor.py` |
| **Decision** | `APPROVE — delete policies copy (527 lines, 0 importers). General CRM canonical.` |
| **Executed** | NO |

---

## Batch 13 (C061–C065) — STATUS: APPROVED

### C061: `rollout_projection.py` (general L5_ui canonical, policies duplicate)

| Field | Value |
|-------|-------|
| **ID** | C061 |
| **Duplicate IDs** | D565, D566, D693–D703, D930 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L5_ui/engines/rollout_projection.py` |
| **Delete Targets** | `policies/L5_engines/rollout_projection.py` |
| **Decision** | `APPROVE — delete policies copy (716 lines, 0 importers). General L5_ui canonical.` |
| **Executed** | NO |

### C062: `utc_now()` in `time.py` vs `guard_write_driver.py` (incidents)

| Field | Value |
|-------|-------|
| **ID** | C062 |
| **Duplicate IDs** | D512 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INCIDENTS |
| **Canonical** | `general/L5_utils/time.py` |
| **Delete Targets** | `incidents/L6_drivers/guard_write_driver.py` |
| **Decision** | `APPROVE — delete inline utc_now() from guard_write_driver.py. Import from general/L5_utils/time.py. Covered by C028 scope.` |
| **Executed** | NO |

### C063: `utc_now()` in `cross_domain.py` vs `incident_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C063 |
| **Duplicate IDs** | D514 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INCIDENTS |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `incidents/L5_engines/incident_engine.py` |
| **Decision** | `SUBSUMED_BY_C041 — same file, same inline utc_now(). CSV duplicate entry (different canonical source).` |
| **Executed** | N/A |

### C064: `utc_now()` in `cross_domain.py` vs `mapper.py` (logs)

| Field | Value |
|-------|-------|
| **ID** | C064 |
| **Duplicate IDs** | D515 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_LOGS |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `logs/L5_engines/mapper.py` |
| **Decision** | `SUBSUMED_BY_C042 — same file, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C065: `utc_now()` in `cross_domain.py` vs `lessons_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C065 |
| **Duplicate IDs** | D516 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `policies/L5_engines/lessons_engine.py` |
| **Decision** | `SUBSUMED_BY_C043 — same file, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

---

## Batch 14 (C066–C070) — STATUS: APPROVED

### C066: `utc_now()` in `cross_domain.py` vs `mapper.py` (policies)

| Field | Value |
|-------|-------|
| **ID** | C066 |
| **Duplicate IDs** | D517 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `policies/L5_engines/mapper.py` |
| **Decision** | `SUBSUMED_BY_C044 — same file, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C067: `utc_now()` / `generate_uuid()` in `cross_domain.py` vs `policy_limits_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C067 |
| **Duplicate IDs** | D548 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `policies/L5_engines/policy_limits_engine.py` |
| **Decision** | `APPROVE — delete inline utc_now() (line 78-80) + generate_uuid() (line 83-85). Import from canonicals.` |
| **Executed** | NO |

### C068: `utc_now()` / `generate_uuid()` in `cross_domain.py` vs `policy_rules_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C068 |
| **Duplicate IDs** | D549 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_POLICIES |
| **Canonical** | `general/L6_drivers/cross_domain.py` |
| **Delete Targets** | `policies/L5_engines/policy_rules_engine.py` |
| **Decision** | `APPROVE — delete inline utc_now() (line 79-81) + generate_uuid() (line 84-86). Import from canonicals.` |
| **Executed** | NO |

### C069: function duplicate in `knowledge_plane.py` vs `datasource_model.py`

| Field | Value |
|-------|-------|
| **ID** | C069 |
| **Duplicate IDs** | D585 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L6_drivers/knowledge_plane.py` |
| **Delete Targets** | `integrations/L5_schemas/datasource_model.py` |
| **Decision** | `SUBSUMED_BY_C052 — same pattern method (record_error). Already REJECTED.` |
| **Executed** | N/A |

### C070: function duplicate in `knowledge_plane.py` vs `connector_registry.py`

| Field | Value |
|-------|-------|
| **ID** | C070 |
| **Duplicate IDs** | D586 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | DELETE_FROM_INTEGRATIONS |
| **Canonical** | `general/L6_drivers/knowledge_plane.py` |
| **Delete Targets** | `integrations/L6_drivers/connector_registry.py` |
| **Decision** | `SUBSUMED_BY_C053 — same pattern method (record_error). Already REJECTED.` |
| **Executed** | N/A |

---

## Batch 15 (C071–C075) — STATUS: APPROVED

### C071: `hallucination_detector.py` (incidents + policies → general)

| Field | Value |
|-------|-------|
| **ID** | C071 |
| **Duplicate IDs** | D622, D844–D849, D916 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/hallucination_detector.py` |
| **Delete Targets** | `policies/L5_engines/hallucination_detector.py` |
| **Decision** | `APPROVE (USER OVERRIDE) — Incidents is canonical (customer-facing WHEN/HOW = domain boundary, not General). Delete policies copy. Keep incidents/L5_engines/hallucination_detector.py. Protocol rule #9 added.` |
| **Executed** | NO |

### C072: `utc_now()` in `incident_engine.py` vs `mapper.py` (logs)

| Field | Value |
|-------|-------|
| **ID** | C072 |
| **Duplicate IDs** | D522 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/incident_engine.py` |
| **Delete Targets** | `incidents/L5_engines/incident_engine.py`, `logs/L5_engines/mapper.py` |
| **Decision** | `SUBSUMED_BY_C041+C042 — same files, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C073: `utc_now()` in `incident_engine.py` vs `lessons_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C073 |
| **Duplicate IDs** | D523 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/incident_engine.py` |
| **Delete Targets** | `incidents/L5_engines/incident_engine.py`, `policies/L5_engines/lessons_engine.py` |
| **Decision** | `SUBSUMED_BY_C041+C043 — same files, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C074: `utc_now()` in `incident_engine.py` vs `mapper.py` (policies)

| Field | Value |
|-------|-------|
| **ID** | C074 |
| **Duplicate IDs** | D524 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/incident_engine.py` |
| **Delete Targets** | `incidents/L5_engines/incident_engine.py`, `policies/L5_engines/mapper.py` |
| **Decision** | `SUBSUMED_BY_C041+C044 — same files, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C075: `notifications_base.py` vs `notifications_facade.py` (both integrations)

| Field | Value |
|-------|-------|
| **ID** | C075 |
| **Duplicate IDs** | D650, D653 |
| **Match Types** | CLASS |
| **Similarity** | 83.3% (partial) |
| **Recommendation** | REVIEW_MERGE |
| **Canonical Target** | `general/notifications_base.py` |
| **Delete Targets** | `integrations/L3_adapters/notifications_base.py`, `integrations/L5_engines/notifications_facade.py` |
| **Decision** | `APPROVE (USER OVERRIDE) — Account is canonical for notifications_facade.py. Delete integrations/L5_engines/notifications_facade.py. Delete integrations/L3_adapters/notifications_base.py. Keep account/L5_engines/notifications_facade.py.` |
| **Executed** | NO |

---

## Batch 16 (C076–C080) — STATUS: APPROVED

### C076: `channel_engine.py` (integrations notifications + engines → general)

| Field | Value |
|-------|-------|
| **ID** | C076 |
| **Duplicate IDs** | D623–D627, D852–D860, D905 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/channel_engine.py` |
| **Delete Targets** | `integrations/L5_engines/channel_engine.py` |
| **Decision** | `APPROVE (USER OVERRIDE) — Integrations is canonical. Keep L5_notifications/engines/channel_engine.py. Delete L5_engines copy. NOT General.` |
| **Executed** | NO |

### C077: `mcp_connector.py` (integrations + policies → general)

| Field | Value |
|-------|-------|
| **ID** | C077 |
| **Duplicate IDs** | D861–D867, D921 |
| **Match Types** | BLOCK, CLASS |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/mcp_connector.py` |
| **Delete Targets** | `policies/L5_engines/mcp_connector.py` |
| **Decision** | `APPROVE (CSV WRONG) — Integrations is canonical. Delete policies copy only. MCP = HOW external systems connect = Integrations domain.` |
| **Executed** | NO |

### C078: `service.py` (integrations vault + engines → general)

| Field | Value |
|-------|-------|
| **ID** | C078 |
| **Duplicate IDs** | D850, D851, D935 |
| **Match Types** | BLOCK, CLASS |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/service.py` |
| **Delete Targets** | `integrations/L5_engines/service.py` |
| **Decision** | `APPROVE — keep L5_vault/engines/service.py (semantically correct path). Delete L5_engines copy. Stay in Integrations.` |
| **Executed** | NO |

### C079: function duplicate in `datasource_model.py` / `connector_registry.py`

| Field | Value |
|-------|-------|
| **ID** | C079 |
| **Duplicate IDs** | D589 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/datasource_model.py` |
| **Delete Targets** | `integrations/L5_schemas/datasource_model.py`, `integrations/L6_drivers/connector_registry.py` |
| **Decision** | `REJECT — pattern infrastructure (_reset_registry) on different domain classes. C052/C053 precedent.` |
| **Executed** | N/A |

### C080: `audit_engine.py` (logs CRM + engines → general)

| Field | Value |
|-------|-------|
| **ID** | C080 |
| **Duplicate IDs** | D628, D629, D868–D874, D903 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/audit_engine.py` |
| **Delete Targets** | `logs/L5_engines/audit_engine.py` |
| **Decision** | `APPROVE — Logs canonical (customer-facing audit verification per C071 ruling). Keep L5_support/CRM/engines/audit_engine.py. Delete L5_engines copy.` |
| **Executed** | NO |

---

## Batch 17 (C081–C085) — STATUS: APPROVED

### C081: function duplicate in `job_execution.py` / `audit_evidence.py` (logs)

| Field | Value |
|-------|-------|
| **ID** | C081 |
| **Duplicate IDs** | D630 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/job_execution.py` |
| **Delete Targets** | `logs/L6_drivers/job_execution.py`, `logs/L5_engines/audit_evidence.py` |
| **Decision** | `REJECT — false positive. Shared _hash_value() utility across L6 driver and L5 engine. Different classes, different purposes.` |
| **Executed** | N/A |

### C082: `audit_reconciler.py` / `reconciler.py` (logs)

| Field | Value |
|-------|-------|
| **ID** | C082 |
| **Duplicate IDs** | D631, D875 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/audit_reconciler.py` |
| **Delete Targets** | `logs/L5_engines/reconciler.py` |
| **Decision** | `APPROVE — Logs canonical = audit_reconciler.py (HOC-native). Delete reconciler.py (legacy app.services import). Repoint 3 importers.` |
| **Executed** | NO |

### C083: `completeness_checker.py` / `export_completeness_checker.py` (logs)

| Field | Value |
|-------|-------|
| **ID** | C083 |
| **Duplicate IDs** | D632, D633, D876–D879 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/completeness_checker.py` |
| **Delete Targets** | `logs/L5_engines/export_completeness_checker.py` |
| **Decision** | `APPROVE — delete alias (518 lines, byte-identical). Keep completeness_checker.py.` |
| **Executed** | NO |

### C084: `utc_now()` in `mapper.py` (logs) vs `lessons_engine.py` (policies)

| Field | Value |
|-------|-------|
| **ID** | C084 |
| **Duplicate IDs** | D525 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/mapper.py` |
| **Delete Targets** | `logs/L5_engines/mapper.py`, `policies/L5_engines/lessons_engine.py` |
| **Decision** | `SUBSUMED_BY_C042+C043 — same files, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C085: `mapper.py` (logs + policies → general)

| Field | Value |
|-------|-------|
| **ID** | C085 |
| **Duplicate IDs** | D526, D634, D880, D920 |
| **Match Types** | BLOCK, CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/mapper.py` |
| **Delete Targets** | `policies/L5_engines/mapper.py` |
| **Decision** | `APPROVE — Logs canonical (recording domain owns SOC2 mapping). Delete policies copy. Repoint policies importers to logs.` |
| **Executed** | NO |

---

## Batch 18 (C086–C090) — STATUS: APPROVED

### C086: `replay_determinism.py` (logs + policies → general)

| Field | Value |
|-------|-------|
| **ID** | C086 |
| **Duplicate IDs** | D881–D888, D927 |
| **Match Types** | BLOCK, CLASS |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/replay_determinism.py` |
| **Delete Targets** | `policies/L5_engines/replay_determinism.py` |
| **Decision** | `APPROVE — Logs canonical (owns replay definitions, marked "CANONICAL DEFINITIONS"). Delete policies copy. Repoint policies importers.` |
| **Executed** | NO |

### C087: `audit_models.py` / `models.py` (logs schemas → general)

| Field | Value |
|-------|-------|
| **ID** | C087 |
| **Duplicate IDs** | D579, D582, D734, D737, D740, D743, D746, D749, D752 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/audit_models.py` |
| **Delete Targets** | `logs/L5_schemas/audit_models.py`, `logs/L5_schemas/models.py` |
| **Decision** | `SUBSUMED_BY_C057+C058 — already approved for these files.` |
| **Executed** | N/A |

### C088: `audit_store.py` / `store.py` (logs drivers → general)

| Field | Value |
|-------|-------|
| **ID** | C088 |
| **Duplicate IDs** | D606, D609, D790, D793, D796 |
| **Match Types** | CLASS, FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/audit_store.py` |
| **Delete Targets** | `logs/L6_drivers/audit_store.py`, `logs/L6_drivers/store.py` |
| **Decision** | `SUBSUMED_BY_C033+C034 — already approved for these files.` |
| **Executed** | N/A |

### C089: `utc_now()` in `lessons_engine.py` vs `mapper.py` (both policies)

| Field | Value |
|-------|-------|
| **ID** | C089 |
| **Duplicate IDs** | D527 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/lessons_engine.py` |
| **Delete Targets** | `policies/L5_engines/lessons_engine.py`, `policies/L5_engines/mapper.py` |
| **Decision** | `SUBSUMED_BY_C043+C044 — same files, same inline utc_now(). CSV duplicate entry.` |
| **Executed** | N/A |

### C090: `utc_now()` / `generate_uuid()` in `policy_limits_engine.py` vs `policy_rules_engine.py`

| Field | Value |
|-------|-------|
| **ID** | C090 |
| **Duplicate IDs** | D528, D550 |
| **Match Types** | FUNCTION |
| **Similarity** | 100.0% |
| **Recommendation** | EXTRACT_TO_GENERAL |
| **Canonical Target** | `general/policy_limits_engine.py` |
| **Delete Targets** | `policies/L5_engines/policy_limits_engine.py`, `policies/L5_engines/policy_rules_engine.py` |
| **Decision** | `SUBSUMED_BY_C067+C068 — same files, same inline utilities. CSV duplicate entry.` |
| **Executed** | N/A |

---

## Execution Log

*Actions will be logged here as batches are approved and executed.*

| Batch | Date | Candidates | Approved | Rejected | Deferred | Files Deleted | Imports Repointed |
|-------|------|-----------|----------|----------|----------|---------------|-------------------|
| 1 | 2026-01-27 | C001–C005 | 4 (C001,C003,C004,C005) | 1 (C002) | 0 | 0 | 0 | RE-ANALYZED with domain criteria. C004: General+rename. C005: Account+rename. |
| 2 | 2026-01-27 | C006–C010 | 5 (C006,C007,C008,C009,C010) | 0 | 0 | 0 | 0 |
| 3 | 2026-01-27 | C011–C015 | 3 (C011,C012,C013) | 0 | 0 | 0 | 0 | C012: Controls not General. C014,C015 subsumed by C013. C026 subsumed by C011. |
| 4 | 2026-01-27 | C016–C020 | 5 (C016,C017,C018,C019,C020) | 0 | 0 | 0 | 0 | C017: KEEP in Controls (not General). C018: DELETE monolith. C020: no new file, import existing canonicals. |
| 5 | 2026-01-27 | C021–C025 | 4 (C022,C023,C024,C025) | 0 | 0 | 0 | 0 | C021 subsumed by C020. C023: fix stale import before delete. |
| 6 | 2026-01-27 | C026–C030 | 3 (C028,C029,C030) | 1 (C027) | 0 | 0 | 0 | C026 subsumed by C011. C027 REJECT (CSV inverted). |
| 7 | 2026-01-27 | C031–C035 | 5 (C031-C035) | 0 | 0 | 0 | 0 | All 0-importer deletes. C032/C033 flagged for future audit. |
| 8 | 2026-01-27 | C036–C040 | 5 (C036-C040) | 0 | 0 | 0 | 0 | C036: 6 repoints. C039: fix broken import. |
| 9 | 2026-01-27 | C041–C045 | 5 (C041-C045) | 0 | 0 | 0 | 0 | C041-C044: utc_now sweep. C045: subdirectory copy. |
| 10 | 2026-01-27 | C046–C050 | 5 (C046-C050) | 0 | 0 | 0 | 0 | C046: REVERSED (keep lifecycle_stages_base). C048-C049: repoints needed. |
| 11 | 2026-01-27 | C051–C055 | 1 (C051) | 4 (C052-C055) | 0 | 0 | 0 | C051: REVERSED (keep L5_lifecycle). C052-C055: pattern/false positives. |
| 12 | 2026-01-27 | C056–C060 | 4 (C056-C058,C060) | 1 (C059) | 0 | 0 | 0 | C056: utc_now from both files. C059: pattern enum. |
| 13 | 2026-01-27 | C061–C065 | 2 (C061,C062) | 0 | 0 | 0 | 0 | C063-C065 subsumed. |
| 14 | 2026-01-27 | C066–C070 | 2 (C067,C068) | 0 | 0 | 0 | 0 | C066,C069,C070 subsumed. |
| 15 | 2026-01-27 | C071–C075 | 2 (C071,C075) | 0 | 0 | 0 | 0 | C071: incidents canonical (user override). C075: account canonical (user override). Protocol rule #9 added. |
| 16 | 2026-01-27 | C076–C080 | 4 (C076-C078,C080) | 1 (C079) | 0 | 0 | 0 | C076: integrations canonical (user override). C077: CSV wrong, integrations not general. |
| 17 | 2026-01-27 | C081–C085 | 3 (C082,C083,C085) | 1 (C081) | 0 | 0 | 0 | C081: false positive. C084 subsumed. |
| 18 | 2026-01-27 | C086–C090 | 1 (C086) | 0 | 0 | 0 | 0 | C087-C090 subsumed by earlier decisions. |

---

## Cross-Reference Index

### By Source Domain (files to be deleted FROM)

| Domain | Candidates | Count |
|--------|-----------|-------|
| general (internal dedup) | C022, C027, C029, C030, C032, C036, C040, C045, C046, C051, C054, C055, C056 | 13 |
| policies | C004, C005, C023, C024, C025, C026, C039, C043, C044, C060, C061, C065, C066, C067, C068, C089, C090 | 17 |
| logs | C033, C034, C035, C037, C042, C057, C058, C064, C080, C081, C082, C083, C084, C085, C087, C088 | 16 |
| integrations | C038, C047, C048, C049, C050, C052, C053, C059, C069, C070, C076, C077, C078, C079 | 14 |
| account | C001, C003, C007, C008 | 4 |
| incidents | C028, C031, C041, C062, C063 | 5 |
| activity | C010, C011, C012 | 3 |
| analytics | C013, C014, C015 | 3 |
| controls | C016, C019 | 2 |
| api_keys | C001 | 1 |

### REVIEW_MERGE Candidates (require manual inspection)

| ID | Similarity | Files | Risk |
|----|-----------|-------|------|
| C002 | 83.3% | `notifications_facade.py` vs `notifications_base.py` | RISKY — L5/L3 layer mismatch |
| C018 | 94.3% | `llm_threshold_driver.py` vs `threshold_driver.py` | MEDIUM — near-identical functions |
| C059 | 70.6% | `skill.py` vs `http_connector.py` | MEDIUM — partial class overlap |
| C075 | 83.3% | `notifications_base.py` vs `notifications_facade.py` | RISKY — L3/L5 layer mismatch |

---

*Workbook generated: 2026-01-27*
*Reference: PIN-470, PIN-479, V3_MANUAL_AUDIT_WORKBOOK.md*
