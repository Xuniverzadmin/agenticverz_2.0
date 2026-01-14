# AURORA L2 Compiler — UI-First Specification v1

**Status:** ACTIVE (Constitutional)
**Created:** 2026-01-14
**Authority:** docs/contracts/UI_AS_CONSTRAINT_V1.md
**Reference:** PIN-421 (to be created)

---

## 1. Prime Directive

> **The compiler reads `ui_plan.yaml` FIRST. All panels declared in the UI plan MUST appear in projection output, regardless of backend readiness.**

---

## 2. Input Authority Stack

The compiler MUST read inputs in this exact order:

| Priority | Input | Purpose |
|----------|-------|---------|
| 1 | `design/l2_1/ui_plan.yaml` | Establishes panel universe (what MUST exist) |
| 2 | `design/l2_1/intents/*.yaml` | Panel intent specifications |
| 3 | `backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml` | Capability declarations and status |
| 4 | SDSR scenario results | Capability observation proofs |
| 5 | Backend endpoint manifests | Implementation details |

If inputs conflict, **higher priority wins**.

---

## 3. Panel State Computation

The compiler MUST compute panel state mechanically:

```
EMPTY     := panel_id in ui_plan.yaml AND intent YAML missing
UNBOUND   := intent YAML exists AND (no capability referenced OR capability not in registry)
DRAFT     := capability exists AND capability.status in (DECLARED, DISCOVERED)
BOUND     := capability exists AND capability.status in (OBSERVED, TRUSTED)
DEFERRED  := panel has deferred_reason in ui_plan.yaml
```

### 3.1 State Computation Pseudocode

```python
def compute_panel_state(panel: PanelSpec, registry: CapabilityRegistry) -> PanelState:
    # Check for explicit deferral first
    if panel.deferred_reason:
        return PanelState.DEFERRED

    # Check if intent exists
    intent_path = Path(panel.intent_spec) if panel.intent_spec else None
    if not intent_path or not intent_path.exists():
        return PanelState.EMPTY

    # Check capability binding
    if not panel.expected_capability:
        return PanelState.UNBOUND

    capability = registry.get(panel.expected_capability)
    if not capability:
        return PanelState.UNBOUND

    # Check capability status
    if capability.status in ('OBSERVED', 'TRUSTED'):
        return PanelState.BOUND
    elif capability.status in ('DECLARED', 'DISCOVERED'):
        return PanelState.DRAFT
    else:
        return PanelState.UNBOUND
```

---

## 4. Required Output Structure

### 4.1 Projection Lock Schema

The compiler MUST emit `ui_projection_lock.json` with this structure:

```json
{
  "version": "2.0.0",
  "generated_at": "2026-01-14T14:00:00Z",
  "authority": "design/l2_1/ui_plan.yaml",
  "domains": [
    {
      "id": "Overview",
      "question": "Is the system okay right now?",
      "subdomains": [
        {
          "id": "SYSTEM_HEALTH",
          "topics": [
            {
              "id": "CURRENT_STATUS",
              "panels": [
                {
                  "panel_id": "OVW-SH-CS-O1",
                  "order": "O1",
                  "panel_class": "interpretation",
                  "state": "UNBOUND",
                  "disabled_reason": null,
                  "capability": null,
                  "data_shape": null,
                  "actions": []
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "summary": {
    "total_panels": 86,
    "by_state": {
      "EMPTY": 31,
      "UNBOUND": 54,
      "DRAFT": 0,
      "BOUND": 1,
      "DEFERRED": 0
    }
  }
}
```

### 4.2 Required Panel Fields

Every panel in projection output MUST include:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `panel_id` | string | YES | Unique identifier (immutable) |
| `order` | string | YES | Display order (O1, O2, ...) |
| `panel_class` | enum | YES | `execution` or `interpretation` |
| `state` | enum | YES | EMPTY, UNBOUND, DRAFT, BOUND, DEFERRED |
| `disabled_reason` | string | nullable | Why panel is disabled (for DEFERRED) |
| `capability` | string | nullable | Bound capability name |
| `data_shape` | object | nullable | Data schema (only for BOUND panels) |
| `actions` | array | YES | Available actions (empty for non-BOUND) |

---

## 5. Emission Rules

### 5.1 EMPTY Panels (Intent Missing)

