# Empty-State UI Contract v1

**Status:** ACTIVE (Constitutional)
**Created:** 2026-01-14
**Authority:** docs/contracts/UI_AS_CONSTRAINT_V1.md
**Reference:** PIN-423 (to be created)

---

## 1. Prime Directive

> **EMPTY and UNBOUND panels MUST render. They are signals, not failures.**

The frontend MUST display all panels declared in the projection, regardless of their state. Hidden gaps lead to drift. Visible gaps drive progress.

---

## 2. Rendering Rules by State

### 2.1 State Summary Table

| State | Visible | Interactive | Content | Purpose |
|-------|---------|-------------|---------|---------|
| EMPTY | YES | NO | Placeholder | Shows planned UI surface |
| UNBOUND | YES | NO | "Coming Soon" | Shows intent exists, capability pending |
| DRAFT | YES | PARTIAL | Disabled Controls | Shows capability exists, not observed |
| BOUND | YES | YES | Full Functionality | Production-ready panel |
| DEFERRED | CONFIGURABLE | NO | Explanation | Shows governance decision |

---

## 3. EMPTY State Rendering

### 3.1 Visual Appearance

```
┌─────────────────────────────────────────────────┐
│  [Panel Title from Intent]                      │
├─────────────────────────────────────────────────┤
│                                                 │
│     ┌──────────────────────────────────┐        │
│     │                                  │        │
│     │    📋 Panel Planned             │        │
│     │                                  │        │
│     │    Intent specification          │        │
│     │    not yet created.              │        │
│     │                                  │        │
│     │    Panel ID: ACC-PR-AI-O1        │        │
│     │                                  │        │
│     └──────────────────────────────────┘        │
│                                                 │
│  [No actions available]                         │
└─────────────────────────────────────────────────┘
```

### 3.2 CSS Requirements

```css
.panel--empty {
  opacity: 0.6;
  background-color: var(--surface-muted);
  border: 2px dashed var(--border-subtle);
}

.panel--empty .panel-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.panel--empty .panel-actions {
  display: none;
}
```

### 3.3 Required Data Attributes

```html
<div
  class="panel panel--empty"
  data-panel-id="ACC-PR-AI-O1"
  data-panel-state="EMPTY"
  data-panel-class="execution"
  aria-disabled="true"
>
  ...
</div>
```

---

## 4. UNBOUND State Rendering

### 4.1 Visual Appearance

```
┌─────────────────────────────────────────────────┐
│  Account Information                            │
├─────────────────────────────────────────────────┤
│                                                 │
│     ┌──────────────────────────────────┐        │
│     │                                  │        │
│     │    🔜 Coming Soon                │        │
│     │                                  │        │
│     │    This panel is defined but     │        │
│     │    awaiting backend capability.  │        │
│     │                                  │        │
│     │    Intent: View account details  │        │
│     │                                  │        │
│     └──────────────────────────────────┘        │
│                                                 │
│  [No actions available]                         │
└─────────────────────────────────────────────────┘
```

### 4.2 CSS Requirements

```css
.panel--unbound {
  opacity: 0.7;
  background-color: var(--surface-pending);
  border: 2px dashed var(--border-info);
}

.panel--unbound .panel-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.panel--unbound .panel-actions {
  display: none;
}
```

### 4.3 Required Data Attributes

```html
<div
  class="panel panel--unbound"
  data-panel-id="ACT-EX-AR-O1"
  data-panel-state="UNBOUND"
  data-panel-class="execution"
  data-intent="View active runs"
  aria-disabled="true"
>
  ...
</div>
```

---

## 5. DRAFT State Rendering

### 5.1 Visual Appearance

```
┌─────────────────────────────────────────────────┐
│  Approval Rules                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │  Rule Name           │  Status  │  Action │  │
│  ├───────────────────────────────────────────┤  │
│  │  ░░░░░░░░░░░░░░░░░░  │  ░░░░░░  │  ░░░░░  │  │
│  │  ░░░░░░░░░░░░░░░░░░  │  ░░░░░░  │  ░░░░░  │  │
│  │  ░░░░░░░░░░░░░░░░░░  │  ░░░░░░  │  ░░░░░  │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ⚠️ Capability not yet observed                 │
│                                                 │
│  [Refresh] [Edit] [Delete]  <- All disabled     │
└─────────────────────────────────────────────────┘
```

