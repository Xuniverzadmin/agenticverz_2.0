# What Changes Require Which Phases

**Status:** AUTHORITATIVE
**Created:** 2025-12-31
**Reference:** PIN-254 (Phase A-D evidence), SESSION_PLAYBOOK.yaml v2.19 Section 29
**Purpose:** Map change types to required re-validation phases. No "safe by default" assumptions.

---

## How To Use This Guide

1. Identify the change type you're making
2. Find it in the table below
3. Run the required phase(s) before merge
4. If your change doesn't fit any category → STOP and escalate

**Rule:** Uncertainty means BLOCK, not "probably fine".

---

## Change Types → Required Phases

| Change Type | Example | Affected Artifacts | Required Phase(s) | Evidence |
|-------------|---------|-------------------|-------------------|----------|
| **New API endpoint** | `POST /ops/new-feature` | API surface, potential execution path | **Phase C** (API Truthfulness) | Phase C found 2 decorative APIs with no real execution (C01, C02 in `ops.py:2271-2286`) |
| **Modified API endpoint** | Change response shape of `/costsim/v2/simulate` | API contract, side-effect disclosure | **Phase C** | Phase C found undisclosed side effects in `/costsim/v2/simulate` (C05) |
| **Removed API endpoint** | Delete deprecated endpoint | Consumer breakage, orphan detection | **Phase C** + **Phase D** (if frontend calls it) | Phase C removed `/ops/jobs/detect-silent-churn` — required frontend audit |
| **New domain rule** | Add threshold to `CostModelEngine` | All downstream behavior | **Phase A** + **Phase B** | Phase A: domain rules must be in L4. Phase B: L3 must not duplicate |
| **Modified domain rule** | Change `confidence >= 0.8` to `0.7` in RecoveryRuleEngine | Execution behavior | **Phase A** (verify L5 still delegates) | Phase A found hardcoded `confidence >= 0.8` in `recovery_evaluator.py` (SHADOW-001) |
| **New domain engine** | Create `AuditEngine` | Authority boundaries | **Phase A** + **Phase B** + **Phase C** | New L4 engine requires full bottom-up verification |
| **New worker/job** | Add `archive_traces_worker.py` | Potential shadow domain logic | **Phase A** | Phase A enumerated 56 L5 actions — new workers must delegate to L4 |
| **Modified worker logic** | Change retry behavior in `worker_runtime.py` | Execution semantics, recovery rules | **Phase A** | Phase A found hardcoded heuristics in `failure_aggregation.py` (SHADOW-002, SHADOW-003) |
| **New adapter** | Create `StripeAdapter` | Translation integrity | **Phase B** | Phase B found 5 adapters with domain logic (B01-B05). New adapters must be translation-only |
| **Modified adapter** | Change mapping in `CostSimV2Adapter` | Translation integrity | **Phase B** | Phase B: `CostSimV2Adapter` had cost modeling logic (B02) |
| **Frontend action → mutation** | New button that calls `POST /agents` | F1, F2, F3 rules | **Phase D** (scoped) | Phase D verified 32 F1 entry points. New entry points require classification |
| **Frontend form submission** | New form that calls existing API | F1 mapping | **Phase D** (F1 check only) | Phase D: all entry points must map to registered L2 APIs |
| **Frontend conditional rendering based on eligibility** | Show/hide based on user tier | **F2 violation risk** | **Phase D** (F2 check) — **BLOCKING if authority** | F2: zero tolerance for client-side authority decisions |
| **Frontend auto-retry/cascade** | Automatic retry on failure | **F3 violation risk** | **Phase D** (F3 check) — **BLOCKING** | F3: no auto-fire without explicit user intent |
| **New persistence table** | Add `audit_events` table | State semantics, signal ownership | **Phase A** (who writes?) + **Signal Registry** | PIN-252: all signals must have producer/consumer mapping |
| **Modified table schema** | Add column to `runs` | Migration safety, semantic ownership | **Phase A** (if semantic) or **None** (if purely structural) | Depends on whether column carries domain meaning |
| **New signal/event emission** | Emit `COST_THRESHOLD_EXCEEDED` | Signal contract | **Signal Registry** + **Phase A** (if L5 emits) | PIN-252: Backend Signal Registry requires producer/consumer documentation |
| **New signal consumer** | New service consumes `RUN_COMPLETED` | Signal contract | **Signal Registry** | PIN-252: consumer must be registered |
| **Change in scheduling logic** | Modify cron timing for cost snapshots | Temporal coordination | **L8 Hygiene Check** | Phase C′: L7 must not contain domain logic |
| **New systemd timer/cron job** | Add `nightly-cleanup.timer` | L7 ops surface | **L8 Hygiene Check** | Phase C′: verified no domain decisions in L7 |
| **New external integration** | Add Slack webhook | Translation integrity, side effects | **Phase B** + **Phase C** | Phase B: adapters must be translation-only. Phase C: API must disclose side effects |
| **Modified external integration** | Change OpenAI model selection | Policy delegation | **Phase B** | Phase B: `OpenAIAdapter` had safety limits logic (B01), now delegates to `LLMPolicyEngine` |
| **New test file** | Add `test_cost_engine.py` | L8 containment | **L8 Hygiene Check** | Phase C′: tests must not import production services incorrectly |
| **CI workflow change** | Modify `.github/workflows/ci.yml` | L8 containment | **L8 Hygiene Check** | Phase C′: CI must not embed domain logic |
| **Refactor (same behavior)** | Rename function, move file | Import boundaries | **Import Boundary Check** (CI Tier 1) | Refactors with zero new transactions are safe work (Section 29) |
| **Refactor (behavior change)** | Change function signature affecting callers | Coupling analysis | **Depends on layer touched** | Must determine which layer owns the changed behavior |