```json
{
  "panel_id": "ACC-PR-AI-O1",
  "state": "EMPTY",
  "disabled_reason": "Intent specification not yet created",
  "capability": null,
  "data_shape": null,
  "actions": []
}
```

### 5.2 UNBOUND Panels (Capability Missing)

```json
{
  "panel_id": "ACT-EX-AR-O1",
  "state": "UNBOUND",
  "disabled_reason": "Awaiting capability declaration",
  "capability": null,
  "data_shape": null,
  "actions": []
}
```

### 5.3 DRAFT Panels (Not Observed)

```json
{
  "panel_id": "POL-AP-AR-O1",
  "state": "DRAFT",
  "disabled_reason": "Capability declared but not observed via SDSR",
  "capability": "policy.approval_rules.list",
  "data_shape": null,
  "actions": []
}
```

### 5.4 BOUND Panels (Fully Ready)

```json
{
  "panel_id": "INC-AI-SUM-O1",
  "state": "BOUND",
  "disabled_reason": null,
  "capability": "summary.incidents",
  "data_shape": {
    "type": "object",
    "properties": {
      "total_active": { "type": "integer" },
      "severity_breakdown": { "type": "object" }
    }
  },
  "actions": [
    {
      "action_id": "refresh",
      "label": "Refresh",
      "method": "POST",
      "endpoint": "/api/v1/incidents/summary/refresh"
    }
  ]
}
```

### 5.5 DEFERRED Panels (Governance Decision)

```json
{
  "panel_id": "LOG-AL-SA-O4",
  "state": "DEFERRED",
  "disabled_reason": "Deferred per PIN-400: Privacy review required",
  "capability": null,
  "data_shape": null,
  "actions": []
}
```

---

## 6. Forbidden Behaviors

The compiler MUST NOT:

| Forbidden | Why |
|-----------|-----|
| Omit panels declared in ui_plan.yaml | UI plan is authoritative |
| Emit panels not in ui_plan.yaml | No unauthorized additions |
| Change panel_id values | Immutable by doctrine |
| Reparent panels (change domain/subdomain/topic) | Requires explicit governance |
| Assign BOUND state without OBSERVED/TRUSTED capability | Breaks trust chain |
| Skip state computation | All panels need computed state |

---

## 7. Compiler Pipeline Integration

### 7.1 Pre-Compilation Validation

Before compilation:

```bash
python scripts/tools/validate_ui_plan.py
# MUST pass before compiler runs
```

### 7.2 Compilation Command

```bash
python backend/aurora_l2/compiler/compile.py \
    --ui-plan design/l2_1/ui_plan.yaml \
    --intents design/l2_1/intents/ \
    --capabilities backend/AURORA_L2_CAPABILITY_REGISTRY/ \
    --output design/l2_1/ui_contract/ui_projection_lock.json
```

### 7.3 Post-Compilation Guard

After compilation:

```bash
python backend/aurora_l2/tools/projection_diff_guard.py
# Validates output against ui_plan.yaml
```

---

## 8. Error Handling

### 8.1 Missing UI Plan

```
FATAL: ui_plan.yaml not found at design/l2_1/ui_plan.yaml
ACTION: Create UI plan or check path
EXIT_CODE: 1
```

### 8.2 Malformed UI Plan

```
FATAL: ui_plan.yaml parse error at line 42
DETAIL: Expected 'panel_id' key in panel definition
ACTION: Fix YAML syntax
EXIT_CODE: 2
```

### 8.3 State Computation Failure

```
WARNING: Could not compute state for panel ACC-PR-AI-O1
REASON: Intent path references non-existent file
DEFAULT: Setting state to EMPTY
```

---

## 9. Changelog

| Date | Change |
|------|--------|
| 2026-01-14 | Initial UI-first specification created |

---

## 10. Related Documents

| Document | Location | Role |
|----------|----------|------|
| UI-as-Constraint Doctrine | `docs/contracts/UI_AS_CONSTRAINT_V1.md` | Authority |
| UI Plan | `design/l2_1/ui_plan.yaml` | Input constraint |
| PDG Invariants | `docs/contracts/PDG_STATE_INVARIANTS_V1.yaml` | Output validation |
| Empty-State Contract | `docs/contracts/EMPTY_STATE_UI_CONTRACT_V1.md` | Frontend rules |