### 5.2 CSS Requirements

```css
.panel--draft {
  opacity: 0.85;
  background-color: var(--surface-default);
  border: 1px solid var(--border-warning);
}

.panel--draft .panel-content {
  filter: grayscale(50%);
}

.panel--draft .panel-actions button {
  pointer-events: none;
  opacity: 0.5;
}

.panel--draft::after {
  content: "Awaiting observation";
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 0.75rem;
  color: var(--text-warning);
}
```

### 5.3 Required Data Attributes

```html
<div
  class="panel panel--draft"
  data-panel-id="POL-AP-AR-O1"
  data-panel-state="DRAFT"
  data-panel-class="execution"
  data-capability="policy.approval_rules.list"
  data-disabled-reason="Capability declared but not observed via SDSR"
  aria-disabled="true"
>
  ...
</div>
```

---

## 6. BOUND State Rendering

### 6.1 Visual Appearance

```
┌─────────────────────────────────────────────────┐
│  Incident Summary                               │
├─────────────────────────────────────────────────┤
│                                                 │
│  Active Incidents: 3                            │
│                                                 │
│  ┌─────────────┬─────────────┬─────────────┐    │
│  │  Critical   │   Warning   │    Info     │    │
│  │      1      │      1      │      1      │    │
│  └─────────────┴─────────────┴─────────────┘    │
│                                                 │
│  Last updated: 2 minutes ago                    │
│                                                 │
│  [Refresh] [View All] [Export]                  │
└─────────────────────────────────────────────────┘
```

### 6.2 CSS Requirements

```css
.panel--bound {
  opacity: 1;
  background-color: var(--surface-default);
  border: 1px solid var(--border-default);
}

.panel--bound .panel-actions button {
  pointer-events: auto;
  opacity: 1;
}
```

### 6.3 Required Data Attributes

```html
<div
  class="panel panel--bound"
  data-panel-id="INC-AI-SUM-O1"
  data-panel-state="BOUND"
  data-panel-class="interpretation"
  data-capability="summary.incidents"
>
  ...
</div>
```

---

## 7. DEFERRED State Rendering

### 7.1 Configuration Options

DEFERRED panels can be rendered in two modes:

| Mode | Visibility | Use Case |
|------|------------|----------|
| HIDDEN | Not rendered | Feature not for current release |
| VISIBLE | Rendered with explanation | Temporarily disabled, coming back |

### 7.2 Visual Appearance (VISIBLE mode)

```
┌─────────────────────────────────────────────────┐
│  Advanced Audit Filters                         │
├─────────────────────────────────────────────────┤
│                                                 │
│     ┌──────────────────────────────────┐        │
│     │                                  │        │
│     │    ⏸️ Temporarily Unavailable    │        │
│     │                                  │        │
│     │    This feature is deferred      │        │
│     │    pending privacy review.       │        │
│     │                                  │        │
│     │    Reference: PIN-400            │        │
│     │                                  │        │
│     └──────────────────────────────────┘        │
│                                                 │
│  [No actions available]                         │
└─────────────────────────────────────────────────┘
```

### 7.3 CSS Requirements

```css
.panel--deferred {
  opacity: 0.5;
  background-color: var(--surface-disabled);
  border: 1px solid var(--border-disabled);
}

.panel--deferred.deferred--hidden {
  display: none;
}

.panel--deferred .panel-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel--deferred .panel-actions {
  display: none;
}
```

### 7.4 Required Data Attributes

```html
<div
  class="panel panel--deferred"
  data-panel-id="LOG-AL-SA-O4"
  data-panel-state="DEFERRED"
  data-panel-class="execution"
  data-deferred-reason="Deferred per PIN-400: Privacy review required"
  data-deferred-mode="visible"
  aria-hidden="false"
>
  ...
</div>
```

---

## 8. Accessibility Requirements

### 8.1 ARIA Attributes

