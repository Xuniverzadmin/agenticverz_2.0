# Repository Snapshot

**Date:** 2025-12-15
**Milestone:** M20 COMPLETE (MN-OS Layer 0)
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
| **M20: Policy Compiler & Runtime** | ✅ **COMPLETE** | PIN-084 |

---

## Latest Session (2025-12-15)

### Business Builder Worker v0.2 (PIN-086)

Implemented the first productized worker using 8+ moats from M0-M20:

| Component | Files |
|-----------|-------|
| Worker | `app/workers/business_builder/worker.py` |
| Execution Plan | `app/workers/business_builder/execution_plan.py` |
| Brand Schema | `app/workers/business_builder/schemas/brand.py` |
| Agent Definitions | `app/workers/business_builder/agents/definitions.py` |
| CLI | `app/workers/business_builder/cli.py` |
| Stages | `app/workers/business_builder/stages/` (research, strategy, copy, ux) |
| Tests | `tests/test_business_builder_worker.py` (33 tests) |

**Moat Integration:**
- M4: Golden replay via deterministic seeds
- M9: Failure pattern matching
- M10: Auto-recovery integration
- M15: 7 agents with real SBA schema
- M17: CARE routing for stages
- M18: Drift anchors and metrics
- M19/M20: Policy rules from brand constraints

**CLI Usage:**
```bash
python -m app.workers.business_builder.cli build-business "AI tool for podcasters" \
    --brand brand.json --budget 5000 --strict
```

---

### Worker Brainstorm & Moat Audit (PIN-085)

Comprehensive brainstorm session to identify product to build on M0-M20:

**35 Unique Moats Identified:**
- 15 individual moats (determinism, failure catalog, recovery, skills, etc.)
- 15 combined moats (synergies between milestones)
- 5 compound moats (3+ combined capabilities)

**GPT's "Launch Package Worker" Proposal:**
- Critiqued as using only ~15% of moats (2-3 actually exercised)
- Could be replicated with LangChain + GPT-4
- Missing: failure recovery, strategy binding, governance, learning loops

**Decision: Build Worker with Phased Moat Adoption**
| Phase | Focus | Moats |
|-------|-------|-------|
| 1 | Basic execution | M4, M11, M12 |
| 2 | Add constraints | + M15, M19 |
| 3 | Add learning | + M9, M18 |
| 4 | Full governance | + M17, M20 |

**Ideal Domain Properties:**
- Recurring decisions (M18 learning)
- Constraints/policies (M19/M20)
- Failure modes (M9/M10)
- Complexity variance (M17 CARE)
- Strategic alignment (M15 SBA)

---

### M20 Policy Compiler & Deterministic Runtime (PIN-084)

Implemented the Policy Compiler and Deterministic Runtime (MN-OS Layer 0):

| Component | Files |
|-----------|-------|
| PLang v2.0 Compiler | `app/policy/compiler/` (grammar, tokenizer, parser) |
| AST with Governance | `app/policy/ast/` (nodes, visitors) |
| IR v2.0 | `app/policy/ir/` (ir_nodes, symbol_table, ir_builder) |
| Governance-Aware Optimizer | `app/policy/optimizer/` (folds, conflict_resolver, dag_sorter) |
| Deterministic Runtime | `app/policy/runtime/` (deterministic_engine, dag_executor, intent) |

**Key Features:**
- PLang v2.0 grammar with M19 category support
- Category-aware execution ordering (SAFETY → PRIVACY → OPERATIONAL → ROUTING → CUSTOM)
- Conflict resolution using category precedence
- Deterministic execution with no randomness
- Intent emission to M18 for governance-aware execution
- Full audit trail for every execution

**MN-OS Subsystem:** Policy Execution Core (PXC)

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
| Memory PINs | 82 |
| Migrations | 36 |
| Milestones Complete | 20/20 |
| CI Jobs Passing | 15/15 |
| MN-OS Subsystems | 20 |

---

## Completed This Session

