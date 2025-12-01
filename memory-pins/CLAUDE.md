# AgenticVerz 2.0 Memory Pin

## Project Overview
Nova AOS (Agent Operating System) - Machine-native runtime that is deterministic, replayable, contract-driven, testable, and never hides failures.

## Vision
- Deterministic state
- Replayable runs
- Contract-bound execution
- Observable behavior
- Testable guarantees
- Zero silent failures
- Planner-agnostic architecture

## Current Status
**M0 (Foundations & Contracts): FINALIZED**
**Next: M1 (Runtime Interfaces)**

## Milestone Roadmap

| Milestone | Name | Status |
|-----------|------|--------|
| M0 | Foundations & Contracts | ✅ FINALIZED |
| M1 | Runtime Interfaces | 🔄 NEXT |
| M2 | Skill Framework | ⏳ Pending |
| M3 | Integration Skills | ⏳ Pending |
| M4 | Planner Interface | ⏳ Pending |
| M5 | Observability | ⏳ Pending |
| M6 | Determinism Tests | ⏳ Pending |

## M0 Deliverables (Completed)

### Schemas (4)
- `backend/app/schemas/` - JSON schemas for contracts

### Specification Documents (2)
- `backend/app/specs/determinism_and_replay.md`
- `backend/app/specs/error_taxonomy.md`

### Golden Files (6)
- `backend/app/schemas/examples/structured_outcome_replayable.json`
- Other canonical examples

### CI Jobs (9)
| Job | Purpose |
|-----|---------|
| lint | Code style |
| type-check | Type validation |
| unit-tests | Core tests |
| schema-validate | JSON schema validation |
| spec-check | Spec consistency |
| replay-smoke | Deterministic field verification |
| side-effect-order | Side-effect ordering rules |
| metadata-drift | Skill version bump warnings |
| integration | End-to-end tests |

### Scripts
- `scripts/bootstrap-dev.sh` - Dev environment setup

## M1 Tasks (Next)

| Task | Priority | Location |
|------|----------|----------|
| Implement runtime.execute() | HIGH | backend/app/worker/runtime/execute.py |
| Implement runtime.describe_skill() | HIGH | backend/app/worker/runtime/describe_skill.py |
| Implement runtime.query() | HIGH | backend/app/worker/runtime/query.py |
| Implement runtime.get_resource_contract() | HIGH | backend/app/worker/contracts.py |
| Create interface tests | HIGH | backend/tests/runtime/test_execute.py |

## Pending Non-Blocking Items

| Item | Priority | Notes |
|------|----------|-------|
| INFRA-001: Fix test timeout | Medium | test_get_run_status container networking |
| Pydantic V2 migration | Low | 10 deprecation warnings, do after M1 |
| pytest-asyncio | Low | Needed for M3 async skills |
| Git repo push to GitHub | Low | CI won't run until pushed |

## Key Architectural Decisions

### Determinism Rules
- Field Stability Table: 16 fields classified
- Plan Field Stability: 10 fields classified
- Forbidden Fields: 7 fields that MUST NOT affect determinism
- Allowed Nondeterminism Zones: 5 zones documented

### Error Taxonomy (42+ codes)
- ERR_RATE_LIMIT_INTERNAL - Internal AOS throttling
- ERR_RATE_LIMIT_CONCURRENT - Concurrent runs limit
- ERR_BUDGET_EXCEEDED - Budget exhaustion
- ERR_HTTP_429 - Provider throttle
- See `backend/app/specs/error_taxonomy.md` for full list

## Important Paths
- Project root: `/root/agenticverz2.0/`
- Backend: `/root/agenticverz2.0/backend/`
- Schemas: `/root/agenticverz2.0/backend/app/schemas/`
- Specs: `/root/agenticverz2.0/backend/app/specs/`
- Tests: `/root/agenticverz2.0/backend/tests/`
- CI: `/root/agenticverz2.0/.github/workflows/ci.yml`
- Docker: `/root/agenticverz2.0/docker-compose.yml`

## Quick Commands

```bash
# Dev environment setup
./scripts/bootstrap-dev.sh

# Run tests
cd /root/agenticverz2.0 && source .venv/bin/activate && pytest

# Validate schemas
python -m pytest backend/tests/test_schemas.py

# Check docker status
docker ps -a | grep nova

# View container logs
docker logs nova_agent_manager --tail 50
```

## Constraints (M0 Lock)
From M0 finalization onwards:
- NO schema changes without version bump
- NO replay rule changes without changelog
- NO taxonomy changes without CI drift check pass
- All changes must pass CI guardrails
