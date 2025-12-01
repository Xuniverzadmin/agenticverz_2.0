# PIN-008: AOS v1 Milestone Plan (Full Detail)

**Serial:** PIN-008
**Created:** 2025-12-01
**Status:** Active
**Category:** Architecture / Planning / Specification
**Supersedes:** PIN-007 (PIN-007 remains as summary view)

---

## Executive Summary

This PIN contains the **complete, finalized, vision-aligned milestone plan** for AOS v1. All gaps from previous reviews have been addressed. The plan is ready for execution.

**Grade: A** — All gaps addressed. Vision-aligned. Ready for execution.

---

## Assumptions (Read This First)

### Repository Layout
Primary repo layout: `backend/app/...` for runtime, skills, schemas, worker; frontend console later under `frontend/`.

### Team Size Options

| Team Size | Composition | Timeline Impact |
|-----------|-------------|-----------------|
| **Small team (recommended for v1)** | 2 backend engineers (1 senior, 1 mid), 1 frontend (Phase 2), 0.5 SRE/DevOps, 0.5 PO (you) | Base estimates |
| **Solo path** | Single developer | Add +50% to all estimates; use mocks; defer high-risk items |

### Scope Boundaries

- **v1 scope** = M0..M6 complete + internal validation + v1 feature freeze
- **Phase 2** features (adaptive runtime, full console, ML failure matching) are **explicitly deferred**

---

## Vision Alignment Verification

| Vision Pillar | Milestone Coverage | Verified |
|---------------|-------------------|----------|
| Deterministic state | M1, M6 | ✅ |
| Replayable runs | M6 (with precise definition) | ✅ |
| Budget & cost contracts | M0, M1, M3 | ✅ |
| Skill contracts | M0, M2, M3 | ✅ |
| System policies | M1, M5 | ✅ |
| Observability | M6 | ✅ |
| Planner modularity | M2.5 | ✅ |
| Zero silent failures | M0, M1, M5 | ✅ |
| Adaptive runtime | M13 (Phase 2, explicit) | ✅ |

---

## Gap Check (All Resolved)

| Previous Gap | Status | Resolution |
|--------------|--------|------------|
| Memory/context integration | ✅ Fixed | M7 added |
| Human-in-the-loop | ✅ Fixed | M11 (Phase 2) explicitly includes it |
| Demo notification dependency | ✅ Fixed | M3.5 documents mock notifier |
| Skill registration placement | ✅ Fixed | M2 is registration, M3 is implementation |
| Artifact path alignment | ✅ Fixed | All paths use `backend/app/...` |
| Team size assumption | ✅ Fixed | Explicit team sizes + solo path noted |
| Testing strategy | ✅ Fixed | M0 includes CI/testing infra |
| Replay definition | ✅ Fixed | Precise definition added |
| Planner modularity | ✅ Fixed | M2.5 |
| Agent profile | ✅ Fixed | M0 |
| Internal validation | ✅ Fixed | M4 |
| v1 feature freeze | ✅ Fixed | M6 |

---

## Milestone Summary Table

| Milestone | Name | Duration | Phase |
|-----------|------|----------|-------|
| M0 | Foundations & Contracts + Testing Infra | 1 week | v1 |
| M1 | Runtime Interfaces | 2 weeks | v1 |
| M2 | Skill Registration + Core Stubs | 2 weeks | v1 |
| M2.5 | Planner Abstraction & Stub Planner | 1 week | v1 |
| M3 | Core Skill Implementations v1 | 4 weeks | v1 |
| M3.5 | CLI + 60s Demo | 2 weeks | v1 |
| M4 | Internal Workflow Validation | 2 weeks | v1 |
| M5 | Failure Catalog v1 | 1 week | v1 |
| M5.5 | Simulation Engine v1 + Simulate CLI | 1.5 weeks | v1 |
| M6 | v1 Feature Freeze & Observability + Tests | 2 weeks | v1 |
| M7 | Memory Integration & Context Management | 1 week | v1 |
| M8 | KV Store + FS | 2 weeks | Post-v1 |
| M9 | Notifications & Email | 3 weeks | Post-v1 |
| M10 | PDF Parsing + Embeddings + Vector Search | 4 weeks | Post-v1 |
| M11 | Web Console & Human-in-the-loop | 4-6 weeks | Phase 2 |
| M12 | External Alpha | 2-4 weeks | Phase 2 |
| M13 | Adaptive Runtime & Simulation v2 | 2-4 months | Phase 2+ |

