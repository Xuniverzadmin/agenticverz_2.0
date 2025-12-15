# Repository Snapshot

**Date:** 2025-12-15
**Milestone:** M19 COMPLETE → M20 Planning
**CI Checker:** v5.0 (MN-OS dual-name support)

---

## Project Status

| Milestone | Status | PIN |
|-----------|--------|-----|
| M0-M7 | ✅ COMPLETE | PIN-009 to PIN-032 |
| M8: Demo + SDK + Auth | ✅ COMPLETE | PIN-033 |
| M9: Failure Catalog v2 | ✅ COMPLETE | PIN-048/049 |
| M10: Recovery Suggestion Engine | ✅ COMPLETE | PIN-050/057/061 |
| M11: Skill Expansion | ✅ COMPLETE | PIN-055/056/059/060 |
| M12: Multi-Agent System | ✅ COMPLETE | PIN-062/063 |
| M13: Console UI & Boundary | ✅ COMPLETE | PIN-064/067/068 |
| M14: BudgetLLM Safety | ✅ COMPLETE | PIN-070 |
| M15: SBA Foundations | ✅ COMPLETE | PIN-071/072/073 |
| M16: Agent Governance Console | ✅ COMPLETE | PIN-074 |
| M17: CARE Routing Engine | ✅ COMPLETE | PIN-075 |
| M18: CARE-L & SBA Evolution | ✅ COMPLETE | PIN-076/077 |
| **M19: Policy Constitutional** | ✅ **COMPLETE** | PIN-078 |
| M20: Machine-Native OS v1.0 | ⏳ PLANNING | - |

---

## Latest Session (2025-12-15)

### MN-OS Naming Evolution (PIN-081)

Established formal naming evolution from legacy milestone identifiers (M0-M19) to Machine-Native Operating System (MN-OS) subsystem names.

| Created | Purpose |
|---------|---------|
| `docs/mn-os/subsystem_mapping.md` | Canonical M→Subsystem mapping |
| `docs/mn-os/transition_guide.md` | Contributor/operator guide |
| `docs/mn-os/architecture_overview.md` | 6-layer architecture diagram |
| `docs/memory-pins/PIN-081-mn-os-naming-evolution.md` | Change documentation |

### CI Consistency Checker v5.0

- `--subsystems` flag for MN-OS dashboard view
- Dual-name recognition (legacy + MN-OS names)
- MNOS_NAME/MNOS_ACRONYM arrays
- All 20 milestones PASS

### Key MN-OS Subsystem Names

| Milestone | MN-OS Name | Acronym |
|-----------|------------|---------|
| M4 | Agent Execution Engine | **AXE** |
| M9 | System Failure Intelligence | **SFIL** |
| M15 | Strategic Agency Kernel | **SAK** |
| M17 | Cognitive Routing Kernel | **CRK** |
| M19 | OS Constitution | **OSC** |

---

## CI Status

**Latest Run:** [20234756645](https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/20234756645)
**Result:** ✅ 15/15 jobs PASS

| Job | Status |
|-----|--------|
| setup-neon-branch | ✅ |
| unit-tests | ✅ |
| lint-alerts | ✅ |
| migration-check | ✅ |
| run-migrations | ✅ |
| determinism | ✅ |
| workflow-engine | ✅ |
| costsim | ✅ |
| costsim-wiremock | ✅ |
| integration | ✅ |
| e2e-tests | ✅ |
| workflow-golden-check | ✅ |
| costsim-integration | ✅ |
| m10-tests | ✅ |

---

## Running Services

| Service | Container | Port |
|---------|-----------|------|
| Backend | nova_agent_manager | 8000 |
| Worker | nova_worker | - |
| Database | nova_db | 5433 |
| PgBouncer | nova_pgbouncer | 6432 |
| Redis | redis | 6379 |
| Prometheus | nova_prometheus | 9090 |
| Grafana | nova_grafana | 3000 |
| Vault | vault | 8200 |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Memory PINs | 81 |
| Migrations | 36 |
| Milestones Complete | 20/20 |
| CI Jobs Passing | 15/15 |
| MN-OS Subsystems | 20 |

---

## Pending Activities

### PIN-047: Polishing Tasks (P1-P3)

| Priority | Task |
|----------|------|
| P1 | Prometheus alert reload |
| P1 | Move remaining secrets to Vault |
| P2 | Quota status API endpoint |
| P2 | Embedding cost monitoring dashboard |
| P3 | Anthropic Voyage backup provider |
| P3 | Embedding cache layer |

### M20 Planning

- Unified syscall-like API
- Cross-subsystem communication bus
- Plugin architecture for extensions
- Marketplace for agents and skills

---

## Quick Commands

```bash
# Run CI consistency check
./scripts/ops/ci_consistency_check.sh

# View MN-OS subsystem dashboard
./scripts/ops/ci_consistency_check.sh --subsystems

# View milestone dashboard
./scripts/ops/ci_consistency_check.sh --milestone

# Check services
docker compose ps
```

---

*Last updated: 2025-12-15 (MN-OS Naming Evolution)*
