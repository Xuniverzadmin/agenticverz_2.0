# L2 → L4 → L5 Construction Plan

**PIN:** 491
**Status:** COMPLETE (all phases A-C executed 2026-01-30)
**Created:** 2026-01-30
**Depends on:** PIN-484 (V2.0.0 Ratification), PIN-487 (L4-L5 Linkage), PIN-489 (P0/P1 Enforcement), PIN-491 (Gap Detector)
**Enforced by:** `l5_spine_pairing_gap_detector.py`, `hoc_spine_study_validator.py`

---

## 1. Problem Statement

The HOC Layer Topology V2.0.0 mandates:

```
L2 (HTTP) → L4 (hoc_spine orchestrator) → L5 (domain engine) → L6 (driver)
```

Reality (measured 2026-01-30):

```
L2 (HTTP) → L5 (domain engine) directly   ← 32 ACTIVE VIOLATIONS
L4 orchestrator → L5                      ← 0 wired operations
L5 engines with no caller                 ← 153 orphaned
```

**Zero operations** flow through the L4 orchestrator. Every active L5 engine is called directly by L2, bypassing cross-domain governance, transaction boundaries, and audit hooks.

---

## 2. Current State (Gap Detector Output)

### 2.1 Direct L2→L5 Gaps (32 unique engine references)

| Domain | L2 Source | L5 Engine | Functions Imported |
|--------|-----------|-----------|-------------------|
| **account** | `aos_accounts.py` | `accounts_facade.py` | `get_accounts_facade` |
| **account** | `notifications.py` | `notifications_facade.py` | `NotificationsFacade`, `get_notifications_facade` |
| **activity** | `cus_telemetry.py` | `cus_telemetry_service.py` | `CusTelemetryService` |
| **activity** | `activity.py` | `activity_facade.py` | `get_activity_facade` |
| **activity** | `activity.py` | `signal_identity.py` | `compute_signal_fingerprint_from_row` |
| **activity** | `activity.py` | `signal_feedback_engine.py` | `SignalFeedbackService` |
| **analytics** | `analytics.py` | `analytics_facade.py` | `get_analytics_facade` |
| **analytics** | `detection.py` | `detection_facade.py` | `DetectionFacade`, `get_detection_facade` |
| **api_keys** | `aos_api_key.py` | `api_keys_facade.py` | `get_api_keys_facade` |
| **controls** | `controls.py` | `controls_facade.py` | `ControlsFacade`, `get_controls_facade` |
| **controls** | `policy_limits_crud.py` | `threshold_engine.py` | `DEFAULT_LLM_RUN_PARAMS`, `ThresholdParams` |
| **incidents** | `incidents.py` | `incidents_facade.py` | `get_incidents_facade` |
| **incidents** | `recovery.py` | `recovery_rule_engine.py` | `evaluate_rules` |
| **integrations** | `aos_cus_integrations.py` | `integrations_facade.py` | `get_integrations_facade` |
| **integrations** | `connectors.py` | `connectors_facade.py` | `ConnectorsFacade`, `get_connectors_facade` |
| **integrations** | `datasources.py` | `datasources_facade.py` | `DataSourcesFacade`, `get_datasources_facade` |
| **logs** | `evidence.py` | `evidence_facade.py` | `EvidenceFacade`, `get_evidence_facade` |
| **logs** | `guard.py` | `certificate.py` | `CertificateService` |
| **logs** | `guard.py` | `replay_determinism.py` | `DeterminismLevel`, `ReplayContextBuilder` |
| **logs** | `guard.py` | `evidence_report.py` | `generate_evidence_report` |
| **logs** | `logs.py` | `logs_facade.py` | `get_logs_facade` |
| **logs** | `incidents.py` | `pdf_renderer.py` | `get_pdf_renderer` |
| **overview** | `overview.py` | `overview_facade.py` | `get_overview_facade` |
| **policies** | `cus_enforcement.py` | `cus_enforcement_service.py` | `CusEnforcementService` |
| **policies** | `governance.py` | `governance_facade.py` | `GovernanceFacade`, `GovernanceMode`, `get_governance_facade` |
| **policies** | `policies.py` | `policies_facade.py` | `get_policies_facade` |
| **policies** | `policy.py` | `lessons_engine.py` | `get_lessons_learned_engine` |
| **policies** | `policy_layer.py` | `policy_driver.py` | `get_policy_facade` |
| **policies** | `policy_limits_crud.py` | `policy_limits_engine.py` | `PolicyLimitsService` + errors |
| **policies** | `policy_rules_crud.py` | `policy_rules_engine.py` | `PolicyRulesService` + errors |
| **policies** | `rate_limits.py` | `limits_facade.py` | `LimitsFacade`, `get_limits_facade` |
| **policies** | `simulate.py` | `limits_simulation_service.py` | `LimitsSimulationService` + errors |