---

## Uncertainty Handling

If a change type is not listed above:

| Situation | Required Action |
|-----------|-----------------|
| Change doesn't fit any category | **STOP** — escalate to governance review |
| Change spans multiple categories | Run **ALL** applicable phases |
| Unsure which category applies | **STOP** — ask before proceeding |
| "Probably fine" reasoning | **INVALID** — must have explicit evidence |

---

## Phase Quick Reference

| Phase | Question It Answers | Trigger Condition |
|-------|--------------------|--------------------|
| **Phase A** | Does L5 delegate to L4 for domain decisions? | New/modified worker, job, domain rule |
| **Phase B** | Is L3 translation-only (no domain logic)? | New/modified adapter |
| **Phase C** | Does L2 API have real execution path? Does it disclose constraints? | New/modified API endpoint |
| **Phase D** | Do L1 entry points map to registered L2 APIs? No authority leaks? | New/modified frontend transaction |
| **L8 Hygiene** | Is L8 free of runtime/domain/execution leaks? | New/modified test, CI, scheduler |
| **Signal Registry** | Is signal producer/consumer documented? | New/modified signal emission/consumption |
| **Import Boundary** | Do imports respect layer boundaries? | Any code change (CI Tier 1) |

---

## "Mini Phase" Definition

When a phase is triggered by a change, it runs as a **scoped phase**:

- **Same rules** as full phase
- **Same BLCA enforcement**
- **Smaller scope** (only affected artifacts)

"Mini" does NOT mean:
- Lighter rules
- Relaxed enforcement
- "Good enough" verification

---

## Evidence Sources

All mappings in this guide are derived from:

| Source | What It Proves |
|--------|---------------|
| Phase A violations (SHADOW-001 to SHADOW-003) | L5 can contain shadow domain logic |
| Phase B violations (B01-B05) | L3 adapters can contain domain logic |
| Phase C violations (C01-C05) | L2 APIs can be decorative or hide constraints |
| Phase D findings (32 F1 entry points) | Frontend actions create transactions |
| PIN-252 (Signal Registry) | Signals require producer/consumer mapping |
| Phase C′ (L8 Hygiene) | Tests/CI can leak into runtime |

---

## Worked Examples

### Example 1: "I want to add a new API endpoint"

1. Change type: **New API endpoint**
2. Required phase: **Phase C**
3. What to verify:
   - Endpoint has real execution path (not decorative)
   - Any derived values disclose methodology
   - Any side effects are disclosed
4. Evidence required: Trace from endpoint to execution

### Example 2: "I want to modify the cost threshold in CostModelEngine"

1. Change type: **Modified domain rule**
2. Required phase: **Phase A**
3. What to verify:
   - L5 workers still delegate to L4 (not hardcoding the old threshold)
   - No adapter caches the old value
4. Evidence required: Grep for hardcoded threshold in L5/L3

### Example 3: "I want to add a button that triggers agent deletion"

1. Change type: **Frontend action → mutation**
2. Required phase: **Phase D** (scoped)
3. What to verify:
   - F1: Button calls registered L2 API (`DELETE /agents/{id}`)
   - F2: No eligibility check in frontend (backend decides)
   - F3: No auto-cascade (single explicit action)
4. Evidence required: Frontend code trace to API call

### Example 4: "I want to refactor worker_runtime.py (no behavior change)"

1. Change type: **Refactor (same behavior)**
2. Required phase: **Import Boundary Check** (CI Tier 1)
3. What to verify:
   - No new transactions introduced
   - Import boundaries still respected
4. Evidence required: CI passes, no new exports

---

## Governance Integration

This guide is enforced by:

- **SESSION_PLAYBOOK.yaml v2.19 Section 29** (steady-state governance loop)
- **BLCA** (Bidirectional Layer Consistency Auditor)
- **CI Tier 1** (blocking structural checks)
- **CI Tier 2** (warning flags for semantic review)

Changes that bypass this guide are governance violations.

---

*Generated from Phase A-D evidence. Not from layer theory.*
*Reference: PIN-254, BIDIRECTIONAL_AUDIT_STATUS.md*
