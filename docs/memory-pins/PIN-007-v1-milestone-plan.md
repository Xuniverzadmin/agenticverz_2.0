# PIN-007: AOS v1 Milestone Plan (Finalized)

**Serial:** PIN-007
**Created:** 2025-12-01
**Status:** Active
**Category:** Architecture / Planning

---

## Executive Summary

This PIN contains the finalized, vision-aligned milestone plan for AOS v1. All gaps from previous reviews have been addressed. The plan is ready for execution.

---

## Assumptions

### Team Size Options

| Team Size | Description | Timeline Impact |
|-----------|-------------|-----------------|
| **Small team (recommended)** | 2 backend engineers (1 senior, 1 mid), 1 frontend (Phase 2), 0.5 SRE/DevOps, 0.5 PO | Base estimates |
| **Solo developer** | Single developer | Add +50% to all estimates |

### Scope Boundaries

- **v1 scope** = M0–M7 complete + internal validation + feature freeze
- **Phase 2** = M8+ (adaptive runtime, web console, ML failure matching)
- Phase 2 features are explicitly deferred

### Repository Layout

All artifacts follow existing structure: `backend/app/...`

---

## Vision Alignment Verification

| Vision Pillar | Milestone Coverage |
|---------------|-------------------|
| Deterministic state | M1, M6 |
| Replayable runs | M6 |
| Budget & cost contracts | M0, M1, M3 |
| Skill contracts | M0, M2, M3 |
| System policies | M1, M5 |
| Observability | M6 |
| Planner modularity | M2.5 |
| Zero silent failures | M0, M1, M5 |
| Adaptive runtime | M13 (Phase 2) |

---

## Milestone Summary

| Milestone | Name | Duration | Phase |
|-----------|------|----------|-------|
| M0 | Foundations & Contracts + Testing Infra | 1 week | v1 |
| M1 | Runtime Interfaces | 2 weeks | v1 |
| M2 | Skill Registration + Core Stubs | 2 weeks | v1 |
| M2.5 | Planner Abstraction | 1 week | v1 |
| M3 | Core Skill Implementations | 4 weeks | v1 |
| M3.5 | CLI + 60s Demo | 2 weeks | v1 |
| M4 | Internal Workflow Validation | 2 weeks | v1 |
| M5 | Failure Catalog v1 | 1 week | v1 |
| M5.5 | Simulation Engine v1 | 1.5 weeks | v1 |
| M6 | Feature Freeze + Observability + Tests | 2 weeks | v1 |
| M7 | Memory Integration | 1 week | v1 |
| M8 | KV Store + FS | 2 weeks | Post-v1 |
| M9 | Notifications & Email | 3 weeks | Post-v1 |
| M10 | PDF + Embeddings + Vector Search | 4 weeks | Post-v1 |
| M11 | Web Console + Human-in-Loop | 4-6 weeks | Phase 2 |
| M12 | External Alpha | 2-4 weeks | Phase 2 |
| M13 | Adaptive Runtime v2 | 2-4 months | Phase 2 |

**Total v1 (M0-M7):** ~19.5 weeks (~5 months for small team, ~8 months solo)

---

## Detailed Milestones

### M0 — Foundations & Contracts + Testing Infra (1 week)

**Scope:** Finalize schemas, error taxonomy, agent profile, and CI/testing basics.

**Deliverables:**
- Error taxonomy & canonical codes
- JSON schemas: StructuredOutcome, SkillMetadata, ResourceContract, AgentProfile
- Determinism & Replay definition doc
- Testing infra: pytest scaffold, GitHub Actions CI pipeline
- Local dev runner doc & env setup

**Artifacts:**
```
backend/app/schemas/structured_outcome.py
backend/app/schemas/skill_metadata.py
backend/app/schemas/resource_contract.py
backend/app/schemas/agent_profile.py
backend/app/specs/error_taxonomy.md
backend/app/specs/determinism_and_replay.md
.github/workflows/ci.yml
backend/tests/conftest.py
```

**Dependencies:** None

**Why:** Prevents divergent error codes, ensures reproducible CI from day 1.

---

### M1 — Runtime Interfaces (2 weeks)

**Scope:** Implement core machine-native APIs (no skill implementations yet).

**Deliverables:**
- `runtime.execute()` wrapper (never throws; returns StructuredOutcome)
- `runtime.describe_skill()` interface
- `runtime.query()` basic queries
- `runtime.get_resource_contract()` generator
- Interface tests + contract validation