### PIN-047: Polishing Tasks ✅ COMPLETE

| Priority | Task | Status |
|----------|------|--------|
| P1 | Prometheus alert reload | ✅ 33 rule groups loaded |
| P1 | Move remaining secrets to Vault | ✅ All 6 in Vault |
| P2 | Quota status API endpoint | ✅ `/api/v1/embedding/quota` |
| P2 | Embedding cost monitoring dashboard | ✅ 13-panel Grafana dashboard |
| P3 | Anthropic Voyage backup provider | ✅ Auto-failover implemented |
| P3 | Embedding cache layer | ✅ Redis-based, 7-day TTL |

**New API Endpoints:**
- `GET /api/v1/embedding/health` (no auth)
- `GET /api/v1/embedding/quota`
- `GET /api/v1/embedding/config`
- `GET /api/v1/embedding/cache/stats`
- `DELETE /api/v1/embedding/cache`

**New Files:**
- `backend/app/api/embedding.py`
- `backend/app/memory/embedding_cache.py`
- `monitoring/grafana/.../embedding_cost_dashboard.json`

### IAEC v3.2 - Instruction-Aware Embedding Composer

Production-scale 4-slot embedding architecture with Transform DAG Manager, correction cooldown, and whitening versioning.

**v3.2 Features (Production Scale Ready):**
| Feature | Description |
|---------|-------------|
| Transform DAG Manager | Canonical paths, graph pruning, transitive collapsing for O(n²) prevention |
| Correction Cooldown | Monotonic correction policy prevents oscillation loops |
| Policy Softmax Folding | Normalized weights ensure sum=1.0 for deep stacks |
| Whitening Versioning | `whitening_basis_id` + `whitening_version` in all outputs for audit replay |

**v3.1 Features (Production Critical):**
| Feature | Description |
|---------|-------------|
| Temporal Mediation | Cross-version embedding transformation for safe mixing |
| 5-Level Policy (L0-L4) | Global/Org/AgentClass/AgentInstance/Task hierarchy with folding |
| Corrective Action | Prescriptive mismatch resolution with confidence scores |
| Whitening Persistence | Version-locked matrix storage in `/tmp/iaec/` |

**v3.0 Features (preserved):**
| Feature | Description |
|---------|-------------|
| 4-Slot Architecture | Instruction + Query + Context + Temporal + Policy |
| Reversible Decomposition | SlotBasis stores original vectors for weighted mode |
| Temporal Signature | 32-dim slot for model drift detection |
| Deep Mismatch Detection | Embedding-based semantic compatibility |
| Self-Verifier | Slot integrity validation |

**API Endpoints:**
- `POST /api/v1/embedding/compose` - Compose with policy/temporal/whitening versioning
- `POST /api/v1/embedding/decompose` - Extract 5 slots from vector
- `POST /api/v1/embedding/iaec/check-mismatch` - Deep mismatch with corrective action + cooldown
- `GET /api/v1/embedding/iaec/segment-info` - Slot layout info
- `GET /api/v1/embedding/iaec/instructions` - Instruction types/weights

**New Metrics (v3.2):**
- `aos_iaec_dag_transforms_total` - Transform DAG operations (prune, collapse, canonical_path)
- `aos_iaec_correction_cooldowns_total` - Correction cooldown events (window_limit, monotonic_block)
- `aos_iaec_policy_softmax_total` - Policy folding with softmax normalization

**Metrics (v3.1):**
- `aos_iaec_temporal_mediations_total` - Cross-version transformations
- `aos_iaec_corrective_actions_total` - Prescriptive actions issued
- `aos_iaec_policy_folding_total` - Multi-level policy folding
- `aos_iaec_whitening_loads_total` - Whitening matrix disk loads

**File:**
- `backend/app/memory/iaec.py` (~2100 lines)

---

## Pending Activities

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

*Last updated: 2025-12-15 (IAEC v3.1 Implementation Complete - Production Ready)*
