# UI-as-Constraint Doctrine v1

**Status:** ACTIVE (Constitutional)
**Created:** 2026-01-14
**Authority:** Human System Owner
**Reference:** PIN-420 (to be created)

---

## Prime Directive (Non-Negotiable)

> **The UI plan defines the surface. Backend and SDSR exist only to fill declared gaps. Automation failures are system defects, never reasons to bypass.**

---

## 1. Core Doctrine

### 1.1 UI Plan as Constraint

The **UI plan (`design/l2_1/ui_plan.yaml`)** is the **active constraint**, not frozen forever, but **stable until gaps are filled**.

We **do not reshape UI** to accommodate backend immaturity.

We **only revisit UI structure after all declared panels reach a terminal state** (BOUND or explicitly DEFERRED by design decision).

This is *not* a freeze. It is a **working constraint**.

> Think of it as: *"We are paying down this surface area before creating new surface area."*

### 1.2 What the UI Plan Represents

It declares **what must eventually be visible to a human**, independent of backend readiness.

Structure:

```
Domain
 └─ Subdomain
     └─ Topic (tab)
         └─ Panel
```

Each **panel entry** declares:

* `panel_id` - Unique identifier
* `domain / subdomain / topic` - Navigation hierarchy
* `panel_class` - execution | interpretation
* `intent` - Human question it answers
* `expected_capability` - Nullable initially
* `initial_state` - Computed by system

No data shapes. No logic. No backend hints beyond capability names.

---

## 2. Panel State Model (System-Wide, Enforced)

Every panel declared in the UI plan must exist in projection with one of these states:

| State | Meaning | Who Fixes It | Rendering |
|-------|---------|--------------|-----------|
| **EMPTY** | UI planned, nothing exists yet | Design / planning | Empty state UX |
| **UNBOUND** | Intent exists, capability missing | Backend team | Empty state UX |
| **DRAFT** | Capability declared, SDSR not observed | SDSR team | Disabled controls |
| **BOUND** | Capability observed (or trusted) | Done | Full functionality |
| **DEFERRED** | Explicit governance decision | You (documented) | Hidden or disabled |

### 2.1 Rendering Rule

**Critical:** EMPTY and UNBOUND panels **MUST render** (with empty state UX).
They are **signals**, not failures.

This alone prevents UI drift.

### 2.2 State Computation

States are **computed by the system**, not hand-coded:

```
EMPTY     := panel_id in ui_plan.yaml AND intent YAML missing
UNBOUND   := intent YAML exists AND (no capability referenced OR capability not in registry)
DRAFT     := capability exists AND capability.status = DECLARED
BOUND     := capability exists AND capability.status in (OBSERVED, TRUSTED)
DEFERRED  := panel has deferred_reason in ui_plan.yaml
```

---

## 3. Authority Reversal (Formal)

### 3.1 Old (Caused Friction)

```
Backend → SDSR → Capability → Projection → UI
```

### 3.2 New (What We Adopt Now)

```
UI Plan → Projection Skeleton → SDSR → Backend → Capability → Fill UI
```

Key shift:

* **Projection exists before truth**
* SDSR's job is to *fill declared holes*, not to decide whether holes exist

### 3.3 Authority Stack (Non-Negotiable Order)

This order **must not be violated**:

| Priority | Authority | Role |
|----------|-----------|------|
| 1 | `ui_plan.yaml` | Human constraint |
| 2 | Intent registry | Declarative bindings |
| 3 | Capability registry | Observability state |
| 4 | SDSR scenarios | System revelation |
| 5 | Backend endpoints | Implementation |
| 6 | Compiler / projection | Mirror only |
| 7 | Frontend renderer | Dumb consumer |

If anything lower contradicts something higher → **lower is wrong**.

---

## 4. Automation Doctrine (Claude Must Obey)

### 4.1 Forbidden Actions

Claude is **explicitly forbidden** from:

| Action | Why Forbidden |
|--------|---------------|
| Manually copying projection files | Bypasses pipeline |
| Skipping pipeline stages | Creates invisible drift |
| Writing ad-hoc fix scripts outside registered tools | Untracked mutations |
| Running steps out of declared order | Violates authority stack |
| Editing UI structure to satisfy backend | Inverts authority |
| Patching state to "get past" guards | Hides real problems |

### 4.2 Required Actions

Claude is **only allowed** to:

| Action | Reason |
|--------|--------|
| Use declared automation entrypoints | Tracked, reproducible |
| Extend automation when blocked | Fixes root cause |
| Treat automation gaps as P1 deliverables | System debt, not heroics |
| Report pipeline failures as system defects | Not reasons to bypass |

### 4.3 Enforcement

If automation blocks progress → **automation is the task**.

Claude must never "get things working" by bypass. Claude must fix the automation.

---

## 5. Declared Automation Entrypoints

### 5.1 Required Primitives

