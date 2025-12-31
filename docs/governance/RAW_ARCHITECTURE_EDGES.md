# RAW_ARCHITECTURE_EDGES.md

**Status:** REFINED (v2)
**Created:** 2025-12-31
**Refined:** 2025-12-31
**Method:** Derived from import statements, function calls, Phase A-D evidence
**Reference:** RAW_ARCHITECTURE_NODES.md (v2)

---

## Refinement Log

| Version | Change | Reason |
|---------|--------|--------|
| v1 | Initial extraction | 63 edges from imports |
| v2 | Added Container → Transaction edges | Entry split required new edge type |
| v2 | Processor → External expanded | External nodes now concrete |
| v2 | Observer edges differentiated | Telemetry ≠ governance control |
| v2 | Scheduler edges annotated | Trigger semantics now explicit |

---

## Extraction Rules Applied

- Edges derived ONLY from: import statements, function signatures, Phase A-D findings
- NO inferred connections
- NO "probably calls" relationships
- Each edge has evidence

---

## ACTOR → ENTRY CONTAINER Edges

| From Node | To Node | Interaction Type | Evidence |
|-----------|---------|------------------|----------|
| ACTOR-001 (Human) | ENTRY-CONTAINER-002 (guard.py) | HTTP via Guard Console | Phase D F1 |
| ACTOR-001 (Human) | ENTRY-CONTAINER-003 (ops.py) | HTTP via Founder Console | Phase D F1 |
| ACTOR-001 (Human) | ENTRY-CONTAINER-005 (founder_actions.py) | HTTP via Founder Console | Phase D F1 |
| ACTOR-002 (SDK Client) | ENTRY-CONTAINER-001 (agents.py) | HTTP request | SDK documentation |
| ACTOR-002 (SDK Client) | ENTRY-CONTAINER-004 (recovery.py) | HTTP request | Machine token auth |
| ACTOR-002 (SDK Client) | ENTRY-CONTAINER-012 (v1_proxy.py) | HTTP request | LLM proxy |
| ACTOR-003 (Scheduler) | SCHED-001 (failure_aggregation) | Process invocation | systemd/cron |
| ACTOR-003 (Scheduler) | SCHED-002 (graduation_evaluator) | Process invocation | systemd/cron |
| ACTOR-003 (Scheduler) | SCHED-003 (cost_snapshots) | Process invocation | systemd/cron |

---

## ENTRY CONTAINER → TRANSACTIONAL ENTRY Edges

These show which containers host which atomic transactions.

| Container | Transactions | Count |
|-----------|--------------|-------|
| ENTRY-CONTAINER-001 (agents.py) | TXENTRY-001 to TXENTRY-010 | 10 |
| ENTRY-CONTAINER-002 (guard.py) | TXENTRY-011 to TXENTRY-017 | 7 |
| ENTRY-CONTAINER-004 (recovery.py) | TXENTRY-018 to TXENTRY-023 | 6 |
| ENTRY-CONTAINER-005 (founder_actions.py) | TXENTRY-024 to TXENTRY-030 | 7 |
| ENTRY-CONTAINER-006 (v1_killswitch.py) | TXENTRY-031 to TXENTRY-035 | 5 |
| ENTRY-CONTAINER-007 (costsim.py) | TXENTRY-036 to TXENTRY-038 | 3 |
| ENTRY-CONTAINER-008 (onboarding.py) | TXENTRY-039 to TXENTRY-044 | 6 |
| ENTRY-CONTAINER-009 (memory_pins.py) | TXENTRY-045 to TXENTRY-046 | 2 |
| ENTRY-CONTAINER-010 (workers.py) | TXENTRY-047 to TXENTRY-049 | 3 |
| ENTRY-CONTAINER-011 (rbac_api.py) | TXENTRY-050 | 1 |
| ENTRY-CONTAINER-012 (v1_proxy.py) | TXENTRY-051 to TXENTRY-052 | 2 |

---

## TRANSACTIONAL ENTRY → PROCESSOR Edges