| State | aria-disabled | aria-hidden | role |
|-------|---------------|-------------|------|
| EMPTY | true | false | region |
| UNBOUND | true | false | region |
| DRAFT | true | false | region |
| BOUND | false | false | region |
| DEFERRED (visible) | true | false | region |
| DEFERRED (hidden) | true | true | none |

### 8.2 Screen Reader Announcements

```javascript
// Announce panel state to screen readers
function announceState(panelId, state) {
  const messages = {
    EMPTY: "Panel planned but not yet implemented",
    UNBOUND: "Feature coming soon, capability pending",
    DRAFT: "Feature in development, controls disabled",
    BOUND: "Feature available",
    DEFERRED: "Feature temporarily unavailable"
  };

  announcer.polite(messages[state]);
}
```

---

## 9. Panel Title Resolution

When a panel is EMPTY (no intent YAML), the frontend MUST derive title from:

1. `panel_id` parsing: `ACC-PR-AI-O1` → "Account - Profile - Account Info - O1"
2. UI plan metadata (if available)
3. Fallback: Display panel_id raw

```javascript
function resolvePanelTitle(panel) {
  if (panel.intent?.title) {
    return panel.intent.title;
  }

  // Parse panel_id: {DOMAIN}-{SUBDOMAIN}-{TOPIC}-{ORDER}
  const parts = panel.panel_id.split('-');
  const domain = DOMAIN_MAP[parts[0]] || parts[0];
  const subdomain = SUBDOMAIN_MAP[parts[1]] || parts[1];
  const topic = TOPIC_MAP[parts[2]] || parts[2];

  return `${domain} - ${topic}`;
}
```

---

## 10. Developer Mode

In development builds, add visual state indicators:

```css
.dev-mode .panel::before {
  content: attr(data-panel-state) " | " attr(data-panel-id);
  position: absolute;
  top: -20px;
  left: 0;
  font-size: 0.625rem;
  font-family: monospace;
  color: var(--text-muted);
  background: var(--surface-code);
  padding: 2px 4px;
}
```

---

## 11. Gap Visibility Dashboard

The frontend SHOULD expose a debug view showing all non-BOUND panels:

```
┌─────────────────────────────────────────────────────────────┐
│  UI Gap Report                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EMPTY (31 panels)                                          │
│  ├── ACC-PR-AI-O1  Account Info                             │
│  ├── ACC-PR-AI-O2  Account Info Details                     │
│  └── ... (29 more)                                          │
│                                                             │
│  UNBOUND (54 panels)                                        │
│  ├── ACT-EX-AR-O1  Active Runs List                         │
│  ├── ACT-EX-AR-O2  Active Run Details                       │
│  └── ... (52 more)                                          │
│                                                             │
│  DRAFT (0 panels)                                           │
│                                                             │
│  BOUND (1 panel)                                            │
│  └── INC-AI-SUM-O1  Incident Summary  ✓                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Implementation Checklist

Frontend teams MUST verify:

- [ ] All EMPTY panels render with placeholder UX
- [ ] All UNBOUND panels render with "coming soon" UX
- [ ] All DRAFT panels render with disabled controls
- [ ] All BOUND panels render with full functionality
- [ ] DEFERRED panels respect visibility mode
- [ ] Panel states have distinct visual treatments
- [ ] ARIA attributes set correctly per state
- [ ] Developer mode shows state debugging info
- [ ] Gap visibility dashboard available in dev builds

---

## 13. Changelog

| Date | Change |
|------|--------|
| 2026-01-14 | Initial empty-state UI contract created |

---

## 14. Related Documents

| Document | Location | Role |
|----------|----------|------|
| UI-as-Constraint Doctrine | `docs/contracts/UI_AS_CONSTRAINT_V1.md` | Authority |
| UI Plan | `design/l2_1/ui_plan.yaml` | Panel source of truth |
| Compiler Spec | `docs/contracts/COMPILER_UI_FIRST_SPEC_V1.md` | Projection generation |
| PDG Invariants | `docs/contracts/PDG_STATE_INVARIANTS_V1.yaml` | State transitions |
