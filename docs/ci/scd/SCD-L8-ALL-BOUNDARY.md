# Signal Circuit Discovery: L8↔All Boundary

**Status:** PHASE 1 DISCOVERY COMPLETE
**Date:** 2025-12-31
**Boundary:** L8 (Catalyst / Meta / CI) ↔ All Layers (L1-L7)
**Reference:** PRODUCT_DEVELOPMENT_CONTRACT_V3.md, CI_SIGNAL_REGISTRY.md

---

## 1. Boundary Lock

```yaml
boundary_pair: L8↔All
from_layer: L8 — Catalyst / Meta (CI)
to_layer: L1-L7 (All codebase layers)
direction: bidirectional
crossing_type: validation + enforcement + feedback
```

**Unique Characteristics:**
- L8 is the meta-layer that validates all other layers
- L8 consumes code artifacts from L1-L7
- L8 emits status signals that gate deployments
- L8 should satisfy: Same commit = Same CI result

---

## 2. Declared Intent

| Field | Value |
|-------|-------|
| Contract Document | `docs/contracts/PRODUCT_DEVELOPMENT_CONTRACT_V3.md` (Phase 1) |
| Contract Version | v3 (ACTIVE) |
| Intent Statement | "CI is the spine... CI must be authoritative before product work proceeds" |
| Enforcement Level | BLOCKING for critical signals, ADVISORY for others |

**Phase 1 Goal:**
> Re-anchor truth, prevent regression, ensure CI is a reliable governor, not noise.

---

## 3. Expected Signals

### 3.1 L8 → All (CI Emits to Codebase)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-L8A-001 | CI Pass/Fail | GitHub Actions | GitHub PR merge gate | GitHub Status | Merge allowed/blocked |
| EXP-L8A-002 | Test Results | pytest/playwright | Developers | Logs/Artifacts | Debug information |
| EXP-L8A-003 | Coverage Report | pytest-cov | Developers | Artifacts | Quality metric |
| EXP-L8A-004 | BLCA Violations | layer_validator.py | Governance | CLI output | Architecture enforcement |
| EXP-L8A-005 | Determinism Result | determinism-check | Developers | Artifacts | Hash parity verification |

