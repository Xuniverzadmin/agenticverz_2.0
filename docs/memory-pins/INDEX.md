# Memory PIN Index

**Project:** AOS / Agenticverz 2.0
**Last Updated:** 2025-12-01

---

## What are Memory PINs?

Memory PINs are persistent knowledge documents that capture:
- Architecture decisions
- Project status snapshots
- Technical specifications
- Roadmaps and priorities
- Implementation patterns

They serve as **context anchors** for AI assistants and team members to quickly understand project state.

---

## Active PINs

| Serial | Title | Category | Status | Updated |
|--------|-------|----------|--------|---------|
| [PIN-001](PIN-001-aos-roadmap-status.md) | AOS Platform Status & Roadmap | Architecture / Roadmap | Active | 2025-11-30 |
| [PIN-002](PIN-002-critical-review.md) | Critical Review - AOS Architecture & Plan | Architecture Review | Active | 2025-11-30 |
| [PIN-003](PIN-003-phase3-completion.md) | Phase 3 Completion - Production Hardening | Architecture / Milestone | Active | 2025-11-30 |
| [PIN-004](PIN-004-phase4-phase5-completion.md) | Phase 4 & 5 Completion - Security Hardening | Architecture / Milestone | Active | 2025-11-30 |
| [PIN-005](PIN-005-machine-native-architecture.md) | Machine-Native Architecture & Strategic Review | Architecture / Strategy | **PRIMARY** | 2025-12-01 |
| [PIN-006](PIN-006-execution-plan-review.md) | Execution Plan Review & Realistic Roadmap | Architecture / Planning | Active | 2025-12-01 |
| [PIN-007](PIN-007-v1-milestone-plan.md) | v1 Milestone Plan (Summary) | Architecture / Planning | Active | 2025-12-01 |
| [PIN-008](PIN-008-v1-milestone-plan-full.md) | **v1 Milestone Plan (Full Detail)** | Architecture / Specification | **PRIMARY** | 2025-12-01 |
| [PIN-009](PIN-009-m0-finalization-report.md) | **M0 Finalization Report** | Milestone / Finalization | **FINALIZED** | 2025-12-01 |
| [PIN-010](PIN-010-m2-completion-report.md) | **M2 Completion Report** | Milestone / Completion | **COMPLETE** | 2025-12-01 |

---

## Planned PINs

| Serial | Title | Category | Priority |
|--------|-------|----------|----------|
| PIN-011 | Planner Architecture Deep Dive | Technical Spec | HIGH |
| PIN-012 | Agent Definition Schema | Technical Spec | Medium |
| PIN-013 | Deployment Guide | Operations | Low |

---

## PIN Categories

- **Architecture / Roadmap** - High-level design and planning
- **Technical Spec** - Detailed implementation specifications
- **Operations** - Deployment, monitoring, incident response
- **Security** - Access control, secrets, hardening
- **Integration** - External APIs, third-party services

---

## PIN Lifecycle

1. **Draft** - Initial creation, under development
2. **Active** - Current and accurate
3. **Superseded** - Replaced by newer PIN
4. **Archived** - Historical reference only

---

## Quick Reference

### Current Project Phase
**Strategic Pivot** → Machine-Native SDK Build (see PIN-005, PIN-008)

**v1 Timeline (~5 months small team, ~8 months solo):**
- M0: Foundations & Contracts (1 week) — **COMPLETE**
- M1-M2.5: Runtime + Skills + Planner (5 weeks)
- M3-M3.5: Core Skills + CLI + Demo (6 weeks)
- M4-M7: Validation + Observability + Memory (7.5 weeks)

### Completed Foundation (Pre-Pivot)
- ✅ Phase 1: Runtime Foundation
- ✅ Phase 2A-D: Core Contracts, Planner, Skills, Auth
- ✅ Phase 3: Production Hardening
- ✅ Phase 4: Multi-Step Execution
- ✅ Phase 5: Budget Protection + Prompt-Injection Gate
- ✅ 65 tests passing (97%)

