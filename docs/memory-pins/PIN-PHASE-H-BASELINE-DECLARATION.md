# PIN: Phase H Baseline Declaration

**PIN ID:** PIN-PHASE-H-BASELINE
**Status:** BASELINE DECLARED
**Date:** 2026-01-05
**Phase:** H (Post-Governance Build)
**Authority:** Baseline Declaration (NOT Freeze)

---

## BASELINE DECLARATION

> **"The backend architecture and governance model are stable.
> Product development continues under enforced invariants."**

This is a **baseline**, not a freeze. Work continues under governance.

---

## 1. Architectural State (STABLE, NON-NEGOTIABLE)

These layers are **done and must not be reworked**.

### Authentication
- Clerk = sole human auth provider
- JWT = identity carrier only
- Session revocation enforced
- API keys = machine-only
- Gateway is the *only* auth entry point

**State:** `CLOSED`

### Authorization
- RBAC v2 is sole authority engine
- No inline role checks
- Default deny everywhere
- Authority surfaces declared and enforced

**State:** `CLOSED`

### Governance
- Capability registry enforced by CI
- Plane purity enforced
- Permission taxonomy version-locked
- Worker auth restricted to API keys
- Drift detection active

**State:** `CLOSED & NON-REGRESSABLE`

---

## 2. Capability Registry Snapshot

```
Total capabilities: 17

CLOSED:      11
READ_ONLY:   2
PARTIAL:     3
PLANNED:     1
```

### CLOSED (structurally complete)
- authentication
- authorization
- replay (authority complete)
- prediction_plane (authority complete)

### READ_ONLY (intentional)
- prediction_plane
- policy_proposals

### PARTIAL (safe, known work)
- replay → client UX iteration possible
- cost_simulation → scenario depth expansion
- founder_console → lifecycle not finalized

### PLANNED
- cross_project (intentionally absent)

---

## 3. Phase H Deliverables (LIVE)

### H1: Replay
- Backend slice API: `backend/app/api/replay.py`
- Timeline-based UX: `ReplaySliceViewer.tsx`
- Founder-visible, read-only
- Self-explanatory (no human mediation required)

**Replay is now a trust surface.**

### H2: Cost Simulation
- Scenario API: `backend/app/api/scenarios.py`
- Advisory-only, pure computation
- No execution hooks, no config writes
- Founder-visible

**Cost intelligence exists without liability.**

### H3: Founder Console
- Explorer API: `backend/app/api/founder_explorer.py`
- Cross-tenant READ-ONLY visibility
- Diagnostics + exploration
- No mutation paths

**Founder insight without corruption.**

### H4: Stabilization Checkpoint
- Captured in `PIN-PHASE-H-STABILIZATION-CHECKPOINT.md`

---

## 4. What Is Explicitly NOT Frozen

Baseline ≠ Freeze. The following are **allowed and expected**:

### Replay
- UX improvements
- Visualization enhancements
- Sharing / annotation (read-only)
- Tenant exposure (future, gated)

### Cost Simulation
- More scenarios
- Better models
- Confidence calibration
- Cost driver explainability

### Founder Console
- Better diagnostics
- Pattern detection
- Insight tooling

**As long as:**
- No execution
- No silent mutation
- No authority creep
- Registry + CI invariants hold

---

## 5. What Remains Forbidden

These remain **out of bounds** unless explicitly elevated:

- Auto-execution based on prediction
- "Apply" buttons for simulation
- Founder silent writes
- Mixed auth planes
- Capability state changes without PIN

---

## 6. Current Work Posture

> **Baseline Product Expansion under Governance**

This means:
- Architecture is trusted
- Features may grow
- Authority may not leak
- Governance must stay loud

This is **not**:
- Cleanup mode
- Refactor mode
- "We'll fix governance later" mode

---

## 7. Open Tasks Ahead (Not Decisions Yet)

Known next work items (no ordering assumed):

- Replay → tenant-admin read-only exposure
- Replay → annotations / bookmarks
- Cost simulation → multi-scenario comparisons
- Cost simulation → historical vs projected cost
- Founder console → insight summarization
- Prediction plane → explanation depth (still READ_ONLY)

---

## 8. Files Delivered in Phase H

### Backend
| File | Purpose |
|------|---------|
| `backend/app/api/replay.py` | H1 Replay slice API |
| `backend/app/api/scenarios.py` | H2 Cost simulation API |
| `backend/app/api/founder_explorer.py` | H3 Cross-tenant explorer |

### Frontend
| File | Purpose |
|------|---------|
| `src/api/replay.ts` | Replay API client |
| `src/api/scenarios.ts` | Scenarios API client |
| `src/api/explorer.ts` | Explorer API client |
| `src/pages/founder/ReplayIndexPage.tsx` | Incident list |
| `src/pages/founder/ReplaySliceViewer.tsx` | Timeline viewer |
| `src/pages/founder/ScenarioBuilderPage.tsx` | Scenario builder |
| `src/pages/founder/FounderExplorerPage.tsx` | Explorer dashboard |

### Routes Added
- `/founder/replay` - Incident index
- `/founder/replay/:incidentId` - Slice viewer
- `/founder/scenarios` - Scenario builder
- `/founder/explorer` - Cross-tenant explorer

---

## 9. Invariants Established

### I-H1: Replay is READ-ONLY
Replay endpoints MUST NOT modify incident data, emit triggering events, or influence control plane.

### I-H2: Cost Simulation is Advisory-Only
Scenario simulation MUST NOT modify budgets, create billing records, or affect policy enforcement.

### I-H3: Explorer is Cross-Tenant READ-ONLY
Explorer endpoints MUST NOT modify tenant data or enable cross-tenant mutations.

### I-H4: FOPS Authentication Required
All Phase H founder endpoints require valid FOPS token.

---

## 10. Baseline Attestation

```
PHASE H BASELINE ATTESTATION

Date: 2026-01-05
Phase: H (Post-Governance Build)
Tasks Completed: H1, H2, H3, H4

Architecture: STABLE
Governance: ENFORCED
Work Posture: PRODUCT EXPANSION UNDER GOVERNANCE

Constraint Violations: NONE
Build Status: PASS

This baseline is the reference point for continued development.
Features may grow. Authority may not leak.
```

---

## Changelog

| Date | Action | Author |
|------|--------|--------|
| 2026-01-05 | Baseline declaration | Claude Opus 4.5 |