| From Transaction | To Node | Interaction Type | Evidence |
|------------------|---------|------------------|----------|
| TXENTRY-001 (POST /jobs) | WORK-001 (runner.py) | Job submission | agents.py imports worker.* |
| TXENTRY-011 (killswitch/activate) | PROC-007 (guard_write_service) | Write delegation | guard.py imports |
| TXENTRY-012 (killswitch/deactivate) | PROC-007 (guard_write_service) | Write delegation | guard.py imports |
| TXENTRY-013 (incidents/acknowledge) | PROC-007 (guard_write_service) | Write delegation | guard.py imports |
| TXENTRY-014 (incidents/resolve) | PROC-007 (guard_write_service) | Write delegation | guard.py imports |
| TXENTRY-015 (replay) | PROC-011 (replay_determinism) | Service call | guard.py imports |
| TXENTRY-016 (keys/freeze) | PROC-010 (certificate.py) | Service call | guard.py imports |
| TXENTRY-017 (keys/unfreeze) | PROC-010 (certificate.py) | Service call | guard.py imports |
| TXENTRY-018 (recovery/suggest) | PROC-006 (recovery_matcher) | Match request | recovery.py imports |
| TXENTRY-019 (candidates/PATCH) | PROC-008 (recovery_write_service) | Write delegation | recovery.py imports |
| TXENTRY-020 (recovery/approve) | PROC-008 (recovery_write_service) | Write delegation | recovery.py imports |
| TXENTRY-024 (freeze-tenant) | PROC-007 (guard_write_service) | Write delegation | founder_actions imports |
| TXENTRY-025 (throttle-tenant) | PROC-009 (ops_write_service) | Write delegation | founder_actions imports |
| TXENTRY-036 (costsim/simulate) | ADAPT-002 (v2_adapter) | Adapter call | costsim.py imports |
| TXENTRY-051 (chat/completions) | ADAPT-001 (openai_adapter) | LLM delegation | v1_proxy imports |

---

## PROCESSOR → PROCESSOR Edges (Domain Delegation)

These are the critical authority delegation edges verified in Phase A-D.

| From Node | To Node | Interaction Type | Evidence |
|-----------|---------|------------------|----------|
| WORK-003 (recovery_evaluator) | PROC-001 (recovery_rule_engine) | Domain delegation | Phase A: SHADOW-001 fix |
| SCHED-001 (failure_aggregation) | PROC-001 (recovery_rule_engine) | Domain delegation | Phase A: SHADOW-002, SHADOW-003 fix |
| SCHED-001 (failure_aggregation) | PROC-012 (incident_aggregator) | Batch processing | Job imports |
| WORK-006 (simulate.py) | PROC-002 (cost_model_engine) | Cost calculation | Phase B: B02 fix |
| ADAPT-002 (v2_adapter) | PROC-002 (cost_model_engine) | Cost delegation | Phase B: B02 fix |
| ADAPT-001 (openai_adapter) | PROC-003 (llm_policy_engine) | Safety check | Phase B: B01 fix |
| WORK-001 (runner.py) | PROC-004 (rbac_engine) | Auth check | Auth middleware |
| WORK-004 (recovery_claim_worker) | PROC-006 (recovery_matcher) | Match request | Worker imports |
| WORK-004 (recovery_claim_worker) | PROC-008 (recovery_write_service) | Write delegation | Worker imports |
| WORK-005 (outbox_processor) | PROC-013 (event_emitter) | Event emission | Worker imports |
| PROC-012 (incident_aggregator) | PROC-001 (recovery_rule_engine) | Classification | Phase A evidence |
| SCHED-002 (graduation_evaluator) | PROC-005 (policy_engine) | Graduation eval | Job imports |
| SCHED-003 (cost_snapshots) | PROC-002 (cost_model_engine) | Cost query | Job imports |

---

## PROCESSOR → STORE Edges

| From Node | To Node | Interaction Type | Evidence |
|-----------|---------|------------------|----------|
| PROC-007 (guard_write_service) | STORE-001 (PostgreSQL) | Write | Service imports db |
| PROC-007 (guard_write_service) | STORE-003 (killswitch model) | ORM write | Service imports models |
| PROC-008 (recovery_write_service) | STORE-001 (PostgreSQL) | Write | Service imports db |
| PROC-008 (recovery_write_service) | STORE-006 (recovery model) | ORM write | Service imports models |
| PROC-009 (ops_write_service) | STORE-001 (PostgreSQL) | Write | Service imports db |
| PROC-010 (certificate.py) | STORE-001 (PostgreSQL) | Write | Service imports db |
| PROC-011 (replay_determinism) | STORE-001 (PostgreSQL) | Read/Write | Service imports db |
| PROC-011 (replay_determinism) | STORE-004 (trace model) | ORM read | Service imports models |
| PROC-006 (recovery_matcher) | STORE-001 (PostgreSQL) | Read | Service imports db |
| PROC-005 (policy_engine) | STORE-001 (PostgreSQL) | Read/Write | Engine imports sqlalchemy |
| PROC-005 (policy_engine) | STORE-005 (policy model) | ORM ops | Engine imports models |
| WORK-001 (runner.py) | STORE-001 (PostgreSQL) | Write | Worker imports db |
| WORK-001 (runner.py) | STORE-004 (trace model) | ORM write | Worker writes traces |
| WORK-005 (outbox_processor) | STORE-001 (PostgreSQL) | Read/Write | Outbox pattern |
| SCHED-001 (failure_aggregation) | STORE-001 (PostgreSQL) | Read/Write | Job imports db |
| SCHED-003 (cost_snapshots) | STORE-001 (PostgreSQL) | Write | Job imports db |

