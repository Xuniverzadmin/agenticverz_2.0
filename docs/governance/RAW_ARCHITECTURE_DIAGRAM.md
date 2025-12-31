# RAW_ARCHITECTURE_DIAGRAM.md

**Status:** DERIVED (mechanically from nodes/edges v2)
**Created:** 2025-12-31
**Source:** RAW_ARCHITECTURE_NODES.md, RAW_ARCHITECTURE_EDGES.md
**Method:** No layering. No grouping. Nodes and edges only.

---

## Derivation Rules

- Every box corresponds to a node in RAW_ARCHITECTURE_NODES.md
- Every arrow corresponds to an edge in RAW_ARCHITECTURE_EDGES.md
- Authority edges marked with `[!]`
- WRITE edges marked with `>>>`
- READ edges marked with `--->`
- CONTROL edges marked with `===>`
- No layer names used
- No abstraction applied

---

## Full System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                    ACTORS                                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│    ┌──────────────┐              ┌──────────────┐              ┌──────────────┐                                     │
│    │ ACTOR-001    │              │ ACTOR-002    │              │ ACTOR-003    │                                     │
│    │ Human User   │              │ SDK Client   │              │ Scheduler    │                                     │
│    │ (external)   │              │ (machine)    │              │ (time-based) │                                     │
│    └──────┬───────┘              └──────┬───────┘              └──────┬───────┘                                     │
│           │                             │                             │                                              │
│           │ HTTP                        │ HTTP                        │ Process                                      │
│           ▼                             ▼                             ▼                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
            │                             │                             │
            │                             │                             │