### M2.5 Status — COMPLETE (2025-12-01)

| Deliverable | Status | Location |
|-------------|--------|----------|
| PlannerInterface protocol | ✅ Done | `backend/app/planner/interface.py` |
| StubPlanner (deterministic) | ✅ Done | `backend/app/planner/stub_planner.py` |
| LegacyStubPlanner | ✅ Done | `backend/app/planner/stub_planner.py` |
| PlannerRegistry | ✅ Done | `backend/app/planner/interface.py` |
| Planner Determinism Contract | ✅ Done | `backend/app/specs/planner_determinism.md` |
| Canonical JSON Rules | ✅ Done | `backend/app/specs/canonical_json.md` |
| canonical_json utility | ✅ Done | `backend/app/utils/canonical_json.py` |
| Version-Gating + Contract Diffing | ✅ Done | `backend/app/skills/registry_v2.py` |
| INFRA-001 Fix (CLOSE_WAIT) | ✅ Done | `backend/app/worker/runner.py` |
| Planner tests (35) | ✅ Done | `backend/tests/planner/test_interface.py` |

### M2 Status — COMPLETE (2025-12-01)

| Deliverable | Status | Location |
|-------------|--------|----------|
| SkillRegistry v2 | ✅ Done | `backend/app/skills/registry_v2.py` |
| Versioned skill resolution | ✅ Done | `backend/app/skills/registry_v2.py` |
| Persistence layer (sqlite) | ✅ Done | `backend/app/skills/registry_v2.py` |
| http_call stub | ✅ Done | `backend/app/skills/stubs/http_call_stub.py` |
| llm_invoke stub | ✅ Done | `backend/app/skills/stubs/llm_invoke_stub.py` |
| json_transform stub | ✅ Done | `backend/app/skills/stubs/json_transform_stub.py` |
| IntegratedRuntime | ✅ Done | `backend/app/worker/runtime/integrated_runtime.py` |
| Registry tests (27) | ✅ Done | `backend/tests/skills/test_registry_v2.py` |
| Stub tests (24) | ✅ Done | `backend/tests/skills/test_stubs.py` |
| Lazy imports (TECH-001) | ✅ Done | `backend/app/worker/__init__.py` |

### M1 Status — COMPLETE (2025-12-01)

| Deliverable | Status | Location |
|-------------|--------|----------|
| runtime.execute() | ✅ Done | `backend/app/worker/runtime/core.py` |
| runtime.describe_skill() | ✅ Done | `backend/app/worker/runtime/core.py` |
| runtime.query() | ✅ Done | `backend/app/worker/runtime/core.py` |
| runtime.get_resource_contract() | ✅ Done | `backend/app/worker/runtime/core.py` |
| StructuredOutcome | ✅ Done | `backend/app/worker/runtime/core.py` |
| SkillDescriptor | ✅ Done | `backend/app/worker/runtime/core.py` |
| ResourceContract | ✅ Done | `backend/app/worker/runtime/core.py` |
| Contract dataclasses | ✅ Done | `backend/app/worker/runtime/contracts.py` |
| StubPlanner example | ✅ Done | `backend/app/planner/stub_planner.py` |
| Interface tests (27) | ✅ Done | `backend/tests/runtime/test_m1_runtime.py` |
| Golden files | ✅ Done | `backend/tests/golden/` |
| Acceptance checklist | ✅ Done | `backend/tests/acceptance_runtime.md` |

### M0 Status — FINALIZED (2025-12-01)

| Deliverable | Status | Location |
|-------------|--------|----------|
| StructuredOutcome schema | ✅ Done | `backend/app/schemas/structured_outcome.schema.json` |
| SkillMetadata schema | ✅ Done | `backend/app/schemas/skill_metadata.schema.json` |
| ResourceContract schema | ✅ Done | `backend/app/schemas/resource_contract.schema.json` |
| AgentProfile schema | ✅ Done | `backend/app/schemas/agent_profile.schema.json` |
| Error taxonomy | ✅ Done | `backend/app/specs/error_taxonomy.md` |
| Determinism & Replay spec | ✅ Done | `backend/app/specs/determinism_and_replay.md` |
| CI pipeline | ✅ Done | `.github/workflows/ci.yml` |
| Test scaffold | ✅ Done | `backend/tests/conftest.py`, `backend/tests/README.md` |
| Schema golden files | ✅ Done | `backend/app/schemas/examples/` |
| Dev bootstrap script | ✅ Done | `scripts/bootstrap-dev.sh` |

