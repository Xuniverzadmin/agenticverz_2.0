# System Contracts Index

**Created:** 2025-12-25
**Status:** FROZEN - `contracts-stable-v1` (2025-12-25)

> **LOCK NOTICE:** All contracts are frozen as of Phase 4 completion.
> Phase 5 implementation must not modify contracts without explicit delta proposal.

---

## Contract Execution Order

| Order | Contract | Question Answered |
|-------|----------|-------------------|
| 1 | PRE-RUN | What must the system declare before execution starts? |
| 2 | CONSTRAINT | What constraints apply, and how are they enforced? |
| 3 | DECISION | What decisions must be surfaced when the system chooses a path? |
| 4 | OUTCOME | How do we reconcile what happened with what was promised? |

---

## Contract Files

| File | Version | Entries Covered |
|------|---------|-----------------|
| [PRE_RUN_CONTRACT.md](PRE_RUN_CONTRACT.md) | 0.1 | 3 |
| [CONSTRAINT_DECLARATION_CONTRACT.md](CONSTRAINT_DECLARATION_CONTRACT.md) | 0.1 | 2 |
| [DECISION_RECORD_CONTRACT.md](DECISION_RECORD_CONTRACT.md) | 0.2 | 4 |
| [OUTCOME_RECONCILIATION_CONTRACT.md](OUTCOME_RECONCILIATION_CONTRACT.md) | 0.1 | 4 |
| [O4_ADVISORY_UI_CONTRACT.md](O4_ADVISORY_UI_CONTRACT.md) | 0.2 | C2 UI |
| [O4_UI_ACCEPTANCE_CRITERIA.md](O4_UI_ACCEPTANCE_CRITERIA.md) | 0.2 (FROZEN) | O4 verification |
| [O4_UI_WIREFRAMES.md](O4_UI_WIREFRAMES.md) | 1.0 (FROZEN) | Implementation layouts |
| [O4_UI_COPY_BLOCKS.md](O4_UI_COPY_BLOCKS.md) | 1.0 (FROZEN) | Pre-approved language |
| [O4_RECERTIFICATION_CHECKS.md](O4_RECERTIFICATION_CHECKS.md) | 1.0 (ACTIVE) | CI enforcement |
| [C3_OPTIMIZATION_SAFETY_CONTRACT.md](C3_OPTIMIZATION_SAFETY_CONTRACT.md) | 1.0 (FROZEN) | C3 acceptance criteria |
| [C3_ENVELOPE_ABSTRACTION.md](C3_ENVELOPE_ABSTRACTION.md) | 1.0 (FROZEN) | C3 envelope schema & lifecycle |
| [C3_KILLSWITCH_ROLLBACK_MODEL.md](C3_KILLSWITCH_ROLLBACK_MODEL.md) | 1.0 (FROZEN) | C3 kill-switch & rollback |
| [C4_ENVELOPE_COORDINATION_CONTRACT.md](C4_ENVELOPE_COORDINATION_CONTRACT.md) | 1.0 (FROZEN) | C4 multi-envelope coordination rules |
| [C4_SYSTEM_LEARNINGS.md](C4_SYSTEM_LEARNINGS.md) | 2.0 (CERTIFIED) | Pre & post-implementation learnings |
| [C4_CI_GUARDRAILS_DESIGN.md](C4_CI_GUARDRAILS_DESIGN.md) | 1.0 (DESIGN) | C4 CI guardrails specification |
| [C4_S1_COORDINATION_SCENARIO.md](C4_S1_COORDINATION_SCENARIO.md) | 1.0 (DESIGN) | C4-S1 safe coexistence scenario |
| [C4_PAPER_SIMULATION_RECORD.md](C4_PAPER_SIMULATION_RECORD.md) | 1.0 (PASSED) | C4 paper simulation (T0-T7) |
| [C4_RECERTIFICATION_RULES.md](C4_RECERTIFICATION_RULES.md) | 1.0 (FROZEN) | C4 re-certification triggers (RC4-T1 to RC4-T8) |
| [C5_CI_GUARDRAILS_DESIGN.md](C5_CI_GUARDRAILS_DESIGN.md) | 1.0 (DESIGN) | C5 CI guardrails specification (CI-C5-1 to CI-C5-6) |
| [C5_S1_LEARNING_SCENARIO.md](C5_S1_LEARNING_SCENARIO.md) | 1.0 (FROZEN) | C5-S1 Learning from Rollback Frequency design |
| [C5_S1_ACCEPTANCE_CRITERIA.md](C5_S1_ACCEPTANCE_CRITERIA.md) | 1.0 (FROZEN) | C5-S1 acceptance criteria (26 tests) |
| [C5_S1_CI_ENFORCEMENT.md](C5_S1_CI_ENFORCEMENT.md) | 1.0 (FROZEN) | C5-S1 CI guardrails mapping |
| [C4_OPERATIONAL_STABILITY_CRITERIA.md](C4_OPERATIONAL_STABILITY_CRITERIA.md) | 1.0 (FROZEN) | Time-based stability gate (7 days) |
| [C4_FOUNDER_STABILITY_CRITERIA.md](C4_FOUNDER_STABILITY_CRITERIA.md) | 1.0 (FROZEN) | Synthetic stability gate (20 cycles) |
| [C4_SYNTHETIC_STABILITY_RUNBOOK.md](C4_SYNTHETIC_STABILITY_RUNBOOK.md) | 1.0 (ACTIVE) | 1-day synthetic stability execution guide |
| [C4_STABILITY_EVIDENCE_PACK.md](C4_STABILITY_EVIDENCE_PACK.md) | 1.1 (TEMPLATE) | Evidence pack (time-based + synthetic modes) |
| [C4_STABILITY_EVIDENCE_PACK_20251228.md](C4_STABILITY_EVIDENCE_PACK_20251228.md) | 1.0 (ATTESTED) | Synthetic stability evidence (2025-12-28) |
| [C4_COORDINATION_AUDIT_SCHEMA.md](C4_COORDINATION_AUDIT_SCHEMA.md) | 1.0 (DESIGN) | C4 coordination audit persistence schema |
| [visibility_contract.yaml](visibility_contract.yaml) | 1.0 | Phase B artifacts |
| [COVERAGE_MATRIX.md](COVERAGE_MATRIX.md) | - | 13 (validation) |
| [M0_M27_CLASSIFICATION.md](M0_M27_CLASSIFICATION.md) | - | 27 milestones |
| [OBLIGATION_DELTAS.md](OBLIGATION_DELTAS.md) | - | 2 deltas |