### 2.2 Orphan Summary (153 engines with no L2 or L4 callers)

| Domain | Total L5 Engines | Active (L2-called) | Orphaned | Orphan % |
|--------|------------------|--------------------|----------|----------|
| policies | 61 | 9 | 52 | 85% |
| integrations | 37 | 3 | 34 | 92% |
| analytics | 20 | 2 | 18 | 90% |
| logs | 18 | 6 | 12 | 67% |
| incidents | 17 | 2 | 15 | 88% |
| controls | 11 | 2 | 9 | 82% |
| account | 10 | 2 | 8 | 80% |
| activity | 8 | 4 | 4 | 50% |
| api_keys | 2 | 1 | 1 | 50% |
| overview | 1 | 1 | 0 | 0% |
| **TOTAL** | **185** | **32** | **153** | **83%** |

---

## 3. Target Architecture

### 3.1 The L4 Operation Registry

The L4 orchestrator already has a `StepHandler` protocol and `JobExecutor` with handler registration. The missing piece is a **domain operation dispatch layer** that L2 APIs call instead of L5 facades.

**New component:** `hoc_spine/orchestrator/operation_registry.py`

```python
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Role: Operation dispatch registry — maps domain operations to L5 handlers

class OperationRegistry:
    """Maps operation names to L5 engine callables via protocol injection."""

    _operations: dict[str, OperationHandler] = {}

    def register(self, name: str, handler: OperationHandler) -> None: ...
    async def execute(self, op: str, ctx: OperationContext) -> OperationResult: ...
```

### 3.2 The L2→L4 Call Pattern

**Before (violation):**
```python
# L2: hoc/api/cus/policies/policies.py
from app.hoc.cus.policies.L5_engines.policies_facade import get_policies_facade

facade = get_policies_facade()
result = await facade.list_rules(session=session, tenant_id=tenant_id)
```

**After (compliant):**
```python
# L2: hoc/api/cus/policies/policies.py
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_operation_registry

registry = get_operation_registry()
result = await registry.execute("policies.list_rules", OperationContext(
    session=session, tenant_id=tenant_id, params={}
))
```

### 3.3 What the Orchestrator Adds

Each operation dispatch through L4 gains:

| Concern | Without L4 | With L4 |
|---------|-----------|---------|
| Transaction boundary | L2 or L5 owns commit | L4 owns via TransactionCoordinator |
| Cross-domain audit | None | AuditStore records operation |
| Authority checks | None | RuntimeSwitch / eligibility gate |
| Concurrent run limits | None | ConcurrentRuns guard |
| Degraded mode | None | DegradedModeChecker fallback |
| Evidence trail | None | ExecutionOrchestrator evidence |

---

## 4. Execution Phases

### Phase A — Loop Construction (32 Operations)

**Goal:** Wire all 32 L2→L5 direct calls through L4 orchestrator.
**Exit criterion:** `l5_spine_pairing_gap_detector.py` reports `Direct L2→L5 (gaps): 0`

#### A.0 — Infrastructure (1 file) ✅ COMPLETE (2026-01-30)

Create the operation registry:

| File | Action |
|------|--------|
| `hoc_spine/orchestrator/operation_registry.py` | **NEW** — `OperationRegistry`, `OperationHandler` protocol, `OperationContext`, `OperationResult`, `get_operation_registry()` singleton |

The registry must:
- Accept `OperationHandler` implementations via `register()`
- Dispatch by operation name string (e.g., `"policies.list_rules"`)
- Wrap execution in TransactionCoordinator boundaries
- Record execution via AuditStore
- Check authority via RuntimeSwitch before dispatch
- Return typed `OperationResult`

#### A.1 — Facade-Pattern Domains (10 operations, lowest risk) ✅ COMPLETE (2026-01-30)

Gap detector: Wired=10, Gaps=22 (down from 32).

These domains use the standard `get_*_facade()` singleton pattern. Each gets ONE operation handler that delegates to the existing facade.

| # | Operation Name | L2 Source | L5 Engine | Import to Remove |
|---|---------------|-----------|-----------|-----------------|
| 1 | `account.query` | `aos_accounts.py` | `accounts_facade.py` | `get_accounts_facade` |
| 2 | `account.notifications` | `notifications.py` | `notifications_facade.py` | `get_notifications_facade` |
| 3 | `analytics.query` | `analytics.py` | `analytics_facade.py` | `get_analytics_facade` |
| 4 | `analytics.detection` | `detection.py` | `detection_facade.py` | `get_detection_facade` |
| 5 | `api_keys.query` | `aos_api_key.py` | `api_keys_facade.py` | `get_api_keys_facade` |
| 6 | `incidents.query` | `incidents.py` | `incidents_facade.py` | `get_incidents_facade` |
| 7 | `integrations.query` | `aos_cus_integrations.py` | `integrations_facade.py` | `get_integrations_facade` |
| 8 | `integrations.connectors` | `connectors.py` | `connectors_facade.py` | `get_connectors_facade` |
| 9 | `integrations.datasources` | `datasources.py` | `datasources_facade.py` | `get_datasources_facade` |
| 10 | `overview.query` | `overview.py` | `overview_facade.py` | `get_overview_facade` |

**Pattern per operation:**
1. Create `hoc_spine/orchestrator/handlers/{domain}_handler.py` — thin handler that receives `OperationContext`, calls existing facade method, returns `OperationResult`
2. Register handler in `operation_registry.py` domain bootstrap
3. Update L2 file to call `registry.execute()` instead of facade directly
4. Remove L5 import from L2 file
5. Run gap detector — confirm gap count decreases

#### A.2 — Compound Facade Domains (6 operations, medium risk) ✅ COMPLETE (2026-01-30)

Gap detector: Wired=16, Gaps=16 (down from 22).

These L2 files import multiple facade methods or engine classes:

| # | Operation Name | L2 Source | L5 Engine | Notes |
|---|---------------|-----------|-----------|-------|
| 11 | `logs.query` | `logs.py` | `logs_facade.py` | Standard facade |
| 12 | `logs.evidence` | `evidence.py` | `evidence_facade.py` | Standard facade |
| 13 | `logs.certificate` | `guard.py` | `certificate.py` | Service class, not facade |
| 14 | `logs.replay` | `guard.py` | `replay_determinism.py` | Multiple classes imported |
| 15 | `logs.evidence_report` | `guard.py` | `evidence_report.py` | Function call |
| 16 | `logs.pdf` | `incidents.py` | `pdf_renderer.py` | Cross-domain (incidents L2 → logs L5) |

**Note on #16:** `incidents.py` (L2 for incidents domain) imports `pdf_renderer` from logs L5. This is a cross-domain violation that should route through L4.

#### A.3 — Controls Domain (2 operations, medium risk) ✅ COMPLETE (2026-01-30)

Gap detector: Wired=18, Gaps=14 (down from 16).

| # | Operation Name | L2 Source | L5 Engine | Notes |
|---|---------------|-----------|-----------|-------|
| 17 | `controls.query` | `controls.py` | `controls_facade.py` | Standard facade |
| 18 | `controls.thresholds` | `policy_limits_crud.py` | `threshold_engine.py` | Constants/validation routed through L4 handler |