**Total v1 (M0-M7):** ~19.5 weeks (~5 months for small team, ~8 months solo)

---

## Detailed Milestones

---

### M0 — Foundations & Contracts + Testing Infra (1 week)

**Scope:** Finalize schemas, error taxonomy, agent profile, and CI/testing basics.

**Deliverables:**
- Error taxonomy & canonical codes
- JSON schemas: StructuredOutcome, SkillMetadata, ResourceContract, AgentProfile
- Determinism & Replay definition doc
- Testing infra: pytest scaffold, test categories, GitHub Actions CI pipeline with unit/integration job templates, basic coverage threshold
- Local dev runner doc & env setup

**Artifacts (repo paths):**
```
backend/app/schemas/structured_outcome.schema.json
backend/app/schemas/skill_metadata.schema.json
backend/app/schemas/resource_contract.schema.json
backend/app/schemas/agent_profile.schema.json
backend/app/specs/error_taxonomy.md
backend/app/specs/determinism_and_replay.md
.github/workflows/ci.yml (unit + integration matrix)
backend/tests/README.md + backend/tests/conftest.py
```

**Owners:** PO (you) define + 1 engineer implements CI/tests. GPT for scaffolding tests.

**Est. time:** 1 week

**Why:** Prevents divergent error codes, untestable behavior, and ensures reproducible CI from day 1.

---

### M1 — Runtime Interfaces (2 weeks)

**Scope:** Implement core machine-native APIs (no skill implementations yet).

**Deliverables:**
- `runtime.execute()` wrapper (never throws; returns StructuredOutcome)
- `runtime.describe_skill()` interface
- `runtime.query()` basic queries (remaining_budget_cents, what_did_i_try_already, allowed_skills, last_step_outcome)
- `runtime.get_resource_contract()` generator
- Interface tests + contract validation

**Artifacts:**
```
backend/app/worker/runtime/execute.py
backend/app/worker/runtime/describe_skill.py
backend/app/worker/runtime/query.py
backend/app/worker/contracts.py
backend/tests/runtime/test_execute.py
```

**Owners:** Senior backend engineer

**Est. time:** 2 weeks

**Why:** These primitives are the kernel of machine-native behavior; everything else plugs in.

---

### M2 — Skill Registration Interface + Core Skill Stubs (2 weeks)

**Scope:** Registration protocol + stub skills + versioning protocol (no heavy implementations yet).

**Deliverables:**
- Skill registration protocol (how skills register, version metadata)
- Registry service (in-memory + persistent mapping)
- Stubs for http_call, llm_invoke, json_transform that conform to describe_skill but use mocks for behavior
- Unit tests for registration/versioning and stub behavior

**Artifacts:**
```
backend/app/skills/registry.py
backend/app/skills/stubs/http_call_stub.py
backend/app/skills/stubs/llm_invoke_stub.py
backend/app/skills/stubs/json_transform_stub.py
backend/app/schemas/skill_registration.md
backend/tests/skills/test_registry.py
```

**Owners:** Backend engineer

**Est. time:** 2 weeks

**Why:** Separates registration concerns from implementations, lets planner + runtime operate against skill contracts early.

---

### M2.5 — Planner Abstraction & Stub Planner (1 week)

**Scope:** Planner interface & a testable stub; make planner pluggable.