---

## Contract Gate Rule

Before any new scenario is processed:

```
1. Which contract does this scenario exercise?
2. Which obligation does it test?
3. Is this a new obligation or an existing one?
```

If these questions cannot be answered, the scenario is rejected.

---

## Related Documents

| Document | Location |
|----------|----------|
| Scenario Observation Contract | `docs/SCENARIO_OBSERVATION_CONTRACT.md` |
| System Truth Ledger | `docs/SYSTEM_TRUTH_LEDGER.md` |
| PIN-167 (Source Scenarios) | `docs/memory-pins/PIN-167-final-review-tasks-1.md` |

---

## Phase Status

| Phase | Status |
|-------|--------|
| Phase 1: Scenario Extraction | COMPLETE (13 entries) |
| Phase 2: Contract Drafting | COMPLETE (4 contracts) |
| Phase 3: M0-M27 Mapping | COMPLETE (27 milestones, 2 deltas, stabilized) |
| Phase 4A: Contract Evolution | COMPLETE (DECISION v0.2, deltas incorporated) |
| Phase 4B: Record Emission | COMPLETE (5 decision types + causal binding) |
| Phase 4C-1: Founder Consumption | COMPLETE (timeline API + causal binding validated) |
| Phase 4C-2: Customer Visibility | COMPLETE (PRE-RUN + acknowledge + outcome) |

---

## Phase 4B Results

**Completion Date:** 2025-12-25

### Decision Record Sink

| Component | Status |
|-----------|--------|
| Migration (049_decision_records) | Created |
| Schema (contracts.decision_records) | Defined |
| Service (DecisionRecordService) | Implemented |

### Instrumented Decision Types

| Type | File | Method |
|------|------|--------|
| Routing | `app/routing/care.py` | `route()` |
| Recovery | `app/worker/recovery_evaluator.py` | `evaluate()` |
| Policy | `app/policy/engine.py` | `evaluate()` |
| Memory | `app/memory/memory_service.py` | `get()` |
| Budget | `app/utils/budget_tracker.py` | `enforce_budget()` |

### Contract Compliance

| Check | Result |
|-------|--------|
| decision_source field | Emitted (system) |
| decision_trigger field | Emitted (explicit/reactive) |
| Ledger entries addressed | 5/13 (DECISION surface) |
| New ledger entries | 0 |

### Phase 4B Extension: Causal Binding (2025-12-25)

**Problem:** Pre-run decisions (routing, budget, policy) are emitted BEFORE run exists, creating a causality gap.

**Solution:**
- Added `request_id` as first-class causal key (always present for pre-run decisions)
- Added `causal_role` enum (pre_run, in_run, post_run)
- Implemented `backfill_run_id_for_request()` to bind pre-run decisions when run is created