┌───────────▼─────────────────────────────▼─────────────────────────────▼─────────────────────────────────────────────┐
│                                         ENTRY CONTAINERS                                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ guard.py        │  │ founder_actions │  │ v1_killswitch   │  │ agents.py       │  │ recovery.py     │            │
│  │ (7 TXENTRY)     │  │ (7 TXENTRY)     │  │ (5 TXENTRY)     │  │ (10 TXENTRY)    │  │ (6 TXENTRY)     │            │
│  │ Guard Console   │  │ Founder Console │  │ Operator        │  │ SDK clients     │  │ Machine tokens  │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                    │                    │                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ costsim.py      │  │ onboarding.py   │  │ v1_proxy.py     │  │ workers.py      │  │ memory_pins.py  │            │
│  │ (3 TXENTRY)     │  │ (6 TXENTRY)     │  │ (2 TXENTRY)     │  │ (3 TXENTRY)     │  │ (2 TXENTRY)     │            │
│  │ API/workers     │  │ Auth flows      │  │ LLM proxy       │  │ Orchestration   │  │ Memory system   │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                    │                    │                      │
│  ┌─────────────────┐  ┌─────────────────┐                                                                            │
│  │ ops.py          │  │ rbac_api.py     │                                                                            │
│  │ (READ-ONLY)     │  │ (1 TXENTRY)     │                                                                            │
│  │ Founder Console │  │ Admin ops       │                                                                            │
│  └─────────────────┘  └────────┬────────┘                                                                            │
│                                │                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │  (52 total transactions)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               CRITICAL TRANSACTIONAL ENTRIES (Authority Actions)                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  [!] TXENTRY-011: POST /guard/killswitch/activate     ──────► HALTS ALL TRAFFIC                                     │
│  [!] TXENTRY-024: POST /ops/actions/freeze-tenant     ──────► BLOCKS TENANT                                         │
│  [!] TXENTRY-026: POST /ops/actions/freeze-api-key    ──────► REVOKES KEY                                           │
│  [!] TXENTRY-031: POST /v1/killswitch/tenant          ──────► FREEZES TENANT                                        │
│  [!] TXENTRY-032: POST /v1/killswitch/key             ──────► FREEZES KEY                                           │
│                                                                                                                      │
│  These 5 transactions can immediately halt system operation.                                                         │
│                                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              PROCESSORS                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                    DOMAIN ENGINES (Decision Authority)                                          ││
│  ├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                                                  ││
│  │  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐                                   ││
│  │  │ PROC-001             │  │ PROC-002             │  │ PROC-003             │                                   ││
│  │  │ recovery_rule_engine │  │ cost_model_engine    │  │ llm_policy_engine    │                                   ││
│  │  │                      │  │                      │  │                      │                                   ││
│  │  │ • should_auto_execute│  │ • estimate_step_cost │  │ • check_safety_limits│                                   ││
│  │  │ • classify_error     │  │ • check_feasibility  │  │ • is_model_allowed   │                                   ││
│  │  │ • suggest_recovery   │  │ • classify_drift     │  │ • get_model_for_task │                                   ││
│  │  │                      │  │                      │  │                      │                                   ││
│  │  │ [Phase A: SHADOW-001 │  │ [Phase B: B02 fix]   │  │ [Phase B: B01 fix]   │                                   ││
│  │  │  SHADOW-002, -003]   │  │                      │  │                      │                                   ││
│  │  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘                                   ││
│  │                                                                                                                  ││
│  │  ┌──────────────────────┐  ┌──────────────────────┐                                                             ││
│  │  │ PROC-004             │  │ PROC-005             │                                                             ││
│  │  │ rbac_engine          │  │ policy_engine        │                                                             ││
│  │  │                      │  │                      │                                                             ││
│  │  │ • check              │  │ • evaluate           │                                                             ││
│  │  │ • get_max_approval   │  │ • validate           │                                                             ││
│  │  │ • map_external_roles │  │                      │                                                             ││
│  │  │                      │  │                      │                                                             ││
│  │  │ [Phase B: B03, B04]  │  │                      │                                                             ││
│  │  └──────────────────────┘  └──────────────────────┘                                                             ││
│  │                                                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                         SERVICES                                                                 ││
│  ├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                                                  ││
│  │  WRITE SERVICES (authority to mutate state):                                                                     ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                                            ││
│  │  │ PROC-007          │  │ PROC-008          │  │ PROC-009          │                                            ││
│  │  │ guard_write_svc   │  │ recovery_write_svc│  │ ops_write_svc     │                                            ││
│  │  │                   │  │                   │  │                   │                                            ││
│  │  │ >>> PostgreSQL    │  │ >>> PostgreSQL    │  │ >>> PostgreSQL    │                                            ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘                                            ││
│  │                                                                                                                  ││
│  │  READ/COMPUTE SERVICES:                                                                                          ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  ┌────────────────┐ ││
│  │  │ PROC-006          │  │ PROC-010          │  │ PROC-011          │  │ PROC-012          │  │ PROC-013       │ ││
│  │  │ recovery_matcher  │  │ certificate       │  │ replay_determinism│  │ incident_aggreg   │  │ event_emitter  │ ││
│  │  │                   │  │                   │  │                   │  │                   │  │                │ ││
│  │  │ ---> VoyageAI     │  │                   │  │                   │  │                   │  │ >>> outbox     │ ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘  └───────────────────┘  └────────────────┘ ││
│  │                                                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                          WORKERS                                                                 ││
│  ├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                                                  ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                                            ││
│  │  │ WORK-001          │  │ WORK-002          │  │ WORK-003          │                                            ││
│  │  │ runner.py         │  │ pool.py           │  │ recovery_evaluator│                                            ││
│  │  │                   │  │                   │  │                   │                                            ││
│  │  │ Executes jobs     │  │ Manages workers   │  │ Evaluates failures│                                            ││
│  │  │                   │  │                   │  │                   │                                            ││
│  │  │ ---> PROC-004     │  │ ---> WORK-001     │  │ ---> PROC-001 [!] │                                            ││
│  │  │ >>> traces        │  │                   │  │ [SHADOW-001 fix]  │                                            ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘                                            ││
│  │                                                                                                                  ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                                            ││
│  │  │ WORK-004          │  │ WORK-005          │  │ WORK-006          │                                            ││
│  │  │ recovery_claim    │  │ outbox_processor  │  │ simulate.py       │                                            ││
│  │  │                   │  │                   │  │                   │                                            ││
│  │  │ ---> PROC-006     │  │ >>> EXT-006       │  │ ---> PROC-002     │                                            ││
│  │  │ ---> PROC-008     │  │ (webhooks)        │  │ [B02 delegation]  │                                            ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘                                            ││
│  │                                                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                         ADAPTERS (Translation Only)                                              ││
│  ├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                                                                  ││
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐                     ││
│  │  │ ADAPT-001         │  │ ADAPT-002         │  │ ADAPT-003         │  │ ADAPT-004         │                     ││
│  │  │ openai_adapter    │  │ v2_adapter        │  │ anthropic_adapter │  │ nats_adapter      │                     ││
│  │  │                   │  │                   │  │                   │  │                   │                     ││
│  │  │ ---> EXT-001      │  │ ---> PROC-002 [!] │  │ ---> EXT-002      │  │ >>> EXT-007       │                     ││
│  │  │ ---> PROC-003 [!] │  │ [B02 delegation]  │  │                   │  │                   │                     ││
│  │  │ [B01 delegation]  │  │                   │  │                   │  │                   │                     ││
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘  └───────────────────┘                     ││
│  │                                                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              STORES                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  ┌───────────────────────────────────────────┐  ┌─────────────────────────┐                                         │
│  │ STORE-001: PostgreSQL                      │  │ STORE-002: Redis        │                                         │
│  │                                            │  │                         │                                         │
│  │ ALL PERSISTENT STATE                       │  │ Advisory cache only     │                                         │
│  │                                            │  │ Loss = no behavior      │                                         │
│  │ ◄─── All write services                    │  │ change (invariant)      │                                         │
│  │ ◄─── All workers                           │  │                         │                                         │
│  │ ◄─── All schedulers                        │  │                         │                                         │
│  └───────────────────────────────────────────┘  └─────────────────────────┘                                         │
│                                                                                                                      │
│  ORM MODELS (PostgreSQL-backed):                                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                             │
│  │ STORE-003        │  │ STORE-004        │  │ STORE-005        │  │ STORE-006        │                             │
│  │ killswitch       │  │ trace            │  │ policy           │  │ recovery         │                             │
│  │                  │  │                  │  │                  │  │                  │                             │
│  │ Incident         │  │ Trace [IMMUT]    │  │ Policy           │  │ RecoveryCandidate│                             │
│  │ IncidentEvent    │  │ TraceStep [IMMUT]│  │ PolicyRule       │  │ RecoveryAction   │                             │
│  │ KillSwitchState  │  │                  │  │ PolicyDecision   │  │                  │                             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘                             │
│                                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SCHEDULERS (Autonomous, Time-Based)                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  ⚠ ALL CAN FIRE WITHOUT HUMAN INTENT                                                                                │
│                                                                                                                      │
│  ┌────────────────────────────┐  ┌────────────────────────────┐  ┌────────────────────────────┐                     │
│  │ SCHED-001                  │  │ SCHED-002                  │  │ SCHED-003                  │                     │
│  │ failure_aggregation        │  │ graduation_evaluator       │  │ cost_snapshots             │                     │
│  │                            │  │                            │  │                            │                     │
│  │ Trigger: systemd/cron      │  │ Trigger: systemd/cron      │  │ Trigger: systemd/cron      │                     │
│  │ Freq: ~hourly              │  │ Freq: ~daily               │  │ Freq: ~hourly/daily        │                     │
│  │                            │  │                            │  │                            │                     │
│  │ ---> PROC-012 (aggregator) │  │ ---> PROC-005 (policy)     │  │ ---> PROC-002 (cost)       │                     │
│  │ ---> PROC-001 (rules) [!]  │  │                            │  │                            │                     │
│  │                            │  │                            │  │                            │                     │
│  │ [SHADOW-002, -003 fix]     │  │                            │  │                            │                     │
│  └────────────────────────────┘  └────────────────────────────┘  └────────────────────────────┘                     │
│                                                                                                                      │
│  Governance: Schedulers delegate all domain decisions to engines (verified Phase A).                                │
│  They do not make authority decisions themselves.                                                                    │
│                                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         EXTERNAL SYSTEMS                                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  READ (influence decision quality):                                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ EXT-001          │  │ EXT-002          │  │ EXT-003          │  │ EXT-004          │  │ EXT-005          │       │
│  │ OpenAI API       │  │ Anthropic API    │  │ VoyageAI         │  │ HashiCorp Vault  │  │ Identity (OAuth) │       │
│  │                  │  │                  │  │                  │  │                  │  │                  │       │
│  │ ◄─ openai_adapter│  │ ◄─ anthropic_adpt│  │ ◄─ recovery_match│  │ ◄─ vault_client  │  │ ◄─ oauth_providers│      │
│  │ ◄─ v1_proxy      │  │ ◄─ claude_adapter│  │ ◄─ voyage_embed  │  │                  │  │ ◄─ clerk_provider│       │
│  │ ◄─ llm_invoke    │  │ ◄─ llm_invoke    │  │                  │  │                  │  │ ◄─ oidc_provider │       │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│                                                                                                                      │
│  WRITE (blast radius - irreversible external state):                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                             │
│  │ EXT-006          │  │ EXT-007          │  │ EXT-008          │  │ EXT-009          │                             │
│  │ Webhooks         │  │ NATS Server      │  │ Slack API        │  │ Email Provider   │                             │
│  │                  │  │                  │  │                  │  │                  │                             │
│  │ ◄─ outbox_proc   │  │ ◄─ nats_adapter  │  │ ◄─ slack_send    │  │ ◄─ email_send    │                             │
│  │ ◄─ webhook_send  │  │                  │  │ ◄─ Alertmanager  │  │ ◄─ email_verify  │                             │
│  │                  │  │                  │  │                  │  │ ◄─ Alertmanager  │                             │
│  │ RETRY: outbox    │  │ RETRY: NATS      │  │                  │  │                  │                             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘                             │
│                                                                                                                      │
│  BLAST RADIUS (if unavailable):                                                                                      │
│  • EXT-001/002: LLM calls fail → circuit breaker, fallback chain                                                    │
│  • EXT-005: Auth fails → token caching                                                                               │
│  • EXT-006: Events undelivered → outbox retry                                                                        │
│  • STORE-001: System down → CRITICAL                                                                                 │
│                                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           OBSERVERS                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                                      │
│  GOVERNANCE CONTROL (can halt work):                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                                                  ││
│  │  ┌───────────────────────────────────────────┐  ┌───────────────────────────────────────────┐                   ││
│  │  │ OBS-001: BLCA                              │  │ OBS-002: CI Pipeline                      │                   ││
│  │  │ Bidirectional Layer Consistency Auditor    │  │                                           │                   ││
│  │  │                                            │  │ Triggered by: PR open/update              │                   ││
│  │  │ Triggered by: Session start, code changes  │  │                                           │                   ││
│  │  │                                            │  │ CONTROL AUTHORITY:                        │                   ││
│  │  │ CONTROL AUTHORITY:                         │  │  • Tier 1: BLOCK PR merge                 │                   ││
│  │  │  ===> BLOCK code changes                   │  │  • Tier 2: WARN (human ACK required)      │                   ││
│  │  │  ===> BLOCK PR merge                       │  │                                           │                   ││
│  │  │  ===> BLOCK session work                   │  │ Evidence: .github/workflows/*.yml         │                   ││
│  │  │                                            │  │                                           │                   ││
│  │  │ Writes: BIDIRECTIONAL_AUDIT_STATUS.md      │  │                                           │                   ││
│  │  │                                            │  │                                           │                   ││
│  │  │ Reference: SESSION_PLAYBOOK Section 28-29  │  │ Reference: PIN-255 three-tier model       │                   ││
│  │  └───────────────────────────────────────────┘  └───────────────────────────────────────────┘                   ││
│  │                                                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                                      │
│  TELEMETRY (passive observation, no control):                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                                                                  ││
│  │  ┌───────────────────────────────────────────┐  ┌───────────────────────────────────────────┐                   ││
│  │  │ OBS-003: Prometheus                        │  │ OBS-004: Alertmanager                     │                   ││
│  │  │                                            │  │                                           │                   ││
│  │  │ ◄─── All entry containers (request metrics)│  │ ◄─── Prometheus (alert trigger)          │                   ││
│  │  │ ◄─── All workers (worker metrics)          │  │                                           │                   ││
│  │  │ ◄─── PostgreSQL (scrape)                   │  │ ---> EXT-008 (Slack notification)        │                   ││
│  │  │                                            │  │ ---> EXT-009 (Email notification)        │                   ││
│  │  │ CONTROL AUTHORITY: NONE                    │  │                                           │                   ││
│  │  │                                            │  │ CONTROL AUTHORITY: NONE                   │                   ││
│  │  │                                            │  │ (notifies humans, does not control)       │                   ││
│  │  └───────────────────────────────────────────┘  └───────────────────────────────────────────┘                   ││
│  │                                                                                                                  ││
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Authority Edge Summary

Edges marked with `[!]` represent Phase A-D verified domain delegation:

| From | To | Authority Type | Evidence |
|------|-----|----------------|----------|
| WORK-003 (recovery_evaluator) | PROC-001 (recovery_rule_engine) | Domain decision | SHADOW-001 |
| SCHED-001 (failure_aggregation) | PROC-001 (recovery_rule_engine) | Classification | SHADOW-002, SHADOW-003 |
| ADAPT-001 (openai_adapter) | PROC-003 (llm_policy_engine) | Safety check | B01 |
| ADAPT-002 (v2_adapter) | PROC-002 (cost_model_engine) | Cost calculation | B02 |
| WORK-006 (simulate.py) | PROC-002 (cost_model_engine) | Cost calculation | B02 |

---

## Hard Authority Actions (System-Stopping)

These 5 transactions can immediately halt operations:

| Transaction | Effect | Undo Available |
|-------------|--------|----------------|
| TXENTRY-011 | HALTS ALL TRAFFIC | TXENTRY-012 |
| TXENTRY-024 | BLOCKS TENANT | TXENTRY-028 |
| TXENTRY-026 | REVOKES KEY | TXENTRY-030 |
| TXENTRY-031 | FREEZES TENANT | TXENTRY-033 |
| TXENTRY-032 | FREEZES KEY | TXENTRY-034 |

---

## Data Flow Summary

```
ACTORS
   │
   │ HTTP / Process
   ▼
ENTRY CONTAINERS ──────► TRANSACTIONS (52)
   │
   │ Delegate
   ▼
PROCESSORS
   │
   ├──────► ENGINES (domain decisions) ◄────── [Phase A-D verified]
   │             │
   ├──────► SERVICES (read/write)
   │             │
   ├──────► WORKERS (execution)
   │             │
   └──────► ADAPTERS (translation) ────► EXTERNAL (9 systems)
                 │
                 │ >>> (WRITE)
                 ▼
STORES (PostgreSQL + models)
   │
   │ Scrape
   ▼
OBSERVERS (telemetry + governance control)

SCHEDULERS (autonomous, time-based)
   │
   │ Delegate to engines
   ▼
PROCESSORS
```

---

## Diagram Statistics

| Element | Count |
|---------|-------|
| Actors | 3 |
| Entry Containers | 12 |
| Transactional Entries | 52 |
| Processors (total) | 23 |
| External Systems | 9 |
| Stores | 6 |
| Schedulers | 3 |
| Observers | 4 |
| **Total Nodes** | 112 |
| Authority Edges [!] | 5 |
| Hard-Stop Transactions | 5 |

---

*Derived mechanically from RAW_ARCHITECTURE_NODES.md and RAW_ARCHITECTURE_EDGES.md (v2)*
*No abstraction. No layering. Evidence-only.*