**Artifacts:**
```
backend/app/worker/runtime/execute.py
backend/app/worker/runtime/describe_skill.py
backend/app/worker/runtime/query.py
backend/app/worker/runtime/contracts.py
backend/tests/runtime/test_execute.py
backend/tests/runtime/test_query.py
```

**Dependencies:** M0

**Why:** These primitives are the kernel of machine-native behavior.

---

### M2 — Skill Registration Interface + Core Stubs (2 weeks)

**Scope:** Registration protocol + stub skills + versioning.

**Deliverables:**
- Skill registration protocol
- Registry service (in-memory + persistent)
- Stubs for http_call, llm_invoke, json_transform
- Unit tests for registration/versioning

**Artifacts:**
```
backend/app/skills/registry.py
backend/app/skills/stubs/http_call_stub.py
backend/app/skills/stubs/llm_invoke_stub.py
backend/app/skills/stubs/json_transform_stub.py
backend/app/schemas/skill_registration.md
backend/tests/skills/test_registry.py
```

**Dependencies:** M1

**Why:** Separates registration from implementation; enables early testing.

---

### M2.5 — Planner Abstraction & Stub Planner (1 week)

**Scope:** Planner interface & testable stub; make planner pluggable.

**Deliverables:**
- `PlannerInterface` protocol
- `claude_planner` adapter refactor
- `stub_planner` rule-based for tests
- AgentProfile supports planner selection

**Artifacts:**
```
backend/app/planner/interface.py
backend/app/planner/claude_adapter.py
backend/app/planner/stub_planner.py
```

**Dependencies:** M0, M1, M2

**Why:** Planner modularity is a core pillar.

---

### M3 — Core Skill Implementations v1 (4 weeks)

**Scope:** Implement production-grade core skills with structured outcomes.

**Deliverables:**
- `http_call` implementation (timeout, DNS, 4xx/5xx, retries, side-effect log)
- `llm_invoke` implementation (multi-model, token cost, safety wrapper)
- `json_transform` implementation (deterministic, schema validation)
- SkillMetadata generation and registration
- Integration tests

**Artifacts:**
```
backend/app/skills/http_call.py
backend/app/skills/llm_invoke.py
backend/app/skills/json_transform.py
backend/app/skills/versions/
backend/tests/integration/test_core_skills.py
```

**Dependencies:** M2.5

**Why:** Minimum viable skills for machine-native demonstration.

---

### M3.5 — CLI + 60s Demo (2 weeks)

**Scope:** CLI tooling and first reproducible demo. Demo uses mock notifier.

**Deliverables:**
- CLI: `aos run`, `aos simulate`, `aos describe-skill`, `aos trace`
- Demo scenario: BTC price with simulated timeout, retry, trace
- Demo README + one-click run script

**Artifacts:**
```
backend/cli/aos.py
backend/app/examples/demo_btc/
backend/app/docs/demo_btc.md
```

**Dependencies:** M3

**Why:** CLI-first speeds adoption; mocks avoid delays.

**Note:** Demo uses mock webhook/notifier. Real notifications in M9.

---

### M4 — Internal Workflow Validation (2 weeks)

**Scope:** Dogfood AOS with 2 real internal workflows.

**Deliverables:**
- 2 workflows ported to AOS (Agenticverz + Mobiverz)
- 1 week monitoring (traces, costs, failures)
- Failure Log export for catalog population
- Validate agent profile & budget enforcement

**Artifacts:**
```
backend/app/int/agenticverz_onboard_agent/
backend/app/int/mobiverz_report_agent/
backend/logs/internal_runs/
reports/internal_validation_report.md
```

**Dependencies:** M3.5

**Why:** Internal use exposes real failure modes; aligns with internal-first strategy.

---

### M5 — Failure Catalog v1 (1 week)

**Scope:** Exact-match lookup failure catalog.

**Deliverables:**
- `failure_catalog.json` seeded from M0 taxonomy + M4 data
- `failure_catalog.match()` exact-match function
- Runtime integration for retry/backoff decisions

**Artifacts:**
```
backend/app/runtime/failure_catalog.py
backend/app/data/failure_catalog.json
backend/tests/test_failure_catalog.py
```

**Dependencies:** M4

**Why:** Simple, reliable failure handling; no premature ML.

---

### M5.5 — Simulation Engine v1 (1.5 weeks)

**Scope:** Static, deterministic simulation.

**Deliverables:**
- `runtime.simulate(plan)` with cost/latency sums, permission checks, budget validation
- CLI `aos simulate` integration
- Tests with synthetic plans

**Artifacts:**
```
backend/app/worker/runtime/simulate.py
backend/cli/aos_simulate.py
backend/tests/test_simulate.py
```

**Dependencies:** M5