| Component | Status |
|-----------|--------|
| Migration (050_decision_records_causal_binding) | Created |
| DecisionRecord model | Updated with request_id, causal_role |
| CARE routing emission | Updated with request_id |
| Budget emission | Updated with request_id |
| API /agents/{agent_id}/goals | Generates request_id, calls backfill |
| Founder Timeline API | Exposes request_id, causal_role |

**Validation Criteria:**
- Pre-run decisions have request_id
- After run creation, pre-run decisions have run_id (via backfill)
- Founder can trace causality: run_id → request_id → all pre-run decisions

**Validation Results (2025-12-25):**
- ✅ Pre-run emission verified (routing, budget with run_id=NULL, causal_role=pre_run)
- ✅ Backfill verified (pre-run decisions updated with run_id after run creation)
- ✅ Founder timeline reconstruction verified (chronological with causal_role)
- ✅ JSONB serialization fixed (json.dumps for decision_inputs, details)

---

## Phase 4C-1 Progress (Founder Consumption)

**Started:** 2025-12-25

### Founder Timeline API

| Endpoint | Purpose |
|----------|---------|
| `GET /founder/timeline/run/{run_id}` | Raw timeline for a run |
| `GET /founder/timeline/decisions` | List all decision records |
| `GET /founder/timeline/decisions/{id}` | Single decision record |
| `GET /founder/timeline/count` | Count records |

### Consumption Rules (Enforced)

- ❌ No aggregation
- ❌ No scoring
- ❌ No health indicators
- ❌ No automation
- ✅ Only filtered visibility of emitted records

### Fields Exposed to Founder

All fields visible:
- `decision_type`, `decision_source`, `decision_trigger`
- `decision_inputs`, `decision_outcome`, `decision_reason`
- `run_id`, `workflow_id`, `tenant_id`, `decided_at`, `details`
- `request_id`, `causal_role` (Phase 4B extension)

### Validation Status

| Check | Status |
|-------|--------|
| PIN-167 re-run | ✅ ADDRESSED (5/6 visibility gaps now have decision records) |
| No confusion reading timeline | ✅ VERIFIED (causal_role distinguishes pre_run/in_run) |
| No need to read code | ✅ VERIFIED (timeline shows decision chain with request_id→run_id) |

### Ledger Mapping

| Ledger Entry | Scenario | Surface | Now Addressed? |
|--------------|----------|---------|----------------|
| CARE routing missing | 2 | Decision | ✅ emit_routing_decision |
| Recovery disconnected | 3 | Decision | ✅ emit_recovery_decision |
| Budget advisory only | 1, 4 | Constraint | ✅ emit_budget_decision (enforcement field) |
| Memory invisible | 6 | Decision | ✅ emit_memory_decision |
| Policy not queryable | 4 | Intent | ❌ (Phase 4D: PRE-RUN surface) |

---

## Phase 4C-2 Results (Customer Visibility)

**Completion Date:** 2025-12-25

### Customer Visibility Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /customer/pre-run` | PRE-RUN declaration before execution |
| `POST /customer/acknowledge` | Customer acknowledgement gate |
| `GET /customer/outcome/{run_id}` | Outcome reconciliation after execution |
| `GET /customer/declaration/{id}` | Retrieve stored declaration |

### What Customers See

**PRE-RUN Declaration:**
- Stages (names and order)
- Cost estimate (min/max/estimate)
- Budget mode (hard/soft)
- Policy posture (strict/advisory)
- Memory mode (isolated/shared)

**Outcome Reconciliation:**
- Task status (success/warning/error)
- Budget status
- Policy status
- Recovery status

### What Customers DON'T See

- decision_source
- decision_trigger
- routing rejections
- recovery taxonomy
- request_id
- internal errors
- founder-only endpoints

### Validation (PIN-167 Predictability)

| Question | Answer |
|----------|--------|
| Can predict cost before running? | ✅ YES (estimated_cents, min/max range) |
| Warned about policy before running? | ✅ YES (posture: strict/advisory) |
| Understand result after running? | ✅ YES (decomposed outcomes) |
| Need to understand "decisions"? | ✅ NO (effects only, not mechanics) |

---

## Phase 3 Results

| Metric | Value |
|--------|-------|
| Milestones classified | 27 |
| Collapsed cleanly | 25 (93%) |
| New obligations | 2 (7%) |
| Stabilization achieved | M15-M27 (13 consecutive) |

### Contract Distribution (Primary)

| Contract | Count | Percentage |
|----------|-------|------------|
| CONSTRAINT | 9 | 33% |
| DECISION | 9 | 33% |
| OUTCOME | 5 | 19% |
| PRE-RUN | 4 | 15% |