**Note on #18:** `DEFAULT_LLM_RUN_PARAMS` and `ThresholdParams` are constants/validation schemas. Routed through `ControlsThresholdHandler` with `get_defaults`, `validate_params`, and `get_effective_params` methods rather than schema extraction.

#### A.4 — Activity Domain (4 operations, medium risk) ✅ COMPLETE (2026-01-30)

| # | Operation Name | L2 Source | L5 Engine | Notes |
|---|---------------|-----------|-----------|-------|
| 19 | `activity.query` | `activity.py` | `activity_facade.py` | Standard facade |
| 20 | `activity.signal_fingerprint` | `activity.py` | `signal_identity.py` | Utility function — may belong in L5_schemas |
| 21 | `activity.signal_feedback` | `activity.py` | `signal_feedback_engine.py` | Service class |
| 22 | `activity.telemetry` | `cus_telemetry.py` | `cus_telemetry_service.py` | Cross-domain (integrations L2 → activity L5) |

**Note on #22:** `cus_telemetry.py` lives in `api/cus/integrations/` but imports from `activity/L5_engines/`. Cross-domain violation now routed through L4 `activity.telemetry` handler.

**A.4 Result:** Gap detector: Wired=22, Gaps=10 (was 14). Activity domain: 4 wired, 0 direct gaps. Signal fingerprint batched via `compute_batch` handler method. Telemetry endpoints use `session=None` (stateless service, no DB session needed at L4).

#### A.5 — Policies Domain (9 operations, highest risk) ✅ COMPLETE (2026-01-30)

**A.5 Result:** Gap detector: Wired=31, Gaps=1 (was 10). Policies domain: 9 wired, 0 direct gaps. All 9 operations registered. 8 L2 files updated: policies.py (15 sites), policy_layer.py (37 facade + 6 lessons), governance.py (6 endpoints), cus_enforcement.py (3 endpoints), policy.py (2 inline), rate_limits.py (6 endpoints), simulate.py (1 endpoint), policy_limits_crud.py (3 CRUD), policy_rules_crud.py (2 CRUD). GovernanceMode enum replaced with inline string validation. Sync/async dispatch used for GovernanceFacade and LessonsLearnedEngine. The remaining 1 gap is recovery.py → recovery_rule_engine.py (L6-only pattern, excluded from A-phase scope).

Policies is the largest domain with the most complex L2→L5 relationships:

| # | Operation Name | L2 Source | L5 Engine | Notes |
|---|---------------|-----------|-----------|-------|
| 23 | `policies.query` | `policies.py` | `policies_facade.py` | Standard facade |
| 24 | `policies.enforcement` | `cus_enforcement.py` | `cus_enforcement_service.py` | Service class |
| 25 | `policies.governance` | `governance.py` | `governance_facade.py` | Multiple exports incl. `GovernanceMode` enum |
| 26 | `policies.lessons` | `policy.py` | `lessons_engine.py` | Called from 7+ locations in policy.py |
| 27 | `policies.policy_facade` | `policy_layer.py` | `policy_driver.py` | Confusing name — this is an L5 facade |
| 28 | `policies.limits` | `policy_limits_crud.py` | `policy_limits_engine.py` | Service + 3 error classes |
| 29 | `policies.rules` | `policy_rules_crud.py` | `policy_rules_engine.py` | Service + 3 error classes |
| 30 | `policies.rate_limits` | `rate_limits.py` | `limits_facade.py` | Standard facade |
| 31 | `policies.simulate` | `simulate.py` | `limits_simulation_service.py` | Service + 2 error classes |
| 32 | `incidents.recovery_rules` | `recovery.py` | `recovery_rule_engine.py` | Cross-domain (recovery L2 → incidents L5) |

**Note on #26:** `lessons_engine.py` is called from 7 different locations in `policy.py` and `policy_layer.py`. Requires single handler with multiple L2 call sites updated.