**Deliverables:**
- PlannerInterface protocol
- claude_planner adapter refactor (or placeholder adapter if Claude not available)
- stub_planner rule-based for tests
- AgentProfile supports planner selection

**Artifacts:**
```
backend/app/planner/interface.py
backend/app/planner/claude_adapter.py (or claude_adapter_stub.py)
backend/app/planner/stub_planner.py
backend/app/specs/agent_profile.schema.json (update with planner field)
```

**Owners:** Backend engineer + PO

**Est. time:** 1 week

**Why:** Planner modularity is a core pillar — must be pluggable for multi-model routing and enterprise flexibility.

---

### M3 — Core Skill Implementations v1 (http_call, llm_invoke, json_transform) (4 weeks)

**Scope:** Implement production-grade core skills (not stubs) with structured outcomes and cost accounting.

**Deliverables:**
- `http_call` implementation: timeout, DNS failure, 4xx/5xx mapping, retries per catalog policy, side-effect log
- `llm_invoke` implementation: multi-model router, token cost estimate, basic safety wrapper
- `json_transform` implementation: deterministic transforms, JSON Schema validation
- SkillMetadata generation and registration
- Integration tests: runtime.execute -> real skill call (use test servers/mock LLM)

**Artifacts:**
```
backend/app/skills/http_call.py
backend/app/skills/llm_invoke.py
backend/app/skills/json_transform.py
backend/app/skills/versions/ (version files)
backend/tests/integration/test_core_skills.py
```

**Owners:** Two backend engineers (one senior + one mid) for parallel work

**Est. time:** 4 weeks (conservative — real-world complexity)

**Why:** These are the minimum viable skills to show machine-native behavior end-to-end.

---

### M3.5 — CLI + 60s Demo (2 weeks)

**Scope:** CLI tooling and the first reproducible demo. Demo uses mock notifier (documented).

**Deliverables:**
- CLI commands: `aos run`, `aos simulate`, `aos describe-skill`, `aos trace`
- Demo scenario: BTC price plan (simulate → http_call to test endpoint → simulate timeout (forced) → structured failure → runtime uses failure_catalog suggestion → retry → trace). Use mock webhook/notifier for demo; real notifier later in M9.
- Demo README + one-click run script (dev environment)

**Artifacts:**
```
backend/cli/aos.py
backend/app/examples/demo_btc/
backend/app/docs/demo_btc.md
```

**Owners:** Backend engineer + PO

**Est. time:** 2 weeks

**Why:** CLI-first approach speeds adoption and testing; mocks avoid delays while notification skills mature.

---

### M4 — Internal Workflow Validation (2 weeks)

**Scope:** Dogfood AOS with 2 real internal workflows (Agenticverz + Mobiverz). Gather failure data.

**Deliverables:**
- Port 2 workflows to AOS runtime
- Run for 1 week under monitoring (collect traces, costs, failures)
- Produce Failure Log export for v1 catalog population
- Validate agent profile usage & budget enforcement

**Artifacts:**
```
backend/app/internal/agenticverz_onboard_agent/
backend/app/internal/mobiverz_report_agent/
backend/logs/internal_runs/*.json
/reports/internal_validation_report.md
```

**Owners:** PO + backend engineers

**Est. time:** 2 weeks

**Why:** Internal use exposes real failure modes and gives data for simulation and catalog; aligns with internal-first strategy.

---

### M5 — Failure Catalog v1 (1 week)

**Scope:** Implement exact-match lookup failure catalog and hook to runtime.

**Deliverables:**
- `failure_catalog.json` (code → {category, retryable, suggestions}) seeded with entries from M0 and M4
- `failure_catalog.match()` exact-match function
- Runtime integrates catalog to drive retry/backoff decisions

**Artifacts:**
```
backend/app/runtime/failure_catalog.py
backend/app/data/failure_catalog.json
backend/tests/test_failure_catalog.py
```