| Primitive | Script | Purpose |
|-----------|--------|---------|
| UI Projection Skeleton Generator | `scripts/tools/generate_projection_skeleton.py` | Generate projection from UI plan (all panels, even EMPTY) |
| SDSR Scenario Auto-Discovery | `scripts/tools/discover_missing_sdsr.py` | Find panels without SDSR coverage |
| Capability-Panel Consistency Guard | `scripts/tools/check_capability_panel_consistency.py` | CI: every panel → capability link valid |
| Projection Diff Guard (UI-Aware) | `backend/aurora_l2/tools/projection_diff_guard.py` | Block removal/reparenting of planned panels |

### 5.2 Pipeline Execution Order

```bash
# Step 1: Validate UI plan
python scripts/tools/validate_ui_plan.py

# Step 2: Generate projection skeleton (includes EMPTY panels)
python scripts/tools/generate_projection_skeleton.py

# Step 3: Run AURORA L2 compiler
./scripts/tools/run_aurora_l2_pipeline.sh

# Step 4: Run projection diff guard
python backend/aurora_l2/tools/projection_diff_guard.py

# Step 5: Copy projection to frontend
cp design/l2_1/ui_contract/ui_projection_lock.json \
   website/app-shell/public/projection/
```

Claude must use this order. Skipping steps is a violation.

---

## 6. Mutation Rules

### 6.1 When UI Plan May Change

The UI plan is **not frozen**, but changes are gated:

| Allowed | Condition |
|---------|-----------|
| Adding new panels | Always allowed (additive) |
| Promoting DEFERRED → EMPTY | Governance decision |
| Reparenting panels | Only after all panels in source topic are BOUND or DEFERRED |
| Removing panels | Never (use DEFERRED state instead) |
| Renaming panels | Never (panel_id is immutable) |

### 6.2 When UI Plan Must NOT Change

| Forbidden | Reason |
|-----------|--------|
| During backend development | UI leads, backend follows |
| To "unblock" a failing pipeline | Fix pipeline, not plan |
| To accommodate missing capability | Capability must fill gap |
| Without closing existing gaps | Pay down debt first |

---

## 7. Gap Visibility

### 7.1 Gap Detection

The system must expose gaps explicitly:

```yaml
# Gap report format
gaps:
  EMPTY:
    - panel_id: ACT-EX-SUM-O1
      reason: Intent YAML not created
      owner: design

  UNBOUND:
    - panel_id: INC-AI-SUM-O1
      reason: Capability not declared
      owner: backend

  DRAFT:
    - panel_id: POL-AP-AR-O1
      reason: SDSR scenario not executed
      owner: sdsr
```

### 7.2 Gap Resolution Order

| Priority | State | Action |
|----------|-------|--------|
| P0 | DRAFT | Run SDSR to observe |
| P1 | UNBOUND | Backend declares capability |
| P2 | EMPTY | Design creates intent YAML |
| P3 | DEFERRED | No action (intentional) |

---

## 8. Integration with Existing Systems

### 8.1 Compiler Changes Required

The AURORA L2 compiler must:

1. Read `ui_plan.yaml` **first** (establishes panel universe)
2. Emit panels even when intent YAML is missing (state: EMPTY)
3. Compute panel state from intent + capability registry
4. Include DEFERRED panels with `disabled_reason`

### 8.2 PDG Changes Required

Projection Diff Guard must:

1. Load `ui_plan.yaml` as reference
2. Allow addition of planned panels
3. Block removal of planned panels (must use DEFERRED)
4. Block reparenting (domain/subdomain/topic changes)

### 8.3 Frontend Changes Required

The frontend must:

1. Render EMPTY panels with placeholder UX
2. Render UNBOUND panels with "coming soon" UX
3. Render DRAFT panels with disabled controls
4. Respect `disabled_reason` from projection

---

## 9. Claude Session Rules

### 9.1 At Session Start

Claude must:

1. Read `ui_plan.yaml`
2. Read `UI_AS_CONSTRAINT_V1.md` (this document)
3. Acknowledge authority stack
4. Never propose UI changes to fix backend gaps

### 9.2 During Session

Claude must:

1. Use only declared automation entrypoints
2. Report pipeline failures as system defects
3. Propose automation fixes, not bypasses
4. Never manually copy files between directories

### 9.3 Hard Stop Conditions

Claude must STOP and report when:

1. Pipeline cannot run due to automation gap
2. UI plan needs change (human decision required)
3. Capability-panel mismatch detected
4. SDSR scenario missing for DRAFT panel

---

## 10. Changelog

| Date | Change |
|------|--------|
| 2026-01-14 | Initial doctrine created |

---

## 11. Related Documents

| Document | Location | Role |
|----------|----------|------|
| UI Plan | `design/l2_1/ui_plan.yaml` | Canonical surface constraint |
| Intent Registry | `design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml` | Panel-intent bindings |
| Capability Registry | `backend/AURORA_L2_CAPABILITY_REGISTRY/` | Backend readiness |
| Projection Lock | `design/l2_1/ui_contract/ui_projection_lock.json` | Compiler output |
| HIL Contract | `design/l2_1/HIL_V1_CONTRACT.md` | Interpretation panels |

---

## 12. Invariant (Constitutional)

> **The UI plan defines what must exist.**
> **Backend and SDSR exist to fill gaps.**
> **Automation failures are system defects, never reasons to bypass.**
> **EMPTY and UNBOUND are signals, not failures.**