### CI Guardrails (M0 Finalization)

| CI Job | Purpose |
|--------|---------|
| `lint` | Ruff + mypy type checking |
| `unit` | Schema and unit tests |
| `schema-validation` | JSON Schema draft-07 validation |
| `integration` | Integration tests with mocked services |
| `spec-check` | Verify required specs exist |
| `changelog-check` | Warn on schema changes without changelog |
| `replay-smoke` | Verify deterministic fields in golden files |
| `side-effect-order` | Verify side-effect ordering rules |
| `metadata-drift` | Warn on skill metadata changes without version bump |

### Determinism Spec Highlights

See `backend/app/specs/determinism_and_replay.md` for full details:

- **Field Stability Tables**: Defines which fields must be deterministic
- **Forbidden Fields**: Fields that MUST NOT affect determinism
- **Allowed Nondeterminism Zones**: External API content, LLM output, timing
- **Side-Effect Ordering**: Guaranteed stable order across replays
- **Retry Influence**: How retries affect replay assertions

### Next Immediate Actions (M3 - Core Skills)
1. Implement real http_call skill (with httpx)
2. Implement real llm_invoke skill (Anthropic Claude)
3. Implement real json_transform skill (jsonpath)
4. Create ClaudeAdapter for planner
5. Push repo + enable CI

### Key Architecture
- **Planner:** Anthropic Claude (`claude-sonnet-4-20250514`)
- **PlannerInterface:** Protocol for planner modularity
- **Rate Limiting:** Redis token bucket (100 req/min per tenant)
- **Concurrency:** Redis semaphore (5 concurrent per agent)
- **Budget:** Multi-layer enforcement (per-run, per-day, per-model, total)
- **Security:** Prompt injection detection, URL sanitization
- **Skills:** http_call, llm_invoke, json_transform, postgres_query, calendar_write
- **Tests:** 113 tests passing (M1:27 + M2:51 + M2.5:35)

---

## How to Use

### For AI Assistants
When resuming work on this project:
1. Read `INDEX.md` first
2. Read relevant active PINs for context
3. Check PIN status dates for freshness

### For Developers
1. Check INDEX for relevant specs before implementing
2. Update PINs when making architectural changes
3. Create new PINs for major decisions

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | M2.5 Planner Abstraction COMPLETE - 113 tests total passing |
| 2025-12-01 | Added PlannerInterface, StubPlanner, canonical JSON, version-gating |
| 2025-12-01 | Fixed INFRA-001 (CLOSE_WAIT leak), added runtime invariants tests |
| 2025-12-01 | Added PIN-010 M2 Completion Report - 78 tests passing |
| 2025-12-01 | M2 Skill Registration + Stubs COMPLETE - 78 tests total passing |
| 2025-12-01 | M1 Runtime Interfaces COMPLETE - 27 tests passing |
| 2025-12-01 | Added PIN-009 M0 Finalization Report - FINALIZED milestone |
| 2025-12-01 | Added PIN-008 v1 Milestone Plan (Full Detail) - PRIMARY reference |
| 2025-12-01 | Added PIN-007 v1 Milestone Plan (Summary) |
| 2025-12-01 | Added PIN-006 Execution Plan Review & Realistic Roadmap |
| 2025-12-01 | Added PIN-005 Machine-Native Architecture & Strategic Review |
| 2025-11-30 | Added PIN-004 Phase 4 & 5 Completion, updated Quick Reference |
| 2025-11-30 | Added PIN-003 Phase 3 Completion |
| 2025-11-30 | Created index with PIN-001 and PIN-002 |