**Owners:** Backend engineer

**Est. time:** 1 week

**Why:** Simple, reliable failure-handling mechanism — avoids premature ML complexity.

---

### M5.5 — Simulation Engine v1 + Simulate CLI (1.5 weeks)

**Scope:** Static, deterministic simulation based on skill metadata only.

**Deliverables:**
- `runtime.simulate(plan)` sums cost_estimate_cents, avg_latency_ms, checks permissions vs ResourceContract, returns feasibility & budget_ok
- CLI `aos simulate` integrated with runtime.simulate
- Tests with synthetic plans

**Artifacts:**
```
backend/app/worker/simulate.py
backend/cli/aos_simulate.py
backend/tests/test_simulate.py
```

**Owners:** Backend engineer

**Est. time:** 1.5 weeks

**Why:** Provides cost/latency visibility for agents before runs; deterministic and conservative.

---

### M6 — v1 Feature Freeze & Observability + Determinism & Replay Tests (2 weeks)

**Scope:** Freeze features (no new skills) and harden observability + define replay semantics.

**Deliverables:**
- Feature freeze: `docs/v1_feature_freeze.md` (scope locked)
- Observability: Prometheus metrics (skill_calls_total, skill_errors_total, step_latency_ms, run_cost_cents_total, run_failures_total)
- Tracing: run traces stored in `backend/app/traces/` with correlation/run IDs
- Determinism test suite: runtime behavior (retries, cost calc) deterministic for same inputs & skill versions
- Replay capability: re-executing stored plan (stored steps + inputs) without re-planning; verify runtime behavior parity (not content parity). Documentation of replay scope & limitations.

**Artifacts:**
```
backend/app/observability/prometheus_metrics.py
backend/app/traces/store.py
backend/tests/test_replay.py
backend/app/docs/replay_scope.md
docs/v1_feature_freeze.md
```

**Owners:** Senior backend engineer + SRE

**Est. time:** 2 weeks

**Why:** Locks v1 scope and demonstrates core machine-native guarantees (replayability, observability, deterministic behavior of runtime).

---

### M7 — Memory Integration & Context Management (1 week)

**Scope:** Wire existing memory retriever into runtime for relevant-memory queries and multi-turn context handling.

**Deliverables:**
- `runtime.query("relevant_memories", goal, max_tokens)` API
- Context window manager: truncation rules & relevance scoring
- Tests for multi-turn behavior with memory retrieval
- AgentProfile supports memory backend selection

**Artifacts:**
```
backend/app/memory/retriever.py (wired into runtime)
backend/app/worker/context_manager.py
backend/tests/test_memory_integration.py
```

**Owners:** Backend engineer

**Est. time:** 1 week

**Why:** Addresses PIN-002 memory gap; enables multi-turn agents and better planner context.

---

### M8 — KV Store + FS (2 weeks)

**Scope:** Persistent short-term state + workspace.

**Deliverables:**
- `kv_store` skill (Redis) with namespace isolation & pooling
- Safe `fs_read` / `fs_write` (workspace root, size & path checks)
- Tests: TTL, concurrency, isolation

**Artifacts:**
```
backend/app/skills/kv_store.py
backend/app/skills/fs.py
backend/tests/test_kv_fs.py
```

**Owners:** Backend engineer

**Est. time:** 2 weeks

**Why:** Memory + KV complement each other; needed for many workflows.

---

### M9 — Notifications & Email (3 weeks)

**Scope:** Real notifier skills for production use.

**Deliverables:**
- `webhook_send` skill
- `slack_send` skill (webhook backed)
- `email_send` skill with SMTP integration & bounce metadata (initially via provider or staging SMTP)
- Deliverability doc for SMTP setup
- Tests & CI mocks

**Artifacts:**
```
backend/app/skills/webhook_send.py
backend/app/skills/slack_send.py
backend/app/skills/email_send.py
backend/app/docs/smtp_setup.md
```

