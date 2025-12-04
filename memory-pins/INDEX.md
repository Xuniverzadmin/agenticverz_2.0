# AgenticVerz 2.0 Memory Pins Index

> Last Updated: 2025-12-04
> Current Milestone: M5 GA (Policy & Observability)

## Memory Pin Files

| File | Purpose | Status |
|------|---------|--------|
| [CLAUDE.md](./CLAUDE.md) | Main memory pin - project overview, milestones, architecture | Active |
| [M0_FINALIZATION.md](./M0_FINALIZATION.md) | M0 completion report and deliverables | Complete |
| [PIN-009-EXTERNAL-ROLLOUT-PENDING.md](./PIN-009-EXTERNAL-ROLLOUT-PENDING.md) | **Pending items for external/production rollout** | **ACTIVE** |

---

## Project Status Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  AGENTICVERZ 2.0 (NOVA AOS)                                │
├─────────────────────────────────────────────────────────────┤
│  Vision: Deterministic, Replayable, Contract-Driven Runtime │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  M0 Foundations    [████████████████████] 100% FINALIZED   │
│  M1 Runtime        [░░░░░░░░░░░░░░░░░░░░]   0% NEXT        │
│  M2 Skills         [░░░░░░░░░░░░░░░░░░░░]   0% PENDING     │
│  M3 Integration    [░░░░░░░░░░░░░░░░░░░░]   0% PENDING     │
│  M4 Planner        [░░░░░░░░░░░░░░░░░░░░]   0% PENDING     │
│  M5 Observability  [░░░░░░░░░░░░░░░░░░░░]   0% PENDING     │
│  M6 Determinism    [░░░░░░░░░░░░░░░░░░░░]   0% PENDING     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## M0 Summary (FINALIZED)

### Deliverables
- 4 JSON Schemas
- 2 Specification Documents
- 6 Golden Files (examples)
- 9 CI Jobs
- 6 Test Files
- 1 Bootstrap Script

### Key Specs
- Determinism & Replay: `backend/app/specs/determinism_and_replay.md`
- Error Taxonomy (42+ codes): `backend/app/specs/error_taxonomy.md`

### CI Guardrails
| Job | Purpose |
|-----|---------|
| replay-smoke | Verify deterministic fields |
| side-effect-order | Verify ordering rules |
| metadata-drift | Warn on skill changes |

---

## M1 Tasks (NEXT)

Priority order:
1. `runtime.execute()` - Never throws, returns StructuredOutcome
2. `runtime.describe_skill()` - Returns SkillMetadata
3. `runtime.query()` - Budget, history, allowed skills
4. `runtime.get_resource_contract()` - Resource requirements
5. Interface tests + contract validation

---

## Pending Items (Non-Blocking)

| Item | Priority | When |
|------|----------|------|
| INFRA-001 test timeout | Medium | Before M3 |
| Pydantic V2 migration | Low | After M1 |
| pytest-asyncio | Low | Before M3 |
| Push to GitHub | Low | ASAP for CI |

---

## Instruction Set (Active)

### M0 Lock Rules
- NO schema changes without version bump
- NO replay rule changes without changelog
- NO taxonomy changes without CI pass

### Next Actions
1. ✅ M0 acknowledged as FINALIZED
2. ⏳ Create INFRA-001 ticket
3. ⏳ Add pytest-asyncio to requirements
4. ⏳ Plan Pydantic V2 migration (after M1)
5. ⏳ Push repo to GitHub
6. ⏳ Start M1 implementation

---

## Quick Reference

### Paths
```
/root/agenticverz2.0/
├── backend/
│   ├── app/
│   │   ├── schemas/      # JSON schemas
│   │   ├── specs/        # Determinism, errors
│   │   └── worker/       # Runtime (M1 target)
│   └── tests/
├── .github/workflows/    # CI
├── docker-compose.yml
└── memory-pins/          # This folder
```

### Commands
```bash
# Check status
docker ps | grep nova

# Run tests
cd /root/agenticverz2.0 && pytest

# View logs
docker logs nova_agent_manager --tail 50
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | M0 finalized, memory pins created |
| 2025-12-01 | Ready for M1 implementation |