---

## PROCESSOR → EXTERNAL Edges (Expanded)

| From Node | To External | Interaction Type | Read/Write | Evidence |
|-----------|-------------|------------------|------------|----------|
| ADAPT-001 (openai_adapter) | EXT-001 (OpenAI API) | HTTP call | READ | `from openai import OpenAI` |
| ADAPT-003 (anthropic_adapter) | EXT-002 (Anthropic API) | HTTP call | READ | `import anthropic` |
| PROC-006 (recovery_matcher) | EXT-003 (VoyageAI) | HTTP call | READ | httpx calls |
| vault_client.py | EXT-004 (HashiCorp Vault) | HTTP call | READ | vault_client imports |
| oauth_providers.py | EXT-005 (Identity Providers) | OAuth flow | READ | httpx calls |
| clerk_provider.py | EXT-005 (Identity Providers) | HTTP call | READ | httpx calls |
| oidc_provider.py | EXT-005 (Identity Providers) | HTTP call | READ | httpx calls |
| WORK-005 (outbox_processor) | EXT-006 (Webhooks) | HTTP call | WRITE | outbox_processor imports |
| webhook_send.py | EXT-006 (Webhooks) | HTTP call | WRITE | httpx imports |
| ADAPT-004 (nats_adapter) | EXT-007 (NATS Server) | Message publish | WRITE | nats imports |
| slack_send.py | EXT-008 (Slack API) | HTTP call | WRITE | httpx imports |
| email_send.py | EXT-009 (Email Provider) | HTTP/SMTP | WRITE | httpx imports |
| email_verification.py | EXT-009 (Email Provider) | HTTP/SMTP | WRITE | httpx imports |
| v1_proxy.py | EXT-001 (OpenAI API) | HTTP call | READ | openai imports |
| llm_invoke.py | EXT-001 (OpenAI API) | HTTP call | READ | openai imports |
| llm_invoke.py | EXT-002 (Anthropic API) | HTTP call | READ | anthropic imports |
| claude_adapter.py | EXT-002 (Anthropic API) | HTTP call | READ | anthropic imports |

---

## OBSERVER EDGES (Differentiated)

### Telemetry Edges (Passive Observation)

These edges represent data flow for monitoring. **No control authority.**

| From Node | To Observer | Interaction Type | Evidence |
|-----------|-------------|------------------|----------|
| STORE-001 (PostgreSQL) | OBS-003 (Prometheus) | Metrics scrape | monitoring/ config |
| All ENTRY nodes | OBS-003 (Prometheus) | Request metrics | workflow/metrics.py |
| All Workers | OBS-003 (Prometheus) | Worker metrics | workflow/metrics.py |
| OBS-003 (Prometheus) | OBS-004 (Alertmanager) | Alert trigger | alertmanager.yml |
| OBS-004 (Alertmanager) | EXT-008 (Slack) | Notification | alertmanager.yml |
| OBS-004 (Alertmanager) | EXT-009 (Email) | Notification | alertmanager.yml |

### Governance Control Edges (Can Halt Work)

These edges represent control flow. **Has authority to BLOCK.**