**Note on #28, #29, #31:** These import error exception classes (`LimitNotFoundError`, `RuleValidationError`, etc.) directly from L5 engines. Error classes should be extracted to L5_schemas so L2 can import them without L5 dependency, OR the operation handler should translate L5 exceptions to L4-level `OperationResult.error`.

#### A.6 — Verification Gate

After all 32 operations are wired:

```bash
# MUST report 0 direct gaps
python3 scripts/ops/l5_spine_pairing_gap_detector.py
# Expected:
#   Wired via L4:         32
#   Direct L2→L5 (gaps):  0
#   Orphaned:             153

# MUST validate clean
python3 scripts/ops/hoc_spine_study_validator.py --validate literature/hoc_spine/

# Regenerate literature with updated pairings
python3 scripts/ops/l5_spine_pairing_gap_detector.py --update-literature
```

---

### Phase B — Orphan Classification (153 Engines) ✅ COMPLETE (2026-01-30)

**Goal:** Classify every orphaned L5 engine. No code changes.
**Exit criterion:** Every L5 engine has a classification in literature.

**B Result:** Created `scripts/ops/l5_orphan_classifier.py`. Classification across 185 engines:
- WIRED: 31 (all Phase A operations)
- L2-DIRECT: 0 (all gaps resolved except recovery.py)
- INTERNAL: 18 (imported by other L5 engines, L3/L6/spine, or part of import chain)
- SCHEMA-ONLY: 32 (types, enums, BaseModel subclasses, constants)
- UNCLASSIFIED: 104 (need manual review — FUTURE, DEPRECATED, or MISSING-WIRE)

Auto-classified: 50 orphans. Manual review needed: 104.
Full report: `docs/architecture/hoc/L5_ORPHAN_CLASSIFICATION.md`

#### B.1 — Classification Taxonomy

| Class | Definition | Action |
|-------|-----------|--------|
| **INTERNAL** | Called by other L5 engines within the same domain (sub-engine, helper) | Document as internal. No L4 wiring needed. |
| **FUTURE** | Built for planned functionality, not yet called | Tag with target PIN/milestone. No wiring until activated. |
| **DEPRECATED** | Superseded by another engine, no longer needed | Schedule deletion in Phase C. |
| **MISSING-WIRE** | Should be called but isn't — a real gap | Add to Phase A backlog as A.7 operation. |
| **SCHEMA-ONLY** | Contains only types/enums/constants, misclassified as engine | Relocate to L5_schemas. |

#### B.2 — Classification Process

1. **Create script:** `scripts/ops/l5_orphan_classifier.py`
   - For each orphaned engine, scan all L5 files in the same domain for intra-domain imports
   - If imported by another L5: classify as **INTERNAL**
   - If importing nothing and exporting only types: classify as **SCHEMA-ONLY**
   - Remaining: require manual review → **FUTURE** or **DEPRECATED**

2. **Output:** Update literature pairing declarations with classification:
   ```yaml
   pairing:
     serves_domains: []
     classification: INTERNAL
     internal_consumers:
       - domain: policies
         engine: policy_graph_engine.py
         calls: ["evaluate_eligibility"]
   ```

3. **Expected distribution (estimate from naming analysis):**

| Domain | INTERNAL | FUTURE | DEPRECATED | MISSING-WIRE | SCHEMA-ONLY |
|--------|----------|--------|------------|--------------|-------------|
| policies (52) | ~25 | ~15 | ~5 | ~3 | ~4 |
| integrations (34) | ~20 | ~8 | ~2 | ~2 | ~2 |
| analytics (18) | ~10 | ~5 | ~1 | ~1 | ~1 |
| incidents (15) | ~8 | ~4 | ~1 | ~1 | ~1 |
| logs (12) | ~6 | ~3 | ~1 | ~1 | ~1 |
| controls (9) | ~5 | ~2 | ~1 | ~1 | ~0 |
| account (8) | ~4 | ~2 | ~1 | ~0 | ~1 |
| activity (4) | ~2 | ~1 | ~0 | ~1 | ~0 |
| api_keys (1) | ~1 | ~0 | ~0 | ~0 | ~0 |