**Why:** Cost/latency visibility before execution; deterministic and conservative.

---

### M6 — v1 Feature Freeze + Observability + Tests (2 weeks)

**Scope:** Freeze features, harden observability, validate determinism & replay.

**Deliverables:**
- Feature freeze document (scope locked, no new skills)
- Prometheus metrics (skill_calls_total, errors, latency, cost, failures)
- Run traces with correlation IDs
- Determinism test suite
- Replay capability and tests

**Artifacts:**
```
backend/app/observability/prometheus_metrics.py
backend/app/traces/store.py
backend/tests/test_determinism.py
backend/tests/test_replay.py
docs/v1_feature_freeze.md
backend/app/docs/replay_scope.md
```

**Dependencies:** M5.5

**Why:** Locks v1 scope; demonstrates core machine-native guarantees.

**Note:** Feature freeze applies to skills. Memory (M7) is runtime infrastructure, not a skill.

---

### M7 — Memory Integration (1 week)

**Scope:** Wire memory retriever into runtime.

**Deliverables:**
- `runtime.query("relevant_memories", goal, max_tokens)` API
- Context window manager (truncation, relevance scoring)
- Multi-turn behavior tests
- AgentProfile memory backend selection

**Artifacts:**
```
backend/app/memory/retriever.py (wired)
backend/app/worker/runtime/context_manager.py
backend/tests/test_memory_integration.py
```

**Dependencies:** M6

**Why:** Addresses PIN-002 memory gap; enables multi-turn agents.

---

## Post-v1 Milestones (Summary)

### M8 — KV Store + FS (2 weeks)
- `kv_store` skill (Redis)
- `fs_read` / `fs_write` skills

### M9 — Notifications & Email (3 weeks)
- `webhook_send`, `slack_send`, `email_send` skills

### M10 — PDF + Embeddings + Vector Search (4 weeks)
- `file_parse`, `text_embed`, `vector_search` skills

### M11 — Web Console + Human-in-Loop (4-6 weeks, Phase 2)
- Run viewer, plan simulator, skill inspector
- Approval gates for human-in-the-loop
- Auth and permissions

### M12 — External Alpha (2-4 weeks, Phase 2)
- 5-10 external teams
- Feedback capture
- Telemetry dashboards

### M13 — Adaptive Runtime v2 (2-4 months, Phase 2)
- Historical metrics pipeline
- Statistical simulation
- Fuzzy failure matching
- Planner feedback loop

---

## Replay & Determinism Definition

### Replay Scope
**Replay** = re-executing a stored plan (skill calls + inputs + versions) without re-planning.

**Asserted invariants:**
- Same retry/backoff behavior
- Same cost accounting
- Same side-effect metadata sequence (timestamps aside)

**NOT guaranteed:**
- External API responses
- LLM output content

Tests validate runtime behavior, not external content parity.

### Determinism Scope
- **Runtime behavior:** Deterministic (same error handling, retry logic)
- **Execution metadata:** Deterministic (same cost calculation)
- **Skill results:** NOT deterministic for I/O skills (external dependencies)

---

## Testing Strategy

### Test Categories
| Category | Scope | Frequency |
|----------|-------|-----------|
| Unit tests | Per module/skill, no network | Every commit |
| Integration tests | Skills with mocks | Every PR |
| E2E tests | Full demo flows | Nightly/release |
| Determinism tests | Replay stored plans | Every PR |
| Failure injection | Force errors, validate recovery | Weekly |

### CI Jobs
```
ci/unit        → fast, every commit
ci/integration → with mocks, every PR
ci/e2e         → nightly or on release
```

---

## Team Ownership

| Role | Responsibilities |
|------|------------------|
| PO (you) | Prioritize, acceptance tests, demo scenarios, early adopters |
| Senior backend | Runtime core, observability, determinism, security |
| Mid backend | Skills, registration, tests |
| Frontend (Phase 2) | Console, human-in-loop |
| SRE/DevOps (0.5) | CI, Prometheus, deployment |

---

## Solo Developer Path

If working solo, use this minimal path:

1. M0 (1 week)
2. M1 (2 weeks)
3. M2 + M2.5 combined (2 weeks)
4. M3 but only http_call + llm_invoke (3 weeks)
5. M3.5 CLI + demo (1.5 weeks)

**Stop. Ship. Iterate.**

Total: ~10 weeks for minimal viable demo.

---

## Related PINs

- [PIN-005](PIN-005-machine-native-architecture.md) - Machine-native architecture
- [PIN-006](PIN-006-execution-plan-review.md) - Execution plan review

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Initial creation - Finalized v1 milestone plan |
