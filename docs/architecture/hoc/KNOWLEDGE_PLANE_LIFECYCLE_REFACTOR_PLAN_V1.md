# Knowledge Plane Lifecycle Refactor Plan (V1)

**Scope:** Knowledge plane lifecycle (GAP-071..085, GAP-086)  
**Non-scope:** Tenant/integration/policy/api_key lifecycle harnessing (handled separately).  
**Goal:** Eliminate duplicate knowledge lifecycle implementations so **worker runtime, tests, and SDK** share one canonical lifecycle manager + one canonical stage handler set.

## Status (2026-02-08)

- **Canonical owner:** hoc_spine
- **Canonical surfaces:**
  - `app.hoc.cus.hoc_spine.orchestrator.lifecycle.stages`
  - `app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager`
  - `app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_sdk`
- **Legacy:** `app.services.lifecycle_stages.*`, `app.services.knowledge_lifecycle_manager`, and `app.services.knowledge_sdk` are compatibility shims (re-exports) only.
- **Verification evidence:** `pytest backend/tests/governance/t4 -q` (429 passed) and `pytest backend/tests/hoc_spine/test_hoc_spine_import_guard.py -q` (3 passed).

---

## 1) Audit (Current Reality)

### 1.1 Two Parallel Implementations Exist

- “Services” implementation (used by tests/SDK):
  - `backend/app/services/knowledge_lifecycle_manager.py`
  - `backend/app/services/knowledge_sdk.py`
  - `backend/app/services/lifecycle_stages/*`
- hoc_spine implementation (used by worker runtime):
  - stage engines: `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/*`
  - shared base types: `backend/app/hoc/cus/hoc_spine/services/lifecycle_stages_base.py`
  - worker imports hoc_spine engines directly: `backend/app/worker/lifecycle_worker.py`

### 1.2 Duplicate Base Types and Stage Engines

- Base type files are not identical; hoc_spine version is the newer HOC-scoped variant:
  - `backend/app/services/lifecycle_stages/base.py`
  - `backend/app/hoc/cus/hoc_spine/services/lifecycle_stages_base.py`
- Onboarding/offboarding stage handlers exist in both places, and have diverged (imports repointed in hoc_spine):
  - `backend/app/services/lifecycle_stages/onboarding.py`
  - `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py`

**Outcome:** “knowledge lifecycle” is split-brain across runtime and tests/SDK.

---

## 2) Target (First Principles)

### 2.1 One Canonical Knowledge Lifecycle System

There must be:
- one canonical KnowledgeLifecycleManager implementation
- one canonical StageRegistry/base-types implementation
- one canonical onboarding/offboarding stage handler set
- one worker entry path for driving transitions

### 2.2 Keep Knowledge Lifecycle Separate From Domain Lifecycle Harness

Knowledge plane lifecycle is a staged state machine (register→verify→ingest→index→activate…),
not an “entity status” lifecycle. It may reuse generic harness utilities (audit/idempotency)
but must remain a distinct subsystem with its own invariants and tests.

---

## 3) Decision Point: Choose the Canonical Owner

**Observed runtime truth:** workers already import hoc_spine stage engines:
- `backend/app/worker/lifecycle_worker.py`

So V1 plan assumes:
- hoc_spine is canonical for stage engines/base types
- “services” becomes a shim/re-export layer until deleted

If you prefer the opposite (services canonical), invert the repointing steps below.

---

## 4) Refactor Plan (Phased)

### Phase 0: Freeze the Contract Surface

1. Identify the canonical public imports required by:
   - governance tests (`backend/tests/governance/t4/*`)
   - SDK (`backend/app/services/knowledge_sdk.py`)
   - worker (`backend/app/worker/lifecycle_worker.py`)
2. Define a single canonical import surface under hoc_spine, for example:
   - `app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager`
   - `app.hoc.cus.hoc_spine.orchestrator.lifecycle.stages` (registry + handlers)

### Phase 1: Canonicalize Base Types

1. Make `backend/app/hoc/cus/hoc_spine/services/lifecycle_stages_base.py` the single source.
2. Change `backend/app/services/lifecycle_stages/base.py` into a compatibility shim that re-exports symbols from hoc_spine.

### Phase 2: Canonicalize Stage Engines

1. Make hoc_spine onboarding/offboarding engines canonical:
   - `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py`
   - `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/offboarding.py`
2. Change `backend/app/services/lifecycle_stages/onboarding.py` and `.../offboarding.py` into shims re-exporting hoc_spine engines, or delete after call sites are migrated.

### Phase 3: Canonicalize KnowledgeLifecycleManager

1. Move or replicate the manager into hoc_spine (canonical path), with minimal churn:
   - new file: `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_lifecycle_manager.py`
2. Make `backend/app/services/knowledge_lifecycle_manager.py` a shim that re-exports the hoc_spine manager (until callers move).

### Phase 4: SDK Alignment

1. Update `backend/app/services/knowledge_sdk.py` to import the canonical manager path.
2. If SDK is considered a “boundary adapter”, consider moving the SDK facade under HOC API/internal SDK surface later; keep the implementation canonical either way.

### Phase 5: Test Alignment

1. Update `backend/tests/governance/t4/*` to import the canonical hoc_spine manager/stages.
2. Ensure import guard still passes:
   - `pytest backend/tests/hoc_spine/test_hoc_spine_import_guard.py -q`

### Phase 6: Delete Duplicates (After Zero Importers)

Only after repo-wide import scan shows 0 non-shim imports, delete:
- `backend/app/services/lifecycle_stages/*`
- `backend/app/services/knowledge_lifecycle_manager.py`
- `backend/app/services/knowledge_sdk.py` (if relocated) or keep as boundary facade

---

## 5) Verification (Mechanical)

- `pytest backend/tests/governance/t4 -q`
- `pytest backend/tests/hoc_spine/test_hoc_spine_import_guard.py -q`
- `pytest backend/tests/workflow/test_golden_lifecycle.py -q` (if applicable)