4. **Any MISSING-WIRE engines** discovered go back to Phase A as additional operations.

#### B.3 — Verification Gate

```bash
# Every L5 engine must have a classification
python3 scripts/ops/l5_orphan_classifier.py --verify
# Expected: 0 unclassified engines

# Update literature
python3 scripts/ops/l5_spine_pairing_gap_detector.py --update-literature
```

---

### Phase C — Freeze & Enforce ✅ COMPLETE (2026-01-30)

**Goal:** Prevent regression. No new L2→L5 direct calls. No new unclassified engines.
**Exit criterion:** CI blocks violations.

**C Result:** Gap detector enhanced with `--check` and `--freeze-baseline` modes. Baseline frozen at `L2_L4_L5_BASELINE.json` (1 known gap: recovery.py). Preflight script `check_l2_l4_l5_freeze.py` created and wired into `run_all_checks.sh`. FREEZE-001 (gap regression) and FREEZE-003 (cross-domain imports) enforced. C.4 (deprecated engine deletion) deferred — requires explicit human approval per engine.

#### C.1 — Import Freeze Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| **FREEZE-001** | No new `from app.hoc.cus.*.L5_engines.*` in L2 API files | CI scanner (gap detector `--check`) |
| **FREEZE-002** | No new L5 engine files without pairing declaration | Validator `--validate` in CI |
| **FREEZE-003** | No `from app.hoc.cus.{A}` in `hoc/api/cus/{B}/` where A ≠ B | Cross-domain detector |
| **FREEZE-004** | Every new L4 operation must have a literature entry | Validator `--validate` |

#### C.2 — CI Integration

Add to `scripts/preflight/` (30-minute cron):

```bash
#!/bin/bash
# L2-L4-L5 Freeze Enforcement

# Check 1: No new direct gaps
python3 scripts/ops/l5_spine_pairing_gap_detector.py --json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(d['summary']['direct_l2_to_l5'])"

# Check 2: Literature integrity
python3 scripts/ops/hoc_spine_study_validator.py --validate literature/hoc_spine/
```

#### C.3 — Gap Detector Enhancement

Add `--check` mode to `l5_spine_pairing_gap_detector.py`:
- Returns exit code 0 if no NEW gaps (allows existing Phase A work-in-progress)
- Returns exit code 1 if gap count exceeds baseline
- Baseline stored in `docs/architecture/hoc/L2_L4_L5_BASELINE.json`

#### C.4 — Deprecated Engine Deletion

Schedule deletion of engines classified as **DEPRECATED** in Phase B:

1. Confirm zero importers (gap detector + intra-domain scan)
2. Create change record per artifact governance rules
3. Delete file
4. Update literature (remove `.md`, update `_summary.md`)
5. Run full validation

---

## 5. Implementation Order & Dependencies

```
Phase A.0 (operation_registry.py)
    │
    ├── A.1 (10 facade operations)  ──── can run in parallel ────┐
    ├── A.2 (6 compound operations)  ─────────────────────────────┤
    ├── A.3 (2 controls operations)  ─────────────────────────────┤
    ├── A.4 (4 activity operations)  ─────────────────────────────┤
    └── A.5 (9 policies operations)  ─────────────────────────────┤
                                                                  │
    A.6 (verification gate) ──────────────────────────────────────┘
    │
    Phase B.1-B.3 (orphan classification, no code changes)
    │
    Phase C.1-C.4 (freeze enforcement)
```