| From Observer | Observes | Control Authority | Evidence |
|---------------|----------|-------------------|----------|
| OBS-001 (BLCA) | All code files | BLOCK code changes | SESSION_PLAYBOOK Section 28-29 |
| OBS-001 (BLCA) | All architecture artifacts | BLOCK PR merge | BIDIRECTIONAL_AUDIT_STATUS.md |
| OBS-001 (BLCA) | Session state | BLOCK session work | Section 29 ACK requirement |
| OBS-002 (CI Pipeline) | Code changes | BLOCK PR merge (Tier 1) | .github/workflows/*.yml |
| OBS-002 (CI Pipeline) | Code changes | WARN (Tier 2) | PIN-255 three-tier model |

---

## SCHEDULER EDGES (With Trigger Semantics)

| Scheduler | Calls | Trigger Type | Can Fire Without Human | Evidence |
|-----------|-------|--------------|----------------------|----------|
| SCHED-001 (failure_aggregation) | PROC-012 (incident_aggregator) | TIME-BASED | YES | systemd timer |
| SCHED-001 (failure_aggregation) | PROC-001 (recovery_rule_engine) | TIME-BASED | YES | Phase A evidence |
| SCHED-002 (graduation_evaluator) | PROC-005 (policy_engine) | TIME-BASED | YES | systemd timer |
| SCHED-003 (cost_snapshots) | PROC-002 (cost_model_engine) | TIME-BASED | YES | systemd timer |

**Governance Note:** All schedulers can fire without human intent. This is acceptable because:
- They delegate domain decisions to L4 engines (verified in Phase A)
- They do not make authority decisions themselves

---

## Phase A-D Verified Critical Paths

These edges were specifically verified during Layered Semantic Completion:

### Phase A: L5 → L4 Delegation (Shadow Logic Fixes)

| Path | Before | After | Evidence |
|------|--------|-------|----------|
| recovery_evaluator → ? | Hardcoded `confidence >= 0.8` | → recovery_rule_engine.should_auto_execute() | SHADOW-001 |
| failure_aggregation → ? | Hardcoded category heuristics | → recovery_rule_engine.classify_error_category() | SHADOW-002 |
| failure_aggregation → ? | Hardcoded recovery mode heuristics | → recovery_rule_engine.suggest_recovery_mode() | SHADOW-003 |

### Phase B: L3 → L4 Delegation (Translation Fixes)

| Path | Before | After | Evidence |
|------|--------|-------|----------|
| openai_adapter → ? | Safety limits in adapter | → llm_policy_engine.check_safety_limits() | B01 |
| v2_adapter → ? | Cost modeling in adapter | → cost_model_engine.estimate_step_cost() | B02 |
| ClerkAuthProvider → ? | Role mapping in provider | → rbac_engine.get_max_approval_level() | B03 |
| OIDCProvider → ? | Role extraction in provider | → rbac_engine.map_external_roles_to_aos() | B04 |
| TenantLLMConfig → ? | Model selection in config | → llm_policy_engine.get_effective_model() | B05 |

### Phase C: L2 API Truthfulness

| API | Issue | Fix | Evidence |
|-----|-------|-----|----------|
| ops.py (detect-silent-churn) | Decorative (no execution) | Removed | C01 |
| ops.py (compute-stickiness) | Decorative (no execution) | Removed | C02 |
| customer_visibility.py | Partial truth (methodology hidden) | Added EstimationMethodology | C03 |
| ops.py (revenue) | Partial truth (basis hidden) | Added EstimationBasis | C04 |
| costsim.py (simulate) | Implicit side-effect | Added SideEffectDisclosure | C05 |

### Phase D: L1 → L2 Transaction Mapping

| Frontend Entry | Calls API | Authority Check | Evidence |
|----------------|-----------|-----------------|----------|
| 32 F1 entry points | All map to registered L2 APIs | All delegate to backend | Phase D Registry |
| F2 (authority) | Zero frontend decisions | All eligibility in L4 | F2 PASS |
| F3 (side effects) | Zero auto-fire patterns | All require user intent | F3 PASS |

---

## Edge Statistics (v2)

| Edge Type | Count |
|-----------|-------|
| Actor → Entry Container | 9 |
| Container → Transaction | 52 (via hosting) |
| Transaction → Processor | 15+ |
| Processor → Processor (delegation) | 13 |
| Processor → Store | 16 |
| Processor → External | 17 |
| Telemetry Edges | 6 |
| Governance Control Edges | 5 |
| Scheduler Edges | 4 |
| **TOTAL UNIQUE EDGES** | ~137 |

---

## Implicit Coupling (Known, Acceptable)

From user governance review:

| Coupling | Status | Note |
|----------|--------|------|
| L7 → L4 feedback via L6 state | Implicit | Not broken; explicit DomainReadinessSignal could be added later |
| L4 → L2 explanation gap | Acceptable | APIs expose simplified views; BLCA will catch drift |

---

## Blast Radius Reference

For governance, these externals have highest blast radius if unavailable:

| External | Blast Radius | Mitigation |
|----------|--------------|------------|
| EXT-001 (OpenAI) | All LLM calls fail | Circuit breaker, fallback to EXT-002 |
| EXT-002 (Anthropic) | Backup LLM fails | Fallback chain |
| EXT-005 (Identity) | All auth fails | Token caching |
| EXT-006 (Webhooks) | Events not delivered | Outbox retry pattern |
| STORE-001 (PostgreSQL) | System down | Critical dependency |

---

*Refined from imports and Phase A-D evidence. Not designed.*
*Reference: RAW_ARCHITECTURE_NODES.md (v2), PIN-254*
*v2: Entry split, External expanded, Observer differentiated, Scheduler semantics*