### 3.2 All → L8 (Codebase Emits to CI)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-AL8-001 | Code Changes | git push | CI workflows | GitHub Events | Trigger CI run |
| EXP-AL8-002 | Test Files | tests/**/*.py | CI runners | File system | Tests executed |
| EXP-AL8-003 | Config Files | *.yml, *.yaml | CI runners | File system | CI configured |
| EXP-AL8-004 | Layer Headers | # Layer: L{X} | BLCA | File system | Layer validation |
| EXP-AL8-005 | Golden Files | golden/*.json | m4-ci | File system | Replay verification |

---

## 4. Reality Inspection

### 4.1 CI Workflow Inventory (24 Total)

| Category | Workflows | Enforcement |
|----------|-----------|-------------|
| **Structural/Governance** | ci.yml, ci-preflight.yml, truth-preflight.yml, import-hygiene.yml, integration-integrity.yml | BLOCKING |
| **Phase Guards** | c1-telemetry-guard.yml, c2-regression.yml | BLOCKING |
| **Determinism/SDK** | determinism-check.yml, e2e-parity-check.yml, publish-python-sdk.yml, publish-js-sdk.yml | BLOCKING for release |
| **Type Safety** | mypy-autofix.yml | BLOCKING (Zone A only) |
| **Workflow Engine** | m4-ci.yml, m4-signoff.yaml | BLOCKING |
| **Load/Performance** | k6-load-test.yml, nightly.yml | ADVISORY |
| **Smoke/Monitoring** | m7-nightly-smoke.yml, prometheus-rules.yml, failure-aggregation.yml | ADVISORY/NOTIFYING |
| **Deploy/Promotion** | deploy.yml, m9-production-promotion.yml | MANUAL |
| **Build** | build-push-webhook.yml | BLOCKING for images |

### 4.2 Signal-to-Layer Mapping

| Signal | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|--------|----|----|----|----|----|----|-----|
| SIG-001 (ci) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SIG-003 (truth-preflight) | - | ✓ | - | ✓ | ✓ | ✓ | - |
| SIG-005 (integration) | ✓ | ✓ | ✓ | - | - | ✓ | - |
| SIG-006 (c1-guard) | - | - | - | ✓ | - | ✓ | - |
| SIG-007 (c2-guard) | - | - | - | ✓ | - | ✓ | - |
| SIG-008 (determinism) | - | - | - | ✓ | ✓ | - | - |
| SIG-013 (m4-ci) | - | - | - | ✓ | ✓ | - | - |

### 4.3 CI Determinism Audit

| Check | Status | Evidence |
|-------|--------|----------|
| Same commit = same result? | MOSTLY | Some environment-dependent tests exist |
| Flaky tests present? | YES | m7-nightly-smoke.yml is environment-dependent |
| Order-independent? | MOSTLY | Some tests depend on DB state |
| Environment parity? | PARTIAL | CI uses ephemeral Postgres, local uses persistent |

### 4.4 Ownership Audit

| Classification | Count | Status |
|----------------|-------|--------|
| CRITICAL (owned by Governance) | 3 | SIG-003, SIG-006, SIG-007 |
| OWNED (SDK Team) | 2 | SIG-010, SIG-011 |
| NEEDS_OWNER | 16 | **P0 GOVERNANCE DEFECT** |
| CRITICAL_UNOWNED | 1 | SIG-001 (main CI) |

---

## 5. End-to-End Circuit Walk

### Circuit 1: Truth Preflight Gate

```
SIGNAL: PR opened → Truth preflight pass/fail → Merge allowed/blocked

INTENT:
  → Declared at: PIN-193, PIN-194
  → Statement: "No Truth Preflight → No Scenario → No Acceptance → No Merge"

EMISSION:
  → Emitter: Developer (git push)
  → Mechanism: GitHub PR event triggers workflow
  → Explicit: YES

TRANSPORT:
  → Type: GitHub Actions orchestration
  → Observable: YES (workflow logs)
  → Failure Mode: Job marked failed, PR blocked

ADAPTER:
  → Location: .github/workflows/truth-preflight.yml
  → Purpose: Translates PR event to verification steps

CONSUMPTION:
  → Consumer: GitHub merge gate
  → Explicit: YES (required status check)
  → Dependency Declared: YES (branch protection rules)

CONSEQUENCE:
  → What happens on success: PR can merge
  → What happens on failure: PR blocked, developer must fix
  → Observable: YES (GitHub status badge)
```

### Circuit 2: Layer Violation Detection

```
SIGNAL: Code change → BLCA check → Violation reported

INTENT:
  → Declared at: PIN-245 (Integration Integrity)
  → Statement: "BLCA must report 0 violations"

EMISSION:
  → Emitter: Developer (code change)
  → Mechanism: Modified file with layer header
  → Explicit: YES (file headers)

TRANSPORT:
  → Type: Git push → GitHub Actions → BLCA script
  → Observable: YES (CLI output)
  → Failure Mode: Non-zero exit code

ADAPTER:
  → Location: scripts/ops/layer_validator.py
  → Purpose: Scans files for layer header and import violations

CONSUMPTION:
  → Consumer: CI integration-integrity job
  → Explicit: PARTIAL (not all workflows run BLCA)
  → Dependency Declared: YES (SESSION_PLAYBOOK.yaml bootstrap)

CONSEQUENCE:
  → What happens on success: No violations, CI continues
  → What happens on failure: Violations listed, CI may fail
  → Observable: YES (CI logs)
```

---

## 6. Failure Classification

| Gap ID | Gap Description | Classification | Severity |
|--------|-----------------|----------------|----------|
| GAP-L8A-001 | 18/22 signals have no documented owner | HUMAN_ONLY_SIGNAL | P0 |
| GAP-L8A-002 | Main CI (SIG-001, 68KB) is CRITICAL_UNOWNED | MISSING_CONSUMER | P0 |
| GAP-L8A-003 | Some tests are environment-dependent (non-deterministic) | BROKEN_CIRCUIT | P1 |
| GAP-L8A-004 | BLCA not run in all relevant workflows | PARTIAL_CIRCUIT | P2 |
| GAP-L8A-005 | No CI check for layer import direction | MISSING_EMITTER | P1 |
| GAP-L8A-006 | CI outcomes don't auto-update governance artifacts | MISSING_CONSUMER | P2 |
| GAP-L8A-007 | Manual overrides possible without ratification | BYPASSED_BOUNDARY | P1 |

### Classification Evidence

**GAP-L8A-001 (HUMAN_ONLY_SIGNAL):**
From CI_SIGNAL_REGISTRY.md: "18 of 22 signals have no documented owner."
Owner assignment requires human decision - no automated process.

**GAP-L8A-002 (MISSING_CONSUMER):**
SIG-001 (ci.yml) is 68KB, runs all tests, but has no documented owner.
Nobody is accountable when it fails unexpectedly.

**GAP-L8A-003 (BROKEN_CIRCUIT):**
m7-nightly-smoke.yml can fail due to environment issues, not code issues.
Same commit can produce different results.

**GAP-L8A-004 (PARTIAL_CIRCUIT):**
BLCA runs in bootstrap but not in all CI workflows.
Layer violations can slip through some paths.

**GAP-L8A-005 (MISSING_EMITTER):**
No CI check validates that L5 doesn't import L4 directly.
Caught in L4↔L5 SCD but not enforced by L8.

---

## 7. Risk Statement

```
RISK SUMMARY:
  - Circuit Status: PARTIAL
  - Gap Count: 7
  - Critical Gaps: GAP-L8A-001 (unowned signals), GAP-L8A-002 (unowned main CI)
  - Blocking for Phase 2: YES (owner assignment required)
  - Human Action Required: YES (assign owners to 18 signals)

RISK NARRATIVE:
  CI is operational but lacks accountability. 18 of 22 signals have no owner,
  meaning nobody is responsible when CI fails unexpectedly. The main CI workflow
  (SIG-001) is 68KB and critical, but unowned. Phase 1 cannot complete until
  every signal has an assigned owner who will be notified on failure.
```

---

## 8. Registry Entry

```yaml
boundary: L8↔All
circuit_status: PARTIAL
signals_expected: 10 (5 L8→All + 5 All→L8)
signals_found: 10
gaps:
  - id: GAP-L8A-001
    type: HUMAN_ONLY_SIGNAL
    severity: P0
    description: 18/22 signals have no documented owner
  - id: GAP-L8A-002
    type: MISSING_CONSUMER
    severity: P0
    description: Main CI (SIG-001) is CRITICAL_UNOWNED
  - id: GAP-L8A-003
    type: BROKEN_CIRCUIT
    severity: P1
    description: Some tests are environment-dependent (non-deterministic)
  - id: GAP-L8A-004
    type: PARTIAL_CIRCUIT
    severity: P2
    description: BLCA not run in all relevant workflows
  - id: GAP-L8A-005
    type: MISSING_EMITTER
    severity: P1
    description: No CI check for layer import direction
  - id: GAP-L8A-006
    type: MISSING_CONSUMER
    severity: P2
    description: CI outcomes don't auto-update governance artifacts
  - id: GAP-L8A-007
    type: BYPASSED_BOUNDARY
    severity: P1
    description: Manual overrides possible without ratification
enforcement:
  ci_coverage: YES (24 workflows)
  blocking_workflow: truth-preflight.yml, integration-integrity.yml, c1-telemetry-guard.yml, c2-regression.yml
  advisory_workflow: nightly.yml, k6-load-test.yml, m7-nightly-smoke.yml
phase_1_complete: NO
phase_1_blocker: Owner assignment for 18 signals (requires human action)
```

---

## 9. Hard Rules (Verification)

| Rule | Check | Status |
|------|-------|--------|
| Did I observe, not fix? | Documented gaps, did not modify workflows | YES |
| Did I document what IS, not what SHOULD BE? | Reality section reflects current CI state | YES |
| Did I trace at least one full circuit? | 2 circuits traced (truth preflight, layer violation) | YES |
| Did I classify all gaps found? | 7 gaps classified with codes | YES |
| Did I note human-only signals? | Owner assignment is human-only | YES |
| Did I check both directions if bidirectional? | L8→All and All→L8 both documented | YES |

---

## 10. Completion Test

| Question | Can Answer? |
|----------|-------------|
| What signals cross this boundary? | YES (22 CI signals + codebase inputs) |
| Where are they emitted? | YES (24 workflow files documented) |
| Where are they consumed? | YES (GitHub merge gate, developers) |
| What happens if any signal is missing? | YES (merge blocked or advisory only) |
| Which gaps block Phase 2? | YES (GAP-L8A-001, GAP-L8A-002 block) |

**Checklist Status: COMPLETE**

---

## CI GREEN Guarantee (What We Can Answer)

> If CI is green, the following is guaranteed:
>
> 1. **Truth preflight passed** (PIN-193, PIN-194)
> 2. **C1 telemetry invariants hold** (if telemetry changed)
> 3. **C2 prediction invariants hold** (if predictions changed)
> 4. **Layer integration contracts satisfied** (PIN-245)
> 5. **Import hygiene clean** (no side effects)
> 6. **Type safety Zone A passed** (critical paths)
> 7. **Determinism verified** (if SDK changed)
>
> **NOT guaranteed:**
> - Performance SLOs met (k6 is advisory)
> - All mypy zones clean (only Zone A enforced)
> - Production readiness (deploy is separate)

---

## Phase 1 Blocking Items

| Item | Status | Owner Required |
|------|--------|----------------|
| Assign owners to 18 unowned signals | PENDING | Human |
| Assign owner to SIG-001 (main CI) | PENDING | Human |
| Document what each CI check guarantees | DONE | (in this document) |
| Verify same-commit determinism | PARTIAL | Needs testing |

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| CI_SIGNAL_REGISTRY.md | Complete signal inventory |
| PRODUCT_DEVELOPMENT_CONTRACT_V3.md | Phase 1 governance |
| PIN-245 | Integration integrity system |
| PIN-193, PIN-194 | Truth preflight gates |
| PIN-210 | C1 telemetry guard |
| PIN-222 | C2 prediction guard |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial SCD for L8↔All boundary |