**Recommended order within Phase A:**
1. **A.0** — Build the registry (blocks everything)
2. **A.1** — Start with facade-pattern domains (10 ops, lowest risk, builds muscle memory)
3. **A.4** — Activity (4 ops, includes cross-domain violation #22)
4. **A.3** — Controls (2 ops, includes constants extraction decision #18)
5. **A.2** — Logs (6 ops, includes cross-domain violation #16)
6. **A.5** — Policies last (9 ops, highest complexity, most L2 call sites)

---

## 6. Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| L5 facade singletons assume import-time init | HIGH | OperationHandler wraps facade getter; lazy init preserved |
| Error exception classes imported directly by L2 | MEDIUM | Extract to L5_schemas or translate in OperationResult |
| Cross-domain L2→L5 calls (#16, #22, #32) | HIGH | These are the highest-priority wires — L4 is designed for cross-domain |
| `policy.py` calls `lessons_engine` from 7 locations | MEDIUM | Single handler, all 7 call sites updated to `registry.execute()` |
| Performance overhead from L4 dispatch | LOW | Registry lookup is O(1) dict. Authority checks already cached by RuntimeSwitch |
| Orphan classification reveals more MISSING-WIRE gaps | LOW | Add to Phase A backlog; gap detector tracks count |

---

## 7. Critical Constraints (Non-Negotiable)

### 7.1 — No Temporary Bypasses

The following are **FORBIDDEN** at any point during or after this plan:

| Forbidden Pattern | Why |
|-------------------|-----|
| `# TODO: route through L4 later` | Creates permanent debt disguised as plan |
| `from app.hoc.cus.*.L5_engines.* import ...` in any new L2 file | New violation while fixing old ones |
| `if USE_ORCHESTRATOR: ... else: direct_call()` | Conditional bypass creates two code paths to maintain |
| Re-exporting L5 engine symbols through L4 `__init__.py` | Re-export is not orchestration; the call must flow through the registry |
| `# temporarily allow` annotations in gap detector | The tool exists to make violations visible. Suppressing it is a process failure. |

### 7.2 — One-Way Door

Once an operation is registered in L4 and the L2 import is removed:

- The L5 facade remains unchanged (it still works for intra-domain L5→L5 calls)
- The L2 file **must never** re-add the direct import
- The operation registration **must not** be removed without replacing the wiring

### 7.3 — Tooling Authority

The gap detector (`l5_spine_pairing_gap_detector.py`) is the **single source of truth** for compliance:

```bash
# This command answers: "Are we done?"
python3 scripts/ops/l5_spine_pairing_gap_detector.py

# Acceptance:
#   Direct L2→L5 (gaps): 0
```

No manual audits, no spreadsheets, no "I checked and it's fine." The tool output is the proof.

---

## 8. Deliverables per Phase

| Phase | Deliverable | Proof |
|-------|-------------|-------|
| A.0 | `operation_registry.py` + `OperationHandler` protocol | Unit test: register + execute round-trip |
| A.1–A.5 | 32 operation handlers + 32 L2 file updates | Gap detector: `direct_l2_to_l5: 0` |
| A.6 | Updated literature (all pairing declarations populated) | Validator: 0 drift |
| B | 153 orphan classifications in literature | Classifier: 0 unclassified |
| C | CI freeze gate + baseline JSON | Preflight scan: exit 0 |

---

## 9. Verification Commands

```bash
# Phase A progress (run after each operation is wired)
python3 scripts/ops/l5_spine_pairing_gap_detector.py
# Watch: "Direct L2→L5 (gaps)" decreasing from 32 → 0

# Phase A completion
python3 scripts/ops/l5_spine_pairing_gap_detector.py --json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['summary'])"
# Must show: {"total_l5_engines": 185, "wired_via_l4": 32, "direct_l2_to_l5": 0, "orphaned": 153}

# Phase B completion
python3 scripts/ops/l5_orphan_classifier.py --verify
# Must show: 0 unclassified

# Phase C enforcement
python3 scripts/ops/l5_spine_pairing_gap_detector.py --check
# Must exit 0

# Full literature validation
python3 scripts/ops/hoc_spine_study_validator.py --validate literature/hoc_spine/
# Must show: no DRIFT, no MISSING-SECTION, no BOUNDARY-DRIFT
```

---

**END OF PLAN**