**Owners:** Backend engineer + PO for SMTP creds

**Est. time:** 3 weeks

**Why:** Real notifications complete the demo pipeline; mandatory for internal ops.

---

### M10 — PDF Parsing + Embeddings + Vector Search (4 weeks)

**Scope:** Document intelligence and retrieval.

**Deliverables:**
- `file_parse` skill (PDF→text + metadata; OCR deferred)
- `text_embed` abstraction (pluggable)
- `vector_search` basic (FAISS or Redis) with index versioning
- Tests & indexing scripts

**Artifacts:**
```
backend/app/skills/file_parse.py
backend/app/skills/embed.py
backend/app/skills/vector_search.py
```

**Owners:** Backend engineer + data-engineer help

**Est. time:** 4 weeks

**Why:** Enables RAG patterns and many product use cases.

---

### M11 — (Phase 2) Web Console & Human-in-the-loop features (4–6 weeks)

**Scope:** UI and approval gates; explicitly Phase 2 (post v1).

**Deliverables:**
- Minimal console (run viewer, simulate view, skill inspector)
- Approval/hold UI for manual gates (Human-in-the-loop)
- Auth (OIDC/API keys) and role-based permission model (read-only first)
- API endpoints for console read operations

**Artifacts:**
```
frontend/console/
backend/app/api/console_endpoints.py
backend/app/docs/human_in_loop.md
```

**Owners:** Frontend + backend

**Est. time:** 4–6 weeks

**Why:** Human approvals are important but not required for v1; move to Phase 2.

---

### M12 — External Alpha (2–4 weeks)

**Scope:** Invite-only external testing.

**Deliverables:**
- Onboarding docs + SDK examples
- 5–10 external teams onboarding
- Feedback capture + telemetry dashboards
- SLA & pilot pricing doc (pilot offers)

**Artifacts:**
```
backend/app/docs/alpha_onboarding.md
/alpha/feedback/
backend/app/telemetry/dashboard_config.json
```

**Owners:** PO + engineers + SRE

**Est. time:** 2–4 weeks

**Why:** Validate adoption & gather data for adaptive runtime.

---

### M13 — Adaptive Runtime & Simulation v2 (Phase 2+, 2–4 months ongoing)

**Scope:** Data-driven simulation and fuzzy failure matching (deferred until adequate run history).

**Deliverables:**
- Historical run metrics pipeline
- Simulation risk modeling (statistical)
- Fuzzy failure match (heuristic → ML later)
- Planner feedback loop (recommend alternative plans based on history)

**Artifacts:**
```
backend/app/runtime/adaptive/
backend/app/data/run_metrics/
```

**Owners:** Data engineer + backend

**Est. time:** 2–4 months (iterative)

**Why:** Core long-term differentiation — built only after data collected.

---

## Cross-cutting Items (Applies to Many Milestones)

| Item | Description |
|------|-------------|
| **Documentation** | Every milestone must add docs under `backend/app/docs/` and update top-level `/README.md` |
| **Security checklist** | Every side-effect skill must include threat model and audit logs. Track under `backend/app/security/` |
| **Release process** | Semantic versions for SDK & skills; tag releases; changelog |
| **Team-size note** | If solo, add +50% to estimates or adopt "solo minimal path" (stop after M4 and ship CLI/demo) |

---

## Replay & Determinism — Precise Definition

### Replay Definition

**Replay** = re-executing a stored plan (list of skill calls + inputs + skill versions) without re-calling the planner.

**Asserted invariants during replay:**
- Same retry/backoff behavior
- Same cost accounting
- Same side-effect metadata sequence (timestamps aside)

**NOT guaranteed:**
- External API responses
- LLM content

Tests must validate **runtime behavior**, not external content parity.

### Determinism Definition

| Aspect | Deterministic? |
|--------|----------------|
| Runtime behavior (retry logic, error handling) | ✅ Yes |
| Execution metadata (cost calculation) | ✅ Yes |
| Skill results for I/O skills | ❌ No (external dependencies) |

---

## Testing Strategy (Expanded from M0)

### Test Categories

| Category | Scope | Frequency | Network |
|----------|-------|-----------|---------|
| Unit tests | Per module/skill | Every commit | No external |
| Integration tests | Skills with mock endpoints | Every PR | Mock only |
| E2E tests | Full demo flows | Nightly/release | Test endpoints |
| Determinism tests | Re-run stored plans | Every PR | None |
| Failure injection | Force errors, validate recovery | Weekly | Mock |

### CI Jobs

```yaml
ci/unit       # Fast, every commit
ci/integration # With mocks, every PR
ci/e2e        # Nightly or on release
```

All specs live in `backend/app/tests/`.

### Failure Injection Harness

Configurable to force TIMEOUT/DNS/4xx/5xx and validate catalog-driven recovery.

---

## Team Suggestions & Ownership

| Role | Owns | Key Milestones |
|------|------|----------------|
| **PO (you)** | Prioritize workflows, acceptance tests, demo scenarios, SMTP setup, early adopters | M0, M4, M9, M12 |
| **Senior backend engineer** | Runtime core, observability, determinism tests, security review | M1, M3, M6 |
| **Mid backend engineer** | Skills (http_call, kv, fs, email), registration, tests | M2, M3, M5, M8, M9 |
| **Frontend (Phase 2)** | Console + human-in-loop | M11 |
| **SRE/DevOps (0.5)** | CI, Prometheus, deployment scripts, backups | M0, M6 |

If you have fewer people, drop Phase 2 and heavy items (sandbox v1) or extend timelines.

---

## Solo Developer Path

If working solo, use this minimal path:

| Step | Milestone | Duration |
|------|-----------|----------|
| 1 | M0: Foundations | 1 week |
| 2 | M1: Runtime Interfaces | 2 weeks |
| 3 | M2 + M2.5 combined | 2 weeks |
| 4 | M3: Only http_call + llm_invoke | 3 weeks |
| 5 | M3.5: CLI + demo | 1.5 weeks |

**Stop. Ship. Iterate.**

**Total: ~10 weeks for minimal viable demo.**

---

## Final Reasoning — Why This Is The Right List

1. **All vision pillars covered for v1** except adaptive runtime (explicitly Phase 2)
2. **Planner modularity, agent profiles, memory, replayability, failure catalog, and observability** are now first-class and testable
3. **Risk mitigated by:**
   - Starting with stubs/registry
   - CI/tests from M0
   - Internal dogfooding (M4)
   - Conservative feature-freeze gate before observability/determinism tests
4. **Deliverables aligned to repo layout** — engineers can implement without filesystem churn
5. **Solo vs team paths explicit** — realistic timing acknowledged
6. **No premature ML or fuzzy matching** — start deterministic, iterate with real data

---

## Observations (Not Blockers)

### M6 Complexity
M6 includes 5 deliverables in 2 weeks. Consider splitting if time runs short:
- M6a: Feature freeze + observability (1 week)
- M6b: Determinism + replay tests (1 week)

### M7 After Feature Freeze
Memory is **runtime infrastructure**, not a skill. `v1_feature_freeze.md` should clarify this.

### Sandbox (code_execute)
Intentionally dropped from v1. Can be added post-M10 if needed.

---

## Related PINs

| PIN | Topic |
|-----|-------|
| [PIN-005](PIN-005-machine-native-architecture.md) | Machine-Native Architecture Definition |
| [PIN-006](PIN-006-execution-plan-review.md) | Execution Plan Review |
| [PIN-007](PIN-007-v1-milestone-plan.md) | v1 Milestone Plan (Summary) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Initial creation - Full detailed v1 milestone plan |
